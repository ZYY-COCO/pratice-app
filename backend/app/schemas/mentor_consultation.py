from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


MentorExamType = Literal["Z001", "Z002", "application"]
MentorOnlineStatus = Literal["online", "offline", "busy"]
MentorVerificationStatus = Literal["unverified", "pending", "verified", "rejected", "revoked"]
MentorProfileChangeRequestStatus = Literal["pending", "approved", "rejected"]
MentorSlotStatus = Literal["available", "held", "booked", "expired", "closed"]
MentorConsultationType = Literal["instant", "booking"]
MentorConsultationOrderStatus = Literal[
    "draft",
    "pending_payment",
    "pending_accept",
    "accepted",
    "in_progress",
    "completed",
    "rejected",
    "timeout",
    "refunded",
    "cancelled",
    "booked",
]
MentorPaymentStatus = Literal["unpaid", "paid", "refunding", "refunded", "failed"]
MentorMessageType = Literal["text", "image", "voice", "system"]
MentorSenderRole = Literal["applicant", "mentor", "system"]
MentorConsultationReportRole = Literal["applicant", "mentor"]
MentorConsultationReportParticipantRole = Literal["reporter", "respondent"]
MentorConsultationReportStatus = Literal["pending", "reviewing", "resolved", "dismissed"]
MentorConsultationCasePriority = Literal["normal", "high", "urgent"]
MentorConsultationReportAppealDecision = Literal["none", "uphold", "reopen"]
MentorConsultationReportResolution = Literal[
    "none",
    "continue_service",
    "refund_full",
    "refund_partial",
    "close_service",
    "warn_participant",
    "hide_review",
    "restore_review",
]


def validate_mentor_exam_score(exam_type: MentorExamType, score: int | None) -> None:
    """Keep application-based admissions free of synthetic entrance-exam scores."""
    if exam_type == "application":
        if score is not None:
            raise ValueError("申请制无需填写初试成绩")
        return
    if score is None:
        raise ValueError("Z001、Z002 必须填写初试成绩")


class MentorAvailabilitySlotItem(BaseModel):
    id: str
    starts_at: str | None = None
    ends_at: str | None = None
    price: float | int | None = None
    status: MentorSlotStatus = "available"


class MentorReviewItem(BaseModel):
    id: str
    author: str = "匿名用户"
    rating: float
    date: str | None = None
    content: str = ""


class MentorPublicItem(BaseModel):
    id: str
    display_name: str
    avatar: str = "研"
    avatar_url: str | None = None
    avatar_tone: str = "blue"
    school: str
    major: str
    admission_year: int
    graduation_year: int | None = None
    exam_type: MentorExamType
    score: int | None = Field(default=None, ge=0, le=150)
    rating: float = Field(default=0, ge=0, le=5)
    rating_count: int = Field(default=0, ge=0)
    consult_count: int = Field(default=0, ge=0)
    price: float | int = Field(ge=0)
    consultation_window_minutes: int = Field(default=60, ge=15, le=180)
    consultation_enabled: bool = True
    online_status: MentorOnlineStatus = "offline"
    accepts_booking: bool = True
    is_featured: bool = False
    recommend_score: int = Field(default=0, ge=0, le=100)
    bio: str = ""
    story: str = ""
    skills: list[str] = Field(default_factory=list)
    verified: bool = True


class MentorPublicListResponse(BaseModel):
    items: list[MentorPublicItem] = Field(default_factory=list)
    count: int = 0


class MentorPublicDetailResponse(BaseModel):
    mentor: MentorPublicItem
    reviews: list[MentorReviewItem] = Field(default_factory=list)
    available_slots: list[MentorAvailabilitySlotItem] = Field(default_factory=list)


class MentorOwnerProfileResponse(BaseModel):
    mentor: MentorPublicItem


class MentorOwnerAvailabilityUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    online_status: MentorOnlineStatus


class MentorProfileChangeRequestCreateRequest(BaseModel):
    """A mentor-owned profile update that must be approved before publication."""

    model_config = ConfigDict(extra="forbid")

    school: str = Field(min_length=1, max_length=120)
    major: str = Field(min_length=1, max_length=120)
    exam_type: MentorExamType
    score: int | None = Field(default=None, ge=0, le=150)
    skills: list[str] = Field(default_factory=list, max_length=4)
    bio: str = Field(default="", max_length=500)
    price_cents: int = Field(ge=0, le=100000)

    @model_validator(mode="after")
    def validate_exam_score(self) -> "MentorProfileChangeRequestCreateRequest":
        validate_mentor_exam_score(self.exam_type, self.score)
        return self


class MentorProfileChangeRequestItem(BaseModel):
    id: str
    mentor_id: str
    owner_user_id: str
    school: str
    major: str
    exam_type: MentorExamType
    score: int | None = Field(default=None, ge=0, le=150)
    skills: list[str] = Field(default_factory=list)
    bio: str = ""
    price: float | int = Field(ge=0)
    request_status: MentorProfileChangeRequestStatus = "pending"
    admin_note: str | None = None
    reviewed_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class MentorProfileChangeRequestStatusResponse(BaseModel):
    request: MentorProfileChangeRequestItem | None = None


class AdminMentorProfileChangeRequestListResponse(BaseModel):
    items: list[MentorProfileChangeRequestItem] = Field(default_factory=list)
    count: int = 0


class AdminMentorProfileChangeDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["approve", "reject"]
    admin_note: str | None = Field(default=None, max_length=1000)


class MentorOwnerAvailabilitySlotListResponse(BaseModel):
    items: list[MentorAvailabilitySlotItem] = Field(default_factory=list)
    count: int = 0
    next_cursor: str | None = None
    has_more: bool = False


class MentorOwnerAvailabilitySlotCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    starts_at: datetime
    ends_at: datetime
    price_cents: int | None = Field(default=None, ge=0, le=100000)


class MentorOwnerAvailabilitySlotStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["available", "closed"]


class AdminMentorProfileItem(MentorPublicItem):
    legal_name: str
    owner_user_id: str | None = None
    verification_status: MentorVerificationStatus
    is_published: bool
    created_at: str | None = None
    updated_at: str | None = None


class AdminMentorProfileListResponse(BaseModel):
    items: list[AdminMentorProfileItem] = Field(default_factory=list)
    count: int = 0


class MentorVerificationDocumentItem(BaseModel):
    id: str
    file_url: str
    file_name: str
    document_type: Literal["admission_notice", "student_card", "other"] = "other"
    mime_type: str | None = None
    created_at: str | None = None


class MentorVerificationApplicationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    legal_name: str = Field(min_length=2, max_length=40)
    school: str = Field(min_length=1, max_length=120)
    major: str = Field(min_length=1, max_length=120)
    admission_year: int = Field(ge=2000, le=2100)
    graduation_year: int | None = Field(default=None, ge=2000, le=2100)
    exam_type: MentorExamType
    score: int | None = Field(default=None, ge=0, le=150)
    skills: list[str] = Field(default_factory=list, max_length=4)
    bio: str = Field(default="", max_length=500)
    price_cents: int = Field(default=3900, ge=0, le=100000)
    consultation_enabled: bool = True

    @model_validator(mode="after")
    def validate_exam_score(self) -> "MentorVerificationApplicationCreateRequest":
        validate_mentor_exam_score(self.exam_type, self.score)
        return self


class MentorVerificationApplicationItem(BaseModel):
    id: str
    applicant_user_id: str
    legal_name: str
    school: str
    major: str
    admission_year: int
    graduation_year: int | None = None
    exam_type: MentorExamType
    score: int | None = Field(default=None, ge=0, le=150)
    skills: list[str] = Field(default_factory=list)
    bio: str = ""
    price: float | int = Field(ge=0)
    consultation_enabled: bool = True
    application_status: Literal["pending", "approved", "rejected", "revoked"] = "pending"
    admin_note: str | None = None
    revocation_reason: str | None = None
    revoked_at: str | None = None
    reviewed_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    document_count: int = 0


class MentorVerificationApplicationStatusResponse(BaseModel):
    application: MentorVerificationApplicationItem | None = None


class MentorVerificationDocumentUploadResponse(MentorVerificationDocumentItem):
    pass


class AdminMentorVerificationApplicationListResponse(BaseModel):
    items: list[MentorVerificationApplicationItem] = Field(default_factory=list)
    count: int = 0


class AdminMentorVerificationApplicationDetailResponse(BaseModel):
    application: MentorVerificationApplicationItem
    applicant: dict = Field(default_factory=dict)
    documents: list[MentorVerificationDocumentItem] = Field(default_factory=list)


class AdminMentorVerificationDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["approve", "reject"]
    admin_note: str | None = Field(default=None, max_length=1000)


class AdminMentorQualificationRevocationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=5, max_length=1000)


class AdminMentorProfileCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner_user_id: UUID | None = None
    legal_name: str = Field(min_length=2, max_length=40)
    avatar: str | None = Field(default=None, min_length=1, max_length=4)
    avatar_url: str | None = Field(default=None, max_length=2048)
    avatar_tone: Literal["mint", "blue", "warm", "violet"] = "blue"
    school: str = Field(min_length=1, max_length=120)
    major: str = Field(min_length=1, max_length=120)
    admission_year: int = Field(ge=2000, le=2100)
    graduation_year: int | None = Field(default=None, ge=2000, le=2100)
    exam_type: MentorExamType
    score: int | None = Field(default=None, ge=0, le=150)
    bio: str = Field(default="", max_length=500)
    story: str = Field(default="", max_length=2000)
    price_cents: int = Field(default=3900, ge=0, le=100000)
    consultation_window_minutes: int = Field(default=60, ge=15, le=180)
    consultation_enabled: bool = True
    online_status: MentorOnlineStatus = "offline"
    accepts_booking: bool = True
    verification_status: MentorVerificationStatus = "pending"
    is_published: bool = False
    is_featured: bool = False
    recommend_score: int = Field(default=0, ge=0, le=100)
    rating: float = Field(default=0, ge=0, le=5)
    rating_count: int = Field(default=0, ge=0)
    consult_count: int = Field(default=0, ge=0)
    skills: list[str] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def validate_exam_score(self) -> "AdminMentorProfileCreateRequest":
        validate_mentor_exam_score(self.exam_type, self.score)
        return self


class AdminMentorProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner_user_id: UUID | None = None
    legal_name: str | None = Field(default=None, min_length=2, max_length=40)
    avatar: str | None = Field(default=None, min_length=1, max_length=4)
    avatar_url: str | None = Field(default=None, max_length=2048)
    avatar_tone: Literal["mint", "blue", "warm", "violet"] | None = None
    school: str | None = Field(default=None, min_length=1, max_length=120)
    major: str | None = Field(default=None, min_length=1, max_length=120)
    admission_year: int | None = Field(default=None, ge=2000, le=2100)
    graduation_year: int | None = Field(default=None, ge=2000, le=2100)
    exam_type: MentorExamType | None = None
    score: int | None = Field(default=None, ge=0, le=150)
    bio: str | None = Field(default=None, max_length=500)
    story: str | None = Field(default=None, max_length=2000)
    price_cents: int | None = Field(default=None, ge=0, le=100000)
    consultation_window_minutes: int | None = Field(default=None, ge=15, le=180)
    consultation_enabled: bool | None = None
    online_status: MentorOnlineStatus | None = None
    accepts_booking: bool | None = None
    verification_status: MentorVerificationStatus | None = None
    is_published: bool | None = None
    is_featured: bool | None = None
    recommend_score: int | None = Field(default=None, ge=0, le=100)
    rating: float | None = Field(default=None, ge=0, le=5)
    rating_count: int | None = Field(default=None, ge=0)
    consult_count: int | None = Field(default=None, ge=0)
    skills: list[str] | None = Field(default=None, max_length=12)


class AdminMentorAvailabilitySlotItem(MentorAvailabilitySlotItem):
    mentor_id: str
    created_at: str | None = None
    updated_at: str | None = None


class AdminMentorAvailabilitySlotListResponse(BaseModel):
    items: list[AdminMentorAvailabilitySlotItem] = Field(default_factory=list)
    count: int = 0


class AdminMentorAvailabilitySlotCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    starts_at: datetime
    ends_at: datetime
    price_cents: int | None = Field(default=None, ge=0, le=100000)
    status: MentorSlotStatus = "available"


class AdminMentorAvailabilitySlotUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    starts_at: datetime | None = None
    ends_at: datetime | None = None
    price_cents: int | None = Field(default=None, ge=0, le=100000)
    status: MentorSlotStatus | None = None


class MentorFavoriteItem(BaseModel):
    mentor_id: str
    created_at: str | None = None
    mentor: MentorPublicItem | None = None


class MentorFavoriteListResponse(BaseModel):
    items: list[MentorFavoriteItem] = Field(default_factory=list)
    count: int = 0


class MentorFavoriteToggleResponse(BaseModel):
    mentor_id: str
    is_favorited: bool


class MentorConsultationQuestionnaire(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=80)
    school: str = Field(min_length=1, max_length=160)
    major: str = Field(min_length=1, max_length=160)
    grade: str = Field(default="其他", max_length=40)
    graduation_year: int | None = Field(default=None, ge=2000, le=2100)
    question: str = Field(default="", max_length=500)


class MentorConsultationOrderCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mentor_id: UUID
    client_order_id: str = Field(min_length=1, max_length=80)
    consultation_type: MentorConsultationType
    slot_id: UUID | None = None
    questionnaire: MentorConsultationQuestionnaire
    service_rules_version: str = Field(min_length=1, max_length=32)
    service_rules_accepted: bool


class MentorConsultationPaymentCapabilityResponse(BaseModel):
    order_creation_enabled: bool = False
    real_payment_enabled: bool = False
    demo_payment_enabled: bool = False
    payment_mode: Literal["demo", "real", "disabled"] = "disabled"
    provider: str = "unconfigured"
    checkout_configured: bool = False
    withdrawal_enabled: bool = False
    service_rules_version: str
    message: str


class MentorConsultationPaymentIntentResponse(BaseModel):
    order_id: str
    order_no: str
    provider: str
    provider_order_id: str
    amount_cents: int = Field(ge=0)
    currency: str = "CNY"
    status: Literal["pending", "paid"]
    checkout_url: str | None = None
    message: str


class MentorConsultationPaymentWebhookRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str = Field(min_length=1, max_length=80)
    provider_event_id: str = Field(min_length=1, max_length=160)
    order_no: str = Field(min_length=1, max_length=80)
    payment_reference: str = Field(min_length=1, max_length=160)
    status: Literal["paid", "failed", "refunded", "refund_failed"]
    amount_cents: int = Field(ge=0, le=100000)
    refund_amount_cents: int | None = Field(default=None, ge=0, le=100000)
    refund_reference: str | None = Field(default=None, max_length=160)
    failure_reason: str | None = Field(default=None, max_length=500)
    raw_payload: dict | None = None


class MentorConsultationPaymentWebhookResponse(BaseModel):
    detail: str
    order: "MentorConsultationOrderItem"
    idempotent: bool = False


class MentorConsultationOrderItem(BaseModel):
    id: str
    order_no: str
    client_order_id: str | None = None
    applicant_user_id: str
    mentor_id: str
    slot_id: str | None = None
    consultation_type: MentorConsultationType
    order_status: MentorConsultationOrderStatus
    payment_status: MentorPaymentStatus
    questionnaire: MentorConsultationQuestionnaire
    price: float | int = Field(ge=0)
    consultation_window_minutes: int = Field(default=60, ge=15, le=180)
    payment_reference: str | None = None
    payment_expires_at: str | None = None
    payment_mode: Literal["demo", "real"] = "real"
    accepted_at: str | None = None
    expires_at: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    applicant_completion_confirmed_at: str | None = None
    mentor_completion_confirmed_at: str | None = None
    refund_amount: float | int = Field(default=0, ge=0)
    refund_reference: str | None = None
    rejection_reason: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class MentorConsultationOrderListResponse(BaseModel):
    items: list[MentorConsultationOrderItem] = Field(default_factory=list)
    count: int = 0
    next_cursor: str | None = None
    has_more: bool = False


class MentorConsultationDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["accept", "reject"]
    reason: str = Field(default="", max_length=500)


class MentorConsultationMessageCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_type: MentorMessageType = "text"
    content: str = Field(default="", max_length=5000)
    duration_seconds: int | None = Field(default=None, ge=0, le=3600)
    client_message_id: str | None = Field(default=None, min_length=1, max_length=80)


class MentorConsultationMessageItem(BaseModel):
    id: str
    sender_role: MentorSenderRole
    message_type: MentorMessageType
    content: str = ""
    duration_seconds: int | None = None
    client_message_id: str | None = None
    created_at: str | None = None


class MentorConsultationMessageListResponse(BaseModel):
    items: list[MentorConsultationMessageItem] = Field(default_factory=list)
    count: int = 0


class MentorConsultationReviewCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rating: int = Field(ge=1, le=5)
    tags: list[str] = Field(default_factory=list, max_length=8)
    content: str = Field(default="", max_length=300)


class MentorConsultationReviewCreateResponse(MentorReviewItem):
    order_id: str


class MentorConsultationReportCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_type: str = Field(min_length=1, max_length=60)
    content: str = Field(min_length=20, max_length=500)


class MentorConsultationReportResponseRequest(BaseModel):
    """A respondent's factual explanation for an open consultation report."""

    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=20, max_length=500)


class MentorConsultationReportAppealCreateRequest(BaseModel):
    """A participant's one-time request to review a closed consultation report."""

    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=20, max_length=500)


class MentorConsultationReportAppealItem(BaseModel):
    id: str
    report_id: str
    appellant_role: MentorConsultationReportParticipantRole
    content: str
    status: MentorConsultationReportStatus = "pending"
    decision: MentorConsultationReportAppealDecision = "none"
    admin_note: str | None = None
    evidence_count: int = Field(default=0, ge=0)
    first_response_due_at: str | None = None
    first_response_at: str | None = None
    priority: MentorConsultationCasePriority = "normal"
    escalation_level: int = Field(default=0, ge=0)
    escalated_at: str | None = None
    sla_status: str = "on_track"
    created_at: str | None = None
    handled_at: str | None = None


class MentorConsultationReportItem(BaseModel):
    id: str
    order_id: str
    reporter_role: MentorConsultationReportRole
    target_role: MentorConsultationReportRole
    issue_type: str
    content: str
    respondent_content: str | None = None
    responded_at: str | None = None
    participation_role: MentorConsultationReportParticipantRole = "reporter"
    can_respond: bool = False
    status: MentorConsultationReportStatus = "pending"
    resolution: MentorConsultationReportResolution = "none"
    refund_amount: float | int = Field(default=0, ge=0)
    admin_note: str | None = None
    reporter_evidence_count: int = Field(default=0, ge=0)
    respondent_evidence_count: int = Field(default=0, ge=0)
    can_appeal: bool = False
    appeal_id: str | None = None
    appeal_status: MentorConsultationReportStatus | None = None
    appeal_decision: MentorConsultationReportAppealDecision | None = None
    appeal_content: str | None = None
    appeal_admin_note: str | None = None
    appeal_evidence_count: int = Field(default=0, ge=0)
    appeal_created_at: str | None = None
    appeal_handled_at: str | None = None
    appeal_first_response_due_at: str | None = None
    appeal_first_response_at: str | None = None
    appeal_priority: MentorConsultationCasePriority | None = None
    appeal_escalation_level: int = Field(default=0, ge=0)
    appeal_escalated_at: str | None = None
    appeal_sla_status: str | None = None
    first_response_due_at: str | None = None
    first_response_at: str | None = None
    priority: MentorConsultationCasePriority = "normal"
    escalation_level: int = Field(default=0, ge=0)
    escalated_at: str | None = None
    sla_status: str = "on_track"
    created_at: str | None = None
    handled_at: str | None = None


class MentorConsultationReportCreateResponse(MentorConsultationReportItem):
    pass


class MentorConsultationReportListResponse(BaseModel):
    items: list[MentorConsultationReportItem] = Field(default_factory=list)
    count: int = 0


class MentorConsultationReportEvidenceUploadResponse(BaseModel):
    id: str
    file_name: str
    mime_type: str | None = None
    submitter_role: MentorConsultationReportParticipantRole = "reporter"
    created_at: str | None = None


class MentorConsultationReportAppealEvidenceUploadResponse(BaseModel):
    id: str
    file_name: str
    mime_type: str | None = None
    created_at: str | None = None


class MentorConsultationReportAppealListResponse(BaseModel):
    items: list[MentorConsultationReportAppealItem] = Field(default_factory=list)
    count: int = 0


class AdminMentorConsultationReportItem(MentorConsultationReportItem):
    reporter: dict = Field(default_factory=dict)
    target: dict = Field(default_factory=dict)
    order_no: str | None = None
    admin_note: str | None = None
    handled_at: str | None = None
    evidence_count: int = 0


class AdminMentorConsultationReportListResponse(BaseModel):
    items: list[AdminMentorConsultationReportItem] = Field(default_factory=list)
    count: int = 0


class AdminMentorConsultationReportAppealItem(MentorConsultationReportAppealItem):
    appellant: dict = Field(default_factory=dict)
    report: dict = Field(default_factory=dict)
    order_no: str | None = None


class AdminMentorConsultationReportEvidenceItem(MentorConsultationReportEvidenceUploadResponse):
    file_url: str


class AdminMentorConsultationReviewItem(BaseModel):
    """Backoffice-only projection of the review attached to a consultation order."""

    id: str
    order_id: str
    mentor_id: str
    reviewer_user_id: str | None = None
    reviewer_display_name: str = "匿名用户"
    rating: float | int = Field(ge=1, le=5)
    tags: list[str] = Field(default_factory=list)
    content: str = ""
    is_published: bool = True
    created_at: str | None = None


class AdminMentorConsultationReportDetailResponse(BaseModel):
    report: AdminMentorConsultationReportItem
    evidence: list[AdminMentorConsultationReportEvidenceItem] = Field(default_factory=list)
    review: AdminMentorConsultationReviewItem | None = None
    order: dict = Field(default_factory=dict)
    messages: list[dict] = Field(default_factory=list)
    events: list[dict] = Field(default_factory=list)


class AdminMentorConsultationReportAppealEvidenceItem(MentorConsultationReportAppealEvidenceUploadResponse):
    file_url: str


class AdminMentorConsultationReportAppealListResponse(BaseModel):
    items: list[AdminMentorConsultationReportAppealItem] = Field(default_factory=list)
    count: int = 0


class AdminMentorConsultationReportAppealDetailResponse(BaseModel):
    appeal: AdminMentorConsultationReportAppealItem
    evidence: list[AdminMentorConsultationReportAppealEvidenceItem] = Field(default_factory=list)
    report: AdminMentorConsultationReportItem
    report_evidence: list[AdminMentorConsultationReportEvidenceItem] = Field(default_factory=list)
    order: dict = Field(default_factory=dict)
    messages: list[dict] = Field(default_factory=list)
    events: list[dict] = Field(default_factory=list)


class AdminMentorConsultationReportStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: MentorConsultationReportStatus
    resolution: MentorConsultationReportResolution = "none"
    refund_amount: float | int = Field(default=0, ge=0, le=1000)
    admin_note: str | None = Field(default=None, max_length=1000)
    priority: MentorConsultationCasePriority | None = None


class AdminMentorConsultationReportAppealStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: MentorConsultationReportStatus
    decision: MentorConsultationReportAppealDecision = "none"
    admin_note: str | None = Field(default=None, max_length=1000)
    priority: MentorConsultationCasePriority | None = None


class AdminMentorConsultationOrderItem(MentorConsultationOrderItem):
    """Backoffice order projection with the parties and current support workload."""

    applicant: dict = Field(default_factory=dict)
    mentor: dict = Field(default_factory=dict)
    slot: dict | None = None
    report_count: int = 0
    open_report_count: int = 0
    overdue_report_count: int = 0
    escalated_report_count: int = 0
    latest_report_status: MentorConsultationReportStatus | None = None
    attention: str | None = None
    attention_reason: str | None = None


class AdminMentorConsultationOrderListResponse(BaseModel):
    items: list[AdminMentorConsultationOrderItem] = Field(default_factory=list)
    count: int = 0


class AdminMentorConsultationOrderDetailResponse(BaseModel):
    order: AdminMentorConsultationOrderItem
    reports: list[AdminMentorConsultationReportItem] = Field(default_factory=list)
    messages: list[dict] = Field(default_factory=list)
    events: list[dict] = Field(default_factory=list)


class AdminMentorConsultationOrderInterventionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["notify_participants", "refund_full", "refund_partial", "close_service"]
    refund_amount: float | int = Field(default=0, ge=0, le=1000)
    admin_note: str = Field(min_length=1, max_length=1000)
