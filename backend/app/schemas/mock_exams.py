from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.questions import Question


MockExamCode = Literal["Z001", "Z002"]
MockExamPaperStatus = Literal["draft", "published", "archived"]
MockExamSectionKey = Literal["culture", "english", "third"]


class MockExamPaperSummary(BaseModel):
    id: str
    title: str
    exam_code: MockExamCode
    description: str = ""
    duration_minutes: int = 120
    status: MockExamPaperStatus
    version: int = 1
    question_count: int = 0
    total_score: int = 0
    sort_order: int = 0
    published_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class MockExamPaperListResponse(BaseModel):
    items: list[MockExamPaperSummary] = Field(default_factory=list)


class MockExamPaperQuestion(Question):
    mock_section_key: MockExamSectionKey
    mock_section: str
    point_value: int = Field(ge=1, le=10)
    position: int = Field(ge=1, le=100)


class MockExamPaperDetailResponse(BaseModel):
    paper: MockExamPaperSummary
    questions: list[MockExamPaperQuestion] = Field(default_factory=list)


class MockExamSectionValidation(BaseModel):
    key: MockExamSectionKey
    label: str
    selected_count: int = 0
    required_count: int
    point_value: int
    selected_score: int = 0
    required_score: int


class MockExamDifficultyValidation(BaseModel):
    key: Literal["basic", "medium", "hard"]
    label: str
    selected_count: int = 0
    required_count: int


class MockExamValidationResult(BaseModel):
    valid: bool = False
    errors: list[str] = Field(default_factory=list)
    question_count: int = 0
    total_score: int = 0
    sections: list[MockExamSectionValidation] = Field(default_factory=list)
    difficulty: list[MockExamDifficultyValidation] = Field(default_factory=list)


class AdminMockExamPaperItemInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1, max_length=80)
    section_key: MockExamSectionKey


class AdminMockExamPaperCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=80)
    exam_code: MockExamCode
    description: str = Field(default="", max_length=500)
    duration_minutes: int = Field(default=120, ge=30, le=360)
    sort_order: int = Field(default=0, ge=0, le=10000)


class AdminMockExamPaperUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=80)
    exam_code: MockExamCode | None = None
    description: str | None = Field(default=None, max_length=500)
    duration_minutes: int | None = Field(default=None, ge=30, le=360)
    sort_order: int | None = Field(default=None, ge=0, le=10000)
    items: list[AdminMockExamPaperItemInput] | None = Field(default=None, max_length=55)


class AdminMockExamPaperDetailResponse(BaseModel):
    paper: MockExamPaperSummary
    items: list[dict] = Field(default_factory=list)
    validation: MockExamValidationResult


class AdminMockExamQuestionListResponse(BaseModel):
    items: list[dict] = Field(default_factory=list)
    count: int = 0
