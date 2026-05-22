from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import get_supabase_admin
from app.dependencies import is_admin_profile, require_admin_user
from app.schemas.admin import (
    AdminFeedbackListResponse,
    AdminGrantMembershipRequest,
    AdminMeResponse,
    AdminOverviewResponse,
    AdminQuestionListResponse,
    AdminUserItem,
    AdminUserListResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _now() -> datetime:
    return datetime.now(UTC)


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
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


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
        pending_feedback=total_feedback,
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

    items = [
        AdminUserItem(
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
            answer_count=answer_counts.get(str(row.get("id")), 0),
        )
        for row in rows
        if row.get("id")
    ]
    return AdminUserListResponse(items=items, count=int(response.count or len(items)))


@router.patch("/users/{user_id}/membership", response_model=AdminUserItem)
def admin_grant_membership(
    user_id: str,
    payload: AdminGrantMembershipRequest,
    admin_profile: dict = Depends(require_admin_user),
) -> AdminUserItem:
    supabase = get_supabase_admin()
    profile_response = supabase.table("users").select("*").eq("id", user_id).limit(1).execute()
    if not profile_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    profile = profile_response.data[0]
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
        answer_count=0,
    )


@router.get("/feedback", response_model=AdminFeedbackListResponse)
def admin_feedback(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_admin_user),
) -> AdminFeedbackListResponse:
    supabase = get_supabase_admin()
    response = (
        supabase.table("beta_feedback")
        .select("*", count="exact")
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return AdminFeedbackListResponse(items=response.data or [], count=int(response.count or 0))


@router.get("/questions", response_model=AdminQuestionListResponse)
def admin_questions(
    exam_code: str | None = Query(default=None, max_length=20),
    subject: str | None = Query(default=None, max_length=40),
    module: str | None = Query(default=None, max_length=80),
    search: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_admin_user),
) -> AdminQuestionListResponse:
    supabase = get_supabase_admin()
    query = supabase.table("questions").select("*", count="exact").order("created_at", desc=True)
    if exam_code:
        query = query.eq("exam_code", exam_code)
    if subject:
        query = query.eq("subject", subject)
    if module:
        query = query.eq("module", module)
    if search:
        term = search.strip()
        if term:
            query = query.ilike("stem", f"%{term}%")
    response = query.range(offset, offset + limit - 1).execute()
    return AdminQuestionListResponse(items=response.data or [], count=int(response.count or 0))
