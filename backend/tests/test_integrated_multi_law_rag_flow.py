import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.api import api_router
from app.core.database import Base, get_db
from app.models.generated_document import GeneratedDocument
from app.models.law_article import LawArticle
from app.models.law_chunk import LawChunk
from app.models.law_document import LawDocument
from app.models.law_embedding import LawEmbedding
from app.models.law_search_log import LawSearchLog
from app.models.site import Site
from app.models.user import User
from app.services.embedding_service import EmbeddingService
from app.services.law_chunking_service import LawChunkingService
from app.services.law_embedding_service import LawEmbeddingService
from app.services.law_ingestion_service import LawIngestionService, LawSourceArticle, LawSourceDocument


TARGET_SOURCES = [
    LawSourceDocument(
        law_name="산업안전보건법",
        law_short_name="산안법",
        effective_date="2024-01-01",
        source_url="https://law.example/osha",
        articles=[
            LawSourceArticle(
                article_no="제38조",
                article_title="안전조치",
                article_text="① 사업주는 추락 위험을 방지하기 위하여 필요한 안전조치를 하여야 한다.\n1. 작업발판 설치\n2. 안전난간 설치",
            )
        ],
    ),
    LawSourceDocument(
        law_name="시설물의 안전 및 유지관리에 관한 특별법",
        law_short_name="시설물안전법",
        effective_date="2024-01-01",
        source_url="https://law.example/facility",
        articles=[
            LawSourceArticle(
                article_no="제11조",
                article_title="안전점검",
                article_text="관리주체는 시설물의 안전점검을 실시하고 필요한 조치를 하여야 한다.",
            )
        ],
    ),
    LawSourceDocument(
        law_name="건설산업기본법",
        law_short_name="건산법",
        effective_date="2024-01-01",
        source_url="https://law.example/construction-industry",
        articles=[
            LawSourceArticle(
                article_no="제22조",
                article_title="건설공사 시공관리",
                article_text="건설사업자는 건설공사의 적정한 시공과 안전한 작업관리를 위하여 필요한 관리를 하여야 한다.",
            )
        ],
    ),
    LawSourceDocument(
        law_name="건설기술 진흥법",
        law_short_name="건설기술진흥법",
        effective_date="2024-01-01",
        source_url="https://law.example/construction-tech",
        articles=[
            LawSourceArticle(
                article_no="제62조",
                article_title="건설공사의 안전관리",
                article_text="건설공사의 참여자는 안전관리계획을 수립하고 이행하여야 한다.",
            )
        ],
    ),
    LawSourceDocument(
        law_name="중대재해 처벌 등에 관한 법률",
        law_short_name="중대재해처벌법",
        effective_date="2024-01-27",
        source_url="https://law.example/serious-accident",
        articles=[
            LawSourceArticle(
                article_no="제4조",
                article_title="사업주와 경영책임자등의 안전 및 보건 확보의무",
                article_text="사업주 또는 경영책임자등은 안전보건관리체계를 구축하고 이행하여야 한다.",
            )
        ],
    ),
]


def _build_client_with_db() -> tuple[TestClient, sessionmaker]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    bind = engine.execution_options(schema_translate_map={"meerkat_pjt": None, "public": None})
    Base.metadata.create_all(bind=bind)
    session_factory = sessionmaker(bind=bind, autocommit=False, autoflush=False, class_=Session)

    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), session_factory


def _seed_site_and_user(db: Session) -> None:
    db.add_all(
        [
            Site(id=1, name="Integrated Site", location="Seoul"),
            User(
                id=100,
                email="integrated@example.com",
                full_name="Integrated User",
                hashed_password="x",
                is_active=True,
                role="admin",
            ),
        ]
    )
    db.commit()


def test_full_multi_law_rag_flow_with_sqlite_and_mocked_external_calls():
    client, session_factory = _build_client_with_db()
    with session_factory() as db:
        _seed_site_and_user(db)
        table_names = set(inspect(db.bind).get_table_names())
        assert {
            "law_documents",
            "law_articles",
            "law_chunks",
            "law_embeddings",
            "law_search_logs",
            "generated_documents",
        }.issubset(table_names)

        ingestion_service = LawIngestionService(db=db, embedding_service=EmbeddingService())
        ingestion_results = [ingestion_service.ingest_source_document(source) for source in TARGET_SOURCES]
        assert all(result["status"] == "ingested" for result in ingestion_results)
        assert db.query(LawDocument).count() == 5
        assert db.query(LawArticle).count() == 5

        chunking_result = LawChunkingService(db).chunk_all_articles()
        assert chunking_result["created_count"] >= 2
        assert db.query(LawChunk).count() >= 7

        embedding_result = LawEmbeddingService(db=db, mock_dimension=8).embed_pending_chunks()
        assert embedding_result["created_count"] > 0
        assert db.query(LawEmbedding).count() >= db.query(LawChunk).count()

    search_response = client.post(
        "/api/v1/laws/search",
        json={"query": "추락 방지 안전조치", "top_k": 3, "user_id": 100, "site_id": 1},
    )
    assert search_response.status_code == 200
    search_body = search_response.json()
    assert "citations" in search_body
    assert "raw_hits" in search_body
    assert search_body["results"]
    assert search_body["results"][0]["law_name"]
    assert search_body["results"][0]["article_no"]
    assert search_body["results"][0]["chunk_text"]
    assert search_body["results"][0]["score"] > 0
    assert search_body["results"][0]["source_url"]
    assert search_body["results"][0]["effective_date"]

    scoped_response = client.post(
        "/api/v1/laws/search",
        json={"query": "안전관리계획", "top_k": 5, "law_scope": "건설기술 진흥법", "site_id": 1},
    )
    assert scoped_response.status_code == 200
    scoped_results = scoped_response.json()["results"]
    assert scoped_results
    assert {item["law_name"] for item in scoped_results} == {"건설기술 진흥법"}

    document_response = client.post(
        "/api/v1/documents/generate",
        json={
            "site_id": 1,
            "user_id": 100,
            "document_type": "tbm",
            "prompt": "추락 위험이 있는 고소작업 TBM 문서 작성",
        },
    )
    assert document_response.status_code == 200
    document_body = document_response.json()
    assert document_body["content"] == document_body["generated_text"]
    assert document_body["references"]
    assert document_body["references"][0]["law_name"]
    assert document_body["references"][0]["article_no"]
    assert document_body["references"][0]["chunk_text"]
    assert "## 참고 법령 목록" in document_body["generated_text"]

    with session_factory() as db:
        logs = db.query(LawSearchLog).order_by(LawSearchLog.id.asc()).all()
        assert len(logs) >= 3
        assert logs[0].top_k == 3
        assert logs[0].result_count >= 1
        assert json.loads(logs[1].law_scope) == ["건설기술 진흥법"]

        generated_document = db.query(GeneratedDocument).one()
        references = json.loads(generated_document.references_json)
        assert references
        assert generated_document.citations_json == generated_document.references_json


def test_backward_compatible_legacy_law_search_response_shape():
    client, session_factory = _build_client_with_db()
    with session_factory() as db:
        _seed_site_and_user(db)
        ingestion_service = LawIngestionService(db=db, embedding_service=EmbeddingService())
        ingestion_service.ingest_source_document(TARGET_SOURCES[0])

    response = client.post("/api/v1/laws/search", json={"query": "추락 방지 조치", "top_k": 1})

    assert response.status_code == 200
    body = response.json()
    assert set(["query", "answer", "citations", "raw_hits", "results"]).issubset(body)
    assert body["citations"]
    assert body["raw_hits"]
    assert body["results"]
