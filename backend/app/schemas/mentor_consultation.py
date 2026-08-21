from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


MentorExamType = Literal["Z001", "Z002", "application"]
MentorOnlineStatus = Literal["online", "offline", "busy"]
MentorVerificationStatus = Literal["unverified", "pending", "verified", "rejected"]
MentorSlotStatus = Literal["available", "booked", "expired", "closed"]
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
    score: int = Field(ge=0, le=150)
    rating: float = Field(default=0, ge=0, le=5)
    rating_count: int = Field(default=0, ge=0)
    consult_count: int = Field(default=0, ge=0)
    price: float | int = Field(ge=0)
    consultation_window_minutes: int = Field(default=60, ge=15, le=180)
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


class MentorOwnerAvailabilitySlotListResponse(BaseModel):
    items: list[MentorAvailabilitySlotItem] = Field(default_factory=list)
    count: int = 0


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
    score: int = Field(ge=0, le=150)
    skills: list[str] = Field(default_factory=list, max_length=4)
    bio: str = Field(default="", max_length=500)
    price_cents: int = Field(default=3900, ge=0, le=100000)


class MentorVerificationApplicationItem(BaseModel):
    id: str
    applicant_user_id: str
    legal_name: str
    school: str
    major: str
    admission_year: int
    graduation_year: int | None = None
    exam_type: MentorExamType
    score: int = Field(ge=0, le=150)
    skills: list[str] = Field(default_factory=list)
    bio: str = ""
    price: float | int = Field(ge=0)
    application_status: Literal["pending", "approved", "rejected"] = "pending"
    admin_note: str | None = None
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
    score: int = Field(ge=0, le=150)
    bio: str = Field(default="", max_length=500)
    story: str = Field(default="", max_length=2000)
    price_cents: int = Field(default=3900, ge=0, le=100000)
    consultation_window_minutes: int = Field(default=60, ge=15, le=180)
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
    consultation_type: MentorConsultationType
    slot_id: UUID | None = None
    questionnaire: MentorConsultationQuestionnaire


class MentorConsultationOrderItem(BaseModel):
    id: str
    order_no: str
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
    accepted_at: str | None = None
    expires_at: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class MentorConsultationOrderListResponse(BaseModel):
    items: list[MentorConsultationOrderItem] = Field(default_factory=list)
    count: int = 0


class MentorConsultationDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["accept", "reject"]


class MentorConsultationMessageCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_type: MentorMessageType = "text"
    content: str = Field(default="", max_length=5000)
    duration_seconds: int | None = Field(default=None, ge=0, le=3600)


class MentorConsultationMessageItem(BaseModel):
    id: str
    sender_role: MentorSenderRole
    message_type: MentorMessageType
    content: str = ""
    duration_seconds: int | None = None
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
