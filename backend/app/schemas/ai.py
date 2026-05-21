from pydantic import BaseModel, Field


class ExplainWrongRequest(BaseModel):
    question_id: str
    selected_answer: str


class ExplainWrongResponse(BaseModel):
    why_wrong: str
    why_correct: str
    knowledge_point: str


class WeaknessAnalysisResponse(BaseModel):
    weak_modules: list[str]
    suggested_points: list[str]
    summary: str


class SimilarQuestionRequest(BaseModel):
    question_id: str
    limit: int = 5


class SimilarQuestionResponse(BaseModel):
    items: list[dict]


class QuestionChatRequest(BaseModel):
    question_id: str = Field(min_length=1)
    user_message: str = Field(min_length=1, max_length=1000)
    submitted: bool = False
    user_answer: str | None = Field(default=None, max_length=8)


class QuestionChatResponse(BaseModel):
    reply: str
    usage: dict[str, str] = Field(default_factory=dict)


class AiTrainingGenerateRequest(BaseModel):
    smart_mode: bool = True
    exam_code: str | None = Field(default=None, pattern="^(Z001|Z002)$")
    subject: str | None = None
    module: str | None = None
    submodule: str | None = None
    difficulty: str | None = None
    question_count: int = Field(default=10, ge=5, le=30)


class AiTrainingTarget(BaseModel):
    subject: str
    module: str
    submodule: str
    difficulty: str
    question_count: int
    basis: str


class AiTrainingRecommendationResponse(BaseModel):
    exam_code: str
    target: AiTrainingTarget
    metrics: dict = Field(default_factory=dict)


class AiTrainingSessionResponse(BaseModel):
    session_id: str
    status: str
    exam_code: str
    target: AiTrainingTarget
    items: list[dict]


class AiTrainingSummaryResponse(BaseModel):
    session_id: str
    total_count: int
    answered_count: int
    correct_count: int
    accuracy: float
    summary: str
    next_step: str
    weak_points: list[str] = Field(default_factory=list)
    items: list[dict] = Field(default_factory=list)
