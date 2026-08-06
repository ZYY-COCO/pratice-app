from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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
    liked: bool = False


class CommunityPostListResponse(BaseModel):
    items: list[CommunityPostItem]
    count: int = 0


class CommunityCommentItem(BaseModel):
    id: str
    author: str
    avatar: str
    avatar_url: str | None = None
    content: str
    created_at: str | None = None
    is_mine: bool = False


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
    content: str = Field(min_length=1, max_length=2000)
    media: list[CommunityMediaItem] = Field(default_factory=list, max_length=9)


class CommunityImageUploadResponse(BaseModel):
    url: str


class CommunityLikeResponse(BaseModel):
    post_id: str
    is_liked: bool
    like_count: int


class CommunityCreateCommentRequest(BaseModel):
    content: str = Field(min_length=1, max_length=500)


class CommunityCreateCommentResponse(BaseModel):
    comment: CommunityCommentItem
    comment_count: int


class CommunityViewRequest(BaseModel):
    anonymous_id: str | None = Field(default=None, max_length=36)


class CommunityViewResponse(BaseModel):
    post_id: str
    counted: bool
    view_count: int
