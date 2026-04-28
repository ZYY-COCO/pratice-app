from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.membership import MembershipStatusResponse

router = APIRouter(prefix="/membership", tags=["会员"])


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _build_membership_status(profile: dict) -> MembershipStatusResponse:
    raw_status = str(profile.get("membership_status") or "inactive").lower()
    expires_at = _parse_datetime(profile.get("membership_expires_at"))
    is_expired = bool(expires_at and expires_at < datetime.now(UTC))
    effective_status = "expired" if raw_status == "active" and is_expired else raw_status

    return MembershipStatusResponse(
        user_id=profile["id"],
        membership_status=effective_status,
        membership_plan=profile.get("membership_plan"),
        membership_started_at=profile.get("membership_started_at"),
        membership_expires_at=profile.get("membership_expires_at"),
        membership_updated_at=profile.get("membership_updated_at"),
        membership_active=effective_status == "active",
    )


@router.get("/status", response_model=MembershipStatusResponse)
def get_membership_status(user_id: str = Depends(get_current_user_id)) -> MembershipStatusResponse:
    supabase_admin = get_supabase_admin()
    response = supabase_admin.table("users").select("*").eq("id", user_id).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
    return _build_membership_status(response.data[0])
