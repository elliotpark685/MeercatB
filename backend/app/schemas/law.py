from pydantic import BaseModel, Field


class LawDocumentMetadata(BaseModel):
    id: int | None = None
    law_name: str
    law_short_name: str | None = None
    law_type: str | None = None
    source_url: str | None = None
    effective_date: str | None = None
    amendment_date: str | None = None
    version_hash: str | None = None
    is_active: bool = True


class LawArticleSchema(BaseModel):
    id: int | None = None
    law_document_id: int
    article_no: str
    article_title: str | None = None
    article_text: str
    chapter: str | None = None
    section: str | None = None
    effective_date: str | None = None


class LawChunkSchema(BaseModel):
    id: int | None = None
    law_article_id: int
    chunk_level: str = Field(default="article", examples=["article", "paragraph", "subparagraph", "item"])
    chunk_no: str | None = None
    chunk_text: str
    token_count: int | None = None
    metadata_json: str | None = None


class LawEmbeddingSchema(BaseModel):
    id: int | None = None
    chunk_id: int | None = None
    article_id: int | None = None
    embedding_model: str


class LawSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    validate_latest: bool = False
    user_id: int | None = None
    site_id: int | None = None
    law_names: list[str] | None = None
    law_scope: list[str] | str | None = None


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


class LawSearchResultItem(BaseModel):
    law_name: str
    article_no: str
    article_title: str | None = None
    chunk_text: str
    score: float
    source_url: str | None = None
    effective_date: str | None = None
    document_effective_date: str | None = None
    article_id: int | None = None
    chunk_id: int | None = None
    matched_reason: list[str] = []


class LawSearchResponse(BaseModel):
    query: str
    answer: str
    citations: list[CitationItem]
    raw_hits: list[RawHitItem]
    results: list[LawSearchResultItem] = []


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
