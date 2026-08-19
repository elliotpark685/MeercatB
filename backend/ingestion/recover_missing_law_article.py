"""Recover one parser-confirmed missing article without replacing its document.

The command parses the original source again, verifies that the selected parsed
article is absent from the existing document, and then uses the regular
LawIngestionService article -> chunk -> embedding creation path.  It is dry-run
by default; database writes require ``--apply``.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.models.law_article import LawArticle
from app.models.law_document import LawDocument
from app.services.embedding_service import EmbeddingService
from app.services.law_ingestion_service import LawIngestionService
from app.utils.article_title_index_loader import load_article_title_index
from app.utils.law_parser import ParsedLawArticle, parse_korean_law_articles


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recover a parser-confirmed missing law article.")
    parser.add_argument("--document-id", type=int, required=True)
    parser.add_argument("--file-path", required=True)
    parser.add_argument("--article-title-index-path", required=True)
    parser.add_argument("--law-name", required=True)
    parser.add_argument("--article-no", required=True)
    parser.add_argument("--article-title", required=True)
    parser.add_argument("--apply", action="store_true", help="Write after all safety checks pass.")
    return parser.parse_args()


def _find_expected_article(args: argparse.Namespace) -> ParsedLawArticle:
    raw_text = LawIngestionService._load_law_text(args.file_path)
    canonical_index = load_article_title_index(args.article_title_index_path)
    parsed = parse_korean_law_articles(raw_text, args.law_name, canonical_index)
    matches = [
        article
        for article in parsed
        if article.article_no == args.article_no and article.article_title == args.article_title
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one parsed article for {args.article_no}({args.article_title}); found {len(matches)}."
        )
    if not matches[0].full_text.strip():
        raise RuntimeError("Parsed article body is empty.")
    return matches[0]


def _summary(article: ParsedLawArticle, *, status: str, article_id: int | None = None) -> dict:
    return {
        "status": status,
        "article_id": article_id,
        "article_no": article.article_no,
        "article_title": article.article_title,
        "source_pages": [article.source_page_start, article.source_page_end],
        "body_length": len(article.full_text),
        "model": settings.embedding_model,
        "expected_dimension": settings.vector_dimension,
    }


def main() -> None:
    args = parse_args()
    source_file = Path(args.file_path)
    if not source_file.is_file():
        raise SystemExit(f"Source file not found: {source_file}")

    parsed = _find_expected_article(args)
    init_db()
    with SessionLocal() as db:
        document = db.get(LawDocument, args.document_id)
        if document is None or document.law_name != args.law_name:
            raise SystemExit("Document ID/law name safety check failed.")
        existing = db.scalar(
            select(LawArticle.id).where(
                LawArticle.law_document_id == document.id,
                LawArticle.article_no == args.article_no,
            )
        )
        if existing is not None:
            print(json.dumps(_summary(parsed, status="already_present", article_id=existing), ensure_ascii=False))
            return
        if not args.apply:
            print(json.dumps(_summary(parsed, status="dry_run_ready"), ensure_ascii=False))
            return

        # EmbeddingService has no mock fallback: absent/failed OpenAI credentials
        # raise and the transaction is rolled back before any partial write commits.
        ingestion = LawIngestionService(db=db, embedding_service=EmbeddingService())
        try:
            article = ingestion.repo.create_law_article(
                law_document_id=document.id,
                article_number=parsed.article_no,
                article_no=parsed.article_no,
                title=parsed.article_title,
                article_title=parsed.article_title,
                chapter=parsed.chapter,
                section=parsed.section,
                full_text=parsed.full_text,
                content=parsed.full_text,
                article_text=parsed.full_text,
                effective_date=parsed.effective_date,
                status=parsed.status,
                source_page_start=parsed.source_page_start,
                source_page_end=parsed.source_page_end,
                version_group_key=parsed.version_group_key,
            )
            ingestion._create_article_chunk_and_embedding(article=article, parsed=parsed)
            embedding = article.embeddings[0]
            if (
                embedding.embedding_model != settings.embedding_model
                or len(embedding.embedding) != settings.vector_dimension
                or embedding.embedding_vector is None
                or len(embedding.embedding_vector) != settings.vector_dimension
            ):
                raise RuntimeError("Embedding verification failed before commit.")
            db.commit()
        except Exception:
            db.rollback()
            raise
        print(json.dumps(_summary(parsed, status="recovered", article_id=article.id), ensure_ascii=False))


if __name__ == "__main__":
    main()
