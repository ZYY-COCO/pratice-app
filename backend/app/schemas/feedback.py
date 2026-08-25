from typing import Literal

from pydantic import BaseModel, Field


class BetaFeedbackRequest(BaseModel):
    feedback_type: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=5, max_length=1000)
    willing_to_pay: bool | None = None
    acceptable_price: str | None = Field(default=None, max_length=50)
    contact: str | None = Field(default=None, max_length=100)
    source_page: str | None = Field(default=None, max_length=50)


class BetaFeedbackResponse(BaseModel):
    id: str
    detail: str


class BetaFeedbackItem(BaseModel):
    id: str
    feedback_type: str
    content: str
    status: Literal["open", "reviewed", "resolved", "ignored"] = "open"
    admin_note: str | None = None
    source_page: str | None = None
    created_at: str | None = None
    handled_at: str | None = None


class BetaFeedbackListResponse(BaseModel):
    items: list[BetaFeedbackItem] = Field(default_factory=list)
    count: int = 0
