from pydantic import BaseModel, Field


class SubmitAnswerRequest(BaseModel):
    question_id: str
    selected_answer: str = Field(pattern="^[ABCDE]$")
    used_time: int = Field(default=0, ge=0)
    exam_code: str | None = Field(default=None, pattern="^(Z001|Z002)$")


class SubmitAnswerResponse(BaseModel):
    question_id: str
    selected_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str
    added_to_wrong_questions: bool
    ability_accuracy: float


class AnswerHistoryQuestion(BaseModel):
    id: str
    exam_code: str
    subject: str
    module: str
    submodule: str
    stem: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    option_e: str | None = None
    answer: str
    explanation: str


class AnswerHistoryItem(BaseModel):
    id: str
    question_id: str
    selected_answer: str
    is_correct: bool
    used_time: int | None = 0
    created_at: str
    question: AnswerHistoryQuestion | None = None


class AnswerHistoryResponse(BaseModel):
    items: list[AnswerHistoryItem]
    count: int
