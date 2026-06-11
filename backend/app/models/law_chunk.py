from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class LawChunk(Base, TimestampMixin):
    __tablename__ = "law_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    law_article_id: Mapped[int] = mapped_column(
        ForeignKey("law_articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_level: Mapped[str] = mapped_column(String(50), nullable=False, default="article", index=True)
    chunk_no: Mapped[str | None] = mapped_column(String(100), index=True)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[str | None] = mapped_column(Text)

    article = relationship("LawArticle", back_populates="chunks")
    embeddings = relationship("LawEmbedding", back_populates="chunk", cascade="all, delete-orphan")
