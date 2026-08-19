"""Evaluation runner that calls the production retriever, not a test retriever."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.law_article import LawArticle
from app.models.law_chunk import LawChunk
from app.models.law_document import LawDocument
from app.models.law_embedding import LawEmbedding
from app.services.law_search_service import LawSearchService, _has_keyword_match
from evaluation.metrics import summarize


@dataclass(frozen=True)
class EvaluationConfig:
    top_k: int = 5
    law_scope: list[str] | None = None


@dataclass(frozen=True)
class DatasetValidationIssue:
    dataset_id: int
    reason: str


def validate_scoped_dataset(db: Session, dataset: list[dict[str, Any]], scope: str) -> list[DatasetValidationIssue]:
    """Validate ground truth and its retrievable pgvector representation."""
    issues: list[DatasetValidationIssue] = []
    for item in dataset:
        expected_id = item.get("expected_article_id")
        if not expected_id:
            issues.append(DatasetValidationIssue(item["id"], "expected_article_id_missing"))
            continue

        row = db.execute(
            select(
                LawArticle.id,
                func.count(func.distinct(LawChunk.id)).label("chunk_count"),
                func.count(func.distinct(LawEmbedding.id)).label("embedding_count"),
            )
            .join(LawDocument, LawDocument.id == LawArticle.law_document_id)
            .outerjoin(LawChunk, LawChunk.law_article_id == LawArticle.id)
            .outerjoin(
                LawEmbedding,
                and_(
                    LawEmbedding.chunk_id == LawChunk.id,
                    LawEmbedding.embedding_model == settings.embedding_model,
                    LawEmbedding.embedding_vector.is_not(None),
                ),
            )
            .where(
                LawArticle.id == expected_id,
                LawDocument.law_name == scope,
                LawDocument.is_active.is_(True),
                LawArticle.article_no == item["expected_article"],
            )
            .group_by(LawArticle.id)
        ).one_or_none()
        if row is None:
            issues.append(DatasetValidationIssue(item["id"], "expected_article_not_found"))
        elif row.chunk_count == 0:
            issues.append(DatasetValidationIssue(item["id"], "chunk_missing"))
        elif row.embedding_count == 0:
            issues.append(DatasetValidationIssue(item["id"], "embedding_vector_missing"))
    return issues


def evaluate_dataset(service: LawSearchService, dataset: list[dict[str, Any]], config: EvaluationConfig) -> list[dict]:
    if config.top_k < 5:
        raise ValueError("top_k must be at least 5 to calculate Hit@5")
    rows: list[dict] = []
    for item in dataset:
        started = time.perf_counter()
        bundle = service.search_for_evaluation(
            query=item["query"], top_k=config.top_k, law_scope=config.law_scope
        )
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        retrieved = [_citation_to_dict(citation) for citation in bundle.citations]
        rank = _find_rank(item, retrieved)
        rows.append({
            "id": item["id"], "query": item["query"], "category": item.get("category"),
            "expected_law": item["expected_law"], "expected_article": item["expected_article"],
            "expected_article_id": item.get("expected_article_id"),
            "expected_keywords": item.get("expected_keywords", []), "rank": rank,
            "hit_at_1": rank == 1, "hit_at_3": bool(rank and rank <= 3),
            "hit_at_5": bool(rank and rank <= 5), "latency_ms": latency_ms,
            "retrieved_articles": retrieved,
        })
    return rows


def evaluate_threshold_diagnostics(
    service: LawSearchService, dataset: list[dict[str, Any]], config: EvaluationConfig
) -> tuple[list[dict], dict]:
    """Measure the existing reranker before/after its filter without mutating it."""
    rows: list[dict] = []
    thresholds = (0.5, 0.6, 0.7, 0.8)
    simulations: dict[float, list[dict]] = {threshold: [] for threshold in thresholds}

    for item in dataset:
        started = time.perf_counter()
        bundle = service.search_for_evaluation_diagnostics(
            query=item["query"], top_k=config.top_k, law_scope=config.law_scope
        )
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        pre_retrieved = [_candidate_to_dict(candidate) for candidate in bundle.candidates[: config.top_k]]
        pre_rank = _find_rank(item, pre_retrieved)
        expected_score = next(
            (candidate.score for candidate in bundle.candidates if candidate.article.id == item["expected_article_id"]),
            None,
        )
        rows.append({
            "id": item["id"], "query": item["query"], "expected_article_id": item["expected_article_id"],
            "pre_rank": pre_rank, "pre_retrieved_articles": pre_retrieved,
            "expected_score": expected_score, "latency_ms": latency_ms,
        })
        for threshold in thresholds:
            retrieved = [
                _candidate_to_dict(candidate)
                for candidate in bundle.candidates
                if candidate.score > threshold
                and (_has_keyword_match(candidate, item["query"]) or candidate.vector_score >= 0.8)
            ][: config.top_k]
            # Match the production entry point: an empty filtered chunk result
            # falls back to article search.  This is evaluation-only simulation;
            # it does not alter the production threshold or fallback behavior.
            if not retrieved:
                fallback = service._search_articles(
                    query=item["query"], top_k=config.top_k, law_scope=config.law_scope or []
                )
                retrieved = [_citation_to_dict(citation) for citation in fallback.citations]
            rank = _find_rank(item, retrieved)
            simulations[threshold].append({
                "rank": rank,
                "hit_at_1": rank == 1,
                "hit_at_3": bool(rank and rank <= 3),
                "hit_at_5": bool(rank and rank <= 5),
                "latency_ms": latency_ms,
                "no_result": not retrieved,
            })

    return rows, {
        str(threshold): {**summarize(simulations[threshold]), "no_result_rate": _mean_bool(row["no_result"] for row in simulations[threshold])}
        for threshold in thresholds
    }


def _citation_to_dict(citation: Any) -> dict:
    return {"article_id": citation.article_id, "law_name": citation.law_name,
            "article_no": citation.article_no, "article_title": citation.article_title}


def _candidate_to_dict(candidate: Any) -> dict:
    return {
        "article_id": candidate.article.id,
        "law_name": candidate.document.law_name or candidate.document.title,
        "article_no": candidate.article.article_no or candidate.article.article_number,
        "article_title": candidate.article.article_title or candidate.article.title,
        "score": candidate.score,
        "vector_score": candidate.vector_score,
    }


def _mean_bool(values: Any) -> float:
    items = [bool(value) for value in values]
    return sum(items) / len(items) if items else 0.0


def _find_rank(expected: dict, retrieved: list[dict]) -> int | None:
    """Prefer immutable DB id, then exact normalised law-name + article number."""
    expected_id = expected.get("expected_article_id")
    if expected_id is not None:
        for index, result in enumerate(retrieved, 1):
            if result["article_id"] == expected_id:
                return index
        return None
    for index, result in enumerate(retrieved, 1):
        if (_normalize(result["law_name"]) == _normalize(expected["expected_law"])
                and _normalize_article(result["article_no"]) == _normalize_article(expected["expected_article"])):
            return index
    return None


def _normalize(value: str | None) -> str:
    return "".join((value or "").lower().split())


def _normalize_article(value: str | None) -> str:
    return _normalize(value).replace("조", "")
