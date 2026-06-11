from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.law_article import LawArticle
from app.models.law_chunk import LawChunk
from app.models.law_document import LawDocument
from app.models.law_embedding import LawEmbedding
from app.services.law_embedding_service import LawEmbeddingService


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


def _seed_chunk(db: Session) -> LawChunk:
    document = LawDocument(title="건설기술 진흥법", law_name="건설기술 진흥법", jurisdiction="KR")
    db.add(document)
    db.flush()
    article = LawArticle(
        law_document_id=document.id,
        article_number="제62조",
        article_no="제62조",
        title="건설공사의 안전관리",
        article_title="건설공사의 안전관리",
        article_text="안전관리계획을 수립하여야 한다.",
        status="effective",
        version_group_key="건설기술진흥법_제62조",
    )
    db.add(article)
    db.flush()
    chunk = LawChunk(
        law_article_id=article.id,
        chunk_level="article",
        chunk_no="제62조",
        chunk_text="건설기술 진흥법 제62조(건설공사의 안전관리)\n안전관리계획을 수립하여야 한다.",
        token_count=8,
        metadata_json="{}",
    )
    db.add(chunk)
    db.commit()
    db.refresh(chunk)
    return chunk


def test_law_embedding_service_uses_mock_without_api_key(monkeypatch):
    monkeypatch.setattr("app.services.law_embedding_service.settings.openai_api_key", None)
    session_factory = _session_factory()
    with session_factory() as db:
        chunk = _seed_chunk(db)
        service = LawEmbeddingService(db=db, mock_dimension=8)

        result = service.embed_chunk(chunk)
        embedding = db.query(LawEmbedding).one()

        assert result["status"] == "embedded"
        assert embedding.chunk_id == chunk.id
        assert embedding.article_id is None
        assert embedding.embedding_model == "text-embedding-3-small"
        assert len(embedding.embedding) == 8
        assert embedding.embedding == embedding.embedding_vector


def test_law_embedding_service_skips_existing_chunk_embedding(monkeypatch):
    monkeypatch.setattr("app.services.law_embedding_service.settings.openai_api_key", None)
    session_factory = _session_factory()
    with session_factory() as db:
        chunk = _seed_chunk(db)
        service = LawEmbeddingService(db=db, mock_dimension=8)

        first = service.embed_chunk(chunk)
        second = service.embed_chunk(chunk)

        assert first["status"] == "embedded"
        assert second["status"] == "skipped_duplicate"
        assert db.query(LawEmbedding).count() == 1


def test_embed_pending_chunks_only_embeds_missing(monkeypatch):
    monkeypatch.setattr("app.services.law_embedding_service.settings.openai_api_key", None)
    session_factory = _session_factory()
    with session_factory() as db:
        _seed_chunk(db)
        service = LawEmbeddingService(db=db, mock_dimension=8)

        first = service.embed_pending_chunks()
        second = service.embed_pending_chunks()

        assert first == {"created_count": 1, "skipped_count": 0}
        assert second == {"created_count": 0, "skipped_count": 0}
        assert db.query(LawEmbedding).count() == 1
