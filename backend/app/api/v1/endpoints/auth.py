from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.site import Site
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, MeResponse, RegisterRequest, RegisterResponse

router = APIRouter()


def _find_user_by_login_id(db: Session, login_id: str) -> User | None:
    normalized = login_id.strip().lower()
    if not normalized:
        return None

    if "@" in normalized:
        return db.scalar(select(User).where(User.email == normalized))

    candidates = db.scalars(select(User).where(User.email.ilike(f"{normalized}@%"))).all()
    exact_local = [u for u in candidates if u.email.split("@", 1)[0].lower() == normalized]
    if len(exact_local) == 1:
        return exact_local[0]
    return None


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = _find_user_by_login_id(db, payload.identifier)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login ID or password")

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login ID or password")

    # Current domain model stores site relation on documents/quizzes, not user profile.
    # Return a default site_id hint when only one site exists in DB.
    site_id = None
    site = db.scalar(select(Site.id).order_by(Site.id.asc()).limit(1))
    if site is not None:
        site_id = int(site)

    token = create_access_token(subject=str(user.id), role=user.role)
    return LoginResponse(
        access_token=token,
        user_id=user.id,
        role=user.role,
        site_id=site_id,
    )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    normalized_email = payload.email.strip().lower()
    if not normalized_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required")

    existing = db.scalar(select(User).where(User.email == normalized_email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=normalized_email,
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
        is_active=True,
        role="worker",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    site_id = None
    site = db.scalar(select(Site.id).order_by(Site.id.asc()).limit(1))
    if site is not None:
        site_id = int(site)

    token = create_access_token(subject=str(user.id), role=user.role)
    return RegisterResponse(
        access_token=token,
        user_id=user.id,
        role=user.role,
        site_id=site_id,
    )


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        user_id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
    )
