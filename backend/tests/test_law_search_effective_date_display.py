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


def _make_row(article_id: int, article_effective_date: date, document_effective_date: date):
    doc = LawDocument(
        id=1,
        title="Sample Law",
        law_name="Sample Law",
        law_type="Rule",
        jurisdiction="KR",
        effective_date=document_effective_date,
    )
    article = LawArticle(
        id=article_id,
        law_document_id=1,
        article_number=f"Article {article_id}",
        title="Sample Article",
        chapter="Chapter 1",
        section="Section 1",
        full_text="Sample text",
        content="Sample text",
        effective_date=article_effective_date,
        status="effective",
        source_page_start=10,
        source_page_end=11,
        version_group_key=f"Sample Law_{article_id}",
    )
    return article, doc


def test_search_result_includes_article_and_document_effective_dates():
    service = LawSearchService(db=None)  # type: ignore[arg-type]
    service.repo = _StubRepo(rows=[_make_row(42, date(2026, 3, 2), date(2026, 6, 1))])

    result = service.search("sample", top_k=5, validate_latest=False)

    assert result.results
    assert result.results[0].effective_date == "2026-03-02"
    assert result.results[0].document_effective_date == "2026-06-01"
