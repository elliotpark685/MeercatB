from sqlalchemy import case, or_, select
from sqlalchemy.orm import Session

from app.models.law_article import LawArticle
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

    def create_law_search_log(self, **kwargs) -> LawSearchLog:
        log = LawSearchLog(**kwargs)
        self.db.add(log)
        self.db.flush()
        return log

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

    def search_by_keyword(self, keyword: str, top_k: int = 20) -> list[tuple[LawArticle, LawDocument]]:
        pattern = f"%{keyword}%"
        status_rank = case(
            (LawArticle.status == "effective", 0),
            (LawArticle.status == "unknown", 1),
            (LawArticle.status == "scheduled", 2),
            else_=3,
        )
        stmt = (
            select(LawArticle, LawDocument)
            .join(LawDocument, LawDocument.id == LawArticle.law_document_id)
            .where(
                or_(
                    LawArticle.full_text.ilike(pattern),
                    LawArticle.title.ilike(pattern),
                    LawArticle.article_number.ilike(pattern),
                    LawDocument.title.ilike(pattern),
                    LawArticle.chapter.ilike(pattern),
                    LawArticle.section.ilike(pattern),
                )
            )
            .order_by(status_rank.asc(), LawArticle.id.desc())
            .limit(top_k)
        )
        rows = self.db.execute(stmt).all()
        return [(row[0], row[1]) for row in rows]

