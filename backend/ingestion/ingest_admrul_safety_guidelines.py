"""고용노동부 표준안전작업지침 ingestion CLI.

사용법:
    python ingestion/ingest_admrul_safety_guidelines.py
    python ingestion/ingest_admrul_safety_guidelines.py --max-docs 10
    python ingestion/ingest_admrul_safety_guidelines.py --doc-id 123456
    python ingestion/ingest_admrul_safety_guidelines.py --embed

중복 방지: version_hash(doc_id + name) 기준으로 이미 있으면 skip.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="법제처 행정규칙 API에서 표준안전작업지침을 수집하여 DB에 저장합니다."
    )
    parser.add_argument("--law-api-oc", default=None, help="법제처 API OC 키 (없으면 LAW_API_OC 환경변수 사용)")
    parser.add_argument("--max-docs", type=int, default=None, help="수집할 최대 문서 수 (None = 전체)")
    parser.add_argument("--doc-id", default=None, help="특정 문서 ID만 수집")
    parser.add_argument("--embed", action="store_true", help="수집 후 임베딩 생성")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # 환경변수/인자에서 API 키 획득
    from app.core.config import settings

    oc = args.law_api_oc or settings.law_api_oc
    if not oc:
        logger.error(
            "법제처 API 키가 없습니다. LAW_API_OC 환경변수를 설정하거나 --law-api-oc 인자를 사용하세요."
        )
        sys.exit(1)

    from app.core.database import SessionLocal, init_db
    from app.services.admrul_ingestion_service import AdmrulIngestionService
    from app.utils.admrul_api_client import AdmrulApiClient

    logger.info("DB 초기화 중...")
    init_db()

    api_client = AdmrulApiClient(oc=oc)

    with SessionLocal() as db:
        service = AdmrulIngestionService(db=db, api_client=api_client)

        if args.doc_id:
            logger.info("단일 문서 수집: id=%s", args.doc_id)
            created = service.ingest_by_id(args.doc_id)
            logger.info("결과: %s", "신규 생성" if created else "이미 존재 (skip)")
        else:
            logger.info("전체 표준안전작업지침 수집 시작...")
            stats = service.ingest_all(max_docs=args.max_docs)
            logger.info(
                "수집 완료 — 조회: %d, 신규: %d, skip: %d, 실패: %d",
                stats["fetched"],
                stats["created"],
                stats["skipped"],
                stats["failed"],
            )

    if args.embed:
        logger.info("규칙 문서 청크 보정 중 (청크 없는 safety_standard/rule 아티클)...")
        _ensure_rule_chunks()
        logger.info("임베딩 생성 시작...")
        _run_embedding()

    logger.info("완료.")


def _ensure_rule_chunks() -> None:
    """source_type='rule' 문서 중 청크 없는 아티클에 청크를 자동 생성."""
    from app.core.database import SessionLocal
    from app.models.law_article import LawArticle
    from app.models.law_chunk import LawChunk
    from app.models.law_document import LawDocument
    from app.services.admrul_ingestion_service import SOURCE_CATEGORY
    from sqlalchemy import select

    with SessionLocal() as db:
        stmt = (
            select(LawArticle)
            .join(LawDocument, LawDocument.id == LawArticle.law_document_id)
            .outerjoin(LawChunk, LawChunk.law_article_id == LawArticle.id)
            .where(
                LawDocument.source_category == SOURCE_CATEGORY,
                LawDocument.source_type == "rule",
                LawDocument.is_active.is_(True),
                LawChunk.id.is_(None),
            )
        )
        articles = list(db.scalars(stmt).unique().all())
        logger.info("청크 없는 규칙 아티클: %d개", len(articles))
        created = 0
        for art in articles:
            text = art.article_text or art.full_text or art.content or ""
            if not text.strip():
                continue
            db.add(LawChunk(
                law_article_id=art.id,
                chunk_level="article",
                chunk_no="1",
                chunk_text=text,
                token_count=len(text.split()),
            ))
            created += 1
        db.commit()
        logger.info("규칙 청크 생성 완료: %d개", created)


def _run_embedding() -> None:
    """수집된 안전기준 청크에 임베딩 생성."""
    from app.core.database import SessionLocal
    from app.repositories.law_repository import LawRepository
    from app.services.admrul_ingestion_service import SOURCE_CATEGORY, SOURCE_TYPE
    from app.services.law_embedding_service import LawEmbeddingService
    from app.models.law_embedding import LawEmbedding
    from app.core.config import settings
    from sqlalchemy import select, and_
    from app.models.law_chunk import LawChunk
    from app.models.law_article import LawArticle
    from app.models.law_document import LawDocument

    embedding_svc = LawEmbeddingService(db=None)  # type: ignore[arg-type]
    embedding_model = settings.embedding_model

    with SessionLocal() as db:
        # 임베딩 없는 안전기준 청크 조회
        stmt = (
            select(LawChunk)
            .join(LawArticle, LawArticle.id == LawChunk.law_article_id)
            .join(LawDocument, LawDocument.id == LawArticle.law_document_id)
            .outerjoin(
                LawEmbedding,
                and_(
                    LawEmbedding.chunk_id == LawChunk.id,
                    LawEmbedding.embedding_model == embedding_model,
                ),
            )
            .where(
                LawDocument.source_category == SOURCE_CATEGORY,  # rule 포함 전체 안전기준
                LawDocument.is_active.is_(True),
                LawEmbedding.id.is_(None),
            )
        )
        chunks = list(db.scalars(stmt).unique().all())
        logger.info("임베딩 대상 청크: %d개", len(chunks))

        for i, chunk in enumerate(chunks):
            try:
                vec = embedding_svc.generate_embedding(chunk.chunk_text)
                emb = LawEmbedding(
                    chunk_id=chunk.id,
                    embedding_model=embedding_model,
                    embedding=vec,
                )
                db.add(emb)
                if (i + 1) % 50 == 0:
                    db.commit()
                    logger.info("임베딩 진행: %d/%d", i + 1, len(chunks))
            except Exception as exc:
                logger.warning("임베딩 실패 chunk_id=%d: %s", chunk.id, exc)

        db.commit()
        logger.info("임베딩 완료.")


if __name__ == "__main__":
    main()
