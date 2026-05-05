from pydantic import BaseModel, Field


class Question(BaseModel):
    id: str
    exam_code: str
    subject: str
    module: str
    submodule: str
    question_type: str
    stem: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    answer: str | None = None
    explanation: str | None = None
    difficulty: int
    source_type: str | None = None
    source_year: int | None = None
    passage_id: str | None = None


class Passage(BaseModel):
    id: str
    exam_code: str
    subject: str
    title: str | None = None
    content: str
    source_type: str | None = None
    source_year: int | None = None


class QuestionListResponse(BaseModel):
    items: list[Question]
    count: int


class QuestionProgressResponse(BaseModel):
    exam_code: str
    subject: str
    total_questions: int
    mastered_questions: int
    progress_percent: int
    review_due_count: int
    next_review_label: str
    review_days: list[int]


class ByModuleQuery(BaseModel):
    exam_code: str = Field(pattern="^(Z001|Z002|COMMON)$")
    subject: str
    module: str
    submodule: str
    limit: int = Field(default=10, ge=1, le=50)
