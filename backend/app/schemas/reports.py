from pydantic import BaseModel, Field


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
    weekly_answers: int = 0
    weekly_correct_answers: int = 0
    weekly_accuracy: float = 0


class LeaderboardItem(BaseModel):
    rank: int
    user_id: str
    nickname: str
    avatar_url: str | None = None
    total_answers: int
    correct_answers: int
    accuracy: float
    weekly_answers: int = 0


class LeaderboardResponse(BaseModel):
    items: list[LeaderboardItem]
    total_users: int


class StudySubjectAdvice(BaseModel):
    subject: str
    status: str = ""
    accuracy: float | None = None
    weak_points: list[str] = Field(default_factory=list)
    fear_points: list[str] = Field(default_factory=list)
    score_tips: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class StudyAdviceResponse(BaseModel):
    exam_code: str
    source: str = "rule"
    summary: str
    summary_items: list[str] = Field(default_factory=list)
    subject_advices: list[StudySubjectAdvice] = Field(default_factory=list)
    next_training: str = ""
