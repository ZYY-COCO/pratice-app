import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.db import get_supabase_admin
from app.services.supabase_resilience import (
    call_supabase,
    is_missing_supabase_relation_error,
)


logger = logging.getLogger(__name__)

LEGACY_NOTIFICATION_ROUTE_MAP = {
    "/pages/circle/mentor-detail": "/pages-sub-consultation/consultation/mentor-detail",
    "/pages/circle/mentor-booking": "/pages-sub-consultation/consultation/mentor-booking",
    "/pages/circle/mentor-schedule": "/pages-sub-consultation/consultation/mentor-schedule",
    "/pages/circle/mentor-info": "/pages-sub-consultation/consultation/mentor-info",
    "/pages/circle/mentor-consult-form": "/pages-sub-consultation/consultation/mentor-consult-form",
    "/pages/circle/mentor-waiting": "/pages-sub-consultation/consultation/mentor-waiting",
    "/pages/circle/mentor-chat": "/pages-sub-consultation/consultation/mentor-chat",
    "/pages/circle/my-consultations": "/pages-sub-consultation/consultation/my-consultations",
    "/pages/circle/mentor-report": "/pages-sub-consultation/consultation/mentor-report",
    "/pages/circle/mentor-support": "/pages-sub-consultation/consultation/mentor-support",
    "/pages/circle/mentor-response": "/pages-sub-consultation/consultation/mentor-response",
    "/pages/circle/mentor-appeal": "/pages-sub-consultation/consultation/mentor-appeal",
    "/pages/circle/mentor-apply": "/pages-sub-consultation/consultation/mentor-apply",
}


def normalize_notification_route_path(route_path: str | None) -> str | None:
    """Resolve routes persisted before consultation pages moved into a subpackage."""

    normalized = str(route_path or "").strip()
    if not normalized:
        return None
    suffix_indexes = [index for marker in ("?", "#") if (index := normalized.find(marker)) >= 0]
    suffix_index = min(suffix_indexes) if suffix_indexes else -1
    pathname = normalized[:suffix_index] if suffix_index >= 0 else normalized
    suffix = normalized[suffix_index:] if suffix_index >= 0 else ""
    return f"{LEGACY_NOTIFICATION_ROUTE_MAP.get(pathname, pathname)}{suffix}"


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
    normalized_route_path = normalize_notification_route_path(route_path)
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

    record = {
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
    }

    try:
        existing = call_supabase(
            lambda: (
                supabase.table("user_notification_outbox")
                .select("id")
                .eq("recipient_user_id", recipient_id)
                .eq("event_key", event_key)
                .limit(1)
                .execute()
            ),
            operation_name="user notification outbox duplicate lookup",
        )
        if existing.data:
            return
        call_supabase(
            lambda: supabase.table("user_notification_outbox").insert(record).execute(),
            operation_name="user notification outbox enqueue",
        )
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            # 滚动部署期间兼容尚未执行 outbox 迁移的环境。
            try:
                _persist_notification(supabase, record)
            except Exception as legacy_exc:
                logger.warning(
                    "User notification legacy write skipped (type=%s recipient=%s error_type=%s)",
                    normalized_type,
                    recipient_id,
                    type(legacy_exc).__name__,
                )
            return
        # 唯一键竞争意味着另一请求已经成功入队，回读确认后按成功处理。
        try:
            duplicate = call_supabase(
                lambda: (
                    supabase.table("user_notification_outbox")
                    .select("id")
                    .eq("recipient_user_id", recipient_id)
                    .eq("event_key", event_key)
                    .limit(1)
                    .execute()
                ),
                operation_name="user notification outbox conflict recovery",
            )
            if duplicate.data:
                return
        except Exception:
            pass
        logger.warning(
            "User notification enqueue deferred (type=%s recipient=%s error_type=%s)",
            normalized_type,
            recipient_id,
            type(exc).__name__,
        )


def _persist_notification(supabase: Any, record: dict[str, Any]) -> str | None:
    """Insert the user-visible notification idempotently and return its id."""

    recipient_id = str(record.get("recipient_user_id") or "")
    event_key = str(record.get("event_key") or "")
    existing = call_supabase(
        lambda: (
            supabase.table("user_notifications")
            .select("id")
            .eq("recipient_user_id", recipient_id)
            .eq("event_key", event_key)
            .limit(1)
            .execute()
        ),
        operation_name="user notification delivery duplicate lookup",
    )
    if existing.data:
        return str(existing.data[0].get("id") or "") or None

    try:
        response = call_supabase(
            lambda: supabase.table("user_notifications").insert({
            "recipient_user_id": recipient_id,
            "category": record.get("category") or "official",
            "notification_type": record.get("notification_type") or "official",
            "title": record.get("title") or "通知",
            "summary": record.get("summary") or "",
            "content": record.get("content") or "",
            "related_type": record.get("related_type"),
            "related_id": record.get("related_id"),
            "route_path": record.get("route_path"),
            "delivery_payload": record.get("delivery_payload") or {},
            "event_key": event_key,
            }).execute(),
            operation_name="user notification delivery",
        )
        return str((response.data or [{}])[0].get("id") or "") or None
    except Exception as exc:
        duplicate = call_supabase(
            lambda: (
                supabase.table("user_notifications")
                .select("id")
                .eq("recipient_user_id", recipient_id)
                .eq("event_key", event_key)
                .limit(1)
                .execute()
            ),
            operation_name="user notification delivery conflict recovery",
        )
        if duplicate.data:
            return str(duplicate.data[0].get("id") or "") or None
        raise exc


def deliver_pending_user_notifications(
    *,
    supabase: Any | None = None,
    limit: int = 50,
) -> int:
    """Claim and reliably deliver pending outbox rows.

    Claiming is atomic and uses SKIP LOCKED in SQL. If a worker stops between the
    visible insert and acknowledgement, the row is reclaimed after five minutes;
    the recipient/event unique key prevents duplicate notifications.
    """

    client = supabase or get_supabase_admin()
    now = datetime.now(timezone.utc)
    try:
        claimed = call_supabase(
            lambda: client.rpc(
                "claim_user_notification_outbox",
                {"p_limit": max(1, min(int(limit or 50), 200)), "p_now": now.isoformat()},
            ).execute(),
            operation_name="user notification outbox claim",
        )
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            return 0
        raise

    delivered = 0
    for row in claimed.data or []:
        outbox_id = str(row.get("id") or "")
        attempts = max(1, int(row.get("attempts") or 1))
        try:
            notification_id = _persist_notification(client, row)
            call_supabase(
                lambda: (
                    client.table("user_notification_outbox")
                    .update({
                        "status": "delivered",
                        "delivered_at": datetime.now(timezone.utc).isoformat(),
                        "delivered_notification_id": notification_id,
                        "locked_at": None,
                        "last_error": None,
                    })
                    .eq("id", outbox_id)
                    .eq("status", "processing")
                    .execute()
                ),
                operation_name="user notification outbox acknowledge",
            )
            delivered += 1
        except Exception as exc:
            retry_at = now + timedelta(seconds=min(3600, 5 * (2 ** min(attempts, 9))))
            next_status = "failed" if attempts >= 12 else "pending"
            try:
                call_supabase(
                    lambda: (
                        client.table("user_notification_outbox")
                        .update({
                            "status": next_status,
                            "available_at": retry_at.isoformat(),
                            "locked_at": None,
                            "last_error": type(exc).__name__[:120],
                        })
                        .eq("id", outbox_id)
                        .eq("status", "processing")
                        .execute()
                    ),
                    operation_name="user notification outbox retry schedule",
                )
            except Exception as schedule_exc:
                logger.warning(
                    "User notification retry scheduling failed (outbox_id=%s error_type=%s)",
                    outbox_id,
                    type(schedule_exc).__name__,
                )
    return delivered


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
