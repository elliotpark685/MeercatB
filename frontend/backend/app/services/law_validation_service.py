from app.core.config import settings


class LawValidationService:
    """Placeholder for future Korean law API validation integration."""

    def __init__(self) -> None:
        self._law_api_oc = settings.law_api_oc

    def validate_latest(self, citations: list[dict]) -> str:
        # External API validation is intentionally not implemented in Step 3.
        _ = citations
        _ = self._law_api_oc
        return "latest validation is not implemented yet"

