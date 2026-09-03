from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class AdminQuestionCreateRequest(BaseModel):
    question_bank_id: str | None = Field(default=None, max_length=80)
    exam_code: str = Field(pattern="^(Z001|Z002|COMMON)$")
    subject: str = Field(min_length=1, max_length=40)
    module: str = Field(min_length=1, max_length=80)
    submodule: str = Field(min_length=1, max_length=80)
    question_type: str = Field(default="single_choice", pattern="^single_choice$")
    stem: str = Field(min_length=1, max_length=5000)
    option_a: str = Field(min_length=1, max_length=1000)
    option_b: str = Field(min_length=1, max_length=1000)
    option_c: str = Field(min_length=1, max_length=1000)
    option_d: str = Field(min_length=1, max_length=1000)
    answer: str = Field(pattern="^[ABCD]$")
    explanation: str | None = Field(default="", max_length=8000)
    difficulty: int = Field(default=2, ge=1, le=5)
    source_type: str | None = Field(default="manual", max_length=40)
    source_year: int | None = Field(default=None, ge=1900, le=2100)
    status: str = Field(default="archived", pattern="^(active|archived)$")
    review_status: str = Field(default="pending", pattern="^(pending|needs_changes|approved|rejected)$")
    review_note: str | None = Field(default=None, max_length=1000)


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


class AdminQuestionBulkStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(pattern="^(active|archived)$")
    ids: list[str] = Field(min_length=1, max_length=20000)


class AdminQuestionBulkStatusResponse(BaseModel):
    updated_count: int


class AdminQuestionBulkDeleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ids: list[str] = Field(min_length=1, max_length=20000)


class AdminQuestionBulkDeleteResponse(BaseModel):
    deleted_count: int


class AdminQuestionImageImportItem(BaseModel):
    exam_code: str | None = Field(default=None, max_length=20)
    subject: str | None = Field(default=None, max_length=40)
    module: str | None = Field(default=None, max_length=80)
    submodule: str | None = Field(default=None, max_length=80)
    question_type: str | None = Field(default="single_choice", max_length=40)
    stem: str | None = Field(default=None, max_length=5000)
    option_a: str | None = Field(default=None, max_length=1000)
    option_b: str | None = Field(default=None, max_length=1000)
    option_c: str | None = Field(default=None, max_length=1000)
    option_d: str | None = Field(default=None, max_length=1000)
    answer: str | None = Field(default=None, max_length=4)
    explanation: str | None = Field(default="", max_length=8000)
    difficulty: int | str | None = Field(default=2)
    source_type: str | None = Field(default="manual", max_length=40)
    source_year: int | str | None = Field(default=None)
    image_name: str | None = Field(default=None, max_length=200)
    image_index: int | None = Field(default=None, ge=0, le=9999)
    excel_row: int | None = Field(default=None, ge=2, le=1_000_000)


class AdminQuestionImageImportRequest(BaseModel):
    question_bank_id: str | None = Field(default=None, max_length=80)
    questions: list[AdminQuestionImageImportItem] = Field(min_length=1, max_length=200)


class AdminQuestionImageImportResultItem(BaseModel):
    index: int
    image_name: str | None = None
    valid: bool
    errors: list[str] = Field(default_factory=list)
    duplicate_id: str | None = None
    question: dict | None = None


class AdminQuestionImageImportDryRunResponse(BaseModel):
    total: int
    valid_count: int
    invalid_count: int
    duplicate_count: int
    items: list[AdminQuestionImageImportResultItem]


class AdminQuestionImageImportCommitResponse(BaseModel):
    inserted_count: int
    questions: list[dict]


class AdminQuestionFileRecognizeResponse(BaseModel):
    filename: str
    extension: str
    provider: str
    text: str
    questions: list[AdminQuestionImageImportItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AdminQuestionDetailResponse(BaseModel):
    question: dict


class AdminQuestionListResponse(BaseModel):
    items: list[dict]
    count: int


class AdminQuestionStatsResponse(BaseModel):
    active: int
    archived: int
    pending_review: int


class QuestionBankItem(BaseModel):
    id: str
    name: str
    question_count: int = 0
    created_at: str | None = None
    updated_at: str | None = None


class QuestionBankListResponse(BaseModel):
    items: list[QuestionBankItem] = Field(default_factory=list)


class QuestionBankCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class QuestionBankRenameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class QuestionBankPendingPublishPreviewResponse(BaseModel):
    question_bank_id: str
    question_bank_name: str
    pending_count: int


class QuestionBankPublishPendingRequest(BaseModel):
    expected_pending_count: int = Field(ge=1, le=20000)


class QuestionBankPublishPendingResponse(BaseModel):
    updated_count: int


class QuestionAdminPortalMeResponse(BaseModel):
    allowed: bool = True
    profile: dict
    permissions: dict


class QuestionAdminDashboardQuestionItem(BaseModel):
    question_id: str
    stem: str
    subject: str | None = None
    module: str | None = None
    wrong_count: int = 0
    attempt_count: int = 0
    accuracy: float = 0


class QuestionAdminDashboardResponse(BaseModel):
    today_practicing_users: int = 0
    online_members: int = 0
    online_window_minutes: int = 15
    registered_users: int = 0
    today_registered_users: int = 0
    difficult_questions_count: int = 0
    difficult_questions_page: int = 1
    difficult_questions_page_size: int = 20
    difficult_questions: list[QuestionAdminDashboardQuestionItem] = Field(default_factory=list)


class AdminCommunityOverviewResponse(BaseModel):
    total_posts: int = 0
    published_posts: int = 0
    archived_posts: int = 0
    today_posts: int = 0
    total_reports: int = 0
    pending_reports: int = 0
    reviewing_reports: int = 0
    pending_experience_reviews: int = 0


class AdminCommunityPostItem(BaseModel):
    id: str
    author_id: str | None = None
    author_name: str = "研友"
    author_avatar: str = "研"
    category: str = "备考日常"
    post_type: str = "chat"
    experience_stages: list[str] = Field(default_factory=list)
    title: str = ""
    content: str = ""
    media: list[dict] = Field(default_factory=list)
    like_count: int = 0
    comment_count: int = 0
    view_count: int = 0
    is_published: bool = True
    is_featured: bool = False
    review_status: Literal["pending", "approved", "rejected"] = "approved"
    review_version: int = 0
    review_reason_code: str | None = None
    review_note: str | None = None
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    submitted_at: str | None = None
    admin_deleted_at: str | None = None
    admin_deleted_by: str | None = None
    admin_purge_after: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class AdminCommunityPostListResponse(BaseModel):
    items: list[AdminCommunityPostItem] = Field(default_factory=list)
    count: int = 0


class AdminCommunityTrashListResponse(BaseModel):
    items: list[AdminCommunityPostItem] = Field(default_factory=list)
    count: int = 0
    retention_days: int = 7


class AdminCommunityTrashMutationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ids: list[str] = Field(min_length=1, max_length=200)


class AdminCommunityTrashMutationResponse(BaseModel):
    affected_count: int


class AdminCommunityPostDetailResponse(BaseModel):
    post: AdminCommunityPostItem
    comments: list["AdminCommunityCommentItem"] = Field(default_factory=list)


class AdminCommunityExperienceReviewHistoryItem(BaseModel):
    id: str
    submission_version: int
    action: Literal["submitted", "approved", "rejected"]
    from_status: Literal["pending", "approved", "rejected"] | None = None
    to_status: Literal["pending", "approved", "rejected"]
    reason_code: str | None = None
    review_note: str | None = None
    actor_user_id: str | None = None
    created_at: str | None = None


class AdminCommunityExperienceReviewListResponse(BaseModel):
    items: list[AdminCommunityPostItem] = Field(default_factory=list)
    count: int = 0


class AdminCommunityExperienceReviewDetailResponse(BaseModel):
    post: AdminCommunityPostItem
    review_history: list[AdminCommunityExperienceReviewHistoryItem] = Field(default_factory=list)


class AdminCommunityExperienceReviewDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["approved", "rejected"]
    reason_code: Literal[
        "advertising_or_diversion",
        "false_or_misleading",
        "infringement",
        "privacy",
        "inappropriate",
        "low_quality",
        "other",
    ] | None = None
    review_note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_rejection_reason(self) -> "AdminCommunityExperienceReviewDecisionRequest":
        self.review_note = str(self.review_note or "").strip() or None
        if self.decision == "rejected" and (not self.reason_code or not self.review_note):
            raise ValueError("驳回经验贴时必须选择官方理由并填写处理说明")
        if self.decision == "approved":
            self.reason_code = None
        return self


class AdminCommunityCommentItem(BaseModel):
    id: str
    author_id: str | None = None
    author_name: str = "研友"
    author_avatar: str = "研"
    content: str = ""
    like_count: int = 0
    is_published: bool = True
    moderation_note: str | None = None
    moderated_at: str | None = None
    created_at: str | None = None


class AdminCommunityPostVisibilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_published: bool


class AdminCommunityCommentVisibilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_published: bool


class AdminCommunityBulkVisibilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_published: bool
    ids: list[str] = Field(min_length=1, max_length=200)


class AdminCommunityBulkVisibilityResponse(BaseModel):
    updated_count: int


class AdminCommunityBulkFeaturedRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_featured: bool
    ids: list[str] = Field(min_length=1, max_length=200)


class AdminCommunityBulkFeaturedResponse(BaseModel):
    updated_count: int


class AdminCommunityReportItem(BaseModel):
    id: str
    target_type: Literal["post", "comment"]
    post_id: str
    comment_id: str | None = None
    reporter: dict = Field(default_factory=dict)
    target: dict = Field(default_factory=dict)
    post_title: str = ""
    target_excerpt: str = ""
    reason: str
    content: str = ""
    status: Literal["pending", "reviewing", "resolved", "dismissed"] = "pending"
    moderation_action: Literal[
        "none",
        "hide_post",
        "restore_post",
        "hide_comment",
        "restore_comment",
    ] = "none"
    admin_note: str | None = None
    created_at: str | None = None
    handled_at: str | None = None


class AdminCommunityReportListResponse(BaseModel):
    items: list[AdminCommunityReportItem] = Field(default_factory=list)
    count: int = 0


class AdminCommunityReportStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["pending", "reviewing", "resolved", "dismissed"]
    moderation_action: Literal[
        "none",
        "hide_post",
        "restore_post",
        "hide_comment",
        "restore_comment",
    ] = "none"
    admin_note: str | None = Field(default=None, max_length=1000)


class AdminCommunityAppealItem(BaseModel):
    id: str
    target_type: Literal["post", "comment"]
    post_id: str
    comment_id: str | None = None
    appellant: dict = Field(default_factory=dict)
    target: dict = Field(default_factory=dict)
    post_title: str = ""
    target_excerpt: str = ""
    content: str
    status: Literal["pending", "reviewing", "resolved", "dismissed"] = "pending"
    moderation_action: Literal["none", "restore_post", "restore_comment", "uphold"] = "none"
    admin_note: str | None = None
    created_at: str | None = None
    handled_at: str | None = None


class AdminCommunityAppealListResponse(BaseModel):
    items: list[AdminCommunityAppealItem] = Field(default_factory=list)
    count: int = 0


class AdminCommunityAppealStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["pending", "reviewing", "resolved", "dismissed"]
    moderation_action: Literal["none", "restore_post", "restore_comment", "uphold"] = "none"
    admin_note: str | None = Field(default=None, max_length=1000)


class QuestionAdminPortalOperationsOverviewResponse(BaseModel):
    total_users: int = 0
    new_today: int = 0
    new_week: int = 0
    active_week: int = 0
    active_members: int = 0
    published_home_items: int = 0
    published_announcements: int = 0
    scoreline_draft_runs: int = 0
    announcement_draft_runs: int = 0
    major_catalog_draft_runs: int = 0
    recent_import_failures: int = 0


class QuestionAdminPortalUserItem(BaseModel):
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


class QuestionAdminPortalUserListResponse(BaseModel):
    items: list[QuestionAdminPortalUserItem] = Field(default_factory=list)
    count: int = 0


class QuestionAdminPortalUserDetailResponse(BaseModel):
    profile: dict = Field(default_factory=dict)
    answer_summary: dict = Field(default_factory=dict)
    subject_accuracy: list[dict] = Field(default_factory=list)
    recent_answers: list[dict] = Field(default_factory=list)
    membership_orders: list[dict] = Field(default_factory=list)
    admin_actions: list[dict] = Field(default_factory=list)


class QuestionAdminPortalUserDisableRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    disabled: bool


class QuestionAdminPortalMembershipRenewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    months: Literal[1, 4]


class AdminOperationsImportPreviewResponse(BaseModel):
    dataset: str
    source_sha256: str
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    preview_items: list[dict] = Field(default_factory=list)
    preview_truncated: bool = False
    warnings: list[str] = Field(default_factory=list)


class AdminOperationsImportRunItem(BaseModel):
    id: str
    source_filename: str = ""
    source_sha256: str = ""
    statistics: dict = Field(default_factory=dict)
    status: str = "draft"
    created_by: str | None = None
    published_by: str | None = None
    created_at: str | None = None
    published_at: str | None = None
    updated_at: str | None = None
    record_count: int = 0


class AdminOperationsImportRunListResponse(BaseModel):
    items: list[AdminOperationsImportRunItem] = Field(default_factory=list)
    count: int = 0


class AdminOperationsImportCommitResponse(BaseModel):
    run: AdminOperationsImportRunItem
    created: bool = True


class AdminAnnouncementRecordUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str | None = Field(default=None, pattern="^(draft|published|archived)$")
    notice_year: str | None = Field(default=None, pattern="^20\\d{2}$")
    region: str | None = Field(default=None, min_length=1, max_length=60)
    school_name: str | None = Field(default=None, min_length=1, max_length=160)
    unit_name: str | None = Field(default=None, max_length=160)
    notice_type: str | None = Field(default=None, pattern="^(brochure|scoreline_retest)$")
    title: str | None = Field(default=None, min_length=1, max_length=500)
    summary: str | None = Field(default=None, max_length=5000)
    notice_date: str | None = Field(default=None, pattern="^20\\d{2}-\\d{2}-\\d{2}$")
    source_url: str | None = Field(default=None, max_length=1000)
    content_text: str | None = Field(default=None, max_length=100000)
    sort_order: int | None = Field(default=None, ge=-10000, le=10000)


class AdminScorelineRecordListResponse(BaseModel):
    items: list[dict] = Field(default_factory=list)
    count: int = 0
    filter_years: list[str] = Field(default_factory=list)
    filter_regions: list[str] = Field(default_factory=list)


class AdminScorelineRecordUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score_year: str | None = Field(default=None, pattern="^20\\d{2}$")
    region: str | None = Field(default=None, min_length=1, max_length=60)
    school_name: str | None = Field(default=None, min_length=1, max_length=160)
    unit_name: str | None = Field(default=None, max_length=160)
    score_raw: str | None = Field(default=None, min_length=1, max_length=1000)
    score_kind: str | None = Field(
        default=None,
        pattern="^(score|missing|unavailable|official|multiple|note)$",
    )
    source_url: str | None = Field(default=None, max_length=1000)
    source_note: str | None = Field(default=None, max_length=2000)


class AdminMajorCatalogRecordListResponse(BaseModel):
    items: list[dict] = Field(default_factory=list)
    count: int = 0
    filter_years: list[str] = Field(default_factory=list)
    filter_regions: list[str] = Field(default_factory=list)
    filter_exam_codes: list[str] = Field(default_factory=list)
    filter_schools: list[dict[str, str]] = Field(default_factory=list)


class AdminMajorCatalogRecordUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    region: str | None = Field(default=None, min_length=1, max_length=60)
    school_name: str | None = Field(default=None, min_length=1, max_length=160)
    department_name: str | None = Field(default=None, min_length=1, max_length=300)
    program_name: str | None = Field(default=None, min_length=1, max_length=300)
    program_code: str | None = Field(default=None, max_length=60)
    direction_name: str | None = Field(default=None, min_length=1, max_length=500)
    tutor: str | None = Field(default=None, max_length=300)
    exam_code: str | None = Field(default=None, pattern="^(Z001|Z002)$")
    degree: str | None = Field(default=None, max_length=100)
    study_mode: str | None = Field(default=None, max_length=100)


class AdminScorelineBootstrapRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score_year: str = Field(pattern="^20\\d{2}$")
    region: str = Field(min_length=1, max_length=60)
    school_name: str = Field(min_length=1, max_length=160)
    unit_name: str = Field(default="", max_length=160)
    score_raw: str = Field(min_length=1, max_length=1000)
    score_kind: str = Field(pattern="^(score|missing|unavailable|official|multiple|note)$")


class AdminScorelineBootstrapRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    records: list[AdminScorelineBootstrapRecord] = Field(min_length=1, max_length=1000)


class AdminHomeContentItem(BaseModel):
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


class AdminHomeContentListResponse(BaseModel):
    items: list[AdminHomeContentItem] = Field(default_factory=list)
    count: int = 0


class AdminHomeContentUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slot: str = Field(pattern="^(focus|news)$")
    title: str = Field(min_length=1, max_length=120)
    subtitle: str = Field(default="", max_length=240)
    badge: str = Field(default="", max_length=30)
    source: str = Field(default="", max_length=80)
    display_date: str | None = Field(default=None, max_length=20)
    cover_label: str = Field(default="", max_length=40)
    tone: str = Field(default="is-blue", pattern="^(is-blue|is-violet|is-mint|is-orange)$")
    target_url: str = Field(default="", max_length=1000)
    route_key: str = Field(default="", max_length=80)
    sort_order: int = Field(default=0, ge=-10000, le=10000)
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")
    starts_at: str | None = Field(default=None, max_length=40)
    ends_at: str | None = Field(default=None, max_length=40)
    announcement_record_id: str | None = Field(default=None, max_length=80)
