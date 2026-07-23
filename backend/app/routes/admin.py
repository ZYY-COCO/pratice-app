from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import ValidationError

from app.db import get_supabase_admin
from app.dependencies import is_admin_profile, require_admin_user, require_question_admin_user
from app.schemas.admin import (
    AdminFeedbackListResponse,
    AdminFeedbackStatusRequest,
    AdminGrantMembershipRequest,
    AdminMeResponse,
    AdminOverviewResponse,
    AdminQuestionBulkFilters,
    AdminQuestionBulkStatusRequest,
    AdminQuestionBulkStatusResponse,
    AdminQuestionCreateRequest,
    AdminQuestionDetailResponse,
    AdminQuestionFileRecognizeResponse,
    AdminQuestionImageImportCommitResponse,
    AdminQuestionImageImportDryRunResponse,
    AdminQuestionImageImportRequest,
    AdminQuestionImageImportResultItem,
    AdminQuestionListResponse,
    AdminQuestionReviewRequest,
    AdminQuestionStatusRequest,
    AdminQuestionUpdateRequest,
    AdminUserDetailResponse,
    AdminUserItem,
    AdminUserListResponse,
    QuestionAdminDashboardQuestionItem,
    QuestionAdminDashboardResponse,
    QuestionAdminPortalMeResponse,
)
from app.services.question_sources import (
    AI_QUESTION_SOURCE_TYPE,
    exclude_ai_generated_questions,
    is_ai_generated_question,
)
from app.services.question_file_recognition import FileRecognitionError, recognize_question_file

router = APIRouter(prefix="/admin", tags=["admin"])

QUESTION_BULK_SELECT_PAGE_SIZE = 500
QUESTION_BULK_UPDATE_CHUNK_SIZE = 100
IMAGE_IMPORT_SOURCE_TYPES = {"real_exam", "ai_generated", "manual", "source_extracted"}
QUESTION_ADMIN_DASHBOARD_LIMIT = 8
QUESTION_ADMIN_ONLINE_WINDOW_MINUTES = 15
CHINA_STANDARD_TIME = timezone(timedelta(hours=8))


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


def _normalize_question_admin_dashboard(raw: object) -> QuestionAdminDashboardResponse:
    payload = raw
    if isinstance(payload, list):
        payload = payload[0] if payload else {}
    if not isinstance(payload, dict):
        payload = {}

    difficult_questions = []
    for item in payload.get("difficult_questions") or []:
        if not isinstance(item, dict) or not item.get("question_id"):
            continue
        difficult_questions.append(QuestionAdminDashboardQuestionItem(
            question_id=str(item.get("question_id")),
            stem=str(item.get("stem") or ""),
            subject=item.get("subject"),
            module=item.get("module"),
            wrong_count=int(item.get("wrong_count") or 0),
            attempt_count=int(item.get("attempt_count") or 0),
            accuracy=float(item.get("accuracy") or 0),
        ))

    return QuestionAdminDashboardResponse(
        today_practicing_users=int(payload.get("today_practicing_users") or 0),
        online_members=int(payload.get("online_members") or 0),
        online_window_minutes=int(
            payload.get("online_window_minutes") or QUESTION_ADMIN_ONLINE_WINDOW_MINUTES
        ),
        difficult_questions=difficult_questions,
    )


def _question_admin_dashboard_fallback(supabase) -> QuestionAdminDashboardResponse:
    """Compatibility path while the dashboard RPC migration is being applied."""

    current = _now()
    shanghai_now = current.astimezone(CHINA_STANDARD_TIME)
    shanghai_day_start = shanghai_now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_start = shanghai_day_start.astimezone(timezone.utc)
    online_start = current - timedelta(minutes=QUESTION_ADMIN_ONLINE_WINDOW_MINUTES)

    today_response = (
        supabase.table("user_answers")
        .select("user_id")
        .gte("created_at", _to_iso(day_start))
        .limit(10000)
        .execute()
    )
    today_users = {
        str(row.get("user_id"))
        for row in today_response.data or []
        if row.get("user_id")
    }

    recent_response = (
        supabase.table("user_answers")
        .select("user_id")
        .gte("created_at", _to_iso(online_start))
        .limit(10000)
        .execute()
    )
    recent_user_ids = list({
        str(row.get("user_id"))
        for row in recent_response.data or []
        if row.get("user_id")
    })
    online_members = 0
    if recent_user_ids:
        member_response = (
            supabase.table("users")
            .select("id,membership_status,membership_expires_at")
            .in_("id", recent_user_ids)
            .execute()
        )
        for member in member_response.data or []:
            if str(member.get("membership_status") or "").lower() != "active":
                continue
            expires_at = _parse_datetime(member.get("membership_expires_at"))
            if expires_at and expires_at <= current:
                continue
            online_members += 1

    answer_response = (
        supabase.table("user_answers")
        .select("question_id,is_correct")
        .limit(20000)
        .execute()
    )
    aggregates: dict[str, dict[str, int]] = defaultdict(lambda: {"attempt_count": 0, "wrong_count": 0})
    for row in answer_response.data or []:
        question_id = str(row.get("question_id") or "")
        if not question_id:
            continue
        aggregates[question_id]["attempt_count"] += 1
        if not bool(row.get("is_correct")):
            aggregates[question_id]["wrong_count"] += 1

    ranked_ids = [
        question_id
        for question_id, _ in sorted(
            aggregates.items(),
            key=lambda pair: (
                pair[1]["wrong_count"],
                pair[1]["attempt_count"],
            ),
            reverse=True,
        )[:QUESTION_ADMIN_DASHBOARD_LIMIT]
    ]
    question_map = {}
    if ranked_ids:
        question_response = (
            supabase.table("questions")
            .select("id,stem,subject,module,source_type")
            .in_("id", ranked_ids)
            .execute()
        )
        question_map = {
            str(row.get("id")): row
            for row in question_response.data or []
            if row.get("id") and not is_ai_generated_question(row)
        }

    difficult_questions = []
    for question_id in ranked_ids:
        question = question_map.get(question_id)
        if not question:
            continue
        stats = aggregates[question_id]
        attempts = stats["attempt_count"]
        correct = max(attempts - stats["wrong_count"], 0)
        difficult_questions.append(QuestionAdminDashboardQuestionItem(
            question_id=question_id,
            stem=str(question.get("stem") or ""),
            subject=question.get("subject"),
            module=question.get("module"),
            wrong_count=stats["wrong_count"],
            attempt_count=attempts,
            accuracy=round((correct / attempts) * 100, 1) if attempts else 0,
        ))

    return QuestionAdminDashboardResponse(
        today_practicing_users=len(today_users),
        online_members=online_members,
        online_window_minutes=QUESTION_ADMIN_ONLINE_WINDOW_MINUTES,
        difficult_questions=difficult_questions,
    )


def _load_question_admin_dashboard(supabase) -> QuestionAdminDashboardResponse:
    try:
        response = supabase.rpc(
            "question_admin_dashboard_snapshot",
            {"p_limit": QUESTION_ADMIN_DASHBOARD_LIMIT},
        ).execute()
        return _normalize_question_admin_dashboard(response.data)
    except Exception:
        return _question_admin_dashboard_fallback(supabase)


def _apply_admin_question_filters(
    query,
    *,
    exam_code: str | None = None,
    subject: str | None = None,
    module: str | None = None,
    question_status: str | None = None,
    review_status: str | None = None,
    exclude_review_status: str | None = None,
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
    if review_status:
        query = query.eq("review_status", review_status)
    if exclude_review_status:
        query = query.neq("review_status", exclude_review_status)
    if difficulty is not None:
        query = query.eq("difficulty", difficulty)
    if search:
        term = search.strip()
        if term:
            query = query.ilike("stem", f"%{term}%")
    return query


def _assert_manageable_question(question: dict) -> None:
    if is_ai_generated_question(question):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI generated training questions are not managed in the official question bank",
        )


def _parse_question_difficulty(value: str | int | None) -> int | None:
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid difficulty")
    if parsed < 1 or parsed > 5:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid difficulty")
    return parsed


def _count_query(query) -> int:
    response = query.limit(1).execute()
    return int(response.count or 0)


def _count_table(supabase, table_name: str) -> int:
    try:
        return _count_query(supabase.table(table_name).select("id", count="exact"))
    except Exception:
        return 0


def _count_admin_questions(supabase) -> int:
    try:
        query = exclude_ai_generated_questions(supabase.table("questions").select("id", count="exact"))
        return _count_query(query)
    except Exception:
        try:
            return _count_query(
                supabase.table("questions")
                .select("id", count="exact")
                .neq("source_type", AI_QUESTION_SOURCE_TYPE)
            )
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


def _get_manageable_question_or_404(supabase, question_id: str) -> dict:
    question = _get_question_or_404(supabase, question_id)
    _assert_manageable_question(question)
    return question


def _assert_bulk_question_ids_manageable(supabase, question_ids: list[str]) -> None:
    for index in range(0, len(question_ids), QUESTION_BULK_SELECT_PAGE_SIZE):
        batch_ids = question_ids[index : index + QUESTION_BULK_SELECT_PAGE_SIZE]
        if not batch_ids:
            continue
        response = (
            supabase.table("questions")
            .select("id, source_type")
            .in_("id", batch_ids)
            .execute()
        )
        if any(is_ai_generated_question(row) for row in (response.data or [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="AI generated training questions are not managed in the official question bank",
            )


def _validation_error_messages(exc: ValidationError) -> list[str]:
    messages: list[str] = []
    for error in exc.errors():
        field = ".".join(str(part) for part in error.get("loc", []) if part != "body")
        reason = str(error.get("msg") or "格式不正确")
        messages.append(f"{field}: {reason}" if field else reason)
    return messages or ["题目字段格式不正确"]


def _build_image_import_create_payload(item) -> AdminQuestionCreateRequest:
    raw = item.model_dump()
    source_type = str(raw.get("source_type") or "source_extracted").strip()
    if source_type not in IMAGE_IMPORT_SOURCE_TYPES:
        raise ValueError(f"source_type 只能是 {', '.join(sorted(IMAGE_IMPORT_SOURCE_TYPES))}")

    difficulty_value = raw.get("difficulty")
    if difficulty_value in (None, ""):
        difficulty = 2
    else:
        try:
            difficulty = int(difficulty_value)
        except (TypeError, ValueError) as exc:
            raise ValueError("difficulty 必须是 1-5 的整数") from exc

    image_name = str(raw.get("image_name") or "").strip()
    review_note = f"图片导入：{image_name}" if image_name else "图片导入"

    return AdminQuestionCreateRequest(
        exam_code=str(raw.get("exam_code") or "").strip(),
        subject=str(raw.get("subject") or "").strip(),
        module=str(raw.get("module") or "").strip(),
        submodule=str(raw.get("submodule") or "").strip(),
        question_type="single_choice",
        stem=str(raw.get("stem") or "").strip(),
        option_a=str(raw.get("option_a") or "").strip(),
        option_b=str(raw.get("option_b") or "").strip(),
        option_c=str(raw.get("option_c") or "").strip(),
        option_d=str(raw.get("option_d") or "").strip(),
        answer=str(raw.get("answer") or "").strip().upper(),
        explanation=str(raw.get("explanation") or "").strip(),
        difficulty=difficulty,
        source_type=source_type,
        source_year=raw.get("source_year"),
        status="archived",
        review_status="pending",
        review_note=review_note,
    )


def _question_duplicate_key(question: dict) -> tuple[str, str, str, str]:
    return (
        str(question.get("stem") or "").strip(),
        str(question.get("subject") or "").strip(),
        str(question.get("module") or "").strip(),
        str(question.get("submodule") or "").strip(),
    )


def _find_existing_question_duplicate_id(supabase, question: dict) -> str | None:
    query = exclude_ai_generated_questions(
        supabase.table("questions")
        .select("id")
        .eq("stem", question["stem"])
        .eq("subject", question["subject"])
        .eq("module", question["module"])
        .eq("submodule", question["submodule"])
    )
    response = query.limit(1).execute()
    if response.data:
        return str(response.data[0].get("id") or "")
    return None


def _dry_run_image_import_questions(
    supabase,
    payload: AdminQuestionImageImportRequest,
    admin_profile: dict,
) -> AdminQuestionImageImportDryRunResponse:
    results: list[AdminQuestionImageImportResultItem] = []
    seen_keys: dict[tuple[str, str, str, str], int] = {}

    for index, item in enumerate(payload.questions):
        errors: list[str] = []
        duplicate_id: str | None = None
        question: dict | None = None
        has_duplicate = False

        try:
            create_payload = _build_image_import_create_payload(item)
            question = _build_question_create_data(create_payload, admin_profile)
            duplicate_key = _question_duplicate_key(question)
            first_index = seen_keys.get(duplicate_key)
            if first_index is not None:
                errors.append(f"与本次导入第 {first_index + 1} 题重复")
                has_duplicate = True
            else:
                seen_keys[duplicate_key] = index

            duplicate_id = _find_existing_question_duplicate_id(supabase, question)
            if duplicate_id:
                errors.append("题库中已存在相同题干、科目、模块和考点")
                has_duplicate = True
        except ValidationError as exc:
            errors.extend(_validation_error_messages(exc))
        except ValueError as exc:
            errors.append(str(exc))
        except HTTPException as exc:
            errors.append(str(exc.detail or "题目校验失败"))

        results.append(
            AdminQuestionImageImportResultItem(
                index=index,
                image_name=item.image_name,
                valid=not errors,
                errors=errors,
                duplicate_id=duplicate_id or ("batch" if has_duplicate else None),
                question=question,
            )
        )

    invalid_count = sum(1 for item in results if not item.valid)
    duplicate_count = sum(1 for item in results if item.duplicate_id)
    valid_count = len(results) - invalid_count
    return AdminQuestionImageImportDryRunResponse(
        total=len(results),
        valid_count=valid_count,
        invalid_count=invalid_count,
        duplicate_count=duplicate_count,
        items=results,
    )


def _build_question_update_data(payload: AdminQuestionUpdateRequest) -> dict:
    data = payload.model_dump(exclude_unset=True)
    text_fields = {
        "exam_code",
        "subject",
        "module",
        "submodule",
        "stem",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "answer",
        "explanation",
    }
    required_text_fields = text_fields - {"explanation"}
    for field in text_fields:
        if field in data and isinstance(data[field], str):
            data[field] = data[field].strip()
    for field in required_text_fields:
        if field in data and not data[field]:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{field} cannot be empty")
    return data


def _build_question_create_data(payload: AdminQuestionCreateRequest, admin_profile: dict) -> dict:
    data = payload.model_dump()
    text_fields = {
        "exam_code",
        "subject",
        "module",
        "submodule",
        "question_type",
        "stem",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "answer",
        "explanation",
        "source_type",
        "review_note",
    }
    required_text_fields = {
        "exam_code",
        "subject",
        "module",
        "submodule",
        "question_type",
        "stem",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "answer",
    }
    for field in text_fields:
        if isinstance(data.get(field), str):
            data[field] = data[field].strip()
    for field in required_text_fields:
        if not data.get(field):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{field} cannot be empty")
    data["answer"] = str(data["answer"]).upper()
    if is_ai_generated_question(data):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Admin-created question source_type cannot be AI generated",
        )
    if data["status"] == "active" and data["review_status"] != "approved":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Published questions must be approved",
        )
    if data["review_status"] == "pending" and data["status"] != "archived":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Pending review questions must be archived",
        )

    current = _now()
    data["explanation"] = data.get("explanation") or ""
    data["source_type"] = data.get("source_type") or "manual"
    data["passage_id"] = None
    data["review_updated_at"] = _to_iso(current)
    if data["review_status"] == "pending":
        data["reviewed_at"] = None
        data["reviewed_by"] = None
    else:
        data["reviewed_at"] = _to_iso(current)
        data["reviewed_by"] = admin_profile.get("id")
    if data["status"] == "archived":
        data["archived_at"] = _to_iso(current)
        data["archived_by"] = admin_profile.get("id")
    else:
        data["archived_at"] = None
        data["archived_by"] = None
    return data


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
        total_questions=_count_admin_questions(supabase),
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


@router.get("/question-portal/me", response_model=QuestionAdminPortalMeResponse)
def question_admin_portal_me(
    profile: dict = Depends(require_question_admin_user),
) -> QuestionAdminPortalMeResponse:
    return QuestionAdminPortalMeResponse(allowed=True, profile=profile)


@router.get("/question-portal/dashboard", response_model=QuestionAdminDashboardResponse)
def question_admin_portal_dashboard(
    _: dict = Depends(require_question_admin_user),
) -> QuestionAdminDashboardResponse:
    return _load_question_admin_dashboard(get_supabase_admin())


@router.get("/questions", response_model=AdminQuestionListResponse)
def admin_questions(
    exam_code: str | None = Query(default=None, max_length=20),
    subject: str | None = Query(default=None, max_length=40),
    module: str | None = Query(default=None, max_length=80),
    question_status: str | None = Query(default=None, alias="status", max_length=20),
    review_status: str | None = Query(default=None, max_length=20),
    exclude_review_status: str | None = Query(default=None, max_length=20),
    search: str | None = Query(default=None, max_length=80),
    difficulty: str | None = Query(default=None, max_length=8),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_question_admin_user),
) -> AdminQuestionListResponse:
    supabase = get_supabase_admin()
    query = exclude_ai_generated_questions(
        supabase.table("questions").select("*", count="exact").order("created_at", desc=True)
    )
    query = _apply_admin_question_filters(
        query,
        exam_code=exam_code,
        subject=subject,
        module=module,
        question_status=question_status,
        review_status=review_status,
        exclude_review_status=exclude_review_status,
        search=search,
        difficulty=_parse_question_difficulty(difficulty),
    )
    response = query.range(offset, offset + limit - 1).execute()
    return AdminQuestionListResponse(items=response.data or [], count=int(response.count or 0))


@router.post("/questions", response_model=AdminQuestionDetailResponse)
def admin_create_question(
    payload: AdminQuestionCreateRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminQuestionDetailResponse:
    supabase = get_supabase_admin()
    insert_data = _build_question_create_data(payload, admin_profile)
    response = supabase.table("questions").insert(insert_data).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question create failed")
    question = response.data[0]
    _log_admin_action(
        supabase,
        admin_profile,
        action="create_question",
        target_type="question",
        target_id=str(question.get("id")) if question.get("id") else None,
        details={
            "status": question.get("status"),
            "review_status": question.get("review_status"),
            "source_type": question.get("source_type"),
        },
    )
    return AdminQuestionDetailResponse(question=question)


@router.post("/questions/image-import/dry-run", response_model=AdminQuestionImageImportDryRunResponse)
def admin_question_image_import_dry_run(
    payload: AdminQuestionImageImportRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminQuestionImageImportDryRunResponse:
    supabase = get_supabase_admin()
    return _dry_run_image_import_questions(supabase, payload, admin_profile)


@router.post("/questions/image-import/recognize", response_model=AdminQuestionFileRecognizeResponse)
async def admin_question_image_import_recognize(
    file: UploadFile = File(...),
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminQuestionFileRecognizeResponse:
    _ = admin_profile
    content = await file.read()
    try:
        result = recognize_question_file(file.filename or "upload", content)
    except FileRecognitionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return AdminQuestionFileRecognizeResponse(**result)


@router.post("/questions/image-import/commit", response_model=AdminQuestionImageImportCommitResponse)
def admin_question_image_import_commit(
    payload: AdminQuestionImageImportRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminQuestionImageImportCommitResponse:
    supabase = get_supabase_admin()
    dry_run = _dry_run_image_import_questions(supabase, payload, admin_profile)
    if dry_run.invalid_count or dry_run.duplicate_count:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "导入前必须先修复无效题目和重复题目",
                "dry_run": dry_run.model_dump(),
            },
        )

    rows = [item.question for item in dry_run.items if item.valid and item.question]
    if not rows:
        return AdminQuestionImageImportCommitResponse(inserted_count=0, questions=[])

    response = supabase.table("questions").insert(rows).execute()
    inserted = response.data or []
    _log_admin_action(
        supabase,
        admin_profile,
        action="image_import_questions",
        target_type="question",
        target_id="bulk",
        details={
            "inserted_count": len(inserted),
            "image_names": [
                item.image_name
                for item in dry_run.items
                if item.image_name
            ][:50],
        },
    )
    return AdminQuestionImageImportCommitResponse(inserted_count=len(inserted), questions=inserted)


@router.patch("/questions/bulk-status", response_model=AdminQuestionBulkStatusResponse)
def admin_bulk_update_question_status(
    payload: AdminQuestionBulkStatusRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminQuestionBulkStatusResponse:
    supabase = get_supabase_admin()
    current = _now()
    filters = payload.filters or AdminQuestionBulkFilters()
    question_ids = list(dict.fromkeys([question_id for question_id in payload.ids if question_id]))

    if not question_ids:
        offset = 0
        while True:
            query = exclude_ai_generated_questions(
                supabase.table("questions").select("id").order("created_at", desc=True)
            )
            query = _apply_admin_question_filters(
                query,
                exam_code=filters.exam_code,
                subject=filters.subject,
                module=filters.module,
                question_status=filters.status,
                review_status=filters.review_status,
                exclude_review_status=filters.exclude_review_status,
                search=filters.search,
                difficulty=filters.difficulty,
            )
            response = query.range(offset, offset + QUESTION_BULK_SELECT_PAGE_SIZE - 1).execute()
            rows = response.data or []
            question_ids.extend(str(row.get("id")) for row in rows if row.get("id"))
            if len(rows) < QUESTION_BULK_SELECT_PAGE_SIZE:
                break
            offset += QUESTION_BULK_SELECT_PAGE_SIZE
    else:
        _assert_bulk_question_ids_manageable(supabase, question_ids)

    if not question_ids:
        return AdminQuestionBulkStatusResponse(updated_count=0)

    update_data = {
        "status": payload.status,
        "archived_at": _to_iso(current) if payload.status == "archived" else None,
        "archived_by": admin_profile.get("id") if payload.status == "archived" else None,
    }
    if payload.status == "active":
        update_data.update({
            "review_status": "approved",
            "review_note": None,
            "reviewed_at": _to_iso(current),
            "reviewed_by": admin_profile.get("id"),
            "review_updated_at": _to_iso(current),
        })
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
def admin_question_detail(
    question_id: str,
    _: dict = Depends(require_question_admin_user),
) -> AdminQuestionDetailResponse:
    supabase = get_supabase_admin()
    return AdminQuestionDetailResponse(question=_get_manageable_question_or_404(supabase, question_id))


@router.patch("/questions/{question_id}", response_model=AdminQuestionDetailResponse)
def admin_update_question(
    question_id: str,
    payload: AdminQuestionUpdateRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminQuestionDetailResponse:
    supabase = get_supabase_admin()
    _get_manageable_question_or_404(supabase, question_id)
    update_data = _build_question_update_data(payload)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No question fields to update")
    response = supabase.table("questions").update(update_data).eq("id", question_id).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question update failed")
    _log_admin_action(
        supabase,
        admin_profile,
        action="update_question",
        target_type="question",
        target_id=question_id,
        details={"fields": sorted(update_data.keys())},
    )
    return AdminQuestionDetailResponse(question=response.data[0])


@router.patch("/questions/{question_id}/status", response_model=AdminQuestionDetailResponse)
def admin_update_question_status(
    question_id: str,
    payload: AdminQuestionStatusRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminQuestionDetailResponse:
    supabase = get_supabase_admin()
    _get_manageable_question_or_404(supabase, question_id)
    current = _now()
    update_data = {
        "status": payload.status,
        "archived_at": _to_iso(current) if payload.status == "archived" else None,
        "archived_by": admin_profile.get("id") if payload.status == "archived" else None,
    }
    if payload.status == "active":
        update_data.update({
            "review_status": "approved",
            "review_note": None,
            "reviewed_at": _to_iso(current),
            "reviewed_by": admin_profile.get("id"),
            "review_updated_at": _to_iso(current),
        })
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


@router.patch("/questions/{question_id}/review", response_model=AdminQuestionDetailResponse)
def admin_update_question_review(
    question_id: str,
    payload: AdminQuestionReviewRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminQuestionDetailResponse:
    supabase = get_supabase_admin()
    _get_manageable_question_or_404(supabase, question_id)
    current = _now()
    review_status = payload.review_status
    if payload.publish and review_status != "approved":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only approved questions can be published")
    review_note = payload.review_note.strip() if payload.review_note else None
    update_data = {
        "review_status": review_status,
        "review_note": review_note,
        "review_updated_at": _to_iso(current),
    }
    if review_status == "pending":
        update_data.update({"reviewed_at": None, "reviewed_by": None})
    else:
        update_data.update({"reviewed_at": _to_iso(current), "reviewed_by": admin_profile.get("id")})
    if review_status == "approved":
        update_data.update({"status": "active", "archived_at": None, "archived_by": None})
    elif review_status in {"needs_changes", "rejected"}:
        update_data.update({
            "status": "archived",
            "archived_at": _to_iso(current),
            "archived_by": admin_profile.get("id"),
        })

    response = supabase.table("questions").update(update_data).eq("id", question_id).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question review update failed")
    _log_admin_action(
        supabase,
        admin_profile,
        action="update_question_review",
        target_type="question",
        target_id=question_id,
        details={
            "review_status": review_status,
            "publish": payload.publish,
            "has_review_note": bool(review_note),
        },
    )
    return AdminQuestionDetailResponse(question=response.data[0])
