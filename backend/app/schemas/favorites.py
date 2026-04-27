from pydantic import BaseModel

from app.schemas.questions import Question


class FavoriteQuestionItem(BaseModel):
    id: str
    question_id: str
    created_at: str
    question: Question | None = None


class FavoriteQuestionListResponse(BaseModel):
    items: list[FavoriteQuestionItem]
    count: int


class FavoriteToggleRequest(BaseModel):
    question_id: str


class FavoriteToggleResponse(BaseModel):
    question_id: str
    is_favorited: bool


class FavoriteStatusResponse(BaseModel):
    question_id: str
    is_favorited: bool
