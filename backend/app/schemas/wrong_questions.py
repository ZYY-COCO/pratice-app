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
    next_cursor: str | None = None
    has_more: bool = False


class WrongQuestionDetailResponse(BaseModel):
    id: str
    question_id: str
    wrong_count: int
    last_wrong_at: str
    latest_selected_answer: str | None = None
    question: Question


class ReviewWrongQuestionRequest(BaseModel):
    question_id: str
    client_submission_id: str | None = Field(default=None, min_length=1, max_length=120)
    selected_answer: str = Field(pattern="^[ABCD]$")
    used_time: int = Field(default=0, ge=0)
    exam_code: str | None = Field(default=None, pattern="^(Z001|Z002)$")
