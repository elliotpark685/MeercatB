from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.services.embedding_service import EmbeddingService
from app.services.law_validation_service import LawValidationService
from app.services.law_search_service import LawSearchService


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


def get_law_validation_service() -> LawValidationService:
    return LawValidationService()


def get_law_search_service(
    db: Session = Depends(get_db),
    law_validation_service: LawValidationService = Depends(get_law_validation_service),
) -> LawSearchService:
    return LawSearchService(db=db, law_validation_service=law_validation_service)


def get_current_user(
    db: Session = Depends(get_db),
    x_user_id: str | None = Header(
        default=None,
        alias="X-User-Id",
        description="Authenticated user id. Admin endpoints require an admin user id.",
        examples=["1"],
    ),
) -> User:
    if x_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-User-Id header is required")

    try:
        user_id = int(x_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-User-Id must be integer") from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user

