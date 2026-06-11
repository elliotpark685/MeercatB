import json
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.law_article import LawArticle
from app.models.law_chunk import LawChunk
from app.models.law_document import LawDocument
from app.models.law_embedding import LawEmbedding
from app.models.law_search_log import LawSearchLog
from app.services.law_search_service import LawSearchService


def _session_factory() -> sessionmaker:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    bind = engine.execution_options(schema_translate_map={"meerkat_pjt": None, "public": None})
    Base.metadata.create_all(bind=bind)
    return sessionmaker(bind=bind, autocommit=False, autoflush=False, class_=Session)


def _seed_law_chunk(
    db: Session,
    *,
    document_id: int,
    article_id: int,
    chunk_id: int,
    law_name: str,
    article_no: str,
    article_title: str,
    chunk_text: str,
    source_url: str,
) -> None:
    document = LawDocument(
        id=document_id,
        title=law_name,
        law_name=law_name,
        jurisdiction="KR",
        source_url=source_url,
        effective_date=date(2024, 1, 1),
    )
    article = LawArticle(
        id=article_id,
        law_document_id=document_id,
        article_number=article_no,
        article_no=article_no,
        title=article_title,
        article_title=article_title,
        article_text=chunk_text,
        effective_date=date(2024, 1, 1),
        status="effective",
        version_group_key=f"{law_name}_{article_no}",
    )
    chunk = LawChunk(
        id=chunk_id,
        law_article_id=article_id,
        chunk_level="article",
        chunk_no=article_no,
        chunk_text=f"{law_name} {article_no}({article_title})\n{chunk_text}",
        token_count=10,
        metadata_json="{}",
    )
    embedding = LawEmbedding(
        chunk_id=chunk_id,
        article_id=None,
        embedding_model="text-embedding-3-small",
        embedding=[0.1, 0.2, 0.3],
        embedding_vector=[0.1, 0.2, 0.3],
    )
    db.add_all([document, article, chunk, embedding])


def test_integrated_search_returns_chunk_fields_and_source(monkeypatch):
    monkeypatch.setattr("app.services.law_embedding_service.settings.openai_api_key", None)
    session_factory = _session_factory()
    with session_factory() as db:
        _seed_law_chunk(
            db,
            document_id=1,
            article_id=1,
            chunk_id=1,
            law_name="건설기술 진흥법",
            article_no="제62조",
            article_title="건설공사의 안전관리",
            chunk_text="건설공사의 참여자는 안전관리계획을 수립하여야 한다.",
            source_url="https://law.example/construct-tech",
        )
        _seed_law_chunk(
            db,
            document_id=2,
            article_id=2,
            chunk_id=2,
            law_name="중대재해 처벌 등에 관한 법률",
            article_no="제4조",
            article_title="안전 및 보건 확보의무",
            chunk_text="사업주는 안전보건관리체계를 구축하여야 한다.",
            source_url="https://law.example/serious-accident",
        )
        db.commit()

        result = LawSearchService(db).search("건설공사 안전관리계획", top_k=1)

        assert result.results
        assert result.results[0].law_name == "건설기술 진흥법"
        assert result.results[0].article_no == "제62조"
        assert result.results[0].article_title == "건설공사의 안전관리"
        assert "안전관리계획" in result.results[0].chunk_text
        assert result.results[0].score > 0
        assert result.results[0].source_url == "https://law.example/construct-tech"
        assert result.results[0].effective_date == "2024-01-01"


def test_law_scope_filters_specific_law_and_logs_scope(monkeypatch):
    monkeypatch.setattr("app.services.law_embedding_service.settings.openai_api_key", None)
    session_factory = _session_factory()
    with session_factory() as db:
        _seed_law_chunk(
            db,
            document_id=1,
            article_id=1,
            chunk_id=1,
            law_name="산업안전보건법",
            article_no="제38조",
            article_title="안전조치",
            chunk_text="사업주는 추락 방지를 위한 안전조치를 하여야 한다.",
            source_url="https://law.example/osha",
        )
        _seed_law_chunk(
            db,
            document_id=2,
            article_id=2,
            chunk_id=2,
            law_name="건설기술 진흥법",
            article_no="제62조",
            article_title="건설공사의 안전관리",
            chunk_text="건설공사의 참여자는 안전관리계획을 수립하여야 한다.",
            source_url="https://law.example/construct-tech",
        )
        db.commit()

        result = LawSearchService(db).search("안전", top_k=5, law_scope="산업안전보건법")
        log = db.query(LawSearchLog).one()

        assert [item.law_name for item in result.results] == ["산업안전보건법"]
        assert json.loads(log.law_scope) == ["산업안전보건법"]
        assert log.top_k == 5
        assert log.result_count == 1
