from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config import get_settings
from app.db import get_supabase_admin
from app.dependencies import require_question_admin_user
from app.schemas.mentor_consultation import (
    AdminMentorConsultationOrderDetailResponse,
    AdminMentorConsultationOrderInterventionRequest,
    AdminMentorConsultationOrderItem,
    AdminMentorConsultationOrderListResponse,
    AdminMentorConsultationReportDetailResponse,
    AdminMentorConsultationReportAppealDetailResponse,
    AdminMentorConsultationReportAppealEvidenceItem,
    AdminMentorConsultationReportAppealItem,
    AdminMentorConsultationReportAppealListResponse,
    AdminMentorConsultationReportAppealStatusUpdateRequest,
    AdminMentorConsultationReportEvidenceItem,
    AdminMentorConsultationReportItem,
    AdminMentorConsultationReportListResponse,
    AdminMentorConsultationReviewItem,
    AdminMentorConsultationReportStatusUpdateRequest,
    AdminMentorAvailabilitySlotCreateRequest,
    AdminMentorAvailabilitySlotItem,
    AdminMentorAvailabilitySlotListResponse,
    AdminMentorAvailabilitySlotUpdateRequest,
    AdminMentorProfileChangeDecisionRequest,
    AdminMentorProfileChangeRequestListResponse,
    AdminMentorProfileCreateRequest,
    AdminMentorProfileItem,
    AdminMentorProfileListResponse,
    AdminMentorProfileUpdateRequest,
    AdminMentorVerificationApplicationDetailResponse,
    AdminMentorVerificationApplicationListResponse,
    AdminMentorVerificationDecisionRequest,
    MentorVerificationApplicationItem,
    MentorVerificationDocumentItem,
    MentorProfileChangeRequestItem,
)
from app.services.mentor_consultation import (
    ADMIN_PROFILE_FIELDS,
    CONSULTATION_MESSAGE_FIELDS,
    CONSULTATION_ORDER_FIELDS,
    fetch_mentor_aggregates,
    fetch_mentor_skills,
    mask_mentor_name,
    normalize_skills,
    serialize_mentor_order,
    serialize_mentor_admin,
)
from app.services.mentor_consultation_lifecycle import (
    refresh_expired_mentor_consultation_order,
    release_terminal_mentor_booking_slot,
)
from app.services.mentor_consultation_sla import (
    case_priority_rank,
    normalize_case_priority,
    serialize_case_sla,
)
from app.services.supabase_resilience import call_supabase
from app.services.user_notifications import create_user_notification


router = APIRouter(prefix="/admin/mentor-consultation", tags=["前辈咨询后台"])
logger = logging.getLogger(__name__)

ADMIN_MENTOR_MAX_LIMIT = 100
MENTOR_VERIFICATION_DOCUMENT_BUCKET = "mentor-verification-documents"
MENTOR_APPLICATION_MAX_LIMIT = 100
MENTOR_PROFILE_CHANGE_REQUEST_MAX_LIMIT = 100
MENTOR_APPLICATION_FIELDS = (
    "id,applicant_user_id,legal_name,school,major,admission_year,graduation_year,"
    "exam_type,score,skills,bio,price_cents,application_status,admin_note,reviewed_by,"
    "reviewed_at,created_at,updated_at"
)
MENTOR_CONSULTATION_REPORT_EVIDENCE_BUCKET = "mentor-consultation-report-evidence"
MENTOR_CONSULTATION_REPORT_APPEAL_EVIDENCE_BUCKET = "mentor-consultation-report-appeal-evidence"
MENTOR_CONSULTATION_REPORT_MAX_LIMIT = 100
MENTOR_CONSULTATION_REPORT_APPEAL_MAX_LIMIT = 100
MENTOR_CONSULTATION_ORDER_ADMIN_MAX_LIMIT = 100
MENTOR_CONSULTATION_ORDER_STATUSES = {
    "draft", "pending_payment", "pending_accept", "accepted", "in_progress", "completed",
    "rejected", "timeout", "refunded", "cancelled", "booked",
}
MENTOR_CONSULTATION_PAYMENT_STATUSES = {"unpaid", "paid", "refunding", "refunded", "failed"}
MENTOR_CONSULTATION_TERMINAL_ORDER_STATUSES = {"completed", "refunded", "cancelled", "rejected", "timeout"}
MENTOR_CONSULTATION_OPEN_REPORT_STATUSES = {"pending", "reviewing"}
MENTOR_CONSULTATION_REPORT_FIELDS = (
    "id,order_id,reporter_user_id,reporter_role,respondent_user_id,target_role,target_user_id,target_mentor_id,"
    "issue_type,content,respondent_content,responded_at,status,resolution,refund_amount_cents,admin_note,handled_by,handled_at,"
    "first_response_due_at,first_response_at,priority,escalation_level,escalated_at,created_at,updated_at"
)
MENTOR_CONSULTATION_REVIEW_FIELDS = (
    "id,order_id,mentor_id,reviewer_user_id,reviewer_display_name,rating,tags,content,is_published,created_at"
)
MENTOR_REVIEW_DISPUTE_ISSUE_TYPE = "恶意评价或失实反馈"
MENTOR_CONSULTATION_REPORT_APPEAL_FIELDS = (
    "id,report_id,appellant_user_id,appellant_role,content,status,decision,admin_note,handled_by,handled_at,"
    "first_response_due_at,first_response_at,priority,escalation_level,escalated_at,created_at,updated_at"
)
MENTOR_CONSULTATION_REPORT_ORDER_FIELDS = (
    "id,order_no,applicant_user_id,mentor_id,slot_id,consultation_type,order_status,payment_status,"
    "questionnaire,price_cents,refund_amount_cents,refund_reference,started_at,ended_at,"
    "applicant_completion_confirmed_at,mentor_completion_confirmed_at,created_at"
)
MENTOR_PROFILE_CHANGE_REQUEST_FIELDS = (
    "id,mentor_id,owner_user_id,school,major,exam_type,score,skills,bio,price_cents,"
    "request_status,admin_note,reviewed_by,reviewed_at,created_at,updated_at"
)


def _is_demo_payment_reference(reference: object) -> bool:
    return str(reference or "").upper().startswith(("DEMO-", "MOCK-"))


def _refund_payment_status_for_order(order: dict) -> str:
    return "refunded" if _is_demo_payment_reference(order.get("payment_reference")) else "refunding"


def _can_initiate_or_retry_refund(order: dict) -> bool:
    payment_status = str(order.get("payment_status") or "")
    return payment_status == "paid" or (payment_status == "failed" and bool(order.get("refund_reference")))


def _replace_mentor_skills(supabase, mentor_id: str, skills: list[str]) -> None:
    normalized_skills = normalize_skills(skills)
    call_supabase(
        lambda: supabase.table("mentor_profile_skills").delete().eq("mentor_id", mentor_id).execute(),
        operation_name="admin mentor skill clear",
    )
    if not normalized_skills:
        return
    rows = [
        {"mentor_id": mentor_id, "skill": skill, "sort_order": index + 1}
        for index, skill in enumerate(normalized_skills)
    ]
    call_supabase(
        lambda: supabase.table("mentor_profile_skills").insert(rows).execute(),
        operation_name="admin mentor skill replace",
    )


def _get_mentor_or_404(supabase, mentor_id: str) -> dict:
    response = call_supabase(
        lambda: (
            supabase.table("mentor_profiles")
            .select(ADMIN_PROFILE_FIELDS)
            .eq("id", mentor_id)
            .limit(1)
            .execute()
        ),
        operation_name="admin mentor profile lookup",
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该前辈档案")
    return response.data[0]


def _get_slot_or_404(supabase, slot_id: str) -> dict:
    response = call_supabase(
        lambda: (
            supabase.table("mentor_availability_slots")
            .select("id,mentor_id,starts_at,ends_at,price_cents,status,created_at,updated_at")
            .eq("id", slot_id)
            .limit(1)
            .execute()
        ),
        operation_name="admin mentor slot lookup",
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该预约时段")
    return response.data[0]


def _serialize_admin_slot(row: dict) -> dict:
    return {
        "id": str(row.get("id") or ""),
        "mentor_id": str(row.get("mentor_id") or ""),
        "starts_at": row.get("starts_at") or None,
        "ends_at": row.get("ends_at") or None,
        "price": round(int(row["price_cents"]) / 100, 2) if row.get("price_cents") is not None else None,
        "status": str(row.get("status") or "available"),
        "created_at": row.get("created_at") or None,
        "updated_at": row.get("updated_at") or None,
    }


def _parse_database_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))


def _as_utc_datetime(value: object) -> datetime | None:
    try:
        parsed = _parse_database_datetime(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _serialize_consultation_case_sla(row: dict, *, appeal: bool = False) -> dict:
    settings = get_settings()
    return serialize_case_sla(
        row,
        fallback_first_response_hours=(
            settings.mentor_consultation_report_appeal_first_response_hours
            if appeal
            else settings.mentor_consultation_report_first_response_hours
        ),
        warning_hours=settings.mentor_consultation_report_sla_warning_hours,
    )


def _apply_consultation_case_sla_filters(
    query,
    *,
    priority: str,
    sla_state: str,
):
    """Apply a database-side work-queue filter for report or appeal cases."""

    if priority:
        query = query.eq("priority", priority)
    if not sla_state:
        return query

    settings = get_settings()
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    warning_deadline = now + timedelta(hours=max(1, int(settings.mentor_consultation_report_sla_warning_hours or 6)))
    if sla_state == "escalated":
        return query.gt("escalation_level", 0)

    query = query.in_("status", ["pending", "reviewing"]).is_("first_response_at", "null")
    if sla_state == "overdue":
        return query.lt("first_response_due_at", now_iso)
    if sla_state == "due_soon":
        return query.gte("first_response_due_at", now_iso).lte("first_response_due_at", warning_deadline.isoformat())
    # The client does not currently expose this option, but retaining it gives
    # operations a stable API for a clean "not close to breach" queue.
    return query.gt("first_response_due_at", warning_deadline.isoformat())


def _validate_owner_binding(supabase, owner_user_id: object, mentor_id: str | None = None) -> str | None:
    if owner_user_id is None:
        return None
    owner_id = str(owner_user_id)
    user_response = call_supabase(
        lambda: supabase.table("users").select("id").eq("id", owner_id).limit(1).execute(),
        operation_name="admin mentor owner lookup",
    )
    if not user_response.data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="绑定账号不存在")

    query = supabase.table("mentor_profiles").select("id").eq("owner_user_id", owner_id)
    if mentor_id:
        query = query.neq("id", mentor_id)
    bound_response = call_supabase(
        lambda: query.limit(1).execute(),
        operation_name="admin mentor owner conflict lookup",
    )
    if bound_response.data:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该账号已绑定其他前辈档案")
    return owner_id


def _log_admin_action(supabase, admin_profile: dict, action: str, mentor_id: str, details: dict | None = None) -> None:
    try:
        call_supabase(
            lambda: supabase.table("admin_action_logs").insert({
                "admin_user_id": admin_profile.get("id"),
                "action": action,
                "target_type": "mentor_profile",
                "target_id": mentor_id,
                "details": details or {},
            }).execute(),
            operation_name="mentor admin action log",
        )
    except Exception as exc:
        logger.warning("Mentor admin action log skipped (error_type=%s)", type(exc).__name__)


def _log_application_action(supabase, admin_profile: dict, action: str, application_id: str, details: dict | None = None) -> None:
    try:
        call_supabase(
            lambda: supabase.table("admin_action_logs").insert({
                "admin_user_id": admin_profile.get("id"),
                "action": action,
                "target_type": "mentor_verification_application",
                "target_id": application_id,
                "details": details or {},
            }).execute(),
            operation_name="mentor application admin action log",
        )
    except Exception as exc:
        logger.warning("Mentor application admin action log skipped (error_type=%s)", type(exc).__name__)


def _log_consultation_report_action(supabase, admin_profile: dict, action: str, report_id: str, details: dict | None = None) -> None:
    try:
        call_supabase(
            lambda: supabase.table("admin_action_logs").insert({
                "admin_user_id": admin_profile.get("id"),
                "action": action,
                "target_type": "mentor_consultation_report",
                "target_id": report_id,
                "details": details or {},
            }).execute(),
            operation_name="mentor consultation report admin action log",
        )
    except Exception as exc:
        logger.warning("Mentor consultation report action log skipped (error_type=%s)", type(exc).__name__)


def _log_consultation_review_action(supabase, admin_profile: dict, action: str, review_id: str, details: dict | None = None) -> None:
    try:
        call_supabase(
            lambda: supabase.table("admin_action_logs").insert({
                "admin_user_id": admin_profile.get("id"),
                "action": action,
                "target_type": "mentor_review",
                "target_id": review_id,
                "details": details or {},
            }).execute(),
            operation_name="mentor consultation review admin action log",
        )
    except Exception as exc:
        logger.warning("Mentor consultation review action log skipped (error_type=%s)", type(exc).__name__)


def _log_consultation_report_appeal_action(supabase, admin_profile: dict, action: str, appeal_id: str, details: dict | None = None) -> None:
    try:
        call_supabase(
            lambda: supabase.table("admin_action_logs").insert({
                "admin_user_id": admin_profile.get("id"),
                "action": action,
                "target_type": "mentor_consultation_report_appeal",
                "target_id": appeal_id,
                "details": details or {},
            }).execute(),
            operation_name="mentor consultation report appeal admin action log",
        )
    except Exception as exc:
        logger.warning("Mentor consultation report appeal action log skipped (error_type=%s)", type(exc).__name__)


def _log_consultation_order_action(supabase, admin_profile: dict, action: str, order_id: str, details: dict | None = None) -> None:
    try:
        call_supabase(
            lambda: supabase.table("admin_action_logs").insert({
                "admin_user_id": admin_profile.get("id"),
                "action": action,
                "target_type": "mentor_consultation_order",
                "target_id": order_id,
                "details": details or {},
            }).execute(),
            operation_name="mentor consultation order action log",
        )
    except Exception as exc:
        logger.warning("Mentor consultation order action log skipped (error_type=%s)", type(exc).__name__)


def _insert_consultation_admin_event(
    supabase,
    order_id: str,
    admin_profile: dict,
    event_type: str,
    details: dict | None = None,
) -> None:
    try:
        call_supabase(
            lambda: supabase.table("mentor_consultation_order_events").insert({
                "order_id": order_id,
                "actor_user_id": admin_profile.get("id"),
                "actor_role": "admin",
                "event_type": event_type,
                "details": details or {},
            }).execute(),
            operation_name="mentor consultation admin event create",
        )
    except Exception as exc:
        logger.warning("Mentor consultation admin event skipped (event=%s error_type=%s)", event_type, type(exc).__name__)


def _insert_consultation_admin_system_message(supabase, order_id: str, content: str) -> None:
    try:
        call_supabase(
            lambda: supabase.table("mentor_consultation_messages").insert({
                "order_id": order_id,
                "sender_role": "system",
                "message_type": "system",
                "content": content,
            }).execute(),
            operation_name="mentor consultation admin system message",
        )
    except Exception as exc:
        logger.warning("Mentor consultation admin system message skipped (error_type=%s)", type(exc).__name__)


def _insert_consultation_system_event(supabase, order_id: str, event_type: str, details: dict | None = None) -> None:
    try:
        call_supabase(
            lambda: supabase.table("mentor_consultation_order_events").insert({
                "order_id": order_id,
                "actor_role": "system",
                "event_type": event_type,
                "details": details or {},
            }).execute(),
            operation_name="mentor consultation system event create",
        )
    except Exception as exc:
        logger.warning("Mentor consultation system event skipped (event=%s error_type=%s)", event_type, type(exc).__name__)


def _serialize_mentor_application(row: dict, *, document_count: int = 0) -> dict:
    return {
        "id": str(row.get("id") or ""),
        "applicant_user_id": str(row.get("applicant_user_id") or ""),
        "legal_name": str(row.get("legal_name") or ""),
        "school": str(row.get("school") or ""),
        "major": str(row.get("major") or ""),
        "admission_year": int(row.get("admission_year") or 0),
        "graduation_year": int(row["graduation_year"]) if row.get("graduation_year") is not None else None,
        "exam_type": str(row.get("exam_type") or "Z001"),
        "score": int(row.get("score") or 0),
        "skills": normalize_skills(row.get("skills") if isinstance(row.get("skills"), list) else []),
        "bio": str(row.get("bio") or ""),
        "price": round(max(0, int(row.get("price_cents") or 0)) / 100, 2),
        "application_status": str(row.get("application_status") or "pending"),
        "admin_note": row.get("admin_note") or None,
        "reviewed_at": row.get("reviewed_at") or None,
        "created_at": row.get("created_at") or None,
        "updated_at": row.get("updated_at") or None,
        "document_count": max(0, int(document_count or 0)),
    }


def _serialize_mentor_profile_change_request(row: dict) -> dict:
    return {
        "id": str(row.get("id") or ""),
        "mentor_id": str(row.get("mentor_id") or ""),
        "owner_user_id": str(row.get("owner_user_id") or ""),
        "school": str(row.get("school") or ""),
        "major": str(row.get("major") or ""),
        "exam_type": str(row.get("exam_type") or "Z001"),
        "score": int(row.get("score") or 0),
        "skills": normalize_skills(row.get("skills") if isinstance(row.get("skills"), list) else [])[:4],
        "bio": str(row.get("bio") or ""),
        "price": round(max(0, int(row.get("price_cents") or 0)) / 100, 2),
        "request_status": str(row.get("request_status") or "pending"),
        "admin_note": row.get("admin_note") or None,
        "reviewed_at": row.get("reviewed_at") or None,
        "created_at": row.get("created_at") or None,
        "updated_at": row.get("updated_at") or None,
    }


def _get_mentor_profile_change_request_or_404(supabase, request_id: str) -> dict:
    response = call_supabase(
        lambda: (
            supabase.table("mentor_profile_change_requests")
            .select(MENTOR_PROFILE_CHANGE_REQUEST_FIELDS)
            .eq("id", request_id)
            .limit(1)
            .execute()
        ),
        operation_name="admin mentor profile change request lookup",
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到资料修改申请")
    return response.data[0]


def _log_profile_change_request_action(supabase, admin_profile: dict, action: str, request_id: str, details: dict | None = None) -> None:
    try:
        call_supabase(
            lambda: supabase.table("admin_action_logs").insert({
                "admin_user_id": admin_profile.get("id"),
                "action": action,
                "target_type": "mentor_profile_change_request",
                "target_id": request_id,
                "details": details or {},
            }).execute(),
            operation_name="mentor profile change request admin action log",
        )
    except Exception as exc:
        logger.warning("Mentor profile change request admin action log skipped (error_type=%s)", type(exc).__name__)


def _fetch_application_users(supabase, user_ids: list[str]) -> dict[str, dict]:
    ids = list(dict.fromkeys(str(user_id) for user_id in user_ids if user_id))
    if not ids:
        return {}
    response = call_supabase(
        lambda: (
            supabase.table("users")
            .select("id,nickname,email,phone,avatar_url")
            .in_("id", ids)
            .execute()
        ),
        operation_name="mentor application user lookup",
    )
    return {str(row.get("id") or ""): row for row in (response.data or [])}


def _fetch_application_document_counts(supabase, application_ids: list[str]) -> dict[str, int]:
    ids = list(dict.fromkeys(str(application_id) for application_id in application_ids if application_id))
    if not ids:
        return {}
    response = call_supabase(
        lambda: (
            supabase.table("mentor_verification_documents")
            .select("application_id")
            .in_("application_id", ids)
            .execute()
        ),
        operation_name="mentor application document count lookup",
    )
    counts = {application_id: 0 for application_id in ids}
    for row in response.data or []:
        application_id = str(row.get("application_id") or "")
        if application_id:
            counts[application_id] = counts.get(application_id, 0) + 1
    return counts


def _fetch_report_mentors(supabase, mentor_ids: list[str]) -> dict[str, dict]:
    ids = list(dict.fromkeys(str(mentor_id) for mentor_id in mentor_ids if mentor_id))
    if not ids:
        return {}
    response = call_supabase(
        lambda: (
            supabase.table("mentor_profiles")
            .select("id,legal_name,display_name,school,major,owner_user_id")
            .in_("id", ids)
            .execute()
        ),
        operation_name="consultation report mentor lookup",
    )
    return {str(row.get("id") or ""): row for row in (response.data or [])}


def _fetch_report_orders(supabase, order_ids: list[str]) -> dict[str, dict]:
    ids = list(dict.fromkeys(str(order_id) for order_id in order_ids if order_id))
    if not ids:
        return {}
    response = call_supabase(
        lambda: (
            supabase.table("mentor_consultation_orders")
            .select(MENTOR_CONSULTATION_REPORT_ORDER_FIELDS)
            .in_("id", ids)
            .execute()
        ),
        operation_name="consultation report order lookup",
    )
    return {str(row.get("id") or ""): row for row in (response.data or [])}


def _fetch_consultation_order_reviews(supabase, order_ids: list[str]) -> dict[str, dict]:
    ids = list(dict.fromkeys(str(order_id) for order_id in order_ids if order_id))
    if not ids:
        return {}
    response = call_supabase(
        lambda: (
            supabase.table("mentor_reviews")
            .select(MENTOR_CONSULTATION_REVIEW_FIELDS)
            .in_("order_id", ids)
            .execute()
        ),
        operation_name="admin consultation order review lookup",
    )
    return {str(row.get("order_id") or ""): row for row in (response.data or [])}


def _get_consultation_order_or_404(supabase, order_id: str) -> dict:
    response = call_supabase(
        lambda: (
            supabase.table("mentor_consultation_orders")
            .select(CONSULTATION_ORDER_FIELDS)
            .eq("id", order_id)
            .limit(1)
            .execute()
        ),
        operation_name="admin consultation order lookup",
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该咨询订单")
    return response.data[0]


def _fetch_consultation_order_slots(supabase, slot_ids: list[str]) -> dict[str, dict]:
    ids = list(dict.fromkeys(str(slot_id) for slot_id in slot_ids if slot_id))
    if not ids:
        return {}
    response = call_supabase(
        lambda: (
            supabase.table("mentor_availability_slots")
            .select("id,mentor_id,starts_at,ends_at,price_cents,status")
            .in_("id", ids)
            .execute()
        ),
        operation_name="admin consultation order slot lookup",
    )
    return {str(row.get("id") or ""): row for row in (response.data or [])}


def _fetch_consultation_order_reports(supabase, order_ids: list[str]) -> list[dict]:
    ids = list(dict.fromkeys(str(order_id) for order_id in order_ids if order_id))
    if not ids:
        return []
    response = call_supabase(
        lambda: (
            supabase.table("mentor_consultation_reports")
            .select(MENTOR_CONSULTATION_REPORT_FIELDS)
            .in_("order_id", ids)
            .order("created_at", desc=True)
            .execute()
        ),
        operation_name="admin consultation order report lookup",
    )
    return response.data or []


def _resolve_single_open_report_from_order_intervention(
    supabase,
    *,
    report: dict,
    admin_profile: dict,
    action: str,
    refund_amount_cents: int,
    admin_note: str,
    now_iso: str,
) -> tuple[dict, bool]:
    """Close the one open case that an order-level final intervention has decided.

    Order-level resolution intentionally supports exactly one open case.  Several
    independent reports must retain their own evidence and decision trail in the
    report queue instead of being closed by a broad order action.
    """

    resolution_by_action = {
        "refund_full": "refund_full",
        "refund_partial": "refund_partial",
        "close_service": "close_service",
    }
    resolution = resolution_by_action.get(action)
    if not resolution:
        return report, False

    report_id = str(report.get("id") or "")
    response = call_supabase(
        lambda: (
            supabase.table("mentor_consultation_reports")
            .update({
                "status": "resolved",
                "resolution": resolution,
            "refund_amount_cents": refund_amount_cents,
            "admin_note": admin_note,
            "handled_by": admin_profile.get("id"),
            "handled_at": now_iso,
            "first_response_at": report.get("first_response_at") or now_iso,
            })
            .eq("id", report_id)
            .in_("status", list(MENTOR_CONSULTATION_OPEN_REPORT_STATUSES))
            .execute()
        ),
        operation_name="admin order intervention report settlement",
    )
    if response.data:
        return response.data[0], True

    current = _get_consultation_report_or_404(supabase, report_id)
    if str(current.get("status") or "") not in MENTOR_CONSULTATION_OPEN_REPORT_STATUSES:
        return current, False
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="订单已完成处置，但关联问题反馈状态已变化；请刷新后在问题反馈队列完成结案",
    )


def _summarize_consultation_order_reports(rows: list[dict]) -> dict[str, dict]:
    summaries: dict[str, dict] = {}
    for row in rows:
        order_id = str(row.get("order_id") or "")
        if not order_id:
            continue
        summary = summaries.setdefault(order_id, {
            "report_count": 0,
            "open_report_count": 0,
            "overdue_report_count": 0,
            "escalated_report_count": 0,
            "latest_report_status": None,
        })
        summary["report_count"] += 1
        report_status = str(row.get("status") or "pending")
        if report_status in MENTOR_CONSULTATION_OPEN_REPORT_STATUSES:
            summary["open_report_count"] += 1
            sla = _serialize_consultation_case_sla(row)
            if sla.get("sla_status") == "overdue":
                summary["overdue_report_count"] += 1
            if int(sla.get("escalation_level") or 0) > 0:
                summary["escalated_report_count"] += 1
        if summary["latest_report_status"] is None:
            summary["latest_report_status"] = report_status
    return summaries


def _refresh_pending_accept_status(supabase, order: dict) -> dict:
    """Use the same timeout settlement as the participant-facing APIs."""

    return refresh_expired_mentor_consultation_order(supabase, order)


def _consultation_order_attention(
    row: dict,
    report_summary: dict,
    slot: dict | None,
) -> tuple[str | None, str | None]:
    open_report_count = int(report_summary.get("open_report_count") or 0)
    overdue_report_count = int(report_summary.get("overdue_report_count") or 0)
    if overdue_report_count:
        return "report_sla_overdue", f"有 {overdue_report_count} 条问题反馈已超过首次处理时限，系统已升级为优先队列。"
    escalated_report_count = int(report_summary.get("escalated_report_count") or 0)
    if escalated_report_count:
        return "report_sla_escalated", f"有 {escalated_report_count} 条问题反馈已升级为优先处理，请尽快完成首次核实。"
    if open_report_count:
        return "open_report", f"有 {open_report_count} 条待处理问题反馈，建议优先介入。"

    order_status = str(row.get("order_status") or "")
    now = datetime.now(timezone.utc)
    if order_status == "accepted":
        start_deadline = _as_utc_datetime(row.get("expires_at"))
        if start_deadline and start_deadline <= now:
            return "start_overdue", "前辈已接单但未在服务保护时间内开始咨询，请优先核实并处理。"

    if order_status == "booked":
        slot_end_at = _as_utc_datetime((slot or {}).get("ends_at"))
        if slot_end_at and slot_end_at <= now:
            return "booking_elapsed", "预约时段已结束，订单仍未完成，请核实履约情况。"

    if order_status == "in_progress":
        applicant_confirmed = bool(row.get("applicant_completion_confirmed_at"))
        mentor_confirmed = bool(row.get("mentor_completion_confirmed_at"))
        if applicant_confirmed != mentor_confirmed:
            waiting_for = "认证前辈" if applicant_confirmed else "咨询用户"
            return "completion_pending", f"一方已确认结束，正在等待{waiting_for}确认。"

        started_at = _as_utc_datetime(row.get("started_at"))
        duration_minutes = max(15, int(row.get("consultation_window_minutes") or 60))
        if started_at and started_at + timedelta(minutes=duration_minutes) <= now:
            return "service_window_elapsed", "约定咨询时段已结束，双方尚未确认完成，建议发送履约提醒。"

    return None, None


def _serialize_admin_consultation_order(
    row: dict,
    users: dict[str, dict],
    mentors: dict[str, dict],
    report_summaries: dict[str, dict],
    slots: dict[str, dict],
) -> dict:
    payload = serialize_mentor_order(row)
    applicant_id = str(row.get("applicant_user_id") or "")
    mentor_id = str(row.get("mentor_id") or "")
    slot_id = str(row.get("slot_id") or "")
    applicant = _serialize_report_user(users.get(applicant_id), "applicant")
    if applicant.get("display_name") == "用户":
        applicant["display_name"] = str(payload.get("questionnaire", {}).get("name") or "咨询用户")
    mentor_profile = mentors.get(mentor_id, {})
    mentor = {
        "id": mentor_id,
        "role": "mentor",
        "display_name": str(mentor_profile.get("display_name") or mentor_profile.get("legal_name") or "认证前辈"),
        "school": str(mentor_profile.get("school") or ""),
        "major": str(mentor_profile.get("major") or ""),
        "owner_user_id": str(mentor_profile.get("owner_user_id") or "") or None,
    }
    slot = slots.get(slot_id)
    summary = report_summaries.get(str(row.get("id") or ""), {})
    attention, attention_reason = _consultation_order_attention(row, summary, slot)
    payload.update({
        "applicant": applicant,
        "mentor": mentor,
        "slot": {
            "id": str(slot.get("id") or ""),
            "starts_at": slot.get("starts_at") or None,
            "ends_at": slot.get("ends_at") or None,
            "status": str(slot.get("status") or "available"),
            "price": round(max(0, int(slot.get("price_cents") or 0)) / 100, 2),
        } if slot else None,
        "report_count": int(summary.get("report_count") or 0),
        "open_report_count": int(summary.get("open_report_count") or 0),
        "overdue_report_count": int(summary.get("overdue_report_count") or 0),
        "escalated_report_count": int(summary.get("escalated_report_count") or 0),
        "latest_report_status": summary.get("latest_report_status") or None,
        "attention": attention,
        "attention_reason": attention_reason,
    })
    return payload


def _fetch_consultation_order_events(supabase, order_id: str) -> list[dict]:
    """The event table is introduced by the dispute migration; old environments stay readable."""

    try:
        response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_order_events")
                .select("id,actor_user_id,actor_role,event_type,details,created_at")
                .eq("order_id", order_id)
                .order("created_at", desc=False)
                .limit(200)
                .execute()
            ),
            operation_name="admin consultation order event list",
        )
        return response.data or []
    except Exception as exc:
        logger.warning("Consultation order events unavailable (error_type=%s)", type(exc).__name__)
        return []


def _fetch_report_evidence_counts(supabase, report_ids: list[str]) -> dict[str, int]:
    ids = list(dict.fromkeys(str(report_id) for report_id in report_ids if report_id))
    if not ids:
        return {}
    response = call_supabase(
        lambda: (
            supabase.table("mentor_consultation_report_evidence")
            .select("report_id")
            .in_("report_id", ids)
            .execute()
        ),
        operation_name="consultation report evidence count lookup",
    )
    counts = {report_id: 0 for report_id in ids}
    for row in response.data or []:
        report_id = str(row.get("report_id") or "")
        if report_id:
            counts[report_id] = counts.get(report_id, 0) + 1
    return counts


def _fetch_report_evidence_role_counts(supabase, report_ids: list[str]) -> dict[str, dict[str, int]]:
    ids = list(dict.fromkeys(str(report_id) for report_id in report_ids if report_id))
    if not ids:
        return {}
    response = call_supabase(
        lambda: (
            supabase.table("mentor_consultation_report_evidence")
            .select("report_id,submitter_role")
            .in_("report_id", ids)
            .execute()
        ),
        operation_name="admin consultation report evidence source lookup",
    )
    counts = {report_id: {"reporter": 0, "respondent": 0} for report_id in ids}
    for row in response.data or []:
        report_id = str(row.get("report_id") or "")
        submitter_role = str(row.get("submitter_role") or "reporter")
        if report_id in counts and submitter_role in {"reporter", "respondent"}:
            counts[report_id][submitter_role] += 1
    return counts


def _serialize_report_user(user: dict | None, role: str) -> dict:
    profile = user or {}
    return {
        "id": str(profile.get("id") or ""),
        "role": role,
        "display_name": str(profile.get("nickname") or profile.get("email") or profile.get("phone") or "用户"),
        "nickname": profile.get("nickname") or None,
        "email": profile.get("email") or None,
        "phone": profile.get("phone") or None,
    }


def _serialize_admin_consultation_report(
    row: dict,
    users: dict[str, dict],
    mentors: dict[str, dict],
    orders: dict[str, dict],
    *,
    evidence_count: int = 0,
    evidence_role_counts: dict[str, int] | None = None,
) -> dict:
    reporter_id = str(row.get("reporter_user_id") or "")
    target_user_id = str(row.get("target_user_id") or "")
    target_mentor_id = str(row.get("target_mentor_id") or "")
    target_role = str(row.get("target_role") or "mentor")
    if target_role == "mentor":
        target_mentor = mentors.get(target_mentor_id, {})
        target = {
            "id": target_mentor_id,
            "role": "mentor",
            "display_name": str(target_mentor.get("display_name") or target_mentor.get("legal_name") or "认证前辈"),
            "school": target_mentor.get("school") or None,
            "major": target_mentor.get("major") or None,
        }
    else:
        target = _serialize_report_user(users.get(target_user_id), "applicant")

    order = orders.get(str(row.get("order_id") or ""), {})
    role_counts = evidence_role_counts or {}
    sla = _serialize_consultation_case_sla(row)
    return {
        "id": str(row.get("id") or ""),
        "order_id": str(row.get("order_id") or ""),
        "reporter_role": str(row.get("reporter_role") or "applicant"),
        "target_role": target_role,
        "issue_type": str(row.get("issue_type") or "其他问题"),
        "content": str(row.get("content") or ""),
        "respondent_content": str(row.get("respondent_content") or "") or None,
        "responded_at": row.get("responded_at") or None,
        "status": str(row.get("status") or "pending"),
        "resolution": str(row.get("resolution") or "none"),
        "refund_amount": round(max(0, int(row.get("refund_amount_cents") or 0)) / 100, 2),
        "created_at": row.get("created_at") or None,
        "reporter": _serialize_report_user(users.get(reporter_id), str(row.get("reporter_role") or "applicant")),
        "target": target,
        "order_no": str(order.get("order_no") or "") or None,
        "admin_note": row.get("admin_note") or None,
        "handled_at": row.get("handled_at") or None,
        "evidence_count": max(0, int(evidence_count or 0)),
        "reporter_evidence_count": max(0, int(role_counts.get("reporter") or 0)),
        "respondent_evidence_count": max(0, int(role_counts.get("respondent") or 0)),
        **sla,
    }


def _serialize_admin_consultation_review(row: dict) -> dict:
    raw_tags = row.get("tags")
    tags = [str(tag).strip() for tag in raw_tags if str(tag).strip()] if isinstance(raw_tags, list) else []
    return {
        "id": str(row.get("id") or ""),
        "order_id": str(row.get("order_id") or ""),
        "mentor_id": str(row.get("mentor_id") or ""),
        "reviewer_user_id": str(row.get("reviewer_user_id") or "") or None,
        "reviewer_display_name": str(row.get("reviewer_display_name") or "匿名用户"),
        "rating": float(row.get("rating") or 0),
        "tags": tags,
        "content": str(row.get("content") or ""),
        "is_published": bool(row.get("is_published")),
        "created_at": row.get("created_at") or None,
    }


def _report_evidence_admin_item(supabase, row: dict) -> dict:
    stored_url = str(row.get("file_url") or "")
    file_url = stored_url
    if stored_url:
        try:
            signed = supabase.storage.from_(MENTOR_CONSULTATION_REPORT_EVIDENCE_BUCKET).create_signed_url(stored_url, 3600)
            if isinstance(signed, dict):
                file_url = str(signed.get("signedURL") or signed.get("signedUrl") or stored_url)
        except Exception as exc:
            logger.warning("Consultation report evidence signing failed (error_type=%s)", type(exc).__name__)
    return {
        "id": str(row.get("id") or ""),
        "file_name": str(row.get("file_name") or "举报凭证"),
        "mime_type": row.get("mime_type") or None,
        "submitter_role": str(row.get("submitter_role") or "reporter"),
        "created_at": row.get("created_at") or None,
        "file_url": file_url,
    }


def _fetch_report_appeal_evidence_counts(supabase, appeal_ids: list[str]) -> dict[str, int]:
    ids = list(dict.fromkeys(str(appeal_id) for appeal_id in appeal_ids if appeal_id))
    if not ids:
        return {}
    response = call_supabase(
        lambda: (
            supabase.table("mentor_consultation_report_appeal_evidence")
            .select("appeal_id")
            .in_("appeal_id", ids)
            .execute()
        ),
        operation_name="admin consultation report appeal evidence count lookup",
    )
    counts = {appeal_id: 0 for appeal_id in ids}
    for row in response.data or []:
        appeal_id = str(row.get("appeal_id") or "")
        if appeal_id in counts:
            counts[appeal_id] += 1
    return counts


def _report_appeal_evidence_admin_item(supabase, row: dict) -> dict:
    stored_url = str(row.get("file_url") or "")
    file_url = stored_url
    if stored_url:
        try:
            signed = supabase.storage.from_(MENTOR_CONSULTATION_REPORT_APPEAL_EVIDENCE_BUCKET).create_signed_url(stored_url, 3600)
            if isinstance(signed, dict):
                file_url = str(signed.get("signedURL") or signed.get("signedUrl") or stored_url)
        except Exception as exc:
            logger.warning("Consultation report appeal evidence signing failed (error_type=%s)", type(exc).__name__)
    return {
        "id": str(row.get("id") or ""),
        "file_name": str(row.get("file_name") or "复核凭证"),
        "mime_type": row.get("mime_type") or None,
        "created_at": row.get("created_at") or None,
        "file_url": file_url,
    }


def _serialize_admin_consultation_report_appeal(
    row: dict,
    reports: dict[str, dict],
    users: dict[str, dict],
    mentors: dict[str, dict],
    orders: dict[str, dict],
    *,
    evidence_count: int = 0,
) -> dict:
    report = reports.get(str(row.get("report_id") or ""), {})
    appellant_role = str(row.get("appellant_role") or "reporter")
    actual_role = str(report.get("reporter_role") or "applicant") if appellant_role == "reporter" else str(report.get("target_role") or "applicant")
    appellant_id = str(row.get("appellant_user_id") or "")
    if actual_role == "mentor":
        mentor = mentors.get(str(report.get("target_mentor_id") or ""), {})
        appellant = {
            "id": appellant_id,
            "role": "mentor",
            "display_name": str(mentor.get("display_name") or mentor.get("legal_name") or "认证前辈"),
            "school": mentor.get("school") or None,
            "major": mentor.get("major") or None,
        }
    else:
        appellant = _serialize_report_user(users.get(appellant_id), "applicant")

    order = orders.get(str(report.get("order_id") or ""), {})
    sla = _serialize_consultation_case_sla(row, appeal=True)
    return {
        "id": str(row.get("id") or ""),
        "report_id": str(row.get("report_id") or ""),
        "appellant_role": appellant_role,
        "content": str(row.get("content") or ""),
        "status": str(row.get("status") or "pending"),
        "decision": str(row.get("decision") or "none"),
        "admin_note": row.get("admin_note") or None,
        "evidence_count": max(0, int(evidence_count or 0)),
        "created_at": row.get("created_at") or None,
        "handled_at": row.get("handled_at") or None,
        "appellant": appellant,
        "report": {
            "id": str(report.get("id") or ""),
            "order_id": str(report.get("order_id") or ""),
            "issue_type": str(report.get("issue_type") or "咨询问题反馈"),
            "status": str(report.get("status") or "pending"),
            "resolution": str(report.get("resolution") or "none"),
            "admin_note": report.get("admin_note") or None,
            "reporter_role": str(report.get("reporter_role") or "applicant"),
            "target_role": str(report.get("target_role") or "mentor"),
        },
        "order_no": str(order.get("order_no") or "") or None,
        **sla,
    }


def _get_consultation_report_appeal_or_404(supabase, appeal_id: str) -> dict:
    response = call_supabase(
        lambda: (
            supabase.table("mentor_consultation_report_appeals")
            .select(MENTOR_CONSULTATION_REPORT_APPEAL_FIELDS)
            .eq("id", appeal_id)
            .limit(1)
            .execute()
        ),
        operation_name="admin consultation report appeal lookup",
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该复核申请")
    return response.data[0]


def _get_consultation_report_or_404(supabase, report_id: str) -> dict:
    response = call_supabase(
        lambda: (
            supabase.table("mentor_consultation_reports")
            .select(MENTOR_CONSULTATION_REPORT_FIELDS)
            .eq("id", report_id)
            .limit(1)
            .execute()
        ),
        operation_name="admin consultation report lookup",
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该举报记录")
    return response.data[0]


def _mentor_document_admin_item(supabase, row: dict) -> dict:
    stored_url = str(row.get("file_url") or "")
    file_url = stored_url
    if stored_url and not stored_url.startswith(("http://", "https://")):
        try:
            signed = supabase.storage.from_(MENTOR_VERIFICATION_DOCUMENT_BUCKET).create_signed_url(stored_url, 3600)
            if isinstance(signed, dict):
                file_url = str(signed.get("signedURL") or signed.get("signedUrl") or stored_url)
        except Exception as exc:
            logger.warning("Mentor verification document signing failed (error_type=%s)", type(exc).__name__)
    return {
        "id": str(row.get("id") or ""),
        "file_url": file_url,
        "file_name": str(row.get("file_name") or "证明材料"),
        "document_type": str(row.get("document_type") or "other"),
        "mime_type": row.get("mime_type") or None,
        "created_at": row.get("created_at") or None,
    }


def _get_mentor_application_or_404(supabase, application_id: str) -> dict:
    response = call_supabase(
        lambda: (
            supabase.table("mentor_verification_applications")
            .select(MENTOR_APPLICATION_FIELDS)
            .eq("id", application_id)
            .limit(1)
            .execute()
        ),
        operation_name="mentor application lookup",
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到前辈申请")
    return response.data[0]


@router.get("/applications", response_model=AdminMentorVerificationApplicationListResponse)
def list_admin_mentor_verification_applications(
    application_status: str | None = Query(default=None, max_length=20),
    keyword: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=50, ge=1, le=MENTOR_APPLICATION_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_question_admin_user),
) -> AdminMentorVerificationApplicationListResponse:
    normalized_status = str(application_status or "").strip().lower()
    normalized_keyword = str(keyword or "").strip().lower()
    if normalized_status and normalized_status not in {"pending", "approved", "rejected"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的申请状态")

    supabase = get_supabase_admin()
    try:
        query = supabase.table("mentor_verification_applications").select(MENTOR_APPLICATION_FIELDS, count="exact")
        if normalized_status:
            query = query.eq("application_status", normalized_status)
        response = call_supabase(
            lambda: query.order("created_at", desc=True).range(offset, offset + limit - 1).execute(),
            operation_name="admin mentor application list",
        )
        rows = response.data or []
        users_by_id = _fetch_application_users(supabase, [str(row.get("applicant_user_id") or "") for row in rows])
        if normalized_keyword:
            rows = [
                row for row in rows
                if normalized_keyword in " ".join(
                    str(value or "")
                    for value in (
                        row.get("legal_name"),
                        row.get("school"),
                        row.get("major"),
                        users_by_id.get(str(row.get("applicant_user_id") or ""), {}).get("nickname"),
                        users_by_id.get(str(row.get("applicant_user_id") or ""), {}).get("email"),
                        users_by_id.get(str(row.get("applicant_user_id") or ""), {}).get("phone"),
                    )
                ).lower()
            ]
        document_counts = _fetch_application_document_counts(supabase, [str(row.get("id") or "") for row in rows])
        return AdminMentorVerificationApplicationListResponse(
            items=[
                MentorVerificationApplicationItem(
                    **_serialize_mentor_application(
                        row,
                        document_count=document_counts.get(str(row.get("id") or ""), 0),
                    )
                )
                for row in rows
            ],
            count=len(rows) if normalized_keyword else int(response.count or len(rows)),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin mentor application list unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="前辈申请数据暂时不可用") from exc


@router.get("/applications/{application_id}", response_model=AdminMentorVerificationApplicationDetailResponse)
def get_admin_mentor_verification_application(
    application_id: str,
    _: dict = Depends(require_question_admin_user),
) -> AdminMentorVerificationApplicationDetailResponse:
    supabase = get_supabase_admin()
    try:
        application = _get_mentor_application_or_404(supabase, application_id)
        user_by_id = _fetch_application_users(supabase, [str(application.get("applicant_user_id") or "")])
        document_response = call_supabase(
            lambda: (
                supabase.table("mentor_verification_documents")
                .select("id,file_url,file_name,document_type,mime_type,created_at")
                .eq("application_id", application_id)
                .order("created_at")
                .limit(3)
                .execute()
            ),
            operation_name="admin mentor application document list",
        )
        documents = [_mentor_document_admin_item(supabase, row) for row in (document_response.data or [])]
        return AdminMentorVerificationApplicationDetailResponse(
            application=MentorVerificationApplicationItem(
                **_serialize_mentor_application(application, document_count=len(documents))
            ),
            applicant=user_by_id.get(str(application.get("applicant_user_id") or ""), {}),
            documents=[MentorVerificationDocumentItem(**document) for document in documents],
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin mentor application detail unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="前辈申请详情暂时不可用") from exc


@router.post("/applications/{application_id}/decision", response_model=MentorVerificationApplicationItem)
def decide_admin_mentor_verification_application(
    application_id: str,
    payload: AdminMentorVerificationDecisionRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> MentorVerificationApplicationItem:
    supabase = get_supabase_admin()
    try:
        application = _get_mentor_application_or_404(supabase, application_id)
        if application.get("application_status") != "pending":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该前辈申请已经处理")

        decision = payload.decision
        update_data = {
            "application_status": "approved" if decision == "approve" else "rejected",
            "admin_note": payload.admin_note.strip() if payload.admin_note else None,
            "reviewed_by": admin_profile.get("id"),
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        }
        mentor_id = None
        if decision == "approve":
            owner_user_id = str(application.get("applicant_user_id") or "")
            profile_response = call_supabase(
                lambda: (
                    supabase.table("mentor_profiles")
                    .select("id")
                    .eq("owner_user_id", owner_user_id)
                    .limit(1)
                    .execute()
                ),
                operation_name="approved mentor profile lookup",
            )
            if profile_response.data:
                mentor_id = str(profile_response.data[0].get("id") or "")
            else:
                profile_data = {
                    "owner_user_id": owner_user_id,
                    "legal_name": str(application.get("legal_name") or "").strip(),
                    "display_name": mask_mentor_name(application.get("legal_name")),
                    "avatar_label": str(application.get("legal_name") or "前")[:1],
                    "avatar_tone": "blue",
                    "school": str(application.get("school") or "").strip(),
                    "major": str(application.get("major") or "").strip(),
                    "admission_year": int(application.get("admission_year") or 0),
                    "graduation_year": application.get("graduation_year"),
                    "exam_type": application.get("exam_type"),
                    "score": int(application.get("score") or 0),
                    "bio": str(application.get("bio") or ""),
                    "story": "",
                    "price_cents": int(application.get("price_cents") or 0),
                    "consultation_window_minutes": 60,
                    "online_status": "offline",
                    "accepts_booking": True,
                    "verification_status": "verified",
                    "is_published": True,
                    "is_featured": False,
                    "recommend_score": 0,
                    "rating": 0,
                    "rating_count": 0,
                    "consult_count": 0,
                }
                profile_response = call_supabase(
                    lambda: supabase.table("mentor_profiles").insert(profile_data).execute(),
                    operation_name="approved mentor profile create",
                )
                if not profile_response.data:
                    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="前辈档案创建失败")
                mentor_id = str(profile_response.data[0].get("id") or "")
                _replace_mentor_skills(supabase, mentor_id, application.get("skills") or [])

        response = call_supabase(
            lambda: (
                supabase.table("mentor_verification_applications")
                .update(update_data)
                .eq("id", application_id)
                .eq("application_status", "pending")
                .execute()
            ),
            operation_name="admin mentor application decision",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该前辈申请已经处理")
        _log_application_action(
            supabase,
            admin_profile,
            "approve_mentor_application" if decision == "approve" else "reject_mentor_application",
            application_id,
            {"mentor_id": mentor_id, "admin_note": update_data["admin_note"]},
        )
        document_counts = _fetch_application_document_counts(supabase, [application_id])
        return MentorVerificationApplicationItem(
            **_serialize_mentor_application(
                response.data[0],
                document_count=document_counts.get(application_id, 0),
            )
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin mentor application decision failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="前辈申请处理失败") from exc


@router.get("/profile-change-requests", response_model=AdminMentorProfileChangeRequestListResponse)
def list_admin_mentor_profile_change_requests(
    request_status: str | None = Query(default=None, max_length=20),
    keyword: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=50, ge=1, le=MENTOR_PROFILE_CHANGE_REQUEST_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_question_admin_user),
) -> AdminMentorProfileChangeRequestListResponse:
    normalized_status = str(request_status or "").strip().lower()
    normalized_keyword = str(keyword or "").strip().lower()
    if normalized_status and normalized_status not in {"pending", "approved", "rejected"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的资料修改状态")

    supabase = get_supabase_admin()
    try:
        query = supabase.table("mentor_profile_change_requests").select(MENTOR_PROFILE_CHANGE_REQUEST_FIELDS, count="exact")
        if normalized_status:
            query = query.eq("request_status", normalized_status)
        response = call_supabase(
            lambda: query.order("created_at", desc=True).range(offset, offset + limit - 1).execute(),
            operation_name="admin mentor profile change request list",
        )
        rows = response.data or []
        if normalized_keyword:
            rows = [
                row for row in rows
                if normalized_keyword in " ".join(
                    str(row.get(field) or "") for field in ("school", "major", "exam_type", "owner_user_id")
                ).lower()
            ]
        return AdminMentorProfileChangeRequestListResponse(
            items=[MentorProfileChangeRequestItem(**_serialize_mentor_profile_change_request(row)) for row in rows],
            count=len(rows) if normalized_keyword else int(response.count or len(rows)),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin mentor profile change request list unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="资料修改申请暂时不可用") from exc


@router.get("/profile-change-requests/{request_id}", response_model=MentorProfileChangeRequestItem)
def get_admin_mentor_profile_change_request(
    request_id: str,
    _: dict = Depends(require_question_admin_user),
) -> MentorProfileChangeRequestItem:
    supabase = get_supabase_admin()
    try:
        return MentorProfileChangeRequestItem(**_serialize_mentor_profile_change_request(
            _get_mentor_profile_change_request_or_404(supabase, request_id)
        ))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin mentor profile change request detail unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="资料修改申请详情暂时不可用") from exc


@router.post("/profile-change-requests/{request_id}/decision", response_model=MentorProfileChangeRequestItem)
def decide_admin_mentor_profile_change_request(
    request_id: str,
    payload: AdminMentorProfileChangeDecisionRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> MentorProfileChangeRequestItem:
    supabase = get_supabase_admin()
    try:
        request_row = _get_mentor_profile_change_request_or_404(supabase, request_id)
        if request_row.get("request_status") != "pending":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该资料修改申请已经处理")

        response = call_supabase(
            lambda: supabase.rpc(
                "resolve_mentor_profile_change_request",
                {
                    "p_request_id": request_id,
                    "p_decision": payload.decision,
                    "p_reviewer_user_id": admin_profile.get("id"),
                    "p_admin_note": payload.admin_note.strip() if payload.admin_note else None,
                },
            ).execute(),
            operation_name="admin mentor profile change request decision",
        )
        resolved = response.data[0] if isinstance(response.data, list) and response.data else response.data
        if not isinstance(resolved, dict):
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="资料修改审核处理失败")
        _log_profile_change_request_action(
            supabase,
            admin_profile,
            "approve_mentor_profile_change_request" if payload.decision == "approve" else "reject_mentor_profile_change_request",
            request_id,
            {"mentor_id": str(request_row.get("mentor_id") or ""), "admin_note": payload.admin_note.strip() if payload.admin_note else None},
        )
        return MentorProfileChangeRequestItem(**_serialize_mentor_profile_change_request(resolved))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin mentor profile change request decision failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="资料修改审核处理失败") from exc


@router.get("/mentors", response_model=AdminMentorProfileListResponse)
def list_admin_mentors(
    keyword: str | None = Query(default=None, max_length=120),
    verification_status: str | None = Query(default=None, max_length=20),
    visibility: str = Query(default="all", max_length=20),
    limit: int = Query(default=30, ge=1, le=ADMIN_MENTOR_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_question_admin_user),
) -> AdminMentorProfileListResponse:
    normalized_keyword = str(keyword or "").strip().lower()
    normalized_status = str(verification_status or "").strip().lower()
    normalized_visibility = str(visibility or "all").strip().lower()
    if normalized_status and normalized_status not in {"unverified", "pending", "verified", "rejected"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的认证状态")
    if normalized_visibility not in {"all", "published", "hidden"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的展示状态")

    supabase = get_supabase_admin()
    try:
        query = supabase.table("mentor_profiles").select(ADMIN_PROFILE_FIELDS, count="exact")
        if normalized_status:
            query = query.eq("verification_status", normalized_status)
        if normalized_visibility == "published":
            query = query.eq("is_published", True)
        elif normalized_visibility == "hidden":
            query = query.eq("is_published", False)
        response = call_supabase(
            lambda: query.order("updated_at", desc=True).range(offset, offset + limit - 1).execute(),
            operation_name="admin mentor profile list",
        )
        rows = response.data or []
        if normalized_keyword:
            rows = [
                row for row in rows
                if normalized_keyword in " ".join(
                    str(row.get(field) or "")
                    for field in ("legal_name", "display_name", "school", "major")
                ).lower()
            ]
        mentor_ids = [str(row.get("id") or "") for row in rows]
        skills_by_mentor = fetch_mentor_skills(supabase, mentor_ids)
        aggregates_by_mentor = fetch_mentor_aggregates(supabase, mentor_ids)
        return AdminMentorProfileListResponse(
            items=[
                serialize_mentor_admin(
                    row,
                    skills_by_mentor.get(str(row.get("id") or ""), []),
                    aggregates_by_mentor.get(str(row.get("id") or "")),
                )
                for row in rows
            ],
            count=len(rows) if normalized_keyword else int(response.count or len(rows)),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin mentor list unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="前辈咨询数据暂时不可用，请确认已应用前辈咨询数据库迁移",
        ) from exc


@router.get("/mentors/{mentor_id}", response_model=AdminMentorProfileItem)
def get_admin_mentor(
    mentor_id: str,
    _: dict = Depends(require_question_admin_user),
) -> AdminMentorProfileItem:
    supabase = get_supabase_admin()
    try:
        row = _get_mentor_or_404(supabase, mentor_id)
        skills_by_mentor = fetch_mentor_skills(supabase, [mentor_id])
        aggregates_by_mentor = fetch_mentor_aggregates(supabase, [mentor_id])
        return AdminMentorProfileItem(**serialize_mentor_admin(
            row,
            skills_by_mentor.get(mentor_id, []),
            aggregates_by_mentor.get(mentor_id),
        ))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin mentor detail unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="前辈档案暂时不可用") from exc


@router.post("/mentors", response_model=AdminMentorProfileItem, status_code=status.HTTP_201_CREATED)
def create_admin_mentor(
    payload: AdminMentorProfileCreateRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminMentorProfileItem:
    data = payload.model_dump(exclude={"skills"})
    data["legal_name"] = data["legal_name"].strip()
    data["display_name"] = mask_mentor_name(data["legal_name"])
    data["avatar_label"] = (data.pop("avatar", None) or data["legal_name"][:1]).strip()[:4]
    data["rating"] = 0
    data["rating_count"] = 0
    data["consult_count"] = 0
    if data.get("graduation_year") is not None and data["graduation_year"] < data["admission_year"]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="毕业年份不能早于入学年份")
    supabase = get_supabase_admin()
    try:
        data["owner_user_id"] = _validate_owner_binding(supabase, data.get("owner_user_id"))
        response = call_supabase(
            lambda: supabase.table("mentor_profiles").insert(data).execute(),
            operation_name="admin mentor profile create",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="前辈档案创建失败")
        row = response.data[0]
        _replace_mentor_skills(supabase, str(row["id"]), payload.skills)
        row = _get_mentor_or_404(supabase, str(row["id"]))
        skills_by_mentor = fetch_mentor_skills(supabase, [str(row["id"])])
        aggregates_by_mentor = fetch_mentor_aggregates(supabase, [str(row["id"])])
        _log_admin_action(supabase, admin_profile, "create_mentor_profile", str(row["id"]), {"fields": sorted(data)})
        return AdminMentorProfileItem(**serialize_mentor_admin(
            row,
            skills_by_mentor.get(str(row["id"]), []),
            aggregates_by_mentor.get(str(row["id"])),
        ))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin mentor create failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="前辈档案创建失败") from exc


@router.patch("/mentors/{mentor_id}", response_model=AdminMentorProfileItem)
def update_admin_mentor(
    mentor_id: str,
    payload: AdminMentorProfileUpdateRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminMentorProfileItem:
    update_data = payload.model_dump(exclude_unset=True, exclude={"skills"})
    for aggregate_field in ("rating", "rating_count", "consult_count"):
        update_data.pop(aggregate_field, None)
    supabase = get_supabase_admin()
    try:
        current = _get_mentor_or_404(supabase, mentor_id)
        avatar_value = update_data.pop("avatar", None)
        if not update_data and "skills" not in payload.model_fields_set and "avatar" not in payload.model_fields_set:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="没有需要更新的字段")
        if "owner_user_id" in update_data:
            update_data["owner_user_id"] = _validate_owner_binding(
                supabase,
                update_data.get("owner_user_id"),
                mentor_id,
            )
        if "legal_name" in update_data:
            update_data["legal_name"] = str(update_data["legal_name"] or "").strip()
            update_data["display_name"] = mask_mentor_name(update_data["legal_name"])
            if "avatar" not in payload.model_fields_set:
                update_data["avatar_label"] = update_data["legal_name"][:1]
        if "avatar" in payload.model_fields_set:
            update_data["avatar_label"] = (avatar_value or current.get("avatar_label") or "研").strip()[:4]
        admission_year = int(update_data.get("admission_year", current.get("admission_year") or 0))
        graduation_year = update_data.get("graduation_year", current.get("graduation_year"))
        if graduation_year is not None and int(graduation_year) < admission_year:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="毕业年份不能早于入学年份")
        if update_data:
            response = call_supabase(
                lambda: supabase.table("mentor_profiles").update(update_data).eq("id", mentor_id).execute(),
                operation_name="admin mentor profile update",
            )
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该前辈档案")
        if "skills" in payload.model_fields_set:
            _replace_mentor_skills(supabase, mentor_id, payload.skills or [])
        row = _get_mentor_or_404(supabase, mentor_id)
        skills_by_mentor = fetch_mentor_skills(supabase, [mentor_id])
        aggregates_by_mentor = fetch_mentor_aggregates(supabase, [mentor_id])
        _log_admin_action(
            supabase,
            admin_profile,
            "update_mentor_profile",
            mentor_id,
            {"fields": sorted([*update_data.keys(), *( ["skills"] if "skills" in payload.model_fields_set else [] )])},
        )
        return AdminMentorProfileItem(**serialize_mentor_admin(
            row,
            skills_by_mentor.get(mentor_id, []),
            aggregates_by_mentor.get(mentor_id),
        ))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin mentor update failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="前辈档案更新失败") from exc


@router.get(
    "/mentors/{mentor_id}/slots",
    response_model=AdminMentorAvailabilitySlotListResponse,
)
def list_admin_mentor_slots(
    mentor_id: str,
    limit: int = Query(default=100, ge=1, le=200),
    _: dict = Depends(require_question_admin_user),
) -> AdminMentorAvailabilitySlotListResponse:
    supabase = get_supabase_admin()
    try:
        _get_mentor_or_404(supabase, mentor_id)
        response = call_supabase(
            lambda: (
                supabase.table("mentor_availability_slots")
                .select("id,mentor_id,starts_at,ends_at,price_cents,status,created_at,updated_at", count="exact")
                .eq("mentor_id", mentor_id)
                .order("starts_at")
                .limit(limit)
                .execute()
            ),
            operation_name="admin mentor slot list",
        )
        rows = response.data or []
        return AdminMentorAvailabilitySlotListResponse(
            items=[AdminMentorAvailabilitySlotItem(**_serialize_admin_slot(row)) for row in rows],
            count=int(response.count or len(rows)),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin mentor slot list failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="预约时段加载失败") from exc


@router.post(
    "/mentors/{mentor_id}/slots",
    response_model=AdminMentorAvailabilitySlotItem,
    status_code=status.HTTP_201_CREATED,
)
def create_admin_mentor_slot(
    mentor_id: str,
    payload: AdminMentorAvailabilitySlotCreateRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminMentorAvailabilitySlotItem:
    if payload.ends_at.timestamp() <= payload.starts_at.timestamp():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="结束时间必须晚于开始时间")
    supabase = get_supabase_admin()
    try:
        _get_mentor_or_404(supabase, mentor_id)
        data = payload.model_dump()
        data.update({
            "mentor_id": mentor_id,
            "starts_at": payload.starts_at.isoformat(),
            "ends_at": payload.ends_at.isoformat(),
        })
        response = call_supabase(
            lambda: supabase.table("mentor_availability_slots").insert(data).execute(),
            operation_name="admin mentor slot create",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="预约时段创建失败")
        row = response.data[0]
        _log_admin_action(
            supabase,
            admin_profile,
            "create_mentor_slot",
            mentor_id,
            {"slot_id": str(row.get("id") or "")},
        )
        return AdminMentorAvailabilitySlotItem(**_serialize_admin_slot(row))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin mentor slot create failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="预约时段创建失败") from exc


@router.patch(
    "/slots/{slot_id}",
    response_model=AdminMentorAvailabilitySlotItem,
)
def update_admin_mentor_slot(
    slot_id: str,
    payload: AdminMentorAvailabilitySlotUpdateRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminMentorAvailabilitySlotItem:
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="没有需要更新的时段字段")
    supabase = get_supabase_admin()
    try:
        current = _get_slot_or_404(supabase, slot_id)
        starts_at = payload.starts_at if "starts_at" in payload.model_fields_set else _parse_database_datetime(current.get("starts_at"))
        ends_at = payload.ends_at if "ends_at" in payload.model_fields_set else _parse_database_datetime(current.get("ends_at"))
        if starts_at is None or ends_at is None or ends_at.timestamp() <= starts_at.timestamp():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="结束时间必须晚于开始时间")
        if "starts_at" in update_data:
            update_data["starts_at"] = starts_at.isoformat()
        if "ends_at" in update_data:
            update_data["ends_at"] = ends_at.isoformat()
        response = call_supabase(
            lambda: (
                supabase.table("mentor_availability_slots")
                .update(update_data)
                .eq("id", slot_id)
                .execute()
            ),
            operation_name="admin mentor slot update",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该预约时段")
        row = response.data[0]
        _log_admin_action(
            supabase,
            admin_profile,
            "update_mentor_slot",
            str(row.get("mentor_id") or ""),
            {"slot_id": slot_id, "fields": sorted(update_data)},
        )
        return AdminMentorAvailabilitySlotItem(**_serialize_admin_slot(row))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin mentor slot update failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="预约时段更新失败") from exc


@router.get("/orders", response_model=AdminMentorConsultationOrderListResponse)
def list_admin_mentor_consultation_orders(
    order_status: str | None = Query(default=None, alias="status", max_length=24),
    payment_status: str | None = Query(default=None, max_length=24),
    report_state: str | None = Query(default=None, max_length=24),
    keyword: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=50, ge=1, le=MENTOR_CONSULTATION_ORDER_ADMIN_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_question_admin_user),
) -> AdminMentorConsultationOrderListResponse:
    """Give operations a direct order queue instead of making reports the only entry point."""

    normalized_order_status = str(order_status or "").strip().lower()
    normalized_payment_status = str(payment_status or "").strip().lower()
    normalized_report_state = str(report_state or "").strip().lower()
    normalized_keyword = str(keyword or "").strip()
    if normalized_order_status and normalized_order_status not in MENTOR_CONSULTATION_ORDER_STATUSES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的订单状态")
    if normalized_payment_status and normalized_payment_status not in MENTOR_CONSULTATION_PAYMENT_STATUSES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的支付状态")
    if normalized_report_state and normalized_report_state not in {"reported", "open"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的投诉筛选条件")

    supabase = get_supabase_admin()
    try:
        report_order_ids: list[str] | None = None
        if normalized_report_state:
            report_query = supabase.table("mentor_consultation_reports").select("order_id")
            if normalized_report_state == "open":
                report_query = report_query.in_("status", list(MENTOR_CONSULTATION_OPEN_REPORT_STATUSES))
            report_response = call_supabase(
                report_query.execute,
                operation_name="admin consultation order report filter",
            )
            report_order_ids = list(dict.fromkeys(
                str(row.get("order_id") or "")
                for row in (report_response.data or [])
                if row.get("order_id")
            ))
            if not report_order_ids:
                return AdminMentorConsultationOrderListResponse(items=[], count=0)

        def fetch_order_page():
            query = supabase.table("mentor_consultation_orders").select(CONSULTATION_ORDER_FIELDS, count="exact")
            if normalized_order_status:
                query = query.eq("order_status", normalized_order_status)
            if normalized_payment_status:
                query = query.eq("payment_status", normalized_payment_status)
            if normalized_keyword:
                query = query.ilike("order_no", f"%{normalized_keyword}%")
            if report_order_ids is not None:
                query = query.in_("id", report_order_ids)
            return call_supabase(
                lambda: query.order("created_at", desc=True).range(offset, offset + limit - 1).execute(),
                operation_name="admin consultation order list",
            )

        response = fetch_order_page()
        rows = response.data or []
        refreshed_rows = [_refresh_pending_accept_status(supabase, row) for row in rows]
        if any(
            str(before.get("order_status") or "") != str(after.get("order_status") or "")
            for before, after in zip(rows, refreshed_rows)
        ):
            # Re-query once so a "待接单" filter never renders an order that was just timed out.
            response = fetch_order_page()
            rows = response.data or []
        else:
            rows = refreshed_rows
        order_ids = [str(row.get("id") or "") for row in rows]
        report_rows = _fetch_consultation_order_reports(supabase, order_ids)
        users = _fetch_application_users(supabase, [str(row.get("applicant_user_id") or "") for row in rows])
        mentors = _fetch_report_mentors(supabase, [str(row.get("mentor_id") or "") for row in rows])
        slots = _fetch_consultation_order_slots(supabase, [str(row.get("slot_id") or "") for row in rows])
        summaries = _summarize_consultation_order_reports(report_rows)
        return AdminMentorConsultationOrderListResponse(
            items=[
                AdminMentorConsultationOrderItem(**_serialize_admin_consultation_order(
                    row,
                    users,
                    mentors,
                    summaries,
                    slots,
                ))
                for row in rows
            ],
            count=int(response.count or len(rows)),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin consultation order list failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="咨询订单列表暂时不可用") from exc


@router.get("/orders/{order_id}", response_model=AdminMentorConsultationOrderDetailResponse)
def get_admin_mentor_consultation_order(
    order_id: str,
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminMentorConsultationOrderDetailResponse:
    supabase = get_supabase_admin()
    try:
        order = _refresh_pending_accept_status(supabase, _get_consultation_order_or_404(supabase, order_id))
        report_rows = _fetch_consultation_order_reports(supabase, [order_id])
        report_user_ids = [
            str(row.get(field) or "")
            for row in report_rows
            for field in ("reporter_user_id", "respondent_user_id", "target_user_id")
        ]
        users = _fetch_application_users(
            supabase,
            [str(order.get("applicant_user_id") or ""), *report_user_ids],
        )
        mentors = _fetch_report_mentors(
            supabase,
            [
                str(order.get("mentor_id") or ""),
                *[str(row.get("target_mentor_id") or "") for row in report_rows],
            ],
        )
        slots = _fetch_consultation_order_slots(supabase, [str(order.get("slot_id") or "")])
        summaries = _summarize_consultation_order_reports(report_rows)
        evidence_counts = _fetch_report_evidence_counts(supabase, [str(row.get("id") or "") for row in report_rows])
        evidence_role_counts = _fetch_report_evidence_role_counts(supabase, [str(row.get("id") or "") for row in report_rows])
        order_map = {order_id: order}
        reports = [
            AdminMentorConsultationReportItem(**_serialize_admin_consultation_report(
                row,
                users,
                mentors,
                order_map,
                evidence_count=evidence_counts.get(str(row.get("id") or ""), 0),
                evidence_role_counts=evidence_role_counts.get(str(row.get("id") or "")),
            ))
            for row in report_rows
        ]
        message_response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_messages")
                .select(CONSULTATION_MESSAGE_FIELDS)
                .eq("order_id", order_id)
                .order("created_at")
                .limit(200)
                .execute()
            ),
            operation_name="admin consultation order message list",
        )
        _log_consultation_order_action(
            supabase,
            admin_profile,
            "view_mentor_consultation_order_detail",
            order_id,
            {"includes": ["reports", "messages", "events"]},
        )
        return AdminMentorConsultationOrderDetailResponse(
            order=AdminMentorConsultationOrderItem(**_serialize_admin_consultation_order(
                order,
                users,
                mentors,
                summaries,
                slots,
            )),
            reports=reports,
            messages=message_response.data or [],
            events=_fetch_consultation_order_events(supabase, order_id),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin consultation order detail failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="咨询订单详情暂时不可用") from exc


@router.post("/orders/{order_id}/intervention", response_model=AdminMentorConsultationOrderItem)
def intervene_admin_mentor_consultation_order(
    order_id: str,
    payload: AdminMentorConsultationOrderInterventionRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminMentorConsultationOrderItem:
    """Send an accountable platform intervention from the all-orders queue."""

    supabase = get_supabase_admin()
    normalized_note = str(payload.admin_note or "").strip()
    if not normalized_note:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="请填写平台处理说明")
    try:
        order = _refresh_pending_accept_status(supabase, _get_consultation_order_or_404(supabase, order_id))
        action = payload.action
        now_iso = datetime.now(timezone.utc).isoformat()
        order_status = str(order.get("order_status") or "")
        refund_amount_cents = 0
        result_order = order
        result_copy = ""
        open_reports = []
        synchronized_report: dict | None = None
        report_synchronized = False
        if action != "notify_participants":
            open_reports = [
                report
                for report in _fetch_consultation_order_reports(supabase, [order_id])
                if str(report.get("status") or "") in MENTOR_CONSULTATION_OPEN_REPORT_STATUSES
            ]
            if len(open_reports) > 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="该订单有多条待处理问题反馈，请在“问题反馈”队列逐条核实并结案后，再从订单页执行退款或结束服务",
                )

        if action in {"refund_full", "refund_partial"}:
            if not _can_initiate_or_retry_refund(order):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该订单当前不处于可退款状态")
            order_price_cents = max(0, int(order.get("price_cents") or 0))
            if action == "refund_partial":
                refund_amount_cents = max(0, int(round(float(payload.refund_amount or 0) * 100)))
                if refund_amount_cents <= 0:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="部分退款金额必须大于 0")
                if refund_amount_cents >= order_price_cents:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="部分退款金额应小于订单总金额；全额退款请使用全额退款动作")
            else:
                refund_amount_cents = order_price_cents
            next_order_status = "refunded" if action == "refund_full" else "completed"
            reference_prefix = "ADMIN" if action == "refund_full" else "ADMIN-PARTIAL"
            next_payment_status = _refund_payment_status_for_order(order)
            response = call_supabase(
                lambda: (
                    supabase.table("mentor_consultation_orders")
                    .update({
                        "order_status": next_order_status,
                        "payment_status": next_payment_status,
                        "ended_at": now_iso,
                        "refund_amount_cents": refund_amount_cents,
                        "refund_reference": f"{reference_prefix}-{str(order.get('order_no') or '')}-{order_id[:8].upper()}",
                    })
                    .eq("id", order_id)
                    .in_("payment_status", ["paid", "failed"])
                    .eq("order_status", order_status)
                    .execute()
                ),
                operation_name="admin consultation order refund",
            )
            if not response.data:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="订单状态已变化，请刷新后重试")
            result_order = response.data[0]
            release_terminal_mentor_booking_slot(supabase, order)
            result_copy = (
                f"平台已按订单金额完成测试退款 ¥{refund_amount_cents / 100:.2f}。"
                if next_payment_status == "refunded" and action == "refund_full"
                else f"平台已提交全额退款 ¥{refund_amount_cents / 100:.2f}，完成后会自动同步。"
                if action == "refund_full"
                else (
                    f"平台已完成测试部分退款 ¥{refund_amount_cents / 100:.2f}，本次服务已结束。"
                    if next_payment_status == "refunded"
                    else f"平台已提交部分退款 ¥{refund_amount_cents / 100:.2f}，本次服务已结束，完成后会自动同步。"
                )
            )
        elif action == "close_service":
            if order_status in MENTOR_CONSULTATION_TERMINAL_ORDER_STATUSES:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该订单已结束，不能重复结束服务")
            response = call_supabase(
                lambda: (
                    supabase.table("mentor_consultation_orders")
                    .update({"order_status": "completed", "ended_at": now_iso})
                    .eq("id", order_id)
                    .eq("order_status", order_status)
                    .execute()
                ),
                operation_name="admin consultation order close service",
            )
            if not response.data:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="订单状态已变化，请刷新后重试")
            result_order = response.data[0]
            release_terminal_mentor_booking_slot(supabase, order)
            result_copy = "平台已介入结束本次咨询服务，聊天记录会继续保留。"
        else:
            result_copy = "平台已向咨询双方发送处理提醒。"

        if open_reports:
            synchronized_report, report_synchronized = _resolve_single_open_report_from_order_intervention(
                supabase,
                report=open_reports[0],
                admin_profile=admin_profile,
                action=action,
                refund_amount_cents=refund_amount_cents,
                admin_note=normalized_note,
                now_iso=now_iso,
            )

        _insert_consultation_admin_system_message(
            supabase,
            order_id,
            f"平台主动介入：{normalized_note}\n{result_copy}",
        )
        _insert_consultation_admin_event(
            supabase,
            order_id,
            admin_profile,
            "admin_order_intervention",
            {
                "action": action,
                "refund_amount_cents": refund_amount_cents,
                "refund_payment_status": str(result_order.get("payment_status") or ""),
                "admin_note": normalized_note,
                "report_id": str(synchronized_report.get("id") or "") if synchronized_report else None,
                "report_synchronized": report_synchronized,
            },
        )
        if action in {"refund_full", "refund_partial"}:
            _insert_consultation_admin_event(
                supabase,
                order_id,
                admin_profile,
                "consultation_refund_completed" if str(result_order.get("payment_status") or "") == "refunded" else "consultation_refund_requested",
                {
                    "refund_amount_cents": refund_amount_cents,
                    "refund_reference": result_order.get("refund_reference"),
                    "reason": "admin_order_intervention",
                },
            )
        _log_consultation_order_action(
            supabase,
            admin_profile,
            "intervene_mentor_consultation_order",
            order_id,
            {
                "action": action,
                "order_status_before": order_status,
                "order_status_after": str(result_order.get("order_status") or ""),
                "refund_amount_cents": refund_amount_cents,
                "report_id": str(synchronized_report.get("id") or "") if synchronized_report else None,
                "report_synchronized": report_synchronized,
            },
        )
        if report_synchronized and synchronized_report:
            _log_consultation_report_action(
                supabase,
                admin_profile,
                "resolve_mentor_consultation_report_from_order_intervention",
                str(synchronized_report.get("id") or ""),
                {
                    "order_id": order_id,
                    "resolution": action,
                    "refund_amount_cents": refund_amount_cents,
                },
            )
        report_rows = _fetch_consultation_order_reports(supabase, [order_id])
        users = _fetch_application_users(supabase, [str(result_order.get("applicant_user_id") or "")])
        mentors = _fetch_report_mentors(supabase, [str(result_order.get("mentor_id") or "")])
        slots = _fetch_consultation_order_slots(supabase, [str(result_order.get("slot_id") or "")])
        return AdminMentorConsultationOrderItem(**_serialize_admin_consultation_order(
            result_order,
            users,
            mentors,
            _summarize_consultation_order_reports(report_rows),
            slots,
        ))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin consultation order intervention failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="咨询订单介入失败") from exc


@router.get("/reports", response_model=AdminMentorConsultationReportListResponse)
def list_admin_mentor_consultation_reports(
    report_status: str | None = Query(default=None, alias="status", max_length=20),
    target_role: str | None = Query(default=None, max_length=20),
    priority: str | None = Query(default=None, max_length=20),
    sla_state: str | None = Query(default=None, max_length=20),
    keyword: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=50, ge=1, le=MENTOR_CONSULTATION_REPORT_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_question_admin_user),
) -> AdminMentorConsultationReportListResponse:
    normalized_status = str(report_status or "").strip().lower()
    normalized_target_role = str(target_role or "").strip().lower()
    normalized_priority = str(priority or "").strip().lower()
    normalized_sla_state = str(sla_state or "").strip().lower()
    normalized_keyword = str(keyword or "").strip()
    valid_statuses = {"pending", "reviewing", "resolved", "dismissed"}
    if normalized_status and normalized_status not in valid_statuses:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的举报处理状态")
    if normalized_target_role and normalized_target_role not in {"applicant", "mentor"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的被举报对象")
    if normalized_priority and normalized_priority not in {"normal", "high", "urgent"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的问题优先级")
    if normalized_sla_state and normalized_sla_state not in {"on_track", "due_soon", "overdue", "escalated"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的处理时限筛选条件")

    supabase = get_supabase_admin()
    try:
        query = supabase.table("mentor_consultation_reports").select(MENTOR_CONSULTATION_REPORT_FIELDS, count="exact")
        if normalized_status:
            query = query.eq("status", normalized_status)
        if normalized_target_role:
            query = query.eq("target_role", normalized_target_role)
        if normalized_keyword:
            query = query.or_(
                f"issue_type.ilike.%{normalized_keyword}%,content.ilike.%{normalized_keyword}%,respondent_content.ilike.%{normalized_keyword}%"
            )
        query = _apply_consultation_case_sla_filters(
            query,
            priority=normalized_priority,
            sla_state=normalized_sla_state,
        )
        response = call_supabase(
            lambda: query.order("escalation_level", desc=True).order("first_response_due_at").order("created_at", desc=True).range(offset, offset + limit - 1).execute(),
            operation_name="admin consultation report list",
        )
        rows = response.data or []
        users = _fetch_application_users(
            supabase,
            [
                str(row.get("reporter_user_id") or "")
                for row in rows
            ] + [
                str(row.get("target_user_id") or "")
                for row in rows
            ] + [
                str(row.get("respondent_user_id") or "")
                for row in rows
            ],
        )
        mentors = _fetch_report_mentors(supabase, [str(row.get("target_mentor_id") or "") for row in rows])
        orders = _fetch_report_orders(supabase, [str(row.get("order_id") or "") for row in rows])
        evidence_counts = _fetch_report_evidence_counts(supabase, [str(row.get("id") or "") for row in rows])
        evidence_role_counts = _fetch_report_evidence_role_counts(supabase, [str(row.get("id") or "") for row in rows])
        return AdminMentorConsultationReportListResponse(
            items=[
                AdminMentorConsultationReportItem(**_serialize_admin_consultation_report(
                    row,
                    users,
                    mentors,
                    orders,
                    evidence_count=evidence_counts.get(str(row.get("id") or ""), 0),
                    evidence_role_counts=evidence_role_counts.get(str(row.get("id") or "")),
                ))
                for row in rows
            ],
            count=int(response.count or len(rows)),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin consultation report list failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="举报列表暂时不可用") from exc


@router.get("/reports/{report_id}", response_model=AdminMentorConsultationReportDetailResponse)
def get_admin_mentor_consultation_report(
    report_id: str,
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminMentorConsultationReportDetailResponse:
    supabase = get_supabase_admin()
    try:
        report = _get_consultation_report_or_404(supabase, report_id)
        users = _fetch_application_users(
            supabase,
            [
                str(report.get("reporter_user_id") or ""),
                str(report.get("respondent_user_id") or ""),
                str(report.get("target_user_id") or ""),
            ],
        )
        mentors = _fetch_report_mentors(supabase, [str(report.get("target_mentor_id") or "")])
        orders = _fetch_report_orders(supabase, [str(report.get("order_id") or "")])
        reviews = _fetch_consultation_order_reviews(supabase, [str(report.get("order_id") or "")])
        evidence_response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_report_evidence")
                .select("id,file_url,file_name,mime_type,submitter_role,created_at")
                .eq("report_id", report_id)
                .order("created_at")
                .limit(6)
                .execute()
            ),
            operation_name="admin consultation report evidence list",
        )
        evidence = [
            AdminMentorConsultationReportEvidenceItem(**_report_evidence_admin_item(supabase, row))
            for row in (evidence_response.data or [])
        ]
        message_response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_messages")
                .select(CONSULTATION_MESSAGE_FIELDS)
                .eq("order_id", str(report.get("order_id") or ""))
                .order("created_at")
                .limit(200)
                .execute()
            ),
            operation_name="admin consultation report message list",
        )
        item = AdminMentorConsultationReportItem(**_serialize_admin_consultation_report(
            report,
            users,
            mentors,
            orders,
            evidence_count=len(evidence),
            evidence_role_counts=_fetch_report_evidence_role_counts(supabase, [report_id]).get(report_id),
        ))
        _log_consultation_report_action(
            supabase,
            admin_profile,
            "view_mentor_consultation_report_detail",
            report_id,
            {
                "order_id": str(report.get("order_id") or ""),
                "includes": ["evidence", "messages", "events", "review"],
            },
        )
        return AdminMentorConsultationReportDetailResponse(
            report=item,
            evidence=evidence,
            review=(
                AdminMentorConsultationReviewItem(**_serialize_admin_consultation_review(
                    reviews[str(report.get("order_id") or "")]
                ))
                if str(report.get("order_id") or "") in reviews
                else None
            ),
            order=orders.get(str(report.get("order_id") or ""), {}),
            messages=message_response.data or [],
            events=_fetch_consultation_order_events(supabase, str(report.get("order_id") or "")),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin consultation report detail failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="举报详情暂时不可用") from exc


@router.patch("/reports/{report_id}/status", response_model=AdminMentorConsultationReportItem)
def update_admin_mentor_consultation_report_status(
    report_id: str,
    payload: AdminMentorConsultationReportStatusUpdateRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminMentorConsultationReportItem:
    supabase = get_supabase_admin()
    try:
        report = _get_consultation_report_or_404(supabase, report_id)
        normalized_note = str(payload.admin_note or "").strip() or None
        terminal = payload.status in {"resolved", "dismissed"}
        resolution = payload.resolution
        if terminal and not normalized_note:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="结案时请填写处理结论")
        if resolution != "none" and payload.status != "resolved":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="执行订单裁决时请将举报标记为已处理")

        now_iso = datetime.now(timezone.utc).isoformat()
        current_priority = normalize_case_priority(report.get("priority"))
        next_priority = normalize_case_priority(payload.priority, default=current_priority)
        priority_escalated = case_priority_rank(next_priority) > case_priority_rank(current_priority)
        current_escalation_level = max(0, int(report.get("escalation_level") or 0))
        next_escalation_level = current_escalation_level + 1 if priority_escalated else current_escalation_level
        first_response_recorded = not report.get("first_response_at") and payload.status != "pending"
        first_response_at = report.get("first_response_at") or (now_iso if first_response_recorded else None)
        refund_amount_cents = 0
        order_id = str(report.get("order_id") or "")
        current_orders = _fetch_report_orders(supabase, [order_id])
        current_order = current_orders.get(order_id, {})
        order_status = str(current_order.get("order_status") or "")
        review_change: dict | None = None
        review_target_published: bool | None = None
        refund_payment_status: str | None = None

        if resolution in {"refund_full", "refund_partial"}:
            if not _can_initiate_or_retry_refund(current_order):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该订单当前不处于可退款状态")
            order_price_cents = max(0, int(current_order.get("price_cents") or 0))
            if resolution == "refund_partial":
                refund_amount_cents = max(0, int(round(float(payload.refund_amount or 0) * 100)))
                if refund_amount_cents <= 0:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="部分退款金额必须大于 0")
                if refund_amount_cents >= order_price_cents:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="部分退款金额应小于订单总金额；全额退款请使用全额退款裁决")
            else:
                refund_amount_cents = order_price_cents
            next_order_status = "refunded" if resolution == "refund_full" else "completed"
            reference_prefix = "CASE" if resolution == "refund_full" else "CASE-PARTIAL"
            refund_payment_status = _refund_payment_status_for_order(current_order)
            order_response = call_supabase(
                lambda: (
                    supabase.table("mentor_consultation_orders")
                    .update({
                        "order_status": next_order_status,
                        "payment_status": refund_payment_status,
                        "ended_at": now_iso,
                        "refund_amount_cents": refund_amount_cents,
                        "refund_reference": f"{reference_prefix}-{str(current_order.get('order_no') or '')}-{report_id[:8].upper()}",
                    })
                    .eq("id", order_id)
                    .in_("payment_status", ["paid", "failed"])
                    .eq("order_status", order_status)
                    .execute()
                ),
                operation_name="admin consultation report refund",
            )
            if not order_response.data:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="订单状态已变化，请刷新后重试")
            release_terminal_mentor_booking_slot(supabase, current_order)
        elif resolution == "close_service":
            if order_status in {"completed", "refunded", "cancelled", "rejected", "timeout"}:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该订单已结束，不能重复结束服务")
            order_response = call_supabase(
                lambda: (
                    supabase.table("mentor_consultation_orders")
                    .update({"order_status": "completed", "ended_at": now_iso})
                    .eq("id", order_id)
                    .eq("order_status", order_status)
                    .execute()
                ),
                operation_name="admin consultation report close service",
            )
            if not order_response.data:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="订单状态已变化，请刷新后重试")
            release_terminal_mentor_booking_slot(supabase, current_order)
        elif resolution in {"hide_review", "restore_review"}:
            if (
                str(report.get("reporter_role") or "") != "mentor"
                or str(report.get("target_role") or "") != "applicant"
                or str(report.get("issue_type") or "") != MENTOR_REVIEW_DISPUTE_ISSUE_TYPE
            ):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="评价处置仅适用于认证前辈提交的“恶意评价或失实反馈”",
                )
            current_review = _fetch_consultation_order_reviews(supabase, [order_id]).get(order_id)
            if not current_review:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该咨询订单尚无可处置的服务评价")
            review_target_published = resolution == "restore_review"
            if bool(current_review.get("is_published")) == review_target_published:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="关联评价状态已变化，请刷新后重试")
            review_response = call_supabase(
                lambda: (
                    supabase.table("mentor_reviews")
                    .update({"is_published": review_target_published})
                    .eq("id", str(current_review.get("id") or ""))
                    .eq("is_published", not review_target_published)
                    .execute()
                ),
                operation_name="admin consultation review moderation",
            )
            if not review_response.data:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="关联评价状态已变化，请刷新后重试")
            review_change = review_response.data[0]
        elif resolution == "continue_service":
            if order_status in {"completed", "refunded", "cancelled", "rejected", "timeout"}:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该订单已结束，不能再建议继续服务")

        update_data = {
            "status": payload.status,
            "resolution": resolution,
            "refund_amount_cents": refund_amount_cents,
            "admin_note": normalized_note,
            "handled_by": admin_profile.get("id") if payload.status != "pending" else None,
            "handled_at": now_iso if terminal else None,
            "first_response_at": first_response_at,
            "priority": next_priority,
            "escalation_level": next_escalation_level,
            "escalated_at": now_iso if priority_escalated else report.get("escalated_at"),
        }
        response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_reports")
                .update(update_data)
                .eq("id", report_id)
                .execute()
            ),
            operation_name="admin consultation report status update",
        )
        if not response.data:
            if review_change and review_target_published is not None:
                try:
                    call_supabase(
                        lambda: (
                            supabase.table("mentor_reviews")
                            .update({"is_published": not review_target_published})
                            .eq("id", str(review_change.get("id") or ""))
                            .eq("is_published", review_target_published)
                            .execute()
                        ),
                        operation_name="admin consultation review moderation rollback",
                    )
                except Exception as rollback_exc:
                    logger.warning(
                        "Consultation review moderation rollback skipped (error_type=%s)",
                        type(rollback_exc).__name__,
                    )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该举报记录")
        row = response.data[0]
        if payload.status != "pending":
            is_reviewing = payload.status == "reviewing"
            create_user_notification(
                supabase,
                recipient_user_id=str(row.get("reporter_user_id") or ""),
                category="consultation",
                notification_type="mentor_report_status",
                title="你的咨询问题反馈已受理" if is_reviewing else "你的咨询问题反馈处理结果已更新",
                summary="平台正在核实本次咨询情况。" if is_reviewing else "平台已更新本次问题反馈的处理结论。",
                content=normalized_note or (
                    "平台正在结合订单、聊天和双方材料进行核实，请留意后续处理进度。"
                    if is_reviewing
                    else "平台已完成核查，处理结果已同步到平台处理进度。"
                ),
                related_type="mentor_consultation_report",
                related_id=str(row.get("id") or report_id),
                route_path="/pages-sub-consultation/consultation/mentor-support",
            )
        if terminal:
            resolution_copy = {
                "refund_full": (
                    f"平台已按本次订单金额完成测试退款 ¥{refund_amount_cents / 100:.2f}。"
                    if refund_payment_status == "refunded"
                    else f"平台已提交全额退款 ¥{refund_amount_cents / 100:.2f}，完成后会自动同步。"
                ),
                "refund_partial": (
                    f"平台已按裁决完成测试部分退款 ¥{refund_amount_cents / 100:.2f}，本次服务已结束。"
                    if refund_payment_status == "refunded"
                    else f"平台已按裁决提交部分退款 ¥{refund_amount_cents / 100:.2f}，本次服务已结束，完成后会自动同步。"
                ),
                "close_service": "平台已介入结束本次咨询服务，聊天记录已保留。",
                "continue_service": "平台核实后建议双方继续在站内完成咨询。",
                "warn_participant": "平台已对相关参与方作出提醒并保留处理记录。",
                "hide_review": "平台已暂时下架关联服务评价，后续可按复核结论恢复公开。",
                "restore_review": "平台已恢复关联服务评价的公开展示。",
            }.get(resolution, "")
            message_content = f"平台已更新本次举报处理结果：{normalized_note}"
            if resolution_copy:
                message_content = f"{message_content}\n{resolution_copy}"
            _insert_consultation_admin_system_message(
                supabase,
                order_id,
                message_content,
            )
            _insert_consultation_admin_event(
                supabase,
                order_id,
                admin_profile,
                "consultation_report_resolved",
                {
                    "report_id": report_id,
                    "status": payload.status,
                    "resolution": resolution,
                    "refund_amount_cents": refund_amount_cents,
                    "refund_payment_status": refund_payment_status,
                },
            )
            if resolution in {"refund_full", "refund_partial"}:
                refreshed_orders = _fetch_report_orders(supabase, [order_id])
                refunded_order = refreshed_orders.get(order_id, {})
                _insert_consultation_admin_event(
                    supabase,
                    order_id,
                    admin_profile,
                    "consultation_refund_completed" if str(refunded_order.get("payment_status") or "") == "refunded" else "consultation_refund_requested",
                    {
                        "report_id": report_id,
                        "refund_amount_cents": refund_amount_cents,
                        "refund_reference": refunded_order.get("refund_reference"),
                        "reason": "consultation_report_resolution",
                    },
                )
            if review_change:
                _insert_consultation_admin_event(
                    supabase,
                    order_id,
                    admin_profile,
                    "consultation_review_restored" if review_target_published else "consultation_review_hidden",
                    {
                        "report_id": report_id,
                        "review_id": str(review_change.get("id") or ""),
                        "is_published": bool(review_target_published),
                    },
                )
        elif first_response_recorded:
            _insert_consultation_admin_system_message(
                supabase,
                order_id,
                "平台已受理本次咨询问题反馈，正在结合订单、聊天和双方材料进行核实。",
            )
            _insert_consultation_admin_event(
                supabase,
                order_id,
                admin_profile,
                "consultation_report_acknowledged",
                {"report_id": report_id, "status": payload.status},
            )
        if priority_escalated:
            _insert_consultation_admin_event(
                supabase,
                order_id,
                admin_profile,
                "consultation_report_priority_escalated",
                {
                    "report_id": report_id,
                    "previous_priority": current_priority,
                    "priority": next_priority,
                    "escalation_level": next_escalation_level,
                },
            )
            if not terminal:
                _insert_consultation_admin_system_message(
                    supabase,
                    order_id,
                    "平台已将本次咨询问题反馈调整为优先处理，正在加快核实进度。",
                )
        users = _fetch_application_users(
            supabase,
            [
                str(row.get("reporter_user_id") or ""),
                str(row.get("respondent_user_id") or ""),
                str(row.get("target_user_id") or ""),
            ],
        )
        mentors = _fetch_report_mentors(supabase, [str(row.get("target_mentor_id") or "")])
        orders = _fetch_report_orders(supabase, [str(row.get("order_id") or "")])
        evidence_counts = _fetch_report_evidence_counts(supabase, [str(row.get("id") or "")])
        evidence_role_counts = _fetch_report_evidence_role_counts(supabase, [str(row.get("id") or "")])
        _log_consultation_report_action(
            supabase,
            admin_profile,
            "update_mentor_consultation_report_status",
            report_id,
            {
                "status": payload.status,
                "resolution": resolution,
                "refund_amount_cents": refund_amount_cents,
                "priority": next_priority,
                "first_response_recorded": first_response_recorded,
            },
        )
        if review_change:
            _log_consultation_review_action(
                supabase,
                admin_profile,
                "restore_mentor_consultation_review" if review_target_published else "hide_mentor_consultation_review",
                str(review_change.get("id") or ""),
                {"order_id": order_id, "report_id": report_id, "is_published": bool(review_target_published)},
            )
        return AdminMentorConsultationReportItem(**_serialize_admin_consultation_report(
            row,
            users,
            mentors,
            orders,
            evidence_count=evidence_counts.get(str(row.get("id") or ""), 0),
            evidence_role_counts=evidence_role_counts.get(str(row.get("id") or "")),
        ))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin consultation report status update failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="举报状态更新失败") from exc


@router.get("/report-appeals", response_model=AdminMentorConsultationReportAppealListResponse)
def list_admin_mentor_consultation_report_appeals(
    appeal_status: str | None = Query(default=None, alias="status", max_length=20),
    priority: str | None = Query(default=None, max_length=20),
    sla_state: str | None = Query(default=None, max_length=20),
    keyword: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=50, ge=1, le=MENTOR_CONSULTATION_REPORT_APPEAL_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_question_admin_user),
) -> AdminMentorConsultationReportAppealListResponse:
    normalized_status = str(appeal_status or "").strip().lower()
    normalized_priority = str(priority or "").strip().lower()
    normalized_sla_state = str(sla_state or "").strip().lower()
    normalized_keyword = str(keyword or "").strip()
    if normalized_status and normalized_status not in {"pending", "reviewing", "resolved", "dismissed"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的复核处理状态")
    if normalized_priority and normalized_priority not in {"normal", "high", "urgent"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的复核优先级")
    if normalized_sla_state and normalized_sla_state not in {"on_track", "due_soon", "overdue", "escalated"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的复核处理时限筛选条件")

    supabase = get_supabase_admin()
    try:
        query = supabase.table("mentor_consultation_report_appeals").select(MENTOR_CONSULTATION_REPORT_APPEAL_FIELDS, count="exact")
        if normalized_status:
            query = query.eq("status", normalized_status)
        if normalized_keyword:
            query = query.ilike("content", f"%{normalized_keyword}%")
        query = _apply_consultation_case_sla_filters(
            query,
            priority=normalized_priority,
            sla_state=normalized_sla_state,
        )
        response = call_supabase(
            lambda: query.order("escalation_level", desc=True).order("first_response_due_at").order("created_at", desc=True).range(offset, offset + limit - 1).execute(),
            operation_name="admin consultation report appeal list",
        )
        rows = response.data or []
        report_ids = [str(row.get("report_id") or "") for row in rows if row.get("report_id")]
        report_response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_reports")
                .select(MENTOR_CONSULTATION_REPORT_FIELDS)
                .in_("id", report_ids)
                .execute()
            ),
            operation_name="admin consultation report appeal report lookup",
        ) if report_ids else None
        reports = {str(row.get("id") or ""): row for row in ((report_response.data if report_response else []) or [])}
        users = _fetch_application_users(
            supabase,
            [str(row.get("appellant_user_id") or "") for row in rows]
            + [str(report.get("reporter_user_id") or "") for report in reports.values()]
            + [str(report.get("respondent_user_id") or "") for report in reports.values()]
            + [str(report.get("target_user_id") or "") for report in reports.values()],
        )
        mentors = _fetch_report_mentors(supabase, [str(report.get("target_mentor_id") or "") for report in reports.values()])
        orders = _fetch_report_orders(supabase, [str(report.get("order_id") or "") for report in reports.values()])
        evidence_counts = _fetch_report_appeal_evidence_counts(supabase, [str(row.get("id") or "") for row in rows])
        return AdminMentorConsultationReportAppealListResponse(
            items=[
                AdminMentorConsultationReportAppealItem(**_serialize_admin_consultation_report_appeal(
                    row,
                    reports,
                    users,
                    mentors,
                    orders,
                    evidence_count=evidence_counts.get(str(row.get("id") or ""), 0),
                ))
                for row in rows
            ],
            count=int(response.count or len(rows)),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin consultation report appeal list failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="复核申请列表暂时不可用") from exc


@router.get("/report-appeals/{appeal_id}", response_model=AdminMentorConsultationReportAppealDetailResponse)
def get_admin_mentor_consultation_report_appeal(
    appeal_id: str,
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminMentorConsultationReportAppealDetailResponse:
    supabase = get_supabase_admin()
    try:
        appeal = _get_consultation_report_appeal_or_404(supabase, appeal_id)
        report = _get_consultation_report_or_404(supabase, str(appeal.get("report_id") or ""))
        users = _fetch_application_users(
            supabase,
            [
                str(appeal.get("appellant_user_id") or ""),
                str(report.get("reporter_user_id") or ""),
                str(report.get("respondent_user_id") or ""),
                str(report.get("target_user_id") or ""),
            ],
        )
        mentors = _fetch_report_mentors(supabase, [str(report.get("target_mentor_id") or "")])
        orders = _fetch_report_orders(supabase, [str(report.get("order_id") or "")])
        appeal_evidence_response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_report_appeal_evidence")
                .select("id,file_url,file_name,mime_type,created_at")
                .eq("appeal_id", appeal_id)
                .order("created_at")
                .limit(3)
                .execute()
            ),
            operation_name="admin consultation report appeal evidence list",
        )
        report_evidence_response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_report_evidence")
                .select("id,file_url,file_name,mime_type,submitter_role,created_at")
                .eq("report_id", str(report.get("id") or ""))
                .order("created_at")
                .limit(6)
                .execute()
            ),
            operation_name="admin consultation report appeal source evidence list",
        )
        message_response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_messages")
                .select(CONSULTATION_MESSAGE_FIELDS)
                .eq("order_id", str(report.get("order_id") or ""))
                .order("created_at")
                .limit(200)
                .execute()
            ),
            operation_name="admin consultation report appeal message list",
        )
        report_id = str(report.get("id") or "")
        item = AdminMentorConsultationReportAppealItem(**_serialize_admin_consultation_report_appeal(
            appeal,
            {report_id: report},
            users,
            mentors,
            orders,
            evidence_count=len(appeal_evidence_response.data or []),
        ))
        report_item = AdminMentorConsultationReportItem(**_serialize_admin_consultation_report(
            report,
            users,
            mentors,
            orders,
            evidence_count=len(report_evidence_response.data or []),
            evidence_role_counts=_fetch_report_evidence_role_counts(supabase, [report_id]).get(report_id),
        ))
        _log_consultation_report_appeal_action(
            supabase,
            admin_profile,
            "view_mentor_consultation_report_appeal_detail",
            appeal_id,
            {
                "report_id": report_id,
                "order_id": str(report.get("order_id") or ""),
                "includes": ["appeal_evidence", "report_evidence", "messages", "events"],
            },
        )
        return AdminMentorConsultationReportAppealDetailResponse(
            appeal=item,
            evidence=[
                AdminMentorConsultationReportAppealEvidenceItem(**_report_appeal_evidence_admin_item(supabase, row))
                for row in (appeal_evidence_response.data or [])
            ],
            report=report_item,
            report_evidence=[
                AdminMentorConsultationReportEvidenceItem(**_report_evidence_admin_item(supabase, row))
                for row in (report_evidence_response.data or [])
            ],
            order=orders.get(str(report.get("order_id") or ""), {}),
            messages=message_response.data or [],
            events=_fetch_consultation_order_events(supabase, str(report.get("order_id") or "")),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin consultation report appeal detail failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="复核申请详情暂时不可用") from exc


@router.patch("/report-appeals/{appeal_id}/status", response_model=AdminMentorConsultationReportAppealItem)
def update_admin_mentor_consultation_report_appeal_status(
    appeal_id: str,
    payload: AdminMentorConsultationReportAppealStatusUpdateRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminMentorConsultationReportAppealItem:
    normalized_note = str(payload.admin_note or "").strip() or None
    terminal = payload.status in {"resolved", "dismissed"}
    if terminal and not normalized_note:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="结案时请填写复核处理说明")
    if payload.decision != "none" and not terminal:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="执行复核结论时请同步将复核申请结案")
    if payload.decision == "reopen" and payload.status != "resolved":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="重新开启原案时请将复核申请标记为已处理")
    if payload.decision == "uphold" and payload.status != "dismissed":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="维持原结论时请将复核申请标记为已驳回")

    supabase = get_supabase_admin()
    try:
        appeal = _get_consultation_report_appeal_or_404(supabase, appeal_id)
        report_id = str(appeal.get("report_id") or "")
        report = _get_consultation_report_or_404(supabase, report_id)
        if payload.decision == "reopen" and str(report.get("status") or "pending") not in {"resolved", "dismissed"}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="原问题反馈已在处理中，请勿重复重新开启")
        now_iso = datetime.now(timezone.utc).isoformat()
        current_priority = normalize_case_priority(appeal.get("priority"))
        next_priority = normalize_case_priority(payload.priority, default=current_priority)
        priority_escalated = case_priority_rank(next_priority) > case_priority_rank(current_priority)
        current_escalation_level = max(0, int(appeal.get("escalation_level") or 0))
        next_escalation_level = current_escalation_level + 1 if priority_escalated else current_escalation_level
        first_response_recorded = not appeal.get("first_response_at") and payload.status != "pending"
        first_response_at = appeal.get("first_response_at") or (now_iso if first_response_recorded else None)
        order_id = str(report.get("order_id") or "")
        report_after = report
        report_reopened = False
        if payload.decision == "reopen":
            report_response = call_supabase(
                lambda: (
                    supabase.table("mentor_consultation_reports")
                    .update({
                        "status": "reviewing",
                        "resolution": "none",
                        "admin_note": "平台已受理复核申请，原处理结果正在重新核实。",
                        "handled_by": admin_profile.get("id"),
                        "handled_at": None,
                    })
                    .eq("id", report_id)
                    .in_("status", ["resolved", "dismissed"])
                    .execute()
                ),
                operation_name="admin consultation report reopen after appeal",
            )
            if not report_response.data:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="原问题反馈状态已变化，请刷新后重试")
            report_after = report_response.data[0]
            report_reopened = True

        def rollback_reopened_report() -> None:
            if not report_reopened:
                return
            try:
                call_supabase(
                    lambda: (
                        supabase.table("mentor_consultation_reports")
                        .update({
                            "status": report.get("status"),
                            "resolution": report.get("resolution"),
                            "admin_note": report.get("admin_note"),
                            "handled_by": report.get("handled_by"),
                            "handled_at": report.get("handled_at"),
                        })
                        .eq("id", report_id)
                        .eq("status", "reviewing")
                        .execute()
                    ),
                    operation_name="admin consultation report reopen rollback",
                )
            except Exception as rollback_exc:
                logger.warning("Consultation report reopen rollback skipped (error_type=%s)", type(rollback_exc).__name__)

        try:
            response = call_supabase(
                lambda: (
                    supabase.table("mentor_consultation_report_appeals")
                    .update({
                        "status": payload.status,
                        "decision": payload.decision,
                        "admin_note": normalized_note,
                        "handled_by": admin_profile.get("id") if payload.status != "pending" else None,
                        "handled_at": now_iso if terminal else None,
                        "first_response_at": first_response_at,
                        "priority": next_priority,
                        "escalation_level": next_escalation_level,
                        "escalated_at": now_iso if priority_escalated else appeal.get("escalated_at"),
                    })
                    .eq("id", appeal_id)
                    .execute()
                ),
                operation_name="admin consultation report appeal status update",
            )
        except Exception:
            rollback_reopened_report()
            raise
        if not response.data:
            rollback_reopened_report()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该复核申请")
        updated = response.data[0]
        if payload.status != "pending":
            is_reviewing = payload.status == "reviewing"
            create_user_notification(
                supabase,
                recipient_user_id=str(updated.get("appellant_user_id") or ""),
                category="consultation",
                notification_type="mentor_report_appeal_status",
                title="你的咨询复核申请已受理" if is_reviewing else "你的咨询复核结果已更新",
                summary="平台正在复核你提交的申请。" if is_reviewing else "平台已更新本次复核申请的处理结论。",
                content=normalized_note or (
                    "平台正在结合订单、聊天和双方材料进行复核，请留意后续处理进度。"
                    if is_reviewing
                    else "平台已完成复核，处理结果已同步到平台处理进度。"
                ),
                related_type="mentor_consultation_report_appeal",
                related_id=str(updated.get("id") or appeal_id),
                route_path="/pages-sub-consultation/consultation/mentor-support",
            )
        if payload.decision == "reopen":
            _insert_consultation_admin_system_message(
                supabase,
                order_id,
                f"平台已受理本次复核申请：{normalized_note}\n原问题反馈已重新进入处理中，平台会再次核对双方材料。",
            )
            _insert_consultation_admin_event(
                supabase,
                order_id,
                admin_profile,
                "consultation_report_reopened_after_appeal",
                {
                    "report_id": report_id,
                    "appeal_id": appeal_id,
                    "previous_status": str(report.get("status") or ""),
                    "previous_resolution": str(report.get("resolution") or "none"),
                    "previous_admin_note": report.get("admin_note") or None,
                },
            )
        elif payload.status != "pending":
            outcome = "原处理结论维持不变。" if payload.decision == "uphold" else ("平台正在复核本次申请。" if payload.status == "reviewing" else "平台已更新本次复核处理进度。")
            _insert_consultation_admin_system_message(
                supabase,
                order_id,
                f"平台已更新本次复核申请：{normalized_note}\n{outcome}",
            )
            _insert_consultation_admin_event(
                supabase,
                order_id,
                admin_profile,
                "consultation_report_appeal_reviewing" if payload.status == "reviewing" else "consultation_report_appeal_resolved",
                {"report_id": report_id, "appeal_id": appeal_id, "status": payload.status, "decision": payload.decision},
            )
        if priority_escalated:
            _insert_consultation_admin_event(
                supabase,
                order_id,
                admin_profile,
                "consultation_report_appeal_priority_escalated",
                {
                    "report_id": report_id,
                    "appeal_id": appeal_id,
                    "previous_priority": current_priority,
                    "priority": next_priority,
                    "escalation_level": next_escalation_level,
                },
            )
            if not terminal:
                _insert_consultation_admin_system_message(
                    supabase,
                    order_id,
                    "平台已将本次复核申请调整为优先处理，正在加快核实进度。",
                )

        users = _fetch_application_users(
            supabase,
            [
                str(updated.get("appellant_user_id") or ""),
                str(report_after.get("reporter_user_id") or ""),
                str(report_after.get("respondent_user_id") or ""),
                str(report_after.get("target_user_id") or ""),
            ],
        )
        mentors = _fetch_report_mentors(supabase, [str(report_after.get("target_mentor_id") or "")])
        orders = _fetch_report_orders(supabase, [str(report_after.get("order_id") or "")])
        evidence_counts = _fetch_report_appeal_evidence_counts(supabase, [appeal_id])
        _log_consultation_report_appeal_action(
            supabase,
            admin_profile,
            "update_mentor_consultation_report_appeal_status",
            appeal_id,
            {
                "report_id": report_id,
                "status": payload.status,
                "decision": payload.decision,
                "priority": next_priority,
                "first_response_recorded": first_response_recorded,
            },
        )
        return AdminMentorConsultationReportAppealItem(**_serialize_admin_consultation_report_appeal(
            updated,
            {report_id: report_after},
            users,
            mentors,
            orders,
            evidence_count=evidence_counts.get(appeal_id, 0),
        ))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin consultation report appeal status update failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="复核申请处理失败") from exc
