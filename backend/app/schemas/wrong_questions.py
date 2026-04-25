from pydantic import BaseModel, Field

from app.schemas.questions import Question


class WrongQuestionItem(BaseModel):
    id: str
    question_id: str
    wrong_count: int
    last_wrong_at: str
    question: Question | None = None


class WrongQuestionListResponse(BaseModel):
    items: list[WrongQuestionItem]
    count: int


class WrongQuestionDetailResponse(BaseModel):
    id: str
    question_id: str
    wrong_count: int
    last_wrong_at: str
    latest_selected_answer: str | None = None
    question: Question


class ReviewWrongQuestionRequest(BaseModel):
    question_id: str
    selected_answer: str = Field(pattern="^[ABCDE]$")
    used_time: int = Field(default=0, ge=0)
