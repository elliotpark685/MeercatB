from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class SafetyQuiz(Base, TimestampMixin):
    __tablename__ = "safety_quizzes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    quiz_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id", ondelete="SET NULL"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    choices_json: Mapped[str] = mapped_column(Text, nullable=False)
    answer_index: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="general-safety", nullable=False)

    site = relationship("Site", back_populates="quizzes")
    user = relationship("User", back_populates="quizzes")

