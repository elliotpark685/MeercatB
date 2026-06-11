import json
import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.law_article import LawArticle
from app.repositories.law_repository import LawRepository

PARAGRAPH_MARK_RE = re.compile(r"([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])")
ITEM_LINE_RE = re.compile(r"^\s*((?:\d+|[가-하])\.)\s*(.+)$")


@dataclass(frozen=True)
class ChunkCandidate:
    chunk_level: str
    chunk_no: str | None
    chunk_text: str
    token_count: int
    metadata_json: str


class LawChunkingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = LawRepository(db)

    def chunk_all_articles(self) -> dict:
        created_count = 0
        skipped_count = 0
        for article in self.repo.list_articles_with_documents():
            result = self.chunk_article(article)
            created_count += result["created_count"]
            skipped_count += result["skipped_count"]
        if self.db is not None:
            self.db.commit()
        return {"created_count": created_count, "skipped_count": skipped_count}

    def chunk_article(self, article: LawArticle) -> dict:
        existing_keys = {
            (chunk.chunk_level, chunk.chunk_no, chunk.chunk_text)
            for chunk in getattr(article, "chunks", [])
        }
        created_count = 0
        skipped_count = 0

        for candidate in self.build_chunk_candidates(article):
            key = (candidate.chunk_level, candidate.chunk_no, candidate.chunk_text)
            if key in existing_keys:
                skipped_count += 1
                continue
            self.repo.create_law_chunk(
                law_article_id=article.id,
                chunk_level=candidate.chunk_level,
                chunk_no=candidate.chunk_no,
                chunk_text=candidate.chunk_text,
                token_count=candidate.token_count,
                metadata_json=candidate.metadata_json,
            )
            existing_keys.add(key)
            created_count += 1

        return {"article_id": article.id, "created_count": created_count, "skipped_count": skipped_count}

    def build_chunk_candidates(self, article: LawArticle) -> list[ChunkCandidate]:
        law_name = self._law_name(article)
        article_no = article.article_no or article.article_number
        article_title = article.article_title or article.title
        article_text = article.article_text or article.full_text or article.content or ""
        metadata = self._metadata(article=article, law_name=law_name, article_no=article_no, article_title=article_title)

        candidates = [
            self._candidate(
                chunk_level="article",
                chunk_no=article_no,
                body=article_text,
                law_name=law_name,
                article_no=article_no,
                article_title=article_title,
                metadata=metadata,
            )
        ]

        for paragraph_no, paragraph_text in self._split_paragraphs(article_text):
            candidates.append(
                self._candidate(
                    chunk_level="paragraph",
                    chunk_no=paragraph_no,
                    body=paragraph_text,
                    law_name=law_name,
                    article_no=article_no,
                    article_title=article_title,
                    metadata={**metadata, "paragraph_no": paragraph_no},
                )
            )
            for item_no, item_text in self._split_items(paragraph_text):
                candidates.append(
                    self._candidate(
                        chunk_level="item",
                        chunk_no=item_no,
                        body=item_text,
                        law_name=law_name,
                        article_no=article_no,
                        article_title=article_title,
                        metadata={**metadata, "paragraph_no": paragraph_no, "item_no": item_no},
                    )
                )

        if len(candidates) == 1:
            for item_no, item_text in self._split_items(article_text):
                candidates.append(
                    self._candidate(
                        chunk_level="item",
                        chunk_no=item_no,
                        body=item_text,
                        law_name=law_name,
                        article_no=article_no,
                        article_title=article_title,
                        metadata={**metadata, "item_no": item_no},
                    )
                )

        return [candidate for candidate in candidates if candidate.chunk_text.strip()]

    @staticmethod
    def _candidate(
        chunk_level: str,
        chunk_no: str | None,
        body: str,
        law_name: str,
        article_no: str,
        article_title: str | None,
        metadata: dict,
    ) -> ChunkCandidate:
        header = f"{law_name} {article_no}"
        if article_title:
            header = f"{header}({article_title})"
        chunk_text = f"{header}\n{body.strip()}".strip()
        return ChunkCandidate(
            chunk_level=chunk_level,
            chunk_no=chunk_no,
            chunk_text=chunk_text,
            token_count=LawChunkingService.count_tokens(chunk_text),
            metadata_json=json.dumps(metadata, ensure_ascii=False, sort_keys=True),
        )

    @staticmethod
    def _metadata(article: LawArticle, law_name: str, article_no: str, article_title: str | None) -> dict:
        return {
            "law_name": law_name,
            "article_no": article_no,
            "article_title": article_title,
            "effective_date": article.effective_date.isoformat() if article.effective_date else None,
        }

    @staticmethod
    def _law_name(article: LawArticle) -> str:
        document = article.law_document
        return document.law_name or document.title

    @staticmethod
    def _split_paragraphs(text: str) -> list[tuple[str, str]]:
        parts = PARAGRAPH_MARK_RE.split(text)
        if len(parts) < 3:
            return []
        paragraphs: list[tuple[str, str]] = []
        prefix = parts[0].strip()
        for index in range(1, len(parts), 2):
            marker = parts[index]
            body = parts[index + 1].strip() if index + 1 < len(parts) else ""
            paragraph_text = f"{marker} {body}".strip()
            if prefix and not paragraphs:
                paragraph_text = f"{prefix}\n{paragraph_text}".strip()
            if body:
                paragraphs.append((marker, paragraph_text))
        return paragraphs

    @staticmethod
    def _split_items(text: str) -> list[tuple[str, str]]:
        items: list[tuple[str, str]] = []
        current_no: str | None = None
        current_lines: list[str] = []

        def flush() -> None:
            nonlocal current_no, current_lines
            if current_no and current_lines:
                items.append((current_no, "\n".join(current_lines).strip()))
            current_no = None
            current_lines = []

        for line in text.splitlines():
            match = ITEM_LINE_RE.match(line)
            if match:
                flush()
                current_no = match.group(1)
                current_lines = [line.strip()]
            elif current_no:
                current_lines.append(line.strip())
        flush()
        return items

    @staticmethod
    def count_tokens(text: str) -> int:
        return len(re.findall(r"[A-Za-z0-9_가-힣]+|[^\s]", text))
