import argparse
import json

from app.core.database import SessionLocal, init_db
from app.services.embedding_service import EmbeddingService
from app.services.law_ingestion_service import LawIngestionService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest Korean law file into DB.")
    parser.add_argument("--file-path", required=True, help="Path to PDF/TXT law file.")
    parser.add_argument(
        "--article-title-index-path",
        required=False,
        default=None,
        help="Optional path to article-title canonical TXT index.",
    )
    parser.add_argument("--law-name", required=True, help="Law name (e.g., 산업안전보건법).")
    parser.add_argument("--law-type", required=False, default=None, help="Law type (e.g., 법률, 시행규칙).")
    parser.add_argument("--law-no", required=False, default=None, help="Law number (e.g., 제21065호).")
    parser.add_argument(
        "--effective-date",
        required=False,
        default=None,
        help="Document-level effective date in YYYY-MM-DD.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    init_db()
    db = SessionLocal()
    try:
        service = LawIngestionService(db=db, embedding_service=EmbeddingService())
        summary = service.ingest_file(
            file_path=args.file_path,
            law_name=args.law_name,
            law_type=args.law_type,
            law_no=args.law_no,
            effective_date=args.effective_date,
            article_title_index_path=args.article_title_index_path,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
