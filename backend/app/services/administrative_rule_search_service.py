from sqlalchemy.orm import Session

from app.schemas.safety_standard import SafetyStandardSearchResponse
from app.services.safety_standard_search_service import SafetyStandardSearchService

ADMINISTRATIVE_RULE_CATEGORY = "administrative_rule"


class AdministrativeRuleSearchService(SafetyStandardSearchService):
    """Search administrative rules without competing with statutes or safety standards."""

    def __init__(self, db: Session) -> None:
        super().__init__(db=db, source_category=ADMINISTRATIVE_RULE_CATEGORY)

    def search(
        self,
        query: str,
        top_k: int = 5,
        source_types: list[str] | None = None,
        user_id: int | None = None,
        site_id: int | None = None,
    ) -> SafetyStandardSearchResponse:
        return super().search(
            query=query,
            top_k=top_k,
            source_types=source_types,
            user_id=user_id,
            site_id=site_id,
        )
