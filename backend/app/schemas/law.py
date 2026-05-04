from pydantic import BaseModel, Field


class LawSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    validate_latest: bool = False
    user_id: int | None = None
    site_id: int | None = None


class CitationItem(BaseModel):
    article_id: int
    law_name: str
    article_no: str
    article_title: str | None = None
    chapter: str | None = None
    section: str | None = None
    status: str
    effective_date: str | None = None
    source_page_start: int | None = None
    source_page_end: int | None = None


class RawHitItem(BaseModel):
    article_id: int
    score: float
    matched_reason: list[str]


class LawSearchResponse(BaseModel):
    query: str
    answer: str
    citations: list[CitationItem]
    raw_hits: list[RawHitItem]


class LawArticleDetailResponse(BaseModel):
    article_id: int
    law_document_id: int
    law_name: str
    article_no: str
    article_title: str | None = None
    chapter: str | None = None
    section: str | None = None
    full_text: str
    status: str
    effective_date: str | None = None
    source_page_start: int | None = None
    source_page_end: int | None = None
    law_type: str | None = None
    law_no: str | None = None
    document_effective_date: str | None = None
    source_file_path: str | None = None

