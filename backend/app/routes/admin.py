import json
import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from hashlib import sha256

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import ValidationError

from app.db import get_supabase_admin
from app.dependencies import (
    invalidate_user_access_cache,
    is_admin_profile,
    require_admin_user,
    require_question_admin_portal_user,
    require_question_admin_user,
)
from app.schemas.admin import (
    AdminCommunityBulkFeaturedRequest,
    AdminCommunityBulkFeaturedResponse,
    AdminCommunityBulkVisibilityRequest,
    AdminCommunityBulkVisibilityResponse,
    AdminCommunityOverviewResponse,
    AdminCommunityPostDetailResponse,
    AdminCommunityPostItem,
    AdminCommunityPostListResponse,
    AdminCommunityPostVisibilityRequest,
    AdminAnnouncementRecordUpdateRequest,
    AdminFeedbackListResponse,
    AdminFeedbackStatusRequest,
    AdminGrantMembershipRequest,
    AdminMeResponse,
    AdminOverviewResponse,
    AdminQuestionBulkDeleteRequest,
    AdminQuestionBulkDeleteResponse,
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
    AdminQuestionStatsResponse,
    AdminQuestionReviewRequest,
    AdminQuestionStatusRequest,
    AdminQuestionUpdateRequest,
    AdminUserDetailResponse,
    AdminUserItem,
    AdminUserListResponse,
    AdminHomeContentItem,
    AdminHomeContentListResponse,
    AdminHomeContentUpsertRequest,
    AdminMajorCatalogRecordListResponse,
    AdminMajorCatalogRecordUpdateRequest,
    AdminOperationsImportCommitResponse,
    AdminOperationsImportPreviewResponse,
    AdminOperationsImportRunItem,
    AdminOperationsImportRunListResponse,
    AdminScorelineBootstrapRequest,
    AdminScorelineRecordListResponse,
    AdminScorelineRecordUpdateRequest,
    QuestionAdminDashboardQuestionItem,
    QuestionAdminDashboardResponse,
    QuestionAdminPortalMeResponse,
    QuestionAdminPortalMembershipRenewRequest,
    QuestionAdminPortalOperationsOverviewResponse,
    QuestionAdminPortalUserDetailResponse,
    QuestionAdminPortalUserDisableRequest,
    QuestionAdminPortalUserItem,
    QuestionAdminPortalUserListResponse,
    QuestionBankCreateRequest,
    QuestionBankItem,
    QuestionBankListResponse,
    QuestionBankPendingPublishPreviewResponse,
    QuestionBankPublishPendingRequest,
    QuestionBankPublishPendingResponse,
    QuestionBankRenameRequest,
)
from app.services.question_sources import (
    AI_QUESTION_SOURCE_TYPE,
    exclude_ai_generated_questions,
    is_ai_generated_question,
)
from app.services.admin_operations_imports import (
    OperationsImportError,
    build_import_records,
    import_preview_items,
    import_run_statistics,
    parse_operations_xlsx,
)
from app.services.major_catalog import get_major_catalog
from app.services.question_catalog import validate_question_classification
from app.services.question_file_recognition import FileRecognitionError, recognize_question_file
from app.services.school_announcements import get_bundled_announcement_index
from app.services.supabase_resilience import call_supabase, is_transient_supabase_error

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)

QUESTION_BULK_SELECT_PAGE_SIZE = 500
QUESTION_BULK_UPDATE_CHUNK_SIZE = 100
QUESTION_BULK_MAX_SIZE = 20_000
IMAGE_IMPORT_SOURCE_TYPES = {"real_exam", "manual", "source_extracted"}
QUESTION_ADMIN_DASHBOARD_LIMIT = 20
QUESTION_ADMIN_ONLINE_WINDOW_MINUTES = 15
QUESTION_ADMIN_DASHBOARD_SUBJECTS = {"中华文化", "英语运用", "逻辑推理", "数学基础"}
QUESTION_ADMIN_DASHBOARD_SORTS = {"wrong_count", "accuracy", "attempt_count"}
QUESTION_ADMIN_DASHBOARD_PERIOD_DAYS = {0, 7, 30}
QUESTION_ADMIN_DASHBOARD_DEFAULT_MIN_ATTEMPTS = 1
QUESTION_ADMIN_DASHBOARD_FALLBACK_MAX_ROWS = 20_000
QUESTION_ADMIN_DASHBOARD_FALLBACK_ACTIVITY_MAX_ROWS = 10_000
COMMUNITY_ADMIN_POST_LIMIT = 20
COMMUNITY_ADMIN_POST_MAX_LIMIT = 50
COMMUNITY_ADMIN_LEGACY_POST_SCAN_LIMIT = 5_000
COMMUNITY_ADMIN_POST_TYPES = {"all", "chat", "experience"}
COMMUNITY_ADMIN_POST_STATUSES = {"all", "published", "archived", "featured"}
COMMUNITY_ADMIN_POST_SORTS = {
    "newest": ("created_at", True),
    "views": ("view_count", True),
    "likes": ("like_count", True),
    "comments": ("comment_count", True),
}
COMMUNITY_POST_TYPE_MARKER_KEY = "_circle_post_type"
CHINA_STANDARD_TIME = timezone(timedelta(hours=8))
OPERATIONS_IMPORT_BATCH_SIZE = 500
SCORELINE_RECORD_KINDS = {"score", "missing", "unavailable", "official", "multiple", "note"}
SCORELINE_NUMERIC_PATTERN = re.compile(r"^\d+(?:\.\d+)?\s*(?:分)?$")
ANNOUNCEMENT_NOTICE_TYPES = {"brochure", "scoreline_retest"}
MAJOR_CATALOG_EXAM_CODES = {"Z001", "Z002"}
OPERATIONS_IMPORT_DATASETS = {
    "scorelines": {
        "run_table": "historical_scoreline_import_runs",
        "record_table": "historical_scoreline_records",
    },
    "announcements": {
        "run_table": "school_announcement_import_runs",
        "record_table": "school_announcement_records",
    },
    "major-catalog": {
        "run_table": "major_catalog_staging_runs",
        "record_table": "major_catalog_staging_records",
    },
}


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

    difficult_questions_page = max(1, int(payload.get("difficult_questions_page") or 1))
    difficult_questions_page_size = max(
        1,
        min(
            int(payload.get("difficult_questions_page_size") or QUESTION_ADMIN_DASHBOARD_LIMIT),
            QUESTION_ADMIN_DASHBOARD_LIMIT,
        ),
    )
    difficult_questions_count = int(
        payload.get("difficult_questions_count")
        if payload.get("difficult_questions_count") is not None
        else len(difficult_questions)
    )

    return QuestionAdminDashboardResponse(
        today_practicing_users=int(payload.get("today_practicing_users") or 0),
        online_members=int(payload.get("online_members") or 0),
        online_window_minutes=int(
            payload.get("online_window_minutes") or QUESTION_ADMIN_ONLINE_WINDOW_MINUTES
        ),
        registered_users=int(payload.get("registered_users") or 0),
        today_registered_users=int(payload.get("today_registered_users") or 0),
        difficult_questions_count=max(0, difficult_questions_count),
        difficult_questions_page=difficult_questions_page,
        difficult_questions_page_size=difficult_questions_page_size,
        difficult_questions=difficult_questions,
    )


def _apply_question_admin_registration_metrics(
    supabase,
    dashboard: QuestionAdminDashboardResponse,
) -> QuestionAdminDashboardResponse:
    """Attach registration totals without requiring a dashboard RPC migration."""
    current = _now()
    local_now = current.astimezone(CHINA_STANDARD_TIME)
    today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timedelta(days=1)

    try:
        registered_users = _count_table(supabase, "users")
        today_registered_users = _count_query(
            supabase.table("users")
            .select("id", count="exact")
            .gte("created_at", _to_iso(today_start.astimezone(timezone.utc)))
            .lt("created_at", _to_iso(tomorrow_start.astimezone(timezone.utc)))
        )
    except Exception as exc:
        logger.warning("Registration metrics unavailable (error_type=%s)", type(exc).__name__)
        return dashboard

    dashboard.registered_users = registered_users
    dashboard.today_registered_users = today_registered_users
    return dashboard


def _dashboard_question_sort_key(
    item: QuestionAdminDashboardQuestionItem,
    sort_by: str,
) -> tuple[float | int | str, ...]:
    if sort_by == "accuracy":
        return (item.accuracy, -item.wrong_count, -item.attempt_count, item.question_id)
    if sort_by == "attempt_count":
        return (-item.attempt_count, -item.wrong_count, item.accuracy, item.question_id)
    return (-item.wrong_count, -item.attempt_count, item.accuracy, item.question_id)


def _dashboard_fallback_rows(response, *, limit: int, dataset: str) -> list[dict]:
    total = int(response.count or 0)
    if total > limit:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Dashboard fallback cannot safely aggregate {dataset} beyond {limit} rows. "
                "Apply database/question_dashboard_filters.sql."
            ),
        )
    return response.data or []


def _question_admin_dashboard_fallback(
    supabase,
    *,
    subject: str | None = None,
    sort_by: str = "wrong_count",
    min_attempts: int = QUESTION_ADMIN_DASHBOARD_DEFAULT_MIN_ATTEMPTS,
    period_days: int = 0,
    page: int = 1,
    page_size: int = QUESTION_ADMIN_DASHBOARD_LIMIT,
) -> QuestionAdminDashboardResponse:
    """Compatibility path while the dashboard RPC migration is being applied."""

    current = _now()
    normalized_page = max(1, int(page or 1))
    normalized_page_size = max(
        1,
        min(int(page_size or QUESTION_ADMIN_DASHBOARD_LIMIT), QUESTION_ADMIN_DASHBOARD_LIMIT),
    )
    offset = (normalized_page - 1) * normalized_page_size
    shanghai_now = current.astimezone(CHINA_STANDARD_TIME)
    shanghai_day_start = shanghai_now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_start = shanghai_day_start.astimezone(timezone.utc)
    online_start = current - timedelta(minutes=QUESTION_ADMIN_ONLINE_WINDOW_MINUTES)
    period_start = current - timedelta(days=period_days) if period_days else None

    today_response = (
        supabase.table("user_answers")
        .select("user_id", count="exact")
        .gte("created_at", _to_iso(day_start))
        .limit(QUESTION_ADMIN_DASHBOARD_FALLBACK_ACTIVITY_MAX_ROWS)
        .execute()
    )
    today_users = {
        str(row.get("user_id"))
        for row in _dashboard_fallback_rows(
            today_response,
            limit=QUESTION_ADMIN_DASHBOARD_FALLBACK_ACTIVITY_MAX_ROWS,
            dataset="today activity",
        )
        if row.get("user_id")
    }

    recent_response = (
        supabase.table("user_answers")
        .select("user_id", count="exact")
        .gte("created_at", _to_iso(online_start))
        .limit(QUESTION_ADMIN_DASHBOARD_FALLBACK_ACTIVITY_MAX_ROWS)
        .execute()
    )
    recent_user_ids = list({
        str(row.get("user_id"))
        for row in _dashboard_fallback_rows(
            recent_response,
            limit=QUESTION_ADMIN_DASHBOARD_FALLBACK_ACTIVITY_MAX_ROWS,
            dataset="recent activity",
        )
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

    answer_query = supabase.table("user_answers").select("question_id,is_correct", count="exact")
    if period_start:
        answer_query = answer_query.gte("created_at", _to_iso(period_start))
    answer_response = answer_query.limit(QUESTION_ADMIN_DASHBOARD_FALLBACK_MAX_ROWS).execute()
    aggregates: dict[str, dict[str, int]] = defaultdict(lambda: {"attempt_count": 0, "wrong_count": 0})
    for row in _dashboard_fallback_rows(
        answer_response,
        limit=QUESTION_ADMIN_DASHBOARD_FALLBACK_MAX_ROWS,
        dataset="answers",
    ):
        question_id = str(row.get("question_id") or "")
        if not question_id:
            continue
        aggregates[question_id]["attempt_count"] += 1
        if not bool(row.get("is_correct")):
            aggregates[question_id]["wrong_count"] += 1

    question_query = supabase.table("questions").select(
        "id,stem,subject,module,source_type", count="exact"
    )
    if subject:
        question_query = question_query.eq("subject", subject)
    question_response = question_query.limit(QUESTION_ADMIN_DASHBOARD_FALLBACK_MAX_ROWS).execute()
    question_map = {
        str(row.get("id")): row
        for row in _dashboard_fallback_rows(
            question_response,
            limit=QUESTION_ADMIN_DASHBOARD_FALLBACK_MAX_ROWS,
            dataset="questions",
        )
        if row.get("id") and not is_ai_generated_question(row)
    }

    difficult_questions = []
    for question_id, stats in aggregates.items():
        question = question_map.get(question_id)
        if not question:
            continue
        attempts = stats["attempt_count"]
        if attempts < min_attempts:
            continue
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
    difficult_questions.sort(key=lambda item: _dashboard_question_sort_key(item, sort_by))
    difficult_questions_count = len(difficult_questions)

    return QuestionAdminDashboardResponse(
        today_practicing_users=len(today_users),
        online_members=online_members,
        online_window_minutes=QUESTION_ADMIN_ONLINE_WINDOW_MINUTES,
        difficult_questions_count=difficult_questions_count,
        difficult_questions_page=normalized_page,
        difficult_questions_page_size=normalized_page_size,
        difficult_questions=difficult_questions[offset:offset + normalized_page_size],
    )


def _load_question_admin_dashboard(
    supabase,
    *,
    subject: str | None = None,
    sort_by: str = "wrong_count",
    min_attempts: int = QUESTION_ADMIN_DASHBOARD_DEFAULT_MIN_ATTEMPTS,
    period_days: int = 0,
    page: int = 1,
    page_size: int = QUESTION_ADMIN_DASHBOARD_LIMIT,
) -> QuestionAdminDashboardResponse:
    normalized_page = max(1, int(page or 1))
    normalized_page_size = max(
        1,
        min(int(page_size or QUESTION_ADMIN_DASHBOARD_LIMIT), QUESTION_ADMIN_DASHBOARD_LIMIT),
    )
    try:
        response = supabase.rpc(
            "question_admin_dashboard_snapshot",
            {
                "p_limit": normalized_page_size,
                "p_subject": subject,
                "p_sort_by": sort_by,
                "p_min_attempts": min_attempts,
                "p_period_days": period_days,
                "p_offset": (normalized_page - 1) * normalized_page_size,
            },
        ).execute()
        dashboard = _normalize_question_admin_dashboard(response.data)
    except Exception:
        fallback = _question_admin_dashboard_fallback(
            supabase,
            subject=subject,
            sort_by=sort_by,
            min_attempts=min_attempts,
            period_days=period_days,
            page=normalized_page,
            page_size=normalized_page_size,
        )
        try:
            legacy_response = supabase.rpc(
                "question_admin_dashboard_snapshot",
                {"p_limit": QUESTION_ADMIN_DASHBOARD_LIMIT},
            ).execute()
            legacy_dashboard = _normalize_question_admin_dashboard(legacy_response.data)
            fallback.today_practicing_users = legacy_dashboard.today_practicing_users
            fallback.online_members = legacy_dashboard.online_members
            fallback.online_window_minutes = legacy_dashboard.online_window_minutes
        except Exception:
            pass
        dashboard = fallback
    return _apply_question_admin_registration_metrics(supabase, dashboard)


def _apply_admin_question_filters(
    query,
    *,
    question_bank_id: str | None = None,
    exam_code: str | None = None,
    subject: str | None = None,
    module: str | None = None,
    question_status: str | None = None,
    review_status: str | None = None,
    exclude_review_status: str | None = None,
    search: str | None = None,
    difficulty: int | None = None,
):
    if question_bank_id:
        query = query.eq("question_bank_id", question_bank_id)
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


def _community_admin_post_type(row: dict) -> str:
    post_type = str(row.get("post_type") or "").strip()
    if post_type in {"chat", "experience"}:
        return post_type

    media = row.get("media")
    if isinstance(media, list):
        for item in media:
            if not isinstance(item, dict):
                continue
            marker = str(item.get(COMMUNITY_POST_TYPE_MARKER_KEY) or "").strip()
            if marker in {"chat", "experience"}:
                return marker
    return "chat"


def _community_admin_media(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [
        item
        for item in value
        if isinstance(item, dict) and COMMUNITY_POST_TYPE_MARKER_KEY not in item
    ][:9]


def _is_missing_community_post_type_column_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "post_type" in message and ("does not exist" in message or "42703" in message)


def _build_admin_community_post_item(row: dict) -> AdminCommunityPostItem:
    author_name = str(row.get("author_name") or "研友").strip() or "研友"
    return AdminCommunityPostItem(
        id=str(row.get("id") or ""),
        author_id=str(row.get("author_id")) if row.get("author_id") else None,
        author_name=author_name,
        author_avatar=str(row.get("author_avatar") or author_name[:1] or "研"),
        category=str(row.get("category") or "备考日常"),
        post_type=_community_admin_post_type(row),
        title=str(row.get("title") or ""),
        content=str(row.get("content") or ""),
        media=_community_admin_media(row.get("media")),
        like_count=_safe_int(row.get("like_count"), 0),
        comment_count=_safe_int(row.get("comment_count"), 0),
        view_count=_safe_int(row.get("view_count"), 0),
        is_published=bool(row.get("is_published")),
        is_featured=bool(row.get("is_featured")),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def _apply_admin_community_post_filters(
    query,
    *,
    post_status: str,
    post_type: str,
    search: str | None,
):
    if post_status == "published":
        query = query.eq("is_published", True)
    elif post_status == "archived":
        query = query.eq("is_published", False)
    elif post_status == "featured":
        query = query.eq("is_featured", True)
    if post_type != "all":
        query = query.eq("post_type", post_type)
    if search:
        term = search.strip().replace(",", " ").replace("(", " ").replace(")", " ")
        if term:
            query = query.or_(
                f"title.ilike.%{term}%,content.ilike.%{term}%,author_name.ilike.%{term}%"
            )
    return query


def _community_post_detail_row(supabase, post_id: str) -> dict:
    response = call_supabase(
        lambda: (
            supabase.table("circle_community_posts")
            .select("*")
            .eq("id", post_id)
            .limit(1)
            .execute()
        ),
        operation_name="admin community post detail",
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community post not found")
    return response.data[0]


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
    response = call_supabase(
        lambda: query.limit(1).execute(),
        operation_name="admin dashboard count",
    )
    return int(response.count or 0)


def _count_table(supabase, table_name: str) -> int:
    return _count_query(supabase.table(table_name).select("id", count="exact"))


def _count_admin_questions(supabase) -> int:
    try:
        query = exclude_ai_generated_questions(supabase.table("questions").select("id", count="exact"))
        return _count_query(query)
    except Exception as exc:
        if is_transient_supabase_error(exc):
            raise
        try:
            return _count_query(
                supabase.table("questions")
                .select("id", count="exact")
                .neq("source_type", AI_QUESTION_SOURCE_TYPE)
            )
        except Exception:
            raise


def _distinct_active_users(supabase, since: datetime) -> int:
    page_size = 1000
    offset = 0
    user_ids: set[str] = set()
    while True:
        response = call_supabase(
            lambda offset=offset: (
                supabase.table("user_answers")
                .select("user_id")
                .gte("created_at", _to_iso(since))
                .range(offset, offset + page_size - 1)
                .execute()
            ),
            operation_name="admin active-user lookup",
        )
        rows = response.data or []
        user_ids.update(str(row.get("user_id")) for row in rows if row.get("user_id"))
        if len(rows) < page_size:
            break
        offset += page_size
    return len(user_ids)


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


def _normalize_question_bank_name(value: str) -> str:
    name = value.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="题库名称不能为空")
    return name


def _get_question_bank_or_404(supabase, question_bank_id: str) -> dict:
    response = (
        supabase.table("question_banks")
        .select("id,name,created_at,updated_at")
        .eq("id", question_bank_id)
        .limit(1)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题库不存在")
    return response.data[0]


def _list_question_bank_items(supabase) -> list[QuestionBankItem]:
    bank_response = (
        supabase.table("question_banks")
        .select("id,name,created_at,updated_at")
        .order("updated_at", desc=True)
        .limit(1000)
        .execute()
    )
    return [
        QuestionBankItem(
            id=str(row.get("id")),
            name=str(row.get("name") or "未命名题库"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
        for row in bank_response.data or []
        if row.get("id")
    ]


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


def _build_question_status_update_data(question_status: str, admin_profile: dict, current: datetime) -> dict:
    update_data = {
        "status": question_status,
        "archived_at": _to_iso(current) if question_status == "archived" else None,
        "archived_by": admin_profile.get("id") if question_status == "archived" else None,
    }
    if question_status == "active":
        update_data.update({
            "review_status": "approved",
            "review_note": None,
            "reviewed_at": _to_iso(current),
            "reviewed_by": admin_profile.get("id"),
            "review_updated_at": _to_iso(current),
        })
    return update_data


def _update_question_statuses_by_ids(
    supabase,
    question_ids: list[str],
    question_status: str,
    admin_profile: dict,
    current: datetime,
) -> int:
    update_data = _build_question_status_update_data(question_status, admin_profile, current)
    updated_count = 0
    for index in range(0, len(question_ids), QUESTION_BULK_UPDATE_CHUNK_SIZE):
        batch_ids = question_ids[index : index + QUESTION_BULK_UPDATE_CHUNK_SIZE]
        response = supabase.table("questions").update(update_data).in_("id", batch_ids).execute()
        updated_count += len(response.data or batch_ids)
    return updated_count


def _delete_questions_by_ids(supabase, question_ids: list[str]) -> int:
    deleted_count = 0
    for index in range(0, len(question_ids), QUESTION_BULK_UPDATE_CHUNK_SIZE):
        batch_ids = question_ids[index : index + QUESTION_BULK_UPDATE_CHUNK_SIZE]
        response = supabase.table("questions").delete().in_("id", batch_ids).execute()
        deleted_count += len(response.data or batch_ids)
    return deleted_count


def _count_pending_questions_for_bank(supabase, question_bank_id: str) -> int:
    response = (
        exclude_ai_generated_questions(supabase.table("questions").select("id", count="exact"))
        .eq("question_bank_id", question_bank_id)
        .eq("review_status", "pending")
        .limit(1)
        .execute()
    )
    return int(response.count or 0)


def _list_pending_question_ids_for_bank(supabase, question_bank_id: str) -> list[str]:
    first_page = (
        exclude_ai_generated_questions(supabase.table("questions").select("id", count="exact"))
        .eq("question_bank_id", question_bank_id)
        .eq("review_status", "pending")
        .order("created_at", desc=True)
        .range(0, QUESTION_BULK_SELECT_PAGE_SIZE - 1)
        .execute()
    )
    pending_count = int(first_page.count or 0)
    if pending_count > QUESTION_BULK_MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Too many pending questions to publish at once",
        )

    question_ids = [str(row.get("id")) for row in (first_page.data or []) if row.get("id")]
    for offset in range(QUESTION_BULK_SELECT_PAGE_SIZE, pending_count, QUESTION_BULK_SELECT_PAGE_SIZE):
        response = (
            exclude_ai_generated_questions(supabase.table("questions").select("id"))
            .eq("question_bank_id", question_bank_id)
            .eq("review_status", "pending")
            .order("created_at", desc=True)
            .range(offset, offset + QUESTION_BULK_SELECT_PAGE_SIZE - 1)
            .execute()
        )
        question_ids.extend(str(row.get("id")) for row in (response.data or []) if row.get("id"))
    return question_ids


def _validation_error_messages(exc: ValidationError) -> list[str]:
    messages: list[str] = []
    for error in exc.errors():
        field = ".".join(str(part) for part in error.get("loc", []) if part != "body")
        reason = str(error.get("msg") or "格式不正确")
        messages.append(f"{field}: {reason}" if field else reason)
    return messages or ["题目字段格式不正确"]


def _build_image_import_create_payload(
    item,
    question_bank_id: str | None = None,
) -> AdminQuestionCreateRequest:
    raw = item.model_dump()
    source_type = str(raw.get("source_type") or "manual").strip()
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

    source_year_value = raw.get("source_year")
    if source_year_value in (None, ""):
        source_year = None
    else:
        try:
            source_year = int(str(source_year_value).strip())
        except (TypeError, ValueError) as exc:
            raise ValueError("source_year 必须为四位年份") from exc
        if source_year < 1900 or source_year > 2100:
            raise ValueError("source_year 必须在 1900-2100 之间")

    image_name = str(raw.get("image_name") or "").strip()
    excel_row = raw.get("excel_row")
    row_note = f" · Excel 第 {excel_row} 行" if excel_row else ""
    review_note = f"Excel 导入：{image_name}{row_note}" if image_name else f"Excel 导入{row_note}"

    return AdminQuestionCreateRequest(
        question_bank_id=question_bank_id,
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
        source_year=source_year,
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
    if question.get("question_bank_id"):
        query = query.eq("question_bank_id", question["question_bank_id"])
    response = query.limit(1).execute()
    if response.data:
        return str(response.data[0].get("id") or "")
    return None


def _dry_run_image_import_questions(
    supabase,
    payload: AdminQuestionImageImportRequest,
    admin_profile: dict,
) -> AdminQuestionImageImportDryRunResponse:
    if payload.question_bank_id:
        _get_question_bank_or_404(supabase, payload.question_bank_id)

    results: list[AdminQuestionImageImportResultItem] = []
    seen_keys: dict[tuple[str, str, str, str], int] = {}

    for index, item in enumerate(payload.questions):
        errors: list[str] = []
        duplicate_id: str | None = None
        question: dict | None = None
        has_duplicate = False

        try:
            create_payload = _build_image_import_create_payload(item, payload.question_bank_id)
            question = _build_question_create_data(create_payload, admin_profile)
            duplicate_key = _question_duplicate_key(question)
            first_index = seen_keys.get(duplicate_key)
            if first_index is not None:
                first_row = payload.questions[first_index].excel_row
                first_label = f"Excel 第 {first_row} 行" if first_row else f"第 {first_index + 1} 题"
                errors.append(f"与本次导入 {first_label} 重复")
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

        if item.excel_row:
            errors = [f"Excel 第 {item.excel_row} 行：{message}" for message in errors]

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


def _validate_question_classification_data(data: dict) -> None:
    try:
        validate_question_classification(
            exam_code=str(data.get("exam_code") or ""),
            subject=str(data.get("subject") or ""),
            module=str(data.get("module") or ""),
            submodule=str(data.get("submodule") or ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


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
    _validate_question_classification_data(data)
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


def _operations_dataset_tables(dataset: str) -> dict[str, str]:
    normalized = (dataset or "").strip().lower()
    tables = OPERATIONS_IMPORT_DATASETS.get(normalized)
    if not tables:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的数据类型")
    return tables


def _operations_run_item(row: dict | None, *, record_count: int | None = None) -> AdminOperationsImportRunItem:
    source = row or {}
    statistics = source.get("statistics") if isinstance(source.get("statistics"), dict) else {}
    resolved_count = record_count
    if resolved_count is None:
        resolved_count = _safe_int(statistics.get("valid_rows"), 0)
    return AdminOperationsImportRunItem(
        id=str(source.get("id") or ""),
        source_filename=str(source.get("source_filename") or ""),
        source_sha256=str(source.get("source_sha256") or ""),
        statistics=statistics,
        status=str(source.get("status") or "draft"),
        created_by=str(source.get("created_by")) if source.get("created_by") else None,
        published_by=str(source.get("published_by")) if source.get("published_by") else None,
        created_at=source.get("created_at"),
        published_at=source.get("published_at"),
        updated_at=source.get("updated_at"),
        record_count=max(0, _safe_int(resolved_count, 0)),
    )


def _scoreline_numeric_value(score_raw: str, score_kind: str) -> float | None:
    if score_kind != "score":
        return None
    normalized = score_raw.strip()
    if not SCORELINE_NUMERIC_PATTERN.fullmatch(normalized):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="数字分数需要填写纯数字，例如 90 或 90.5",
        )
    numeric_text = normalized[:-1].strip() if normalized.endswith("分") else normalized
    value = float(numeric_text)
    if value > 99_999.99:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="分数数值超出允许范围")
    return value


def _normalize_scoreline_bootstrap_records(payload: AdminScorelineBootstrapRequest) -> list[dict]:
    records_by_key: dict[tuple[str, str, str, str], dict] = {}
    for index, source in enumerate(payload.records, start=1):
        item = source.model_dump()
        score_year = str(item.get("score_year") or "").strip()
        region = str(item.get("region") or "").strip()
        school_name = str(item.get("school_name") or "").strip()
        unit_name = str(item.get("unit_name") or "").strip()
        score_raw = str(item.get("score_raw") or "").strip()
        score_kind = str(item.get("score_kind") or "").strip()
        if not re.fullmatch(r"20\d{2}", score_year):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"第 {index} 条记录的年份不正确")
        if not region or not school_name or not score_raw or score_kind not in SCORELINE_RECORD_KINDS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"第 {index} 条记录字段不完整")
        key = (score_year, region, school_name, unit_name)
        existing = records_by_key.get(key)
        if existing:
            existing["score_raw"] = f"{existing['score_raw']}；{score_raw}"
            existing["score_value"] = None
            existing["score_kind"] = "multiple"
            continue
        records_by_key[key] = {
            "score_year": score_year,
            "region": region,
            "school_name": school_name,
            "unit_name": unit_name,
            "score_raw": score_raw,
            "score_value": _scoreline_numeric_value(score_raw, score_kind),
            "score_kind": score_kind,
            "source_url": None,
            "source_note": None,
            "is_published": False,
        }
    return list(records_by_key.values())


def _snapshot_source_sha256(records: list[dict]) -> str:
    canonical_records = sorted(
        records,
        key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    )
    return sha256(
        json.dumps(canonical_records, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _bundled_announcement_snapshot() -> tuple[str, str, dict, list[dict]]:
    announcement_index = get_bundled_announcement_index()
    announcements = announcement_index.get("announcements")
    if not isinstance(announcements, dict) or not announcements:
        raise ValueError("本地院校公告快照为空")
    if any(not isinstance(item, dict) for item in announcements.values()):
        raise ValueError("本地院校公告快照格式不正确")

    source_items = list(announcements.values())
    records: list[dict] = []
    identities: set[tuple[str, ...]] = set()
    for item in sorted(
        source_items,
        key=lambda source: (
            str(source.get("year") or ""),
            str(source.get("region") or ""),
            str(source.get("school_name") or ""),
            str(source.get("notice_type") or ""),
            str(source.get("notice_date") or ""),
            str(source.get("title") or ""),
        ),
    ):
        notice_year = str(item.get("year") or "").strip()
        region = str(item.get("region") or "").strip()
        school_name = str(item.get("school_name") or "").strip()
        unit_name = str(item.get("unit_name") or "").strip()
        notice_type = str(item.get("notice_type") or "").strip()
        title = str(item.get("title") or "").strip()
        summary = str(item.get("summary") or "").strip()
        notice_date = str(item.get("notice_date") or "").strip() or None
        source_url = str(item.get("source_url") or "").strip() or None
        content_text = str(item.get("content_text") or "").strip()
        if (
            not re.fullmatch(r"20\d{2}", notice_year)
            or not region
            or not school_name
            or not title
            or notice_type not in ANNOUNCEMENT_NOTICE_TYPES
        ):
            raise ValueError("本地院校公告存在字段不完整或类型错误的记录")
        record = {
            "notice_year": notice_year,
            "region": region,
            "school_name": school_name,
            "unit_name": unit_name,
            "notice_type": notice_type,
            "title": title,
            "summary": summary,
            "notice_date": notice_date,
            "source_url": source_url,
            "content_text": content_text,
            "is_published": False,
            "status": "draft",
        }
        identity = tuple(str(record.get(field) or "") for field in record if field not in {"is_published", "status"})
        if identity in identities:
            continue
        identities.add(identity)
        records.append(record)

    if not records:
        raise ValueError("本地院校公告没有可接入的记录")
    years = sorted({record["notice_year"] for record in records})
    statistics = {
        "dataset": "announcements",
        "total_rows": len(source_items),
        "valid_rows": len(records),
        "invalid_rows": 0,
        "duplicate_rows": len(source_items) - len(records),
        "origin": "student_bundled_snapshot",
        "source_version": str(announcement_index.get("version") or ""),
        "year_count": len(years),
        "school_count": len({(record["region"], record["school_name"]) for record in records}),
        "region_count": len({record["region"] for record in records}),
    }
    source_filename = f"学生端院校公告（{'、'.join(years)}）"
    return source_filename, _snapshot_source_sha256(records), statistics, records


def _bundled_major_catalog_snapshot() -> tuple[str, str, dict, list[dict]]:
    catalog = get_major_catalog()
    catalog_year = str(catalog.get("target_year") or "").strip()
    if not re.fullmatch(r"20\d{2}", catalog_year):
        raise ValueError("本地专业目录缺少有效年份")

    schools = catalog.get("schools")
    regions = catalog.get("regions")
    if not isinstance(schools, dict) or not isinstance(regions, list) or not regions:
        raise ValueError("本地专业目录快照格式不正确")

    # The bundled file is the student's default comprehensive 2026 directory.
    # Its year filter is an optional verified-overlay view, not the snapshot
    # that backs the default "全部目录" experience.
    expected_school_ids = {
        str(school_id or "").strip()
        for region_item in regions
        if isinstance(region_item, dict)
        for school_id in (region_item.get("school_ids") or [])
    }
    if not expected_school_ids or "" in expected_school_ids or expected_school_ids != set(schools):
        raise ValueError("本地专业目录院校范围不正确")
    seen_school_ids: set[str] = set()
    department_keys: set[tuple[str, str, str]] = set()
    program_keys: set[tuple[str, str, str, str, str]] = set()
    records: list[dict] = []
    source_row = 0
    for region_item in regions:
        if not isinstance(region_item, dict):
            raise ValueError("本地专业目录地区格式不正确")
        region = str(region_item.get("name") or "").strip()
        region_school_ids = region_item.get("school_ids")
        if not region or not isinstance(region_school_ids, list):
            raise ValueError("本地专业目录地区信息不完整")
        for school_id in region_school_ids:
            normalized_school_id = str(school_id or "").strip()
            if normalized_school_id not in expected_school_ids:
                raise ValueError("本地专业目录地区包含未知院校")
            if normalized_school_id in seen_school_ids:
                raise ValueError("本地专业目录院校重复归属地区")
            school = schools.get(normalized_school_id)
            if not isinstance(school, dict):
                raise ValueError("本地专业目录存在找不到的院校")
            school_name = str(school.get("name") or "").strip()
            departments = school.get("departments")
            if not school_name or not isinstance(departments, list) or not departments:
                raise ValueError("本地专业目录院校信息不完整")
            seen_school_ids.add(normalized_school_id)
            for department in departments:
                if not isinstance(department, dict):
                    raise ValueError("本地专业目录院系格式不正确")
                department_name = str(department.get("name") or "").strip() or "未区分院系所"
                programs = department.get("programs")
                if not isinstance(programs, list) or not programs:
                    raise ValueError("本地专业目录院系缺少专业")
                department_keys.add((region, school_name, department_name))
                for program in programs:
                    if not isinstance(program, dict):
                        raise ValueError("本地专业目录专业格式不正确")
                    program_name = str(program.get("name") or "").strip()
                    program_code = str(program.get("code") or "").strip()
                    directions = program.get("directions")
                    if not program_name or not isinstance(directions, list) or not directions:
                        raise ValueError("本地专业目录专业缺少研究方向")
                    program_keys.add((region, school_name, department_name, program_name, program_code))
                    for direction in directions:
                        if not isinstance(direction, dict):
                            raise ValueError("本地专业目录研究方向格式不正确")
                        direction_name = str(direction.get("name") or "").strip() or "不区分研究方向"
                        exam_code = str(direction.get("exam_code") or "").strip()
                        if exam_code not in MAJOR_CATALOG_EXAM_CODES:
                            raise ValueError("本地专业目录存在无效考试代码")
                        source_row += 1
                        records.append({
                            "catalog_year": catalog_year,
                            "region": region,
                            "school_name": school_name,
                            "department_name": department_name,
                            "program_name": program_name,
                            "program_code": program_code,
                            "direction_name": direction_name,
                            "tutor": str(direction.get("tutor") or "").strip(),
                            "exam_code": exam_code,
                            "degree": str(direction.get("degree") or "").strip(),
                            "study_mode": str(direction.get("study_mode") or "").strip(),
                            "source_row": source_row,
                        })

    if seen_school_ids != expected_school_ids:
        raise ValueError("本地专业目录存在未归属地区的院校")
    if not records:
        raise ValueError("本地专业目录没有可接入的记录")
    statistics = {
        "dataset": "major-catalog",
        "total_rows": len(records),
        "valid_rows": len(records),
        "invalid_rows": 0,
        "catalog_year": catalog_year,
        "origin": "student_bundled_snapshot",
        "source_version": str(catalog.get("version") or ""),
        "region_count": len({record["region"] for record in records}),
        "school_count": len(seen_school_ids),
        "department_count": len(department_keys),
        "program_count": len(program_keys),
        "direction_count": len(records),
    }
    source_filename = f"学生端专业目录（{catalog_year}）"
    return source_filename, _snapshot_source_sha256(records), statistics, records


def _bootstrap_existing_admission_snapshot(
    *,
    dataset: str,
    source_filename: str,
    source_sha256: str,
    statistics: dict,
    records: list[dict],
    action: str,
    target_type: str,
    admin_profile: dict,
) -> AdminOperationsImportCommitResponse:
    tables = _operations_dataset_tables(dataset)
    supabase = get_supabase_admin()
    run: dict | None = None
    retrying_failed_run = False
    try:
        existing_response = call_supabase(
            lambda: (
                supabase.table(tables["run_table"])
                .select("*")
                .eq("source_sha256", source_sha256)
                .limit(1)
                .execute()
            ),
            operation_name="question portal bundled snapshot duplicate check",
        )
        existing_rows = existing_response.data or []
        if existing_rows:
            existing_run = existing_rows[0]
            if str(existing_run.get("status") or "draft") != "failed":
                return AdminOperationsImportCommitResponse(
                    run=_operations_run_item(existing_run),
                    created=False,
                )
            retrying_failed_run = True
            run = existing_run
            call_supabase(
                lambda: (
                    supabase.table(tables["record_table"])
                    .delete()
                    .eq("import_run_id", run.get("id"))
                    .execute()
                ),
                operation_name="question portal bundled snapshot failed cleanup",
            )

        run_data = {
            "source_filename": source_filename,
            "source_sha256": source_sha256,
            "statistics": statistics,
            "status": "draft",
            "created_by": admin_profile.get("id"),
        }
        if dataset == "major-catalog":
            run_data["catalog_year"] = str(statistics.get("catalog_year") or "")
        if retrying_failed_run:
            run_data.update({"published_by": None, "published_at": None})
            run_response = call_supabase(
                lambda: (
                    supabase.table(tables["run_table"])
                    .update(run_data)
                    .eq("id", run.get("id"))
                    .execute()
                ),
                operation_name="question portal bundled snapshot failed retry",
            )
        else:
            run_response = call_supabase(
                lambda: supabase.table(tables["run_table"]).insert(run_data).execute(),
                operation_name="question portal bundled snapshot run create",
            )
        if not run_response.data:
            raise RuntimeError("现有数据版本创建失败")
        run = run_response.data[0]
        record_rows = [{**record, "import_run_id": run.get("id")} for record in records]
        for start in range(0, len(record_rows), OPERATIONS_IMPORT_BATCH_SIZE):
            batch = record_rows[start:start + OPERATIONS_IMPORT_BATCH_SIZE]
            call_supabase(
                lambda batch=batch: supabase.table(tables["record_table"]).insert(batch).execute(),
                operation_name="question portal bundled snapshot record insert",
            )
        _log_admin_action(
            supabase,
            admin_profile,
            action=action,
            target_type=target_type,
            target_id=str(run.get("id") or ""),
            details={**statistics, "record_count": len(records)},
        )
        return AdminOperationsImportCommitResponse(
            run=_operations_run_item(run, record_count=len(records)),
            created=True,
        )
    except HTTPException:
        raise
    except Exception as exc:
        if run and run.get("id"):
            try:
                supabase.table(tables["run_table"]).update({"status": "failed"}).eq("id", run["id"]).execute()
            except Exception:
                pass
        logger.warning("Question portal bundled snapshot bootstrap failed (dataset=%s error_type=%s)", dataset, type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="现有数据接入失败，请稍后重试",
        ) from exc


def _scoreline_update_data(payload: AdminScorelineRecordUpdateRequest, current: dict) -> dict:
    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="没有需要更新的字段")

    for field in ("score_year", "region", "school_name", "unit_name", "score_raw", "score_kind"):
        if field not in update_data:
            continue
        update_data[field] = str(update_data[field] or "").strip()
    if "score_year" in update_data and not re.fullmatch(r"20\d{2}", update_data["score_year"]):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="年份必须为 20xx")
    for field, label in (("region", "地区"), ("school_name", "院校"), ("score_raw", "分数线")):
        if field in update_data and not update_data[field]:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{label}不能为空")
    if "score_kind" in update_data and update_data["score_kind"] not in SCORELINE_RECORD_KINDS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的分数状态")
    for field in ("source_url", "source_note"):
        if field in update_data:
            update_data[field] = str(update_data[field] or "").strip() or None

    resolved_raw = str(update_data.get("score_raw", current.get("score_raw")) or "").strip()
    resolved_kind = str(update_data.get("score_kind", current.get("score_kind")) or "").strip()
    if "score_raw" in update_data or "score_kind" in update_data:
        update_data["score_value"] = _scoreline_numeric_value(resolved_raw, resolved_kind)
    return update_data


def _portal_user_item(row: dict) -> QuestionAdminPortalUserItem:
    return QuestionAdminPortalUserItem(
        id=str(row.get("id") or ""),
        email=row.get("email"),
        phone=row.get("phone"),
        nickname=row.get("nickname"),
        avatar_url=row.get("avatar_url"),
        exam_target=row.get("exam_target"),
        membership_status=row.get("membership_status"),
        membership_plan=row.get("membership_plan"),
        membership_expires_at=row.get("membership_expires_at"),
        disabled_at=row.get("disabled_at"),
        created_at=row.get("created_at"),
        answer_count=max(0, _safe_int(row.get("answer_count"), 0)),
        correct_count=max(0, _safe_int(row.get("correct_count"), 0)),
        wrong_count=max(0, _safe_int(row.get("wrong_count"), 0)),
        accuracy=max(0, float(row.get("accuracy") or 0)),
        last_answer_at=row.get("last_answer_at"),
    )


def _rpc_object(response) -> dict:
    payload = getattr(response, "data", response)
    if isinstance(payload, list):
        payload = payload[0] if payload else {}
    return payload if isinstance(payload, dict) else {}


def _portal_user_list_fallback(
    supabase,
    *,
    search: str | None,
    exam_target: str | None,
    membership_status: str | None,
    account_status: str,
    activity: str,
    registered_from: str | None,
    registered_to: str | None,
    sort_by: str,
    sort_direction: str,
    limit: int,
    offset: int,
) -> QuestionAdminPortalUserListResponse:
    """Small compatibility path while the operations SQL migration is pending."""
    if activity != "all" or sort_by not in {"created_at", "exam_target"}:
        raise RuntimeError("Aggregated user filters require the operations migration")

    query = supabase.table("users").select("*", count="exact")
    if exam_target:
        query = query.eq("exam_target", exam_target)
    if membership_status == "active":
        query = (
            query.eq("membership_status", "active")
            .or_(f"membership_expires_at.is.null,membership_expires_at.gt.{_to_iso(_now())}")
        )
    elif membership_status == "inactive":
        query = query.or_(
            f"membership_status.is.null,membership_status.neq.active,membership_expires_at.lte.{_to_iso(_now())}"
        )
    if account_status == "active":
        query = query.is_("disabled_at", "null")
    elif account_status == "disabled":
        query = query.not_.is_("disabled_at", "null")
    if registered_from:
        query = query.gte("created_at", registered_from)
    if registered_to:
        query = query.lt("created_at", registered_to)
    if search:
        term = search.strip().replace(",", " ").replace("(", " ").replace(")", " ")
        if term:
            query = query.or_(
                f"email.ilike.%{term}%,phone.ilike.%{term}%,nickname.ilike.%{term}%"
            )
    if sort_by == "exam_target":
        query = query.order("exam_target", desc=sort_direction == "desc").order("created_at", desc=True)
    else:
        query = query.order("created_at", desc=sort_direction == "desc")
    response = call_supabase(
        lambda: query.range(offset, offset + limit - 1).execute(),
        operation_name="question portal user fallback list",
    )
    rows = response.data or []
    normalized_rows: list[QuestionAdminPortalUserItem] = []
    for row in rows:
        user_id = str(row.get("id") or "")
        total = _count_query(
            supabase.table("user_answers")
            .select("id", count="exact")
            .eq("user_id", user_id)
        )
        correct = _count_query(
            supabase.table("user_answers")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("is_correct", True)
        )
        latest_response = call_supabase(
            lambda user_id=user_id: (
                supabase.table("user_answers")
                .select("created_at")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            ),
            operation_name="question portal user fallback latest answer",
        )
        answered_at = (latest_response.data or [{}])[0].get("created_at")
        normalized_rows.append(_portal_user_item({
            **row,
            "answer_count": total,
            "correct_count": correct,
            "last_answer_at": answered_at,
            "wrong_count": max(total - correct, 0),
            "accuracy": round((correct / total) * 100, 1) if total else 0,
        }))
    return QuestionAdminPortalUserListResponse(
        items=normalized_rows,
        count=int(response.count or len(normalized_rows)),
    )


def _optional_operations_count(query) -> int:
    try:
        return _count_query(query)
    except Exception:
        return 0


def _operations_overview_fallback(supabase) -> QuestionAdminPortalOperationsOverviewResponse:
    """Keep core user metrics truthful while optional operations tables roll out."""

    current = _now()
    local_now = current.astimezone(CHINA_STANDARD_TIME)
    today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    week_start = current - timedelta(days=7)
    failure_start = current - timedelta(days=30)
    return QuestionAdminPortalOperationsOverviewResponse(
        total_users=_count_table(supabase, "users"),
        new_today=_count_query(
            supabase.table("users").select("id", count="exact").gte("created_at", _to_iso(today_start))
        ),
        new_week=_count_query(
            supabase.table("users").select("id", count="exact").gte("created_at", _to_iso(week_start))
        ),
        active_week=_distinct_active_users(supabase, week_start),
        active_members=_count_query(
            supabase.table("users")
            .select("id", count="exact")
            .eq("membership_status", "active")
            .or_(f"membership_expires_at.is.null,membership_expires_at.gt.{_to_iso(current)}")
        ),
        published_home_items=_optional_operations_count(
            supabase.table("home_content_items").select("id", count="exact").eq("status", "published")
        ),
        published_announcements=_optional_operations_count(
            supabase.table("school_announcement_records").select("id", count="exact").eq("status", "published")
        ),
        scoreline_draft_runs=_optional_operations_count(
            supabase.table("historical_scoreline_import_runs").select("id", count="exact").eq("status", "draft")
        ),
        announcement_draft_runs=_optional_operations_count(
            supabase.table("school_announcement_import_runs").select("id", count="exact").eq("status", "draft")
        ),
        major_catalog_draft_runs=_optional_operations_count(
            supabase.table("major_catalog_staging_runs").select("id", count="exact").eq("status", "draft")
        ),
        recent_import_failures=sum(
            _optional_operations_count(
                supabase.table(table_name)
                .select("id", count="exact")
                .eq("status", "failed")
                .gte("created_at", _to_iso(failure_start))
            )
            for table_name in (
                "historical_scoreline_import_runs",
                "school_announcement_import_runs",
                "major_catalog_staging_runs",
            )
        ),
    )


def _home_content_item(row: dict) -> AdminHomeContentItem:
    return AdminHomeContentItem(
        id=str(row.get("id") or ""),
        slot=str(row.get("slot") or "focus"),
        title=str(row.get("title") or ""),
        subtitle=str(row.get("subtitle") or ""),
        badge=str(row.get("badge") or ""),
        source=str(row.get("source") or ""),
        display_date=row.get("display_date"),
        cover_label=str(row.get("cover_label") or ""),
        tone=str(row.get("tone") or "is-blue"),
        target_url=str(row.get("target_url") or ""),
        route_key=str(row.get("route_key") or ""),
        sort_order=_safe_int(row.get("sort_order"), 0),
        status=str(row.get("status") or "draft"),
        starts_at=row.get("starts_at"),
        ends_at=row.get("ends_at"),
        announcement_record_id=str(row.get("announcement_record_id")) if row.get("announcement_record_id") else None,
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


@router.get("/me", response_model=AdminMeResponse)
def admin_me(profile: dict = Depends(require_admin_user)) -> AdminMeResponse:
    return AdminMeResponse(is_admin=is_admin_profile(profile), profile=profile)


@router.get("/overview", response_model=AdminOverviewResponse)
def admin_overview(_: dict = Depends(require_admin_user)) -> AdminOverviewResponse:
    supabase = get_supabase_admin()
    current = _now()
    try:
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
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin overview unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin data temporarily unavailable",
        ) from exc


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
    try:
        response = call_supabase(
            lambda: query.range(resolved_offset, resolved_offset + resolved_limit - 1).execute(),
            operation_name="admin user list",
        )
        rows = response.data or []
        user_ids = [row.get("id") for row in rows if row.get("id")]
        answer_counts: dict[str, int] = {}
        if user_ids:
            answer_response = call_supabase(
                lambda: (
                    supabase.table("user_answers")
                    .select("user_id")
                    .in_("user_id", user_ids)
                    .limit(10000)
                    .execute()
                ),
                operation_name="admin user answer-count lookup",
            )
            for row in answer_response.data or []:
                user_id = str(row.get("user_id") or "")
                if user_id:
                    answer_counts[user_id] = answer_counts.get(user_id, 0) + 1

        items = [_build_admin_user_item(row, answer_counts.get(str(row.get("id")), 0)) for row in rows if row.get("id")]
        return AdminUserListResponse(items=items, count=int(response.count or len(items)))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin user list unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin user data temporarily unavailable",
        ) from exc


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
    profile: dict = Depends(require_question_admin_portal_user),
) -> QuestionAdminPortalMeResponse:
    return QuestionAdminPortalMeResponse(allowed=True, profile=profile)


@router.get("/question-portal/dashboard", response_model=QuestionAdminDashboardResponse)
def question_admin_portal_dashboard(
    subject: str | None = Query(default=None, max_length=40),
    sort_by: str = Query(default="wrong_count", max_length=30),
    min_attempts: int = Query(default=QUESTION_ADMIN_DASHBOARD_DEFAULT_MIN_ATTEMPTS, ge=1, le=10000),
    period_days: int = Query(default=0, ge=0, le=365),
    page: int = Query(default=1, ge=1, le=50000),
    page_size: int = Query(default=QUESTION_ADMIN_DASHBOARD_LIMIT, ge=1, le=QUESTION_ADMIN_DASHBOARD_LIMIT),
    _: dict = Depends(require_question_admin_portal_user),
) -> QuestionAdminDashboardResponse:
    normalized_subject = subject.strip() if subject else None
    if normalized_subject and normalized_subject not in QUESTION_ADMIN_DASHBOARD_SUBJECTS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的题目类型")

    normalized_sort = sort_by.strip().lower() or "wrong_count"
    if normalized_sort not in QUESTION_ADMIN_DASHBOARD_SORTS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的排序方式")
    if period_days not in QUESTION_ADMIN_DASHBOARD_PERIOD_DAYS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的时间范围")

    return _load_question_admin_dashboard(
        get_supabase_admin(),
        subject=normalized_subject,
        sort_by=normalized_sort,
        min_attempts=min_attempts,
        period_days=period_days,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/question-portal/operations/overview",
    response_model=QuestionAdminPortalOperationsOverviewResponse,
)
def question_admin_portal_operations_overview(
    _: dict = Depends(require_question_admin_portal_user),
) -> QuestionAdminPortalOperationsOverviewResponse:
    supabase = get_supabase_admin()
    try:
        payload = _rpc_object(
            call_supabase(
                lambda: supabase.rpc("question_admin_portal_operations_overview").execute(),
                operation_name="question portal operations overview",
            )
        )
        return QuestionAdminPortalOperationsOverviewResponse(**payload)
    except Exception as exc:
        logger.warning("Question portal operations overview unavailable (error_type=%s)", type(exc).__name__)
        try:
            return _operations_overview_fallback(supabase)
        except Exception as fallback_exc:
            logger.warning("Question portal operations fallback unavailable (error_type=%s)", type(fallback_exc).__name__)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="运营数据暂时不可用",
            ) from fallback_exc


@router.get("/question-portal/users", response_model=QuestionAdminPortalUserListResponse)
def question_admin_portal_users(
    search: str | None = Query(default=None, max_length=80),
    exam_target: str | None = Query(default=None, max_length=12),
    membership_status: str | None = Query(default=None, max_length=30),
    account_status: str = Query(default="all", max_length=20),
    activity: str = Query(default="all", max_length=20),
    registered_from: str | None = Query(default=None, max_length=40),
    registered_to: str | None = Query(default=None, max_length=40),
    sort_by: str = Query(default="created_at", max_length=20),
    sort_direction: str = Query(default="desc", max_length=4),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_question_admin_portal_user),
) -> QuestionAdminPortalUserListResponse:
    normalized_activity = (activity or "all").strip().lower()
    normalized_account_status = (account_status or "all").strip().lower()
    normalized_sort = (sort_by or "created_at").strip().lower()
    normalized_sort_direction = (sort_direction or "desc").strip().lower()
    normalized_exam_target = (exam_target or "").strip().upper()
    normalized_membership_status = (membership_status or "").strip().lower()
    if normalized_activity not in {"all", "active_7d", "inactive"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的活跃度筛选")
    if normalized_sort not in {"created_at", "exam_target", "accuracy", "answer_count", "last_active"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的排序方式")
    if normalized_sort_direction not in {"asc", "desc"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的排序方向")
    if normalized_account_status not in {"all", "active", "disabled"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的账号状态筛选")
    if normalized_exam_target not in {"", "Z001", "Z002"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的考试类型筛选")
    if normalized_membership_status not in {"", "active", "inactive"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的会员状态筛选")
    if registered_from and not _parse_datetime(registered_from):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="注册开始时间格式不正确")
    if registered_to and not _parse_datetime(registered_to):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="注册结束时间格式不正确")

    supabase = get_supabase_admin()
    try:
        payload = _rpc_object(
            call_supabase(
                lambda: supabase.rpc(
                    "question_admin_portal_user_list",
                    {
                        "p_search": search.strip() if search else None,
                        "p_exam_target": normalized_exam_target or None,
                        "p_membership_status": normalized_membership_status or None,
                        "p_account_status": normalized_account_status,
                        "p_activity": normalized_activity,
                        "p_registered_from": registered_from,
                        "p_registered_to": registered_to,
                        "p_sort_by": normalized_sort,
                        "p_sort_direction": normalized_sort_direction,
                        "p_limit": limit,
                        "p_offset": offset,
                    },
                ).execute(),
                operation_name="question portal user list",
            )
        )
        return QuestionAdminPortalUserListResponse(
            items=[_portal_user_item(item) for item in (payload.get("items") or []) if isinstance(item, dict)],
            count=max(0, _safe_int(payload.get("count"), 0)),
        )
    except Exception:
        try:
            return _portal_user_list_fallback(
                supabase,
                search=search,
                exam_target=normalized_exam_target or None,
                membership_status=normalized_membership_status or None,
                account_status=normalized_account_status,
                activity=normalized_activity,
                registered_from=registered_from,
                registered_to=registered_to,
                sort_by=normalized_sort,
                sort_direction=normalized_sort_direction,
                limit=limit,
                offset=offset,
            )
        except Exception as exc:
            logger.warning("Question portal user list unavailable (error_type=%s)", type(exc).__name__)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="用户管理数据暂时不可用，请确认已应用后台运营迁移",
            ) from exc


@router.get("/question-portal/users/{user_id}", response_model=QuestionAdminPortalUserDetailResponse)
def question_admin_portal_user_detail(
    user_id: str,
    _: dict = Depends(require_question_admin_portal_user),
) -> QuestionAdminPortalUserDetailResponse:
    supabase = get_supabase_admin()
    try:
        payload = _rpc_object(
            call_supabase(
                lambda: supabase.rpc("question_admin_portal_user_detail", {"p_user_id": user_id}).execute(),
                operation_name="question portal user detail",
            )
        )
        if not payload.get("profile"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该用户")
        return QuestionAdminPortalUserDetailResponse(**payload)
    except HTTPException:
        raise
    except Exception:
        try:
            legacy = admin_user_detail(user_id, {})
            return QuestionAdminPortalUserDetailResponse(
                profile=legacy.profile,
                answer_summary=legacy.answer_summary,
                subject_accuracy=[],
                recent_answers=legacy.recent_answers,
                membership_orders=legacy.membership_orders,
                admin_actions=legacy.admin_actions,
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("Question portal user detail unavailable (error_type=%s)", type(exc).__name__)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="用户详情暂时不可用",
            ) from exc


@router.patch("/question-portal/users/{user_id}/disabled", response_model=QuestionAdminPortalUserItem)
def question_admin_portal_update_user_disabled(
    user_id: str,
    payload: QuestionAdminPortalUserDisableRequest,
    admin_profile: dict = Depends(require_question_admin_portal_user),
) -> QuestionAdminPortalUserItem:
    if payload.disabled and str(admin_profile.get("id") or "") == user_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不能停用当前登录账号")
    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: (
                supabase.table("users")
                .update({"disabled_at": _to_iso(_now()) if payload.disabled else None})
                .eq("id", user_id)
                .execute()
            ),
            operation_name="question portal user disabled update",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该用户")
        invalidate_user_access_cache(user_id)
        _log_admin_action(
            supabase,
            admin_profile,
            action="disable_user" if payload.disabled else "restore_user",
            target_type="user",
            target_id=user_id,
            details={"disabled": payload.disabled},
        )
        return _portal_user_item(response.data[0])
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Question portal user status update failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="用户状态更新失败",
        ) from exc


@router.post(
    "/question-portal/admission/{dataset}/preview",
    response_model=AdminOperationsImportPreviewResponse,
)
async def question_admin_portal_admission_preview(
    dataset: str,
    file: UploadFile = File(...),
    _: dict = Depends(require_question_admin_portal_user),
) -> AdminOperationsImportPreviewResponse:
    _operations_dataset_tables(dataset)
    filename = str(file.filename or "")
    if not filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="仅支持标准 .xlsx 文件")
    try:
        parsed = parse_operations_xlsx(dataset, await file.read())
    except OperationsImportError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    statistics = import_run_statistics(parsed)
    return AdminOperationsImportPreviewResponse(
        dataset=parsed.dataset,
        source_sha256=parsed.source_sha256,
        total_rows=parsed.total_rows,
        valid_rows=int(statistics["valid_rows"]),
        invalid_rows=int(statistics["invalid_rows"]),
        preview_items=import_preview_items(parsed),
        preview_truncated=parsed.total_rows > 100,
        warnings=parsed.warnings,
    )


@router.post(
    "/question-portal/admission/{dataset}/commit",
    response_model=AdminOperationsImportCommitResponse,
)
async def question_admin_portal_admission_commit(
    dataset: str,
    file: UploadFile = File(...),
    admin_profile: dict = Depends(require_question_admin_portal_user),
) -> AdminOperationsImportCommitResponse:
    tables = _operations_dataset_tables(dataset)
    filename = str(file.filename or "")
    if not filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="仅支持标准 .xlsx 文件")
    try:
        parsed = parse_operations_xlsx(dataset, await file.read())
    except OperationsImportError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    if parsed.errors or not parsed.records:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="请先修复 Excel 中标记的错误行后再提交")

    supabase = get_supabase_admin()
    run: dict | None = None
    retrying_failed_run = False
    try:
        existing_response = call_supabase(
            lambda: (
                supabase.table(tables["run_table"])
                .select("*")
                .eq("source_sha256", parsed.source_sha256)
                .limit(1)
                .execute()
            ),
            operation_name="question portal import duplicate check",
        )
        existing_rows = existing_response.data or []
        if existing_rows:
            existing_run = existing_rows[0]
            if str(existing_run.get("status") or "draft") != "failed":
                return AdminOperationsImportCommitResponse(
                    run=_operations_run_item(existing_run),
                    created=False,
                )
            retrying_failed_run = True
            run = existing_run
            call_supabase(
                lambda: (
                    supabase.table(tables["record_table"])
                    .delete()
                    .eq("import_run_id", run.get("id"))
                    .execute()
                ),
                operation_name="question portal failed import cleanup",
            )

        statistics = import_run_statistics(parsed)
        run_data = {
            "source_filename": filename,
            "source_sha256": parsed.source_sha256,
            "statistics": statistics,
            "status": "draft",
            "created_by": admin_profile.get("id"),
        }
        if parsed.dataset == "major-catalog":
            run_data["catalog_year"] = str(statistics.get("catalog_year") or "")
        if retrying_failed_run:
            run_data.update({"published_by": None, "published_at": None})
            run_response = call_supabase(
                lambda: (
                    supabase.table(tables["run_table"])
                    .update(run_data)
                    .eq("id", run.get("id"))
                    .execute()
                ),
                operation_name="question portal failed import retry",
            )
        else:
            run_response = call_supabase(
                lambda: (
                    supabase.table(tables["run_table"])
                    .insert(run_data)
                    .execute()
                ),
                operation_name="question portal import run create",
            )
        if not run_response.data:
            raise RuntimeError("导入批次创建失败")
        run = run_response.data[0]
        records = build_import_records(parsed, str(run.get("id")))
        for start in range(0, len(records), OPERATIONS_IMPORT_BATCH_SIZE):
            batch = records[start:start + OPERATIONS_IMPORT_BATCH_SIZE]
            call_supabase(
                lambda batch=batch: supabase.table(tables["record_table"]).insert(batch).execute(),
                operation_name="question portal import record insert",
            )
        _log_admin_action(
            supabase,
            admin_profile,
            action="retry_admission_import_run" if retrying_failed_run else "create_admission_import_run",
            target_type=f"admission_{dataset}",
            target_id=str(run.get("id") or ""),
            details=import_run_statistics(parsed),
        )
        return AdminOperationsImportCommitResponse(
            run=_operations_run_item(run, record_count=len(records)),
            created=True,
        )
    except HTTPException:
        raise
    except Exception as exc:
        if run and run.get("id"):
            try:
                supabase.table(tables["run_table"]).update({"status": "failed"}).eq("id", run["id"]).execute()
            except Exception:
                pass
        logger.warning("Question portal import commit failed (dataset=%s error_type=%s)", dataset, type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="导入提交失败，请稍后重试",
        ) from exc


@router.patch("/question-portal/users/{user_id}/membership", response_model=QuestionAdminPortalUserItem)
def question_admin_portal_renew_membership(
    user_id: str,
    payload: QuestionAdminPortalMembershipRenewRequest,
    admin_profile: dict = Depends(require_question_admin_portal_user),
) -> QuestionAdminPortalUserItem:
    supabase = get_supabase_admin()
    try:
        profile = _get_user_or_404(supabase, user_id)
        current = _now()
        current_expires = _parse_datetime(profile.get("membership_expires_at"))
        base_time = current_expires if current_expires and current_expires > current else current
        expires_at = base_time + timedelta(days=payload.months * 30)
        response = call_supabase(
            lambda: (
                supabase.table("users")
                .update(
                    {
                        "membership_status": "active",
                        "membership_plan": "admin_grant",
                        "membership_started_at": profile.get("membership_started_at") or _to_iso(current),
                        "membership_expires_at": _to_iso(expires_at),
                        "membership_updated_at": _to_iso(current),
                    }
                )
                .eq("id", user_id)
                .execute()
            ),
            operation_name="question portal membership renewal",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该用户")
        invalidate_user_access_cache(user_id)
        _log_admin_action(
            supabase,
            admin_profile,
            action="grant_membership",
            target_type="user",
            target_id=user_id,
            details={"months": payload.months, "plan": "admin_grant"},
        )
        return _portal_user_item(response.data[0])
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Question portal membership renewal failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="会员有效期更新失败",
        ) from exc


@router.delete("/question-portal/users/{user_id}/membership", response_model=QuestionAdminPortalUserItem)
def question_admin_portal_cancel_membership(
    user_id: str,
    admin_profile: dict = Depends(require_question_admin_portal_user),
) -> QuestionAdminPortalUserItem:
    supabase = get_supabase_admin()
    try:
        _get_user_or_404(supabase, user_id)
        current = _now()
        response = call_supabase(
            lambda: (
                supabase.table("users")
                .update(
                    {
                        "membership_status": "inactive",
                        "membership_plan": None,
                        "membership_started_at": None,
                        "membership_expires_at": None,
                        "membership_updated_at": _to_iso(current),
                    }
                )
                .eq("id", user_id)
                .execute()
            ),
            operation_name="question portal membership cancellation",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该用户")
        invalidate_user_access_cache(user_id)
        _log_admin_action(
            supabase,
            admin_profile,
            action="cancel_membership",
            target_type="user",
            target_id=user_id,
            details={"reason": "admin_manual_cancel"},
        )
        return _portal_user_item(response.data[0])
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Question portal membership cancellation failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="会员取消失败",
        ) from exc


@router.post(
    "/question-portal/admission/scorelines/bootstrap",
    response_model=AdminOperationsImportCommitResponse,
)
def question_admin_portal_bootstrap_scorelines(
    payload: AdminScorelineBootstrapRequest,
    admin_profile: dict = Depends(require_question_admin_portal_user),
) -> AdminOperationsImportCommitResponse:
    """Bring the pre-existing student scoreline dataset under version control."""
    input_record_count = len(payload.records)
    records = _normalize_scoreline_bootstrap_records(payload)
    canonical_records = sorted(
        records,
        key=lambda item: (
            item["score_year"],
            item["region"],
            item["school_name"],
            item["unit_name"],
            item["score_raw"],
        ),
    )
    source_sha256 = sha256(
        json.dumps(canonical_records, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    years = sorted({item["score_year"] for item in records})
    source_filename = f"学生端历史分数线（{years[0]}-{years[-1]}）" if years else "学生端历史分数线"
    supabase = get_supabase_admin()
    run: dict | None = None
    retrying_failed_run = False
    try:
        existing_response = call_supabase(
            lambda: (
                supabase.table("historical_scoreline_import_runs")
                .select("*")
                .eq("source_sha256", source_sha256)
                .limit(1)
                .execute()
            ),
            operation_name="question portal legacy scoreline duplicate check",
        )
        existing_rows = existing_response.data or []
        if existing_rows:
            existing_run = existing_rows[0]
            if str(existing_run.get("status") or "draft") != "failed":
                return AdminOperationsImportCommitResponse(
                    run=_operations_run_item(existing_run),
                    created=False,
                )
            retrying_failed_run = True
            run = existing_run
            call_supabase(
                lambda: (
                    supabase.table("historical_scoreline_records")
                    .delete()
                    .eq("import_run_id", run.get("id"))
                    .execute()
                ),
                operation_name="question portal legacy scoreline failed cleanup",
            )

        statistics = {
            "dataset": "scorelines",
            "total_rows": input_record_count,
            "valid_rows": len(records),
            "invalid_rows": 0,
            "merged_rows": input_record_count - len(records),
            "origin": "student_static_dataset",
        }
        run_data = {
            "source_filename": source_filename,
            "source_sha256": source_sha256,
            "statistics": statistics,
            "status": "draft",
            "created_by": admin_profile.get("id"),
        }
        if retrying_failed_run:
            run_data.update({"published_by": None, "published_at": None})
            run_response = call_supabase(
                lambda: (
                    supabase.table("historical_scoreline_import_runs")
                    .update(run_data)
                    .eq("id", run.get("id"))
                    .execute()
                ),
                operation_name="question portal legacy scoreline retry",
            )
        else:
            run_response = call_supabase(
                lambda: supabase.table("historical_scoreline_import_runs").insert(run_data).execute(),
                operation_name="question portal legacy scoreline run create",
            )
        if not run_response.data:
            raise RuntimeError("历史分数线版本创建失败")
        run = run_response.data[0]
        record_rows = [{**record, "import_run_id": run.get("id")} for record in records]
        for start in range(0, len(record_rows), OPERATIONS_IMPORT_BATCH_SIZE):
            batch = record_rows[start:start + OPERATIONS_IMPORT_BATCH_SIZE]
            call_supabase(
                lambda batch=batch: supabase.table("historical_scoreline_records").insert(batch).execute(),
                operation_name="question portal legacy scoreline record insert",
            )
        _log_admin_action(
            supabase,
            admin_profile,
            action="bootstrap_legacy_scorelines",
            target_type="admission_scorelines",
            target_id=str(run.get("id") or ""),
            details={"input_record_count": input_record_count, "record_count": len(records), "years": years},
        )
        return AdminOperationsImportCommitResponse(
            run=_operations_run_item(run, record_count=len(records)),
            created=True,
        )
    except HTTPException:
        raise
    except Exception as exc:
        if run and run.get("id"):
            try:
                supabase.table("historical_scoreline_import_runs").update({"status": "failed"}).eq("id", run["id"]).execute()
            except Exception:
                pass
        logger.warning("Question portal legacy scoreline bootstrap failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="现有分数线接入失败，请稍后重试",
        ) from exc


@router.post(
    "/question-portal/admission/announcements/bootstrap",
    response_model=AdminOperationsImportCommitResponse,
)
def question_admin_portal_bootstrap_announcements(
    admin_profile: dict = Depends(require_question_admin_portal_user),
) -> AdminOperationsImportCommitResponse:
    """Bring the bundled student announcement snapshot under version control."""
    try:
        source_filename, source_sha256, statistics, records = _bundled_announcement_snapshot()
        return _bootstrap_existing_admission_snapshot(
            dataset="announcements",
            source_filename=source_filename,
            source_sha256=source_sha256,
            statistics=statistics,
            records=records,
            action="bootstrap_bundled_school_announcements",
            target_type="admission_announcements",
            admin_profile=admin_profile,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Question portal announcement snapshot unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="现有院校公告暂时不可接入",
        ) from exc


@router.post(
    "/question-portal/admission/major-catalog/bootstrap",
    response_model=AdminOperationsImportCommitResponse,
)
def question_admin_portal_bootstrap_major_catalog(
    admin_profile: dict = Depends(require_question_admin_portal_user),
) -> AdminOperationsImportCommitResponse:
    """Bring the bundled student major-catalog snapshot under version control."""
    try:
        source_filename, source_sha256, statistics, records = _bundled_major_catalog_snapshot()
        return _bootstrap_existing_admission_snapshot(
            dataset="major-catalog",
            source_filename=source_filename,
            source_sha256=source_sha256,
            statistics=statistics,
            records=records,
            action="bootstrap_bundled_major_catalog",
            target_type="admission_major_catalog",
            admin_profile=admin_profile,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Question portal major-catalog snapshot unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="现有专业目录暂时不可接入",
        ) from exc


@router.get(
    "/question-portal/admission/scorelines/records",
    response_model=AdminScorelineRecordListResponse,
)
def question_admin_portal_scoreline_records(
    import_run_id: str | None = Query(default=None, max_length=80),
    score_year: str | None = Query(default=None, max_length=4),
    region: str | None = Query(default=None, max_length=60),
    keyword: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_question_admin_portal_user),
) -> AdminScorelineRecordListResponse:
    normalized_year = (score_year or "").strip()
    if normalized_year and not re.fullmatch(r"20\d{2}", normalized_year):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="年份必须为 20xx")
    normalized_region = (region or "").strip()
    normalized_keyword = (keyword or "").strip()
    supabase = get_supabase_admin()
    try:
        query = supabase.table("historical_scoreline_records").select("*", count="exact")
        if import_run_id:
            query = query.eq("import_run_id", import_run_id)
        if normalized_year:
            query = query.eq("score_year", normalized_year)
        if normalized_region:
            query = query.ilike("region", f"%{normalized_region}%")
        if normalized_keyword:
            query = query.ilike("school_name", f"%{normalized_keyword}%")
        response = call_supabase(
            lambda: (
                query.order("score_year", desc=True)
                .order("region")
                .order("school_name")
                .order("unit_name")
                .range(offset, offset + limit - 1)
                .execute()
            ),
            operation_name="question portal scoreline record list",
        )
        filter_query = supabase.table("historical_scoreline_records").select("score_year,region")
        if import_run_id:
            filter_query = filter_query.eq("import_run_id", import_run_id)
        filter_response = call_supabase(
            lambda: filter_query.order("score_year", desc=True).order("region").limit(1000).execute(),
            operation_name="question portal scoreline record filter options",
        )
        filter_rows = filter_response.data or []
        return AdminScorelineRecordListResponse(
            items=response.data or [],
            count=max(0, _safe_int(response.count, 0)),
            filter_years=sorted({str(item.get("score_year") or "").strip() for item in filter_rows if item.get("score_year")}, reverse=True),
            filter_regions=sorted({str(item.get("region") or "").strip() for item in filter_rows if item.get("region")}),
        )
    except Exception as exc:
        logger.warning("Question portal scoreline record list unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="分数线记录暂时不可用",
        ) from exc


@router.patch("/question-portal/admission/scorelines/records/{record_id}", response_model=dict)
def question_admin_portal_update_scoreline_record(
    record_id: str,
    payload: AdminScorelineRecordUpdateRequest,
    admin_profile: dict = Depends(require_question_admin_portal_user),
) -> dict:
    supabase = get_supabase_admin()
    try:
        current_response = call_supabase(
            lambda: (
                supabase.table("historical_scoreline_records")
                .select("*")
                .eq("id", record_id)
                .limit(1)
                .execute()
            ),
            operation_name="question portal scoreline record lookup",
        )
        if not current_response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该分数线记录")
        update_data = _scoreline_update_data(payload, current_response.data[0])
        response = call_supabase(
            lambda: (
                supabase.table("historical_scoreline_records")
                .update(update_data)
                .eq("id", record_id)
                .execute()
            ),
            operation_name="question portal scoreline record update",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该分数线记录")
        _log_admin_action(
            supabase,
            admin_profile,
            action="update_historical_scoreline_record",
            target_type="historical_scoreline",
            target_id=record_id,
            details={"fields": sorted(update_data)},
        )
        return response.data[0]
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Question portal scoreline record update failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="分数线更新失败") from exc


@router.get(
    "/question-portal/admission/major-catalog/records",
    response_model=AdminMajorCatalogRecordListResponse,
)
def question_admin_portal_major_catalog_records(
    import_run_id: str | None = Query(default=None, max_length=80),
    catalog_year: str | None = Query(default=None, max_length=4),
    region: str | None = Query(default=None, max_length=60),
    exam_code: str | None = Query(default=None, max_length=4),
    keyword: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_question_admin_portal_user),
) -> AdminMajorCatalogRecordListResponse:
    normalized_year = (catalog_year or "").strip()
    if normalized_year and not re.fullmatch(r"20\d{2}", normalized_year):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="年份必须为 20xx")
    normalized_region = (region or "").strip()
    normalized_exam_code = (exam_code or "").strip().upper()
    if normalized_exam_code and normalized_exam_code not in MAJOR_CATALOG_EXAM_CODES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="考试类型仅支持 Z001 或 Z002")
    normalized_keyword = (keyword or "").strip()
    search_keyword = " ".join(re.sub(r"[,%().]", " ", normalized_keyword).split())
    supabase = get_supabase_admin()
    try:
        query = supabase.table("major_catalog_staging_records").select("*", count="exact")
        if import_run_id:
            query = query.eq("import_run_id", import_run_id)
        if normalized_year:
            query = query.eq("catalog_year", normalized_year)
        if normalized_region:
            query = query.eq("region", normalized_region)
        if normalized_exam_code:
            query = query.eq("exam_code", normalized_exam_code)
        if search_keyword:
            pattern = f"%{search_keyword}%"
            query = query.or_(
                ",".join(
                    f"{field}.ilike.{pattern}"
                    for field in ("school_name", "department_name", "program_name", "program_code", "direction_name")
                )
            )
        response = call_supabase(
            lambda: (
                query.order("catalog_year", desc=True)
                .order("region")
                .order("school_name")
                .order("department_name")
                .order("program_name")
                .order("source_row")
                .range(offset, offset + limit - 1)
                .execute()
            ),
            operation_name="question portal major catalog record list",
        )
        filter_query = supabase.table("major_catalog_staging_records").select("region,exam_code")
        if import_run_id:
            filter_query = filter_query.eq("import_run_id", import_run_id)
        filter_response = call_supabase(
            lambda: filter_query.order("region").limit(60_000).execute(),
            operation_name="question portal major catalog filter options",
        )
        filter_rows = filter_response.data or []
        return AdminMajorCatalogRecordListResponse(
            items=response.data or [],
            count=max(0, _safe_int(response.count, 0)),
            filter_regions=sorted({str(item.get("region") or "").strip() for item in filter_rows if item.get("region")}),
            filter_exam_codes=sorted({str(item.get("exam_code") or "").strip() for item in filter_rows if item.get("exam_code")}),
        )
    except Exception as exc:
        logger.warning("Question portal major catalog record list unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="专业目录记录暂时不可用",
        ) from exc


@router.patch("/question-portal/admission/major-catalog/records/{record_id}", response_model=dict)
def question_admin_portal_update_major_catalog_record(
    record_id: str,
    payload: AdminMajorCatalogRecordUpdateRequest,
    admin_profile: dict = Depends(require_question_admin_portal_user),
) -> dict:
    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="没有需要更新的字段")
    for field in ("region", "school_name", "department_name", "program_name", "program_code", "direction_name", "tutor", "exam_code", "degree", "study_mode"):
        if field in update_data:
            update_data[field] = str(update_data[field] or "").strip()
    for field, label in (("region", "地区"), ("school_name", "院校"), ("department_name", "院系"), ("program_name", "专业"), ("direction_name", "研究方向")):
        if field in update_data and not update_data[field]:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{label}不能为空")
    if "exam_code" in update_data and update_data["exam_code"] not in MAJOR_CATALOG_EXAM_CODES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="考试类型仅支持 Z001 或 Z002")

    supabase = get_supabase_admin()
    try:
        current_response = call_supabase(
            lambda: (
                supabase.table("major_catalog_staging_records")
                .select("id,import_run_id")
                .eq("id", record_id)
                .limit(1)
                .execute()
            ),
            operation_name="question portal major catalog record lookup",
        )
        if not current_response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该专业目录记录")
        current_record = current_response.data[0]
        response = call_supabase(
            lambda: (
                supabase.table("major_catalog_staging_records")
                .update(update_data)
                .eq("id", record_id)
                .execute()
            ),
            operation_name="question portal major catalog record update",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该专业目录记录")

        run_id = str(current_record.get("import_run_id") or "")
        run_response = call_supabase(
            lambda: (
                supabase.table("major_catalog_staging_runs")
                .select("status")
                .eq("id", run_id)
                .limit(1)
                .execute()
            ),
            operation_name="question portal major catalog run lookup",
        )
        run_status = str((run_response.data or [{}])[0].get("status") or "")
        if run_status == "published":
            call_supabase(
                lambda: supabase.rpc(
                    "question_admin_portal_publish_import_run",
                    {"p_dataset": "major-catalog", "p_run_id": run_id, "p_actor_id": admin_profile.get("id")},
                ).execute(),
                operation_name="question portal major catalog resync",
            )
        _log_admin_action(
            supabase,
            admin_profile,
            action="update_major_catalog_record",
            target_type="major_catalog_record",
            target_id=record_id,
            details={"fields": sorted(update_data), "resynced_student_view": run_status == "published"},
        )
        return response.data[0]
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Question portal major catalog record update failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="专业目录更新失败") from exc


@router.get(
    "/question-portal/admission/{dataset}/runs",
    response_model=AdminOperationsImportRunListResponse,
)
def question_admin_portal_admission_runs(
    dataset: str,
    limit: int = Query(default=30, ge=1, le=100),
    _: dict = Depends(require_question_admin_portal_user),
) -> AdminOperationsImportRunListResponse:
    tables = _operations_dataset_tables(dataset)
    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: (
                supabase.table(tables["run_table"])
                .select("*", count="exact")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            ),
            operation_name="question portal import run list",
        )
        return AdminOperationsImportRunListResponse(
            items=[_operations_run_item(row) for row in (response.data or [])],
            count=max(0, _safe_int(response.count, 0)),
        )
    except Exception as exc:
        logger.warning("Question portal import run list unavailable (dataset=%s error_type=%s)", dataset, type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="导入记录暂时不可用，请确认已应用后台运营迁移",
        ) from exc


@router.post(
    "/question-portal/admission/{dataset}/runs/{run_id}/publish",
    response_model=AdminOperationsImportRunItem,
)
def question_admin_portal_publish_admission_run(
    dataset: str,
    run_id: str,
    admin_profile: dict = Depends(require_question_admin_portal_user),
) -> AdminOperationsImportRunItem:
    tables = _operations_dataset_tables(dataset)
    supabase = get_supabase_admin()
    try:
        run_response = call_supabase(
            lambda: supabase.table(tables["run_table"]).select("*").eq("id", run_id).limit(1).execute(),
            operation_name="question portal import run lookup",
        )
        if not run_response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该导入批次")
        run_status = str(run_response.data[0].get("status") or "draft")
        if run_status == "failed":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="失败批次不可发布，请重新导入")
        if run_status == "published":
            return _operations_run_item(run_response.data[0])
        call_supabase(
            lambda: supabase.rpc(
                "question_admin_portal_publish_import_run",
                {"p_dataset": dataset, "p_run_id": run_id, "p_actor_id": admin_profile.get("id")},
            ).execute(),
            operation_name="question portal import publish",
        )
        refreshed_response = call_supabase(
            lambda: supabase.table(tables["run_table"]).select("*").eq("id", run_id).limit(1).execute(),
            operation_name="question portal import published run lookup",
        )
        row = (refreshed_response.data or [run_response.data[0]])[0]
        _log_admin_action(
            supabase,
            admin_profile,
            action="publish_admission_import_run",
            target_type=f"admission_{dataset}",
            target_id=run_id,
            details={"status": "published"},
        )
        return _operations_run_item(row)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Question portal import publish failed (dataset=%s error_type=%s)", dataset, type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="发布失败，请确认数据迁移已应用后重试",
        ) from exc


@router.get("/question-portal/admission/announcements/records", response_model=dict)
def question_admin_portal_announcement_records(
    import_run_id: str | None = Query(default=None, max_length=80),
    record_status: str | None = Query(default=None, alias="status", max_length=20),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_question_admin_portal_user),
) -> dict:
    supabase = get_supabase_admin()
    if record_status and record_status not in {"draft", "published", "archived"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的公告状态")
    try:
        query = supabase.table("school_announcement_records").select("*", count="exact")
        if import_run_id:
            query = query.eq("import_run_id", import_run_id)
        if record_status:
            query = query.eq("status", record_status)
        response = call_supabase(
            lambda: (
                query.order("sort_order")
                .order("notice_date", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            ),
            operation_name="question portal announcement record list",
        )
        return {"items": response.data or [], "count": max(0, _safe_int(response.count, 0))}
    except Exception as exc:
        logger.warning("Question portal announcement record list unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="院校公告记录暂时不可用",
        ) from exc


@router.patch("/question-portal/admission/announcements/records/{record_id}", response_model=dict)
def question_admin_portal_update_announcement_record(
    record_id: str,
    payload: AdminAnnouncementRecordUpdateRequest,
    admin_profile: dict = Depends(require_question_admin_portal_user),
) -> dict:
    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="没有需要更新的字段")
    supabase = get_supabase_admin()
    try:
        current_response = call_supabase(
            lambda: (
                supabase.table("school_announcement_records")
                .select("id,import_run_id,status")
                .eq("id", record_id)
                .limit(1)
                .execute()
            ),
            operation_name="question portal announcement record lookup",
        )
        if not current_response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该公告")
        current_record = current_response.data[0]
        if update_data.get("status") == "published":
            run_id = str(current_record.get("import_run_id") or "")
            run_response = call_supabase(
                lambda: (
                    supabase.table("school_announcement_import_runs")
                    .select("status")
                    .eq("id", run_id)
                    .limit(1)
                    .execute()
                ),
                operation_name="question portal announcement published run lookup",
            )
            run_status = str((run_response.data or [{}])[0].get("status") or "")
            if run_status != "published":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="请先发布该公告导入版本")
        current = _to_iso(_now())
        if update_data.get("status") == "published":
            update_data.update({"is_published": True, "published_at": current, "published_by": admin_profile.get("id"), "archived_at": None, "archived_by": None})
        elif update_data.get("status") == "archived":
            update_data.update({"is_published": False, "archived_at": current, "archived_by": admin_profile.get("id")})
        elif update_data.get("status") == "draft":
            update_data.update({"is_published": False})
        response = call_supabase(
            lambda: (
                supabase.table("school_announcement_records")
                .update(update_data)
                .eq("id", record_id)
                .execute()
            ),
            operation_name="question portal announcement record update",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该公告")
        _log_admin_action(
            supabase,
            admin_profile,
            action="update_school_announcement_record",
            target_type="school_announcement",
            target_id=record_id,
            details=update_data,
        )
        return response.data[0]
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Question portal announcement record update failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="公告更新失败") from exc


@router.get("/question-portal/home-content", response_model=AdminHomeContentListResponse)
def question_admin_portal_home_content(
    slot: str | None = Query(default=None, max_length=20),
    _: dict = Depends(require_question_admin_portal_user),
) -> AdminHomeContentListResponse:
    normalized_slot = (slot or "").strip().lower()
    if normalized_slot and normalized_slot not in {"focus", "news"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的首页内容位置")
    supabase = get_supabase_admin()
    try:
        query = supabase.table("home_content_items").select("*", count="exact")
        if normalized_slot:
            query = query.eq("slot", normalized_slot)
        response = call_supabase(
            lambda: query.order("slot").order("sort_order").order("created_at", desc=True).execute(),
            operation_name="question portal home content list",
        )
        return AdminHomeContentListResponse(
            items=[_home_content_item(row) for row in (response.data or [])],
            count=max(0, _safe_int(response.count, 0)),
        )
    except Exception as exc:
        logger.warning("Question portal home content list unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="首页运营内容暂时不可用，请确认已应用后台运营迁移",
        ) from exc


def _home_content_write_data(payload: AdminHomeContentUpsertRequest, admin_profile: dict) -> dict:
    data = payload.model_dump()
    data["title"] = str(data.get("title") or "").strip()
    if not data["title"]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="首页内容标题不能为空")
    route_key = str(data.get("route_key") or "").strip()
    if route_key not in {"", "school-announcements", "major-catalog", "application-guide"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的首页内容点击去向")
    data["route_key"] = route_key
    data["target_url"] = str(data.get("target_url") or "").strip()
    if route_key:
        data["target_url"] = ""
    for field in ("starts_at", "ends_at"):
        if data.get(field):
            parsed = _parse_datetime(data[field])
            if not parsed:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{field} 时间格式不正确")
            data[field] = _to_iso(parsed)
    starts_at = _parse_datetime(data.get("starts_at"))
    ends_at = _parse_datetime(data.get("ends_at"))
    if starts_at and ends_at and starts_at >= ends_at:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="下线时间必须晚于生效时间")
    if data.get("target_url") and not data["target_url"].startswith(("https://", "http://")):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="跳转链接必须以 http:// 或 https:// 开头")
    data["updated_by"] = admin_profile.get("id")
    return data


@router.post("/question-portal/home-content", response_model=AdminHomeContentItem)
def question_admin_portal_create_home_content(
    payload: AdminHomeContentUpsertRequest,
    admin_profile: dict = Depends(require_question_admin_portal_user),
) -> AdminHomeContentItem:
    data = _home_content_write_data(payload, admin_profile)
    data["created_by"] = admin_profile.get("id")
    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: supabase.table("home_content_items").insert(data).execute(),
            operation_name="question portal home content create",
        )
        if not response.data:
            raise RuntimeError("首页内容创建失败")
        row = response.data[0]
        _log_admin_action(
            supabase,
            admin_profile,
            action="create_home_content",
            target_type="home_content",
            target_id=str(row.get("id") or ""),
            details={"slot": row.get("slot"), "status": row.get("status")},
        )
        return _home_content_item(row)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Question portal home content create failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="首页内容创建失败") from exc


@router.patch("/question-portal/home-content/{content_id}", response_model=AdminHomeContentItem)
def question_admin_portal_update_home_content(
    content_id: str,
    payload: AdminHomeContentUpsertRequest,
    admin_profile: dict = Depends(require_question_admin_portal_user),
) -> AdminHomeContentItem:
    data = _home_content_write_data(payload, admin_profile)
    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: supabase.table("home_content_items").update(data).eq("id", content_id).execute(),
            operation_name="question portal home content update",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该首页内容")
        row = response.data[0]
        _log_admin_action(
            supabase,
            admin_profile,
            action="update_home_content",
            target_type="home_content",
            target_id=content_id,
            details={"slot": row.get("slot"), "status": row.get("status")},
        )
        return _home_content_item(row)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Question portal home content update failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="首页内容更新失败") from exc


@router.get("/question-portal/community/overview", response_model=AdminCommunityOverviewResponse)
def question_admin_community_overview(
    _: dict = Depends(require_question_admin_portal_user),
) -> AdminCommunityOverviewResponse:
    supabase = get_supabase_admin()
    local_now = datetime.now(CHINA_STANDARD_TIME)
    today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    try:
        return AdminCommunityOverviewResponse(
            total_posts=_count_table(supabase, "circle_community_posts"),
            published_posts=_count_query(
                supabase.table("circle_community_posts")
                .select("id", count="exact")
                .eq("is_published", True)
            ),
            archived_posts=_count_query(
                supabase.table("circle_community_posts")
                .select("id", count="exact")
                .eq("is_published", False)
            ),
            today_posts=_count_query(
                supabase.table("circle_community_posts")
                .select("id", count="exact")
                .gte("created_at", _to_iso(today_start))
            ),
        )
    except Exception as exc:
        logger.warning("Admin community overview unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="社区内容数据暂时不可用",
        ) from exc


@router.get("/question-portal/community/posts", response_model=AdminCommunityPostListResponse)
def question_admin_community_posts(
    post_status: str = Query(default="all", alias="status", max_length=20),
    post_type: str = Query(default="all", max_length=20),
    sort_by: str = Query(default="newest", max_length=20),
    search: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=COMMUNITY_ADMIN_POST_LIMIT, ge=1, le=COMMUNITY_ADMIN_POST_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_question_admin_portal_user),
) -> AdminCommunityPostListResponse:
    normalized_status = post_status.strip().lower() or "all"
    normalized_type = post_type.strip().lower() or "all"
    normalized_sort = sort_by.strip().lower() or "newest"
    if normalized_status not in COMMUNITY_ADMIN_POST_STATUSES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的帖子状态")
    if normalized_type not in COMMUNITY_ADMIN_POST_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的帖子类型")
    if normalized_sort not in COMMUNITY_ADMIN_POST_SORTS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的排序方式")

    order_field, order_desc = COMMUNITY_ADMIN_POST_SORTS[normalized_sort]
    supabase = get_supabase_admin()
    def build_query(*, include_post_type: bool, include_count: bool):
        query = supabase.table("circle_community_posts")
        query = query.select("*", count="exact") if include_count else query.select("*")
        query = _apply_admin_community_post_filters(
            query,
            post_status=normalized_status,
            post_type=normalized_type if include_post_type else "all",
            search=search,
        )
        return query.order(order_field, desc=order_desc).order("created_at", desc=True)

    query = build_query(include_post_type=True, include_count=True)
    try:
        response = call_supabase(
            lambda: query.range(offset, offset + limit - 1).execute(),
            operation_name="admin community post list",
        )
        return AdminCommunityPostListResponse(
            items=[_build_admin_community_post_item(row) for row in (response.data or [])],
            count=int(response.count or 0),
        )
    except HTTPException:
        raise
    except Exception as exc:
        if normalized_type != "all" and _is_missing_community_post_type_column_error(exc):
            try:
                legacy_response = call_supabase(
                    lambda: build_query(include_post_type=False, include_count=False)
                    .range(0, COMMUNITY_ADMIN_LEGACY_POST_SCAN_LIMIT - 1)
                    .execute(),
                    operation_name="admin community post legacy list",
                )
                legacy_rows = [
                    row
                    for row in (legacy_response.data or [])
                    if _community_admin_post_type(row) == normalized_type
                ]
                page_rows = legacy_rows[offset:offset + limit]
                return AdminCommunityPostListResponse(
                    items=[_build_admin_community_post_item(row) for row in page_rows],
                    count=len(legacy_rows),
                )
            except Exception as legacy_exc:
                logger.warning(
                    "Admin community legacy post list unavailable (error_type=%s)",
                    type(legacy_exc).__name__,
                )
        logger.warning("Admin community post list unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="社区帖子列表暂时不可用",
        ) from exc


@router.get("/question-portal/community/posts/{post_id}", response_model=AdminCommunityPostDetailResponse)
def question_admin_community_post_detail(
    post_id: str,
    _: dict = Depends(require_question_admin_portal_user),
) -> AdminCommunityPostDetailResponse:
    supabase = get_supabase_admin()
    try:
        post = _community_post_detail_row(supabase, post_id)
        comments_response = call_supabase(
            lambda: (
                supabase.table("circle_community_comments")
                .select("*")
                .eq("post_id", post_id)
                .order("created_at", desc=False)
                .limit(200)
                .execute()
            ),
            operation_name="admin community post comments",
        )
        comments = [
            {
                "id": str(row.get("id") or ""),
                "author_id": str(row.get("author_id")) if row.get("author_id") else None,
                "author_name": str(row.get("author_name") or "研友"),
                "author_avatar": str(row.get("author_avatar") or "研"),
                "content": str(row.get("content") or ""),
                "like_count": _safe_int(row.get("like_count"), 0),
                "created_at": row.get("created_at"),
            }
            for row in (comments_response.data or [])
        ]
        return AdminCommunityPostDetailResponse(
            post=_build_admin_community_post_item(post),
            comments=comments,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin community post detail unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="社区帖子详情暂时不可用",
        ) from exc


@router.patch(
    "/question-portal/community/posts/bulk-visibility",
    response_model=AdminCommunityBulkVisibilityResponse,
)
def question_admin_bulk_update_community_post_visibility(
    payload: AdminCommunityBulkVisibilityRequest,
    admin_profile: dict = Depends(require_question_admin_portal_user),
) -> AdminCommunityBulkVisibilityResponse:
    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: (
                supabase.table("circle_community_posts")
                .update({"is_published": payload.is_published, "updated_at": _to_iso(_now())})
                .in_("id", payload.ids)
                .execute()
            ),
            operation_name="admin community bulk visibility update",
        )
        updated_count = len(response.data or [])
        _log_admin_action(
            supabase,
            admin_profile,
            action="publish_community_posts" if payload.is_published else "archive_community_posts",
            target_type="community_post",
            target_id=None,
            details={"post_ids": payload.ids, "updated_count": updated_count},
        )
        return AdminCommunityBulkVisibilityResponse(updated_count=updated_count)
    except Exception as exc:
        logger.warning("Admin community bulk visibility update failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="社区帖子状态更新失败",
        ) from exc


@router.patch(
    "/question-portal/community/posts/bulk-featured",
    response_model=AdminCommunityBulkFeaturedResponse,
)
def question_admin_bulk_update_community_post_featured(
    payload: AdminCommunityBulkFeaturedRequest,
    admin_profile: dict = Depends(require_question_admin_portal_user),
) -> AdminCommunityBulkFeaturedResponse:
    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: (
                supabase.table("circle_community_posts")
                .update({"is_featured": payload.is_featured, "updated_at": _to_iso(_now())})
                .in_("id", payload.ids)
                .execute()
            ),
            operation_name="admin community bulk featured update",
        )
        updated_count = len(response.data or [])
        _log_admin_action(
            supabase,
            admin_profile,
            action="feature_community_posts" if payload.is_featured else "unfeature_community_posts",
            target_type="community_post",
            target_id=None,
            details={
                "post_ids": payload.ids,
                "is_featured": payload.is_featured,
                "updated_count": updated_count,
            },
        )
        return AdminCommunityBulkFeaturedResponse(updated_count=updated_count)
    except Exception as exc:
        logger.warning("Admin community bulk featured update failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="社区精选状态更新失败",
        ) from exc


@router.patch(
    "/question-portal/community/posts/{post_id}/visibility",
    response_model=AdminCommunityPostItem,
)
def question_admin_update_community_post_visibility(
    post_id: str,
    payload: AdminCommunityPostVisibilityRequest,
    admin_profile: dict = Depends(require_question_admin_portal_user),
) -> AdminCommunityPostItem:
    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: (
                supabase.table("circle_community_posts")
                .update({"is_published": payload.is_published, "updated_at": _to_iso(_now())})
                .eq("id", post_id)
                .execute()
            ),
            operation_name="admin community post visibility update",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community post not found")
        _log_admin_action(
            supabase,
            admin_profile,
            action="publish_community_post" if payload.is_published else "archive_community_post",
            target_type="community_post",
            target_id=post_id,
            details={"is_published": payload.is_published},
        )
        return _build_admin_community_post_item(response.data[0])
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin community post visibility update failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="社区帖子状态更新失败",
        ) from exc


@router.get("/question-banks", response_model=QuestionBankListResponse)
def admin_question_banks(
    _: dict = Depends(require_question_admin_user),
) -> QuestionBankListResponse:
    return QuestionBankListResponse(items=_list_question_bank_items(get_supabase_admin()))


@router.post("/question-banks", response_model=QuestionBankItem, status_code=status.HTTP_201_CREATED)
def admin_create_question_bank(
    payload: QuestionBankCreateRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> QuestionBankItem:
    supabase = get_supabase_admin()
    name = _normalize_question_bank_name(payload.name)
    response = supabase.table("question_banks").insert({
        "name": name,
        "created_by": admin_profile.get("id"),
    }).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="题库创建失败")
    row = response.data[0]
    _log_admin_action(
        supabase,
        admin_profile,
        action="create_question_bank",
        target_type="question_bank",
        target_id=str(row.get("id") or ""),
        details={"name": name},
    )
    return QuestionBankItem(
        id=str(row.get("id")),
        name=str(row.get("name") or name),
        question_count=0,
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


@router.patch("/question-banks/{question_bank_id}", response_model=QuestionBankItem)
def admin_rename_question_bank(
    question_bank_id: str,
    payload: QuestionBankRenameRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> QuestionBankItem:
    supabase = get_supabase_admin()
    existing = _get_question_bank_or_404(supabase, question_bank_id)
    name = _normalize_question_bank_name(payload.name)
    response = (
        supabase.table("question_banks")
        .update({"name": name})
        .eq("id", question_bank_id)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="题库重命名失败")
    row = response.data[0]
    _log_admin_action(
        supabase,
        admin_profile,
        action="rename_question_bank",
        target_type="question_bank",
        target_id=question_bank_id,
        details={"from": existing.get("name"), "to": name},
    )
    return QuestionBankItem(
        id=str(row.get("id")),
        name=str(row.get("name") or name),
        question_count=0,
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


@router.get(
    "/question-banks/{question_bank_id}/pending-publish-preview",
    response_model=QuestionBankPendingPublishPreviewResponse,
)
def admin_preview_pending_question_publish(
    question_bank_id: str,
    _: dict = Depends(require_question_admin_user),
) -> QuestionBankPendingPublishPreviewResponse:
    supabase = get_supabase_admin()
    question_bank = _get_question_bank_or_404(supabase, question_bank_id)
    return QuestionBankPendingPublishPreviewResponse(
        question_bank_id=question_bank_id,
        question_bank_name=str(question_bank.get("name") or "未命名题库"),
        pending_count=_count_pending_questions_for_bank(supabase, question_bank_id),
    )


@router.post(
    "/question-banks/{question_bank_id}/publish-pending",
    response_model=QuestionBankPublishPendingResponse,
)
def admin_publish_pending_questions_to_bank(
    question_bank_id: str,
    payload: QuestionBankPublishPendingRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> QuestionBankPublishPendingResponse:
    supabase = get_supabase_admin()
    question_bank = _get_question_bank_or_404(supabase, question_bank_id)
    question_ids = _list_pending_question_ids_for_bank(supabase, question_bank_id)
    actual_count = len(question_ids)
    if actual_count != payload.expected_pending_count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pending question count changed. Review the preview and confirm again.",
        )

    current = _now()
    updated_count = _update_question_statuses_by_ids(
        supabase,
        question_ids,
        "active",
        admin_profile,
        current,
    )
    _log_admin_action(
        supabase,
        admin_profile,
        action="publish_pending_questions_to_bank",
        target_type="question_bank",
        target_id=question_bank_id,
        details={
            "question_bank_name": question_bank.get("name"),
            "expected_pending_count": payload.expected_pending_count,
            "updated_count": updated_count,
        },
    )
    return QuestionBankPublishPendingResponse(updated_count=updated_count)


def _count_question_statuses(supabase, question_bank_id: str | None = None) -> AdminQuestionStatsResponse:
    def base_query():
        query = exclude_ai_generated_questions(supabase.table("questions").select("id", count="exact"))
        if question_bank_id:
            query = query.eq("question_bank_id", question_bank_id)
        return query

    return AdminQuestionStatsResponse(
        active=_count_query(base_query().eq("status", "active")),
        archived=_count_query(
            base_query().eq("status", "archived").neq("review_status", "pending")
        ),
        pending_review=_count_query(
            base_query().eq("status", "archived").eq("review_status", "pending")
        ),
    )


@router.get("/question-stats", response_model=AdminQuestionStatsResponse)
def admin_question_stats(
    question_bank_id: str | None = Query(default=None, max_length=80),
    _: dict = Depends(require_question_admin_user),
) -> AdminQuestionStatsResponse:
    return _count_question_statuses(get_supabase_admin(), question_bank_id)


@router.get("/questions", response_model=AdminQuestionListResponse)
def admin_questions(
    question_bank_id: str | None = Query(default=None, max_length=80),
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
        question_bank_id=question_bank_id,
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
    if payload.question_bank_id:
        _get_question_bank_or_404(supabase, payload.question_bank_id)
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
    question_ids = list(dict.fromkeys([question_id for question_id in payload.ids if question_id]))

    if not question_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Bulk status updates require at least one question id",
        )

    _assert_bulk_question_ids_manageable(supabase, question_ids)
    updated_count = _update_question_statuses_by_ids(
        supabase,
        question_ids,
        payload.status,
        admin_profile,
        current,
    )

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
        },
    )
    return AdminQuestionBulkStatusResponse(updated_count=updated_count)


@router.delete("/questions/bulk", response_model=AdminQuestionBulkDeleteResponse)
def admin_bulk_delete_questions(
    payload: AdminQuestionBulkDeleteRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminQuestionBulkDeleteResponse:
    supabase = get_supabase_admin()
    question_ids = list(dict.fromkeys([question_id for question_id in payload.ids if question_id]))

    if not question_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Bulk deletion requires at least one question id",
        )

    _assert_bulk_question_ids_manageable(supabase, question_ids)
    deleted_count = _delete_questions_by_ids(supabase, question_ids)

    _log_admin_action(
        supabase,
        admin_profile,
        action="bulk_delete_questions",
        target_type="question",
        target_id="bulk",
        details={
            "deleted_count": deleted_count,
            "selected_count": len(question_ids),
        },
    )
    return AdminQuestionBulkDeleteResponse(deleted_count=deleted_count)


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
    existing_question = _get_manageable_question_or_404(supabase, question_id)
    update_data = _build_question_update_data(payload)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No question fields to update")
    classification_fields = {"exam_code", "subject", "module", "submodule"}
    if classification_fields.intersection(update_data):
        _validate_question_classification_data({**existing_question, **update_data})
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
    if review_status == "approved" and payload.publish:
        update_data.update({"status": "active", "archived_at": None, "archived_by": None})
    elif review_status == "approved":
        update_data.update({
            "status": "archived",
            "archived_at": _to_iso(current),
            "archived_by": admin_profile.get("id"),
        })
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
