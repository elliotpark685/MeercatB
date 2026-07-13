from pydantic import BaseModel, Field


class DocumentGenerateRequest(BaseModel):
    site_id: int
    user_id: int | None = None
    document_type: str = Field(default="tbm", examples=["tbm", "risk_assessment"])
    workplace_name: str = Field(min_length=2, max_length=200)
    work_title: str | None = Field(default=None, max_length=200)
    safety_keywords: list[str] = Field(default_factory=list)
    equipment_tools: list[str] = Field(default_factory=list)
    law_names: list[str] = Field(default_factory=list)
    kosha_categories: list[str] = Field(default_factory=list)
    prompt: str = Field(default="", max_length=4000)


class DocumentGenerateResponse(BaseModel):
    document_id: int
    title: str
    content: str
    citations: list[dict]
