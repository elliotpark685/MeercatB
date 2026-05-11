from datetime import date

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.api import api_router
from app.core.security import create_access_token
from app.core.database import Base, get_db
from app.models.generated_document import GeneratedDocument
from app.models.law_article import LawArticle
from app.models.law_document import LawDocument
from app.models.law_search_log import LawSearchLog
from app.models.safety_quiz import SafetyQuiz
from app.models.site import Site
from app.models.user import User


REQUIRED_SECTIONS = {
    "tbm": ["## 작업개요", "## 주요위험요인", "## 안전대책", "## 관련법령", "## TBM 전달사항"],
    "risk_assessment": ["## 작업공종", "## 위험요인", "## 현재대책", "## 개선대책", "## 위험도", "## 관련법령"],
    "work_plan": ["## 작업목적", "## 작업절차", "## 장비/인원", "## 위험요소", "## 안전조치", "## 관련법령"],
    "inspection_checklist": ["## 점검항목", "## 점검기준", "## 적합/부적합", "## 조치사항", "## 관련법령"],
}


def _auth_header(user_id: int, role: str) -> dict[str, str]:
    token = create_access_token(subject=str(user_id), role=role)
    return {"Authorization": f"Bearer {token}"}


def _build_client_with_db() -> tuple[TestClient, sessionmaker]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    bind = engine.execution_options(schema_translate_map={"meerkat_pjt": None})
    Base.metadata.create_all(bind=bind)
    TestingSessionLocal = sessionmaker(bind=bind, autocommit=False, autoflush=False, class_=Session)

    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), TestingSessionLocal


def _seed_base_data(session_factory: sessionmaker) -> None:
    with session_factory() as db:
        site = Site(id=1, name="Site A", location="Seoul")
        admin = User(
            id=100,
            email="admin@example.com",
            full_name="Admin",
            hashed_password="x",
            is_active=True,
            role="admin",
        )
        worker = User(
            id=200,
            email="worker@example.com",
            full_name="Worker",
            hashed_password="x",
            is_active=True,
            role="worker",
        )
        law_doc = LawDocument(id=1, title="산업안전보건기준에 관한 규칙", jurisdiction="KR")
        law_article = LawArticle(
            id=1,
            law_document_id=1,
            article_number="제1조",
            title="목적",
            chapter="총칙",
            section="공통",
            full_text="작업 전 위험성평가와 추락방지 조치를 실시해야 한다.",
            content="작업 전 위험성평가와 추락방지 조치를 실시해야 한다.",
            status="effective",
            version_group_key="산업안전보건기준에 관한 규칙_제1조",
        )
        quiz = SafetyQuiz(
            quiz_date=date.today(),
            site_id=1,
            user_id=None,
            question="q",
            choices_json='["a","b","c","d"]',
            answer_index=0,
            explanation="e",
            category="general",
            is_active=True,
        )
        db.add_all([site, admin, worker, law_doc, law_article, quiz])
        db.commit()


def test_law_search_saves_log():
    client, session_factory = _build_client_with_db()
    _seed_base_data(session_factory)

    payload = {"query": "추락 방지 조치", "top_k": 5, "user_id": 100, "site_id": 1}
    response = client.post("/api/v1/laws/search", json=payload)

    assert response.status_code == 200
    with session_factory() as db:
        logs = db.query(LawSearchLog).all()
        assert len(logs) == 1
        assert logs[0].query == payload["query"]
        assert logs[0].user_id == 100
        assert logs[0].site_id == 1
        assert logs[0].top_k == 5
        assert logs[0].result_count >= 0


def test_document_generate_has_required_sections_by_type():
    client, session_factory = _build_client_with_db()
    _seed_base_data(session_factory)

    for doc_type, sections in REQUIRED_SECTIONS.items():
        response = client.post(
            "/api/v1/documents/generate",
            json={
                "site_id": 1,
                "user_id": 100,
                "document_type": doc_type,
                "prompt": "추락 위험이 있는 작업 계획 작성",
            },
        )
        assert response.status_code == 200
        content = response.json()["content"]
        for section in sections:
            assert section in content


def test_admin_dashboard_returns_aggregates():
    client, session_factory = _build_client_with_db()
    _seed_base_data(session_factory)

    client.post(
        "/api/v1/laws/search",
        json={"query": "추락 방지 조치", "top_k": 3, "user_id": 100, "site_id": 1},
    )
    client.post(
        "/api/v1/documents/generate",
        json={
            "site_id": 1,
            "user_id": 100,
            "document_type": "tbm",
            "prompt": "고소작업 TBM",
        },
    )

    response = client.get("/api/v1/admin/dashboard?site_id=1", headers=_auth_header(100, "admin"))
    assert response.status_code == 200

    body = response.json()
    assert body["site_id"] == 1
    assert body["total_generated_documents"] >= 1
    assert body["total_law_searches"] >= 1
    assert body["today_quiz_count"] >= 1
    assert len(body["latest_generated_documents"]) >= 1
    assert len(body["latest_law_searches"]) >= 1
    assert "id" in body["latest_generated_documents"][0]
    assert "created_at" in body["latest_generated_documents"][0]
    assert "id" in body["latest_law_searches"][0]
    assert "created_at" in body["latest_law_searches"][0]


def test_worker_cannot_access_admin_dashboard():
    client, session_factory = _build_client_with_db()
    _seed_base_data(session_factory)

    response = client.get("/api/v1/admin/dashboard?site_id=1", headers=_auth_header(200, "worker"))
    assert response.status_code == 403


def test_law_search_logs_table_created_by_create_all():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    bind = engine.execution_options(schema_translate_map={"meerkat_pjt": None})
    Base.metadata.create_all(bind=bind)
    table_names = set(inspect(bind).get_table_names())
    assert "law_search_logs" in table_names


def test_admin_dashboard_returns_zero_and_empty_lists_when_no_data():
    client, session_factory = _build_client_with_db()
    with session_factory() as db:
        db.add(
            User(
                id=101,
                email="admin2@example.com",
                full_name="Admin Two",
                hashed_password="x",
                is_active=True,
                role="admin",
            )
        )
        db.commit()

    response = client.get("/api/v1/admin/dashboard", headers=_auth_header(101, "admin"))
    assert response.status_code == 200
    body = response.json()
    assert body["total_generated_documents"] == 0
    assert body["total_law_searches"] == 0
    assert body["today_quiz_count"] == 0
    assert body["latest_generated_documents"] == []
    assert body["latest_law_searches"] == []


def test_missing_authorization_rejected_for_admin_dashboard():
    client, _ = _build_client_with_db()
    response = client.get("/api/v1/admin/dashboard")
    assert response.status_code == 401


def test_nonexistent_user_rejected_for_admin_dashboard():
    client, _ = _build_client_with_db()
    response = client.get("/api/v1/admin/dashboard", headers=_auth_header(999999, "admin"))
    assert response.status_code == 401


def test_admin_can_access_dashboard():
    client, session_factory = _build_client_with_db()
    _seed_base_data(session_factory)
    response = client.get("/api/v1/admin/dashboard?site_id=1", headers=_auth_header(100, "admin"))
    assert response.status_code == 200
