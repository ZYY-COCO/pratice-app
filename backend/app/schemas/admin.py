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


class AdminUserDetailResponse(BaseModel):
    profile: dict
    answer_summary: dict
    recent_answers: list[dict]
    membership_orders: list[dict]
    admin_actions: list[dict] = []


class AdminFeedbackStatusRequest(BaseModel):
    status: str = Field(pattern="^(open|reviewed|resolved|ignored)$")
    admin_note: str | None = Field(default=None, max_length=500)


class AdminFeedbackListResponse(BaseModel):
    items: list[dict]
    count: int


class AdminQuestionStatusRequest(BaseModel):
    status: str = Field(pattern="^(active|archived)$")


class AdminQuestionUpdateRequest(BaseModel):
    exam_code: str | None = Field(default=None, pattern="^(Z001|Z002|COMMON)$")
    subject: str | None = Field(default=None, min_length=1, max_length=40)
    module: str | None = Field(default=None, min_length=1, max_length=80)
    submodule: str | None = Field(default=None, min_length=1, max_length=80)
    stem: str | None = Field(default=None, min_length=1, max_length=5000)
    option_a: str | None = Field(default=None, min_length=1, max_length=1000)
    option_b: str | None = Field(default=None, min_length=1, max_length=1000)
    option_c: str | None = Field(default=None, min_length=1, max_length=1000)
    option_d: str | None = Field(default=None, min_length=1, max_length=1000)
    answer: str | None = Field(default=None, pattern="^[ABCD]$")
    explanation: str | None = Field(default=None, max_length=8000)
    difficulty: int | None = Field(default=None, ge=1, le=5)


class AdminQuestionReviewRequest(BaseModel):
    review_status: str = Field(pattern="^(pending|needs_changes|approved|rejected)$")
    review_note: str | None = Field(default=None, max_length=1000)
    publish: bool = False


class AdminQuestionBulkFilters(BaseModel):
    exam_code: str | None = Field(default=None, max_length=20)
    subject: str | None = Field(default=None, max_length=40)
    module: str | None = Field(default=None, max_length=80)
    status: str | None = Field(default=None, max_length=20)
    review_status: str | None = Field(default=None, max_length=20)
    exclude_review_status: str | None = Field(default=None, max_length=20)
    search: str | None = Field(default=None, max_length=80)
    difficulty: int | None = Field(default=None, ge=1, le=5)


class AdminQuestionBulkStatusRequest(BaseModel):
    status: str = Field(pattern="^(active|archived)$")
    ids: list[str] = Field(default_factory=list, max_length=20000)
    filters: AdminQuestionBulkFilters | None = None


class AdminQuestionBulkStatusResponse(BaseModel):
    updated_count: int


class AdminQuestionDetailResponse(BaseModel):
    question: dict


class AdminQuestionListResponse(BaseModel):
    items: list[dict]
    count: int
