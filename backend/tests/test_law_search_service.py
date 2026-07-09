from datetime import date

from app.models.law_article import LawArticle
from app.models.law_document import LawDocument
from app.models.law_embedding import LawEmbedding
from app.services.law_search_service import LawSearchService


class _StubRepo:
    def __init__(self, rows=None, with_embeddings=True):
        self.rows = rows or []
        self.with_embeddings = with_embeddings

    def search_by_keyword(self, keyword, top_k=20, law_scope=None):
        return [(article, document) for article, document in self.rows[:top_k]]

    def get_article_with_document(self, article_id):
        for article, document in self.rows:
            if article.id == article_id:
                return article, document
        return None

    def create_law_search_log(self, **kwargs):
        pass

    def search_chunks_by_keyword(self, **kwargs):
        if not self.with_embeddings:
            return []
        return []

    def list_chunks_for_scope(self, **kwargs):
        return []


def _make_row(article_id: int, title: str, status: str):
    doc = LawDocument(id=1, title='Sample Law', law_name='Sample Law', law_type='Rule', jurisdiction='KR')
    article = LawArticle(
        id=article_id,
        law_document_id=1,
        article_number=f'Article {article_id}',
        title=title,
        chapter='Chapter 1',
        section='Section 1',
        full_text='Workers shall install fall protection and inspect equipment before work.',
        content='Workers shall install fall protection and inspect equipment before work.',
        effective_date=date(2026, 3, 2),
        status=status,
        source_page_start=10,
        source_page_end=11,
        version_group_key=f'Sample Law_{article_id}',
    )
    return article, doc


def test_law_search_service_returns_citations():
    service = LawSearchService(db=None)  # type: ignore[arg-type]
    service.repo = _StubRepo(rows=[_make_row(42, 'Fall protection', 'effective')])

    result = service.search('fall protection plan', top_k=5, validate_latest=False)
    assert result.citations
    assert result.citations[0].article_id == 42
    assert result.results[0].content_preview


def test_scheduled_articles_kept_but_penalized():
    service = LawSearchService(db=None)  # type: ignore[arg-type]
    rows = [
        _make_row(1, 'Fall protection', 'effective'),
        _make_row(2, 'Fall protection (scheduled)', 'scheduled'),
    ]
    service.repo = _StubRepo(rows=rows)

    result = service.search('fall protection', top_k=2, validate_latest=False)
    assert len(result.citations) == 2
    assert result.citations[0].status == 'effective'
    assert {c.status for c in result.citations} == {'effective', 'scheduled'}
    assert result.results[0].content_preview


def test_validate_latest_returns_placeholder_message():
    service = LawSearchService(db=None)  # type: ignore[arg-type]
    service.repo = _StubRepo(rows=[_make_row(42, 'Fall protection', 'effective')])

    result = service.search('fall protection', top_k=1, validate_latest=True)
    assert result.answer == 'latest validation is not implemented yet'
