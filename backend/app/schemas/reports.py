from pydantic import BaseModel


class AbilityStatItem(BaseModel):
    id: str
    exam_code: str
    subject: str
    module: str
    submodule: str
    total_count: int
    correct_count: int
    accuracy: float
    level: str
    recommendation: str


class AbilityReportResponse(BaseModel):
    items: list[AbilityStatItem]
    weak_items: list[AbilityStatItem]


class LearningSummaryResponse(BaseModel):
    exam_code: str | None = None
    total_answers: int
    correct_answers: int
    accuracy: float
    wrong_question_count: int
