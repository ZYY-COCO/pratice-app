"""Response and command models for the desktop administration operations centre."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class QuestionPortalUserOverviewResponse(BaseModel):
    total_users: int = 0
    new_today: int = 0
    new_week: int = 0
    active_week: int = 0
    active_members: int = 0


class QuestionPortalUserItem(BaseModel):
    id: str
    email: str | None = None
    phone: str | None = None
    nickname: str | None = None
    avatar_url: str | None = None
    exam_target: str | None = None
    membership_status: str | None = None
    membership_plan: str | None = None
    membership_expires_at: str | None = None
    disabled_at: str | None = None
    created_at: str | None = None
    answer_count: int = 0
    correct_count: int = 0
    wrong_count: int = 0
    accuracy: float = 0
    last_answer_at: str | None = None


class QuestionPortalUserListResponse(BaseModel):
    items: list[QuestionPortalUserItem] = Field(default_factory=list)
    count: int = 0


class QuestionPortalUserDetailResponse(BaseModel):
    profile: dict[str, Any] = Field(default_factory=dict)
    answer_summary: dict[str, Any] = Field(default_factory=dict)
    subject_accuracy: list[dict[str, Any]] = Field(default_factory=list)
    recent_answers: list[dict[str, Any]] = Field(default_factory=list)
    membership_orders: list[dict[str, Any]] = Field(default_factory=list)
    admin_actions: list[dict[str, Any]] = Field(default_factory=list)


class QuestionPortalMembershipRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    months: int = Field(ge=1, le=36)
    plan: str = Field(default="admin_grant", min_length=1, max_length=40)


class QuestionPortalUserStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    disabled: bool
    reason: str | None = Field(default=None, max_length=300)


class OperationsDashboardResponse(BaseModel):
    total_users: int = 0
    new_today: int = 0
    active_week: int = 0
    active_members: int = 0
    published_home_items: int = 0
    published_announcements: int = 0
    scoreline_draft_runs: int = 0
    announcement_draft_runs: int = 0
    recent_import_failures: int = 0


class OperationsImportPreviewResponse(BaseModel):
    dataset: str
    source_sha256: str
    total_rows: int
    valid_count: int
    invalid_count: int
    valid: bool
    records: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class OperationsImportRunItem(BaseModel):
    id: str
    source_filename: str
    source_sha256: str
    statistics: dict[str, Any] = Field(default_factory=dict)
    status: str
    created_by: str | None = None
    published_by: str | None = None
    created_at: str | None = None
    published_at: str | None = None
    updated_at: str | None = None


class OperationsImportRunListResponse(BaseModel):
    items: list[OperationsImportRunItem] = Field(default_factory=list)
    count: int = 0


class OperationsImportCommitResponse(BaseModel):
    import_run: OperationsImportRunItem
    inserted_count: int = 0


class OperationsImportRunStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(pattern="^(draft|published|archived)$")


class OperationsScorelineListResponse(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


class OperationsAnnouncementListResponse(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


class OperationsAnnouncementUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str | None = Field(default=None, pattern="^(draft|published|archived)$")
    is_pinned: bool | None = None
    sort_order: int | None = Field(default=None, ge=-9999, le=9999)
    summary: str | None = Field(default=None, max_length=2000)
    source_url: str | None = Field(default=None, max_length=1000)


class HomeContentItem(BaseModel):
    id: str
    slot: str
    title: str
    subtitle: str = ""
    badge: str = ""
    source: str = ""
    display_date: str | None = None
    cover_label: str = ""
    tone: str = "is-blue"
    target_url: str = ""
    route_key: str = ""
    sort_order: int = 0
    status: str = "draft"
    starts_at: str | None = None
    ends_at: str | None = None
    announcement_record_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class HomeContentListResponse(BaseModel):
    items: list[HomeContentItem] = Field(default_factory=list)
    count: int = 0


class HomeContentUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slot: str = Field(pattern="^(focus|news|service)$")
    title: str = Field(min_length=1, max_length=120)
    subtitle: str = Field(default="", max_length=240)
    badge: str = Field(default="", max_length=40)
    source: str = Field(default="", max_length=80)
    display_date: str | None = Field(default=None, max_length=40)
    cover_label: str = Field(default="", max_length=40)
    tone: str = Field(default="is-blue", pattern="^(is-blue|is-violet|is-mint|is-orange|is-school|is-major|is-guide)$")
    target_url: str = Field(default="", max_length=1000)
    route_key: str = Field(default="", max_length=80)
    sort_order: int = Field(default=0, ge=-9999, le=9999)
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")
    starts_at: str | None = Field(default=None, max_length=40)
    ends_at: str | None = Field(default=None, max_length=40)
    announcement_record_id: str | None = None
