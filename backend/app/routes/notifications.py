from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.notifications import (
    UserNotificationItem,
    UserNotificationListResponse,
    UserNotificationReadResponse,
    UserNotificationReadScopeRequest,
    UserNotificationUnreadSummary,
)


router = APIRouter(prefix="/notifications", tags=["notifications"])

POST_INTERACTION_NOTIFICATION_TYPES = (
    "community_post_like",
    "community_post_comment",
)
COMMUNITY_REPORT_NOTIFICATION_TYPES = (
    "community_report_status",
    "community_appeal_status",
    "community_content_moderation",
)


def _to_item(row: dict) -> UserNotificationItem:
    return UserNotificationItem(
        id=str(row.get("id") or ""),
        category=str(row.get("category") or "official"),
        notification_type=str(row.get("notification_type") or "official"),
        title=str(row.get("title") or ""),
        summary=str(row.get("summary") or ""),
        content=str(row.get("content") or ""),
        related_type=str(row.get("related_type") or "") or None,
        related_id=str(row.get("related_id") or "") or None,
        route_path=str(row.get("route_path") or "") or None,
        delivery_payload=row.get("delivery_payload") if isinstance(row.get("delivery_payload"), dict) else {},
        created_at=row.get("created_at"),
        read=bool(row.get("read_at")),
    )


def _count_unread_notifications(
    supabase,
    user_id: str,
    *,
    category: str | None = None,
    notification_types: tuple[str, ...] = (),
) -> int:
    query = (
        supabase.table("user_notifications")
        .select("id", count="exact")
        .eq("recipient_user_id", user_id)
        .is_("read_at", "null")
    )
    if category:
        query = query.eq("category", category)
    if notification_types:
        query = query.in_("notification_type", list(notification_types))
    response = query.execute()
    return int(response.count or 0)


def _apply_read_scope(query, scope: str):
    if scope == "post_interactions":
        return query.in_("notification_type", list(POST_INTERACTION_NOTIFICATION_TYPES))
    if scope == "community_reports":
        return query.in_("notification_type", list(COMMUNITY_REPORT_NOTIFICATION_TYPES))
    if scope == "consultations":
        return query.eq("category", "consultation")
    return query.eq("category", "community")


@router.get("", response_model=UserNotificationListResponse)
def list_user_notifications(
    limit: int = Query(default=100, ge=1, le=200),
    category: str | None = Query(default=None, max_length=30),
    user_id: str = Depends(get_current_user_id),
) -> UserNotificationListResponse:
    supabase = get_supabase_admin()
    query = (
        supabase.table("user_notifications")
        .select("*")
        .eq("recipient_user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
    )
    if category:
        query = query.eq("category", category)
    response = query.execute()
    unread_response = (
        supabase.table("user_notifications")
        .select("id", count="exact")
        .eq("recipient_user_id", user_id)
        .is_("read_at", "null")
        .execute()
    )
    return UserNotificationListResponse(
        items=[_to_item(row) for row in (response.data or [])],
        unread_count=int(unread_response.count or 0),
    )


@router.get("/unread-summary", response_model=UserNotificationUnreadSummary)
def get_user_notification_unread_summary(
    user_id: str = Depends(get_current_user_id),
) -> UserNotificationUnreadSummary:
    """Return one authoritative unread count per UI entry point."""

    supabase = get_supabase_admin()
    return UserNotificationUnreadSummary(
        total=_count_unread_notifications(supabase, user_id),
        community=_count_unread_notifications(supabase, user_id, category="community"),
        post_interactions=_count_unread_notifications(
            supabase,
            user_id,
            notification_types=POST_INTERACTION_NOTIFICATION_TYPES,
        ),
        community_reports=_count_unread_notifications(
            supabase,
            user_id,
            notification_types=COMMUNITY_REPORT_NOTIFICATION_TYPES,
        ),
        consultations=_count_unread_notifications(supabase, user_id, category="consultation"),
    )


@router.post("/read-scope", response_model=UserNotificationReadResponse)
def mark_user_notification_scope_read(
    payload: UserNotificationReadScopeRequest,
    user_id: str = Depends(get_current_user_id),
) -> UserNotificationReadResponse:
    """Mark only the messages represented by the page the user has opened as read."""

    supabase = get_supabase_admin()
    query = (
        supabase.table("user_notifications")
        .update({"read_at": datetime.now(timezone.utc).isoformat()})
        .eq("recipient_user_id", user_id)
        .is_("read_at", "null")
    )
    response = _apply_read_scope(query, payload.scope).execute()
    return UserNotificationReadResponse(updated_count=len(response.data or []))


@router.post("/{notification_id}/read", response_model=UserNotificationReadResponse)
def mark_user_notification_read(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
) -> UserNotificationReadResponse:
    supabase = get_supabase_admin()
    response = (
        supabase.table("user_notifications")
        .update({"read_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", notification_id)
        .eq("recipient_user_id", user_id)
        .is_("read_at", "null")
        .execute()
    )
    if not response.data:
        existing = (
            supabase.table("user_notifications")
            .select("id")
            .eq("id", notification_id)
            .eq("recipient_user_id", user_id)
            .limit(1)
            .execute()
        )
        if not existing.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息不存在")
    return UserNotificationReadResponse(updated_count=len(response.data or []))
