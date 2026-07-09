import json

from app.models.generated_document import GeneratedDocument
from app.models.site import Site
from app.schemas.law import LawSearchResponse, LawSearchResultItem
from app.services.document_generation_service import DocumentGenerationService


class _FakeDB:
    def __init__(self):
        self.site = Site(id=1, name='Site A', location='Seoul')
        self.document = None
        self.committed = False

    def get(self, model, id_):
        if model is Site and id_ == 1:
            return self.site
        return None

    def add(self, item):
        self.document = item
        item.id = 10

    def commit(self):
        self.committed = True

    def refresh(self, item):
        item.id = 10


class _FakeLawSearchService:
    def __init__(self):
        self.last_kwargs = None

    def search(self, *args, **kwargs):
        self.last_kwargs = {'args': args, 'kwargs': kwargs}
        return LawSearchResponse(
            query=args[0],
            answer='answer',
            citations=[],
            results=[
                LawSearchResultItem(
                    article_id=1,
                    law_name='Construction Tech Act',
                    article_no='Article 62',
                    title='Construction work safety management',
                    content_preview='The contractor shall establish a safety management plan for construction work.',
                    score=1.2,
                ),
                LawSearchResultItem(
                    article_id=3,
                    law_name='Serious Accidents Punishment Act',
                    article_no='Article 4',
                    title='Duty to secure safety and health',
                    content_preview='The employer shall establish a safety and health management system.',
                    score=1.0,
                ),
            ],
        )


def test_document_generation_uses_integrated_law_context_and_stores_references(monkeypatch):
    monkeypatch.setattr('app.services.document_generation_service.settings.openai_api_key', None)
    db = _FakeDB()
    law_search_service = _FakeLawSearchService()
    service = DocumentGenerationService(db=db, law_search_service=law_search_service)  # type: ignore[arg-type]

    document = service.generate(
        site_id=1,
        user_id=100,
        document_type='tbm',
        prompt='Write a safety document for a high-risk construction site',
    )

    references = json.loads(document.references_json)
    assert law_search_service.last_kwargs['kwargs']['top_k'] == 5
    assert document.content
    assert references[0]['law_name'] == 'Construction Tech Act'
    assert references[0]['article_no'] == 'Article 62'
    assert references[0]['chunk_text']
    assert document.citations_json == document.references_json
    assert db.committed is True


def test_document_generation_missing_site_raises_value_error():
    db = _FakeDB()
    law_search_service = _FakeLawSearchService()
    service = DocumentGenerationService(db=db, law_search_service=law_search_service)  # type: ignore[arg-type]

    try:
        service.generate(site_id=999, user_id=None, document_type='tbm', prompt='test prompt')
    except ValueError as exc:
        assert str(exc) == 'Site not found'
    else:
        raise AssertionError('Expected ValueError')
