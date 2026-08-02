from datetime import date

from app.models.law_article import LawArticle
from app.models.law_document import LawDocument
from app.repositories.law_repository import LawRepository


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeSession:
    def __init__(self, rows):
        self.rows = rows
        self.last_stmt = None

    def execute(self, stmt):
        self.last_stmt = stmt
        return _FakeResult(self.rows)


def test_search_by_keyword_finds_article_title():
    doc = LawDocument(id=1, title="산업안전보건기준에 관한 규칙", jurisdiction="KR")
    article = LawArticle(
        id=1,
        law_document_id=1,
        article_number="제42조",
        title="추락의 방지",
        chapter="제1장 총칙",
        section="제2절",
        full_text="비계 작업에서 추락 방지 조치를 해야 한다.",
        content="비계 작업에서 추락 방지 조치를 해야 한다.",
        effective_date=date(2026, 3, 2),
        status="effective",
        source_page_start=28,
        source_page_end=29,
        version_group_key="산업안전보건기준에 관한 규칙_제42조",
    )
    session = _FakeSession(rows=[(article, doc)])
    repo = LawRepository(session)

    results = repo.search_by_keyword("추락의 방지", top_k=5)
    assert len(results) == 1
    assert results[0][0].title == "추락의 방지"
    assert "law_articles.title" in str(session.last_stmt)


def test_deactivate_other_documents_normalizes_law_name_before_updating():
    session = _FakeSession(rows=[])
    repo = LawRepository(session)

    repo.deactivate_other_documents(law_name=" Sample Law ", keep_document_id=7)

    assert "trim(meerkat_pjt.law_documents.law_name)" in str(session.last_stmt)
    assert "Sample Law" in session.last_stmt.compile().params.values()
