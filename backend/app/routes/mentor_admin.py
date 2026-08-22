from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import get_supabase_admin
from app.dependencies import require_question_admin_portal_user, require_question_admin_user
from app.schemas.mentor_consultation import (
    AdminMentorConsultationReportDetailResponse,
    AdminMentorConsultationReportEvidenceItem,
    AdminMentorConsultationReportItem,
    AdminMentorConsultationReportListResponse,
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
    fetch_mentor_aggregates,
    fetch_mentor_skills,
    mask_mentor_name,
    normalize_skills,
    serialize_mentor_admin,
)
from app.services.supabase_resilience import call_supabase


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
MENTOR_CONSULTATION_REPORT_MAX_LIMIT = 100
MENTOR_CONSULTATION_REPORT_FIELDS = (
    "id,order_id,reporter_user_id,reporter_role,target_role,target_user_id,target_mentor_id,"
    "issue_type,content,status,admin_note,handled_by,handled_at,created_at,updated_at"
)
MENTOR_CONSULTATION_REPORT_ORDER_FIELDS = (
    "id,order_no,consultation_type,order_status,questionnaire,price_cents,"
    "started_at,ended_at,created_at"
)
MENTOR_PROFILE_CHANGE_REQUEST_FIELDS = (
    "id,mentor_id,owner_user_id,school,major,exam_type,score,skills,bio,price_cents,"
    "request_status,admin_note,reviewed_by,reviewed_at,created_at,updated_at"
)


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
    return {
        "id": str(row.get("id") or ""),
        "order_id": str(row.get("order_id") or ""),
        "reporter_role": str(row.get("reporter_role") or "applicant"),
        "target_role": target_role,
        "issue_type": str(row.get("issue_type") or "其他问题"),
        "content": str(row.get("content") or ""),
        "status": str(row.get("status") or "pending"),
        "created_at": row.get("created_at") or None,
        "reporter": _serialize_report_user(users.get(reporter_id), str(row.get("reporter_role") or "applicant")),
        "target": target,
        "order_no": str(order.get("order_no") or "") or None,
        "admin_note": row.get("admin_note") or None,
        "handled_at": row.get("handled_at") or None,
        "evidence_count": max(0, int(evidence_count or 0)),
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
        "created_at": row.get("created_at") or None,
        "file_url": file_url,
    }


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
    _: dict = Depends(require_question_admin_portal_user),
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
    _: dict = Depends(require_question_admin_portal_user),
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
    admin_profile: dict = Depends(require_question_admin_portal_user),
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
    _: dict = Depends(require_question_admin_portal_user),
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
    _: dict = Depends(require_question_admin_portal_user),
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
    admin_profile: dict = Depends(require_question_admin_portal_user),
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
    _: dict = Depends(require_question_admin_portal_user),
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
    _: dict = Depends(require_question_admin_portal_user),
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
    admin_profile: dict = Depends(require_question_admin_portal_user),
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
    admin_profile: dict = Depends(require_question_admin_portal_user),
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
    _: dict = Depends(require_question_admin_portal_user),
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
    admin_profile: dict = Depends(require_question_admin_portal_user),
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
    admin_profile: dict = Depends(require_question_admin_portal_user),
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


@router.get("/reports", response_model=AdminMentorConsultationReportListResponse)
def list_admin_mentor_consultation_reports(
    report_status: str | None = Query(default=None, alias="status", max_length=20),
    limit: int = Query(default=50, ge=1, le=MENTOR_CONSULTATION_REPORT_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_question_admin_user),
) -> AdminMentorConsultationReportListResponse:
    normalized_status = str(report_status or "").strip().lower()
    valid_statuses = {"pending", "reviewing", "resolved", "dismissed"}
    if normalized_status and normalized_status not in valid_statuses:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的举报处理状态")

    supabase = get_supabase_admin()
    try:
        query = supabase.table("mentor_consultation_reports").select(MENTOR_CONSULTATION_REPORT_FIELDS, count="exact")
        if normalized_status:
            query = query.eq("status", normalized_status)
        response = call_supabase(
            lambda: query.order("created_at", desc=True).range(offset, offset + limit - 1).execute(),
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
            ],
        )
        mentors = _fetch_report_mentors(supabase, [str(row.get("target_mentor_id") or "") for row in rows])
        orders = _fetch_report_orders(supabase, [str(row.get("order_id") or "") for row in rows])
        evidence_counts = _fetch_report_evidence_counts(supabase, [str(row.get("id") or "") for row in rows])
        return AdminMentorConsultationReportListResponse(
            items=[
                AdminMentorConsultationReportItem(**_serialize_admin_consultation_report(
                    row,
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
        logger.warning("Admin consultation report list failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="举报列表暂时不可用") from exc


@router.get("/reports/{report_id}", response_model=AdminMentorConsultationReportDetailResponse)
def get_admin_mentor_consultation_report(
    report_id: str,
    _: dict = Depends(require_question_admin_user),
) -> AdminMentorConsultationReportDetailResponse:
    supabase = get_supabase_admin()
    try:
        report = _get_consultation_report_or_404(supabase, report_id)
        users = _fetch_application_users(
            supabase,
            [str(report.get("reporter_user_id") or ""), str(report.get("target_user_id") or "")],
        )
        mentors = _fetch_report_mentors(supabase, [str(report.get("target_mentor_id") or "")])
        orders = _fetch_report_orders(supabase, [str(report.get("order_id") or "")])
        evidence_response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_report_evidence")
                .select("id,file_url,file_name,mime_type,created_at")
                .eq("report_id", report_id)
                .order("created_at")
                .limit(3)
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
        ))
        return AdminMentorConsultationReportDetailResponse(
            report=item,
            evidence=evidence,
            order=orders.get(str(report.get("order_id") or ""), {}),
            messages=message_response.data or [],
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
        _get_consultation_report_or_404(supabase, report_id)
        normalized_note = str(payload.admin_note or "").strip() or None
        terminal = payload.status in {"resolved", "dismissed"}
        update_data = {
            "status": payload.status,
            "admin_note": normalized_note,
            "handled_by": admin_profile.get("id") if payload.status != "pending" else None,
            "handled_at": datetime.now(timezone.utc).isoformat() if terminal else None,
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该举报记录")
        row = response.data[0]
        users = _fetch_application_users(
            supabase,
            [str(row.get("reporter_user_id") or ""), str(row.get("target_user_id") or "")],
        )
        mentors = _fetch_report_mentors(supabase, [str(row.get("target_mentor_id") or "")])
        orders = _fetch_report_orders(supabase, [str(row.get("order_id") or "")])
        evidence_counts = _fetch_report_evidence_counts(supabase, [str(row.get("id") or "")])
        _log_consultation_report_action(
            supabase,
            admin_profile,
            "update_mentor_consultation_report_status",
            report_id,
            {"status": payload.status},
        )
        return AdminMentorConsultationReportItem(**_serialize_admin_consultation_report(
            row,
            users,
            mentors,
            orders,
            evidence_count=evidence_counts.get(str(row.get("id") or ""), 0),
        ))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin consultation report status update failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="举报状态更新失败") from exc
