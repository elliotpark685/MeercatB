from dataclasses import dataclass
import json
import math
import re
from typing import Protocol

from sqlalchemy.orm import Session

from app.models.law_article import LawArticle
from app.models.law_chunk import LawChunk
from app.models.law_document import LawDocument
from app.models.law_embedding import LawEmbedding
from app.repositories.law_repository import LawRepository
from app.schemas.law import (
    CitationItem,
    LawArticleDetailResponse,
    LawSearchResponse,
    LawSearchResultItem,
    RawHitItem,
)
from app.services.law_embedding_service import LawEmbeddingService
from app.services.law_validation_service import LawValidationService
from app.services.query_analyzer import QueryAnalysis, QueryAnalyzer


DEFAULT_LAW_SCOPE = [
    "산업안전보건법",
    "시설물의 안전 및 유지관리에 관한 특별법",
    "건설산업기본법",
    "건설기술 진흥법",
    "중대재해 처벌 등에 관한 법률",
]


@dataclass
class ScoredArticle:
    article: LawArticle
    document: LawDocument
    score: float
    matched_reason: list[str]


@dataclass
class SearchCandidate:
    chunk: LawChunk | None
    article: LawArticle
    document: LawDocument
    embedding: LawEmbedding | None
    keyword_score: float = 0.0
    vector_score: float = 0.0
    score: float = 0.0
    matched_reason: list[str] | None = None


class Reranker(Protocol):
    def rerank(self, query: str, candidates: list[SearchCandidate], law_scope: list[str]) -> list[SearchCandidate]:
        ...


class DeterministicLawReranker:
    def rerank(self, query: str, candidates: list[SearchCandidate], law_scope: list[str]) -> list[SearchCandidate]:
        query_compact = query.replace(" ", "")
        query_terms = _tokenize(query)
        scoped_names = [item.replace(" ", "") for item in law_scope]
        for candidate in candidates:
            reasons: list[str] = []
            law_name = _document_name(candidate.document)
            law_names = " ".join(
                [
                    candidate.document.law_name or "",
                    candidate.document.law_short_name or "",
                    candidate.document.title or "",
                ]
            )
            article_title = _article_title(candidate.article) or ""
            chunk_text = _candidate_text(candidate)

            keyword_hits = sum(1 for term in query_terms if term in chunk_text)
            keyword_score = keyword_hits / max(len(query_terms), 1)
            title_score = 0.4 if article_title and any(term in article_title for term in query_terms) else 0.0
            law_name_score = 0.5 if any(name and name in law_names.replace(" ", "") for name in scoped_names) else 0.0
            query_law_bonus = 0.5 if law_name.replace(" ", "") in query_compact else 0.0

            if keyword_hits:
                reasons.append(f"keyword:{keyword_hits}")
            if title_score:
                reasons.append("article_title")
            if law_name_score:
                reasons.append("law_scope")
            if query_law_bonus:
                reasons.append("law_name_query")
            if candidate.vector_score:
                reasons.append("vector")

            candidate.keyword_score = round(keyword_score + title_score + law_name_score + query_law_bonus, 4)
            candidate.score = round((candidate.keyword_score * 0.7) + (candidate.vector_score * 0.3), 4)
            candidate.matched_reason = reasons

        candidates.sort(key=lambda item: item.score, reverse=True)
        return candidates


class LawSearchService:
    def __init__(
        self,
        db: Session,
        law_validation_service: LawValidationService | None = None,
        reranker: Reranker | None = None,
    ) -> None:
        self.db = db
        self.repo = LawRepository(db)
        self.query_analyzer = QueryAnalyzer()
        self.law_validation_service = law_validation_service or LawValidationService()
        self.reranker = reranker or DeterministicLawReranker()

    def search(
        self,
        query: str,
        top_k: int = 5,
        validate_latest: bool = False,
        user_id: int | None = None,
        site_id: int | None = None,
        law_names: list[str] | None = None,
        law_scope: list[str] | str | None = None,
    ) -> LawSearchResponse:
        normalized_scope = self._normalize_law_scope(law_names=law_names, law_scope=law_scope)

        if hasattr(self.repo, "search_chunks_by_keyword") and hasattr(self.repo, "list_chunks_for_scope"):
            response = self._search_chunks(query=query, top_k=top_k, law_scope=normalized_scope)
            if not response.results:
                response = self._search_articles(query=query, top_k=top_k, law_scope=normalized_scope)
        else:
            response = self._search_articles(query=query, top_k=top_k, law_scope=normalized_scope)

        if validate_latest:
            response.answer = self.law_validation_service.validate_latest(
                [citation.model_dump() for citation in response.citations]
            )

        self._log_search(
            query=query,
            user_id=user_id,
            site_id=site_id,
            law_scope=normalized_scope,
            top_k=top_k,
            result_count=len(response.results or response.citations),
        )
        return response

    def _search_chunks(self, query: str, top_k: int, law_scope: list[str]) -> LawSearchResponse:
        keywords = self._expand_query_keywords(query)
        row_map: dict[int, SearchCandidate] = {}

        keyword_rows = self.repo.search_chunks_by_keyword(
            keywords=keywords,
            law_scope=law_scope,
            limit=max(top_k * 20, 100),
        )
        for chunk, article, document, embedding in keyword_rows:
            row_map[chunk.id] = SearchCandidate(chunk=chunk, article=article, document=document, embedding=embedding)

        vector_rows = self.repo.list_chunks_for_scope(law_scope=law_scope, limit=500)
        query_vector = self._query_embedding(query) if any(row[3] is not None for row in vector_rows) else []
        for chunk, article, document, embedding in vector_rows:
            candidate = row_map.setdefault(
                chunk.id,
                SearchCandidate(chunk=chunk, article=article, document=document, embedding=embedding),
            )
            if embedding is not None and query_vector:
                candidate.vector_score = max(candidate.vector_score, _cosine_similarity(query_vector, embedding.embedding))

        candidates = self.reranker.rerank(query=query, candidates=list(row_map.values()), law_scope=law_scope)
        top_candidates = candidates[:top_k]
        results = [self._candidate_to_result(candidate) for candidate in top_candidates]
        citations = [self._candidate_to_citation(candidate) for candidate in top_candidates]
        raw_hits = [
            RawHitItem(
                article_id=candidate.article.id,
                score=candidate.score,
                matched_reason=candidate.matched_reason or [],
            )
            for candidate in top_candidates
        ]
        return LawSearchResponse(
            query=query,
            answer=self._build_answer(citations),
            citations=citations,
            raw_hits=raw_hits,
            results=results,
        )

    def _search_articles(self, query: str, top_k: int, law_scope: list[str]) -> LawSearchResponse:
        analysis = self.query_analyzer.analyze(query)
        expanded_keywords = self._expand_query_keywords(query)

        row_map: dict[int, tuple[LawArticle, LawDocument]] = {}
        for keyword in expanded_keywords:
            try:
                rows = self.repo.search_by_keyword(keyword=keyword, top_k=max(top_k * 5, top_k), law_scope=law_scope)
            except TypeError:
                rows = self.repo.search_by_keyword(keyword=keyword, top_k=max(top_k * 5, top_k))
            for article, document in rows:
                row_map[article.id] = (article, document)

        rows = list(row_map.values())
        scored = [self._score_article(article, document, analysis) for article, document in rows]
        scored.sort(key=lambda item: item.score, reverse=True)
        top_scored = scored[:top_k]
        citations = [self._to_citation(item) for item in top_scored]
        raw_hits = [
            RawHitItem(article_id=item.article.id, score=item.score, matched_reason=item.matched_reason)
            for item in top_scored
        ]
        results = [self._article_to_result(item) for item in top_scored]
        return LawSearchResponse(
            query=query,
            answer=self._build_answer(citations),
            citations=citations,
            raw_hits=raw_hits,
            results=results,
        )

    def _log_search(
        self,
        query: str,
        user_id: int | None,
        site_id: int | None,
        law_scope: list[str],
        top_k: int,
        result_count: int,
    ) -> None:
        if not hasattr(self.repo, "create_law_search_log"):
            return
        self.repo.create_law_search_log(
            query=query,
            user_id=user_id,
            site_id=site_id,
            law_scope=json.dumps(law_scope, ensure_ascii=False),
            top_k=top_k,
            result_count=result_count,
        )
        if self.db is not None:
            self.db.commit()

    def get_article_detail(self, article_id: int) -> LawArticleDetailResponse | None:
        row = self.repo.get_article_with_document(article_id)
        if row is None:
            return None
        article, document = row
        return LawArticleDetailResponse(
            article_id=article.id,
            law_document_id=article.law_document_id,
            law_name=_document_name(document),
            article_no=_article_no(article),
            article_title=_article_title(article),
            chapter=article.chapter,
            section=article.section,
            full_text=_article_text(article),
            status=article.status,
            effective_date=article.effective_date.isoformat() if article.effective_date else None,
            source_page_start=article.source_page_start,
            source_page_end=article.source_page_end,
            law_type=document.law_type,
            law_no=document.law_no,
            document_effective_date=document.effective_date.isoformat() if document.effective_date else None,
            source_file_path=document.source_file_path,
        )

    def _score_article(self, article: LawArticle, document: LawDocument, analysis: QueryAnalysis) -> ScoredArticle:
        score = 1.0
        matched_reason: list[str] = []
        haystack = " ".join(
            [
                document.law_name or "",
                document.law_short_name or "",
                document.title or "",
                article.chapter or "",
                article.section or "",
                _article_title(article) or "",
                _article_text(article),
            ]
        )

        document_names = " ".join([document.law_name or "", document.law_short_name or "", document.title or ""])
        if analysis.law_name != "unknown" and analysis.law_name in document_names:
            score += 1.0
            matched_reason.append(f"law_name:{analysis.law_name}")

        for work_type in analysis.work_types:
            if work_type in haystack:
                score += 0.35
                matched_reason.append(f"work_type:{work_type}")

        for risk_type in analysis.risk_types:
            if risk_type in haystack:
                score += 0.5
                matched_reason.append(f"risk_type:{risk_type}")

        for action_type in analysis.action_types:
            if action_type in haystack:
                score += 0.25
                matched_reason.append(f"action_type:{action_type}")

        if article.status == "effective":
            score += 0.3
            matched_reason.append("status:effective_boost")
        elif article.status == "scheduled":
            score -= 0.2
            matched_reason.append("status:scheduled_penalty")

        return ScoredArticle(
            article=article,
            document=document,
            score=round(score, 4),
            matched_reason=matched_reason,
        )

    @staticmethod
    def _normalize_law_scope(law_names: list[str] | None, law_scope: list[str] | str | None) -> list[str]:
        raw_scope: list[str]
        if law_names:
            raw_scope = law_names
        elif isinstance(law_scope, str):
            raw_scope = [law_scope]
        elif law_scope:
            raw_scope = list(law_scope)
        else:
            raw_scope = DEFAULT_LAW_SCOPE

        seen: set[str] = set()
        normalized: list[str] = []
        for item in raw_scope:
            value = item.strip()
            if not value or value in seen:
                continue
            seen.add(value)
            normalized.append(value)
        return normalized or DEFAULT_LAW_SCOPE

    @staticmethod
    def _query_embedding(query: str) -> list[float]:
        return LawEmbeddingService(db=None).generate_embedding(query)  # type: ignore[arg-type]

    @staticmethod
    def _candidate_to_result(candidate: SearchCandidate) -> LawSearchResultItem:
        effective_date = candidate.article.effective_date or candidate.document.effective_date
        return LawSearchResultItem(
            law_name=_document_name(candidate.document),
            article_no=_article_no(candidate.article),
            article_title=_article_title(candidate.article),
            chunk_text=_candidate_text(candidate),
            score=candidate.score,
            source_url=candidate.document.source_url,
            effective_date=effective_date.isoformat() if effective_date else None,
            document_effective_date=(
                candidate.document.effective_date.isoformat() if candidate.document.effective_date else None
            ),
            article_id=candidate.article.id,
            chunk_id=candidate.chunk.id if candidate.chunk else None,
            matched_reason=candidate.matched_reason or [],
        )

    @staticmethod
    def _candidate_to_citation(candidate: SearchCandidate) -> CitationItem:
        effective_date = candidate.article.effective_date or candidate.document.effective_date
        return CitationItem(
            article_id=candidate.article.id,
            law_name=_document_name(candidate.document),
            article_no=_article_no(candidate.article),
            article_title=_article_title(candidate.article),
            chapter=candidate.article.chapter,
            section=candidate.article.section,
            status=candidate.article.status,
            effective_date=effective_date.isoformat() if effective_date else None,
            source_page_start=candidate.article.source_page_start,
            source_page_end=candidate.article.source_page_end,
        )

    @staticmethod
    def _article_to_result(item: ScoredArticle) -> LawSearchResultItem:
        effective_date = item.article.effective_date or item.document.effective_date
        return LawSearchResultItem(
            law_name=_document_name(item.document),
            article_no=_article_no(item.article),
            article_title=_article_title(item.article),
            chunk_text=_article_text(item.article),
            score=item.score,
            source_url=item.document.source_url,
            effective_date=effective_date.isoformat() if effective_date else None,
            document_effective_date=(
                item.document.effective_date.isoformat() if item.document.effective_date else None
            ),
            article_id=item.article.id,
            chunk_id=None,
            matched_reason=item.matched_reason,
        )

    @staticmethod
    def _to_citation(item: ScoredArticle) -> CitationItem:
        effective_date = item.article.effective_date or item.document.effective_date
        return CitationItem(
            article_id=item.article.id,
            law_name=_document_name(item.document),
            article_no=_article_no(item.article),
            article_title=_article_title(item.article),
            chapter=item.article.chapter,
            section=item.article.section,
            status=item.article.status,
            effective_date=effective_date.isoformat() if effective_date else None,
            source_page_start=item.article.source_page_start,
            source_page_end=item.article.source_page_end,
        )

    @staticmethod
    def _build_answer(citations: list[CitationItem]) -> str:
        if not citations:
            return "관련 법령 조문을 찾지 못했습니다. 검색어를 구체화해 주세요."

        first = citations[0]
        return (
            f"주요 근거 조문은 {first.law_name} {first.article_no}"
            f"{f'({first.article_title})' if first.article_title else ''} 입니다. "
            "아래 인용 조문을 확인해 작업 계획에 반영하세요."
        )

    @staticmethod
    def _expand_query_keywords(query: str) -> list[str]:
        normalized = " ".join(query.split()).strip()
        if not normalized:
            return [query]

        variants = [normalized]
        compact = normalized.replace(" ", "")
        if compact != normalized:
            variants.append(compact)

        suffixes = ["방지", "안전", "조치", "점검", "작업", "관리", "계획"]
        for suffix in suffixes:
            if compact.endswith(suffix) and len(compact) > len(suffix):
                head = compact[: -len(suffix)]
                variants.extend([f"{head} {suffix}", head, suffix])

        seen: set[str] = set()
        result: list[str] = []
        for candidate in variants:
            for token in re.split(r"\s+", candidate.strip()):
                if len(token) < 2:
                    continue
                if token in seen:
                    continue
                seen.add(token)
                result.append(token)

        return result or [normalized]


def _document_name(document: LawDocument) -> str:
    return document.law_name or document.title


def _article_no(article: LawArticle) -> str:
    return article.article_no or article.article_number


def _article_title(article: LawArticle) -> str | None:
    return article.article_title or article.title


def _article_text(article: LawArticle) -> str:
    return article.article_text or article.full_text or article.content or ""


def _candidate_text(candidate: SearchCandidate) -> str:
    return candidate.chunk.chunk_text if candidate.chunk is not None else _article_text(candidate.article)


def _tokenize(text: str) -> list[str]:
    return [token for token in re.split(r"[\s,.;:()\[\]{}]+", text.strip()) if len(token) >= 2]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    size = min(len(left), len(right))
    if size == 0:
        return 0.0
    left_slice = left[:size]
    right_slice = right[:size]
    dot = sum(a * b for a, b in zip(left_slice, right_slice))
    left_norm = math.sqrt(sum(a * a for a in left_slice))
    right_norm = math.sqrt(sum(b * b for b in right_slice))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return max(0.0, dot / (left_norm * right_norm))
