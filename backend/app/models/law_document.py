from datetime import date

from sqlalchemy import Boolean, Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class LawDocument(Base, TimestampMixin):
    __tablename__ = "law_documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    law_name: Mapped[str | None] = mapped_column(String(255), index=True)
    law_short_name: Mapped[str | None] = mapped_column(String(100), index=True)
    law_type: Mapped[str | None] = mapped_column(String(50))
    law_no: Mapped[str | None] = mapped_column(String(100))
    effective_date: Mapped[date | None] = mapped_column(Date)
    amendment_date: Mapped[date | None] = mapped_column(Date)
    jurisdiction: Mapped[str] = mapped_column(String(100), nullable=False, default="KR")
    version: Mapped[str | None] = mapped_column(String(50))
    version_hash: Mapped[str | None] = mapped_column(String(128), index=True)
    source_url: Mapped[str | None] = mapped_column(String(1024))
    source_file_path: Mapped[str | None] = mapped_column(String(1024))
    raw_text: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # 안전기준 구분 필드 (NULL = 기존 5개 법령)
    source_category: Mapped[str | None] = mapped_column(String(50), index=True)
    source_type: Mapped[str | None] = mapped_column(String(100), index=True)
    provider: Mapped[str | None] = mapped_column(String(100))

    articles = relationship("LawArticle", back_populates="law_document", cascade="all, delete-orphan")
