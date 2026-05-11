from datetime import date

from pydantic import BaseModel


class QuizItem(BaseModel):
    quiz_id: int
    quiz_date: date
    question: str
    choices: list[str]
    answer_index: int
    explanation: str
    category: str


class DailyQuizResponse(BaseModel):
    quizzes: list[QuizItem]

