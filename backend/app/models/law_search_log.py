from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class LawSearchLog(Base, TimestampMixin):
    __tablename__ = "law_search_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id", ondelete="SET NULL"), index=True)
    law_scope: Mapped[str | None] = mapped_column(Text)
    top_k: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    result_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user = relationship("User", back_populates="law_search_logs")
    site = relationship("Site", back_populates="law_search_logs")

