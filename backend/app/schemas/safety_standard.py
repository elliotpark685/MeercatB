from pydantic import BaseModel, Field


class SafetyStandardSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    source_types: list[str] | None = None
    user_id: int | None = None
    site_id: int | None = None


class SafetyStandardResultItem(BaseModel):
    source_type: str
    source_name: str
    article_no: str | None = None
    article_title: str | None = None
    content: str
    score: float
    provider: str = "law.go.kr"
    article_id: int | None = None
    chunk_id: int | None = None
    matched_reason: list[str] = []


class SafetyStandardSearchResponse(BaseModel):
    query: str
    results: list[SafetyStandardResultItem]
