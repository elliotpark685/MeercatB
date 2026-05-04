from datetime import date

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class LawDocument(Base, TimestampMixin):
    __tablename__ = "law_documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    law_type: Mapped[str | None] = mapped_column(String(50))
    law_no: Mapped[str | None] = mapped_column(String(100))
    effective_date: Mapped[date | None] = mapped_column(Date)
    jurisdiction: Mapped[str] = mapped_column(String(100), nullable=False, default="KR")
    version: Mapped[str | None] = mapped_column(String(50))
    source_url: Mapped[str | None] = mapped_column(String(1024))
    source_file_path: Mapped[str | None] = mapped_column(String(1024))
    raw_text: Mapped[str | None] = mapped_column(Text)

    articles = relationship("LawArticle", back_populates="law_document", cascade="all, delete-orphan")
