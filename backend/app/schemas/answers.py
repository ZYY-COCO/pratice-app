from pydantic import BaseModel, Field


class SubmitAnswerRequest(BaseModel):
    question_id: str
    client_submission_id: str | None = Field(default=None, min_length=1, max_length=120)
    practice_session_item_id: str | None = Field(default=None, min_length=1, max_length=120)
    selected_answer: str = Field(pattern="^[ABCD]$")
    used_time: int = Field(default=0, ge=0)
    exam_code: str | None = Field(default=None, pattern="^(Z001|Z002)$")


class SubmitBatchAnswerItem(BaseModel):
    question_id: str
    client_submission_id: str | None = Field(default=None, min_length=1, max_length=120)
    selected_answer: str = Field(pattern="^[ABCD]$")
    used_time: int = Field(default=0, ge=0)


class SubmitBatchAnswerRequest(BaseModel):
    answers: list[SubmitBatchAnswerItem] = Field(min_length=1, max_length=50)
    exam_code: str | None = Field(default=None, pattern="^(Z001|Z002)$")


class MarkUnfamiliarRequest(BaseModel):
    question_id: str
    client_submission_id: str | None = Field(default=None, min_length=1, max_length=120)
    practice_session_item_id: str | None = Field(default=None, min_length=1, max_length=120)
    used_time: int = Field(default=0, ge=0)
    exam_code: str | None = Field(default=None, pattern="^(Z001|Z002)$")


class GradeAnswerResponse(BaseModel):
    question_id: str
    selected_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str
    added_to_wrong_questions: bool


class AdaptiveAnswerUpdateResponse(BaseModel):
    adaptive_updated: bool
    idempotent: bool | None = None
    migration_pending: bool | None = None
    retryable: bool | None = None
    error: str | None = None
    answer_id: str | None = None
    practice_session_item_id: str | None = None
    diagnostic_status: str | None = None
    theta: float | None = None
    uncertainty: float | None = None
    effective_evidence: float | None = None
    pending_conflicts: int | None = None


class SubmitAnswerResponse(BaseModel):
    question_id: str
    selected_answer: str
    correct_answer: str
    is_correct: bool | None
    explanation: str
    added_to_wrong_questions: bool | None
    ability_accuracy: float | None = None
    submission_id: str | None = None
    client_submission_id: str | None = None
    stats_exam_code: str | None = None
    persisted: bool = True
    idempotent: bool = False
    is_first_attempt: bool | None = None
    attempt_number: int | None = None
    is_first_attempt_in_scope: bool | None = None
    scope_attempt_number: int | None = None
    adaptive: AdaptiveAnswerUpdateResponse | None = None
    persistence_error: str | None = None
    persistence_retryable: bool = False


class SubmitBatchAnswerResponse(BaseModel):
    items: list[SubmitAnswerResponse]


class AbilityAccuracyResponse(BaseModel):
    ability_accuracy: float | None = None


class AnswerHistoryQuestion(BaseModel):
    id: str
    exam_code: str
    subject: str
    module: str
    submodule: str
    difficulty: int | None = None
    stem: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    answer: str
    explanation: str
    source_type: str | None = None
    source_year: int | None = None


class AnswerHistoryItem(BaseModel):
    id: str
    question_id: str
    selected_answer: str
    is_correct: bool
    used_time: int | None = 0
    client_submission_id: str | None = None
    stats_exam_code: str | None = None
    attempt_number: int = 1
    is_first_attempt: bool = False
    scope_attempt_number: int | None = None
    is_first_attempt_in_scope: bool | None = None
    created_at: str
    question: AnswerHistoryQuestion | None = None


class AnswerHistoryResponse(BaseModel):
    items: list[AnswerHistoryItem]
    count: int
