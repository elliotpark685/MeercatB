from sqlalchemy import and_, case, or_, select, update
from sqlalchemy.orm import Session, joinedload

from app.models.law_article import LawArticle
from app.models.law_chunk import LawChunk
from app.models.law_document import LawDocument
from app.models.law_embedding import LawEmbedding
from app.models.law_search_log import LawSearchLog


class LawRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_law_document(self, **kwargs) -> LawDocument:
        law_document = LawDocument(**kwargs)
        self.db.add(law_document)
        self.db.flush()
        return law_document

    def create_law_article(self, **kwargs) -> LawArticle:
        article = LawArticle(**kwargs)
        self.db.add(article)
        self.db.flush()
        return article

    def create_law_embedding(self, **kwargs) -> LawEmbedding:
        embedding = LawEmbedding(**kwargs)
        self.db.add(embedding)
        self.db.flush()
        return embedding

    def create_law_chunk(self, **kwargs) -> LawChunk:
        chunk = LawChunk(**kwargs)
        self.db.add(chunk)
        self.db.flush()
        return chunk

    def create_law_search_log(self, **kwargs) -> LawSearchLog:
        log = LawSearchLog(**kwargs)
        self.db.add(log)
        self.db.flush()
        return log

    def get_law_document_by_version_hash(self, version_hash: str) -> LawDocument | None:
        stmt = select(LawDocument).where(LawDocument.version_hash == version_hash)
        return self.db.scalars(stmt).first()

    def deactivate_other_documents(self, law_name: str, keep_document_id: int) -> None:
        """Mark older versions of a law as inactive once a newer one is ingested."""
        stmt = (
            update(LawDocument)
            .where(
                LawDocument.law_name == law_name,
                LawDocument.id != keep_document_id,
                LawDocument.is_active.is_(True),
            )
            .values(is_active=False)
        )
        self.db.execute(stmt)

    def list_articles_with_documents(self) -> list[LawArticle]:
        stmt = select(LawArticle).options(joinedload(LawArticle.law_document), joinedload(LawArticle.chunks))
        return list(self.db.scalars(stmt).unique().all())

    def list_chunks_without_embedding(self, embedding_model: str, limit: int | None = None) -> list[LawChunk]:
        stmt = (
            select(LawChunk)
            .options(joinedload(LawChunk.article).joinedload(LawArticle.law_document))
            .outerjoin(
                LawEmbedding,
                (LawEmbedding.chunk_id == LawChunk.id) & (LawEmbedding.embedding_model == embedding_model),
            )
            .where(LawEmbedding.id.is_(None))
            .order_by(LawChunk.id.asc())
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).unique().all())

    def get_embedding_by_chunk_and_model(self, chunk_id: int, embedding_model: str) -> LawEmbedding | None:
        stmt = select(LawEmbedding).where(
            LawEmbedding.chunk_id == chunk_id,
            LawEmbedding.embedding_model == embedding_model,
        )
        return self.db.scalars(stmt).first()

    def search_chunks_by_keyword(
        self,
        keywords: list[str],
        law_scope: list[str] | None = None,
        limit: int = 100,
    ) -> list[tuple[LawChunk, LawArticle, LawDocument, LawEmbedding | None]]:
        keyword_filter = self._keyword_filter(keywords)
        filters = [item for item in [self._law_scope_filter(law_scope), keyword_filter] if item is not None]
        stmt = self._chunk_select_stmt().order_by(LawChunk.id.asc()).limit(limit)
        if filters:
            stmt = stmt.where(and_(*filters))
        rows = self.db.execute(stmt).all()
        return [(row[0], row[1], row[2], row[3]) for row in rows]

    def list_chunks_for_scope(
        self,
        law_scope: list[str] | None = None,
        limit: int = 500,
    ) -> list[tuple[LawChunk, LawArticle, LawDocument, LawEmbedding | None]]:
        stmt = self._chunk_select_stmt().order_by(LawChunk.id.asc()).limit(limit)
        scope_filter = self._law_scope_filter(law_scope)
        if scope_filter is not None:
            stmt = stmt.where(scope_filter)
        rows = self.db.execute(stmt).all()
        return [(row[0], row[1], row[2], row[3]) for row in rows]

    def get_article_by_id(self, article_id: int) -> LawArticle | None:
        return self.db.get(LawArticle, article_id)

    def get_article_with_document(self, article_id: int) -> tuple[LawArticle, LawDocument] | None:
        stmt = (
            select(LawArticle, LawDocument)
            .join(LawDocument, LawDocument.id == LawArticle.law_document_id)
            .where(LawArticle.id == article_id)
        )
        row = self.db.execute(stmt).first()
        if not row:
            return None
        return row[0], row[1]

    def search_by_keyword(
        self,
        keyword: str,
        top_k: int = 20,
        law_scope: list[str] | None = None,
    ) -> list[tuple[LawArticle, LawDocument]]:
        pattern = f"%{keyword}%"
        status_rank = case(
            (LawArticle.status == "effective", 0),
            (LawArticle.status == "unknown", 1),
            (LawArticle.status == "scheduled", 2),
            else_=3,
        )
        filters = [
            LawDocument.is_active.is_(True),
            or_(
                LawArticle.full_text.ilike(pattern),
                LawArticle.article_text.ilike(pattern),
                LawArticle.title.ilike(pattern),
                LawArticle.article_title.ilike(pattern),
                LawArticle.article_number.ilike(pattern),
                LawArticle.article_no.ilike(pattern),
                LawDocument.title.ilike(pattern),
                LawDocument.law_name.ilike(pattern),
                LawDocument.law_short_name.ilike(pattern),
                LawArticle.chapter.ilike(pattern),
                LawArticle.section.ilike(pattern),
            ),
        ]
        scope_filter = self._law_scope_filter(law_scope)
        if scope_filter is not None:
            filters.append(scope_filter)
        stmt = (
            select(LawArticle, LawDocument)
            .join(LawDocument, LawDocument.id == LawArticle.law_document_id)
            .where(and_(*filters))
            .order_by(status_rank.asc(), LawArticle.id.desc())
            .limit(top_k)
        )
        rows = self.db.execute(stmt).all()
        return [(row[0], row[1]) for row in rows]

    @staticmethod
    def _chunk_select_stmt():
        return (
            select(LawChunk, LawArticle, LawDocument, LawEmbedding)
            .join(LawArticle, LawArticle.id == LawChunk.law_article_id)
            .join(LawDocument, LawDocument.id == LawArticle.law_document_id)
            .outerjoin(LawEmbedding, LawEmbedding.chunk_id == LawChunk.id)
            .where(LawDocument.is_active.is_(True))
        )

    @staticmethod
    def _keyword_filter(keywords: list[str]):
        filters = []
        for keyword in keywords:
            pattern = f"%{keyword}%"
            filters.append(
                or_(
                    LawChunk.chunk_text.ilike(pattern),
                    LawArticle.article_text.ilike(pattern),
                    LawArticle.article_title.ilike(pattern),
                    LawArticle.article_no.ilike(pattern),
                    LawDocument.law_name.ilike(pattern),
                    LawDocument.law_short_name.ilike(pattern),
                    LawDocument.title.ilike(pattern),
                )
            )
        return or_(*filters) if filters else None

    @staticmethod
    def _law_scope_filter(law_scope: list[str] | None):
        if not law_scope:
            return None
        filters = []
        for law_name in law_scope:
            pattern = f"%{law_name}%"
            filters.append(
                or_(
                    LawDocument.law_name.ilike(pattern),
                    LawDocument.law_short_name.ilike(pattern),
                    LawDocument.title.ilike(pattern),
                )
            )
        return or_(*filters)
