from datetime import date, datetime

from pydantic import BaseModel, Field


class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    due_date: date | None = None


class TodoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    due_date: date | None = None
    is_completed: bool | None = None


class TodoResponse(BaseModel):
    id: int
    title: str
    description: str | None
    due_date: date | None
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
