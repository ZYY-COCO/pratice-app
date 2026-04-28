from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query

from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.reports import (
    AbilityReportResponse,
    AbilityStatItem,
    LeaderboardItem,
    LeaderboardResponse,
    LearningSummaryResponse,
)
from app.services.reports import build_ability_item

router = APIRouter(prefix="/report", tags=["能力报告"])

PUBLIC_SUBJECTS = {"中华文化", "英语运用"}
PAGE_SIZE = 1000


def belongs_to_exam(question: dict | None, exam_code: str | None) -> bool:
    if not exam_code:
        return True
    question = question or {}
    question_exam_code = question.get("exam_code")
    if question_exam_code == exam_code:
        return True
    return question_exam_code == "COMMON" and question.get("subject") in PUBLIC_SUBJECTS


def safe_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def get_display_name(profile: dict) -> str:
    nickname = profile.get("nickname")
    if isinstance(nickname, str) and nickname.strip():
        return nickname.strip()
    email = str(profile.get("email") or "")
    prefix = email.split("@", maxsplit=1)[0]
    if prefix:
        return f"{prefix[:2]}***"
    return "学习用户"


def fetch_user_profiles(supabase) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while True:
        chunk = (
            supabase.table("users")
            .select("id, email, nickname, avatar_url")
            .order("created_at")
            .range(offset, offset + PAGE_SIZE - 1)
            .execute()
            .data
            or []
        )
        rows.extend(chunk)
        if len(chunk) < PAGE_SIZE:
            return rows
        offset += PAGE_SIZE


def fetch_ability_rows(supabase, exam_code: str | None) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while True:
        query = supabase.table("ability_stats").select("user_id, total_count, correct_count")
        if exam_code:
            query = query.eq("exam_code", exam_code)
        chunk = query.range(offset, offset + PAGE_SIZE - 1).execute().data or []
        rows.extend(chunk)
        if len(chunk) < PAGE_SIZE:
            return rows
        offset += PAGE_SIZE


def fetch_weekly_answer_rows(supabase, week_start: datetime) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while True:
        chunk = (
            supabase.table("user_answers")
            .select("user_id, questions(exam_code, subject)")
            .gte("created_at", week_start.isoformat())
            .range(offset, offset + PAGE_SIZE - 1)
            .execute()
            .data
            or []
        )
        rows.extend(chunk)
        if len(chunk) < PAGE_SIZE:
            return rows
        offset += PAGE_SIZE


@router.get("/ability", response_model=AbilityReportResponse)
def ability_report(
    user_id: str = Depends(get_current_user_id),
    exam_code: str | None = None,
) -> AbilityReportResponse:
    supabase = get_supabase_admin()
    query = supabase.table("ability_stats").select("*").eq("user_id", user_id)
    if exam_code:
        query = query.eq("exam_code", exam_code)

    response = query.order("accuracy").execute()
    items = [AbilityStatItem(**build_ability_item(row)) for row in response.data]
    weak_items = [item for item in items if item.accuracy < 60][:5]
    return AbilityReportResponse(items=items, weak_items=weak_items)


@router.get("/summary", response_model=LearningSummaryResponse)
def learning_summary(
    user_id: str = Depends(get_current_user_id),
    exam_code: str | None = None,
) -> LearningSummaryResponse:
    supabase = get_supabase_admin()

    ability_query = supabase.table("ability_stats").select("total_count, correct_count").eq("user_id", user_id)
    if exam_code:
        ability_query = ability_query.eq("exam_code", exam_code)
    ability_response = ability_query.execute()

    total_answers = sum(int(row.get("total_count") or 0) for row in ability_response.data)
    correct_answers = sum(int(row.get("correct_count") or 0) for row in ability_response.data)
    accuracy = round(correct_answers / total_answers * 100, 2) if total_answers else 0

    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    week_start = datetime.combine(
        (now - timedelta(days=now.weekday())).date(),
        datetime.min.time(),
        tzinfo=ZoneInfo("Asia/Shanghai"),
    ).astimezone(timezone.utc)
    weekly_response = (
        supabase.table("user_answers")
        .select("id, is_correct, questions(exam_code, subject)")
        .eq("user_id", user_id)
        .gte("created_at", week_start.isoformat())
        .limit(1000)
        .execute()
    )
    weekly_rows = weekly_response.data
    if exam_code:
        weekly_rows = [row for row in weekly_rows if belongs_to_exam(row.get("questions"), exam_code)]
    weekly_answers = len(weekly_rows)
    weekly_correct_answers = sum(1 for row in weekly_rows if row.get("is_correct"))
    weekly_accuracy = round(weekly_correct_answers / weekly_answers * 100, 2) if weekly_answers else 0

    wrong_response = (
        supabase.table("wrong_questions")
        .select("id, questions(exam_code, subject)")
        .eq("user_id", user_id)
        .limit(1000)
        .execute()
    )
    wrong_rows = wrong_response.data
    if exam_code:
        wrong_rows = [row for row in wrong_rows if belongs_to_exam(row.get("questions"), exam_code)]

    return LearningSummaryResponse(
        exam_code=exam_code,
        total_answers=total_answers,
        correct_answers=correct_answers,
        accuracy=accuracy,
        wrong_question_count=len(wrong_rows),
        weekly_answers=weekly_answers,
        weekly_correct_answers=weekly_correct_answers,
        weekly_accuracy=weekly_accuracy,
    )


@router.get("/leaderboard", response_model=LeaderboardResponse)
def leaderboard(
    _user_id: str = Depends(get_current_user_id),
    exam_code: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
) -> LeaderboardResponse:
    supabase = get_supabase_admin()
    users = fetch_user_profiles(supabase)
    ability_rows = fetch_ability_rows(supabase, exam_code)

    stats_by_user: dict[str, dict[str, int]] = {}
    for row in ability_rows:
        row_user_id = row.get("user_id")
        if not row_user_id:
            continue
        current = stats_by_user.setdefault(str(row_user_id), {"total": 0, "correct": 0})
        current["total"] += safe_int(row.get("total_count"))
        current["correct"] += safe_int(row.get("correct_count"))

    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    week_start = datetime.combine(
        (now - timedelta(days=now.weekday())).date(),
        datetime.min.time(),
        tzinfo=ZoneInfo("Asia/Shanghai"),
    ).astimezone(timezone.utc)
    weekly_rows = fetch_weekly_answer_rows(supabase, week_start)
    weekly_by_user: dict[str, int] = {}
    for row in weekly_rows:
        if exam_code and not belongs_to_exam(row.get("questions"), exam_code):
            continue
        row_user_id = row.get("user_id")
        if not row_user_id:
            continue
        row_user_id = str(row_user_id)
        weekly_by_user[row_user_id] = weekly_by_user.get(row_user_id, 0) + 1

    ranking_rows = []
    for profile in users:
        row_user_id = str(profile.get("id") or "")
        if not row_user_id:
            continue
        stats = stats_by_user.get(row_user_id, {"total": 0, "correct": 0})
        total_answers = stats["total"]
        correct_answers = stats["correct"]
        accuracy = round(correct_answers / total_answers * 100, 2) if total_answers else 0
        nickname = get_display_name(profile)
        ranking_rows.append(
            {
                "user_id": row_user_id,
                "nickname": nickname,
                "avatar_url": profile.get("avatar_url"),
                "total_answers": total_answers,
                "correct_answers": correct_answers,
                "accuracy": accuracy,
                "weekly_answers": weekly_by_user.get(row_user_id, 0),
            }
        )

    ranking_rows.sort(
        key=lambda row: (
            -row["accuracy"],
            -row["weekly_answers"],
            -row["total_answers"],
            row["nickname"],
        )
    )

    items = [
        LeaderboardItem(rank=index + 1, **row)
        for index, row in enumerate(ranking_rows[:limit])
    ]
    return LeaderboardResponse(items=items, total_users=len(ranking_rows))
