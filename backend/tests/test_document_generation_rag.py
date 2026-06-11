import json

from app.models.generated_document import GeneratedDocument
from app.models.site import Site
from app.schemas.law import LawSearchResponse, LawSearchResultItem
from app.services.document_generation_service import DocumentGenerationService


class _FakeDB:
    def __init__(self):
        self.site = Site(id=1, name="Site A", location="Seoul")
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
        self.last_kwargs = {"args": args, "kwargs": kwargs}
        return LawSearchResponse(
            query=args[0],
            answer="answer",
            citations=[],
            raw_hits=[],
            results=[
                LawSearchResultItem(
                    law_name="건설기술 진흥법",
                    article_no="제62조",
                    article_title="건설공사의 안전관리",
                    chunk_text="건설공사의 참여자는 안전관리계획을 수립하여야 한다.",
                    score=1.2,
                    source_url="https://law.example/construct-tech",
                    effective_date="2024-01-01",
                    article_id=1,
                    chunk_id=2,
                    matched_reason=["keyword:1"],
                ),
                LawSearchResultItem(
                    law_name="중대재해 처벌 등에 관한 법률",
                    article_no="제4조",
                    article_title="안전 및 보건 확보의무",
                    chunk_text="사업주는 안전보건관리체계를 구축하여야 한다.",
                    score=1.0,
                    source_url="https://law.example/serious-accident",
                    effective_date="2024-01-27",
                    article_id=3,
                    chunk_id=4,
                    matched_reason=["keyword:1"],
                ),
            ],
        )


def test_document_generation_uses_integrated_law_context_and_stores_references(monkeypatch):
    monkeypatch.setattr("app.services.document_generation_service.settings.openai_api_key", None)
    db = _FakeDB()
    law_search_service = _FakeLawSearchService()
    service = DocumentGenerationService(db=db, law_search_service=law_search_service)  # type: ignore[arg-type]

    document = service.generate(
        site_id=1,
        user_id=100,
        document_type="tbm",
        prompt="고소작업 안전 문서 작성",
    )

    references = json.loads(document.references_json)
    assert law_search_service.last_kwargs["kwargs"]["top_k"] == 5
    assert "제공된 법령 context에 근거" in document.content
    assert "추가 검토 필요" in document.content
    assert "## 참고 법령 목록" in document.content
    assert references[0]["law_name"] == "건설기술 진흥법"
    assert references[0]["article_no"] == "제62조"
    assert references[0]["chunk_text"]
    assert document.citations_json == document.references_json
    assert db.committed is True


def test_document_generation_missing_site_raises_value_error():
    db = _FakeDB()
    law_search_service = _FakeLawSearchService()
    service = DocumentGenerationService(db=db, law_search_service=law_search_service)  # type: ignore[arg-type]

    try:
        service.generate(site_id=999, user_id=None, document_type="tbm", prompt="test prompt")
    except ValueError as exc:
        assert str(exc) == "Site not found"
    else:
        raise AssertionError("Expected ValueError")
