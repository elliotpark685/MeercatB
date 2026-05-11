from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.core.database import Base
from app.models.mixins import TimestampMixin

if settings.use_pgvector:
    from pgvector.sqlalchemy import Vector

    EMBEDDING_COLUMN_TYPE = Vector(settings.vector_dimension)
else:
    EMBEDDING_COLUMN_TYPE = JSON


class LawEmbedding(Base, TimestampMixin):
    __tablename__ = "law_embeddings"
    __table_args__ = (
        UniqueConstraint("article_id", "embedding_model", name="uq_article_embedding_model"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    article_id: Mapped[int] = mapped_column(
        ForeignKey("law_articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    embedding: Mapped[list[float]] = mapped_column(EMBEDDING_COLUMN_TYPE, nullable=False)

    article = relationship("LawArticle", back_populates="embeddings")
