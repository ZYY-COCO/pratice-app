"""Server-side lifecycle settlement for mentor consultation orders.

The client keeps polling its own order for a responsive experience, but money
and order-state outcomes must not depend on either participant reopening the
app.  This module is intentionally independent from route handlers so the
application lifecycle can settle expired orders in the background as well.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.db import get_supabase_admin
from app.services.mentor_consultation_sla import normalize_case_priority
from app.services.supabase_resilience import call_supabase, is_missing_supabase_relation_error
from app.services.user_notifications import create_user_notification
from app.services.wallet_ledger import record_consultation_income_pending


logger = logging.getLogger(__name__)
DEFAULT_SWEEP_LIMIT = 200
DEFAULT_INSTANT_START_GRACE_MINUTES = 10


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def _get_order_or_existing(supabase: Any, order_id: str, existing: dict) -> dict:
    response = call_supabase(
        lambda: (
            supabase.table("mentor_consultation_orders")
            .select("*")
            .eq("id", order_id)
            .limit(1)
            .execute()
        ),
        operation_name="consultation lifecycle order refresh",
    )
    return response.data[0] if response.data else existing


def _insert_system_message(supabase: Any, order_id: str, content: str) -> None:
    try:
        call_supabase(
            lambda: supabase.table("mentor_consultation_messages").insert({
                "order_id": order_id,
                "sender_role": "system",
                "message_type": "system",
                "content": content,
            }).execute(),
            operation_name="consultation lifecycle system message",
        )
    except Exception as exc:
        logger.warning("Consultation lifecycle system message skipped (error_type=%s)", type(exc).__name__)


def _insert_event(supabase: Any, order_id: str, event_type: str, details: dict | None = None) -> None:
    try:
        call_supabase(
            lambda: supabase.table("mentor_consultation_order_events").insert({
                "order_id": order_id,
                "actor_role": "system",
                "event_type": event_type,
                "details": details or {},
            }).execute(),
            operation_name="consultation lifecycle event",
        )
    except Exception as exc:
        logger.warning(
            "Consultation lifecycle event skipped (event=%s error_type=%s)",
            event_type,
            type(exc).__name__,
        )


def _notify_applicant_of_lifecycle_timeout(
    supabase: Any,
    *,
    order: dict,
    timeout_reason: str,
    title: str,
    summary: str,
    content: str,
) -> None:
    """Write one applicant-scoped status notification after a won transition."""

    order_id = str(order.get("id") or "").strip()
    recipient_user_id = str(order.get("applicant_user_id") or "").strip()
    if not order_id or not recipient_user_id:
        return

    route_path = "/pages-sub-consultation/consultation/my-consultations"
    try:
        create_user_notification(
            supabase,
            recipient_user_id=recipient_user_id,
            category="consultation",
            notification_type="mentor_order_status",
            title=title,
            summary=summary,
            content=content,
            related_type="mentor_consultation_order",
            related_id=f"{order_id}:timeout",
            route_path=route_path,
            delivery_payload={
                "surface": "mentor_order",
                "audience": "applicant",
                "event": "timeout",
                "order_id": order_id,
                "mentor_id": str(order.get("mentor_id") or ""),
                "order_status": str(order.get("order_status") or "timeout"),
                "timeout_reason": timeout_reason,
                "consultation_type": str(order.get("consultation_type") or ""),
                "payment_status": str(order.get("payment_status") or ""),
                "refund_amount_cents": max(0, int(order.get("refund_amount_cents") or 0)),
            },
        )
    except Exception as exc:
        logger.warning(
            "Consultation lifecycle notification skipped (order_id=%s reason=%s error_type=%s)",
            order_id,
            timeout_reason,
            type(exc).__name__,
        )


def _has_open_consultation_dispute(supabase: Any, order_id: str) -> bool:
    """Resolve the UX-only block reason after the atomic RPC declines."""

    try:
        report_response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_reports")
                .select("id,status")
                .eq("order_id", order_id)
                .execute()
            ),
            operation_name="consultation auto completion dispute lookup",
        )
        reports = report_response.data or []
        if any(str(report.get("status") or "") in {"pending", "reviewing"} for report in reports):
            return True
        report_ids = [str(report.get("id") or "") for report in reports if report.get("id")]
        if not report_ids:
            return False
        appeal_response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_report_appeals")
                .select("id")
                .in_("report_id", report_ids)
                .in_("status", ["pending", "reviewing"])
                .limit(1)
                .execute()
            ),
            operation_name="consultation auto completion appeal lookup",
        )
        return bool(appeal_response.data)
    except Exception as exc:
        logger.warning(
            "Consultation auto completion dispute reason unavailable (order_id=%s error_type=%s)",
            order_id,
            type(exc).__name__,
        )
        return False


def _is_demo_payment_reference(reference: object) -> bool:
    return str(reference or "").upper().startswith(("DEMO-", "MOCK-"))


def _refund_payment_status(order: dict) -> str:
    return "refunded" if _is_demo_payment_reference(order.get("payment_reference")) else "refunding"


def _escalate_unanswered_consultation_case(
    supabase: Any,
    *,
    table_name: str,
    case_id: str,
    current_priority: object,
    current_escalation_level: object,
    now: datetime,
    operation_name: str,
) -> dict | None:
    """Atomically mark a first-response SLA breach as an urgent case once."""

    level = max(0, int(current_escalation_level or 0))
    if not case_id or level > 0:
        return None
    response = call_supabase(
        lambda: (
            supabase.table(table_name)
            .update({
                "priority": "urgent",
                "escalation_level": level + 1,
                "escalated_at": now.isoformat(),
            })
            .eq("id", case_id)
            .eq("status", "pending")
            .is_("first_response_at", "null")
            .eq("escalation_level", level)
            .execute()
        ),
        operation_name=operation_name,
    )
    return response.data[0] if response.data else None


def sweep_mentor_consultation_report_slas(
    *,
    supabase: Any | None = None,
    now: datetime | None = None,
    limit: int = DEFAULT_SWEEP_LIMIT,
) -> int:
    """Escalate consultation cases that missed their first-response promise.

    A conditional update makes the job idempotent across app workers. The queue
    only receives one automatic escalation per case; after that an operator owns
    the resolution and the order event remains the audit trail.
    """

    current_time = now or _utc_now()
    batch_size = max(1, min(int(limit or DEFAULT_SWEEP_LIMIT), DEFAULT_SWEEP_LIMIT))
    client = supabase or get_supabase_admin()
    changed = 0
    try:
        report_response = call_supabase(
            lambda: (
                client.table("mentor_consultation_reports")
                .select("id,order_id,status,priority,escalation_level,first_response_due_at,first_response_at")
                .eq("status", "pending")
                .is_("first_response_at", "null")
                .eq("escalation_level", 0)
                .lt("first_response_due_at", current_time.isoformat())
                .order("first_response_due_at")
                .limit(batch_size)
                .execute()
            ),
            operation_name="consultation report first response SLA sweep",
        )
        for report in report_response.data or []:
            report_id = str(report.get("id") or "")
            try:
                updated = _escalate_unanswered_consultation_case(
                    client,
                    table_name="mentor_consultation_reports",
                    case_id=report_id,
                    current_priority=report.get("priority"),
                    current_escalation_level=report.get("escalation_level"),
                    now=current_time,
                    operation_name="consultation report first response SLA escalation",
                )
            except Exception as exc:
                logger.warning("Consultation report SLA escalation skipped (error_type=%s)", type(exc).__name__)
                continue
            if not updated:
                continue
            changed += 1
            order_id = str(updated.get("order_id") or report.get("order_id") or "")
            if order_id:
                _insert_system_message(
                    client,
                    order_id,
                    "本次咨询问题反馈已超过平台首次响应时限，系统已升级为优先处理；平台会尽快完成首次核实。",
                )
                _insert_event(
                    client,
                    order_id,
                    "consultation_report_sla_escalated",
                    {
                        "report_id": report_id,
                        "first_response_due_at": updated.get("first_response_due_at") or report.get("first_response_due_at"),
                        "previous_priority": normalize_case_priority(report.get("priority")),
                        "priority": "urgent",
                        "escalation_level": int(updated.get("escalation_level") or 1),
                    },
                )

        appeal_response = call_supabase(
            lambda: (
                client.table("mentor_consultation_report_appeals")
                .select("id,report_id,status,priority,escalation_level,first_response_due_at,first_response_at")
                .eq("status", "pending")
                .is_("first_response_at", "null")
                .eq("escalation_level", 0)
                .lt("first_response_due_at", current_time.isoformat())
                .order("first_response_due_at")
                .limit(batch_size)
                .execute()
            ),
            operation_name="consultation report appeal first response SLA sweep",
        )
        appeals = appeal_response.data or []
        report_ids = [str(row.get("report_id") or "") for row in appeals if row.get("report_id")]
        order_ids_by_report: dict[str, str] = {}
        if report_ids:
            source_report_response = call_supabase(
                lambda: (
                    client.table("mentor_consultation_reports")
                    .select("id,order_id")
                    .in_("id", report_ids)
                    .execute()
                ),
                operation_name="consultation report appeal SLA order lookup",
            )
            order_ids_by_report = {
                str(row.get("id") or ""): str(row.get("order_id") or "")
                for row in (source_report_response.data or [])
                if row.get("id") and row.get("order_id")
            }
        for appeal in appeals:
            appeal_id = str(appeal.get("id") or "")
            try:
                updated = _escalate_unanswered_consultation_case(
                    client,
                    table_name="mentor_consultation_report_appeals",
                    case_id=appeal_id,
                    current_priority=appeal.get("priority"),
                    current_escalation_level=appeal.get("escalation_level"),
                    now=current_time,
                    operation_name="consultation report appeal first response SLA escalation",
                )
            except Exception as exc:
                logger.warning("Consultation report appeal SLA escalation skipped (error_type=%s)", type(exc).__name__)
                continue
            if not updated:
                continue
            changed += 1
            report_id = str(updated.get("report_id") or appeal.get("report_id") or "")
            order_id = order_ids_by_report.get(report_id, "")
            if order_id:
                _insert_system_message(
                    client,
                    order_id,
                    "本次咨询复核申请已超过平台首次响应时限，系统已升级为优先处理；平台会尽快完成首次核实。",
                )
                _insert_event(
                    client,
                    order_id,
                    "consultation_report_appeal_sla_escalated",
                    {
                        "report_id": report_id,
                        "appeal_id": appeal_id,
                        "first_response_due_at": updated.get("first_response_due_at") or appeal.get("first_response_due_at"),
                        "previous_priority": normalize_case_priority(appeal.get("priority")),
                        "priority": "urgent",
                        "escalation_level": int(updated.get("escalation_level") or 1),
                    },
                )
    except Exception as exc:
        # The SLA migration may be rolling out separately from application code.
        # A missing table/column must not block paid-order timeout settlement.
        logger.warning("Consultation report SLA sweep deferred (error_type=%s)", type(exc).__name__)
    return changed


def release_terminal_mentor_booking_slot(
    supabase: Any,
    order: dict,
    *,
    now: datetime | None = None,
) -> bool:
    """Release a reserved booking slot after its order leaves the service flow.

    Order cancellation/refund and slot release are separate database writes.  The
    route performs this immediately, while the periodic lifecycle sweep retries
    it if a transient storage/database failure happened between the two writes.
    """

    if str(order.get("consultation_type") or "") != "booking":
        return False
    slot_id = str(order.get("slot_id") or "")
    if not slot_id:
        return False

    current_time = now or _utc_now()
    try:
        slot_response = call_supabase(
            lambda: (
                supabase.table("mentor_availability_slots")
                .select("id,ends_at,status,held_order_id")
                .eq("id", slot_id)
                .limit(1)
                .execute()
            ),
            operation_name="consultation terminal booking slot lookup",
        )
        slot = (slot_response.data or [None])[0]
        slot_status = str((slot or {}).get("status") or "")
        if not slot or slot_status not in {"held", "booked"}:
            return False
        if slot_status == "held" and str(slot.get("held_order_id") or "") != str(order.get("id") or ""):
            return False

        ends_at = _as_utc_datetime(slot.get("ends_at"))
        next_status = "expired" if ends_at is not None and ends_at <= current_time else "available"
        query = (
            supabase.table("mentor_availability_slots")
            .update({"status": next_status, "held_order_id": None, "hold_expires_at": None})
            .eq("id", slot_id)
            .eq("status", slot_status)
        )
        if slot_status == "held":
            query = query.eq("held_order_id", str(order.get("id") or ""))
        response = call_supabase(
            query.execute,
            operation_name="consultation terminal booking slot release",
        )
        return bool(response.data)
    except Exception as exc:
        logger.warning(
            "Consultation terminal booking slot release deferred (error_type=%s)",
            type(exc).__name__,
        )
        return False


def refresh_expired_mentor_consultation_order(
    supabase: Any,
    order: dict,
    *,
    now: datetime | None = None,
) -> dict:
    """Return the current order, settling expired paid orders atomically.

    The conditional status update is the concurrency guard: a participant who
    accepts or starts service at the same moment wins their newer state, while
    only the successful lifecycle transition writes a refund/event/message.
    """

    current_time = now or _utc_now()
    order_id = str(order.get("id") or "")
    order_status = str(order.get("order_status") or "")
    if not order_id:
        return order

    if order_status == "in_progress":
        started_at = _as_utc_datetime(order.get("started_at"))
        consultation_minutes = max(15, min(180, int(order.get("consultation_window_minutes") or 60)))
        if started_at is None:
            return order
        service_ends_at = started_at + timedelta(minutes=consultation_minutes)
        if service_ends_at > current_time:
            return order
        try:
            response = call_supabase(
                lambda: supabase.rpc(
                    "auto_complete_expired_mentor_consultation_order",
                    {"p_order_id": order_id, "p_now": current_time.isoformat()},
                ).execute(),
                operation_name="consultation service window auto completion",
            )
        except Exception as exc:
            if is_missing_supabase_relation_error(exc):
                # During a rolling release, order reads stay available until the
                # required database migration reaches this environment.
                logger.warning(
                    "Consultation auto completion RPC unavailable; migration pending "
                    "(order_id=%s error_type=%s)",
                    order_id,
                    type(exc).__name__,
                )
                return order
            raise
        if not response.data:
            # An open report/appeal intentionally leaves the order in progress;
            # a concurrent completion is returned when one already won.
            current_order = _get_order_or_existing(supabase, order_id, order)
            if str(current_order.get("order_status") or "") == "in_progress":
                current_order = {
                    **current_order,
                    "auto_completion_blocked_by_dispute": _has_open_consultation_dispute(
                        supabase,
                        order_id,
                    ),
                }
            return current_order

        completed_order = response.data[0]
        if str(completed_order.get("order_status") or "") != "completed":
            return completed_order
        # The RPC owns the order transition, system message, audit event and
        # both notification-outbox rows in one transaction. Python only starts
        # the idempotent wallet write; the periodic reconciler is its retry path.
        try:
            record_consultation_income_pending(supabase, completed_order)
        except Exception as exc:
            # The regular ledger reconciler retries idempotently in the same
            # background loop, so settlement accounting is never coupled to UX.
            logger.warning(
                "Consultation auto completion ledger write deferred "
                "(order_id=%s error_type=%s)",
                order_id,
                type(exc).__name__,
            )
        return completed_order

    if order_status == "pending_payment":
        payment_expires_at = _as_utc_datetime(order.get("payment_expires_at"))
        if payment_expires_at is None or payment_expires_at > current_time:
            return order
        response = call_supabase(
            lambda: supabase.rpc(
                "expire_mentor_consultation_payment_hold",
                {"p_order_id": order_id, "p_now": current_time.isoformat()},
            ).execute(),
            operation_name="consultation payment hold expiry",
        )
        if not response.data:
            return order
        expired_order = response.data[0]
        if str(expired_order.get("order_status") or "") != "pending_payment":
            _insert_system_message(
                supabase,
                order_id,
                "订单支付时限已结束，系统已关闭未支付订单并释放预约时段；本次未发生扣款。",
            )
            _insert_event(
                supabase,
                order_id,
                "consultation_payment_hold_expired",
                {
                    "payment_expires_at": payment_expires_at.isoformat(),
                    "slot_id": str(order.get("slot_id") or "") or None,
                },
            )
        return expired_order

    if order_status == "pending_accept":
        expires_at = _as_utc_datetime(order.get("expires_at"))
        if expires_at is None or expires_at > current_time:
            return order

        paid = str(order.get("payment_status") or "") == "paid"
        refund_amount_cents = max(0, int(order.get("price_cents") or 0)) if paid else 0
        refund_payment_status = _refund_payment_status(order) if paid else str(order.get("payment_status") or "unpaid")
        response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_orders")
                .update({
                    "order_status": "timeout",
                    "payment_status": refund_payment_status,
                    "ended_at": current_time.isoformat(),
                    "refund_amount_cents": refund_amount_cents,
                    "refund_reference": f"TIMEOUT-{str(order.get('order_no') or '')}" if paid else None,
                })
                .eq("id", order_id)
                .eq("order_status", "pending_accept")
                .execute()
            ),
            operation_name="consultation instant timeout settlement",
        )
        if not response.data:
            return _get_order_or_existing(supabase, order_id, order)
        timeout_content = (
            "前辈未在规定时间内接单，本次咨询已自动取消；测试退款已完成。"
            if paid and refund_payment_status == "refunded"
            else "前辈未在规定时间内接单，本次咨询已自动取消，平台已提交退款处理。"
            if paid
            else "前辈未在规定时间内接单，本次咨询已自动取消。"
        )
        _insert_system_message(supabase, order_id, timeout_content)
        _insert_event(
            supabase,
            order_id,
            "order_timed_out",
            {"refund_amount_cents": refund_amount_cents, "payment_status": refund_payment_status},
        )
        if paid:
            _insert_event(
                supabase,
                order_id,
                "consultation_refund_completed" if refund_payment_status == "refunded" else "consultation_refund_requested",
                {"refund_amount_cents": refund_amount_cents, "refund_reference": f"TIMEOUT-{str(order.get('order_no') or '')}", "reason": "order_timeout"},
            )
        _notify_applicant_of_lifecycle_timeout(
            supabase,
            order={**order, **response.data[0]},
            timeout_reason="order_timed_out",
            title="本次咨询已自动取消",
            summary="前辈未在规定时间内接单，订单与退款状态已更新。",
            content=timeout_content,
        )
        return response.data[0]

    if order_status == "accepted":
        # An instant request is not fulfilled merely because it was accepted:
        # the mentor must open the service window.  Older accepted rows did
        # not retain a deadline, so fall back to accepted_at during rollout.
        if str(order.get("consultation_type") or "") != "instant" or order.get("started_at"):
            return order
        start_deadline = _as_utc_datetime(order.get("expires_at"))
        if start_deadline is None:
            accepted_at = _as_utc_datetime(order.get("accepted_at"))
            if accepted_at is not None:
                start_deadline = accepted_at + timedelta(minutes=DEFAULT_INSTANT_START_GRACE_MINUTES)
        if start_deadline is None or start_deadline > current_time:
            return order

        paid = str(order.get("payment_status") or "") == "paid"
        refund_amount_cents = max(0, int(order.get("price_cents") or 0)) if paid else 0
        refund_payment_status = _refund_payment_status(order) if paid else str(order.get("payment_status") or "unpaid")
        response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_orders")
                .update({
                    "order_status": "timeout",
                    "payment_status": refund_payment_status,
                    "ended_at": current_time.isoformat(),
                    "refund_amount_cents": refund_amount_cents,
                    "refund_reference": f"START-TIMEOUT-{str(order.get('order_no') or '')}" if paid else None,
                })
                .eq("id", order_id)
                .eq("order_status", "accepted")
                .is_("started_at", "null")
                .execute()
            ),
            operation_name="consultation accepted start timeout settlement",
        )
        if not response.data:
            return _get_order_or_existing(supabase, order_id, order)
        timeout_content = (
            "前辈已接单但未在规定时间内开始服务，本次咨询已自动取消；测试退款已完成。"
            if paid and refund_payment_status == "refunded"
            else "前辈已接单但未在规定时间内开始服务，本次咨询已自动取消，平台已提交退款处理。"
            if paid
            else "前辈已接单但未在规定时间内开始服务，本次咨询已自动取消。"
        )
        _insert_system_message(supabase, order_id, timeout_content)
        _insert_event(
            supabase,
            order_id,
            "accepted_start_timed_out",
            {
                "start_deadline": start_deadline.isoformat(),
                "refund_amount_cents": refund_amount_cents,
                "payment_status": refund_payment_status,
            },
        )
        if paid:
            _insert_event(
                supabase,
                order_id,
                "consultation_refund_completed" if refund_payment_status == "refunded" else "consultation_refund_requested",
                {"refund_amount_cents": refund_amount_cents, "refund_reference": f"START-TIMEOUT-{str(order.get('order_no') or '')}", "reason": "accepted_start_timeout"},
            )
        _notify_applicant_of_lifecycle_timeout(
            supabase,
            order={**order, **response.data[0]},
            timeout_reason="accepted_start_timed_out",
            title="本次咨询未按时开始",
            summary="前辈接单后未在规定时间内开始服务，订单与退款状态已更新。",
            content=timeout_content,
        )
        return response.data[0]

    if order_status != "booked" or order.get("started_at"):
        return order

    slot_id = str(order.get("slot_id") or "")
    if not slot_id:
        return order
    slot_response = call_supabase(
        lambda: (
            supabase.table("mentor_availability_slots")
            .select("id,ends_at")
            .eq("id", slot_id)
            .limit(1)
            .execute()
        ),
        operation_name="consultation booking slot lifecycle lookup",
    )
    slot = (slot_response.data or [None])[0]
    ends_at = _as_utc_datetime((slot or {}).get("ends_at"))
    if ends_at is None or ends_at > current_time:
        return order

    paid = str(order.get("payment_status") or "") == "paid"
    refund_amount_cents = max(0, int(order.get("price_cents") or 0)) if paid else 0
    refund_payment_status = _refund_payment_status(order) if paid else str(order.get("payment_status") or "unpaid")
    response = call_supabase(
        lambda: (
            supabase.table("mentor_consultation_orders")
            .update({
                "order_status": "timeout",
                "payment_status": refund_payment_status,
                "ended_at": current_time.isoformat(),
                "refund_amount_cents": refund_amount_cents,
                "refund_reference": f"BOOKING-TIMEOUT-{str(order.get('order_no') or '')}" if paid else None,
            })
            .eq("id", order_id)
            .eq("order_status", "booked")
            .execute()
        ),
        operation_name="consultation booking no-show settlement",
    )
    if not response.data:
        return _get_order_or_existing(supabase, order_id, order)

    try:
        call_supabase(
            lambda: (
                supabase.table("mentor_availability_slots")
                .update({"status": "expired"})
                .eq("id", slot_id)
                .eq("status", "booked")
                .execute()
            ),
            operation_name="consultation booking no-show slot expiry",
        )
    except Exception as exc:
        logger.warning("Consultation booking no-show slot expiry skipped (error_type=%s)", type(exc).__name__)
    timeout_content = (
        "预约时段已结束，前辈未开始服务，本次咨询已自动取消；测试退款已完成。"
        if paid and refund_payment_status == "refunded"
        else "预约时段已结束，前辈未开始服务，本次咨询已自动取消，平台已提交退款处理。"
        if paid
        else "预约时段已结束，前辈未开始服务，本次咨询已自动取消。"
    )
    _insert_system_message(supabase, order_id, timeout_content)
    _insert_event(
        supabase,
        order_id,
        "booking_no_show_timed_out",
        {
            "slot_id": slot_id,
            "refund_amount_cents": refund_amount_cents,
            "payment_status": refund_payment_status,
        },
    )
    if paid:
        _insert_event(
            supabase,
            order_id,
            "consultation_refund_completed" if refund_payment_status == "refunded" else "consultation_refund_requested",
            {"refund_amount_cents": refund_amount_cents, "refund_reference": f"BOOKING-TIMEOUT-{str(order.get('order_no') or '')}", "reason": "booking_no_show"},
        )
    _notify_applicant_of_lifecycle_timeout(
        supabase,
        order={**order, **response.data[0]},
        timeout_reason="booking_no_show_timed_out",
        title="预约咨询未按时开始",
        summary="预约时段已结束，订单与退款状态已更新。",
        content=timeout_content,
    )
    return response.data[0]


def settle_expired_mentor_consultation_orders(*, limit: int = DEFAULT_SWEEP_LIMIT) -> int:
    """Settle expired orders and raise unanswered support cases without polling."""

    batch_size = max(1, min(int(limit or DEFAULT_SWEEP_LIMIT), DEFAULT_SWEEP_LIMIT))
    now = _utc_now()
    supabase = get_supabase_admin()
    changed = 0

    # The batch RPC filters on the stored service deadline after excluding open
    # reports/appeals, so a long-running dispute cannot occupy the page and
    # starve later eligible orders. Each transition and its visible side effects
    # still commit in one database transaction.
    try:
        in_progress_response = call_supabase(
            lambda: supabase.rpc(
                "auto_complete_expired_mentor_consultation_orders",
                {"p_limit": batch_size, "p_now": now.isoformat()},
            ).execute(),
            operation_name="consultation lifecycle in-progress batch completion",
        )
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            logger.warning(
                "Consultation auto completion batch RPC unavailable; migration pending "
                "(error_type=%s)",
                type(exc).__name__,
            )
            in_progress_response = None
        else:
            raise
    for completed_order in ((in_progress_response.data if in_progress_response else []) or []):
        changed += 1
        try:
            record_consultation_income_pending(supabase, completed_order)
        except Exception as exc:
            logger.warning(
                "Consultation auto completion ledger write deferred "
                "(order_id=%s error_type=%s)",
                str(completed_order.get("id") or ""),
                type(exc).__name__,
            )

    unpaid_response = call_supabase(
        lambda: (
            supabase.table("mentor_consultation_orders")
            .select("*")
            .eq("order_status", "pending_payment")
            .in_("payment_status", ["unpaid", "failed"])
            .lte("payment_expires_at", now.isoformat())
            .order("payment_expires_at")
            .limit(batch_size)
            .execute()
        ),
        operation_name="consultation lifecycle payment hold candidate list",
    )
    for order in unpaid_response.data or []:
        updated = refresh_expired_mentor_consultation_order(supabase, order, now=now)
        if str(updated.get("order_status") or "") != str(order.get("order_status") or ""):
            changed += 1

    pending_response = call_supabase(
        lambda: (
            supabase.table("mentor_consultation_orders")
            .select("*")
            .eq("order_status", "pending_accept")
            .lte("expires_at", now.isoformat())
            .order("expires_at")
            .limit(batch_size)
            .execute()
        ),
        operation_name="consultation lifecycle instant candidate list",
    )
    for order in pending_response.data or []:
        updated = refresh_expired_mentor_consultation_order(supabase, order, now=now)
        if str(updated.get("order_status") or "") != str(order.get("order_status") or ""):
            changed += 1

    accepted_response = call_supabase(
        lambda: (
            supabase.table("mentor_consultation_orders")
            .select("*")
            .eq("order_status", "accepted")
            .eq("consultation_type", "instant")
            .is_("started_at", "null")
            .order("accepted_at")
            .limit(batch_size)
            .execute()
        ),
        operation_name="consultation lifecycle accepted start candidate list",
    )
    for order in accepted_response.data or []:
        updated = refresh_expired_mentor_consultation_order(supabase, order, now=now)
        if str(updated.get("order_status") or "") != str(order.get("order_status") or ""):
            changed += 1

    expired_slot_response = call_supabase(
        lambda: (
            supabase.table("mentor_availability_slots")
            .select("id")
            .lte("ends_at", now.isoformat())
            .order("ends_at")
            .limit(batch_size)
            .execute()
        ),
        operation_name="consultation lifecycle booking slot candidate list",
    )
    slot_ids = [str(row.get("id") or "") for row in (expired_slot_response.data or []) if row.get("id")]
    if slot_ids:
        booked_response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_orders")
                .select("*")
                .eq("order_status", "booked")
                .in_("slot_id", slot_ids)
                .limit(batch_size)
                .execute()
            ),
            operation_name="consultation lifecycle booking candidate list",
        )
        for order in booked_response.data or []:
            updated = refresh_expired_mentor_consultation_order(supabase, order, now=now)
            if str(updated.get("order_status") or "") != str(order.get("order_status") or ""):
                changed += 1

        # A booking can finish from an already-started consultation. Once its
        # slot end has passed, converge any remaining `booked` slot to
        # `expired`; the legacy cleanup below intentionally targets orders that
        # never started and therefore does not cover this case.
        started_terminal_response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_orders")
                .select("id,consultation_type,slot_id,started_at")
                .eq("consultation_type", "booking")
                .in_("order_status", ["cancelled", "refunded", "timeout", "completed"])
                .in_("slot_id", slot_ids)
                .not_.is_("started_at", "null")
                .limit(batch_size)
                .execute()
            ),
            operation_name="consultation lifecycle started terminal booking cleanup list",
        )
        for order in started_terminal_response.data or []:
            release_terminal_mentor_booking_slot(supabase, order, now=now)

    # A user/admin cancellation updates the order first, then releases the
    # slot.  Retry terminal booking releases here so an interrupted request
    # never leaves a future time permanently unavailable.
    terminal_booking_response = call_supabase(
        lambda: (
            supabase.table("mentor_consultation_orders")
            .select("id,consultation_type,slot_id")
            .eq("consultation_type", "booking")
            .in_("order_status", ["cancelled", "refunded", "timeout", "completed"])
            .is_("started_at", "null")
            .limit(batch_size)
            .execute()
        ),
        operation_name="consultation lifecycle terminal booking cleanup list",
    )
    for order in terminal_booking_response.data or []:
        release_terminal_mentor_booking_slot(supabase, order, now=now)
    return changed + sweep_mentor_consultation_report_slas(
        supabase=supabase,
        now=now,
        limit=batch_size,
    )
