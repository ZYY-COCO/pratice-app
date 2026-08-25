from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


COMMUNITY_CHAT_CATEGORIES = {"备考日常", "中华文化", "数学基础", "英语运用", "逻辑推理"}
COMMUNITY_EXPERIENCE_CATEGORIES = {"Z001", "Z002", "专业课", "复试"}


class CommunityMediaItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    kicker: str = Field(default="", max_length=32)
    title: str = Field(default="", max_length=64)
    copy_text: str = Field(default="", alias="copy", serialization_alias="copy", max_length=96)
    tone: str = Field(default="sky", pattern="^(sky|mint|warm|paper)$")
    image_url: str | None = Field(default=None, alias="imageUrl", serialization_alias="imageUrl", max_length=2048)


class CommunityPostStats(BaseModel):
    likes: int = 0
    comments: int = 0
    views: int = 0


class CommunityCommentPreview(BaseModel):
    author: str
    text: str


class CommunityPostItem(BaseModel):
    id: str
    post_type: Literal["chat", "experience"] = "chat"
    category: str
    author: str
    avatar: str
    avatar_url: str | None = None
    publish_time: str
    tone: str
    title: str
    summary: str
    content: str
    media: list[CommunityMediaItem] = Field(default_factory=list)
    comment_preview: CommunityCommentPreview | None = None
    comment_previews: list[CommunityCommentPreview] = Field(default_factory=list)
    stats: CommunityPostStats = Field(default_factory=CommunityPostStats)
    is_featured: bool = False
    liked: bool = False
    author_verified: bool = False


class CommunityPostListResponse(BaseModel):
    items: list[CommunityPostItem]
    count: int = 0
    next_cursor: str | None = None
    has_more: bool = False


class CommunityDeletePostsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    post_ids: list[UUID] = Field(min_length=1, max_length=100)


class CommunityDeletePostsResponse(BaseModel):
    deleted_post_ids: list[str] = Field(default_factory=list)
    deleted_count: int = 0


class CommunityDeleteCommentResponse(BaseModel):
    comment_id: str
    comment_count: int = 0


class CommunityLikedPostItem(CommunityPostItem):
    liked_at: str | None = None


class CommunityLikedPostListResponse(BaseModel):
    items: list[CommunityLikedPostItem] = Field(default_factory=list)
    count: int = 0
    next_cursor: str | None = None
    has_more: bool = False


class CommunityCommentItem(BaseModel):
    id: str
    author: str
    avatar: str
    avatar_url: str | None = None
    content: str
    created_at: str | None = None
    is_mine: bool = False
    like_count: int = 0
    liked: bool = False


class CommunityPostDetailResponse(BaseModel):
    post: CommunityPostItem
    comments: list[CommunityCommentItem] = Field(default_factory=list)


class CommunityLikeItem(BaseModel):
    id: str
    author: str
    avatar: str
    avatar_url: str | None = None
    liked_at: str | None = None


class CommunityLikeListResponse(BaseModel):
    items: list[CommunityLikeItem] = Field(default_factory=list)
    count: int = 0


class CommunityCreatePostRequest(BaseModel):
    post_type: Literal["chat", "experience"] = "chat"
    category: str = Field(min_length=1, max_length=24)
    title: str = Field(min_length=1, max_length=80)
    content: str = Field(min_length=1, max_length=3000)
    media: list[CommunityMediaItem] = Field(default_factory=list, max_length=9)

    @model_validator(mode="after")
    def validate_category_for_post_type(self) -> "CommunityCreatePostRequest":
        self.category = self.category.strip()
        allowed_categories = (
            COMMUNITY_EXPERIENCE_CATEGORIES
            if self.post_type == "experience"
            else COMMUNITY_CHAT_CATEGORIES
        )
        if self.category not in allowed_categories:
            message = (
                "经验贴分类仅支持 Z001、Z002、专业课、复试"
                if self.post_type == "experience"
                else "研友聊分类仅支持备考日常、中华文化、数学基础、英语运用、逻辑推理"
            )
            raise ValueError(message)
        return self


class CommunityImageUploadResponse(BaseModel):
    url: str


class CommunityLikeResponse(BaseModel):
    post_id: str
    is_liked: bool
    like_count: int


class CommunityCommentLikeResponse(BaseModel):
    comment_id: str
    is_liked: bool
    like_count: int


class CommunityCreateCommentRequest(BaseModel):
    content: str = Field(min_length=1, max_length=500)


class CommunityCreateCommentResponse(BaseModel):
    comment: CommunityCommentItem
    comment_count: int


CommunityReportTargetType = Literal["post", "comment"]
CommunityReportStatus = Literal["pending", "reviewing", "resolved", "dismissed"]
CommunityModerationAction = Literal[
    "none",
    "hide_post",
    "restore_post",
    "hide_comment",
    "restore_comment",
]


class CommunityCreateReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=60)
    content: str = Field(min_length=10, max_length=500)


class CommunityReportItem(BaseModel):
    id: str
    target_type: CommunityReportTargetType
    post_id: str
    comment_id: str | None = None
    reason: str
    content: str = ""
    status: CommunityReportStatus = "pending"
    moderation_action: CommunityModerationAction = "none"
    admin_note: str | None = None
    target_title: str = ""
    target_excerpt: str = ""
    created_at: str | None = None
    handled_at: str | None = None


class CommunityReportListResponse(BaseModel):
    items: list[CommunityReportItem] = Field(default_factory=list)
    count: int = 0


CommunityAppealStatus = Literal["pending", "reviewing", "resolved", "dismissed"]
CommunityAppealModerationAction = Literal["none", "restore_post", "restore_comment", "uphold"]


class CommunityModerationAppealCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=10, max_length=500)


class CommunityModerationAppealItem(BaseModel):
    id: str
    target_type: CommunityReportTargetType
    post_id: str
    comment_id: str | None = None
    content: str
    status: CommunityAppealStatus = "pending"
    moderation_action: CommunityAppealModerationAction = "none"
    admin_note: str | None = None
    created_at: str | None = None
    handled_at: str | None = None


class CommunityModerationStatusItem(BaseModel):
    target_type: CommunityReportTargetType
    target_id: str
    post_id: str
    comment_id: str | None = None
    title: str = ""
    excerpt: str = ""
    is_published: bool = False
    moderation_note: str | None = None
    moderated_at: str | None = None
    appeal: CommunityModerationAppealItem | None = None


class CommunityModerationStatusListResponse(BaseModel):
    items: list[CommunityModerationStatusItem] = Field(default_factory=list)
    count: int = 0


class CommunityViewRequest(BaseModel):
    anonymous_id: str | None = Field(default=None, max_length=36)


class CommunityViewResponse(BaseModel):
    post_id: str
    counted: bool
    view_count: int
