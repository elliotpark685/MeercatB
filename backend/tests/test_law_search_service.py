from datetime import date

import app.models.generated_document  # noqa: F401
import app.models.law_search_log  # noqa: F401
import app.models.safety_quiz  # noqa: F401
import app.models.site  # noqa: F401
import app.models.user  # noqa: F401
from app.models.law_article import LawArticle
from app.models.law_document import LawDocument
from app.services.law_search_service import LawSearchService


class _StubRepo:
    def __init__(self, rows):
        self.rows = rows

    def search_by_keyword(self, keyword: str, top_k: int = 20):
        return self.rows[:top_k]

    def get_article_with_document(self, article_id: int):
        for article, document in self.rows:
            if article.id == article_id:
                return article, document
        return None


def _make_row(article_id: int, title: str, status: str):
    doc = LawDocument(id=1, title="산업안전보건기준에 관한 규칙", law_type="시행규칙", jurisdiction="KR")
    article = LawArticle(
        id=article_id,
        law_document_id=1,
        article_number=f"제{article_id}조",
        title=title,
        chapter="제1장",
        section="제1절",
        full_text="비계 작업 시 추락 위험 방지를 위해 보호구 설치 및 점검",
        content="비계 작업 시 추락 위험 방지를 위해 보호구 설치 및 점검",
        effective_date=date(2026, 3, 2),
        status=status,
        source_page_start=10,
        source_page_end=11,
        version_group_key=f"산업안전보건기준에 관한 규칙_제{article_id}조",
    )
    return article, doc


def test_law_search_service_returns_citations():
    service = LawSearchService(db=None)  # type: ignore[arg-type]
    service.repo = _StubRepo(rows=[_make_row(42, "추락의 방지", "effective")])

    result = service.search("비계 추락 방지 설치 점검", top_k=5, validate_latest=False)
    assert result.citations
    assert result.citations[0].article_id == 42
    assert result.raw_hits[0].matched_reason


def test_scheduled_articles_kept_but_penalized():
    service = LawSearchService(db=None)  # type: ignore[arg-type]
    rows = [
        _make_row(1, "추락의 방지", "effective"),
        _make_row(2, "추락의 방지(신설)", "scheduled"),
    ]
    service.repo = _StubRepo(rows=rows)

    result = service.search("비계 추락 방지", top_k=2, validate_latest=False)
    assert len(result.citations) == 2
    assert result.citations[0].status == "effective"
    assert {c.status for c in result.citations} == {"effective", "scheduled"}
    scheduled_hit = [hit for hit in result.raw_hits if hit.article_id == 2][0]
    assert "status:scheduled_penalty" in scheduled_hit.matched_reason


def test_validate_latest_returns_placeholder_message():
    service = LawSearchService(db=None)  # type: ignore[arg-type]
    service.repo = _StubRepo(rows=[_make_row(42, "추락의 방지", "effective")])

    result = service.search("비계 추락 방지", top_k=1, validate_latest=True)
    assert result.answer == "latest validation is not implemented yet"
