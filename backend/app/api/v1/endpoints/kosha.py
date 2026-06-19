from fastapi import APIRouter, Query

from app.schemas.kosha import (
    KoshaCategory,
    KoshaSearchResponse,
    KoshaSummaryRequest,
    KoshaSummaryResponse,
)
from app.services.kosha_search_service import KoshaSearchService
from app.services.kosha_summary_service import KoshaSummaryService

router = APIRouter()


@router.get("/search", response_model=KoshaSearchResponse)
def search_kosha(
    query: str = Query(min_length=1, max_length=1000),
    category: KoshaCategory = Query(default=KoshaCategory.KOSHA_GUIDE),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=50),
) -> KoshaSearchResponse:
    service = KoshaSearchService()
    return service.search(query=query, category=category, page=page, size=size)


@router.post("/summarize", response_model=KoshaSummaryResponse)
def summarize_kosha(payload: KoshaSummaryRequest) -> KoshaSummaryResponse:
    service = KoshaSummaryService()
    return service.summarize(query=payload.query, items=payload.items)
