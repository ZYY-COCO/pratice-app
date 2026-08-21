from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

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
from app.services.supabase_resilience import call_supabase


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
ORDER_PAYMENT_WINDOW_MINUTES = 10
ORDER_LIST_MAX_LIMIT = 100
MENTOR_SLOT_MAX_LIMIT = 100
MENTOR_SLOT_WINDOW_MINUTES = 60
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
MENTOR_VERIFICATION_APPLICATION_FIELDS = (
    "id,applicant_user_id,legal_name,school,major,admission_year,graduation_year,"
    "exam_type,score,skills,bio,price_cents,application_status,admin_note,reviewed_at,"
    "created_at,updated_at"
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


def _refresh_pending_accept_status(supabase, order: dict) -> dict:
    if str(order.get("order_status") or "") != "pending_accept":
        return order
    expires_at = _as_utc_datetime(order.get("expires_at"))
    if expires_at is None or expires_at > _utc_now():
        return order

    response = call_supabase(
        lambda: (
            supabase.table("mentor_consultation_orders")
            .update({
                "order_status": "timeout",
                "payment_status": "refunded",
                "ended_at": _utc_now().isoformat(),
            })
            .eq("id", str(order.get("id") or ""))
            .eq("order_status", "pending_accept")
            .execute()
        ),
        operation_name="consultation order timeout refresh",
    )
    if response.data:
        return response.data[0]
    return _get_order_or_404(supabase, str(order.get("id") or ""))


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
    limit: int = Query(default=MENTOR_SLOT_MAX_LIMIT, ge=1, le=MENTOR_SLOT_MAX_LIMIT),
    user_id: str = Depends(get_current_user_id),
) -> MentorOwnerAvailabilitySlotListResponse:
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
        response = call_supabase(
            lambda: (
                supabase.table("mentor_availability_slots")
                .select("id,starts_at,ends_at,price_cents,status", count="exact")
                .eq("mentor_id", mentor_id)
                .order("starts_at")
                .limit(limit)
                .execute()
            ),
            operation_name="mentor own availability list",
        )
        rows = response.data or []
        return MentorOwnerAvailabilitySlotListResponse(
            items=[MentorAvailabilitySlotItem(**serialize_mentor_slot(row)) for row in rows],
            count=int(response.count or len(rows)),
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
                .in_("status", ["available", "booked"])
                .lt("starts_at", ends_at_iso)
                .gt("ends_at", starts_at_iso)
                .limit(1)
                .execute()
            ),
            operation_name="mentor availability overlap lookup",
        )
        if overlap_response.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该时间与已有预约时段重叠")

        price_cents = payload.price_cents
        if price_cents is None:
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
        if str(slot.get("status") or "") == "booked":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已被预约的时段不能关闭")
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
    limit: int = Query(default=30, ge=1, le=ORDER_LIST_MAX_LIMIT),
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationOrderListResponse:
    normalized_status = str(order_status or "").strip().lower()
    if normalized_status and normalized_status not in CONSULTATION_ORDER_STATUSES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的订单状态")

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
        response = call_supabase(
            lambda: query.order("created_at", desc=True).limit(limit).execute(),
            operation_name="received mentor consultation order list",
        )
        rows = [_refresh_pending_accept_status(supabase, row) for row in (response.data or [])]
        return MentorConsultationOrderListResponse(
            items=[_serialize_order_item(row) for row in rows],
            count=int(response.count or len(rows)),
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


@router.post(
    "/orders",
    response_model=MentorConsultationOrderItem,
    status_code=status.HTTP_201_CREATED,
)
def create_mentor_consultation_order(
    payload: MentorConsultationOrderCreateRequest,
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationOrderItem:
    mentor_id = str(payload.mentor_id)
    consultation_type = payload.consultation_type
    questionnaire = payload.questionnaire.model_dump()
    for required_field in ("name", "school", "major"):
        questionnaire[required_field] = str(questionnaire.get(required_field) or "").strip()
        if not questionnaire[required_field]:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="请完整填写咨询基本信息")
    questionnaire["grade"] = str(questionnaire.get("grade") or "其他").strip()[:40] or "其他"
    questionnaire["question"] = str(questionnaire.get("question") or "").strip()

    supabase = get_supabase_admin()
    try:
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
            if str(slot.get("status") or "") != "available":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该预约时段已不可用，请重新选择")
            starts_at = _as_utc_datetime(slot.get("starts_at"))
            if starts_at is not None and starts_at <= _utc_now():
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该预约时段已过期，请重新选择")
            price_cents = int(
                slot.get("price_cents")
                if slot.get("price_cents") is not None
                else mentor.get("price_cents") or 0
            )

        response = call_supabase(
            lambda: supabase.table("mentor_consultation_orders").insert({
                "order_no": _new_order_no(),
                "applicant_user_id": user_id,
                "mentor_id": mentor_id,
                "slot_id": str(payload.slot_id) if payload.slot_id is not None else None,
                "consultation_type": consultation_type,
                "order_status": "pending_payment",
                "payment_status": "unpaid",
                "questionnaire": questionnaire,
                "price_cents": max(0, price_cents),
                "consultation_window_minutes": int(mentor.get("consultation_window_minutes") or 60),
            }).execute(),
            operation_name="consultation order create",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="咨询订单创建失败")
        return _serialize_order_item(response.data[0])
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Consultation order create failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="咨询订单创建失败") from exc


@router.post("/orders/{order_id}/mock-pay", response_model=MentorConsultationOrderItem)
def mock_pay_mentor_consultation_order(
    order_id: UUID,
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationOrderItem:
    normalized_order_id = str(order_id)
    supabase = get_supabase_admin()
    reserved_slot_id: str | None = None
    try:
        order, participant_role, _ = _get_order_participant(supabase, normalized_order_id, user_id)
        if participant_role != "applicant":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅咨询发起人可以支付订单")
        order = _refresh_pending_accept_status(supabase, order)
        order_status = str(order.get("order_status") or "")
        if order_status in {"pending_accept", "booked"} and str(order.get("payment_status") or "") == "paid":
            return _serialize_order_item(order)
        _assert_order_status(order, {"pending_payment"}, "该订单当前无法支付")

        now = _utc_now()
        consultation_type = str(order.get("consultation_type") or "instant")
        update_data = {
            "payment_status": "paid",
            "payment_reference": f"MOCK-{str(order.get('order_no') or '')}-{uuid4().hex[:6].upper()}",
        }
        if consultation_type == "booking":
            slot_id = str(order.get("slot_id") or "")
            if not slot_id:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="预约订单缺少预约时段")
            slot = _get_slot_or_404(supabase, slot_id)
            if str(slot.get("mentor_id") or "") != str(order.get("mentor_id") or ""):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="预约时段与订单不匹配")
            starts_at = _as_utc_datetime(slot.get("starts_at"))
            if starts_at is not None and starts_at <= now:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该预约时段已过期，请重新选择")
            slot_response = call_supabase(
                lambda: (
                    supabase.table("mentor_availability_slots")
                    .update({"status": "booked"})
                    .eq("id", slot_id)
                    .eq("status", "available")
                    .execute()
                ),
                operation_name="consultation booking slot reserve",
            )
            if not slot_response.data:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该预约时段刚刚被占用，请重新选择")
            reserved_slot_id = slot_id
            update_data.update({"order_status": "booked", "expires_at": None})
        else:
            update_data.update({
                "order_status": "pending_accept",
                "expires_at": (now + timedelta(minutes=ORDER_PAYMENT_WINDOW_MINUTES)).isoformat(),
            })

        response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_orders")
                .update(update_data)
                .eq("id", normalized_order_id)
                .eq("applicant_user_id", user_id)
                .eq("order_status", "pending_payment")
                .execute()
            ),
            operation_name="consultation mock payment",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="订单状态已变化，请刷新后重试")
        reserved_slot_id = None
        return _serialize_order_item(response.data[0])
    except HTTPException:
        if reserved_slot_id:
            try:
                call_supabase(
                    lambda: (
                        supabase.table("mentor_availability_slots")
                        .update({"status": "available"})
                        .eq("id", reserved_slot_id)
                        .eq("status", "booked")
                        .execute()
                    ),
                    operation_name="consultation booking slot release",
                )
            except Exception as rollback_error:
                logger.warning("Consultation booking slot rollback skipped (error_type=%s)", type(rollback_error).__name__)
        raise
    except Exception as exc:
        if reserved_slot_id:
            try:
                call_supabase(
                    lambda: (
                        supabase.table("mentor_availability_slots")
                        .update({"status": "available"})
                        .eq("id", reserved_slot_id)
                        .eq("status", "booked")
                        .execute()
                    ),
                    operation_name="consultation booking slot failure release",
                )
            except Exception as rollback_error:
                logger.warning("Consultation booking slot rollback skipped (error_type=%s)", type(rollback_error).__name__)
        logger.warning("Consultation mock payment failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="模拟支付暂时不可用") from exc


@router.get("/me/orders", response_model=MentorConsultationOrderListResponse)
def list_my_mentor_consultation_orders(
    limit: int = Query(default=30, ge=1, le=ORDER_LIST_MAX_LIMIT),
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationOrderListResponse:
    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_orders")
                .select(CONSULTATION_ORDER_FIELDS, count="exact")
                .eq("applicant_user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            ),
            operation_name="my consultation order list",
        )
        rows = [_refresh_pending_accept_status(supabase, row) for row in (response.data or [])]
        return MentorConsultationOrderListResponse(
            items=[_serialize_order_item(row) for row in rows],
            count=int(response.count or len(rows)),
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

        now = _utc_now().isoformat()
        update_data = (
            {"order_status": "accepted", "accepted_at": now, "expires_at": None}
            if payload.decision == "accept"
            else {"order_status": "rejected", "payment_status": "refunded", "ended_at": now}
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
        return _serialize_order_item(response.data[0])
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
        order, _, _ = _get_order_participant(supabase, normalized_order_id, user_id)
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
                .update({"order_status": "in_progress", "started_at": _utc_now().isoformat()})
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
        return _serialize_order_item(response.data[0])
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
        order, _, _ = _get_order_participant(supabase, normalized_order_id, user_id)
        if str(order.get("order_status") or "") == "completed":
            return _serialize_order_item(order)
        _assert_order_status(order, {"in_progress"}, "该订单当前还没有开始咨询")
        response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_orders")
                .update({"order_status": "completed", "ended_at": _utc_now().isoformat()})
                .eq("id", normalized_order_id)
                .eq("order_status", "in_progress")
                .execute()
            ),
            operation_name="consultation order complete",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="订单状态已变化，请刷新后重试")
        _insert_system_message(supabase, normalized_order_id, "本次咨询已结束，聊天记录会继续保留。")
        return _serialize_order_item(response.data[0])
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Consultation order complete failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="结束咨询暂时不可用") from exc


@router.get("/orders/{order_id}/messages", response_model=MentorConsultationMessageListResponse)
def list_mentor_consultation_messages(
    order_id: UUID,
    limit: int = Query(default=100, ge=1, le=200),
    user_id: str = Depends(get_current_user_id),
) -> MentorConsultationMessageListResponse:
    normalized_order_id = str(order_id)
    supabase = get_supabase_admin()
    try:
        _get_order_participant(supabase, normalized_order_id, user_id)
        response = call_supabase(
            lambda: (
                supabase.table("mentor_consultation_messages")
                .select(CONSULTATION_MESSAGE_FIELDS, count="exact")
                .eq("order_id", normalized_order_id)
                .order("created_at")
                .limit(limit)
                .execute()
            ),
            operation_name="consultation message list",
        )
        rows = response.data or []
        return MentorConsultationMessageListResponse(
            items=[MentorConsultationMessageItem(**serialize_mentor_message(row)) for row in rows],
            count=int(response.count or len(rows)),
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
    supabase = get_supabase_admin()
    try:
        order, participant_role, _ = _get_order_participant(supabase, normalized_order_id, user_id)
        _assert_order_status(order, {"in_progress"}, "本次咨询已结束，暂不能继续发送消息")
        response = call_supabase(
            lambda: supabase.table("mentor_consultation_messages").insert({
                "order_id": normalized_order_id,
                "sender_role": participant_role,
                "sender_user_id": user_id,
                "message_type": "text",
                "content": content,
            }).execute(),
            operation_name="consultation message create",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="消息发送失败")
        return MentorConsultationMessageItem(**serialize_mentor_message(response.data[0]))
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
