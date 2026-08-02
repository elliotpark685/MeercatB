from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.safety_standard import SafetyStandardSearchRequest, SafetyStandardSearchResponse
from app.services.administrative_rule_search_service import AdministrativeRuleSearchService

router = APIRouter()


@router.post("/search", response_model=SafetyStandardSearchResponse)
def search_administrative_rules(
    payload: SafetyStandardSearchRequest,
    db: Session = Depends(get_db),
) -> SafetyStandardSearchResponse:
    return AdministrativeRuleSearchService(db=db).search(
        query=payload.query,
        top_k=payload.top_k,
        source_types=payload.source_types,
        user_id=payload.user_id,
        site_id=payload.site_id,
    )
