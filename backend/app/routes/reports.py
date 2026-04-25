from fastapi import APIRouter, Depends

from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.reports import AbilityReportResponse, AbilityStatItem, LearningSummaryResponse
from app.services.reports import build_ability_item

router = APIRouter(prefix="/report", tags=["能力报告"])


@router.get("/ability", response_model=AbilityReportResponse)
def ability_report(
    user_id: str = Depends(get_current_user_id),
    exam_code: str | None = None,
) -> AbilityReportResponse:
    supabase = get_supabase_admin()
    query = supabase.table("ability_stats").select("*").eq("user_id", user_id)
    if exam_code:
        query = query.eq("exam_code", exam_code)

    response = query.order("accuracy").execute()
    items = [AbilityStatItem(**build_ability_item(row)) for row in response.data]
    weak_items = [item for item in items if item.accuracy < 60][:5]
    return AbilityReportResponse(items=items, weak_items=weak_items)


@router.get("/summary", response_model=LearningSummaryResponse)
def learning_summary(
    user_id: str = Depends(get_current_user_id),
    exam_code: str | None = None,
) -> LearningSummaryResponse:
    supabase = get_supabase_admin()

    ability_query = supabase.table("ability_stats").select("total_count, correct_count").eq("user_id", user_id)
    if exam_code:
        ability_query = ability_query.eq("exam_code", exam_code)
    ability_response = ability_query.execute()

    total_answers = sum(int(row.get("total_count") or 0) for row in ability_response.data)
    correct_answers = sum(int(row.get("correct_count") or 0) for row in ability_response.data)
    accuracy = round(correct_answers / total_answers * 100, 2) if total_answers else 0

    wrong_response = (
        supabase.table("wrong_questions")
        .select("id, questions(exam_code)")
        .eq("user_id", user_id)
        .limit(1000)
        .execute()
    )
    wrong_rows = wrong_response.data
    if exam_code:
        wrong_rows = [row for row in wrong_rows if (row.get("questions") or {}).get("exam_code") == exam_code]

    return LearningSummaryResponse(
        exam_code=exam_code,
        total_answers=total_answers,
        correct_answers=correct_answers,
        accuracy=accuracy,
        wrong_question_count=len(wrong_rows),
    )
