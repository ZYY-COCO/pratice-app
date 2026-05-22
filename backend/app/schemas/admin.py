from pydantic import BaseModel, Field


class AdminMeResponse(BaseModel):
    is_admin: bool
    profile: dict


class AdminOverviewResponse(BaseModel):
    total_users: int
    active_today: int
    active_week: int
    active_month: int
    active_year: int
    total_questions: int
    total_feedback: int
    pending_feedback: int
    active_members: int


class AdminUserItem(BaseModel):
    id: str
    email: str | None = None
    phone: str | None = None
    nickname: str | None = None
    auth_provider: str | None = None
    exam_target: str | None = None
    role: str | None = "user"
    disabled_at: str | None = None
    membership_status: str | None = None
    membership_plan: str | None = None
    membership_expires_at: str | None = None
    created_at: str | None = None
    answer_count: int = 0


class AdminUserListResponse(BaseModel):
    items: list[AdminUserItem]
    count: int


class AdminGrantMembershipRequest(BaseModel):
    months: int = Field(ge=1, le=36)
    plan: str = Field(default="admin_grant", max_length=40)


class AdminFeedbackListResponse(BaseModel):
    items: list[dict]
    count: int


class AdminQuestionListResponse(BaseModel):
    items: list[dict]
    count: int
