import json
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.safety_quiz import SafetyQuiz
from app.schemas.quiz import QuizItem


class QuizService:
    """Provides daily safety quiz content."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_daily_quizzes(self, site_id: int | None = None, user_id: int | None = None) -> list[QuizItem]:
        today = date.today()
        stmt = select(SafetyQuiz).where(SafetyQuiz.quiz_date == today, SafetyQuiz.is_active.is_(True))
        if site_id is not None:
            stmt = stmt.where((SafetyQuiz.site_id == site_id) | (SafetyQuiz.site_id.is_(None)))
        if user_id is not None:
            stmt = stmt.where((SafetyQuiz.user_id == user_id) | (SafetyQuiz.user_id.is_(None)))

        quizzes = self.db.scalars(stmt).all()
        if not quizzes:
            quizzes = [self._seed_default_quiz(today, site_id=site_id, user_id=user_id)]

        return [
            QuizItem(
                quiz_id=quiz.id,
                quiz_date=quiz.quiz_date,
                question=quiz.question,
                choices=json.loads(quiz.choices_json),
                answer_index=quiz.answer_index,
                explanation=quiz.explanation,
                category=quiz.category,
            )
            for quiz in quizzes
        ]

    def _seed_default_quiz(self, quiz_date: date, site_id: int | None, user_id: int | None) -> SafetyQuiz:
        quiz = SafetyQuiz(
            quiz_date=quiz_date,
            site_id=site_id,
            user_id=user_id,
            question="What should be checked first before elevated work starts?",
            choices_json=json.dumps(
                [
                    "Coffee break schedule",
                    "Fall protection and anchor points",
                    "Concrete color",
                    "Vehicle fuel level",
                ]
            ),
            answer_index=1,
            explanation="Fall hazards are a leading cause of severe construction incidents.",
            category="working-at-height",
            is_active=True,
        )
        self.db.add(quiz)
        self.db.commit()
        self.db.refresh(quiz)
        return quiz

