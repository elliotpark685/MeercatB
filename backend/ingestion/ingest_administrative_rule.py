"""Ingest one administrative rule from the Ministry of Government Legislation API."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from sqlalchemy import select, text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.models.law_article import LawArticle
from app.models.law_chunk import LawChunk
from app.models.law_document import LawDocument
from app.services.admrul_ingestion_service import AdmrulIngestionService
from app.services.law_embedding_service import LawEmbeddingService
from app.utils.admrul_api_client import AdmrulApiClient

DEFAULT_DOCUMENT_ID = "2100000246934"
DEFAULT_DOCUMENT_NAME = "근로감독관 집무규정(산업안전보건)"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest and embed one administrative rule.")
    parser.add_argument("--doc-id", default=DEFAULT_DOCUMENT_ID)
    parser.add_argument("--name", default=DEFAULT_DOCUMENT_NAME)
    parser.add_argument("--law-api-oc", default=settings.law_api_oc)
    parser.add_argument("--embed", action="store_true", help="Create article-level embeddings after ingestion.")
    return parser.parse_args()


def _embed_document_chunks(db, document_id: int) -> dict[str, int]:
    chunks = db.scalars(
        select(LawChunk)
        .join(LawArticle, LawArticle.id == LawChunk.law_article_id)
        .where(LawArticle.law_document_id == document_id, LawChunk.chunk_level == "article")
        .order_by(LawChunk.id)
    ).all()
    service = LawEmbeddingService(db=db, model_name=settings.embedding_model)
    embedded = 0
    skipped = 0
    for chunk in chunks:
        result = service.embed_chunk(chunk)
        if result["status"] == "embedded":
            embedded += 1
        else:
            skipped += 1
    db.commit()
    return {"embedded": embedded, "skipped": skipped}


def _link_industrial_safety_and_health_act(db, administrative_rule_id: int) -> None:
    law_id = db.scalar(
        select(LawDocument.id)
        .where(LawDocument.law_name == "산업안전보건법", LawDocument.is_active.is_(True))
        .order_by(LawDocument.id.desc())
        .limit(1)
    )
    if law_id is None:
        return
    db.execute(
        text(
            """
        insert into meerkat_pjt.law_document_relations
            (source_document_id, target_document_id, relation_type)
        values (:source_document_id, :target_document_id, 'related_law')
        on conflict do nothing
        """
        ),
        {"source_document_id": administrative_rule_id, "target_document_id": law_id},
    )
    db.commit()


def main() -> None:
    args = parse_args()
    if not args.law_api_oc:
        raise SystemExit("LAW_API_OC or --law-api-oc is required.")

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    init_db()
    with SessionLocal() as db:
        service = AdmrulIngestionService(db=db, api_client=AdmrulApiClient(args.law_api_oc))
        service.configure_document_classification(
            source_category="administrative_rule",
            source_type="moel_instruction",
            rule_form="훈령",
            rule_domain="labor_inspection",
            rule_purpose="enforcement_procedure",
            ministry="고용노동부",
        )
        created = service.ingest_by_id(args.doc_id)
        document = db.scalar(
            select(LawDocument)
            .where(LawDocument.law_no == args.doc_id, LawDocument.is_active.is_(True))
            .order_by(LawDocument.id.desc())
            .limit(1)
        )
        if document is None:
            raise SystemExit(f"No active document was stored for {args.name} ({args.doc_id}).")

        _link_industrial_safety_and_health_act(db, document.id)
        result = {"created": created, "document_id": document.id, "name": document.law_name}
        if args.embed:
            result["embedding"] = _embed_document_chunks(db, document.id)
        print(result)


if __name__ == "__main__":
    main()
