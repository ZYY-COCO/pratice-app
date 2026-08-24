from typing import Any, Literal

from pydantic import BaseModel, Field


class UserNotificationItem(BaseModel):
    id: str
    category: str
    notification_type: str
    title: str
    summary: str = ""
    content: str = ""
    related_type: str | None = None
    related_id: str | None = None
    route_path: str | None = None
    delivery_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None
    read: bool = False


class UserNotificationListResponse(BaseModel):
    items: list[UserNotificationItem] = Field(default_factory=list)
    unread_count: int = 0


class UserNotificationUnreadSummary(BaseModel):
    """Unread counts mapped to the entry points that surface a red dot."""

    total: int = 0
    community: int = 0
    post_interactions: int = 0
    community_reports: int = 0
    consultations: int = 0


class UserNotificationReadScopeRequest(BaseModel):
    scope: Literal["post_interactions", "community_reports", "consultations", "community"]


class UserNotificationReadResponse(BaseModel):
    ok: bool = True
    updated_count: int = 0
