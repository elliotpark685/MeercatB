from enum import Enum

from pydantic import BaseModel, Field


class KoshaCategory(str, Enum):
    """KOSHA 스마트검색 카테고리 코드."""

    SAFETY_HEALTH_RULE = "4"  # 산업안전보건기준에 관한 규칙
    NOTICE_DIRECTIVE = "5"  # 고시·훈령·예규
    SAFETY_MEDIA = "6"  # 안전보건 미디어
    KOSHA_GUIDE = "7"  # KOSHA GUIDE


class KoshaResultItem(BaseModel):
    title: str
    content: str
    category: str
    keywords: list[str] = Field(default_factory=list)
    score: float = 0.0
    url: str = ""
    doc_id: str = ""


class KoshaSearchResponse(BaseModel):
    query: str
    category: KoshaCategory
    page: int
    size: int
    total: int
    results: list[KoshaResultItem]
    related_keywords: list[str] = Field(default_factory=list)


class KoshaSummaryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    items: list[KoshaResultItem] = Field(min_length=1, max_length=3)


class KoshaSummaryResponse(BaseModel):
    query: str
    core_content: str
    applicable_scope: str
    field_application: str
    precautions: str
    related_regulations: str
