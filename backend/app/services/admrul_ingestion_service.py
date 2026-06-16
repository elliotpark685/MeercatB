"""고용노동부 표준안전작업지침 ingestion 서비스.

법제처 행정규칙 API에서 문서를 가져와 DB에 저장한다.
- source_category = "safety_standard"
- source_type     = "moel_standard_safety_guideline"
- provider        = "law.go.kr"
"""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import date

from sqlalchemy.orm import Session

from app.models.law_article import LawArticle
from app.models.law_chunk import LawChunk
from app.models.law_document import LawDocument
from app.repositories.law_repository import LawRepository
from app.utils.admrul_api_client import AdmrulApiClient, AdmrulDocument

logger = logging.getLogger(__name__)

SOURCE_CATEGORY = "safety_standard"
SOURCE_TYPE = "moel_standard_safety_guideline"
PROVIDER = "law.go.kr"

# 수집 대상 쿼리 목록
ADMRUL_QUERIES = [
    "표준안전 작업지침",
    "표준안전작업지침",
]


def _parse_date(date_str: str) -> date | None:
    s = re.sub(r"[^0-9]", "", date_str or "")
    if len(s) == 8:
        try:
            return date(int(s[:4]), int(s[4:6]), int(s[6:8]))
        except ValueError:
            pass
    return None


def _version_hash(doc_id: str, name: str) -> str:
    return hashlib.sha256(f"{doc_id}::{name}".encode()).hexdigest()


class AdmrulIngestionService:
    """행정규칙 ingestion 서비스."""

    def __init__(self, db: Session, api_client: AdmrulApiClient) -> None:
        self.db = db
        self.repo = LawRepository(db)
        self.client = api_client

    # ── 퍼블릭 API ───────────────────────────────────────────────────────────

    def ingest_all(self, max_docs: int | None = None) -> dict:
        """모든 대상 쿼리로 행정규칙 수집."""
        seen_ids: set[str] = set()
        all_items: list = []
        for query in ADMRUL_QUERIES:
            items = self.client.search_all(query=query, max_pages=10, display=20)
            for item in items:
                if item.id and item.id not in seen_ids:
                    seen_ids.add(item.id)
                    all_items.append(item)

        if max_docs:
            all_items = all_items[:max_docs]

        stats = {"fetched": len(all_items), "created": 0, "skipped": 0, "failed": 0}
        for item in all_items:
            try:
                created = self._ingest_item(item.id, item.name)
                if created:
                    stats["created"] += 1
                else:
                    stats["skipped"] += 1
            except Exception as exc:
                logger.error("ingest failed for id=%s name=%s: %s", item.id, item.name, exc)
                stats["failed"] += 1

        return stats

    def ingest_by_id(self, doc_id: str) -> bool:
        """특정 ID의 행정규칙 수집."""
        return self._ingest_item(doc_id, "")

    # ── 내부 구현 ─────────────────────────────────────────────────────────────

    def _ingest_item(self, doc_id: str, hint_name: str) -> bool:
        """단일 문서 수집. 이미 있으면 skip. 새로 생성하면 True 반환."""
        admrul_doc = self.client.get_document(doc_id)
        if admrul_doc is None:
            logger.warning("no document returned for id=%s", doc_id)
            return False

        name = admrul_doc.name or hint_name
        if not name:
            logger.warning("empty name for id=%s, skipping", doc_id)
            return False

        vhash = _version_hash(doc_id, name)
        existing = self.repo.get_law_document_by_version_hash(vhash)
        if existing is not None:
            logger.debug("skip duplicate: id=%s name=%s", doc_id, name)
            return False

        law_doc = self._create_law_document(admrul_doc, name, vhash)
        self._create_articles_and_chunks(law_doc, admrul_doc)
        self.db.commit()
        logger.info("ingested: id=%s name=%s articles=%d", doc_id, name, len(admrul_doc.articles))
        return True

    def _create_law_document(
        self, admrul_doc: AdmrulDocument, name: str, vhash: str
    ) -> LawDocument:
        effective_date = _parse_date(admrul_doc.enforcement_date)
        return self.repo.create_law_document(
            title=name,
            law_name=name,
            law_short_name=None,
            law_type="행정규칙",
            law_no=admrul_doc.id,
            effective_date=effective_date,
            jurisdiction="KR",
            version_hash=vhash,
            source_url=f"https://www.law.go.kr/admRulLsInfoP.do?admRulId={admrul_doc.id}",
            raw_text=admrul_doc.raw_text,
            is_active=True,
            source_category=SOURCE_CATEGORY,
            source_type=SOURCE_TYPE,
            provider=PROVIDER,
        )

    def _create_articles_and_chunks(self, law_doc: LawDocument, admrul_doc: AdmrulDocument) -> None:
        if not admrul_doc.articles:
            # 조문이 없으면 전체 본문을 단일 article로 처리
            self._create_single_article(law_doc, admrul_doc)
            return

        for idx, art in enumerate(admrul_doc.articles, start=1):
            article_no = art.article_no or str(idx)
            article = LawArticle(
                law_document_id=law_doc.id,
                article_number=article_no,
                article_no=article_no,
                title=art.title or None,
                article_title=art.title or None,
                chapter=art.chapter or None,
                section=art.section or None,
                article_text=art.content,
                full_text=art.content,
                content=art.content,
                status="effective",
                version_group_key=f"{law_doc.id}::{article_no}",
            )
            self.db.add(article)
            self.db.flush()

            # 청크 생성 (조문 단위)
            self._create_chunk(article, art.content, "article", article_no)

    def _create_single_article(self, law_doc: LawDocument, admrul_doc: AdmrulDocument) -> None:
        text = admrul_doc.raw_text or ""
        article = LawArticle(
            law_document_id=law_doc.id,
            article_number="전문",
            article_no="전문",
            title=admrul_doc.name,
            article_title=admrul_doc.name,
            article_text=text,
            full_text=text,
            content=text,
            status="effective",
            version_group_key=f"{law_doc.id}::전문",
        )
        self.db.add(article)
        self.db.flush()
        # 단락 기준 청킹
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
        if not paragraphs:
            paragraphs = [text] if text else []
        for i, para in enumerate(paragraphs):
            self._create_chunk(article, para, "paragraph", str(i + 1))

    def _create_chunk(
        self,
        article: LawArticle,
        text: str,
        chunk_level: str,
        chunk_no: str,
    ) -> LawChunk:
        chunk = LawChunk(
            law_article_id=article.id,
            chunk_level=chunk_level,
            chunk_no=chunk_no,
            chunk_text=text,
            token_count=len(text.split()),
        )
        self.db.add(chunk)
        self.db.flush()
        return chunk
