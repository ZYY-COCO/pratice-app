import hashlib
import json
import logging
from typing import Any


logger = logging.getLogger(__name__)


def create_user_notification(
    supabase: Any,
    *,
    recipient_user_id: str,
    category: str,
    notification_type: str,
    title: str,
    summary: str = "",
    content: str = "",
    related_type: str | None = None,
    related_id: str | None = None,
    route_path: str | None = None,
    delivery_payload: dict[str, Any] | None = None,
) -> None:
    """Persist one recipient-scoped notification without impacting the source workflow."""

    recipient_id = str(recipient_user_id or "").strip()
    normalized_type = str(notification_type or "").strip()
    normalized_title = str(title or "").strip()
    if not recipient_id or not normalized_type or not normalized_title:
        return

    normalized_summary = str(summary or "").strip()
    normalized_content = str(content or "").strip()
    normalized_related_id = str(related_id or "").strip() or None
    normalized_route_path = str(route_path or "").strip() or None
    normalized_delivery_payload = _build_delivery_payload(
        notification_type=normalized_type,
        title=normalized_title,
        summary=normalized_summary,
        content=normalized_content,
        related_type=related_type,
        related_id=normalized_related_id,
        route_path=normalized_route_path,
        extra=delivery_payload,
    )
    event_key = _build_event_key(
        notification_type=normalized_type,
        related_id=normalized_related_id,
        title=normalized_title,
        summary=normalized_summary,
        content=normalized_content,
        route_path=normalized_route_path,
        delivery_payload=normalized_delivery_payload,
    )

    try:
        existing = (
            supabase.table("user_notifications")
            .select("id")
            .eq("recipient_user_id", recipient_id)
            .eq("event_key", event_key)
            .limit(1)
            .execute()
        )
        if existing.data:
            return
        supabase.table("user_notifications").insert({
            "recipient_user_id": recipient_id,
            "category": str(category or "official").strip() or "official",
            "notification_type": normalized_type,
            "title": normalized_title,
            "summary": normalized_summary,
            "content": normalized_content,
            "related_type": str(related_type or "").strip() or None,
            "related_id": normalized_related_id,
            "route_path": normalized_route_path,
            "delivery_payload": normalized_delivery_payload,
            "event_key": event_key,
        }).execute()
    except Exception as exc:
        # 通知失败不能回滚已完成的后台处置；用户仍可从原处理记录查看结论。
        logger.warning(
            "User notification write skipped (type=%s recipient=%s error_type=%s)",
            normalized_type,
            recipient_id,
            type(exc).__name__,
        )


def _build_event_key(
    *,
    notification_type: str,
    related_id: str | None,
    title: str,
    summary: str,
    content: str,
    route_path: str | None,
    delivery_payload: dict[str, Any],
) -> str:
    payload = json.dumps(
        {
            "type": notification_type,
            "related_id": related_id or "",
            "title": title,
            "summary": summary,
            "content": content,
            "route_path": route_path or "",
            "delivery_payload": delivery_payload,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
    source = (related_id or "general").replace("-", "")[:36]
    return f"{notification_type}:{source}:{digest}"[:255]


def _build_delivery_payload(
    *,
    notification_type: str,
    title: str,
    summary: str,
    content: str,
    related_type: str | None,
    related_id: str | None,
    route_path: str | None,
    extra: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build the stable in-app/native-push payload shared by every delivery channel."""

    payload: dict[str, Any] = {
        "schema_version": 1,
        "event": notification_type,
        "title": title,
        "body": content or summary,
        "route_path": route_path or "",
        "related_type": str(related_type or "").strip(),
        "related_id": related_id or "",
    }
    if isinstance(extra, dict):
        payload.update({key: value for key, value in extra.items() if isinstance(key, str) and key})
    return payload
