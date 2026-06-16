from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.safety_standard import SafetyStandardSearchRequest, SafetyStandardSearchResponse
from app.services.safety_standard_search_service import SafetyStandardSearchService

router = APIRouter()


@router.post("/search", response_model=SafetyStandardSearchResponse)
def search_safety_standards(
    payload: SafetyStandardSearchRequest,
    db: Session = Depends(get_db),
) -> SafetyStandardSearchResponse:
    service = SafetyStandardSearchService(db=db)
    return service.search(
        query=payload.query,
        top_k=payload.top_k,
        source_types=payload.source_types,
        user_id=payload.user_id,
        site_id=payload.site_id,
    )
