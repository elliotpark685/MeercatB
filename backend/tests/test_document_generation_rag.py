import json

from app.models.generated_document import GeneratedDocument
from app.models.site import Site
from app.schemas.law import LawSearchResponse, LawSearchResultItem
from app.schemas.safety_standard import SafetyStandardResultItem, SafetyStandardSearchResponse
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


class _FakeAdministrativeRuleSearchService:
    def __init__(self):
        self.last_kwargs = None

    def search(self, **kwargs):
        self.last_kwargs = kwargs
        return SafetyStandardSearchResponse(
            query=kwargs["query"],
            results=[
                SafetyStandardResultItem(
                    source_type="moel_instruction",
                    source_name="근로감독관 집무규정(산업안전보건)",
                    article_no="제44조",
                    article_title="작업중지",
                    content_preview="근로감독관은 급박한 위험이 있으면 작업중지를 명할 수 있다.",
                    score=0.9,
                    ministry="고용노동부",
                )
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
        workplace_name='Tower A level 3',
        equipment_tools=['Mobile scaffold', 'Safety harness'],
        prompt='Write a safety document for a high-risk construction site',
    )

    references = json.loads(document.references_json)
    assert law_search_service.last_kwargs['kwargs']['top_k'] == 5
    assert document.content
    assert references[0]['law_name'] == 'Construction Tech Act'
    assert references[0]['article_no'] == 'Article 62'
    assert references[0]['chunk_text']
    assert document.citations_json == document.references_json
    assert '작업장소: Tower A level 3' in document.content
    assert 'Mobile scaffold, Safety harness' in document.content
    assert db.committed is True


def test_document_generation_adds_administrative_rule_context_for_safety_keywords(monkeypatch):
    monkeypatch.setattr('app.services.document_generation_service.settings.openai_api_key', None)
    db = _FakeDB()
    administrative_rules = _FakeAdministrativeRuleSearchService()
    service = DocumentGenerationService(
        db=db,
        law_search_service=_FakeLawSearchService(),  # type: ignore[arg-type]
        administrative_rule_search_service=administrative_rules,  # type: ignore[arg-type]
    )

    document = service.generate(
        site_id=1,
        user_id=100,
        document_type='tbm',
        workplace_name='Tower A level 3',
        safety_keywords=['작업중지', '추락'],
        prompt='고소 작업 TBM을 작성해줘',
    )

    references = json.loads(document.references_json)
    assert administrative_rules.last_kwargs['query'] == '작업중지 추락'
    assert administrative_rules.last_kwargs['top_k'] == 3
    assert any(reference['reference_type'] == '행정규칙' for reference in references)
    assert '근로감독관 집무규정(산업안전보건)' in document.content


def test_document_generation_missing_site_raises_value_error():
    db = _FakeDB()
    law_search_service = _FakeLawSearchService()
    service = DocumentGenerationService(db=db, law_search_service=law_search_service)  # type: ignore[arg-type]

    try:
        service.generate(site_id=999, user_id=None, document_type='tbm', workplace_name='Test site', prompt='test prompt')
    except ValueError as exc:
        assert str(exc) == 'Site not found'
    else:
        raise AssertionError('Expected ValueError')
