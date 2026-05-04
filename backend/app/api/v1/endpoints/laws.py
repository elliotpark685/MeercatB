from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_law_search_service
from app.schemas.law import LawArticleDetailResponse, LawSearchRequest, LawSearchResponse
from app.services.law_search_service import LawSearchService

router = APIRouter()


@router.post("/search", response_model=LawSearchResponse)
def search_laws(
    payload: LawSearchRequest,
    service: LawSearchService = Depends(get_law_search_service),
) -> LawSearchResponse:
    return service.search(
        query=payload.query,
        top_k=payload.top_k,
        validate_latest=payload.validate_latest,
        user_id=payload.user_id,
        site_id=payload.site_id,
    )


@router.get("/articles/{article_id}", response_model=LawArticleDetailResponse)
def get_law_article(
    article_id: int,
    service: LawSearchService = Depends(get_law_search_service),
) -> LawArticleDetailResponse:
    detail = service.get_article_detail(article_id=article_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Law article {article_id} not found",
        )
    return detail

