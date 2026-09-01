from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.routes.official_messages import _fetch_read_message_ids, _fetch_visible_messages
from app.schemas.notifications import (
    UserNotificationItem,
    UserNotificationListResponse,
    UserNotificationReadAllResponse,
    UserNotificationReadResponse,
    UserNotificationReadScopeRequest,
    UserNotificationReadTargetRequest,
    UserNotificationUnreadSummary,
)
from app.services.user_notifications import normalize_notification_route_path


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
CONSULTATION_ORDER_NOTIFICATION_TYPES = (
    "mentor_order_created",
    "mentor_chat_message",
    "mentor_order_status",
)


def _to_item(row: dict) -> UserNotificationItem:
    route_path = normalize_notification_route_path(row.get("route_path"))
    delivery_payload = row.get("delivery_payload") if isinstance(row.get("delivery_payload"), dict) else {}
    if delivery_payload:
        delivery_payload = dict(delivery_payload)
        delivery_payload["route_path"] = normalize_notification_route_path(delivery_payload.get("route_path")) or ""
    return UserNotificationItem(
        id=str(row.get("id") or ""),
        category=str(row.get("category") or "official"),
        notification_type=str(row.get("notification_type") or "official"),
        title=str(row.get("title") or ""),
        summary=str(row.get("summary") or ""),
        content=str(row.get("content") or ""),
        related_type=str(row.get("related_type") or "") or None,
        related_id=str(row.get("related_id") or "") or None,
        route_path=route_path,
        delivery_payload=delivery_payload,
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


def _notification_payload(row: dict) -> dict:
    payload = row.get("delivery_payload")
    return payload if isinstance(payload, dict) else {}


def _community_notification_tab(row: dict) -> str:
    payload = _notification_payload(row)
    explicit = str(payload.get("post_type") or "").strip()
    if explicit in {"chat", "experience"}:
        return explicit
    route_path = str(payload.get("route_path") or row.get("route_path") or "").strip()
    try:
        route_tab = str(parse_qs(urlsplit(route_path).query).get("communityTab", [""])[0]).strip()
    except (TypeError, ValueError):
        route_tab = ""
    return "experience" if route_tab == "experience" else "chat"


def _notification_route_query_value(row: dict, key: str) -> str:
    payload = _notification_payload(row)
    route_path = str(payload.get("route_path") or row.get("route_path") or "").strip()
    try:
        return str(parse_qs(urlsplit(route_path).query).get(key, [""])[0]).strip()
    except (TypeError, ValueError):
        return ""


def _consultation_notification_audience(row: dict) -> str:
    payload = _notification_payload(row)
    explicit = str(payload.get("audience") or "").strip()
    if explicit in {"mentor", "applicant"}:
        return explicit
    notification_type = str(row.get("notification_type") or "").strip()
    if notification_type == "mentor_order_created":
        return "mentor"
    if notification_type == "mentor_chat_message":
        return "mentor" if str(payload.get("sender_role") or "").strip() == "applicant" else "applicant"
    return "applicant"


def _notification_target_id(row: dict, target_type: str) -> str:
    payload = _notification_payload(row)
    if target_type == "community_post":
        post_id = str(payload.get("post_id") or "").strip() or _notification_route_query_value(row, "postId")
        if post_id:
            return post_id
        # 兼容早期写入的互动通知：当时部分记录只有 related_id，
        # 可能是“帖子 ID:互动类型:用户 ID”或直接使用帖子 ID。
        if str(row.get("related_type") or "").strip() == "community_post":
            return str(row.get("related_id") or "").split(":", 1)[0].strip()
        return ""
    order_id = str(payload.get("order_id") or "").strip() or _notification_route_query_value(row, "orderId")
    if order_id:
        return order_id
    if str(row.get("related_type") or "").strip() == "mentor_consultation_order":
        return str(row.get("related_id") or "").split(":", 1)[0].strip()
    return ""


def _increment_target(targets: dict[str, int], target_id: str) -> None:
    if target_id:
        targets[target_id] = targets.get(target_id, 0) + 1


def _summarize_unread_rows(rows: list[dict]) -> UserNotificationUnreadSummary:
    community_post_targets: dict[str, dict[str, int]] = {"chat": {}, "experience": {}}
    consultation_order_targets: dict[str, dict[str, int]] = {"applicant": {}, "mentor": {}}
    community = 0
    post_interactions = 0
    community_reports = 0
    consultations = 0
    community_chat = 0
    community_experience = 0
    applicant_consultations = 0
    mentor_consultations = 0

    for row in rows:
        category = str(row.get("category") or "").strip()
        notification_type = str(row.get("notification_type") or "").strip()
        if category == "community":
            community += 1
        if category == "consultation":
            consultations += 1
        if notification_type in COMMUNITY_REPORT_NOTIFICATION_TYPES:
            community_reports += 1
        if notification_type in POST_INTERACTION_NOTIFICATION_TYPES:
            post_interactions += 1
            tab = _community_notification_tab(row)
            if tab == "experience":
                community_experience += 1
            else:
                community_chat += 1
            _increment_target(
                community_post_targets[tab],
                _notification_target_id(row, "community_post"),
            )
        if notification_type in CONSULTATION_ORDER_NOTIFICATION_TYPES:
            audience = _consultation_notification_audience(row)
            if audience == "mentor":
                mentor_consultations += 1
            else:
                applicant_consultations += 1
            _increment_target(
                consultation_order_targets[audience],
                _notification_target_id(row, "consultation_order"),
            )

    consultation_orders = applicant_consultations + mentor_consultations
    return UserNotificationUnreadSummary(
        total=len(rows),
        community=community,
        post_interactions=post_interactions,
        community_reports=community_reports,
        consultations=consultations,
        circle=post_interactions + consultation_orders,
        community_chat=community_chat,
        community_experience=community_experience,
        consultation_orders=consultation_orders,
        applicant_consultations=applicant_consultations,
        mentor_consultations=mentor_consultations,
        community_post_targets=community_post_targets,
        consultation_order_targets=consultation_order_targets,
    )


def _notification_matches_target(row: dict, payload: UserNotificationReadTargetRequest) -> bool:
    notification_type = str(row.get("notification_type") or "").strip()
    if payload.target_type == "community_post":
        return (
            notification_type in POST_INTERACTION_NOTIFICATION_TYPES
            and _notification_target_id(row, payload.target_type) == payload.target_id
        )
    return (
        notification_type in CONSULTATION_ORDER_NOTIFICATION_TYPES
        and _notification_target_id(row, payload.target_type) == payload.target_id
    )


def _apply_read_scope(query, scope: str):
    if scope == "post_interactions":
        return query.in_("notification_type", list(POST_INTERACTION_NOTIFICATION_TYPES))
    if scope == "community_reports":
        return query.in_("notification_type", list(COMMUNITY_REPORT_NOTIFICATION_TYPES))
    if scope == "consultations":
        return query.eq("category", "consultation")
    return query.eq("category", "community")


def _mark_visible_official_messages_read(supabase, user_id: str, read_at: str) -> int:
    """Mark currently visible official messages as read for this user.

    Official messages keep read state in a separate per-user table, so only
    messages returned by the same visibility rules as the message centre are
    eligible here.  Existing read rows are left untouched and an empty batch
    avoids an unnecessary upsert request.
    """

    visible_rows = _fetch_visible_messages(supabase, limit=None)
    message_ids = []
    seen_ids: set[str] = set()
    for row in visible_rows:
        message_id = str(row.get("id") or "").strip()
        if message_id and message_id not in seen_ids:
            seen_ids.add(message_id)
            message_ids.append(message_id)
    if not message_ids:
        return 0

    read_ids = _fetch_read_message_ids(supabase, user_id, message_ids)
    unread_ids = [message_id for message_id in message_ids if message_id not in read_ids]
    if not unread_ids:
        return 0

    rows = [
        {"user_id": user_id, "message_id": message_id, "read_at": read_at}
        for message_id in unread_ids
    ]
    response = supabase.table("user_official_message_reads").upsert(
        rows,
        on_conflict="user_id,message_id",
    ).execute()
    # Supabase returns the upserted representation by default.  Falling back
    # to the request size keeps the count useful with deployments configured
    # to use a minimal mutation response.
    return len(response.data) if response.data else len(rows)


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
    response = (
        supabase.table("user_notifications")
        .select("id,category,notification_type,related_type,related_id,route_path,delivery_payload")
        .eq("recipient_user_id", user_id)
        .is_("read_at", "null")
        .execute()
    )
    return _summarize_unread_rows(response.data or [])


@router.post("/read-all", response_model=UserNotificationReadAllResponse)
def mark_all_user_notifications_read(
    user_id: str = Depends(get_current_user_id),
) -> UserNotificationReadAllResponse:
    """Mark all personal and currently visible official messages as read."""

    supabase = get_supabase_admin()
    read_at = datetime.now(timezone.utc).isoformat()
    personal_response = (
        supabase.table("user_notifications")
        .update({"read_at": read_at})
        .eq("recipient_user_id", user_id)
        .is_("read_at", "null")
        .execute()
    )
    personal_count = len(personal_response.data or [])
    official_count = _mark_visible_official_messages_read(supabase, user_id, read_at)
    return UserNotificationReadAllResponse(
        updated_count=personal_count + official_count,
        personal_updated_count=personal_count,
        official_updated_count=official_count,
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


@router.post("/read-target", response_model=UserNotificationReadResponse)
def mark_user_notification_target_read(
    payload: UserNotificationReadTargetRequest,
    user_id: str = Depends(get_current_user_id),
) -> UserNotificationReadResponse:
    """Mark unread messages only after the user opens their concrete post or order."""

    supabase = get_supabase_admin()
    unread_response = (
        supabase.table("user_notifications")
        .select("id,notification_type,related_type,related_id,route_path,delivery_payload")
        .eq("recipient_user_id", user_id)
        .is_("read_at", "null")
        .execute()
    )
    notification_ids = [
        str(row.get("id") or "")
        for row in (unread_response.data or [])
        if row.get("id") and _notification_matches_target(row, payload)
    ]
    if not notification_ids:
        return UserNotificationReadResponse(updated_count=0)
    response = (
        supabase.table("user_notifications")
        .update({"read_at": datetime.now(timezone.utc).isoformat()})
        .eq("recipient_user_id", user_id)
        .is_("read_at", "null")
        .in_("id", notification_ids)
        .execute()
    )
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
