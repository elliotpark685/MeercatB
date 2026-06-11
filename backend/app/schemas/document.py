from pydantic import BaseModel, Field


class DocumentGenerateRequest(BaseModel):
    site_id: int
    user_id: int | None = None
    document_type: str = Field(default="tbm", examples=["tbm", "risk_assessment"])
    prompt: str = Field(min_length=5, max_length=4000)


class DocumentGenerateResponse(BaseModel):
    document_id: int
    title: str
    content: str
    citations: list[dict]
    generated_text: str
    references: list[dict]
