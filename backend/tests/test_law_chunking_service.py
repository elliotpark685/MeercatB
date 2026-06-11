import json
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.law_article import LawArticle
from app.models.law_chunk import LawChunk
from app.models.law_document import LawDocument
from app.services.law_chunking_service import LawChunkingService


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


def _seed_article(db: Session) -> LawArticle:
    document = LawDocument(title="산업안전보건법", law_name="산업안전보건법", jurisdiction="KR")
    db.add(document)
    db.flush()
    article = LawArticle(
        law_document_id=document.id,
        article_number="제38조",
        article_no="제38조",
        title="안전조치",
        article_title="안전조치",
        article_text=(
            "① 사업주는 위험을 예방하기 위하여 필요한 조치를 하여야 한다.\n"
            "1. 추락 방지 조치\n"
            "2. 붕괴 방지 조치\n"
            "② 근로자는 안전조치를 준수하여야 한다."
        ),
        effective_date=date(2024, 1, 1),
        status="effective",
        version_group_key="산업안전보건법_제38조",
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def test_chunk_article_creates_article_paragraph_and_item_chunks():
    session_factory = _session_factory()
    with session_factory() as db:
        article = _seed_article(db)
        service = LawChunkingService(db)

        result = service.chunk_article(article)
        chunks = db.query(LawChunk).order_by(LawChunk.id).all()

        assert result["created_count"] == 5
        assert [chunk.chunk_level for chunk in chunks] == ["article", "paragraph", "item", "item", "paragraph"]
        assert all("산업안전보건법 제38조(안전조치)" in chunk.chunk_text for chunk in chunks)
        metadata = json.loads(chunks[0].metadata_json)
        assert metadata["law_name"] == "산업안전보건법"
        assert metadata["article_no"] == "제38조"
        assert metadata["article_title"] == "안전조치"
        assert metadata["effective_date"] == "2024-01-01"
        assert chunks[0].token_count > 0


def test_chunk_article_skips_existing_chunks():
    session_factory = _session_factory()
    with session_factory() as db:
        article = _seed_article(db)
        service = LawChunkingService(db)

        first = service.chunk_article(article)
        db.refresh(article)
        second = service.chunk_article(article)

        assert first["created_count"] == 5
        assert second["created_count"] == 0
        assert second["skipped_count"] == 5
