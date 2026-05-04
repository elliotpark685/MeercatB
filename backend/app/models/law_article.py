from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class LawArticle(Base, TimestampMixin):
    __tablename__ = "law_articles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    law_document_id: Mapped[int] = mapped_column(
        ForeignKey("law_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    article_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(255))
    chapter: Mapped[str | None] = mapped_column(String(255))
    section: Mapped[str | None] = mapped_column(String(255))
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    effective_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    source_page_start: Mapped[int | None] = mapped_column(Integer)
    source_page_end: Mapped[int | None] = mapped_column(Integer)
    version_group_key: Mapped[str] = mapped_column(String(400), nullable=False, index=True)

    law_document = relationship("LawDocument", back_populates="articles")
    embeddings = relationship("LawEmbedding", back_populates="article", cascade="all, delete-orphan")
