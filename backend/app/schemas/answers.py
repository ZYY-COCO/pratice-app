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
