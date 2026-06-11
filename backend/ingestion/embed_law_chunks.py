import argparse
import json

from app.core.database import SessionLocal, init_db
from app.services.law_chunking_service import LawChunkingService
from app.services.law_embedding_service import LawEmbeddingService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create law chunks and embeddings for stored law articles.")
    parser.add_argument("--chunk-only", action="store_true", help="Only create law_chunks from law_articles.")
    parser.add_argument("--embed-only", action="store_true", help="Only embed existing law_chunks.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of chunks to embed.")
    parser.add_argument("--model", default="text-embedding-3-small", help="Embedding model name.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    init_db()
    db = SessionLocal()
    try:
        result: dict[str, dict] = {}
        if not args.embed_only:
            result["chunking"] = LawChunkingService(db).chunk_all_articles()
        if not args.chunk_only:
            result["embedding"] = LawEmbeddingService(db=db, model_name=args.model).embed_pending_chunks(limit=args.limit)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
