from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import get_supabase_admin
from app.dependencies import is_admin_profile, require_admin_user
from app.schemas.admin import (
    AdminFeedbackListResponse,
    AdminFeedbackStatusRequest,
    AdminGrantMembershipRequest,
    AdminMeResponse,
    AdminOverviewResponse,
    AdminQuestionBulkFilters,
    AdminQuestionBulkStatusRequest,
    AdminQuestionBulkStatusResponse,
    AdminQuestionDetailResponse,
    AdminQuestionListResponse,
    AdminQuestionStatusRequest,
    AdminUserDetailResponse,
    AdminUserItem,
    AdminUserListResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])

QUESTION_BULK_SELECT_PAGE_SIZE = 500
QUESTION_BULK_UPDATE_CHUNK_SIZE = 100


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _apply_admin_question_filters(
    query,
    *,
    exam_code: str | None = None,
    subject: str | None = None,
    module: str | None = None,
    question_status: str | None = None,
    search: str | None = None,
    difficulty: int | None = None,
):
    if exam_code:
        query = query.eq("exam_code", exam_code)
    if subject:
        query = query.eq("subject", subject)
    if module:
        query = query.eq("module", module)
    if question_status:
        query = query.eq("status", question_status)
    if difficulty is not None:
        query = query.eq("difficulty", difficulty)
    if search:
        term = search.strip()
        if term:
            query = query.ilike("stem", f"%{term}%")
    return query


def _count_query(query) -> int:
    response = query.limit(1).execute()
    return int(response.count or 0)


def _count_table(supabase, table_name: str) -> int:
    try:
        return _count_query(supabase.table(table_name).select("id", count="exact"))
    except Exception:
        return 0


def _distinct_active_users(supabase, since: datetime) -> int:
    try:
        response = (
            supabase.table("user_answers")
            .select("user_id")
            .gte("created_at", _to_iso(since))
            .limit(10000)
            .execute()
        )
    except Exception:
        return 0
    return len({row.get("user_id") for row in (response.data or []) if row.get("user_id")})


def _safe_int(value: int | str | None, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _build_admin_user_item(row: dict, answer_count: int = 0) -> AdminUserItem:
    return AdminUserItem(
        id=str(row.get("id")),
        email=row.get("email"),
        phone=row.get("phone"),
        nickname=row.get("nickname"),
        auth_provider=row.get("auth_provider"),
        exam_target=row.get("exam_target"),
        role=row.get("role") or "user",
        disabled_at=row.get("disabled_at"),
        membership_status=row.get("membership_status"),
        membership_plan=row.get("membership_plan"),
        membership_expires_at=row.get("membership_expires_at"),
        created_at=row.get("created_at"),
        answer_count=answer_count,
    )


def _get_user_or_404(supabase, user_id: str) -> dict:
    response = supabase.table("users").select("*").eq("id", user_id).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return response.data[0]


def _get_question_or_404(supabase, question_id: str) -> dict:
    response = supabase.table("questions").select("*").eq("id", question_id).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return response.data[0]


def _log_admin_action(supabase, admin_profile: dict, action: str, target_type: str, target_id: str | None, details: dict | None = None) -> None:
    row = {
        "admin_user_id": admin_profile.get("id"),
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "details": details or {},
    }
    try:
        supabase.table("admin_action_logs").insert(row).execute()
    except Exception:
        # The audit-log migration may not be applied yet; admin actions should still work.
        return


@router.get("/me", response_model=AdminMeResponse)
def admin_me(profile: dict = Depends(require_admin_user)) -> AdminMeResponse:
    return AdminMeResponse(is_admin=is_admin_profile(profile), profile=profile)


@router.get("/overview", response_model=AdminOverviewResponse)
def admin_overview(_: dict = Depends(require_admin_user)) -> AdminOverviewResponse:
    supabase = get_supabase_admin()
    current = _now()
    total_feedback = _count_table(supabase, "beta_feedback")
    return AdminOverviewResponse(
        total_users=_count_table(supabase, "users"),
        active_today=_distinct_active_users(supabase, current - timedelta(days=1)),
        active_week=_distinct_active_users(supabase, current - timedelta(days=7)),
        active_month=_distinct_active_users(supabase, current - timedelta(days=30)),
        active_year=_distinct_active_users(supabase, current - timedelta(days=365)),
        total_questions=_count_table(supabase, "questions"),
        total_feedback=total_feedback,
        pending_feedback=_count_query(
            supabase.table("beta_feedback").select("id", count="exact").eq("status", "open")
        ),
        active_members=_count_query(
            supabase.table("users").select("id", count="exact").eq("membership_status", "active")
        ),
    )


@router.get("/users", response_model=AdminUserListResponse)
def admin_users(
    search: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_admin_user),
) -> AdminUserListResponse:
    supabase = get_supabase_admin()
    resolved_limit = _safe_int(limit, 20)
    resolved_offset = _safe_int(offset, 0)

    query = supabase.table("users").select("*", count="exact").order("created_at", desc=True)
    if search:
        term = search.strip()
        if term:
            query = query.ilike("email", f"%{term}%")
    response = query.range(resolved_offset, resolved_offset + resolved_limit - 1).execute()
    rows = response.data or []
    user_ids = [row.get("id") for row in rows if row.get("id")]
    answer_counts: dict[str, int] = {}
    if user_ids:
        try:
            answer_response = (
                supabase.table("user_answers")
                .select("user_id")
                .in_("user_id", user_ids)
                .limit(10000)
                .execute()
            )
            for row in answer_response.data or []:
                user_id = str(row.get("user_id") or "")
                if user_id:
                    answer_counts[user_id] = answer_counts.get(user_id, 0) + 1
        except Exception:
            answer_counts = {}

    items = [_build_admin_user_item(row, answer_counts.get(str(row.get("id")), 0)) for row in rows if row.get("id")]
    return AdminUserListResponse(items=items, count=int(response.count or len(items)))


@router.get("/users/{user_id}", response_model=AdminUserDetailResponse)
def admin_user_detail(user_id: str, _: dict = Depends(require_admin_user)) -> AdminUserDetailResponse:
    supabase = get_supabase_admin()
    profile = _get_user_or_404(supabase, user_id)
    answer_summary = {"total": 0, "correct": 0, "wrong": 0, "accuracy": 0}
    recent_answers: list[dict] = []
    membership_orders: list[dict] = []
    admin_actions: list[dict] = []

    try:
        total_response = (
            supabase.table("user_answers")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        correct_response = (
            supabase.table("user_answers")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("is_correct", True)
            .limit(1)
            .execute()
        )
        total = int(total_response.count or 0)
        correct = int(correct_response.count or 0)
        answer_summary = {
            "total": total,
            "correct": correct,
            "wrong": max(total - correct, 0),
            "accuracy": round((correct / total) * 100, 1) if total else 0,
        }
    except Exception:
        answer_summary = {"total": 0, "correct": 0, "wrong": 0, "accuracy": 0}

    try:
        answer_response = (
            supabase.table("user_answers")
            .select("id,question_id,selected_answer,is_correct,used_time,created_at,questions(exam_code,subject,module,submodule,stem)")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        recent_answers = answer_response.data or []
    except Exception:
        recent_answers = []

    try:
        order_response = (
            supabase.table("membership_orders")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        membership_orders = order_response.data or []
    except Exception:
        membership_orders = []

    try:
        action_response = (
            supabase.table("admin_action_logs")
            .select("*")
            .eq("target_type", "user")
            .eq("target_id", user_id)
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        admin_actions = action_response.data or []
    except Exception:
        admin_actions = []

    return AdminUserDetailResponse(
        profile=profile,
        answer_summary=answer_summary,
        recent_answers=recent_answers,
        membership_orders=membership_orders,
        admin_actions=admin_actions,
    )


@router.patch("/users/{user_id}/membership", response_model=AdminUserItem)
def admin_grant_membership(
    user_id: str,
    payload: AdminGrantMembershipRequest,
    admin_profile: dict = Depends(require_admin_user),
) -> AdminUserItem:
    supabase = get_supabase_admin()
    profile = _get_user_or_404(supabase, user_id)
    current = _now()
    current_expires = _parse_datetime(profile.get("membership_expires_at"))
    base_time = current_expires if current_expires and current_expires > current else current
    expires_at = base_time + timedelta(days=payload.months * 30)
    update_data = {
        "membership_status": "active",
        "membership_plan": payload.plan,
        "membership_started_at": profile.get("membership_started_at") or _to_iso(current),
        "membership_expires_at": _to_iso(expires_at),
        "membership_updated_at": _to_iso(current),
    }
    updated_response = supabase.table("users").update(update_data).eq("id", user_id).execute()
    if not updated_response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Membership update failed")

    _log_admin_action(
        supabase,
        admin_profile,
        action="grant_membership",
        target_type="user",
        target_id=user_id,
        details={"months": payload.months, "plan": payload.plan},
    )
    row = updated_response.data[0]
    return _build_admin_user_item(row)


@router.delete("/users/{user_id}/membership", response_model=AdminUserItem)
def admin_cancel_membership(
    user_id: str,
    admin_profile: dict = Depends(require_admin_user),
) -> AdminUserItem:
    supabase = get_supabase_admin()
    _get_user_or_404(supabase, user_id)
    current = _now()
    update_data = {
        "membership_status": "inactive",
        "membership_plan": None,
        "membership_started_at": None,
        "membership_expires_at": None,
        "membership_updated_at": _to_iso(current),
    }
    updated_response = supabase.table("users").update(update_data).eq("id", user_id).execute()
    if not updated_response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Membership cancel failed")

    _log_admin_action(
        supabase,
        admin_profile,
        action="cancel_membership",
        target_type="user",
        target_id=user_id,
        details={"reason": "admin_manual_cancel"},
    )
    row = updated_response.data[0]
    return _build_admin_user_item(row)


@router.get("/feedback", response_model=AdminFeedbackListResponse)
def admin_feedback(
    feedback_status: str | None = Query(default=None, alias="status", max_length=20),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_admin_user),
) -> AdminFeedbackListResponse:
    supabase = get_supabase_admin()
    query = supabase.table("beta_feedback").select("*", count="exact").order("created_at", desc=True)
    if feedback_status:
        query = query.eq("status", feedback_status)
    response = query.range(offset, offset + limit - 1).execute()
    return AdminFeedbackListResponse(items=response.data or [], count=int(response.count or 0))


@router.patch("/feedback/{feedback_id}/status", response_model=dict)
def admin_update_feedback_status(
    feedback_id: str,
    payload: AdminFeedbackStatusRequest,
    admin_profile: dict = Depends(require_admin_user),
) -> dict:
    supabase = get_supabase_admin()
    update_data = {
        "status": payload.status,
        "admin_note": payload.admin_note,
        "handled_by": admin_profile.get("id"),
        "handled_at": _to_iso(_now()) if payload.status != "open" else None,
    }
    response = supabase.table("beta_feedback").update(update_data).eq("id", feedback_id).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    _log_admin_action(
        supabase,
        admin_profile,
        action="update_feedback_status",
        target_type="feedback",
        target_id=feedback_id,
        details={"status": payload.status},
    )
    return response.data[0]


@router.get("/questions", response_model=AdminQuestionListResponse)
def admin_questions(
    exam_code: str | None = Query(default=None, max_length=20),
    subject: str | None = Query(default=None, max_length=40),
    module: str | None = Query(default=None, max_length=80),
    question_status: str | None = Query(default=None, alias="status", max_length=20),
    search: str | None = Query(default=None, max_length=80),
    difficulty: int | None = Query(default=None, ge=1, le=5),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_admin_user),
) -> AdminQuestionListResponse:
    supabase = get_supabase_admin()
    query = supabase.table("questions").select("*", count="exact").order("created_at", desc=True)
    query = _apply_admin_question_filters(
        query,
        exam_code=exam_code,
        subject=subject,
        module=module,
        question_status=question_status,
        search=search,
        difficulty=difficulty,
    )
    response = query.range(offset, offset + limit - 1).execute()
    return AdminQuestionListResponse(items=response.data or [], count=int(response.count or 0))


@router.patch("/questions/bulk-status", response_model=AdminQuestionBulkStatusResponse)
def admin_bulk_update_question_status(
    payload: AdminQuestionBulkStatusRequest,
    admin_profile: dict = Depends(require_admin_user),
) -> AdminQuestionBulkStatusResponse:
    supabase = get_supabase_admin()
    current = _now()
    filters = payload.filters or AdminQuestionBulkFilters()
    question_ids = list(dict.fromkeys([question_id for question_id in payload.ids if question_id]))

    if not question_ids:
        offset = 0
        while True:
            query = supabase.table("questions").select("id").order("created_at", desc=True)
            query = _apply_admin_question_filters(
                query,
                exam_code=filters.exam_code,
                subject=filters.subject,
                module=filters.module,
                question_status=filters.status,
                search=filters.search,
                difficulty=filters.difficulty,
            )
            response = query.range(offset, offset + QUESTION_BULK_SELECT_PAGE_SIZE - 1).execute()
            rows = response.data or []
            question_ids.extend(str(row.get("id")) for row in rows if row.get("id"))
            if len(rows) < QUESTION_BULK_SELECT_PAGE_SIZE:
                break
            offset += QUESTION_BULK_SELECT_PAGE_SIZE

    if not question_ids:
        return AdminQuestionBulkStatusResponse(updated_count=0)

    update_data = {
        "status": payload.status,
        "archived_at": _to_iso(current) if payload.status == "archived" else None,
        "archived_by": admin_profile.get("id") if payload.status == "archived" else None,
    }
    updated_count = 0
    for index in range(0, len(question_ids), QUESTION_BULK_UPDATE_CHUNK_SIZE):
        batch_ids = question_ids[index : index + QUESTION_BULK_UPDATE_CHUNK_SIZE]
        response = supabase.table("questions").update(update_data).in_("id", batch_ids).execute()
        updated_count += len(response.data or batch_ids)

    _log_admin_action(
        supabase,
        admin_profile,
        action="bulk_update_question_status",
        target_type="question",
        target_id="bulk",
        details={
            "status": payload.status,
            "updated_count": updated_count,
            "selected_count": len(question_ids),
            "filters": filters.model_dump(exclude_none=True),
        },
    )
    return AdminQuestionBulkStatusResponse(updated_count=updated_count)


@router.get("/questions/{question_id}", response_model=AdminQuestionDetailResponse)
def admin_question_detail(question_id: str, _: dict = Depends(require_admin_user)) -> AdminQuestionDetailResponse:
    supabase = get_supabase_admin()
    return AdminQuestionDetailResponse(question=_get_question_or_404(supabase, question_id))


@router.patch("/questions/{question_id}/status", response_model=AdminQuestionDetailResponse)
def admin_update_question_status(
    question_id: str,
    payload: AdminQuestionStatusRequest,
    admin_profile: dict = Depends(require_admin_user),
) -> AdminQuestionDetailResponse:
    supabase = get_supabase_admin()
    _get_question_or_404(supabase, question_id)
    current = _now()
    update_data = {
        "status": payload.status,
        "archived_at": _to_iso(current) if payload.status == "archived" else None,
        "archived_by": admin_profile.get("id") if payload.status == "archived" else None,
    }
    response = supabase.table("questions").update(update_data).eq("id", question_id).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question status update failed")
    _log_admin_action(
        supabase,
        admin_profile,
        action="update_question_status",
        target_type="question",
        target_id=question_id,
        details={"status": payload.status},
    )
    return AdminQuestionDetailResponse(question=response.data[0])
