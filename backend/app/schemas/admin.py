from datetime import datetime

from pydantic import BaseModel


class DashboardDocumentItem(BaseModel):
    id: int
    site_id: int
    document_type: str
    title: str
    created_at: datetime


class DashboardLawSearchItem(BaseModel):
    id: int
    query: str
    top_k: int
    result_count: int
    created_at: datetime


class AdminDashboardResponse(BaseModel):
    site_id: int | None
    total_generated_documents: int
    total_law_searches: int
    today_quiz_count: int
    latest_generated_documents: list[DashboardDocumentItem]
    latest_law_searches: list[DashboardLawSearchItem]

