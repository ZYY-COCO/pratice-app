from pydantic import BaseModel


class MembershipStatusResponse(BaseModel):
    user_id: str
    membership_status: str = "inactive"
    membership_plan: str | None = None
    membership_started_at: str | None = None
    membership_expires_at: str | None = None
    membership_updated_at: str | None = None
    membership_active: bool = False
