from __future__ import annotations

import hashlib
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile, status

from app.config import get_settings
from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.mentor_consultation import (
    MentorConsultationDecisionRequest,
    MentorConsultationMessageCreateRequest,
    MentorConsultationMessageItem,
    MentorConsultationMessageListResponse,
    MentorConsultationOrderCreateRequest,
    MentorConsultationOrderItem,
    MentorConsultationOrderListResponse,
    MentorConsultationPaymentCapabilityResponse,
    MentorConsultationPaymentIntentResponse,
    MentorConsultationPaymentWebhookRequest,
    MentorConsultationPaymentWebhookResponse,
    MentorConsultationReportCreateRequest,
    MentorConsultationReportCreateResponse,
    MentorConsultationReportAppealCreateRequest,
    MentorConsultationReportAppealEvidenceUploadResponse,
    MentorConsultationReportAppealItem,
    MentorConsultationReportAppealListResponse,
    MentorConsultationReportEvidenceUploadResponse,
    MentorConsultationReportListResponse,
    MentorConsultationReportResponseRequest,
    MentorConsultationReviewCreateRequest,
    MentorConsultationReviewCreateResponse,
    MentorAvailabilitySlotItem,
    MentorFavoriteItem,
    MentorFavoriteListResponse,
    MentorFavoriteToggleResponse,
    MentorOwnerAvailabilitySlotCreateRequest,
    MentorOwnerAvailabilitySlotListResponse,
    MentorOwnerAvailabilitySlotStatusUpdateRequest,
    MentorOwnerAvailabilityUpdateRequest,
    MentorOwnerProfileResponse,
    MentorProfileChangeRequestCreateRequest,
    MentorProfileChangeRequestItem,
    MentorProfileChangeRequestStatusResponse,
    MentorPublicDetailResponse,
    MentorPublicListResponse,
    MentorVerificationApplicationCreateRequest,
    MentorVerificationApplicationItem,
    MentorVerificationApplicationStatusResponse,
    MentorVerificationDocumentUploadResponse,
)
from app.services.mentor_consultation import (
    CONSULTATION_MESSAGE_FIELDS,
    CONSULTATION_ORDER_FIELDS,
    PUBLIC_PROFILE_FIELDS,
    fetch_mentor_aggregates,
    fetch_mentor_skills,
    normalize_skills,
    serialize_mentor_message,
    serialize_mentor_order,
    serialize_mentor_public,
    serialize_mentor_review,
    serialize_mentor_slot,
)
from app.services.mentor_consultation_lifecycle import (
    refresh_expired_mentor_consultation_order,
    release_terminal_mentor_booking_slot,
)
from app.services.mentor_consultation_sla import (
    first_response_deadline,
    initial_report_priority,
    serialize_case_sla,
)
from app.services.supabase_resilience import call_supabase
from app.services.user_notifications import create_user_notification
from app.services.wallet_ledger import (
    record_consultation_income_pending,
    record_consultation_payment,
    record_consultation_refund,
)
from app.utils.cursor_pagination import (
    build_keyset_filter,
    cursor_datetime,
    cursor_uuid,
    decode_page_cursor,
    encode_page_cursor,
)


router = APIRouter(prefix="/mentor-consultation", tags=["前辈咨询"])
logger = logging.getLogger(__name__)

PUBLIC_MENTOR_SORTS = {"recommended", "consult_count", "rating", "price"}
PUBLIC_MENTOR_AVAILABILITIES = {"all", "online", "bookable"}
PUBLIC_MENTOR_EXAM_TYPES = {"Z001", "Z002", "application"}
PUBLIC_MENTOR_MAX_LIMIT = 100
ORDER_MENTOR_FIELDS = (
    "id,owner_user_id,online_status,accepts_booking,price_cents,"
    "consultation_window_minutes,is_published,verification_status"
)
ORDER_MENTOR_RESPONSE_WINDOW_MINUTES = 10
ORDER_LIST_MAX_LIMIT = 100
MENTOR_SLOT_MAX_LIMIT = 100
MENTOR_SLOT_WINDOW_MINUTES = 60
MENTOR_SLOT_DATE_WINDOW_DAYS = 3
MENTOR_SLOT_FIRST_HOUR = 9
MENTOR_SLOT_LAST_HOUR = 23
MENTOR_SLOT_LOCAL_TIMEZONE = timezone(timedelta(hours=8), name="Asia/Shanghai")
CONSULTATION_ORDER_STATUSES = {
    "draft", "pending_payment", "pending_accept", "accepted", "in_progress",
    "completed", "rejected", "timeout", "refunded", "cancelled", "booked",
}
MENTOR_VERIFICATION_DOCUMENT_BUCKET = "mentor-verification-documents"
MAX_MENTOR_VERIFICATION_DOCUMENT_BYTES = 8 * 1024 * 1024
MENTOR_VERIFICATION_DOCUMENT_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
MENTOR_CONSULTATION_REPORT_EVIDENCE_BUCKET = "mentor-consultation-report-evidence"
MENTOR_CONSULTATION_REPORT_APPEAL_EVIDENCE_BUCKET = "mentor-consultation-report-appeal-evidence"
MAX_MENTOR_CONSULTATION_REPORT_EVIDENCE_BYTES = 8 * 1024 * 1024
MENTOR_CONSULTATION_REPORT_EVIDENCE_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
MENTOR_CONSULTATION_REPORT_ISSUE_TYPES = {
    "mentor": {
        "服务态度问题",
        "虚假经历或信息",
        "收费或诱导私下交易",
        "爽约或未提供服务",
        "骚扰、辱骂或不当言行",
        "泄露隐私",
        "其他问题",
    },
    "applicant": {
        "骚扰、辱骂或不当言行",
        "虚假身份或材料",
        "诱导私下交易",
        "恶意占用时段或爽约",
        "侵犯隐私",
        "发布不当内容",
        "恶意评价或失实反馈",
        "其他问题",
    },
}
MENTOR_REVIEW_DISPUTE_ISSUE_TYPE = "恶意评价或失实反馈"
MENTOR_CONSULTATION_REPORT_FIELDS = (
    "id,order_id,reporter_user_id,reporter_role,respondent_user_id,target_role,target_user_id,target_mentor_id,"
    "issue_type,content,respondent_content,responded_at,status,resolution,refund_amount_cents,admin_note,handled_by,handled_at,"
    "first_response_due_at,first_response_at,priority,escalation_level,escalated_at,created_at,updated_at"
)
MENTOR_CONSULTATION_REPORT_APPEAL_FIELDS = (
    "id,report_id,appellant_user_id,appellant_role,content,status,decision,admin_note,handled_by,handled_at,"
    "first_response_due_at,first_response_at,priority,escalation_level,escalated_at,created_at,updated_at"
)
MENTOR_VERIFICATION_APPLICATION_FIELDS = (
    "id,applicant_user_id,legal_name,school,major,admission_year,graduation_year,"
    "exam_type,score,skills,bio,price_cents,application_status,admin_note,reviewed_at,"
    "created_at,updated_at"
)
MENTOR_PROFILE_CHANGE_REQUEST_FIELDS = (
    "id,mentor_id,owner_user_id,school,major,exam_type,score,skills,bio,price_cents,"
    "request_status,admin_note,reviewed_at,created_at,updated_at"
)


def _normalise_keyword(value: str | None) -> str:
    return str(value or "").strip().lower()


def _matches_keyword(row: dict, keyword: str) -> bool:
    if not keyword:
        return True
    haystack = " ".join(
        str(row.get(field) or "")
        for field in ("display_name", "school", "major")
    ).lower()
    return all(token in haystack for token in keyword.split() if token)


def _sort_mentors(rows: list[dict], sort: str) -> list[dict]:
    if sort == "consult_count":
        return sorted(rows, key=lambda row: (-int(row.get("consult_count") or 0), -float(row.get("rating") or 0)))
    if sort == "rating":
        return sorted(rows, key=lambda row: (-float(row.get("rating") or 0), -int(row.get("consult_count") or 0)))
    if sort == "price":
        return sorted(rows, key=lambda row: (int(row.get("price_cents") or 0), -float(row.get("rating") or 0)))
    return sorted(
        rows,
        key=lambda row: (
            -int(row.get("recommend_score") or 0),
            not bool(row.get("is_featured")),
            -float(row.get("rating") or 0),
            -int(row.get("consult_count") or 0),
        ),
    )


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc_datetime(value: object) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _validate_mentor_slot_schedule_window(starts_at: datetime, ends_at: datetime) -> None:
    """Keep owner-created appointment slots within the public scheduling window."""
    local_start = starts_at.astimezone(MENTOR_SLOT_LOCAL_TIMEZONE)
    local_end = ends_at.astimezone(MENTOR_SLOT_LOCAL_TIMEZONE)
    local_today = _utc_now().astimezone(MENTOR_SLOT_LOCAL_TIMEZONE).date()
    latest_date = local_today + timedelta(days=MENTOR_SLOT_DATE_WINDOW_DAYS - 1)

    if local_start.date() < local_today or local_start.date() > latest_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"预约日期仅可选择今天起 {MENTOR_SLOT_DATE_WINDOW_DAYS} 天内",
        )

    is_full_hour = (
        local_start.minute == 0
        and local_start.second == 0
        and local_start.microsecond == 0
        and local_end.minute == 0
        and local_end.second == 0
        and local_end.microsecond == 0
    )
    is_supported_hour = (
        MENTOR_SLOT_FIRST_HOUR <= local_start.hour < MENTOR_SLOT_LAST_HOUR
        and local_end.date() == local_start.date()
        and local_end.hour == local_start.hour + 1
    )
    if not is_full_hour or not is_supported_hour:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"预约时段仅支持 {MENTOR_SLOT_FIRST_HOUR:02d}:00–{MENTOR_SLOT_LAST_HOUR:02d}:00 的整点 60 分钟时段",
        )


def _new_order_no() -> str:
    return f"MC{_utc_now():%Y%m%d%H%M%S}{uuid4().hex[:8].upper()}"


def _detect_mentor_verification_document_content_type(data: bytes) -> tuple[str, str] | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", "jpg"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp", "webp"
    return None


def _ensure_mentor_verification_document_bucket(storage) -> None:
    try:
        storage.get_bucket(MENTOR_VERIFICATION_DOCUMENT_BUCKET)
        return
    except Exception:
        pass

    try:
        storage.create_bucket(
            MENTOR_VERIFICATION_DOCUMENT_BUCKET,
            options={
                "public": False,
                "file_size_limit": MAX_MENTOR_VERIFICATION_DOCUMENT_BYTES,
                "allowed_mime_types": list(MENTOR_VERIFICATION_DOCUMENT_CONTENT_TYPES),
            },
        )
    except Exception:
        storage.get_bucket(MENTOR_VERIFICATION_DOCUMENT_BUCKET)


def _ensure_mentor_consultation_report_evidence_bucket(storage) -> None:
    try:
        storage.get_bucket(MENTOR_CONSULTATION_REPORT_EVIDENCE_BUCKET)
        return
    except Exception:
        pass

    try:
        storage.create_bucket(
            MENTOR_CONSULTATION_REPORT_EVIDENCE_BUCKET,
            options={
                "public": False,
                "file_size_limit": MAX_MENTOR_CONSULTATION_REPORT_EVIDENCE_BYTES,
                "allowed_mime_types": list(MENTOR_CONSULTATION_REPORT_EVIDENCE_CONTENT_TYPES),
            },
        )
    except Exception:
        storage.get_bucket(MENTOR_CONSULTATION_REPORT_EVIDENCE_BUCKET)


def _ensure_mentor_consultation_report_appeal_evidence_bucket(storage) -> None:
    try:
        storage.get_bucket(MENTOR_CONSULTATION_REPORT_APPEAL_EVIDENCE_BUCKET)
        return
    except Exception:
        pass

    try:
        storage.create_bucket(
            MENTOR_CONSULTATION_REPORT_APPEAL_EVIDENCE_BUCKET,
            options={
                "public": False,
                "file_size_limit": MAX_MENTOR_CONSULTATION_REPORT_EVIDENCE_BYTES,
                "allowed_mime_types": list(MENTOR_CONSULTATION_REPORT_EVIDENCE_CONTENT_TYPES),
            },
        )
    except Exception:
        storage.get_bucket(MENTOR_CONSULTATION_REPORT_APPEAL_EVIDENCE_BUCKET)


def _serialize_mentor_verification_application(row: dict, *, document_count: int = 0) -> dict:
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


def _get_owned_mentor_verification_application_or_404(supabase, application_id: str, user_id: str) -> dict:
    response = call_supabase(
        lambda: (
            supabase.table("mentor_verification_applications")
            .select(MENTOR_VERIFICATION_APPLICATION_FIELDS)
            .eq("id", application_id)
            .eq("applicant_user_id", user_id)
            .limit(1)
            .execute()
        ),
        operation_name="mentor verification application lookup",
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到前辈申请")
    return response.data[0]


def _get_order_mentor_or_404(supabase, mentor_id: str, *, require_public: bool = True) -> dict:
    query = supabase.table("mentor_profiles").select(ORDER_MENTOR_FIELDS).eq("id", mentor_id)
    if require_public:
        query = query.eq("is_published", True).eq("verification_status", "verified")
    response = call_supabase(
        lambda: query.limit(1).execute(),
        operation_name="consultation mentor lookup",
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到可咨询的前辈")
    return response.data[0]


def _get_current_owned_mentor_or_404(supabase, user_id: str) -> dict:
    response = call_supabase(
        lambda: (
            supabase.table("mentor_profiles")
            .select(PUBLIC_PROFILE_FIELDS)
            .eq("owner_user_id", user_id)
            .limit(1)
            .execute()
        ),
        operation_name="current mentor profile lookup",
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="当前账号尚未绑定前辈档案")
    mentor = response.data[0]
    try:
        user_response = call_supabase(
            lambda: (
                supabase.table("users")
                .select("avatar_url")
                .eq("id", user_id)
                .limit(1)
                .execute()
            ),
            operation_name="current mentor avatar lookup",
        )
        avatar_url = str((user_response.data or [{}])[0].get("avatar_url") or "").strip()
        if avatar_url:
            mentor = {**mentor, "avatar_url": avatar_url}
    except Exception as exc:
        logger.warning("Current mentor avatar lookup skipped (error_type=%s)", type(exc).__name__)
    return mentor


def _get_current_owned_mentor_for_action_or_404(supabase, user_id: str) -> dict:
    """Return only the fields needed by a mentor-owned write/list action.

    The owner homepage has a richer profile lookup for display.  Most owner
    actions only need the mentor id (and slot creation can use the default
    price), so avoid the extra avatar lookup on those hot paths.
    """
    response = call_supabase(
        lambda: (
            supabase.table("mentor_profiles")
            .select("id,price_cents")
            .eq("owner_user_id", user_id)
            .limit(1)
            .execute()
        ),
        operation_name="current mentor action lookup",
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="当前账号尚未绑定前辈档案")
    return response.data[0]


def _serialize_owned_mentor_profile(supabase, row: dict) -> MentorOwnerProfileResponse:
    mentor_id = str(row.get("id") or "")
    skills_by_mentor = fetch_mentor_skills(supabase, [mentor_id])
    # mentor_profiles.rating / rating_count / consult_count are maintained by
    # database/mentor_consultation_aggregates.sql triggers.  Reusing those
    # fields avoids two full scans of reviews and completed orders whenever a
    # mentor opens their own homepage.
    return MentorOwnerProfileResponse(mentor=serialize_mentor_public(
        row,
        skills_by_mentor.get(mentor_id, []),
    ))


def _get_order_or_404(supabase, order_id: str) -> dict:
    response = call_supabase(
        lambda: (
            supabase.table("mentor_consultation_orders")
            .select(CONSULTATION_ORDER_FIELDS)
            .eq("id", order_id)
            .limit(1)
            .execute()
        ),
        operation_name="consultation order lookup",
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该咨询订单")
    return response.data[0]


def _get_slot_or_404(supabase, slot_id: str) -> dict:
    response = call_supabase(
        lambda: (
            supabase.table("mentor_availability_slots")
            .select("id,mentor_id,starts_at,ends_at,price_cents,status")
            .eq("id", slot_id)
            .limit(1)
            .execute()
        ),
        operation_name="consultation slot lookup",
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该预约时段")
    return response.data[0]


def _serialize_order_item(row: dict) -> MentorConsultationOrderItem:
    return MentorConsultationOrderItem(**serialize_mentor_order(row))


def _get_order_participant(supabase, order_id: str, user_id: str) -> tuple[dict, str, dict]:
    order = _get_order_or_404(supabase, order_id)
    mentor = _get_order_mentor_or_404(
        supabase,
        str(order.get("mentor_id") or ""),
        require_public=False,
    )
    if str(order.get("applicant_user_id") or "") == user_id:
        return order, "applicant", mentor
    if str(mentor.get("owner_user_id") or "") == user_id:
        return order, "mentor", mentor
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该咨询订单")


def _get_consultation_report_participation_role(row: dict, user_id: str) -> str | None:
    if str(row.get("reporter_user_id") or "") == user_id:
        return "reporter"
    # target_user_id is retained as a safe read fallback for records created before the
    # respondent column was backfilled by the incremental migration.
    respondent_user_id = str(row.get("respondent_user_id") or row.get("target_user_id") or "")
    if respondent_user_id == user_id:
        return "respondent"
    return None


def _serialize_consultation_report_appeal(row: dict, *, evidence_count: int = 0) -> dict:
    settings = get_settings()
    sla = serialize_case_sla(
        row,
        fallback_first_response_hours=settings.mentor_consultation_report_appeal_first_response_hours,
        warning_hours=settings.mentor_consultation_report_sla_warning_hours,
    )
    return {
        "id": str(row.get("id") or ""),
        "report_id": str(row.get("report_id") or ""),
        "appellant_role": str(row.get("appellant_role") or "reporter"),
        "content": str(row.get("content") or ""),
        "status": str(row.get("status") or "pending"),
        "decision": str(row.get("decision") or "none"),
        "admin_note": row.get("admin_note") or None,
        "evidence_count": max(0, int(evidence_count or 0)),
        **sla,
        "created_at": row.get("created_at") or None,
        "handled_at": row.get("handled_at") or None,
    }


def _fetch_consultation_report_appeal_summary(
    supabase,
    report_ids: list[str],
    user_id: str,
) -> dict[str, dict]:
    ids = list(dict.fromkeys(str(report_id) for report_id in report_ids if report_id))
    if not ids or not user_id:
        return {}
    try:
        response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_report_appeals")
                .select(MENTOR_CONSULTATION_REPORT_APPEAL_FIELDS)
                .in_("report_id", ids)
                .eq("appellant_user_id", user_id)
                .execute()
            ),
            operation_name="consultation report appeal summary lookup",
        )
    except Exception as exc:
        logger.warning("Consultation report appeal summary unavailable (error_type=%s)", type(exc).__name__)
        return {}
    rows = response.data or []
    appeal_ids = [str(row.get("id") or "") for row in rows if row.get("id")]
    evidence_counts = {appeal_id: 0 for appeal_id in appeal_ids}
    if appeal_ids:
        try:
            evidence_response = call_supabase(
                lambda: (
                    supabase.table("mentor_consultation_report_appeal_evidence")
                    .select("appeal_id")
                    .in_("appeal_id", appeal_ids)
                    .execute()
                ),
                operation_name="consultation report appeal evidence summary lookup",
            )
        except Exception as exc:
            logger.warning("Consultation report appeal evidence summary unavailable (error_type=%s)", type(exc).__name__)
            evidence_response = None
        for evidence in ((evidence_response.data if evidence_response else []) or []):
            appeal_id = str(evidence.get("appeal_id") or "")
            if appeal_id in evidence_counts:
                evidence_counts[appeal_id] += 1
    return {
        str(row.get("report_id") or ""): {
            **row,
            "evidence_count": evidence_counts.get(str(row.get("id") or ""), 0),
        }
        for row in rows
        if row.get("report_id")
    }


def _serialize_consultation_report(
    row: dict,
    *,
    user_id: str | None = None,
    evidence_summary: dict | None = None,
    appeal_summary: dict | None = None,
) -> dict:
    participation_role = _get_consultation_report_participation_role(row, user_id) if user_id else "reporter"
    summary = evidence_summary or {}
    appeal = appeal_summary or {}
    report_status = str(row.get("status") or "pending")
    settings = get_settings()
    sla = serialize_case_sla(
        row,
        fallback_first_response_hours=settings.mentor_consultation_report_first_response_hours,
        warning_hours=settings.mentor_consultation_report_sla_warning_hours,
    )
    appeal_sla = serialize_case_sla(
        appeal,
        fallback_first_response_hours=settings.mentor_consultation_report_appeal_first_response_hours,
        warning_hours=settings.mentor_consultation_report_sla_warning_hours,
    ) if appeal else {}
    return {
        "id": str(row.get("id") or ""),
        "order_id": str(row.get("order_id") or ""),
        "reporter_role": str(row.get("reporter_role") or "applicant"),
        "target_role": str(row.get("target_role") or "mentor"),
        "issue_type": str(row.get("issue_type") or "其他问题"),
        "content": str(row.get("content") or ""),
        "respondent_content": str(row.get("respondent_content") or "") or None,
        "responded_at": row.get("responded_at") or None,
        "participation_role": participation_role or "reporter",
        "can_respond": participation_role == "respondent" and report_status in {"pending", "reviewing"},
        "status": report_status,
        "resolution": str(row.get("resolution") or "none"),
        "refund_amount": round(max(0, int(row.get("refund_amount_cents") or 0)) / 100, 2),
        "admin_note": row.get("admin_note") or None,
        "reporter_evidence_count": max(0, int(summary.get("reporter") or 0)),
        "respondent_evidence_count": max(0, int(summary.get("respondent") or 0)),
        "can_appeal": bool(participation_role and report_status in {"resolved", "dismissed"} and not appeal),
        "appeal_id": str(appeal.get("id") or "") or None,
        "appeal_status": str(appeal.get("status") or "") or None,
        "appeal_decision": str(appeal.get("decision") or "") or None,
        "appeal_content": str(appeal.get("content") or "") or None,
        "appeal_admin_note": appeal.get("admin_note") or None,
        "appeal_evidence_count": max(0, int(appeal.get("evidence_count") or 0)),
        "appeal_created_at": appeal.get("created_at") or None,
        "appeal_handled_at": appeal.get("handled_at") or None,
        "appeal_first_response_due_at": appeal_sla.get("first_response_due_at") or None,
        "appeal_first_response_at": appeal_sla.get("first_response_at") or None,
        "appeal_priority": appeal_sla.get("priority") or None,
        "appeal_escalation_level": max(0, int(appeal_sla.get("escalation_level") or 0)),
        "appeal_escalated_at": appeal_sla.get("escalated_at") or None,
        "appeal_sla_status": appeal_sla.get("sla_status") or None,
        **sla,
        "created_at": row.get("created_at") or None,
        "handled_at": row.get("handled_at") or None,
    }


def _fetch_consultation_report_evidence_summary(supabase, report_ids: list[str]) -> dict[str, dict[str, int]]:
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
        operation_name="consultation report evidence summary lookup",
    )
    summary = {report_id: {"reporter": 0, "respondent": 0} for report_id in ids}
    for row in response.data or []:
        report_id = str(row.get("report_id") or "")
        submitter_role = str(row.get("submitter_role") or "reporter")
        if report_id in summary and submitter_role in {"reporter", "respondent"}:
            summary[report_id][submitter_role] += 1
    return summary


def _get_participant_consultation_report_or_404(supabase, report_id: str, user_id: str) -> tuple[dict, str]:
    response = call_supabase(
        lambda: (
            supabase.table("mentor_consultation_reports")
            .select(MENTOR_CONSULTATION_REPORT_FIELDS)
            .eq("id", report_id)
            .limit(1)
            .execute()
        ),
        operation_name="consultation report lookup",
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该举报记录")
    report = response.data[0]
    participation_role = _get_consultation_report_participation_role(report, user_id)
    if not participation_role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该举报记录")
    return report, participation_role


def _refresh_pending_accept_status(supabase, order: dict) -> dict:
    """Resolve visible orders with the same server-side lifecycle rules."""

    return refresh_expired_mentor_consultation_order(supabase, order)


def _assert_order_status(order: dict, allowed: set[str], message: str) -> None:
    if str(order.get("order_status") or "") not in allowed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)


def _insert_system_message(supabase, order_id: str, content: str) -> None:
    try:
        call_supabase(
            lambda: supabase.table("mentor_consultation_messages").insert({
                "order_id": order_id,
                "sender_role": "system",
                "message_type": "system",
                "content": content,
            }).execute(),
            operation_name="consultation system message create",
        )
    except Exception as exc:
        logger.warning("Consultation system message skipped (error_type=%s)", type(exc).__name__)


def _insert_order_event(
    supabase,
    order_id: str,
    *,
    event_type: str,
    actor_role: str,
    actor_user_id: str | None = None,
    details: dict | None = None,
) -> None:
    """Keep an append-only business trail independent of chat display messages."""

    try:
        call_supabase(
            lambda: supabase.table("mentor_consultation_order_events").insert({
                "order_id": order_id,
                "actor_user_id": actor_user_id,
                "actor_role": actor_role,
                "event_type": event_type,
                "details": details or {},
            }).execute(),
            operation_name="consultation order event create",
        )
    except Exception as exc:
        logger.warning("Consultation order event skipped (event=%s error_type=%s)", event_type, type(exc).__name__)


def _configured_payment_provider() -> str:
    provider = str(get_settings().mentor_consultation_payment_provider or "").strip()
    return provider[:80] or "unconfigured"


def _payment_mode() -> str:
    return "demo" if get_settings().mentor_consultation_demo_payment_enabled else "real"


def _real_payment_ready() -> bool:
    settings = get_settings()
    return bool(
        settings.mentor_consultation_real_payment_enabled
        and _configured_payment_provider() != "unconfigured"
        and str(settings.mentor_consultation_payment_checkout_url or "").strip()
        and str(settings.payment_webhook_secret or "").strip()
    )


def _order_creation_enabled() -> bool:
    return bool(get_settings().mentor_consultation_demo_payment_enabled or _real_payment_ready())


def _assert_order_creation_enabled() -> None:
    if not _order_creation_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="微信支付商户资质审核中，当前暂不创建收费咨询订单，也不会发生扣款。",
        )


def _order_request_fingerprint(
    *,
    mentor_id: str,
    consultation_type: str,
    slot_id: str | None,
    questionnaire: dict,
    service_rules_version: str,
) -> str:
    canonical = json.dumps(
        {
            "mentor_id": mentor_id,
            "consultation_type": consultation_type,
            "slot_id": slot_id or "",
            "questionnaire": questionnaire,
            "service_rules_version": service_rules_version,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _map_order_rpc_error(exc: Exception) -> HTTPException | None:
    error_text = str(exc).lower()
    mappings = (
        ("client_order_conflict", status.HTTP_409_CONFLICT, "该提交标识已用于另一份咨询内容，请返回后重新发起"),
        ("slot_unavailable", status.HTTP_409_CONFLICT, "该预约时段刚刚被占用，请重新选择"),
        ("slot_mismatch", status.HTTP_422_UNPROCESSABLE_ENTITY, "预约时段与前辈不匹配"),
        ("booking_unavailable", status.HTTP_409_CONFLICT, "该前辈暂未开放预约"),
        ("mentor_unavailable", status.HTTP_404_NOT_FOUND, "该前辈暂不可咨询"),
        ("self_consultation_not_allowed", status.HTTP_409_CONFLICT, "前辈本人不能创建自己的咨询订单"),
        ("booking_hold_lost", status.HTTP_409_CONFLICT, "预约时段预占已失效，请重新选择"),
        ("order_not_payable", status.HTTP_409_CONFLICT, "该订单当前无法确认支付"),
    )
    for marker, status_code, detail in mappings:
        if marker in error_text:
            return HTTPException(status_code=status_code, detail=detail)
    return None


def _is_demo_payment_reference(reference: object) -> bool:
    return str(reference or "").upper().startswith(("DEMO-", "MOCK-"))


def _build_payment_reference(order: dict) -> str:
    existing = str(order.get("payment_reference") or "").strip()
    if existing and not _is_demo_payment_reference(existing):
        return existing
    return f"MCON-{str(order.get('order_no') or '')}"


def _build_checkout_url(order: dict, payment_reference: str) -> str | None:
    template = str(get_settings().mentor_consultation_payment_checkout_url or "").strip()
    if not template:
        return None
    return (
        template
        .replace("{order_no}", str(order.get("order_no") or ""))
        .replace("{payment_reference}", payment_reference)
        .replace("{amount_cents}", str(max(0, int(order.get("price_cents") or 0))))
    )


def _refund_payment_status_for_order(order: dict) -> str:
    """Only historical/demo money can be settled synchronously inside the app."""

    return "refunded" if _is_demo_payment_reference(order.get("payment_reference")) else "refunding"


def _new_refund_reference(prefix: str, order: dict) -> str:
    return f"{prefix}-{str(order.get('order_no') or '')}-{uuid4().hex[:8].upper()}"


def _register_late_consultation_payment_for_refund(
    supabase,
    order: dict,
    *,
    payment_reference: str,
) -> dict:
    response = call_supabase(
        lambda: supabase.rpc(
            "register_mentor_consultation_late_payment",
            {
                "p_order_id": str(order.get("id") or ""),
                "p_payment_reference": payment_reference,
                "p_refund_reference": _new_refund_reference("LATE-PAY", order),
                "p_now": _utc_now().isoformat(),
            },
        ).execute(),
        operation_name="consultation late payment refund registration",
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到对应的咨询订单")
    return response.data[0]


def _mark_mentor_consultation_order_paid(
    supabase,
    order: dict,
    *,
    payment_reference: str,
    operation_name: str,
    allowed_payment_statuses: set[str] | None = None,
) -> dict:
    """Move a held order into the paid service flow in one database transaction."""

    order_id = str(order.get("id") or "")
    current_status = str(order.get("order_status") or "")
    current_payment_status = str(order.get("payment_status") or "")
    permitted_statuses = allowed_payment_statuses or {"unpaid", "failed"}
    if current_status in {"pending_accept", "booked"} and current_payment_status == "paid":
        return order
    _assert_order_status(order, {"pending_payment"}, "该订单当前无法确认支付")
    if current_payment_status not in permitted_statuses:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该订单当前支付状态不可确认")

    try:
        now = _utc_now()
        response = call_supabase(
            lambda: supabase.rpc(
                "confirm_mentor_consultation_payment",
                {
                    "p_order_id": order_id,
                    "p_payment_reference": payment_reference,
                    "p_response_expires_at": (
                        now + timedelta(minutes=ORDER_MENTOR_RESPONSE_WINDOW_MINUTES)
                    ).isoformat(),
                    "p_now": now.isoformat(),
                },
            ).execute(),
            operation_name=operation_name,
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到对应的咨询订单")
        paid_order = response.data[0]
        if str(paid_order.get("payment_status") or "") != "paid":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="订单支付预占已过期，请重新选择咨询时段并创建订单",
            )
        record_consultation_payment(supabase, paid_order)
        _notify_mentor_of_paid_consultation_order(supabase, paid_order)
        return paid_order
    except HTTPException:
        raise
    except Exception as exc:
        mapped_error = _map_order_rpc_error(exc)
        if mapped_error:
            raise mapped_error from exc
        raise


def _notify_mentor_of_paid_consultation_order(supabase, order: dict) -> None:
    """Create the source-of-truth in-app notification for a newly paid mentor order."""

    order_id = str(order.get("id") or "").strip()
    mentor_id = str(order.get("mentor_id") or "").strip()
    if not order_id or not mentor_id:
        return

    try:
        mentor = _get_order_mentor_or_404(supabase, mentor_id)
        recipient_user_id = str(mentor.get("owner_user_id") or "").strip()
        if not recipient_user_id:
            return

        consultation_type = str(order.get("consultation_type") or "instant")
        is_booking = consultation_type == "booking"
        title = "新的预约咨询已确认" if is_booking else "新的即时咨询待接单"
        summary = (
            "有考生已完成预约，请提前查看咨询资料。"
            if is_booking
            else "有考生已支付咨询费用，正在等待你的确认。"
        )
        content = (
            "预约时间已为你保留，点击查看时间和咨询信息。"
            if is_booking
            else "请在 10 分钟内前往咨询主页处理；超时后订单将自动关闭。"
        )
        route_path = f"/pages-sub-consultation/consultation/mentor-apply?mode=center&orderId={order_id}"
        create_user_notification(
            supabase,
            recipient_user_id=recipient_user_id,
            category="consultation",
            notification_type="mentor_order_created",
            title=title,
            summary=summary,
            content=content,
            related_type="mentor_consultation_order",
            related_id=order_id,
            route_path=route_path,
            delivery_payload={
                "surface": "mentor_order",
                "audience": "mentor",
                "order_id": order_id,
                "order_no": str(order.get("order_no") or ""),
                "consultation_type": consultation_type,
                "order_status": str(order.get("order_status") or ""),
                "expires_at": str(order.get("expires_at") or "") or None,
                "native_push": {
                    "title": title,
                    "body": summary,
                    "route_path": route_path,
                },
            },
        )
    except Exception as exc:
        # 消息投递异常不影响支付确认；订单页仍可作为前辈的兜底入口。
        logger.warning("Mentor order notification write skipped (order_id=%s error_type=%s)", order_id, type(exc).__name__)


def _notify_consultation_chat_message(
    supabase,
    *,
    order: dict,
    mentor: dict,
    sender_role: str,
    sender_user_id: str,
    message: dict,
) -> None:
    """Notify only the other consultation participant after a persisted chat message."""

    order_id = str(order.get("id") or "").strip()
    mentor_id = str(order.get("mentor_id") or "").strip()
    message_id = str(message.get("id") or "").strip()
    if not order_id or not mentor_id or not message_id:
        return

    is_mentor_sender = sender_role == "mentor"
    recipient_user_id = str(
        order.get("applicant_user_id") if is_mentor_sender else mentor.get("owner_user_id")
    ).strip()
    if not recipient_user_id or recipient_user_id == str(sender_user_id or ""):
        return

    sender_label = "前辈" if is_mentor_sender else "咨询用户"
    route_path = (
        f"/pages-sub-consultation/consultation/mentor-chat?mentorId={mentor_id}&orderId={order_id}"
        "&role=applicant&from=my-consultations"
        if is_mentor_sender
        else f"/pages-sub-consultation/consultation/mentor-apply?mode=center&orderId={order_id}"
    )
    content = str(message.get("content") or "").strip()[:180] or "对方发来了一条新消息。"
    create_user_notification(
        supabase,
        recipient_user_id=recipient_user_id,
        category="consultation",
        notification_type="mentor_chat_message",
        title="新的咨询消息",
        summary=f"{sender_label}发来一条新消息",
        content=content,
        related_type="mentor_consultation_message",
        related_id=message_id,
        route_path=route_path,
        delivery_payload={
            "surface": "mentor_chat",
            "audience": "applicant" if is_mentor_sender else "mentor",
            "order_id": order_id,
            "mentor_id": mentor_id,
            "sender_role": sender_role,
            "sender_user_id": str(sender_user_id or ""),
            "message_id": message_id,
            "native_push": {
                "title": "新的咨询消息",
                "body": content,
                "route_path": route_path,
            },
        },
    )


def _notify_consultation_applicant_order_status(
    supabase,
    *,
    order: dict,
    event: str,
    detail: str = "",
) -> None:
    """Keep the consultation owner informed when the mentor changes a visible order state."""

    order_id = str(order.get("id") or "").strip()
    mentor_id = str(order.get("mentor_id") or "").strip()
    recipient_user_id = str(order.get("applicant_user_id") or "").strip()
    if not order_id or not mentor_id or not recipient_user_id:
        return

    if event == "accepted":
        title = "你的咨询已被前辈接单"
        summary = "咨询已开始，可以进入聊天与前辈沟通。"
        content = detail or "本次咨询窗口已开启，请及时进入聊天页面。"
        route_path = f"/pages-sub-consultation/consultation/mentor-chat?mentorId={mentor_id}&orderId={order_id}&role=applicant&from=my-consultations"
    elif event == "started":
        title = "你的预约咨询已开始"
        summary = "前辈已开启本次预约咨询。"
        content = detail or "现在可以进入聊天页面与前辈沟通。"
        route_path = f"/pages-sub-consultation/consultation/mentor-chat?mentorId={mentor_id}&orderId={order_id}&role=applicant&from=my-consultations"
    elif event == "cancelled":
        title = "本次咨询已被前辈取消"
        summary = "订单状态与退款进度已同步到你的咨询记录。"
        content = detail or "你可以在“我的咨询”中查看处理说明。"
        route_path = "/pages-sub-consultation/consultation/my-consultations"
    else:
        title = "本次咨询暂未被接单"
        summary = "前辈暂未接受本次咨询，退款状态已同步到咨询记录。"
        content = detail or "你可以在“我的咨询”中查看处理说明和订单状态。"
        route_path = "/pages-sub-consultation/consultation/my-consultations"

    create_user_notification(
        supabase,
        recipient_user_id=recipient_user_id,
        category="consultation",
        notification_type="mentor_order_status",
        title=title,
        summary=summary,
        content=content,
        related_type="mentor_consultation_order",
        related_id=f"{order_id}:{event}",
        route_path=route_path,
        delivery_payload={
            "surface": "mentor_order",
            "audience": "applicant",
            "event": event,
            "order_id": order_id,
            "mentor_id": mentor_id,
            "order_status": str(order.get("order_status") or ""),
        },
    )


@router.get("/me/verification-application", response_model=MentorVerificationApplicationStatusResponse)
def get_my_mentor_verification_application(
    user_id: str = Depends(get_current_user_id),
) -> MentorVerificationApplicationStatusResponse:
    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: (
                supabase.table("mentor_verification_applications")
                .select(MENTOR_VERIFICATION_APPLICATION_FIELDS)
                .eq("applicant_user_id", user_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            ),
            operation_name="my mentor verification application",
        )
        if not response.data:
            return MentorVerificationApplicationStatusResponse(application=None)
        application = response.data[0]
        document_response = call_supabase(
            lambda: (
                supabase.table("mentor_verification_documents")
                .select("id", count="exact")
                .eq("application_id", application["id"])
                .limit(1)
                .execute()
            ),
            operation_name="my mentor verification document count",
        )
        return MentorVerificationApplicationStatusResponse(
            application=MentorVerificationApplicationItem(
                **_serialize_mentor_verification_application(
                    application,
                    document_count=int(document_response.count or 0),
                )
            )
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Mentor verification application lookup failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="前辈申请状态暂时不可用") from exc


@router.post("/verification-applications", response_model=MentorVerificationApplicationItem, status_code=status.HTTP_201_CREATED)
def create_mentor_verification_application(
    payload: MentorVerificationApplicationCreateRequest,
    user_id: str = Depends(get_current_user_id),
) -> MentorVerificationApplicationItem:
    if payload.graduation_year is not None and payload.graduation_year < payload.admission_year:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="毕业年份不能早于入学年份")

    supabase = get_supabase_admin()
    try:
        profile_response = call_supabase(
            lambda: (
                supabase.table("mentor_profiles")
                .select("id")
                .eq("owner_user_id", user_id)
                .limit(1)
                .execute()
            ),
            operation_name="mentor verification profile lookup",
        )
        if profile_response.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="你已拥有前辈档案，无需重复申请")

        pending_response = call_supabase(
            lambda: (
                supabase.table("mentor_verification_applications")
                .select("id")
                .eq("applicant_user_id", user_id)
                .eq("application_status", "pending")
                .limit(1)
                .execute()
            ),
            operation_name="mentor verification pending lookup",
        )
        if pending_response.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="你已有正在审核的前辈申请")

        data = payload.model_dump()
        data.update(
            {
                "applicant_user_id": user_id,
                "legal_name": payload.legal_name.strip(),
                "school": payload.school.strip(),
                "major": payload.major.strip(),
                "bio": payload.bio.strip(),
                "skills": normalize_skills(payload.skills),
                "application_status": "pending",
            }
        )
        response = call_supabase(
            lambda: supabase.table("mentor_verification_applications").insert(data).execute(),
            operation_name="mentor verification application create",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="前辈申请提交失败")
        return MentorVerificationApplicationItem(**_serialize_mentor_verification_application(response.data[0]))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Mentor verification application create failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="前辈申请提交失败") from exc


@router.post(
    "/verification-applications/{application_id}/documents",
    response_model=MentorVerificationDocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_mentor_verification_document(
    application_id: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
) -> MentorVerificationDocumentUploadResponse:
    data = await file.read(MAX_MENTOR_VERIFICATION_DOCUMENT_BYTES + 1)
    filename = str(file.filename or "证明材料").strip()[:255] or "证明材料"
    await file.close()

    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="证明材料为空")
    if len(data) > MAX_MENTOR_VERIFICATION_DOCUMENT_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="单份证明材料不能超过 8 MB")
    detected = _detect_mentor_verification_document_content_type(data)
    if not detected:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="证明材料仅支持 PNG、JPG 或 WebP 图片")

    content_type, extension = detected
    supabase = get_supabase_admin()
    try:
        application = _get_owned_mentor_verification_application_or_404(supabase, application_id, user_id)
        if application.get("application_status") != "pending":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="当前申请已处理，不能继续补充证明材料")
        count_response = call_supabase(
            lambda: (
                supabase.table("mentor_verification_documents")
                .select("id", count="exact")
                .eq("application_id", application_id)
                .limit(1)
                .execute()
            ),
            operation_name="mentor verification document limit check",
        )
        if int(count_response.count or 0) >= 3:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="最多上传 3 份证明材料")

        _ensure_mentor_verification_document_bucket(supabase.storage)
        storage_path = f"{user_id}/{application_id}/{uuid4().hex}.{extension}"
        supabase.storage.from_(MENTOR_VERIFICATION_DOCUMENT_BUCKET).upload(
            storage_path,
            data,
            file_options={
                "content-type": content_type,
                "cache-control": "31536000",
                "upsert": "false",
            },
        )
        response = call_supabase(
            lambda: supabase.table("mentor_verification_documents").insert(
                {
                    "application_id": application_id,
                    "file_url": storage_path,
                    "file_name": filename,
                    "document_type": "other",
                    "mime_type": content_type,
                }
            ).execute(),
            operation_name="mentor verification document create",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="证明材料保存失败")
        document = response.data[0]
        return MentorVerificationDocumentUploadResponse(
            id=str(document.get("id") or ""),
            file_url=str(document.get("file_url") or ""),
            file_name=str(document.get("file_name") or filename),
            document_type=str(document.get("document_type") or "other"),
            mime_type=document.get("mime_type") or content_type,
            created_at=document.get("created_at") or None,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Mentor verification document upload failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="证明材料上传失败") from exc


@router.get("/me/mentor-profile", response_model=MentorOwnerProfileResponse)
def get_my_owned_mentor_profile(
    user_id: str = Depends(get_current_user_id),
) -> MentorOwnerProfileResponse:
    supabase = get_supabase_admin()
    try:
        mentor = _get_current_owned_mentor_or_404(supabase, user_id)
        return _serialize_owned_mentor_profile(supabase, mentor)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Current mentor profile unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="前辈主页暂时不可用") from exc


@router.get("/me/mentor-profile/change-request", response_model=MentorProfileChangeRequestStatusResponse)
def get_my_mentor_profile_change_request(
    user_id: str = Depends(get_current_user_id),
) -> MentorProfileChangeRequestStatusResponse:
    """Return only the active revision request so a mentor can continue using the old profile."""
    supabase = get_supabase_admin()
    try:
        _get_current_owned_mentor_for_action_or_404(supabase, user_id)
        response = call_supabase(
            lambda: (
                supabase.table("mentor_profile_change_requests")
                .select(MENTOR_PROFILE_CHANGE_REQUEST_FIELDS)
                .eq("owner_user_id", user_id)
                .eq("request_status", "pending")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            ),
            operation_name="mentor profile change request lookup",
        )
        row = (response.data or [None])[0]
        return MentorProfileChangeRequestStatusResponse(
            request=MentorProfileChangeRequestItem(**_serialize_mentor_profile_change_request(row)) if row else None
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Mentor profile change request lookup failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="资料修改审核状态暂时不可用") from exc


@router.post(
    "/me/mentor-profile/change-request",
    response_model=MentorProfileChangeRequestItem,
    status_code=status.HTTP_201_CREATED,
)
def create_my_mentor_profile_change_request(
    payload: MentorProfileChangeRequestCreateRequest,
    user_id: str = Depends(get_current_user_id),
) -> MentorProfileChangeRequestItem:
    """Create a review request without changing the verified mentor profile."""
    school = payload.school.strip()
    major = payload.major.strip()
    if not school or not major:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="录取院校和专业不能为空")

    supabase = get_supabase_admin()
    try:
        mentor = _get_current_owned_mentor_for_action_or_404(supabase, user_id)
        mentor_id = str(mentor.get("id") or "")
        existing_response = call_supabase(
            lambda: (
                supabase.table("mentor_profile_change_requests")
                .select("id")
                .eq("mentor_id", mentor_id)
                .eq("request_status", "pending")
                .limit(1)
                .execute()
            ),
            operation_name="mentor pending profile change request lookup",
        )
        if existing_response.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="你已有正在审核的资料修改申请")

        response = call_supabase(
            lambda: supabase.table("mentor_profile_change_requests").insert({
                "mentor_id": mentor_id,
                "owner_user_id": user_id,
                "school": school,
                "major": major,
                "exam_type": payload.exam_type,
                "score": payload.score,
                "skills": normalize_skills(payload.skills)[:4],
                "bio": payload.bio.strip(),
                "price_cents": payload.price_cents,
                "request_status": "pending",
            }).execute(),
            operation_name="mentor profile change request create",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="资料修改申请提交失败")
        return MentorProfileChangeRequestItem(**_serialize_mentor_profile_change_request(response.data[0]))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Mentor profile change request create failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="资料修改申请提交失败") from exc


@router.patch("/me/mentor-profile/availability", response_model=MentorOwnerProfileResponse)
def update_my_owned_mentor_availability(
    payload: MentorOwnerAvailabilityUpdateRequest,
    user_id: str = Depends(get_current_user_id),
) -> MentorOwnerProfileResponse:
    supabase = get_supabase_admin()
    try:
        mentor = _get_current_owned_mentor_for_action_or_404(supabase, user_id)
        mentor_id = str(mentor.get("id") or "")
        response = call_supabase(
            lambda: (
                supabase.table("mentor_profiles")
                .update({"online_status": payload.online_status})
                .eq("id", mentor_id)
                .eq("owner_user_id", user_id)
                .execute()
            ),
            operation_name="mentor availability update",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="前辈在线状态已变化，请刷新后重试")
        return _serialize_owned_mentor_profile(supabase, response.data[0])
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Mentor availability update failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="在线状态更新失败") from exc


@router.get("/me/mentor-slots", response_model=MentorOwnerAvailabilitySlotListResponse)
def list_my_mentor_availability_slots(
    include_past: bool = Query(default=False),
    limit: int = Query(default=30, ge=1, le=MENTOR_SLOT_MAX_LIMIT),
    cursor: str | None = Query(default=None, max_length=2048),
    user_id: str = Depends(get_current_user_id),
) -> MentorOwnerAvailabilitySlotListResponse:
    cursor_context = {"include_past": include_past}
    cursor_payload = decode_page_cursor(
        cursor,
        kind="mentor_slots",
        context=cursor_context,
    )
    supabase = get_supabase_admin()
    try:
        mentor = _get_current_owned_mentor_for_action_or_404(supabase, user_id)
        mentor_id = str(mentor.get("id") or "")
        now_iso = _utc_now().isoformat()
        call_supabase(
            lambda: (
                supabase.table("mentor_availability_slots")
                .update({"status": "expired"})
                .eq("mentor_id", mentor_id)
                .eq("status", "available")
                .lt("ends_at", now_iso)
                .execute()
            ),
            operation_name="mentor slot expiry refresh",
        )
        query = (
            supabase.table("mentor_availability_slots")
            .select("id,starts_at,ends_at,price_cents,status", count="exact")
            .eq("mentor_id", mentor_id)
        )
        if not include_past:
            query = query.gt("ends_at", now_iso)
        if cursor_payload:
            query = query.or_(build_keyset_filter([
                ("starts_at", "asc", cursor_datetime(cursor_payload, "starts_at")),
                ("id", "asc", cursor_uuid(cursor_payload, "id")),
            ]))
        response = call_supabase(
            lambda: (
                query
                .order("starts_at")
                .order("id")
                .limit(limit + 1)
                .execute()
            ),
            operation_name="mentor own availability list",
        )
        rows = list(response.data or [])
        has_more = len(rows) > limit
        page_rows = rows[:limit]
        next_cursor = None
        if has_more and page_rows:
            anchor = page_rows[-1]
            next_cursor = encode_page_cursor("mentor_slots", {
                **cursor_context,
                "starts_at": str(anchor.get("starts_at") or ""),
                "id": str(anchor.get("id") or ""),
            })
        return MentorOwnerAvailabilitySlotListResponse(
            items=[MentorAvailabilitySlotItem(**serialize_mentor_slot(row)) for row in page_rows],
            count=int(response.count or len(page_rows)),
            next_cursor=next_cursor,
            has_more=has_more,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Mentor availability slots unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="预约时段暂时不可用") from exc


@router.post(
    "/me/mentor-slots",
    response_model=MentorAvailabilitySlotItem,
    status_code=status.HTTP_201_CREATED,
)
def create_my_mentor_availability_slot(
    payload: MentorOwnerAvailabilitySlotCreateRequest,
    user_id: str = Depends(get_current_user_id),
) -> MentorAvailabilitySlotItem:
    starts_at = payload.starts_at.astimezone(timezone.utc) if payload.starts_at.tzinfo else payload.starts_at.replace(tzinfo=timezone.utc)
    ends_at = payload.ends_at.astimezone(timezone.utc) if payload.ends_at.tzinfo else payload.ends_at.replace(tzinfo=timezone.utc)
    if starts_at <= _utc_now() + timedelta(minutes=5):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="预约时段需从 5 分钟后开始")
    if ends_at <= starts_at:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="结束时间必须晚于开始时间")
    if ends_at - starts_at != timedelta(minutes=MENTOR_SLOT_WINDOW_MINUTES):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"单次预约时段需为 {MENTOR_SLOT_WINDOW_MINUTES} 分钟",
        )
    _validate_mentor_slot_schedule_window(starts_at, ends_at)

    supabase = get_supabase_admin()
    try:
        mentor = _get_current_owned_mentor_for_action_or_404(supabase, user_id)
        mentor_id = str(mentor.get("id") or "")
        starts_at_iso = starts_at.isoformat()
        ends_at_iso = ends_at.isoformat()
        overlap_response = call_supabase(
            lambda: (
                supabase.table("mentor_availability_slots")
                .select("id")
                .eq("mentor_id", mentor_id)
                .in_("status", ["available", "held", "booked", "closed"])
                .lt("starts_at", ends_at_iso)
                .gt("ends_at", starts_at_iso)
                .limit(1)
                .execute()
            ),
            operation_name="mentor availability overlap lookup",
        )
        if overlap_response.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该时间与已有预约时段重叠")

        # 预约时段始终沿用前辈资料中已审核的价格，不能由前辈在放号时单独改价。
        price_cents = max(0, int(mentor.get("price_cents") or 0))
        response = call_supabase(
            lambda: supabase.table("mentor_availability_slots").insert({
                "mentor_id": mentor_id,
                "starts_at": starts_at_iso,
                "ends_at": ends_at_iso,
                "price_cents": price_cents,
                "status": "available",
            }).execute(),
            operation_name="mentor availability slot create",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="预约时段创建失败")
        return MentorAvailabilitySlotItem(**serialize_mentor_slot(response.data[0]))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Mentor availability slot create failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="预约时段创建失败") from exc


@router.patch("/me/mentor-slots/{slot_id}", response_model=MentorAvailabilitySlotItem)
def update_my_mentor_availability_slot(
    slot_id: UUID,
    payload: MentorOwnerAvailabilitySlotStatusUpdateRequest,
    user_id: str = Depends(get_current_user_id),
) -> MentorAvailabilitySlotItem:
    supabase = get_supabase_admin()
    try:
        mentor = _get_current_owned_mentor_for_action_or_404(supabase, user_id)
        mentor_id = str(mentor.get("id") or "")
        slot = _get_slot_or_404(supabase, str(slot_id))
        if str(slot.get("mentor_id") or "") != mentor_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该预约时段")
        if str(slot.get("status") or "") in {"held", "booked"}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已被预占或预约的时段不能关闭")
        if payload.status == "available":
            ends_at = _as_utc_datetime(slot.get("ends_at"))
            if ends_at is None or ends_at <= _utc_now():
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已过期的时段不能重新开放")
        response = call_supabase(
            lambda: (
                supabase.table("mentor_availability_slots")
                .update({"status": payload.status})
                .eq("id", str(slot_id))
                .eq("mentor_id", mentor_id)
                .execute()
            ),
            operation_name="mentor availability slot status update",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="预约时段状态已变化，请刷新后重试")
        return MentorAvailabilitySlotItem(**serialize_mentor_slot(response.data[0]))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Mentor availability slot update failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="预约时段更新失败") from exc


@router.get("/me/mentor-orders", response_model=MentorConsultationOrderListResponse)
def list_my_received_mentor_consultation_orders(
    order_status: str | None = Query(default=None, max_length=32),
    limit: int = Query(default=20, ge=1, le=ORDER_LIST_MAX_LIMIT),
    cursor: str | None = Query(default=None, max_length=2048),
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationOrderListResponse:
    normalized_status = str(order_status or "").strip().lower()
    if normalized_status and normalized_status not in CONSULTATION_ORDER_STATUSES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的订单状态")

    cursor_context = {"order_status": normalized_status}
    cursor_payload = decode_page_cursor(
        cursor,
        kind="mentor_received_orders",
        context=cursor_context,
    )
    supabase = get_supabase_admin()
    try:
        mentor = _get_current_owned_mentor_for_action_or_404(supabase, user_id)
        query = (
            supabase.table("mentor_consultation_orders")
            .select(CONSULTATION_ORDER_FIELDS, count="exact")
            .eq("mentor_id", str(mentor.get("id") or ""))
        )
        if normalized_status:
            query = query.eq("order_status", normalized_status)
        if cursor_payload:
            query = query.or_(build_keyset_filter([
                ("created_at", "desc", cursor_datetime(cursor_payload, "created_at")),
                ("id", "desc", cursor_uuid(cursor_payload, "id")),
            ]))
        response = call_supabase(
            lambda: (
                query
                .order("created_at", desc=True)
                .order("id", desc=True)
                .limit(limit + 1)
                .execute()
            ),
            operation_name="received mentor consultation order list",
        )
        rows = list(response.data or [])
        has_more = len(rows) > limit
        page_rows = rows[:limit]
        next_cursor = None
        if has_more and page_rows:
            anchor = page_rows[-1]
            next_cursor = encode_page_cursor("mentor_received_orders", {
                **cursor_context,
                "created_at": str(anchor.get("created_at") or ""),
                "id": str(anchor.get("id") or ""),
            })
        refreshed_rows = [_refresh_pending_accept_status(supabase, row) for row in page_rows]
        return MentorConsultationOrderListResponse(
            items=[_serialize_order_item(row) for row in refreshed_rows],
            count=int(response.count or len(page_rows)),
            next_cursor=next_cursor,
            has_more=has_more,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Received mentor consultation orders unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="待处理咨询暂时不可用") from exc


@router.get("/mentors", response_model=MentorPublicListResponse)
def list_public_mentors(
    keyword: str | None = Query(default=None, max_length=120),
    exam_type: str | None = Query(default=None, max_length=20),
    admission_year: int | None = Query(default=None, ge=2000, le=2100),
    admission_year_before: int | None = Query(default=None, ge=2000, le=2100),
    availability: str = Query(default="all", max_length=20),
    min_price: int | None = Query(default=None, ge=0, le=100000),
    max_price: int | None = Query(default=None, ge=0, le=100000),
    sort: str = Query(default="recommended", max_length=32),
    limit: int = Query(default=30, ge=1, le=PUBLIC_MENTOR_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> MentorPublicListResponse:
    normalized_exam_type = str(exam_type or "").strip()
    normalized_availability = str(availability or "all").strip().lower()
    normalized_sort = str(sort or "recommended").strip().lower()
    if normalized_exam_type and normalized_exam_type not in PUBLIC_MENTOR_EXAM_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的考试类别")
    if normalized_availability not in PUBLIC_MENTOR_AVAILABILITIES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的咨询状态")
    if normalized_sort not in PUBLIC_MENTOR_SORTS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的排序方式")
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="价格区间不正确")

    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: (
                supabase.table("mentor_profiles")
                .select(PUBLIC_PROFILE_FIELDS)
                .eq("is_published", True)
                .eq("verification_status", "verified")
                .limit(PUBLIC_MENTOR_MAX_LIMIT)
                .execute()
            ),
            operation_name="public mentor profile list",
        )
        rows = list(response.data or [])
        normalized_keyword = _normalise_keyword(keyword)
        rows = [row for row in rows if _matches_keyword(row, normalized_keyword)]
        if normalized_exam_type:
            rows = [row for row in rows if row.get("exam_type") == normalized_exam_type]
        if admission_year is not None:
            rows = [row for row in rows if int(row.get("admission_year") or 0) == admission_year]
        if admission_year_before is not None:
            rows = [row for row in rows if int(row.get("admission_year") or 0) <= admission_year_before]
        if normalized_availability == "online":
            rows = [row for row in rows if row.get("online_status") == "online"]
        elif normalized_availability == "bookable":
            rows = [
                row for row in rows
                if bool(row.get("accepts_booking")) and row.get("online_status") != "online"
            ]
        if min_price is not None:
            rows = [row for row in rows if int(row.get("price_cents") or 0) >= min_price * 100]
        if max_price is not None:
            rows = [row for row in rows if int(row.get("price_cents") or 0) <= max_price * 100]

        rows = _sort_mentors(rows, normalized_sort)
        count = len(rows)
        page_rows = rows[offset:offset + limit]
        mentor_ids = [str(row.get("id") or "") for row in page_rows]
        skills_by_mentor = fetch_mentor_skills(supabase, mentor_ids)
        aggregates_by_mentor = fetch_mentor_aggregates(supabase, mentor_ids)
        return MentorPublicListResponse(
            items=[
                serialize_mentor_public(
                    row,
                    skills_by_mentor.get(str(row.get("id") or ""), []),
                    aggregates_by_mentor.get(str(row.get("id") or "")),
                )
                for row in page_rows
            ],
            count=count,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Public mentor list unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="前辈咨询数据暂时不可用，请确认已应用前辈咨询数据库迁移",
        ) from exc


@router.get("/mentors/{mentor_id}", response_model=MentorPublicDetailResponse)
def get_public_mentor(mentor_id: str) -> MentorPublicDetailResponse:
    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: (
                supabase.table("mentor_profiles")
                .select(PUBLIC_PROFILE_FIELDS)
                .eq("id", mentor_id)
                .eq("is_published", True)
                .eq("verification_status", "verified")
                .limit(1)
                .execute()
            ),
            operation_name="public mentor profile detail",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到可咨询的前辈")

        mentor_row = response.data[0]
        skills_by_mentor = fetch_mentor_skills(supabase, [mentor_id])
        aggregates_by_mentor = fetch_mentor_aggregates(supabase, [mentor_id])
        reviews_response = call_supabase(
            lambda: (
                supabase.table("mentor_reviews")
                .select("id,reviewer_display_name,rating,content,created_at")
                .eq("mentor_id", mentor_id)
                .eq("is_published", True)
                .order("created_at", desc=True)
                .limit(20)
                .execute()
            ),
            operation_name="public mentor review list",
        )
        slots_response = call_supabase(
            lambda: (
                supabase.table("mentor_availability_slots")
                .select("id,starts_at,ends_at,price_cents,status")
                .eq("mentor_id", mentor_id)
                .in_("status", ["available", "booked"])
                .gte("ends_at", _utc_now().isoformat())
                .order("starts_at")
                .limit(60)
                .execute()
            ),
            operation_name="public mentor availability list",
        )
        return MentorPublicDetailResponse(
            mentor=serialize_mentor_public(
                mentor_row,
                skills_by_mentor.get(mentor_id, []),
                aggregates_by_mentor.get(mentor_id),
            ),
            reviews=[serialize_mentor_review(row) for row in (reviews_response.data or [])],
            available_slots=[serialize_mentor_slot(row) for row in (slots_response.data or [])],
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Public mentor detail unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="前辈咨询数据暂时不可用，请确认已应用前辈咨询数据库迁移",
        ) from exc


@router.get("/me/favorites", response_model=MentorFavoriteListResponse)
def list_my_mentor_favorites(
    user_id: str = Depends(get_current_user_id),
) -> MentorFavoriteListResponse:
    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: (
                supabase.table("mentor_favorites")
                .select("mentor_id,created_at", count="exact")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(ORDER_LIST_MAX_LIMIT)
                .execute()
            ),
            operation_name="mentor favorite list",
        )
        rows = response.data or []
        return MentorFavoriteListResponse(
            items=[MentorFavoriteItem(
                mentor_id=str(row.get("mentor_id") or ""),
                created_at=row.get("created_at") or None,
            ) for row in rows],
            count=int(response.count or len(rows)),
        )
    except Exception as exc:
        logger.warning("Mentor favorite list unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="收藏状态暂时不可用") from exc


@router.post("/mentors/{mentor_id}/favorite", response_model=MentorFavoriteToggleResponse)
def toggle_mentor_favorite(
    mentor_id: UUID,
    user_id: str = Depends(get_current_user_id),
) -> MentorFavoriteToggleResponse:
    normalized_mentor_id = str(mentor_id)
    supabase = get_supabase_admin()
    try:
        _get_order_mentor_or_404(supabase, normalized_mentor_id)
        existing_response = call_supabase(
            lambda: (
                supabase.table("mentor_favorites")
                .select("mentor_id")
                .eq("user_id", user_id)
                .eq("mentor_id", normalized_mentor_id)
                .limit(1)
                .execute()
            ),
            operation_name="mentor favorite lookup",
        )
        if existing_response.data:
            call_supabase(
                lambda: (
                    supabase.table("mentor_favorites")
                    .delete()
                    .eq("user_id", user_id)
                    .eq("mentor_id", normalized_mentor_id)
                    .execute()
                ),
                operation_name="mentor favorite remove",
            )
            return MentorFavoriteToggleResponse(mentor_id=normalized_mentor_id, is_favorited=False)

        call_supabase(
            lambda: supabase.table("mentor_favorites").insert({
                "user_id": user_id,
                "mentor_id": normalized_mentor_id,
            }).execute(),
            operation_name="mentor favorite create",
        )
        return MentorFavoriteToggleResponse(mentor_id=normalized_mentor_id, is_favorited=True)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Mentor favorite update failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="收藏操作暂时不可用") from exc


@router.get(
    "/payment-capability",
    response_model=MentorConsultationPaymentCapabilityResponse,
)
def get_mentor_consultation_payment_capability() -> MentorConsultationPaymentCapabilityResponse:
    settings = get_settings()
    demo_enabled = bool(settings.mentor_consultation_demo_payment_enabled)
    real_enabled = _real_payment_ready()
    if demo_enabled:
        payment_mode = "demo"
        message = "当前仅启用本地 Demo 咨询流程，所有金额都与真实资金隔离。"
    elif real_enabled:
        payment_mode = "real"
        message = "支付渠道已就绪，支付结果以渠道回调为准。"
    else:
        payment_mode = "disabled"
        message = "微信支付商户资质审核中，收费咨询、退款打款和提现入口暂未开放。"
    return MentorConsultationPaymentCapabilityResponse(
        order_creation_enabled=bool(demo_enabled or real_enabled),
        real_payment_enabled=real_enabled,
        demo_payment_enabled=demo_enabled,
        payment_mode=payment_mode,
        provider=("demo" if demo_enabled else _configured_payment_provider()),
        checkout_configured=bool(real_enabled),
        withdrawal_enabled=bool(real_enabled and settings.wallet_withdrawal_enabled),
        service_rules_version=settings.mentor_consultation_service_rules_version,
        message=message,
    )


@router.post(
    "/orders",
    response_model=MentorConsultationOrderItem,
    status_code=status.HTTP_201_CREATED,
)
def create_mentor_consultation_order(
    payload: MentorConsultationOrderCreateRequest,
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationOrderItem:
    _assert_order_creation_enabled()
    mentor_id = str(payload.mentor_id)
    client_order_id = str(payload.client_order_id or "").strip()
    consultation_type = payload.consultation_type
    rules_version = str(payload.service_rules_version or "").strip()
    if not payload.service_rules_accepted or rules_version != get_settings().mentor_consultation_service_rules_version:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="请阅读并同意当前版本的咨询服务与纠纷处理规则后再提交订单",
        )
    questionnaire = payload.questionnaire.model_dump()
    for required_field in ("name", "school", "major"):
        questionnaire[required_field] = str(questionnaire.get(required_field) or "").strip()
        if not questionnaire[required_field]:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="请完整填写咨询基本信息")
    questionnaire["grade"] = str(questionnaire.get("grade") or "其他").strip()[:40] or "其他"
    questionnaire["question"] = str(questionnaire.get("question") or "").strip()
    normalized_slot_id = str(payload.slot_id) if payload.slot_id is not None else None
    request_fingerprint = _order_request_fingerprint(
        mentor_id=mentor_id,
        consultation_type=consultation_type,
        slot_id=normalized_slot_id,
        questionnaire=questionnaire,
        service_rules_version=rules_version,
    )
    questionnaire["service_rules_version"] = rules_version
    questionnaire["service_rules_accepted_at"] = _utc_now().isoformat()

    supabase = get_supabase_admin()
    try:
        existing_response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_orders")
                .select(CONSULTATION_ORDER_FIELDS)
                .eq("applicant_user_id", user_id)
                .eq("client_order_id", client_order_id)
                .limit(1)
                .execute()
            ),
            operation_name="consultation idempotent order lookup",
        )
        if existing_response.data:
            existing_order = existing_response.data[0]
            if str(existing_order.get("request_fingerprint") or "") != request_fingerprint:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="该提交标识已用于另一份咨询内容，请返回后重新发起",
                )
            return _serialize_order_item(existing_order)

        mentor = _get_order_mentor_or_404(supabase, mentor_id)
        if str(mentor.get("owner_user_id") or "") == user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="前辈本人不能创建自己的咨询订单")

        slot: dict | None = None
        if consultation_type == "instant":
            if payload.slot_id is not None:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="即时咨询不需要预约时段")
            if str(mentor.get("online_status") or "") != "online":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该前辈当前不在线，请选择预约咨询")
            price_cents = int(mentor.get("price_cents") or 0)
        else:
            if payload.slot_id is None:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="请选择一个预约时段")
            if not bool(mentor.get("accepts_booking")):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该前辈暂未开放预约")
            slot = _get_slot_or_404(supabase, str(payload.slot_id))
            if str(slot.get("mentor_id") or "") != mentor_id:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="预约时段与前辈不匹配")
            starts_at = _as_utc_datetime(slot.get("starts_at"))
            if starts_at is not None and starts_at <= _utc_now():
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该预约时段已过期，请重新选择")
            price_cents = int(
                slot.get("price_cents")
                if slot.get("price_cents") is not None
                else mentor.get("price_cents") or 0
            )

        order_no = _new_order_no()
        hold_minutes = max(5, min(int(get_settings().mentor_consultation_payment_hold_minutes or 15), 60))
        payment_expires_at = _utc_now() + timedelta(minutes=hold_minutes)
        response = call_supabase(
            lambda: supabase.rpc(
                "create_mentor_consultation_order_with_hold",
                {
                    "p_order_no": order_no,
                    "p_applicant_user_id": user_id,
                    "p_mentor_id": mentor_id,
                    "p_slot_id": normalized_slot_id,
                    "p_consultation_type": consultation_type,
                    "p_questionnaire": questionnaire,
                    "p_price_cents": max(0, price_cents),
                    "p_consultation_window_minutes": int(mentor.get("consultation_window_minutes") or 60),
                    "p_client_order_id": client_order_id,
                    "p_request_fingerprint": request_fingerprint,
                    "p_payment_mode": _payment_mode(),
                    "p_payment_expires_at": payment_expires_at.isoformat(),
                },
            ).execute(),
            operation_name="consultation order create",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="咨询订单创建失败")
        created_order = response.data[0]
        if str(created_order.get("order_no") or "") == order_no:
            _insert_order_event(
                supabase,
                str(created_order.get("id") or ""),
                event_type="consultation_order_created",
                actor_role="applicant",
                actor_user_id=user_id,
                details={
                    "client_order_id": client_order_id,
                    "consultation_type": consultation_type,
                    "slot_id": normalized_slot_id,
                    "price_cents": max(0, price_cents),
                    "payment_mode": _payment_mode(),
                    "payment_expires_at": payment_expires_at.isoformat(),
                    "service_rules_version": rules_version,
                    "service_rules_accepted": True,
                },
            )
        return _serialize_order_item(created_order)
    except HTTPException:
        raise
    except Exception as exc:
        mapped_error = _map_order_rpc_error(exc)
        if mapped_error:
            raise mapped_error from exc
        logger.warning("Consultation order create failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="咨询订单创建失败，请确认第二批数据库迁移已执行",
        ) from exc


@router.post("/orders/{order_id}/payment-intent", response_model=MentorConsultationPaymentIntentResponse)
def create_mentor_consultation_payment_intent(
    order_id: UUID,
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationPaymentIntentResponse:
    """Create a payment hand-off without treating order creation as payment success."""

    normalized_order_id = str(order_id)
    supabase = get_supabase_admin()
    try:
        order, participant_role, _ = _get_order_participant(supabase, normalized_order_id, user_id)
        if participant_role != "applicant":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅咨询发起人可以创建支付订单")
        order = _refresh_pending_accept_status(supabase, order)
        order_payment_mode = str(order.get("payment_mode") or "real")
        if order_payment_mode == "demo":
            if not get_settings().mentor_consultation_demo_payment_enabled:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该 Demo 订单已停止受理")
        elif not _real_payment_ready():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="微信支付商户资质审核中，当前不会生成真实支付请求。",
            )
        current_status = str(order.get("order_status") or "")
        current_payment_status = str(order.get("payment_status") or "")
        payment_reference = _build_payment_reference(order)
        if current_status in {"pending_accept", "accepted", "booked", "in_progress", "completed"} and current_payment_status == "paid":
            return MentorConsultationPaymentIntentResponse(
                order_id=normalized_order_id,
                order_no=str(order.get("order_no") or ""),
                provider=_configured_payment_provider(),
                provider_order_id=payment_reference,
                amount_cents=max(0, int(order.get("price_cents") or 0)),
                status="paid",
                checkout_url=None,
                message="该咨询订单已完成支付确认。",
            )
        _assert_order_status(order, {"pending_payment"}, "该订单当前无法创建支付订单")
        if current_payment_status not in {"unpaid", "failed"}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该订单当前支付状态不可继续支付")
        response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_orders")
                .update({"payment_status": "unpaid", "payment_reference": payment_reference})
                .eq("id", normalized_order_id)
                .eq("applicant_user_id", user_id)
                .eq("order_status", "pending_payment")
                .in_("payment_status", ["unpaid", "failed"])
                .execute()
            ),
            operation_name="consultation payment intent create",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="订单状态已变化，请刷新后重试")
        updated_order = response.data[0]
        checkout_url = _build_checkout_url(updated_order, payment_reference)
        _insert_order_event(
            supabase,
            normalized_order_id,
            event_type="consultation_payment_intent_created",
            actor_role="applicant",
            actor_user_id=user_id,
            details={
                "provider": _configured_payment_provider(),
                "payment_reference": payment_reference,
                "price_cents": max(0, int(updated_order.get("price_cents") or 0)),
                "checkout_configured": bool(checkout_url),
            },
        )
        return MentorConsultationPaymentIntentResponse(
            order_id=normalized_order_id,
            order_no=str(updated_order.get("order_no") or ""),
            provider=_configured_payment_provider(),
            provider_order_id=payment_reference,
            amount_cents=max(0, int(updated_order.get("price_cents") or 0)),
            status="pending",
            checkout_url=checkout_url,
            message=(
                "支付订单已生成，完成支付后系统会自动确认。"
                if checkout_url
                else "支付订单已生成，当前尚未配置支付跳转；订单会保持待支付，平台不会将其标记为已支付。"
            ),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Consultation payment intent create failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="支付订单暂时不可用") from exc


@router.post("/payments/webhook", response_model=MentorConsultationPaymentWebhookResponse)
def handle_mentor_consultation_payment_webhook(
    payload: MentorConsultationPaymentWebhookRequest,
    x_payment_webhook_secret: Annotated[str | None, Header()] = None,
) -> MentorConsultationPaymentWebhookResponse:
    """Apply confirmed payment/refund results from the configured payment channel.

    The provider must send a stable event id.  Repeated delivery is recognized by
    the already-transitioned order and returns the same current order instead of
    performing a second state change.
    """

    settings = get_settings()
    if not _real_payment_ready():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="真实咨询支付渠道尚未启用")
    expected_secret = str(settings.payment_webhook_secret or "")
    if not expected_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="支付回调尚未配置")
    if not x_payment_webhook_secret or not secrets.compare_digest(x_payment_webhook_secret, expected_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="支付回调校验失败")
    expected_provider = _configured_payment_provider()
    if expected_provider == "unconfigured":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="咨询支付渠道尚未配置")
    if payload.provider != expected_provider:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="支付渠道与当前订单配置不匹配")

    supabase = get_supabase_admin()
    try:
        lookup = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_orders")
                .select(CONSULTATION_ORDER_FIELDS)
                .eq("order_no", payload.order_no)
                .limit(1)
                .execute()
            ),
            operation_name="consultation payment callback order lookup",
        )
        if not lookup.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到对应的咨询订单")
        order = _refresh_pending_accept_status(supabase, lookup.data[0])
        order_id = str(order.get("id") or "")
        if str(order.get("payment_mode") or "real") != "real":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Demo 订单不接受真实支付回调")
        expected_amount = max(0, int(order.get("price_cents") or 0))
        if int(payload.amount_cents) != expected_amount:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="支付金额与咨询订单不一致")
        existing_reference = str(order.get("payment_reference") or "")
        if existing_reference and existing_reference != payload.payment_reference:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="支付流水号与咨询订单不一致")

        callback_details = {
            "provider": payload.provider,
            "provider_event_id": payload.provider_event_id,
            "payment_reference": payload.payment_reference,
            "amount_cents": int(payload.amount_cents),
        }
        current_payment_status = str(order.get("payment_status") or "")
        if payload.status == "paid":
            if current_payment_status == "paid" and str(order.get("payment_reference") or "") == payload.payment_reference:
                return MentorConsultationPaymentWebhookResponse(
                    detail="支付结果已处理",
                    order=_serialize_order_item(order),
                    idempotent=True,
                )
            try:
                paid_order = _mark_mentor_consultation_order_paid(
                    supabase,
                    order,
                    payment_reference=payload.payment_reference,
                    operation_name="consultation payment callback confirm",
                )
            except HTTPException:
                refreshed_order = _get_order_or_404(supabase, order_id)
                if str(refreshed_order.get("payment_status") or "") == "paid" and str(refreshed_order.get("payment_reference") or "") == payload.payment_reference:
                    return MentorConsultationPaymentWebhookResponse(
                        detail="支付结果已处理",
                        order=_serialize_order_item(refreshed_order),
                        idempotent=True,
                    )
                refreshed_payment_status = str(refreshed_order.get("payment_status") or "")
                if (
                    str(refreshed_order.get("order_status") or "") in {"pending_payment", "cancelled"}
                    and refreshed_payment_status in {"unpaid", "failed", "refunding"}
                ):
                    already_registered = refreshed_payment_status == "refunding"
                    late_order = _register_late_consultation_payment_for_refund(
                        supabase,
                        refreshed_order,
                        payment_reference=payload.payment_reference,
                    )
                    if not already_registered:
                        record_consultation_payment(
                            supabase,
                            {**late_order, "payment_status": "paid"},
                        )
                        _insert_order_event(
                            supabase,
                            order_id,
                            event_type="consultation_payment_confirmed_after_hold_expiry",
                            actor_role="system",
                            details=callback_details,
                        )
                        _insert_order_event(
                            supabase,
                            order_id,
                            event_type="consultation_refund_requested",
                            actor_role="system",
                            details={
                                "refund_amount_cents": int(late_order.get("refund_amount_cents") or 0),
                                "refund_reference": late_order.get("refund_reference"),
                                "reason": "payment_hold_expired",
                            },
                        )
                        _insert_system_message(
                            supabase,
                            order_id,
                            "支付结果到达时订单预占已结束，平台已自动关闭订单并提交全额原路退款。",
                        )
                    return MentorConsultationPaymentWebhookResponse(
                        detail="支付已确认，但订单预占已结束；全额退款处理中",
                        order=_serialize_order_item(late_order),
                        idempotent=already_registered,
                    )
                raise
            _insert_order_event(
                supabase,
                order_id,
                event_type="consultation_payment_confirmed",
                actor_role="system",
                details=callback_details,
            )
            _insert_system_message(
                supabase,
                order_id,
                (
                    "平台已确认咨询费用，咨询请求已发送给前辈；请等待前辈在 10 分钟内确认接单。"
                    if str(paid_order.get("consultation_type") or "") == "instant"
                    else "平台已确认预约咨询费用，前辈可在预约时段开始咨询。"
                ),
            )
            return MentorConsultationPaymentWebhookResponse(
                detail="支付确认成功",
                order=_serialize_order_item(paid_order),
            )

        if payload.status == "failed":
            if current_payment_status == "failed" and not order.get("refund_reference") and existing_reference == payload.payment_reference:
                return MentorConsultationPaymentWebhookResponse(
                    detail="支付失败结果已处理",
                    order=_serialize_order_item(order),
                    idempotent=True,
                )
            _assert_order_status(order, {"pending_payment"}, "该订单当前无法更新支付结果")
            response = call_supabase(
                lambda: (
                    supabase.table("mentor_consultation_orders")
                    .update({"payment_status": "failed", "payment_reference": payload.payment_reference})
                    .eq("id", order_id)
                    .eq("order_status", "pending_payment")
                    .in_("payment_status", ["unpaid", "failed"])
                    .execute()
                ),
                operation_name="consultation payment callback failure",
            )
            if not response.data:
                refreshed_order = _get_order_or_404(supabase, order_id)
                if (
                    str(refreshed_order.get("payment_status") or "") == "failed"
                    and not refreshed_order.get("refund_reference")
                    and str(refreshed_order.get("payment_reference") or "") == payload.payment_reference
                ):
                    return MentorConsultationPaymentWebhookResponse(
                        detail="支付失败结果已处理",
                        order=_serialize_order_item(refreshed_order),
                        idempotent=True,
                    )
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="订单状态已变化，请刷新后重试")
            callback_details["failure_reason"] = str(payload.failure_reason or "") or None
            _insert_order_event(supabase, order_id, event_type="consultation_payment_failed", actor_role="system", details=callback_details)
            _insert_system_message(supabase, order_id, "本次支付未完成，订单仍处于待支付状态；请重新发起支付或取消订单。")
            return MentorConsultationPaymentWebhookResponse(
                detail="已记录支付失败结果",
                order=_serialize_order_item(response.data[0]),
            )

        expected_refund_amount = max(0, int(order.get("refund_amount_cents") or 0))
        callback_refund_amount = int(payload.refund_amount_cents if payload.refund_amount_cents is not None else expected_refund_amount)
        if not order.get("refund_reference") or payload.refund_reference != str(order.get("refund_reference") or ""):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="退款流水号与咨询订单不一致")
        if callback_refund_amount != expected_refund_amount:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="退款金额与咨询订单不一致")
        callback_details.update({"refund_reference": payload.refund_reference, "refund_amount_cents": callback_refund_amount})
        if payload.status == "refunded":
            if current_payment_status == "refunded":
                return MentorConsultationPaymentWebhookResponse(
                    detail="退款结果已处理",
                    order=_serialize_order_item(order),
                    idempotent=True,
                )
            if current_payment_status != "refunding":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该订单当前不处于退款处理中")
            response = call_supabase(
                lambda: (
                    supabase.table("mentor_consultation_orders")
                    .update({"payment_status": "refunded"})
                    .eq("id", order_id)
                    .eq("payment_status", "refunding")
                    .execute()
                ),
                operation_name="consultation refund callback confirm",
            )
            if not response.data:
                refreshed_order = _get_order_or_404(supabase, order_id)
                if str(refreshed_order.get("payment_status") or "") == "refunded" and str(refreshed_order.get("refund_reference") or "") == payload.refund_reference:
                    return MentorConsultationPaymentWebhookResponse(
                        detail="退款结果已处理",
                        order=_serialize_order_item(refreshed_order),
                        idempotent=True,
                    )
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="订单状态已变化，请刷新后重试")
            _insert_order_event(supabase, order_id, event_type="consultation_refund_completed", actor_role="system", details=callback_details)
            _insert_system_message(supabase, order_id, f"平台已确认退款完成，退款金额 ¥{callback_refund_amount / 100:.2f} 将原路退回。")
            record_consultation_refund(supabase, response.data[0])
            return MentorConsultationPaymentWebhookResponse(
                detail="退款确认成功",
                order=_serialize_order_item(response.data[0]),
            )

        if current_payment_status == "failed" and order.get("refund_reference"):
            return MentorConsultationPaymentWebhookResponse(
                detail="退款异常结果已处理",
                order=_serialize_order_item(order),
                idempotent=True,
            )
        if current_payment_status != "refunding":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该订单当前不处于退款处理中")
        response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_orders")
                .update({"payment_status": "failed"})
                .eq("id", order_id)
                .eq("payment_status", "refunding")
                .execute()
            ),
            operation_name="consultation refund callback failure",
        )
        if not response.data:
            refreshed_order = _get_order_or_404(supabase, order_id)
            if str(refreshed_order.get("payment_status") or "") == "failed" and str(refreshed_order.get("refund_reference") or "") == payload.refund_reference:
                return MentorConsultationPaymentWebhookResponse(
                    detail="退款异常结果已处理",
                    order=_serialize_order_item(refreshed_order),
                    idempotent=True,
                )
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="订单状态已变化，请刷新后重试")
        callback_details["failure_reason"] = str(payload.failure_reason or "") or None
        _insert_order_event(supabase, order_id, event_type="consultation_refund_failed", actor_role="system", details=callback_details)
        _insert_system_message(supabase, order_id, "退款处理出现异常，平台已收到提醒并会继续跟进；你可以在平台处理进度查看结果。")
        return MentorConsultationPaymentWebhookResponse(
            detail="已记录退款异常",
            order=_serialize_order_item(response.data[0]),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Consultation payment webhook failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="支付回调处理暂时不可用") from exc


@router.post("/orders/{order_id}/mock-pay", response_model=MentorConsultationOrderItem)
def mock_pay_mentor_consultation_order(
    order_id: UUID,
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationOrderItem:
    if not get_settings().mentor_consultation_demo_payment_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="咨询服务当前未启用")
    normalized_order_id = str(order_id)
    supabase = get_supabase_admin()
    try:
        order, participant_role, _ = _get_order_participant(supabase, normalized_order_id, user_id)
        if participant_role != "applicant":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅咨询发起人可以确认本次咨询")
        order = _refresh_pending_accept_status(supabase, order)
        if str(order.get("payment_mode") or "real") != "demo":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前订单不属于本地 Demo 流程")
        order_status = str(order.get("order_status") or "")
        payment_status = str(order.get("payment_status") or "")
        is_no_payment_order = _is_demo_payment_reference(order.get("payment_reference"))
        if payment_status == "paid" and is_no_payment_order and order_status in {
            "pending_accept", "accepted", "booked", "in_progress", "completed"
        }:
            return _serialize_order_item(order)
        _assert_order_status(order, {"pending_payment"}, "该订单当前无法确认")
        consultation_type = str(order.get("consultation_type") or "instant")
        paid_order = _mark_mentor_consultation_order_paid(
            supabase,
            order,
            payment_reference=f"DEMO-{str(order.get('order_no') or '')}-{uuid4().hex[:6].upper()}",
            operation_name="consultation local no-payment confirmation",
        )
        _insert_order_event(
            supabase,
            normalized_order_id,
            event_type="consultation_demo_payment_recorded",
            actor_role="applicant",
            actor_user_id=user_id,
            details={
                "payment_reference": paid_order.get("payment_reference"),
                "consultation_type": consultation_type,
                "price_cents": int(order.get("price_cents") or 0),
                "order_status": str(paid_order.get("order_status") or ""),
                "payment_exempt": True,
            },
        )
        _insert_system_message(
            supabase,
            normalized_order_id,
            (
                "已确认本次咨询，咨询请求已发送给前辈；请等待前辈在 10 分钟内确认接单。"
                if consultation_type == "instant"
                else "已确认本次预约，前辈可在预约时段开始咨询。"
            ),
        )
        return _serialize_order_item(paid_order)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Consultation no-payment confirmation failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="咨询服务暂时不可用") from exc


@router.post("/orders/{order_id}/local-rehearsal-complete", response_model=MentorConsultationOrderItem)
def complete_mentor_consultation_local_rehearsal(
    order_id: UUID,
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationOrderItem:
    """Close a local rehearsal without requiring a second account confirmation."""

    if not get_settings().mentor_consultation_demo_payment_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="咨询服务当前未启用")
    normalized_order_id = str(order_id)
    supabase = get_supabase_admin()
    try:
        order, participant_role, _ = _get_order_participant(supabase, normalized_order_id, user_id)
        if participant_role != "applicant":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅咨询发起人可以结束本次咨询")
        order = _refresh_pending_accept_status(supabase, order)
        if str(order.get("order_status") or "") == "completed":
            return _serialize_order_item(order)
        if not _is_demo_payment_reference(order.get("payment_reference")):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前订单暂不支持该操作")
        _assert_order_status(order, {"in_progress"}, "该订单当前尚未开始咨询")

        now_iso = _utc_now().isoformat()
        response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_orders")
                .update({
                    "order_status": "completed",
                    "applicant_completion_confirmed_at": now_iso,
                    "mentor_completion_confirmed_at": now_iso,
                    "ended_at": now_iso,
                })
                .eq("id", normalized_order_id)
                .eq("order_status", "in_progress")
                .execute()
            ),
            operation_name="consultation local rehearsal complete",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="订单状态已变化，请刷新后重试")
        completed_order = response.data[0]
        _insert_order_event(
            supabase,
            normalized_order_id,
            event_type="completion_confirmed",
            actor_role="applicant",
            actor_user_id=user_id,
            details={"mode": "local_rehearsal", "both_parties_confirmed": True},
        )
        _insert_order_event(
            supabase,
            normalized_order_id,
            event_type="consultation_completed",
            actor_role="system",
            details={"completion": "local_rehearsal"},
        )
        _insert_system_message(
            supabase,
            normalized_order_id,
            "本次咨询已结束并进入评价阶段；聊天、问题反馈和后台处理记录会继续保留。",
        )
        record_consultation_income_pending(supabase, completed_order)
        return _serialize_order_item(completed_order)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Consultation local rehearsal completion failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="结束咨询暂时不可用") from exc


@router.post("/orders/{order_id}/cancel", response_model=MentorConsultationOrderItem)
def cancel_mentor_consultation_order(
    order_id: UUID,
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationOrderItem:
    """Let either participant end an unstarted consultation with an auditable result."""

    normalized_order_id = str(order_id)
    supabase = get_supabase_admin()
    try:
        order, participant_role, _ = _get_order_participant(supabase, normalized_order_id, user_id)
        order = _refresh_pending_accept_status(supabase, order)
        order_status = str(order.get("order_status") or "")
        if order_status == "cancelled":
            return _serialize_order_item(order)
        allowed_statuses = (
            {"pending_payment", "pending_accept", "accepted", "booked"}
            if participant_role == "applicant"
            else {"accepted", "booked"}
        )
        _assert_order_status(
            order,
            allowed_statuses,
            (
                "即时咨询请先选择暂不接受；已开始或已结束的咨询请通过平台介入处理"
                if participant_role == "mentor"
                else "咨询已开始或已结束，请通过平台介入处理"
            ),
        )

        paid = str(order.get("payment_status") or "") == "paid"
        now_iso = _utc_now().isoformat()
        next_payment_status = _refund_payment_status_for_order(order) if paid else "unpaid"
        update_data = {
            "order_status": "cancelled",
            "payment_status": next_payment_status,
            "ended_at": now_iso,
            "refund_amount_cents": int(order.get("price_cents") or 0) if paid else 0,
            "refund_reference": (
                _new_refund_reference("CANCEL", order)
                if paid else None
            ),
        }
        update_query = (
            supabase.table("mentor_consultation_orders")
            .update(update_data)
            .eq("id", normalized_order_id)
            .eq("order_status", order_status)
        )
        # The applicant id is a useful database-level guard for a user
        # cancellation.  A mentor is verified through the current owner binding
        # above, because that owner relationship lives on mentor_profiles.
        if participant_role == "applicant":
            update_query = update_query.eq("applicant_user_id", user_id)
        response = call_supabase(
            update_query.execute,
            operation_name="consultation order cancel",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="订单状态已变化，请刷新后重试")
        release_terminal_mentor_booking_slot(supabase, order)
        cancelled_by_mentor = participant_role == "mentor"
        _insert_system_message(
            supabase,
            normalized_order_id,
            (
                "认证前辈因暂时无法服务，已取消本次咨询。"
                if cancelled_by_mentor
                else "咨询订单已由咨询用户取消。"
            ) + (
                "测试退款已完成。" if next_payment_status == "refunded" else "费用已进入退款处理，完成后会自动同步。"
                if paid
                else ""
            ) + (
                "如有异议，可在平台处理进度提交问题反馈。"
                if cancelled_by_mentor
                else ""
            ),
        )
        _insert_order_event(
            supabase,
            normalized_order_id,
            event_type=f"order_cancelled_by_{participant_role}",
            actor_role=participant_role,
            actor_user_id=user_id,
            details={
                "was_paid": paid,
                "payment_status": next_payment_status,
                "refund_amount_cents": update_data["refund_amount_cents"],
                "consultation_type": str(order.get("consultation_type") or ""),
            },
        )
        if paid:
            _insert_order_event(
                supabase,
                normalized_order_id,
                event_type=("consultation_refund_completed" if next_payment_status == "refunded" else "consultation_refund_requested"),
                actor_role=participant_role,
                actor_user_id=user_id,
                details={
                    "refund_amount_cents": update_data["refund_amount_cents"],
                    "refund_reference": update_data["refund_reference"],
                    "reason": "order_cancelled",
                },
            )
        cancelled_order = response.data[0]
        if str(cancelled_order.get("payment_status") or "") == "refunded":
            record_consultation_refund(supabase, cancelled_order)
        if cancelled_by_mentor:
            _notify_consultation_applicant_order_status(
                supabase,
                order=cancelled_order,
                event="cancelled",
            )
        return _serialize_order_item(cancelled_order)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Consultation order cancel failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="取消咨询订单失败") from exc


@router.get("/me/orders", response_model=MentorConsultationOrderListResponse)
def list_my_mentor_consultation_orders(
    limit: int = Query(default=20, ge=1, le=ORDER_LIST_MAX_LIMIT),
    cursor: str | None = Query(default=None, max_length=2048),
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationOrderListResponse:
    cursor_payload = decode_page_cursor(cursor, kind="mentor_applicant_orders")
    supabase = get_supabase_admin()
    try:
        query = (
            supabase.table("mentor_consultation_orders")
            .select(CONSULTATION_ORDER_FIELDS, count="exact")
            .eq("applicant_user_id", user_id)
        )
        if cursor_payload:
            query = query.or_(build_keyset_filter([
                ("created_at", "desc", cursor_datetime(cursor_payload, "created_at")),
                ("id", "desc", cursor_uuid(cursor_payload, "id")),
            ]))
        response = call_supabase(
            lambda: (
                query
                .order("created_at", desc=True)
                .order("id", desc=True)
                .limit(limit + 1)
                .execute()
            ),
            operation_name="my consultation order list",
        )
        rows = list(response.data or [])
        has_more = len(rows) > limit
        page_rows = rows[:limit]
        next_cursor = None
        if has_more and page_rows:
            anchor = page_rows[-1]
            next_cursor = encode_page_cursor("mentor_applicant_orders", {
                "created_at": str(anchor.get("created_at") or ""),
                "id": str(anchor.get("id") or ""),
            })
        refreshed_rows = [_refresh_pending_accept_status(supabase, row) for row in page_rows]
        return MentorConsultationOrderListResponse(
            items=[_serialize_order_item(row) for row in refreshed_rows],
            count=int(response.count or len(page_rows)),
            next_cursor=next_cursor,
            has_more=has_more,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("My consultation order list unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="咨询订单暂时不可用") from exc


@router.get("/orders/{order_id}", response_model=MentorConsultationOrderItem)
def get_mentor_consultation_order(
    order_id: UUID,
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationOrderItem:
    supabase = get_supabase_admin()
    try:
        order, _, _ = _get_order_participant(supabase, str(order_id), user_id)
        return _serialize_order_item(_refresh_pending_accept_status(supabase, order))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Consultation order read failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="咨询订单暂时不可用") from exc


@router.post("/orders/{order_id}/decision", response_model=MentorConsultationOrderItem)
def decide_mentor_consultation_order(
    order_id: UUID,
    payload: MentorConsultationDecisionRequest,
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationOrderItem:
    normalized_order_id = str(order_id)
    supabase = get_supabase_admin()
    try:
        order, participant_role, _ = _get_order_participant(supabase, normalized_order_id, user_id)
        if participant_role != "mentor":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅已绑定账号的前辈可以处理接单")
        order = _refresh_pending_accept_status(supabase, order)
        _assert_order_status(order, {"pending_accept"}, "该订单当前无法处理接单")

        now = _utc_now()
        now_iso = now.isoformat()
        rejection_reason = str(payload.reason or "").strip()
        rejection_payment_status = _refund_payment_status_for_order(order)
        questionnaire = dict(order.get("questionnaire") or {})
        update_data = (
            {
                "order_status": "in_progress",
                "accepted_at": now_iso,
                "started_at": now_iso,
                "expires_at": None,
            }
            if payload.decision == "accept"
            else {
                "order_status": "rejected",
                "payment_status": rejection_payment_status,
                "ended_at": now_iso,
                "refund_amount_cents": int(order.get("price_cents") or 0),
                "refund_reference": _new_refund_reference("REJECT", order),
                "questionnaire": {
                    **questionnaire,
                    **({"mentor_rejection_reason": rejection_reason} if rejection_reason else {}),
                },
            }
        )
        response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_orders")
                .update(update_data)
                .eq("id", normalized_order_id)
                .eq("order_status", "pending_accept")
                .execute()
            ),
            operation_name="consultation order decision",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="订单状态已变化，请刷新后重试")
        _insert_order_event(
            supabase,
            normalized_order_id,
            event_type="mentor_order_decision",
            actor_role="mentor",
            actor_user_id=user_id,
            details={
                "decision": payload.decision,
                "start_deadline": update_data.get("expires_at"),
                "rejection_reason": rejection_reason or None,
            },
        )
        if payload.decision == "accept":
            _insert_system_message(
                supabase,
                normalized_order_id,
                f"认证前辈已确认接单，本次 {int(order.get('consultation_window_minutes') or 60)} 分钟咨询已开始。",
            )
            _insert_order_event(
                supabase,
                normalized_order_id,
                event_type="consultation_started",
                actor_role="mentor",
                actor_user_id=user_id,
                details={"started_after_acceptance": True},
            )
        else:
            _insert_order_event(
                supabase,
                normalized_order_id,
                event_type=("consultation_refund_completed" if rejection_payment_status == "refunded" else "consultation_refund_requested"),
                actor_role="mentor",
                actor_user_id=user_id,
                details={
                    "refund_amount_cents": int(order.get("price_cents") or 0),
                    "refund_reference": update_data.get("refund_reference"),
                    "reason": "mentor_rejected",
                },
            )
            _insert_system_message(
                supabase,
                normalized_order_id,
                (
                    f"认证前辈暂未接受本次咨询。说明：{rejection_reason}。测试退款已完成。"
                    if rejection_reason and rejection_payment_status == "refunded"
                    else "认证前辈暂未接受本次咨询；测试退款已完成。"
                )
                if rejection_payment_status == "refunded"
                else (
                    f"认证前辈暂未接受本次咨询。说明：{rejection_reason}。平台已提交退款处理，完成后会自动同步。"
                    if rejection_reason
                    else "认证前辈暂未接受本次咨询，平台已提交退款处理，完成后会自动同步。"
                ),
            )
        updated_order = response.data[0]
        _notify_consultation_applicant_order_status(
            supabase,
            order=updated_order,
            event="accepted" if payload.decision == "accept" else "rejected",
            detail=rejection_reason if payload.decision != "accept" else "",
        )
        return _serialize_order_item(updated_order)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Consultation order decision failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="处理接单暂时不可用") from exc


@router.post("/orders/{order_id}/start", response_model=MentorConsultationOrderItem)
def start_mentor_consultation_order(
    order_id: UUID,
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationOrderItem:
    normalized_order_id = str(order_id)
    supabase = get_supabase_admin()
    try:
        order, participant_role, _ = _get_order_participant(supabase, normalized_order_id, user_id)
        if participant_role != "mentor":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅认证前辈可以开始本次咨询")
        order = _refresh_pending_accept_status(supabase, order)
        order_status = str(order.get("order_status") or "")
        if order_status == "in_progress":
            return _serialize_order_item(order)
        _assert_order_status(order, {"accepted", "booked"}, "该订单当前还不能开始咨询")

        if str(order.get("consultation_type") or "") == "booking":
            slot_id = str(order.get("slot_id") or "")
            slot = _get_slot_or_404(supabase, slot_id)
            starts_at = _as_utc_datetime(slot.get("starts_at"))
            ends_at = _as_utc_datetime(slot.get("ends_at"))
            now = _utc_now()
            if starts_at and now < starts_at:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="未到预约时间，届时即可开始咨询")
            if ends_at and now > ends_at:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该预约时段已结束，请联系平台处理")

        response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_orders")
                .update({"order_status": "in_progress", "started_at": _utc_now().isoformat(), "expires_at": None})
                .eq("id", normalized_order_id)
                .eq("order_status", order_status)
                .execute()
            ),
            operation_name="consultation order start",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="订单状态已变化，请刷新后重试")
        _insert_system_message(
            supabase,
            normalized_order_id,
            f"前辈已接受咨询，本次 {int(order.get('consultation_window_minutes') or 60)} 分钟咨询窗口已开始。",
        )
        _insert_order_event(
            supabase,
            normalized_order_id,
            event_type="consultation_started",
            actor_role=participant_role,
            actor_user_id=user_id,
        )
        started_order = response.data[0]
        _notify_consultation_applicant_order_status(
            supabase,
            order=started_order,
            event="started",
        )
        return _serialize_order_item(started_order)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Consultation order start failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="开始咨询暂时不可用") from exc


@router.post("/orders/{order_id}/complete", response_model=MentorConsultationOrderItem)
def complete_mentor_consultation_order(
    order_id: UUID,
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationOrderItem:
    normalized_order_id = str(order_id)
    supabase = get_supabase_admin()
    try:
        order, participant_role, _ = _get_order_participant(supabase, normalized_order_id, user_id)
        if str(order.get("order_status") or "") == "completed":
            return _serialize_order_item(order)
        _assert_order_status(order, {"in_progress"}, "该订单当前还没有开始咨询")
        confirmation_field = (
            "mentor_completion_confirmed_at"
            if participant_role == "mentor"
            else "applicant_completion_confirmed_at"
        )
        now_iso = _utc_now().isoformat()
        if not order.get(confirmation_field):
            response = call_supabase(
                lambda: (
                    supabase.table("mentor_consultation_orders")
                    .update({confirmation_field: now_iso})
                    .eq("id", normalized_order_id)
                    .eq("order_status", "in_progress")
                    .execute()
                ),
                operation_name="consultation completion confirmation",
            )
            if not response.data:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="订单状态已变化，请刷新后重试")
            _insert_order_event(
                supabase,
                normalized_order_id,
                event_type="completion_confirmed",
                actor_role=participant_role,
                actor_user_id=user_id,
            )

        current = _get_order_or_404(supabase, normalized_order_id)
        applicant_confirmed = bool(current.get("applicant_completion_confirmed_at"))
        mentor_confirmed = bool(current.get("mentor_completion_confirmed_at"))
        if applicant_confirmed and mentor_confirmed:
            completed_response = call_supabase(
                lambda: (
                    supabase.table("mentor_consultation_orders")
                    .update({"order_status": "completed", "ended_at": now_iso})
                    .eq("id", normalized_order_id)
                    .eq("order_status", "in_progress")
                    .execute()
                ),
                operation_name="consultation order complete after mutual confirmation",
            )
            final_order = completed_response.data[0] if completed_response.data else _get_order_or_404(supabase, normalized_order_id)
            if completed_response.data and str(final_order.get("order_status") or "") == "completed":
                _insert_system_message(supabase, normalized_order_id, "双方已确认本次咨询完成，聊天记录会继续保留。")
                _insert_order_event(
                    supabase,
                    normalized_order_id,
                    event_type="consultation_completed",
                    actor_role="system",
                    details={"completion": "mutual_confirmation"},
                )
                record_consultation_income_pending(supabase, final_order)
            return _serialize_order_item(final_order)

        other_party = "前辈" if participant_role == "applicant" else "咨询用户"
        _insert_system_message(supabase, normalized_order_id, f"{ '咨询用户' if participant_role == 'applicant' else '前辈' }已提交结束确认，等待{other_party}确认。")
        return _serialize_order_item(current)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Consultation order complete failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="结束咨询暂时不可用") from exc


@router.get("/orders/{order_id}/messages", response_model=MentorConsultationMessageListResponse)
def list_mentor_consultation_messages(
    order_id: UUID,
    after: datetime | None = Query(default=None),
    before: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationMessageListResponse:
    normalized_order_id = str(order_id)
    if after is not None and before is not None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="聊天记录游标不能同时使用前后两个方向")
    supabase = get_supabase_admin()
    try:
        _get_order_participant(supabase, normalized_order_id, user_id)
        query = (
            supabase.table("mentor_consultation_messages")
            .select(CONSULTATION_MESSAGE_FIELDS)
            .eq("order_id", normalized_order_id)
        )
        if after is not None:
            query = query.gt("created_at", after.isoformat())
        if before is not None:
            query = query.lt("created_at", before.isoformat())
        response = call_supabase(
            lambda: query.order("created_at", desc=after is None).limit(limit).execute(),
            operation_name="consultation message list",
        )
        rows = response.data or []
        if after is None:
            rows.reverse()
        return MentorConsultationMessageListResponse(
            items=[MentorConsultationMessageItem(**serialize_mentor_message(row)) for row in rows],
            count=len(rows),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Consultation message list unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="聊天记录暂时不可用") from exc


@router.post("/orders/{order_id}/messages", response_model=MentorConsultationMessageItem)
def create_mentor_consultation_message(
    order_id: UUID,
    payload: MentorConsultationMessageCreateRequest,
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationMessageItem:
    if payload.message_type != "text":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="当前仅支持写入文字消息")
    content = str(payload.content or "").strip()
    if not content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="消息内容不能为空")

    normalized_order_id = str(order_id)
    client_message_id = str(payload.client_message_id or "").strip() or None
    supabase = get_supabase_admin()
    try:
        order, participant_role, mentor = _get_order_participant(supabase, normalized_order_id, user_id)
        if client_message_id:
            existing_response = call_supabase(
                lambda: (
                    supabase.table("mentor_consultation_messages")
                    .select(CONSULTATION_MESSAGE_FIELDS)
                    .eq("order_id", normalized_order_id)
                    .eq("sender_user_id", user_id)
                    .eq("client_message_id", client_message_id)
                    .limit(1)
                    .execute()
                ),
                operation_name="consultation idempotent message lookup",
            )
            if existing_response.data:
                existing_message = existing_response.data[0]
                if (
                    str(existing_message.get("message_type") or "") == "text"
                    and str(existing_message.get("content") or "") == content
                    and existing_message.get("duration_seconds") is None
                ):
                    return MentorConsultationMessageItem(**serialize_mentor_message(existing_message))
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="同一消息标识已用于不同内容，请生成新的消息标识后重试",
                )
        _assert_order_status(order, {"in_progress"}, "本次咨询已结束，暂不能继续发送消息")
        confirmation_field = (
            "mentor_completion_confirmed_at"
            if participant_role == "mentor"
            else "applicant_completion_confirmed_at"
        )
        if order.get(confirmation_field):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="你已确认结束本次咨询，正在等待对方确认",
            )
        started_at = _as_utc_datetime(order.get("started_at"))
        consultation_minutes = max(15, min(180, int(order.get("consultation_window_minutes") or 60)))
        if started_at and started_at + timedelta(minutes=consultation_minutes) <= _utc_now():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="本次服务时间已到，请双方确认结束或发起平台介入",
            )
        message = {
            "order_id": normalized_order_id,
            "sender_role": participant_role,
            "sender_user_id": user_id,
            "message_type": "text",
            "content": content,
            "client_message_id": client_message_id,
        }
        try:
            response = call_supabase(
                lambda: supabase.table("mentor_consultation_messages").insert(message).execute(),
                operation_name="consultation message create",
            )
        except Exception as insert_error:
            # 请求可能在服务端写入成功后于网络响应阶段失败；唯一键冲突时回读并比对正文。
            if not client_message_id:
                raise
            duplicate_response = call_supabase(
                lambda: (
                    supabase.table("mentor_consultation_messages")
                    .select(CONSULTATION_MESSAGE_FIELDS)
                    .eq("order_id", normalized_order_id)
                    .eq("sender_user_id", user_id)
                    .eq("client_message_id", client_message_id)
                    .limit(1)
                    .execute()
                ),
                operation_name="consultation duplicate message recovery",
            )
            if not duplicate_response.data:
                raise insert_error
            existing_message = duplicate_response.data[0]
            if (
                str(existing_message.get("message_type") or "") != "text"
                or str(existing_message.get("content") or "") != content
                or existing_message.get("duration_seconds") is not None
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="同一消息标识已用于不同内容，请生成新的消息标识后重试",
                ) from insert_error
            return MentorConsultationMessageItem(**serialize_mentor_message(existing_message))
        if not response.data:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="消息发送失败")
        saved_message = response.data[0]
        _notify_consultation_chat_message(
            supabase,
            order=order,
            mentor=mentor,
            sender_role=participant_role,
            sender_user_id=user_id,
            message=saved_message,
        )
        return MentorConsultationMessageItem(**serialize_mentor_message(saved_message))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Consultation message create failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="消息发送失败") from exc


@router.post("/orders/{order_id}/review", response_model=MentorConsultationReviewCreateResponse)
def create_mentor_consultation_review(
    order_id: UUID,
    payload: MentorConsultationReviewCreateRequest,
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationReviewCreateResponse:
    normalized_order_id = str(order_id)
    supabase = get_supabase_admin()
    try:
        order, participant_role, _ = _get_order_participant(supabase, normalized_order_id, user_id)
        if participant_role != "applicant":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅咨询发起人可以评价本次服务")
        _assert_order_status(order, {"completed"}, "请在咨询结束后再提交评价")
        existing_response = call_supabase(
            lambda: (
                supabase.table("mentor_reviews")
                .select("id")
                .eq("order_id", normalized_order_id)
                .limit(1)
                .execute()
            ),
            operation_name="consultation review lookup",
        )
        if existing_response.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="本次咨询已评价")

        tags = []
        for tag in payload.tags:
            normalized_tag = str(tag or "").strip()[:40]
            if normalized_tag and normalized_tag not in tags:
                tags.append(normalized_tag)
        response = call_supabase(
            lambda: supabase.table("mentor_reviews").insert({
                "order_id": normalized_order_id,
                "mentor_id": str(order.get("mentor_id") or ""),
                "reviewer_user_id": user_id,
                "reviewer_display_name": "匿名用户",
                "rating": payload.rating,
                "tags": tags,
                "content": str(payload.content or "").strip(),
                "is_published": True,
            }).execute(),
            operation_name="consultation review create",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="评价提交失败")
        return MentorConsultationReviewCreateResponse(
            order_id=normalized_order_id,
            **serialize_mentor_review(response.data[0]),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Consultation review create failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="评价提交失败") from exc


@router.get("/me/reports", response_model=MentorConsultationReportListResponse)
def list_my_mentor_consultation_reports(
    limit: int = Query(default=100, ge=1, le=200),
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationReportListResponse:
    """Both parties can trace platform handling progress and the final order outcome."""

    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_reports")
                .select(MENTOR_CONSULTATION_REPORT_FIELDS, count="exact")
                .or_(
                    f"reporter_user_id.eq.{user_id},respondent_user_id.eq.{user_id},target_user_id.eq.{user_id}"
                )
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            ),
            operation_name="my consultation report list",
        )
        rows = response.data or []
        evidence_summary = _fetch_consultation_report_evidence_summary(
            supabase,
            [str(row.get("id") or "") for row in rows],
        )
        appeal_summary = _fetch_consultation_report_appeal_summary(
            supabase,
            [str(row.get("id") or "") for row in rows],
            user_id,
        )
        return MentorConsultationReportListResponse(
            items=[
                MentorConsultationReportCreateResponse(**_serialize_consultation_report(
                    row,
                    user_id=user_id,
                    evidence_summary=evidence_summary.get(str(row.get("id") or "")),
                    appeal_summary=appeal_summary.get(str(row.get("id") or "")),
                ))
                for row in rows
            ],
            count=int(response.count or len(rows)),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("My consultation report list unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="举报记录暂时不可用") from exc


@router.post(
    "/orders/{order_id}/reports",
    response_model=MentorConsultationReportCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_mentor_consultation_report(
    order_id: UUID,
    payload: MentorConsultationReportCreateRequest,
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationReportCreateResponse:
    normalized_order_id = str(order_id)
    issue_type = str(payload.issue_type or "").strip()
    content = str(payload.content or "").strip()
    supabase = get_supabase_admin()
    try:
        order, reporter_role, mentor = _get_order_participant(supabase, normalized_order_id, user_id)
        target_role = "mentor" if reporter_role == "applicant" else "applicant"
        if issue_type not in MENTOR_CONSULTATION_REPORT_ISSUE_TYPES[target_role]:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="请选择与举报对象相符的问题类型")
        if not content or len(content) < 20:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="举报说明请至少填写 20 个字")

        if issue_type == MENTOR_REVIEW_DISPUTE_ISSUE_TYPE:
            review_response = call_supabase(
                lambda: (
                    supabase.table("mentor_reviews")
                    .select("id")
                    .eq("order_id", normalized_order_id)
                    .eq("mentor_id", str(mentor.get("id") or ""))
                    .limit(1)
                    .execute()
                ),
                operation_name="consultation review dispute lookup",
            )
            if not review_response.data:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="该订单暂未产生服务评价，无法提交评价争议反馈",
                )

        existing_response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_reports")
                .select("id")
                .eq("order_id", normalized_order_id)
                .eq("reporter_user_id", user_id)
                .limit(1)
                .execute()
            ),
            operation_name="consultation report duplicate lookup",
        )
        if existing_response.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="本次咨询已提交过问题反馈；如需补充凭证，请在“平台处理进度”中找到该记录后继续上传",
            )

        target_user_id = None
        target_mentor_id = None
        if target_role == "mentor":
            target_mentor_id = str(mentor.get("id") or "")
            if not target_mentor_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到被举报前辈")
            target_user_id = str(mentor.get("owner_user_id") or "") or None
        else:
            target_user_id = str(order.get("applicant_user_id") or "")
            if not target_user_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到被举报咨询用户")

        settings = get_settings()
        case_priority = initial_report_priority(issue_type)
        first_response_hours = (
            settings.mentor_consultation_urgent_report_first_response_hours
            if case_priority == "urgent"
            else settings.mentor_consultation_report_first_response_hours
        )
        first_response_due_at = first_response_deadline(
            now=_utc_now(),
            hours=first_response_hours,
        )

        response = call_supabase(
            lambda: supabase.table("mentor_consultation_reports").insert({
                "order_id": normalized_order_id,
                "reporter_user_id": user_id,
                "reporter_role": reporter_role,
                "respondent_user_id": target_user_id,
                "target_role": target_role,
                "target_user_id": target_user_id,
                "target_mentor_id": target_mentor_id,
                "issue_type": issue_type,
                "content": content,
                "status": "pending",
                "first_response_due_at": first_response_due_at,
                "priority": case_priority,
                "escalation_level": 0,
            }).execute(),
            operation_name="consultation report create",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="举报提交失败")
        _insert_order_event(
            supabase,
            normalized_order_id,
            event_type="consultation_report_created",
            actor_role=reporter_role,
            actor_user_id=user_id,
            details={"report_id": str(response.data[0].get("id") or ""), "issue_type": issue_type},
        )
        _insert_system_message(
            supabase,
            normalized_order_id,
            (
                "平台已收到本次咨询的问题反馈。为保障双方权益，发起方可在“平台处理进度”补充凭证，"
                "被反馈方可提交说明与凭证；平台将结合订单、聊天和双方材料核实。"
                f"本案最迟将在 {first_response_hours} 小时内获得平台首次响应。"
            ),
        )
        return MentorConsultationReportCreateResponse(**_serialize_consultation_report(
            response.data[0],
            user_id=user_id,
        ))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Consultation report create failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="举报提交暂时不可用") from exc


@router.post(
    "/reports/{report_id}/response",
    response_model=MentorConsultationReportCreateResponse,
)
def respond_to_mentor_consultation_report(
    report_id: UUID,
    payload: MentorConsultationReportResponseRequest,
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationReportCreateResponse:
    """Allow the reported participant to make or update a factual response before closure."""

    normalized_report_id = str(report_id)
    content = str(payload.content or "").strip()
    if len(content) < 20:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="回应说明请至少填写 20 个字")

    supabase = get_supabase_admin()
    try:
        report, participation_role = _get_participant_consultation_report_or_404(
            supabase,
            normalized_report_id,
            user_id,
        )
        if participation_role != "respondent":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有被反馈方可以提交回应")
        if str(report.get("status") or "pending") not in {"pending", "reviewing"}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该反馈已处理，不能继续提交回应")

        responded_at = _utc_now().isoformat()
        response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_reports")
                .update({"respondent_content": content, "responded_at": responded_at})
                .eq("id", normalized_report_id)
                .in_("status", ["pending", "reviewing"])
                .execute()
            ),
            operation_name="consultation report respondent response",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该反馈状态已变化，请刷新后重试")
        updated = response.data[0]
        order_id = str(updated.get("order_id") or "")
        _insert_order_event(
            supabase,
            order_id,
            event_type="consultation_report_responded",
            actor_role=str(updated.get("target_role") or "applicant"),
            actor_user_id=user_id,
            details={"report_id": normalized_report_id},
        )
        _insert_system_message(
            supabase,
            order_id,
            "被反馈方已补充本次咨询的说明。平台正在结合双方材料、订单和聊天记录核实。",
        )
        evidence_summary = _fetch_consultation_report_evidence_summary(supabase, [normalized_report_id])
        return MentorConsultationReportCreateResponse(**_serialize_consultation_report(
            updated,
            user_id=user_id,
            evidence_summary=evidence_summary.get(normalized_report_id),
        ))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Consultation report response failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="回应提交暂时不可用") from exc


@router.post(
    "/reports/{report_id}/evidence",
    response_model=MentorConsultationReportEvidenceUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_mentor_consultation_report_evidence(
    report_id: UUID,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationReportEvidenceUploadResponse:
    data = await file.read(MAX_MENTOR_CONSULTATION_REPORT_EVIDENCE_BYTES + 1)
    filename = str(file.filename or "咨询凭证").strip()[:255] or "咨询凭证"
    await file.close()

    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="凭证图片为空")
    if len(data) > MAX_MENTOR_CONSULTATION_REPORT_EVIDENCE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="单张凭证图片不能超过 8 MB")
    detected = _detect_mentor_verification_document_content_type(data)
    if not detected:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="凭证仅支持 PNG、JPG 或 WebP 图片")

    normalized_report_id = str(report_id)
    content_type, extension = detected
    supabase = get_supabase_admin()
    bucket = None
    storage_path = ""
    try:
        report, participation_role = _get_participant_consultation_report_or_404(
            supabase,
            normalized_report_id,
            user_id,
        )
        if str(report.get("status") or "pending") not in {"pending", "reviewing"}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该举报已处理，不能继续补充凭证")
        count_response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_report_evidence")
                .select("id", count="exact")
                .eq("report_id", normalized_report_id)
                .eq("submitter_role", participation_role)
                .limit(1)
                .execute()
            ),
            operation_name="consultation report evidence limit check",
        )
        if int(count_response.count or 0) >= 3:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="每一方最多上传 3 张凭证图片")

        _ensure_mentor_consultation_report_evidence_bucket(supabase.storage)
        bucket = supabase.storage.from_(MENTOR_CONSULTATION_REPORT_EVIDENCE_BUCKET)
        storage_path = f"{user_id}/{normalized_report_id}/{participation_role}/{uuid4().hex}.{extension}"
        bucket.upload(
            storage_path,
            data,
            file_options={
                "content-type": content_type,
                "cache-control": "31536000",
                "upsert": "false",
            },
        )
        response = call_supabase(
            lambda: supabase.table("mentor_consultation_report_evidence").insert({
                "report_id": normalized_report_id,
                "file_url": storage_path,
                "file_name": filename,
                "mime_type": content_type,
                "submitter_role": participation_role,
            }).execute(),
            operation_name="consultation report evidence create",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="凭证图片保存失败")
        evidence = response.data[0]
        _insert_order_event(
            supabase,
            str(report.get("order_id") or ""),
            event_type="consultation_report_evidence_uploaded",
            actor_role=(str(report.get("reporter_role") or "applicant") if participation_role == "reporter" else str(report.get("target_role") or "applicant")),
            actor_user_id=user_id,
            details={"report_id": normalized_report_id, "submitter_role": participation_role},
        )
        return MentorConsultationReportEvidenceUploadResponse(
            id=str(evidence.get("id") or ""),
            file_name=str(evidence.get("file_name") or filename),
            mime_type=evidence.get("mime_type") or content_type,
            submitter_role=str(evidence.get("submitter_role") or participation_role),
            created_at=evidence.get("created_at") or None,
        )
    except HTTPException:
        if bucket and storage_path:
            try:
                bucket.remove([storage_path])
            except Exception:
                pass
        raise
    except Exception as exc:
        if bucket and storage_path:
            try:
                bucket.remove([storage_path])
            except Exception:
                pass
        logger.warning("Consultation report evidence upload failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="凭证图片上传失败") from exc


@router.get("/me/report-appeals", response_model=MentorConsultationReportAppealListResponse)
def list_my_mentor_consultation_report_appeals(
    limit: int = Query(default=100, ge=1, le=200),
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationReportAppealListResponse:
    """Let a participant trace every review request they submitted."""

    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_report_appeals")
                .select(MENTOR_CONSULTATION_REPORT_APPEAL_FIELDS, count="exact")
                .eq("appellant_user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            ),
            operation_name="my consultation report appeal list",
        )
        rows = response.data or []
        appeal_ids = [str(row.get("id") or "") for row in rows if row.get("id")]
        evidence_counts = {appeal_id: 0 for appeal_id in appeal_ids}
        if appeal_ids:
            evidence_response = call_supabase(
                lambda: (
                    supabase.table("mentor_consultation_report_appeal_evidence")
                    .select("appeal_id")
                    .in_("appeal_id", appeal_ids)
                    .execute()
                ),
                operation_name="my consultation report appeal evidence count",
            )
            for evidence in evidence_response.data or []:
                appeal_id = str(evidence.get("appeal_id") or "")
                if appeal_id in evidence_counts:
                    evidence_counts[appeal_id] += 1
        return MentorConsultationReportAppealListResponse(
            items=[
                MentorConsultationReportAppealItem(**_serialize_consultation_report_appeal(
                    row,
                    evidence_count=evidence_counts.get(str(row.get("id") or ""), 0),
                ))
                for row in rows
            ],
            count=int(response.count or len(rows)),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("My consultation report appeal list unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="复核记录暂时不可用") from exc


@router.post(
    "/reports/{report_id}/appeals",
    response_model=MentorConsultationReportAppealItem,
    status_code=status.HTTP_201_CREATED,
)
def create_mentor_consultation_report_appeal(
    report_id: UUID,
    payload: MentorConsultationReportAppealCreateRequest,
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationReportAppealItem:
    """Give either party one documented chance to request a review after a decision."""

    normalized_report_id = str(report_id)
    content = str(payload.content or "").strip()
    supabase = get_supabase_admin()
    try:
        report, participation_role = _get_participant_consultation_report_or_404(
            supabase,
            normalized_report_id,
            user_id,
        )
        if str(report.get("status") or "pending") not in {"resolved", "dismissed"}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="当前问题反馈仍在处理中，暂不需要申请复核")
        duplicate_response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_report_appeals")
                .select("id")
                .eq("report_id", normalized_report_id)
                .eq("appellant_user_id", user_id)
                .limit(1)
                .execute()
            ),
            operation_name="consultation report appeal duplicate lookup",
        )
        if duplicate_response.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="你已申请过本次复核，可在平台处理进度查看结果")
        settings = get_settings()
        first_response_hours = settings.mentor_consultation_report_appeal_first_response_hours
        first_response_due_at = first_response_deadline(
            now=_utc_now(),
            hours=first_response_hours,
        )
        response = call_supabase(
            lambda: supabase.table("mentor_consultation_report_appeals").insert({
                "report_id": normalized_report_id,
                "appellant_user_id": user_id,
                "appellant_role": participation_role,
                "content": content,
                "status": "pending",
                "decision": "none",
                "first_response_due_at": first_response_due_at,
                "priority": "normal",
                "escalation_level": 0,
            }).execute(),
            operation_name="consultation report appeal create",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="复核申请提交失败")
        appeal = response.data[0]
        actor_role = str(report.get("reporter_role") or "applicant") if participation_role == "reporter" else str(report.get("target_role") or "applicant")
        _insert_order_event(
            supabase,
            str(report.get("order_id") or ""),
            event_type="consultation_report_appeal_created",
            actor_role=actor_role,
            actor_user_id=user_id,
            details={"report_id": normalized_report_id, "appeal_id": str(appeal.get("id") or ""), "appellant_role": participation_role},
        )
        actor_label = "咨询用户" if actor_role == "applicant" else "认证前辈"
        _insert_system_message(
            supabase,
            str(report.get("order_id") or ""),
            (
                f"{actor_label}已申请复核本次平台处理结果。平台将重新核对双方说明、凭证、订单和聊天记录。"
                f"复核申请最迟将在 {first_response_hours} 小时内获得平台首次响应。"
            ),
        )
        return MentorConsultationReportAppealItem(**_serialize_consultation_report_appeal(appeal))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Consultation report appeal create failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="复核申请暂时不可用") from exc


@router.post(
    "/report-appeals/{appeal_id}/evidence",
    response_model=MentorConsultationReportAppealEvidenceUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_mentor_consultation_report_appeal_evidence(
    appeal_id: UUID,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationReportAppealEvidenceUploadResponse:
    data = await file.read(MAX_MENTOR_CONSULTATION_REPORT_EVIDENCE_BYTES + 1)
    filename = str(file.filename or "复核凭证").strip()[:255] or "复核凭证"
    await file.close()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="凭证图片为空")
    if len(data) > MAX_MENTOR_CONSULTATION_REPORT_EVIDENCE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="单张凭证图片不能超过 8 MB")
    detected = _detect_mentor_verification_document_content_type(data)
    if not detected:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="凭证仅支持 PNG、JPG 或 WebP 图片")

    normalized_appeal_id = str(appeal_id)
    content_type, extension = detected
    supabase = get_supabase_admin()
    bucket = None
    storage_path = ""
    try:
        appeal_response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_report_appeals")
                .select(MENTOR_CONSULTATION_REPORT_APPEAL_FIELDS)
                .eq("id", normalized_appeal_id)
                .eq("appellant_user_id", user_id)
                .limit(1)
                .execute()
            ),
            operation_name="consultation report appeal lookup",
        )
        if not appeal_response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到可补充的复核申请")
        appeal = appeal_response.data[0]
        if str(appeal.get("status") or "pending") not in {"pending", "reviewing"}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该复核已处理，不能继续补充凭证")
        count_response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_report_appeal_evidence")
                .select("id", count="exact")
                .eq("appeal_id", normalized_appeal_id)
                .limit(1)
                .execute()
            ),
            operation_name="consultation report appeal evidence limit check",
        )
        if int(count_response.count or 0) >= 3:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="每次复核最多上传 3 张凭证图片")
        report, participation_role = _get_participant_consultation_report_or_404(
            supabase,
            str(appeal.get("report_id") or ""),
            user_id,
        )
        _ensure_mentor_consultation_report_appeal_evidence_bucket(supabase.storage)
        bucket = supabase.storage.from_(MENTOR_CONSULTATION_REPORT_APPEAL_EVIDENCE_BUCKET)
        storage_path = f"{user_id}/{normalized_appeal_id}/{uuid4().hex}.{extension}"
        bucket.upload(
            storage_path,
            data,
            file_options={"content-type": content_type, "cache-control": "31536000", "upsert": "false"},
        )
        response = call_supabase(
            lambda: supabase.table("mentor_consultation_report_appeal_evidence").insert({
                "appeal_id": normalized_appeal_id,
                "file_url": storage_path,
                "file_name": filename,
                "mime_type": content_type,
            }).execute(),
            operation_name="consultation report appeal evidence create",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="复核凭证保存失败")
        evidence = response.data[0]
        actor_role = str(report.get("reporter_role") or "applicant") if participation_role == "reporter" else str(report.get("target_role") or "applicant")
        _insert_order_event(
            supabase,
            str(report.get("order_id") or ""),
            event_type="consultation_report_appeal_evidence_uploaded",
            actor_role=actor_role,
            actor_user_id=user_id,
            details={"report_id": str(report.get("id") or ""), "appeal_id": normalized_appeal_id},
        )
        return MentorConsultationReportAppealEvidenceUploadResponse(
            id=str(evidence.get("id") or ""),
            file_name=str(evidence.get("file_name") or filename),
            mime_type=evidence.get("mime_type") or content_type,
            created_at=evidence.get("created_at") or None,
        )
    except HTTPException:
        if bucket and storage_path:
            try:
                bucket.remove([storage_path])
            except Exception:
                pass
        raise
    except Exception as exc:
        if bucket and storage_path:
            try:
                bucket.remove([storage_path])
            except Exception:
                pass
        logger.warning("Consultation report appeal evidence upload failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="复核凭证上传失败") from exc
