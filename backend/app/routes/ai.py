from fastapi import APIRouter, Depends

from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.ai import (
    ExplainWrongRequest,
    ExplainWrongResponse,
    SimilarQuestionRequest,
    SimilarQuestionResponse,
    WeaknessAnalysisResponse,
)
from app.services.answers import get_question_or_404
from app.services.reports import build_ability_item

router = APIRouter(prefix="/ai", tags=["AI 预留"])


@router.post("/explain-wrong", response_model=ExplainWrongResponse)
def explain_wrong(payload: ExplainWrongRequest, _: str = Depends(get_current_user_id)) -> ExplainWrongResponse:
    supabase = get_supabase_admin()
    question = get_question_or_404(supabase, payload.question_id)

    return ExplainWrongResponse(
        why_wrong=f"你选择了 {payload.selected_answer}，建议先对照题干关键词与选项含义，排除不符合知识点的选项。",
        why_correct=f"正确答案是 {question['answer']}。标准解析：{question['explanation']}",
        knowledge_point=f"{question['subject']} / {question['module']} / {question['submodule']}",
    )


@router.post("/weakness-analysis", response_model=WeaknessAnalysisResponse)
def weakness_analysis(user_id: str = Depends(get_current_user_id)) -> WeaknessAnalysisResponse:
    supabase = get_supabase_admin()
    response = (
        supabase.table("ability_stats")
        .select("*")
        .eq("user_id", user_id)
        .order("accuracy")
        .limit(3)
        .execute()
    )
    weak_items = [build_ability_item(row) for row in response.data]
    weak_modules = [f"{item['subject']} / {item['module']} / {item['submodule']}" for item in weak_items]

    return WeaknessAnalysisResponse(
        weak_modules=weak_modules,
        suggested_points=weak_modules,
        summary="第一版暂使用规则分析：优先训练正确率最低的 2-3 个知识点，并结合错题解析复盘。",
    )


@router.post("/generate-similar-question", response_model=SimilarQuestionResponse)
def generate_similar_question(
    payload: SimilarQuestionRequest,
    _: str = Depends(get_current_user_id),
) -> SimilarQuestionResponse:
    supabase = get_supabase_admin()
    question = get_question_or_404(supabase, payload.question_id)
    response = (
        supabase.table("questions")
        .select("*")
        .eq("exam_code", question["exam_code"])
        .eq("subject", question["subject"])
        .eq("module", question["module"])
        .eq("submodule", question["submodule"])
        .neq("id", payload.question_id)
        .limit(payload.limit)
        .execute()
    )

    items = [{**row, "answer": None, "explanation": None} for row in response.data]
    return SimilarQuestionResponse(items=items)
