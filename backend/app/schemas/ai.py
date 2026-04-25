from pydantic import BaseModel


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
