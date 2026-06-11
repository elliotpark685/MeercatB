from datetime import date

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.law_article import LawArticle
from app.models.law_chunk import LawChunk
from app.models.law_document import LawDocument
from app.models.law_embedding import LawEmbedding
from app.repositories.law_repository import LawRepository
from app.services.law_search_service import LawSearchService


def _build_session_factory() -> sessionmaker:
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
    return sessionmaker(bind=bind, autocommit=False, autoflush=False, class_=Session)


def test_multi_law_tables_and_columns_are_created_in_sqlite():
    session_factory = _build_session_factory()
    bind = session_factory.kw["bind"]
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())

    assert {"law_documents", "law_articles", "law_chunks", "law_embeddings"}.issubset(table_names)
    assert {"law_name", "law_short_name", "amendment_date", "version_hash", "is_active"}.issubset(
        {column["name"] for column in inspector.get_columns("law_documents")}
    )
    assert {"article_no", "article_title", "article_text"}.issubset(
        {column["name"] for column in inspector.get_columns("law_articles")}
    )
    assert {"chunk_id", "embedding_model", "embedding_vector"}.issubset(
        {column["name"] for column in inspector.get_columns("law_embeddings")}
    )


def test_multi_law_chunk_embedding_can_be_persisted():
    session_factory = _build_session_factory()
    with session_factory() as db:
        document = LawDocument(
            title="중대재해 처벌 등에 관한 법률",
            law_name="중대재해 처벌 등에 관한 법률",
            law_short_name="중대재해처벌법",
            law_type="법률",
            source_url="https://example.test/law",
            effective_date=date(2024, 1, 27),
            amendment_date=date(2023, 12, 26),
            version_hash="hash-1",
            jurisdiction="KR",
        )
        db.add(document)
        db.flush()

        article = LawArticle(
            law_document_id=document.id,
            article_number="제4조",
            article_no="제4조",
            title="사업주와 경영책임자등의 안전 및 보건 확보의무",
            article_title="사업주와 경영책임자등의 안전 및 보건 확보의무",
            full_text="사업주 또는 경영책임자등은 안전보건관리체계를 구축하고 이행하여야 한다.",
            content="사업주 또는 경영책임자등은 안전보건관리체계를 구축하고 이행하여야 한다.",
            article_text="사업주 또는 경영책임자등은 안전보건관리체계를 구축하고 이행하여야 한다.",
            status="effective",
            effective_date=date(2024, 1, 27),
            version_group_key="중대재해처벌법_제4조",
        )
        db.add(article)
        db.flush()

        chunk = LawChunk(
            law_article_id=article.id,
            chunk_level="paragraph",
            chunk_no="제1항",
            chunk_text="안전보건관리체계 구축 및 이행",
            token_count=3,
            metadata_json='{"paragraph_no":"1"}',
        )
        db.add(chunk)
        db.flush()

        embedding = LawEmbedding(
            article_id=article.id,
            chunk_id=chunk.id,
            embedding_model="test-embedding",
            embedding=[0.1, 0.2, 0.3],
            embedding_vector=[0.1, 0.2, 0.3],
        )
        db.add(embedding)
        db.commit()

        saved_chunk = db.get(LawChunk, chunk.id)
        saved_embedding = db.get(LawEmbedding, embedding.id)

        assert saved_chunk is not None
        assert saved_chunk.article.law_document.law_short_name == "중대재해처벌법"
        assert saved_embedding is not None
        assert saved_embedding.chunk_id == saved_chunk.id


def test_search_finds_new_law_name_and_article_text_columns():
    session_factory = _build_session_factory()
    with session_factory() as db:
        document = LawDocument(
            title="건설기술 진흥법",
            law_name="건설기술 진흥법",
            law_short_name="건설기술진흥법",
            law_type="법률",
            jurisdiction="KR",
        )
        db.add(document)
        db.flush()
        article = LawArticle(
            law_document_id=document.id,
            article_number="제62조",
            article_no="제62조",
            title="건설공사의 안전관리",
            article_title="건설공사의 안전관리",
            article_text="건설공사의 참여자는 안전관리계획을 수립하고 이행하여야 한다.",
            status="effective",
            version_group_key="건설기술진흥법_제62조",
        )
        db.add(article)
        db.commit()

        repo = LawRepository(db)
        rows = repo.search_by_keyword("안전관리계획", top_k=5)
        service = LawSearchService(db)

        assert rows[0][0].article_no == "제62조"
        result = service.search("건설기술진흥법 안전관리계획", top_k=1)
        assert result.citations[0].law_name == "건설기술 진흥법"
        assert result.citations[0].article_no == "제62조"
