from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from app.repositories.law_repository import LawRepository
from app.services.embedding_service import EmbeddingService
from app.utils.article_title_index_loader import load_article_title_index
from app.utils.embedding_text_builder import build_law_embedding_text
from app.utils.law_parser import parse_korean_law_articles
from app.utils.pdf_loader import load_pdf_text_with_page_markers
from app.utils.text_loader import load_text_file


class LawIngestionService:
    """Ingest Korean law documents from PDF/TXT and store articles + embeddings."""

    def __init__(self, db: Session, embedding_service: EmbeddingService) -> None:
        self.db = db
        self.embedding_service = embedding_service
        self.repo = LawRepository(db)

    def ingest_file(
        self,
        file_path: str,
        law_name: str,
        law_type: str | None = None,
        law_no: str | None = None,
        effective_date: str | None = None,
        article_title_index_path: str | None = None,
    ) -> dict:
        text = self._load_law_text(file_path)
        parsed_document_effective_date = date.fromisoformat(effective_date) if effective_date else None
        canonical_article_index = (
            load_article_title_index(article_title_index_path) if article_title_index_path else None
        )

        law_document = self.repo.create_law_document(
            title=law_name,
            law_type=law_type,
            law_no=law_no,
            effective_date=parsed_document_effective_date,
            source_file_path=file_path,
            raw_text=text,
            jurisdiction="KR",
        )

        parsed_articles = parse_korean_law_articles(
            text=text,
            law_name=law_name,
            canonical_article_index=canonical_article_index,
            default_effective_date=parsed_document_effective_date,
        )
        effective_count = 0
        scheduled_count = 0
        unknown_count = 0

        for parsed in parsed_articles:
            article = self.repo.create_law_article(
                law_document_id=law_document.id,
                article_number=parsed.article_no,
                title=parsed.article_title,
                chapter=parsed.chapter,
                section=parsed.section,
                full_text=parsed.full_text,
                content=parsed.full_text,
                effective_date=parsed.effective_date,
                status=parsed.status,
                source_page_start=parsed.source_page_start,
                source_page_end=parsed.source_page_end,
                version_group_key=parsed.version_group_key,
            )

            embedding_text = build_law_embedding_text(parsed)
            embedding_vector = self.embedding_service.generate_embedding(embedding_text)
            self.repo.create_law_embedding(
                article_id=article.id,
                embedding_model=self.embedding_service.model_name,
                embedding=embedding_vector,
            )

            if parsed.status == "effective":
                effective_count += 1
            elif parsed.status == "scheduled":
                scheduled_count += 1
            else:
                unknown_count += 1

        canonical_article_numbers = [item.article_no for item in (canonical_article_index or [])]
        parsed_article_numbers = [item.article_no for item in parsed_articles]
        missing_from_pdf = [
            article_no for article_no in canonical_article_numbers if article_no not in parsed_article_numbers
        ]
        extra_detected_articles = [
            article_no
            for article_no in parsed_article_numbers
            if canonical_article_numbers and article_no not in canonical_article_numbers
        ]

        self.db.commit()
        return {
            "document_id": law_document.id,
            "total_articles": len(parsed_articles),
            "canonical_article_count": len(canonical_article_numbers),
            "parsed_article_count": len(parsed_articles),
            "missing_from_pdf": missing_from_pdf,
            "extra_detected_articles": extra_detected_articles,
            "effective_count": effective_count,
            "scheduled_count": scheduled_count,
            "unknown_count": unknown_count,
        }

    @staticmethod
    def _load_law_text(file_path: str) -> str:
        suffix = Path(file_path).suffix.lower()
        if suffix == ".pdf":
            return load_pdf_text_with_page_markers(file_path)
        if suffix == ".txt":
            return load_text_file(file_path)
        raise ValueError(f"Unsupported file extension: {suffix}")
