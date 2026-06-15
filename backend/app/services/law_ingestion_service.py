from dataclasses import dataclass
from datetime import date
import hashlib
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.repositories.law_repository import LawRepository
from app.services.embedding_service import EmbeddingService
from app.utils.article_title_index_loader import load_article_title_index
from app.utils.embedding_text_builder import build_law_embedding_text
from app.utils.law_parser import parse_korean_law_articles
from app.utils.pdf_loader import load_pdf_text_with_page_markers
from app.utils.text_loader import load_text_file


@dataclass
class LawSourceArticle:
    article_no: str
    article_title: str | None
    article_text: str
    chapter: str | None = None
    section: str | None = None
    effective_date: str | None = None
    status: str = "effective"


@dataclass
class LawSourceDocument:
    law_name: str
    law_short_name: str | None = None
    law_type: str | None = None
    law_no: str | None = None
    source_url: str | None = None
    source_file_path: str | None = None
    effective_date: str | None = None
    amendment_date: str | None = None
    raw_text: str | None = None
    articles: list[LawSourceArticle] | None = None


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
        amendment_date: str | None = None,
        source_url: str | None = None,
        law_short_name: str | None = None,
        article_title_index_path: str | None = None,
    ) -> dict:
        text = self._load_law_text(file_path)
        canonical_article_index = (
            load_article_title_index(article_title_index_path) if article_title_index_path else None
        )
        return self.ingest_source_document(
            LawSourceDocument(
                law_name=law_name,
                law_short_name=law_short_name,
                law_type=law_type,
                law_no=law_no,
                source_url=source_url,
                source_file_path=file_path,
                effective_date=effective_date,
                amendment_date=amendment_date,
                raw_text=text,
            ),
            canonical_article_index=canonical_article_index,
        )

    def ingest_source_document(
        self,
        source: LawSourceDocument,
        canonical_article_index=None,
    ) -> dict:
        if not source.raw_text and not source.articles:
            raise ValueError(f"No raw text or articles supplied for {source.law_name}")

        raw_text = source.raw_text or self._join_source_articles(source.articles or [])
        version_hash = self._build_version_hash(source=source, raw_text=raw_text)
        existing_document = self._get_existing_document(version_hash)
        if existing_document is not None:
            return {
                "law_name": source.law_name,
                "document_id": existing_document.id,
                "version_hash": version_hash,
                "status": "skipped_duplicate",
                "total_articles": 0,
                "effective_count": 0,
                "scheduled_count": 0,
                "unknown_count": 0,
            }

        parsed_document_effective_date = self._parse_date(source.effective_date)
        parsed_amendment_date = self._parse_date(source.amendment_date)

        law_document = self.repo.create_law_document(
            title=source.law_name,
            law_name=source.law_name,
            law_short_name=source.law_short_name,
            law_type=source.law_type,
            law_no=source.law_no,
            effective_date=parsed_document_effective_date,
            amendment_date=parsed_amendment_date,
            source_url=source.source_url,
            source_file_path=source.source_file_path,
            raw_text=raw_text,
            jurisdiction="KR",
            version_hash=version_hash,
            is_active=True,
        )
        self.repo.deactivate_other_documents(law_name=source.law_name, keep_document_id=law_document.id)

        if source.articles:
            parsed_articles = self._source_articles_to_parsed(
                source=source,
                default_effective_date=parsed_document_effective_date,
            )
            canonical_article_numbers: list[str] = []
        else:
            parsed_articles = parse_korean_law_articles(
                text=raw_text,
                law_name=source.law_name,
                canonical_article_index=canonical_article_index,
                default_effective_date=parsed_document_effective_date,
            )
            canonical_article_numbers = [item.article_no for item in (canonical_article_index or [])]
        effective_count = 0
        scheduled_count = 0
        unknown_count = 0

        for parsed in parsed_articles:
            article = self.repo.create_law_article(
                law_document_id=law_document.id,
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

            self._create_article_chunk_and_embedding(article=article, parsed=parsed)

            if parsed.status == "effective":
                effective_count += 1
            elif parsed.status == "scheduled":
                scheduled_count += 1
            else:
                unknown_count += 1

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
            "law_name": source.law_name,
            "document_id": law_document.id,
            "version_hash": version_hash,
            "status": "ingested",
            "total_articles": len(parsed_articles),
            "canonical_article_count": len(canonical_article_numbers),
            "parsed_article_count": len(parsed_articles),
            "missing_from_pdf": missing_from_pdf,
            "extra_detected_articles": extra_detected_articles,
            "effective_count": effective_count,
            "scheduled_count": scheduled_count,
            "unknown_count": unknown_count,
        }

    def _create_article_chunk_and_embedding(self, article, parsed) -> None:
        embedding_text = build_law_embedding_text(parsed)
        embedding_vector = self.embedding_service.generate_embedding(embedding_text)
        chunk = None
        if hasattr(self.repo, "create_law_chunk"):
            chunk = None
            chunk = self.repo.create_law_chunk(
                law_article_id=article.id,
                chunk_level="article",
                chunk_no=parsed.article_no,
                chunk_text=parsed.full_text,
                token_count=len(parsed.full_text.split()),
                metadata_json=None,
            )
        self.repo.create_law_embedding(
            article_id=article.id,
            chunk_id=chunk.id if chunk else None,
            embedding_model=self.embedding_service.model_name,
            embedding=embedding_vector,
            embedding_vector=embedding_vector,
        )

    def _get_existing_document(self, version_hash: str):
        if hasattr(self.repo, "get_law_document_by_version_hash"):
            return self.repo.get_law_document_by_version_hash(version_hash)
        return None

    @staticmethod
    def _load_law_text(file_path: str) -> str:
        suffix = Path(file_path).suffix.lower()
        if suffix == ".pdf":
            return load_pdf_text_with_page_markers(file_path)
        if suffix == ".txt":
            return load_text_file(file_path)
        raise ValueError(f"Unsupported file extension: {suffix}")

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        if not value:
            return None
        normalized = value.strip().replace(".", "-")
        if len(normalized) == 8 and normalized.isdigit():
            normalized = f"{normalized[:4]}-{normalized[4:6]}-{normalized[6:]}"
        return date.fromisoformat(normalized.strip("-"))

    @staticmethod
    def _build_version_hash(source: LawSourceDocument, raw_text: str) -> str:
        payload = {
            "law_name": source.law_name,
            "law_short_name": source.law_short_name,
            "law_type": source.law_type,
            "law_no": source.law_no,
            "effective_date": source.effective_date,
            "amendment_date": source.amendment_date,
            "raw_text": raw_text,
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _join_source_articles(articles: list[LawSourceArticle]) -> str:
        return "\n\n".join(
            [
                f"{article.article_no}"
                f"{f'({article.article_title})' if article.article_title else ''}\n"
                f"{article.article_text}"
                for article in articles
            ]
        )

    @staticmethod
    def _source_articles_to_parsed(source: LawSourceDocument, default_effective_date: date | None):
        parsed_items = []
        for article in source.articles or []:
            effective_date = LawIngestionService._parse_date(article.effective_date) or default_effective_date
            parsed_items.append(
                type(
                    "ParsedLawArticleLike",
                    (),
                    {
                        "law_name": source.law_name,
                        "article_no": article.article_no,
                        "article_title": article.article_title,
                        "chapter": article.chapter,
                        "section": article.section,
                        "full_text": article.article_text,
                        "effective_date": effective_date,
                        "status": article.status,
                        "source_page_start": None,
                        "source_page_end": None,
                        "version_group_key": f"{source.law_name}_{article.article_no}",
                    },
                )()
            )
        return parsed_items
