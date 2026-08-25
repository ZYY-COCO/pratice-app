from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.feedback import (
    BetaFeedbackItem,
    BetaFeedbackListResponse,
    BetaFeedbackRequest,
    BetaFeedbackResponse,
)

router = APIRouter(prefix="/feedback", tags=["内测反馈"])


@router.get("/me", response_model=BetaFeedbackListResponse)
def list_my_feedback(
    limit: int = Query(default=50, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
) -> BetaFeedbackListResponse:
    supabase = get_supabase_admin()
    try:
        response = (
            supabase.table("beta_feedback")
            .select("id,feedback_type,content,status,admin_note,source_page,created_at,handled_at", count="exact")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="反馈记录暂时不可用，请稍后重试",
        ) from exc
    items = [BetaFeedbackItem(**row) for row in (response.data or [])]
    return BetaFeedbackListResponse(items=items, count=int(response.count or len(items)))


@router.post("/beta", response_model=BetaFeedbackResponse)
def submit_beta_feedback(
    payload: BetaFeedbackRequest,
    user_id: str = Depends(get_current_user_id),
) -> BetaFeedbackResponse:
    supabase = get_supabase_admin()
    row = {
        "user_id": user_id,
        "feedback_type": payload.feedback_type,
        "content": payload.content,
        "willing_to_pay": payload.willing_to_pay,
        "acceptable_price": payload.acceptable_price,
        "contact": payload.contact,
        "source_page": payload.source_page,
    }

    try:
        response = supabase.table("beta_feedback").insert(row).execute()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="反馈提交失败，请确认 beta_feedback 表已创建",
        ) from exc

    if not response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="反馈提交失败")

    return BetaFeedbackResponse(id=response.data[0]["id"], detail="反馈已提交，感谢你的内测建议")
