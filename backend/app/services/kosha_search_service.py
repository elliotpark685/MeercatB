"""KOSHA GUIDE 스마트검색 서비스.

KOSHA OpenAPI 호출 → HTML 태그 제거 → 내부 표준 모델 변환까지 담당한다.
API 키가 없거나 외부 API 호출이 실패해도 예외를 올리지 않고
빈 결과로 graceful fallback 한다 (검색 페이지 자체는 항상 응답).
"""
from __future__ import annotations

import logging

from app.core.config import settings
from app.schemas.kosha import KoshaCategory, KoshaResultItem, KoshaSearchResponse
from app.utils.kosha_api_client import KoshaApiClient, strip_html

logger = logging.getLogger(__name__)


class KoshaSearchService:
    def __init__(self) -> None:
        self._client: KoshaApiClient | None = None
        if settings.kosha_api_key:
            self._client = KoshaApiClient(service_key=settings.kosha_api_key)

    def search(
        self,
        query: str,
        category: KoshaCategory,
        page: int,
        size: int,
    ) -> KoshaSearchResponse:
        if self._client is None:
            logger.warning("KOSHA search skipped: DATA_KEY is not configured")
            return KoshaSearchResponse(
                query=query, category=category, page=page, size=size, total=0, results=[]
            )

        try:
            raw_items, total, related_keywords = self._client.search(
                query=query, category=category.value, page=page, size=size
            )
        except Exception as exc:
            logger.warning("KOSHA search failed, returning empty result: %s", exc)
            raw_items, total, related_keywords = [], 0, []

        results = [
            KoshaResultItem(
                title=strip_html(item.title),
                content=strip_html(item.content),
                category=item.category or category.value,
                keywords=item.keywords,
                score=item.score,
                url=item.url,
                doc_id=item.doc_id,
            )
            for item in raw_items
        ]

        return KoshaSearchResponse(
            query=query,
            category=category,
            page=page,
            size=size,
            total=total,
            results=results,
            related_keywords=related_keywords,
        )
