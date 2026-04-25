from fastapi import APIRouter, Depends, HTTPException, status

from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.feedback import BetaFeedbackRequest, BetaFeedbackResponse

router = APIRouter(prefix="/feedback", tags=["内测反馈"])


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
