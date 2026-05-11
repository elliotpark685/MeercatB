from collections.abc import Generator
import logging

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

_engine = None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, class_=Session)
Base = declarative_base(metadata=MetaData(schema=settings.db_schema))
logger = logging.getLogger(__name__)


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.sqlalchemy_database_uri,
            pool_pre_ping=True,
            future=True,
        )
        SessionLocal.configure(bind=_engine)
    return _engine


def create_vector_extension() -> bool:
    """Try to enable pgvector extension.

    Returns False when DB user lacks permission, so startup can continue.
    """
    if not settings.use_pgvector:
        logger.info("USE_PGVECTOR=false, skipping pgvector extension creation.")
        return False

    try:
        with get_engine().connect() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            connection.commit()
            return True
    except SQLAlchemyError as exc:
        logger.warning(
            "Could not create pgvector extension automatically. "
            "Continue startup and create it manually if needed. Error: %s",
            exc,
        )
        return False


def create_schema_if_not_exists() -> bool:
    """Create application schema if it does not exist."""
    schema = settings.db_schema.replace('"', "")
    try:
        with get_engine().connect() as connection:
            connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}";'))
            connection.commit()
            return True
    except SQLAlchemyError as exc:
        logger.warning(
            "Could not create schema '%s' automatically. "
            "Continue startup and create it manually if needed. Error: %s",
            settings.db_schema,
            exc,
        )
        return False


def init_db() -> None:
    # Import all model modules before create_all so metadata is complete.
    from app.models.generated_document import GeneratedDocument  # noqa: F401
    from app.models.law_article import LawArticle  # noqa: F401
    from app.models.law_document import LawDocument  # noqa: F401
    from app.models.law_embedding import LawEmbedding  # noqa: F401
    from app.models.safety_quiz import SafetyQuiz  # noqa: F401
    from app.models.site import Site  # noqa: F401
    from app.models.user import User  # noqa: F401

    create_vector_extension()
    create_schema_if_not_exists()
    Base.metadata.create_all(bind=get_engine())


def get_db() -> Generator[Session, None, None]:
    get_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


