from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.quiz import DailyQuizResponse
from app.services.quiz_service import QuizService

router = APIRouter()


def get_quiz_service(db: Session = Depends(get_db)) -> QuizService:
    return QuizService(db=db)


@router.get("/daily", response_model=DailyQuizResponse)
def get_daily_quiz(
    site_id: int | None = Query(default=None),
    user_id: int | None = Query(default=None),
    service: QuizService = Depends(get_quiz_service),
) -> DailyQuizResponse:
    quizzes = service.get_daily_quizzes(site_id=site_id, user_id=user_id)
    return DailyQuizResponse(quizzes=quizzes)

