from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.questions import Question


class AdaptivePracticeScope(BaseModel):
    module: str = Field(min_length=1, max_length=160)
    submodule: str | None = Field(default=None, max_length=160)

    @field_validator("module", mode="before")
    @classmethod
    def normalize_module(cls, value):
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("scope module cannot be empty")
        return normalized

    @field_validator("submodule", mode="before")
    @classmethod
    def normalize_submodule(cls, value):
        if value is None or not isinstance(value, str):
            return value
        return value.strip() or None


class CreateAdaptivePracticeSessionRequest(BaseModel):
    exam_code: Literal["Z001", "Z002"]
    subject: str = Field(min_length=1, max_length=80)
    practice_mode: Literal["special", "comprehensive"] = "special"
    scopes: list[AdaptivePracticeScope] = Field(default_factory=list, max_length=50)
    question_count: int = Field(default=10, ge=1, le=30)
    preference: Literal["steady", "standard", "challenge"] = "standard"
    accepted_challenge: bool = False
    client_session_id: str | None = Field(default=None, min_length=1, max_length=120)
    resume_existing_session: bool = False

    @model_validator(mode="after")
    def validate_scopes(self):
        if self.resume_existing_session and not self.client_session_id:
            raise ValueError(
                "resuming an adaptive session requires client_session_id"
            )
        if self.practice_mode == "special" and not self.scopes:
            raise ValueError("special practice requires at least one scope")
        if self.practice_mode == "comprehensive" and self.scopes:
            raise ValueError("comprehensive practice must not include explicit scopes")
        if self.practice_mode == "comprehensive" and (
            self.preference != "standard" or self.accepted_challenge
        ):
            raise ValueError(
                "comprehensive practice uses the standard D1-D4 difficulty policy"
            )
        return self


class AdaptiveSubjectStateResponse(BaseModel):
    theta: float
    uncertainty: float
    effective_evidence: float
    reliable_first_attempt_count: int
    diagnostic_status: str
    pending_conflicts: int
    confidence_label: str
    initial_level_range: str


class AdaptivePracticeSessionResponse(BaseModel):
    id: str
    exam_code: str
    subject: str
    practice_mode: str
    question_count: int
    preference: str
    status: str
    diagnostic_status: str
    strategy_version: str
    model_version: str


class AdaptivePracticeItemResponse(BaseModel):
    id: str
    session_id: str
    position: int
    reason_codes: list[str]
    target_zone: str
    predicted_correct_probability: float | None = None
    is_diagnostic: bool = False
    is_challenge: bool = False
    question: Question


class CreateAdaptivePracticeSessionResponse(BaseModel):
    session: AdaptivePracticeSessionResponse
    state: AdaptiveSubjectStateResponse
    next_item: AdaptivePracticeItemResponse | None = None
    items: list[AdaptivePracticeItemResponse] = Field(default_factory=list)


class NextAdaptivePracticeItemResponse(BaseModel):
    session: AdaptivePracticeSessionResponse
    state: AdaptiveSubjectStateResponse
    next_item: AdaptivePracticeItemResponse | None = None
    finished: bool = False


class AdaptivePracticeItemEventRequest(BaseModel):
    event_type: Literal["presented", "skipped", "answer_viewed", "abandoned"]


class AdaptivePracticeItemEventResponse(BaseModel):
    session_id: str
    session_item_id: str
    event_type: str
    recorded: bool = True


class CompleteAdaptivePracticeSessionRequest(BaseModel):
    reason: Literal["completed", "abandoned", "cancelled"] = "completed"


class CompleteAdaptivePracticeSessionResponse(BaseModel):
    session_id: str
    status: str
    reason: str
    state: AdaptiveSubjectStateResponse | None = None


class SubmitAdaptiveComprehensiveAnswer(BaseModel):
    practice_session_item_id: str = Field(min_length=1, max_length=120)
    selected_answer: Literal["A", "B", "C", "D"] | None = None
    used_time: int = Field(default=0, ge=0, le=86400)
    client_submission_id: str = Field(min_length=1, max_length=120)

    @field_validator("practice_session_item_id", "client_submission_id", mode="before")
    @classmethod
    def normalize_identifiers(cls, value):
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("comprehensive submission identifiers cannot be empty")
        return normalized


class SubmitAdaptiveComprehensiveSessionRequest(BaseModel):
    client_submission_id: str = Field(min_length=1, max_length=120)
    answers: list[SubmitAdaptiveComprehensiveAnswer] = Field(min_length=1, max_length=30)

    @field_validator("client_submission_id", mode="before")
    @classmethod
    def normalize_client_submission_id(cls, value):
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("comprehensive submission identifier cannot be empty")
        return normalized

    @model_validator(mode="after")
    def validate_unique_items(self):
        item_ids = [answer.practice_session_item_id for answer in self.answers]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("comprehensive answers must contain each session item once")
        submission_ids = [answer.client_submission_id for answer in self.answers]
        if len(submission_ids) != len(set(submission_ids)):
            raise ValueError("comprehensive answer submission ids must be unique")
        return self


class AdaptiveComprehensiveResultItem(BaseModel):
    practice_session_item_id: str
    question_id: str
    position: int
    selected_answer: Literal["A", "B", "C", "D"] | None = None
    correct_answer: Literal["A", "B", "C", "D"]
    is_correct: bool | None = None
    explanation: str


class AdaptiveComprehensiveSummary(BaseModel):
    total_count: int
    answered_count: int
    correct_count: int
    wrong_count: int
    skipped_count: int
    accuracy: float
    used_time: int


class SubmitAdaptiveComprehensiveSessionResponse(BaseModel):
    session_id: str
    status: str
    reason: str
    idempotent: bool = False
    summary: AdaptiveComprehensiveSummary
    results: list[AdaptiveComprehensiveResultItem]
    state: AdaptiveSubjectStateResponse
    adaptive_settled: bool = True
