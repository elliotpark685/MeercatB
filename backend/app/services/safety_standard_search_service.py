"""안전기준 검색 서비스.

기존 LawSearchService의 청크 기반 하이브리드 검색 로직을 재사용하되,
source_category = 'safety_standard' 인 문서만 검색한다.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.law_article import LawArticle
from app.models.law_chunk import LawChunk
from app.models.law_document import LawDocument
from app.models.law_embedding import LawEmbedding
from app.repositories.law_repository import LawRepository, SAFETY_STANDARD_CATEGORY
from app.schemas.safety_standard import SafetyStandardResultItem, SafetyStandardSearchResponse
from app.services.law_embedding_service import LawEmbeddingService

# 검색 대상 source_type 목록
RULE_SOURCE_TYPE = "rule"
GUIDELINE_SOURCE_TYPE = "moel_standard_safety_guideline"

# 산업안전보건기준에 관한 규칙 법령 이름 (DB 저장값 패턴)
RULE_LAW_NAMES = ["산업안전보건기준에 관한 규칙", "산업안전보건기준"]


@dataclass
class _Candidate:
    chunk: LawChunk | None
    article: LawArticle
    document: LawDocument
    embedding: LawEmbedding | None
    keyword_score: float = 0.0
    vector_score: float = 0.0
    score: float = 0.0
    matched_reason: list[str] | None = None


class SafetyStandardSearchService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = LawRepository(db)

    def search(
        self,
        query: str,
        top_k: int = 5,
        source_types: list[str] | None = None,
        user_id: int | None = None,
        site_id: int | None = None,
    ) -> SafetyStandardSearchResponse:
        # source_types 미지정이면 전체 안전기준 검색
        effective_types = source_types or None

        keywords = _expand_query_keywords(query)

        # 청크 기반 검색 시도
        row_map: dict[int, _Candidate] = {}

        keyword_rows = self.repo.search_chunks_by_keyword_for_category(
            keywords=keywords,
            source_category=SAFETY_STANDARD_CATEGORY,
            source_types=effective_types,
            limit=max(top_k * 20, 100),
        )
        for chunk, article, document, embedding in keyword_rows:
            row_map[chunk.id] = _Candidate(
                chunk=chunk, article=article, document=document, embedding=embedding
            )

        vector_rows = self.repo.list_chunks_for_category(
            source_category=SAFETY_STANDARD_CATEGORY,
            source_types=effective_types,
            limit=500,
        )
        query_vector = (
            _query_embedding(query)
            if any(row[3] is not None for row in vector_rows)
            else []
        )
        for chunk, article, document, embedding in vector_rows:
            candidate = row_map.setdefault(
                chunk.id,
                _Candidate(chunk=chunk, article=article, document=document, embedding=embedding),
            )
            if embedding is not None and query_vector:
                candidate.vector_score = max(
                    candidate.vector_score,
                    _cosine_similarity(query_vector, embedding.embedding),
                )

        # 점수 계산 + 정렬
        candidates = list(row_map.values())
        _rerank(query=query, candidates=candidates)
        top_candidates = candidates[:top_k]

        # 결과 없으면 article 레벨 fallback
        if not top_candidates:
            top_candidates = self._fallback_article_search(
                query=query, keywords=keywords, top_k=top_k, source_types=effective_types
            )

        results = [_to_result(c) for c in top_candidates]
        return SafetyStandardSearchResponse(query=query, results=results)

    def _fallback_article_search(
        self,
        query: str,
        keywords: list[str],
        top_k: int,
        source_types: list[str] | None,
    ) -> list[_Candidate]:
        row_map: dict[int, tuple[LawArticle, LawDocument]] = {}
        for kw in keywords:
            rows = self.repo.search_by_keyword_for_category(
                keyword=kw,
                source_category=SAFETY_STANDARD_CATEGORY,
                source_types=source_types,
                top_k=max(top_k * 5, 20),
            )
            for article, document in rows:
                row_map[article.id] = (article, document)

        candidates = [
            _Candidate(chunk=None, article=a, document=d, embedding=None)
            for a, d in row_map.values()
        ]
        _rerank(query=query, candidates=candidates)
        return candidates[:top_k]


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────


def _rerank(query: str, candidates: list[_Candidate]) -> None:
    query_terms = _tokenize(query)
    for c in candidates:
        text = c.chunk.chunk_text if c.chunk else (c.article.article_text or "")
        title = c.article.article_title or c.article.title or ""
        keyword_hits = sum(1 for t in query_terms if t in text)
        keyword_score = keyword_hits / max(len(query_terms), 1)
        title_score = 0.4 if title and any(t in title for t in query_terms) else 0.0
        reasons: list[str] = []
        if keyword_hits:
            reasons.append(f"keyword:{keyword_hits}")
        if title_score:
            reasons.append("article_title")
        if c.vector_score:
            reasons.append("vector")
        c.keyword_score = round(keyword_score + title_score, 4)
        c.score = round((c.keyword_score * 0.7) + (c.vector_score * 0.3), 4)
        c.matched_reason = reasons
    candidates.sort(key=lambda x: x.score, reverse=True)


def _to_result(c: _Candidate) -> SafetyStandardResultItem:
    doc = c.document
    source_type = doc.source_type or ""
    source_name = doc.law_name or doc.title
    provider = doc.provider or "law.go.kr"
    article_no = c.article.article_no or c.article.article_number or None
    article_title = c.article.article_title or c.article.title or None
    content = (
        c.chunk.chunk_text
        if c.chunk
        else (c.article.article_text or c.article.full_text or c.article.content or "")
    )
    return SafetyStandardResultItem(
        source_type=source_type,
        source_name=source_name,
        article_no=article_no,
        article_title=article_title,
        content=content,
        score=c.score,
        provider=provider,
        article_id=c.article.id,
        chunk_id=c.chunk.id if c.chunk else None,
        matched_reason=c.matched_reason or [],
    )


def _query_embedding(query: str) -> list[float]:
    return LawEmbeddingService(db=None).generate_embedding(query)  # type: ignore[arg-type]


def _expand_query_keywords(query: str) -> list[str]:
    normalized = " ".join(query.split()).strip()
    if not normalized:
        return [query]
    variants = [normalized]
    compact = normalized.replace(" ", "")
    if compact != normalized:
        variants.append(compact)
    seen: set[str] = set()
    result: list[str] = []
    for candidate in variants:
        for token in re.split(r"\s+", candidate.strip()):
            if len(token) >= 2 and token not in seen:
                seen.add(token)
                result.append(token)
    return result or [normalized]


def _tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[\s,.;:()\[\]{}]+", text.strip()) if len(t) >= 2]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    size = min(len(left), len(right))
    if size == 0:
        return 0.0
    a, b = left[:size], right[:size]
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return max(0.0, dot / (norm_a * norm_b))
