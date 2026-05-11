from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.api import api_router
from app.core.database import Base, get_db
from app.core.security import verify_password
from app.models.site import Site
from app.models.user import User


def _build_client_with_db() -> tuple[TestClient, sessionmaker]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    bind = engine.execution_options(
        schema_translate_map={
            "meerkat_pjt": None,
            "public": None,
        }
    )
    Base.metadata.create_all(bind=bind)
    testing_session_local = sessionmaker(bind=bind, autocommit=False, autoflush=False, class_=Session)

    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), testing_session_local


def test_register_creates_user_and_returns_token():
    client, session_factory = _build_client_with_db()
    with session_factory() as db:
        db.add(Site(id=1, name="Site A", location="Seoul"))
        db.commit()

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "new.user@example.com", "full_name": "New User", "password": "devpass1234"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["role"] == "worker"
    assert body["site_id"] == 1

    with session_factory() as db:
        created = db.query(User).filter(User.email == "new.user@example.com").first()
        assert created is not None
        assert created.full_name == "New User"
        assert created.role == "worker"
        assert verify_password("devpass1234", created.hashed_password)


def test_register_rejects_duplicate_email():
    client, session_factory = _build_client_with_db()
    with session_factory() as db:
        db.add(
            User(
                email="dup@example.com",
                full_name="Existing",
                hashed_password="sha256$salt$hash",
                is_active=True,
                role="worker",
            )
        )
        db.commit()

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "full_name": "Another", "password": "devpass1234"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"
