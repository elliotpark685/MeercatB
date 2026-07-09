from datetime import date

from app.core.database import Base
from app.models.law_article import LawArticle
from app.models.law_chunk import LawChunk
from app.models.law_document import LawDocument
from app.models.law_embedding import LawEmbedding
from app.repositories.law_repository import LawRepository
from app.services.law_search_service import LawSearchService
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def _session_factory() -> sessionmaker:
    engine = create_engine(
        'sqlite+pysqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
        future=True,
    )
    bind = engine.execution_options(schema_translate_map={'meerkat_pjt': None, 'public': None})
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
        jurisdiction='KR',
        source_url=source_url,
        effective_date=date(2024, 1, 1),
        is_active=True,
    )
    article = LawArticle(
        id=article_id,
        law_document_id=document_id,
        article_number=article_no,
        article_no=article_no,
        title=article_title,
        article_title=article_title,
        article_text=chunk_text,
        full_text=chunk_text,
        content=chunk_text,
        effective_date=date(2024, 1, 1),
        status='effective',
        version_group_key=f'{law_name}_{article_no}',
    )
    chunk = LawChunk(
        id=chunk_id,
        law_article_id=article_id,
        chunk_level='article',
        chunk_no=article_no,
        chunk_text=f'{law_name} {article_no}({article_title})\n{chunk_text}',
        token_count=10,
        metadata_json='{}',
    )
    embedding = LawEmbedding(
        chunk_id=chunk_id,
        article_id=None,
        embedding_model='text-embedding-3-small',
        embedding=[0.1, 0.2, 0.3],
        embedding_vector=[0.1, 0.2, 0.3],
    )
    db.add_all([document, article, chunk, embedding])


def test_integrated_search_returns_brief_fields(monkeypatch):
    monkeypatch.setattr('app.services.law_embedding_service.settings.openai_api_key', None)
    session_factory = _session_factory()
    with session_factory() as db:
        _seed_law_chunk(
            db,
            document_id=1,
            article_id=1,
            chunk_id=1,
            law_name='Construction Tech Act',
            article_no='Article 62',
            article_title='Construction work safety management',
            chunk_text='The contractor shall establish a safety management plan for construction work.',
            source_url='https://law.example/construct-tech',
        )
        _seed_law_chunk(
            db,
            document_id=2,
            article_id=2,
            chunk_id=2,
            law_name='Serious Accidents Punishment Act',
            article_no='Article 4',
            article_title='Duty to secure safety and health',
            chunk_text='The employer shall establish a safety and health management system.',
            source_url='https://law.example/serious-accident',
        )
        db.commit()

        result = LawSearchService(db).search('construction safety management', top_k=1, law_scope='Construction Tech Act')

        assert result.results
        assert result.results[0].law_name == 'Construction Tech Act'
        assert result.results[0].article_no == 'Article 62'
        assert result.results[0].title == 'Construction work safety management'
        assert 'safety management plan' in result.results[0].content_preview
        assert result.results[0].score > 0


def test_law_scope_filters_specific_law_and_logs_scope(monkeypatch):
    monkeypatch.setattr('app.services.law_embedding_service.settings.openai_api_key', None)
    session_factory = _session_factory()
    with session_factory() as db:
        _seed_law_chunk(
            db,
            document_id=1,
            article_id=1,
            chunk_id=1,
            law_name='Occupational Safety and Health Act',
            article_no='Article 8',
            article_title='Safety measures',
            chunk_text='The employer shall take necessary safety measures to prevent falls.',
            source_url='https://law.example/osha',
        )
        _seed_law_chunk(
            db,
            document_id=2,
            article_id=2,
            chunk_id=2,
            law_name='Construction Tech Act',
            article_no='Article 62',
            article_title='Construction work safety management',
            chunk_text='The contractor shall establish a safety management plan for construction work.',
            source_url='https://law.example/construct-tech',
        )
        db.commit()

        result = LawSearchService(db).search('safety', top_k=5, law_scope='Occupational Safety and Health Act')
        assert result.results[0].law_name == 'Occupational Safety and Health Act'
