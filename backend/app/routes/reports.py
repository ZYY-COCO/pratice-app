import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config import get_settings
from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.reports import (
    AbilityReportResponse,
    AbilityStatItem,
    DailyStudyLeaderboardItem,
    DailyStudyLeaderboardResponse,
    LeaderboardItem,
    LeaderboardResponse,
    LearningSummaryResponse,
    LearningTrendPoint,
    PlatformPracticeTrendPoint,
    PlatformPracticeTrendResponse,
    StudyGoalResponse,
    StudyGoalUpdateRequest,
    StudyAdviceResponse,
    StudySubjectAdvice,
    SubjectWeeklyChange,
)
from app.services.question_sources import is_ai_generated_question
from app.services.reports import build_ability_item
from app.services.supabase_resilience import call_supabase, is_missing_supabase_relation_error

router = APIRouter(prefix="/report", tags=["能力报告"])

PUBLIC_SUBJECTS = {"中华文化", "英语运用"}
EXAM_SUBJECTS = {
    "Z001": ["中华文化", "英语运用", "逻辑推理"],
    "Z002": ["中华文化", "英语运用", "数学基础"],
}
PAGE_SIZE = 1000
LEARNING_ACTIVITY_LIMIT = 5000
PLATFORM_PRACTICE_TREND_DAYS = 7
DAILY_STUDY_MAX_SECONDS_PER_ANSWER = 15 * 60
DEFAULT_STUDY_GOAL_DAILY_MINUTES = 60
DEFAULT_STUDY_GOAL_WEEKLY_QUESTIONS = 300


def get_app_timezone():
    try:
        return ZoneInfo("Asia/Shanghai")
    except ZoneInfoNotFoundError:
        return timezone(timedelta(hours=8))


APP_TIMEZONE = get_app_timezone()


def belongs_to_exam(
    question: dict | None,
    exam_code: str | None,
    *,
    stats_exam_code: str | None = None,
) -> bool:
    if not exam_code:
        return True
    if stats_exam_code and stats_exam_code != exam_code:
        return False
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


def safe_float(value: object) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0


def compact_text(value: object, max_length: int = 240) -> str:
    return str(value or "").strip()[:max_length]


def normalize_exam_code(exam_code: str | None) -> str:
    return exam_code if exam_code in EXAM_SUBJECTS else "Z001"


def build_study_goal_response(
    row: dict | None,
    exam_code: str,
    *,
    sync_available: bool = True,
) -> StudyGoalResponse:
    record = row or {}
    return StudyGoalResponse(
        exam_code=exam_code,
        configured=bool(row),
        sync_available=sync_available,
        daily_minutes=int(record.get("daily_minutes") or DEFAULT_STUDY_GOAL_DAILY_MINUTES),
        weekly_question_target=int(
            record.get("weekly_question_target") or DEFAULT_STUDY_GOAL_WEEKLY_QUESTIONS
        ),
        updated_at=(str(record.get("updated_at")) if record.get("updated_at") else None),
    )


def fetch_study_goal_record(supabase, user_id: str, exam_code: str) -> dict | None:
    response = call_supabase(
        lambda: (
            supabase.table("user_study_goals")
            .select("id, exam_code, daily_minutes, weekly_question_target, updated_at")
            .eq("user_id", user_id)
            .eq("exam_code", exam_code)
            .limit(1)
            .execute()
        ),
        operation_name="study goal lookup",
    )
    return (response.data or [None])[0]


def to_local_datetime(value: object) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(APP_TIMEZONE)


def calculate_accuracy(rows: list[dict]) -> float | None:
    if not rows:
        return None
    correct = sum(1 for row in rows if row.get("is_correct"))
    return round(correct / len(rows) * 100, 2)


def filter_learning_activity_rows(rows: list[dict], exam_code: str | None) -> list[dict]:
    return [
        row
        for row in rows
        if belongs_to_exam(row.get("questions"), exam_code)
    ]


def calculate_study_seconds(rows: list[dict]) -> int:
    return sum(max(0, safe_int(row.get("used_time"))) for row in rows)


def fetch_learning_activity_rows(
    supabase,
    user_id: str,
    start_at: datetime,
    exam_code: str | None = None,
) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while len(rows) < LEARNING_ACTIVITY_LIMIT:
        query = (
            supabase.table("user_answers")
            .select("is_correct, used_time, created_at, questions(exam_code, subject)")
            .eq("user_id", user_id)
            .gte("created_at", start_at.isoformat())
        )
        if exam_code:
            query = query.eq("stats_exam_code", exam_code)
        chunk = query.order("created_at", desc=True).range(
            offset, min(offset + PAGE_SIZE - 1, LEARNING_ACTIVITY_LIMIT - 1)
        ).execute().data or []
        rows.extend(chunk)
        if len(chunk) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return rows


def fetch_recent_learning_days(supabase, user_id: str, exam_code: str | None) -> set:
    query = (
        supabase.table("user_answers")
        .select("created_at, questions(exam_code, subject)")
        .eq("user_id", user_id)
    )
    if exam_code:
        query = query.eq("stats_exam_code", exam_code)
    rows = query.order("created_at", desc=True).limit(LEARNING_ACTIVITY_LIMIT).execute().data or []
    learning_dates = set()
    for row in filter_learning_activity_rows(rows, exam_code):
        local_time = to_local_datetime(row.get("created_at"))
        if local_time:
            learning_dates.add(local_time.date())
    return learning_dates


def calculate_study_streak(learning_dates: set, today) -> int:
    if not learning_dates:
        return 0
    current = today if today in learning_dates else today - timedelta(days=1)
    streak = 0
    while current in learning_dates:
        streak += 1
        current -= timedelta(days=1)
    return streak


def get_display_name(profile: dict) -> str:
    nickname = profile.get("nickname")
    if isinstance(nickname, str) and nickname.strip():
        return nickname.strip()
    phone = str(profile.get("phone") or "").strip()
    if phone:
        prefix_length = 4 if phone.startswith("+") else 3
        if len(phone) > prefix_length + 4:
            return f"{phone[:prefix_length]}****{phone[-4:]}"
        return phone
    email = str(profile.get("email") or "")
    if email.endswith("@phone.gangyantong.local") or email.endswith("@wechat.gangyantong.local"):
        return "学习用户"
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
            .select("id, email, phone, nickname, avatar_url, role, disabled_at")
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


def fetch_weekly_answer_rows(
    supabase,
    week_start: datetime,
    exam_code: str | None = None,
) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while True:
        query = (
            supabase.table("user_answers")
            .select("user_id, stats_exam_code, questions(exam_code, subject)")
            .gte("created_at", week_start.isoformat())
        )
        if exam_code:
            query = query.eq("stats_exam_code", exam_code)
        chunk = query.range(offset, offset + PAGE_SIZE - 1).execute().data or []
        rows.extend(chunk)
        if len(chunk) < PAGE_SIZE:
            return rows
        offset += PAGE_SIZE


def build_daily_study_window(now: datetime | None = None) -> tuple[datetime, datetime, datetime]:
    local_now = (now or datetime.now(APP_TIMEZONE)).astimezone(APP_TIMEZONE)
    local_start = datetime.combine(local_now.date(), datetime.min.time(), tzinfo=APP_TIMEZONE)
    local_end = local_start + timedelta(days=1)
    return local_now, local_start.astimezone(timezone.utc), local_end.astimezone(timezone.utc)


def fetch_daily_study_rows(supabase, start_at: datetime, end_at: datetime) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while True:
        response = call_supabase(
            lambda: (
                supabase.table("user_answers")
                .select("user_id, used_time, is_correct, created_at")
                .gte("created_at", start_at.isoformat())
                .lt("created_at", end_at.isoformat())
                .order("created_at")
                .range(offset, offset + PAGE_SIZE - 1)
                .execute()
            ),
            operation_name="daily study leaderboard activity lookup",
        )
        chunk = response.data or []
        rows.extend(chunk)
        if len(chunk) < PAGE_SIZE:
            return rows
        offset += PAGE_SIZE


def build_daily_study_leaderboard(
    rows: list[dict],
    profiles: list[dict],
    current_user_id: str,
    *,
    limit: int,
    offset: int = 0,
    now: datetime | None = None,
) -> DailyStudyLeaderboardResponse:
    local_now, _, _ = build_daily_study_window(now)
    stats_by_user: dict[str, dict] = {}
    for row in rows:
        row_user_id = str(row.get("user_id") or "").strip()
        if not row_user_id:
            continue
        used_time = max(0, safe_int(row.get("used_time")))
        effective_seconds = min(used_time, DAILY_STUDY_MAX_SECONDS_PER_ANSWER)
        current = stats_by_user.setdefault(
            row_user_id,
            {
                "study_seconds": 0,
                "answer_count": 0,
                "correct_count": 0,
                "last_answered_at": datetime.min.replace(tzinfo=APP_TIMEZONE),
            },
        )
        current["study_seconds"] += effective_seconds
        current["answer_count"] += 1
        current["correct_count"] += 1 if row.get("is_correct") else 0
        answered_at = to_local_datetime(row.get("created_at"))
        if answered_at and answered_at > current["last_answered_at"]:
            current["last_answered_at"] = answered_at

    profiles_by_id = {
        str(profile.get("id") or ""): profile
        for profile in profiles
        if profile.get("id")
        and str(profile.get("role") or "user") != "admin"
        and not profile.get("disabled_at")
    }
    ranking_rows: list[dict] = []
    for row_user_id, stats in stats_by_user.items():
        profile = profiles_by_id.get(row_user_id)
        if not profile or stats["study_seconds"] <= 0:
            continue
        answer_count = stats["answer_count"]
        correct_count = stats["correct_count"]
        ranking_rows.append(
            {
                "user_id": row_user_id,
                "nickname": get_display_name(profile),
                "avatar_url": profile.get("avatar_url"),
                "study_seconds": stats["study_seconds"],
                "answer_count": answer_count,
                "correct_count": correct_count,
                "accuracy": round(correct_count / answer_count * 100, 2) if answer_count else 0,
                "last_answered_at": stats["last_answered_at"],
            }
        )

    ranking_rows.sort(
        key=lambda row: (
            -row["study_seconds"],
            -row["answer_count"],
            row["last_answered_at"],
            row["nickname"].casefold(),
            row["user_id"],
        )
    )
    ranked_items = [
        DailyStudyLeaderboardItem(
            rank=index + 1,
            is_current_user=row["user_id"] == current_user_id,
            **{key: value for key, value in row.items() if key != "last_answered_at"},
        )
        for index, row in enumerate(ranking_rows)
    ]
    page_items = ranked_items[offset:offset + limit]
    current_user = next(
        (item for item in ranked_items if item.user_id == current_user_id),
        None,
    )
    return DailyStudyLeaderboardResponse(
        date=local_now.date().isoformat(),
        updated_at=local_now.isoformat(),
        items=page_items,
        total_users=len(ranked_items),
        has_more=offset + len(page_items) < len(ranked_items),
        current_user=current_user,
    )


def build_platform_practice_trend_dates(days: int = PLATFORM_PRACTICE_TREND_DAYS, now: datetime | None = None) -> list:
    safe_days = max(1, min(int(days or PLATFORM_PRACTICE_TREND_DAYS), 31))
    current = now or datetime.now(APP_TIMEZONE)
    today = current.astimezone(APP_TIMEZONE).date()
    return [today - timedelta(days=safe_days - 1 - offset) for offset in range(safe_days)]


def build_platform_practice_trend(
    rows: list[dict],
    days: int = PLATFORM_PRACTICE_TREND_DAYS,
    now: datetime | None = None,
) -> list[PlatformPracticeTrendPoint]:
    trend_dates = build_platform_practice_trend_dates(days, now)
    trend_date_texts = {item.isoformat() for item in trend_dates}
    users_by_date = {item.isoformat(): set() for item in trend_dates}

    for row in rows:
        date_value = row.get("stat_date") or row.get("date")
        date_text = str(date_value or "")[:10]
        if date_text not in trend_date_texts:
            continue

        if "practice_users" in row or "user_count" in row:
            try:
                users_by_date[date_text] = max(0, int(row.get("practice_users", row.get("user_count", 0)) or 0))
            except (TypeError, ValueError):
                users_by_date[date_text] = 0
            continue

        user_id = str(row.get("user_id") or "").strip()
        if user_id:
            users_by_date[date_text].add(user_id)

    points = []
    for trend_date in trend_dates:
        date_text = trend_date.isoformat()
        value = users_by_date[date_text]
        practice_users = value if isinstance(value, int) else len(value)
        points.append(PlatformPracticeTrendPoint(date=date_text, practice_users=practice_users))
    return points


def fetch_platform_practice_activity_rows(supabase, start_at: datetime, end_at: datetime) -> list[dict]:
    rows: list[dict] = []
    offset = 0

    while True:
        response = call_supabase(
            lambda: (
                supabase.table("user_answers")
                .select("user_id,created_at")
                .gte("created_at", start_at.isoformat())
                .lt("created_at", end_at.isoformat())
                .order("created_at")
                .range(offset, offset + PAGE_SIZE - 1)
                .execute()
            ),
            operation_name="platform practice activity lookup",
        )
        chunk = response.data or []
        rows.extend(chunk)
        if len(chunk) < PAGE_SIZE:
            return rows
        offset += PAGE_SIZE


def fetch_platform_practice_trend(supabase) -> list[PlatformPracticeTrendPoint]:
    trend_dates = build_platform_practice_trend_dates()
    try:
        response = call_supabase(
            lambda: supabase.rpc(
                "platform_practice_user_trend",
                {"p_days": PLATFORM_PRACTICE_TREND_DAYS},
            ).execute(),
            operation_name="platform practice trend aggregate",
        )
        return build_platform_practice_trend(response.data or [])
    except Exception:
        # 兼容尚未执行聚合 SQL 的环境：直接从真实作答记录按用户去重统计。
        start_at = datetime.combine(trend_dates[0], datetime.min.time(), tzinfo=APP_TIMEZONE).astimezone(timezone.utc)
        end_at = datetime.combine(trend_dates[-1] + timedelta(days=1), datetime.min.time(), tzinfo=APP_TIMEZONE).astimezone(timezone.utc)
        activity_rows = fetch_platform_practice_activity_rows(supabase, start_at, end_at)
        local_rows = []
        for row in activity_rows:
            local_time = to_local_datetime(row.get("created_at"))
            if local_time:
                local_rows.append({
                    "date": local_time.date().isoformat(),
                    "user_id": row.get("user_id"),
                })
        return build_platform_practice_trend(local_rows)


def fetch_study_ability_rows(supabase, user_id: str, exam_code: str) -> list[dict]:
    return (
        supabase.table("ability_stats")
        .select("subject, module, submodule, total_count, correct_count, accuracy")
        .eq("user_id", user_id)
        .eq("exam_code", exam_code)
        .order("accuracy")
        .execute()
        .data
        or []
    )


def fetch_study_wrong_rows(supabase, user_id: str, exam_code: str, limit: int = 40) -> list[dict]:
    rows = (
        supabase.table("wrong_questions")
        .select("wrong_count, last_wrong_at, questions(exam_code, subject, module, submodule, stem, source_type)")
        .eq("user_id", user_id)
        .eq("stats_exam_code", exam_code)
        .order("last_wrong_at", desc=True)
        .limit(limit)
        .execute()
        .data
        or []
    )
    allowed = set(EXAM_SUBJECTS[exam_code])
    return [
        row
        for row in rows
        if belongs_to_exam(row.get("questions"), exam_code)
        and (row.get("questions") or {}).get("subject") in allowed
        and not is_ai_generated_question(row.get("questions"))
    ]


def subject_status(accuracy: float | None, total: int) -> str:
    if total <= 0 or accuracy is None:
        return "待积累数据"
    if accuracy < 45:
        return "重点补强"
    if accuracy < 65:
        return "继续加固"
    if accuracy < 80:
        return "稳定提升"
    return "保持优势"


def subject_fear_points(subject: str, weak_points: list[str]) -> list[str]:
    focus = weak_points[0] if weak_points else "基础题型"
    if subject == "数学基础":
        return [f"看到 {focus} 时容易急着套公式，忽略适用条件。", "遇到变形题时容易先慌，建议先写出已知条件再计算。"]
    if subject == "逻辑推理":
        return [f"遇到 {focus} 时容易凭语感判断，建议先找结论和条件。", "题干较长时容易漏掉限定词，要养成圈关键词的习惯。"]
    if subject == "英语运用":
        return [f"{focus} 容易靠直觉选择，建议回到固定搭配和句子结构。", "长句里容易被生词带偏，先抓主谓宾再判断选项。"]
    return [f"{focus} 容易出现记忆混淆，建议把相近概念放在一起对照。", "文化常识题不要只背结论，要补一句原因或时代背景。"]


def subject_score_tips(subject: str, weak_points: list[str]) -> list[str]:
    focus = weak_points[0] if weak_points else "当前薄弱点"
    if subject == "数学基础":
        return [f"我建议先把 {focus} 做成 10 题小组，错题必须写出公式条件。", "每次练完只复盘一个错误类型，别同时追求速度和难题。"]
    if subject == "逻辑推理":
        return [f"我建议先训练 {focus} 的题干拆解，先判断题型再看选项。", "做错后记录错因是偷换概念、条件不足还是方向判断错。"]
    if subject == "英语运用":
        return [f"我建议把 {focus} 的错题整理成短词组或短句，第二天再复测。", "先保证基础词汇和句法稳定，再去追求难句速度。"]
    return [f"我建议围绕 {focus} 做一轮同类复盘，先把高频常识稳住。", "同一人物、朝代、作品和流派要放在一张表里横向对比。"]


def build_rule_study_advice(
    exam_code: str,
    ability_rows: list[dict],
    wrong_rows: list[dict],
) -> StudyAdviceResponse:
    allowed_subjects = EXAM_SUBJECTS[exam_code]
    stats = {
        subject: {
            "subject": subject,
            "total": 0,
            "correct": 0,
            "ability": [],
            "wrong": [],
        }
        for subject in allowed_subjects
    }

    for row in ability_rows:
        subject = row.get("subject")
        if subject not in stats:
            continue
        total = safe_int(row.get("total_count"))
        correct = safe_int(row.get("correct_count"))
        stats[subject]["total"] += total
        stats[subject]["correct"] += correct
        stats[subject]["ability"].append(row)

    for row in wrong_rows:
        question = row.get("questions") or {}
        subject = question.get("subject")
        if subject not in stats:
            continue
        stats[subject]["wrong"].append(
            {
                "module": question.get("module"),
                "submodule": question.get("submodule"),
                "stem": question.get("stem"),
                "wrong_count": safe_int(row.get("wrong_count")) or 1,
            }
        )

    subject_advices: list[StudySubjectAdvice] = []
    for subject in allowed_subjects:
        item = stats[subject]
        total = item["total"]
        accuracy = round(item["correct"] / total * 100, 2) if total else None
        ability_focus = sorted(item["ability"], key=lambda row: safe_float(row.get("accuracy")))[:2]
        weak_points = [
            compact_text(row.get("submodule") or row.get("module") or subject, 40)
            for row in ability_focus
            if row.get("submodule") or row.get("module")
        ]
        if not weak_points:
            weak_points = [
                compact_text(row.get("submodule") or row.get("module") or subject, 40)
                for row in item["wrong"][:2]
                if row.get("submodule") or row.get("module")
            ]
        if not weak_points:
            weak_points = ["先完成一组基础练习建立样本"]

        subject_advices.append(
            StudySubjectAdvice(
                subject=subject,
                status=subject_status(accuracy, total),
                accuracy=accuracy,
                weak_points=weak_points[:3],
                fear_points=subject_fear_points(subject, weak_points)[:3],
                score_tips=subject_score_tips(subject, weak_points)[:3],
                next_actions=[
                    f"先做一组 10 题 {weak_points[0]} 专项训练。",
                    "做完后只复盘错题解析，再做 3 道同类题确认是否掌握。",
                ],
            )
        )

    ranked = sorted(
        subject_advices,
        key=lambda item: item.accuracy if item.accuracy is not None else 101,
    )
    focus = ranked[0]
    focus_point = focus.weak_points[0] if focus.weak_points else focus.subject
    summary = f"先抓 {focus.subject} 的 {focus_point}，用短练和错题复盘稳住提分。"
    summary_items = [
        f"{focus.subject} 当前{focus.status}，建议优先完成一组 10 题专项训练。",
        f"重点复盘 {focus_point}，先看错题解析，再做同类题。",
    ]
    if len(ranked) > 1:
        second = ranked[1]
        summary_items.append(f"{second.subject} 先保持练习节奏，避免薄弱点继续累积。")

    return StudyAdviceResponse(
        exam_code=exam_code,
        source="rule",
        summary=summary,
        summary_items=summary_items[:4],
        subject_advices=subject_advices,
        next_training=f"{focus.subject} / {focus_point} / 10 题",
    )


def extract_json_object(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("DeepSeek did not return JSON")
    return json.loads(text[start : end + 1])


def clean_text_list(value: object, max_items: int = 4, max_length: int = 120) -> list[str]:
    if not isinstance(value, list):
        return []
    return [compact_text(item, max_length) for item in value if compact_text(item, max_length)][:max_items]


def sanitize_study_advice(
    parsed: dict,
    fallback: StudyAdviceResponse,
    allowed_subjects: list[str],
) -> StudyAdviceResponse:
    fallback_by_subject = {item.subject: item for item in fallback.subject_advices}
    raw_subjects = parsed.get("subject_advices") if isinstance(parsed, dict) else []
    subject_advices: list[StudySubjectAdvice] = []
    seen: set[str] = set()

    if isinstance(raw_subjects, list):
        for raw in raw_subjects:
            if not isinstance(raw, dict):
                continue
            subject = compact_text(raw.get("subject"), 40)
            if subject not in allowed_subjects or subject in seen:
                continue
            base = fallback_by_subject.get(subject)
            subject_advices.append(
                StudySubjectAdvice(
                    subject=subject,
                    status=compact_text(raw.get("status"), 30) or (base.status if base else ""),
                    accuracy=safe_float(raw.get("accuracy")) if raw.get("accuracy") is not None else (base.accuracy if base else None),
                    weak_points=clean_text_list(raw.get("weak_points"), 4) or (base.weak_points if base else []),
                    fear_points=clean_text_list(raw.get("fear_points"), 4) or (base.fear_points if base else []),
                    score_tips=clean_text_list(raw.get("score_tips"), 4) or (base.score_tips if base else []),
                    next_actions=clean_text_list(raw.get("next_actions"), 4) or (base.next_actions if base else []),
                )
            )
            seen.add(subject)

    for subject in allowed_subjects:
        if subject not in seen and subject in fallback_by_subject:
            subject_advices.append(fallback_by_subject[subject])

    summary_items = clean_text_list(parsed.get("summary_items"), 4, 120) or fallback.summary_items
    summary = compact_text(parsed.get("summary"), 160) or fallback.summary
    next_training = compact_text(parsed.get("next_training"), 120) or fallback.next_training
    return StudyAdviceResponse(
        exam_code=fallback.exam_code,
        source="deepseek",
        summary=summary,
        summary_items=summary_items,
        subject_advices=subject_advices,
        next_training=next_training,
    )


async def call_deepseek_study_advice(
    exam_code: str,
    ability_rows: list[dict],
    wrong_rows: list[dict],
    fallback: StudyAdviceResponse,
) -> dict:
    settings = get_settings()
    if not settings.deepseek_api_key:
        raise ValueError("DeepSeek API Key not configured")

    allowed_subjects = EXAM_SUBJECTS[exam_code]
    context = {
        "exam_code": exam_code,
        "allowed_subjects": allowed_subjects,
        "ability_stats": ability_rows[:30],
        "recent_wrong_questions": [
            {
                "subject": (row.get("questions") or {}).get("subject"),
                "module": (row.get("questions") or {}).get("module"),
                "submodule": (row.get("questions") or {}).get("submodule"),
                "wrong_count": row.get("wrong_count"),
                "stem": compact_text((row.get("questions") or {}).get("stem"), 120),
            }
            for row in wrong_rows[:12]
        ],
        "rule_fallback": fallback.model_dump(),
    }
    forbidden_note = (
        "Z001 只包含中华文化、英语运用、逻辑推理，绝对不要出现数学基础、高数、微积分建议。"
        if exam_code == "Z001"
        else "Z002 只包含中华文化、英语运用、数学基础，绝对不要出现逻辑推理建议。"
    )
    messages = [
        {
            "role": "system",
            "content": (
                "你是港澳台考研刷题 App 的学习诊断老师。请只输出合法 JSON，不要输出 Markdown。"
                "建议要短、具体、有提分感，像老师看完学生错题后给出的复盘建议。"
                "必须严格按 allowed_subjects 输出，不得编造该考试版本不存在的科目。"
                f"{forbidden_note}"
            ),
        },
        {
            "role": "user",
            "content": (
                "请根据以下真实作答统计和错题记录，生成学习建议。\n"
                f"{json.dumps(context, ensure_ascii=False)}\n\n"
                "输出 JSON 格式："
                '{"summary":"一句总建议","summary_items":["卡片展示建议1","卡片展示建议2"],'
                '"subject_advices":[{"subject":"科目","status":"状态","accuracy":60,'
                '"weak_points":["薄弱点"],"fear_points":["害怕点"],'
                '"score_tips":["我建议..."],"next_actions":["下一步动作"]}],'
                '"next_training":"推荐训练范围"}'
            ),
        },
    ]
    body = {
        "model": settings.deepseek_model,
        "messages": messages,
        "temperature": 0.35,
        "response_format": {"type": "json_object"},
    }
    timeout = aiohttp.ClientTimeout(total=settings.deepseek_timeout_seconds)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            json=body,
        ) as response:
            data = await response.json(content_type=None)
            if response.status >= 400:
                raise ValueError("DeepSeek study advice failed")
    choices = data.get("choices") or []
    content = choices[0].get("message", {}).get("content") if choices else ""
    return extract_json_object(content)


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

    now = datetime.now(APP_TIMEZONE)
    week_start = datetime.combine(
        (now - timedelta(days=now.weekday())).date(),
        datetime.min.time(),
        tzinfo=APP_TIMEZONE,
    ).astimezone(timezone.utc)
    previous_week_start = week_start - timedelta(days=7)
    trend_start_date = now.date() - timedelta(days=6)
    trend_start = datetime.combine(trend_start_date, datetime.min.time(), tzinfo=APP_TIMEZONE).astimezone(timezone.utc)
    activity_start = min(previous_week_start, trend_start)
    activity_rows = filter_learning_activity_rows(
        fetch_learning_activity_rows(supabase, user_id, activity_start, exam_code),
        exam_code,
    )

    weekly_rows = []
    previous_week_rows = []
    daily_rows: dict = {}
    subject_rows: dict = {}
    for row in activity_rows:
        local_time = to_local_datetime(row.get("created_at"))
        if not local_time:
            continue
        question = row.get("questions") or {}
        subject = question.get("subject") or ""
        local_date = local_time.date()
        if local_date >= trend_start_date:
            daily_rows.setdefault(local_date, []).append(row)
        if local_date >= week_start.astimezone(APP_TIMEZONE).date():
            weekly_rows.append(row)
            if subject:
                subject_rows.setdefault(subject, {"current": [], "previous": []})["current"].append(row)
        elif local_date >= previous_week_start.astimezone(APP_TIMEZONE).date():
            previous_week_rows.append(row)
            if subject:
                subject_rows.setdefault(subject, {"current": [], "previous": []})["previous"].append(row)

    today_study_seconds = calculate_study_seconds(daily_rows.get(now.date(), []))
    weekly_answers = len(weekly_rows)
    weekly_correct_answers = sum(1 for row in weekly_rows if row.get("is_correct"))
    weekly_accuracy = round(weekly_correct_answers / weekly_answers * 100, 2) if weekly_answers else 0
    previous_week_answers = len(previous_week_rows)
    previous_week_correct_answers = sum(1 for row in previous_week_rows if row.get("is_correct"))
    previous_week_accuracy = calculate_accuracy(previous_week_rows)
    weekly_accuracy_change = (
        round(weekly_accuracy - previous_week_accuracy, 2)
        if weekly_answers and previous_week_accuracy is not None
        else None
    )

    trend = []
    for offset in range(7):
        current_date = trend_start_date + timedelta(days=offset)
        rows = daily_rows.get(current_date, [])
        trend.append(
            LearningTrendPoint(
                date=current_date.isoformat(),
                label=f"周{'一二三四五六日'[current_date.weekday()]}",
                accuracy=calculate_accuracy(rows),
                total_answers=len(rows),
            )
        )

    allowed_subjects = EXAM_SUBJECTS.get(exam_code, []) if exam_code else []
    subject_names = allowed_subjects or sorted(subject_rows)
    subject_weekly_changes = []
    for subject in subject_names:
        rows = subject_rows.get(subject, {"current": [], "previous": []})
        current_rows = rows["current"]
        previous_rows = rows["previous"]
        current_accuracy = calculate_accuracy(current_rows)
        subject_previous_accuracy = calculate_accuracy(previous_rows)
        subject_weekly_changes.append(
            SubjectWeeklyChange(
                subject=subject,
                current_answers=len(current_rows),
                current_accuracy=current_accuracy,
                previous_answers=len(previous_rows),
                previous_accuracy=subject_previous_accuracy,
                accuracy_change=(
                    round(current_accuracy - subject_previous_accuracy, 2)
                    if current_accuracy is not None and subject_previous_accuracy is not None
                    else None
                ),
            )
        )

    study_streak = calculate_study_streak(
        fetch_recent_learning_days(supabase, user_id, exam_code),
        now.date(),
    )

    wrong_response = (
        supabase.table("wrong_questions")
        .select("id, questions(exam_code, subject, source_type)")
        .eq("user_id", user_id)
    )
    if exam_code:
        wrong_response = wrong_response.eq("stats_exam_code", exam_code)
    wrong_response = wrong_response.limit(1000).execute()
    wrong_rows = wrong_response.data
    if exam_code:
        wrong_rows = [row for row in wrong_rows if belongs_to_exam(row.get("questions"), exam_code)]
    wrong_rows = [row for row in wrong_rows if not is_ai_generated_question(row.get("questions"))]

    return LearningSummaryResponse(
        exam_code=exam_code,
        total_answers=total_answers,
        correct_answers=correct_answers,
        accuracy=accuracy,
        wrong_question_count=len(wrong_rows),
        today_study_seconds=today_study_seconds,
        weekly_answers=weekly_answers,
        weekly_correct_answers=weekly_correct_answers,
        weekly_accuracy=weekly_accuracy,
        previous_week_answers=previous_week_answers,
        previous_week_correct_answers=previous_week_correct_answers,
        previous_week_accuracy=previous_week_accuracy,
        weekly_accuracy_change=weekly_accuracy_change,
        study_streak=study_streak,
        trend=trend,
        subject_weekly_changes=subject_weekly_changes,
    )


@router.get("/study-goal", response_model=StudyGoalResponse)
def study_goal(
    user_id: str = Depends(get_current_user_id),
    exam_code: str = Query(default="Z001", pattern=r"^(Z001|Z002)$"),
) -> StudyGoalResponse:
    resolved_exam_code = normalize_exam_code(exam_code)
    try:
        row = fetch_study_goal_record(get_supabase_admin(), user_id, resolved_exam_code)
        return build_study_goal_response(row, resolved_exam_code)
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            return build_study_goal_response(
                None,
                resolved_exam_code,
                sync_available=False,
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="学习任务暂时未同步，请稍后重试",
        ) from exc


@router.put("/study-goal", response_model=StudyGoalResponse)
def update_study_goal(
    payload: StudyGoalUpdateRequest,
    user_id: str = Depends(get_current_user_id),
) -> StudyGoalResponse:
    supabase = get_supabase_admin()
    record = {
        "user_id": user_id,
        "exam_code": payload.exam_code,
        "daily_minutes": payload.daily_minutes,
        "weekly_question_target": payload.weekly_question_target,
    }
    try:
        response = call_supabase(
            lambda: (
                supabase.table("user_study_goals")
                .upsert(record, on_conflict="user_id,exam_code")
                .execute()
            ),
            operation_name="study goal upsert",
        )
        saved = (response.data or [None])[0]
        if not saved:
            saved = fetch_study_goal_record(supabase, user_id, payload.exam_code)
        return build_study_goal_response(saved, payload.exam_code)
    except HTTPException:
        raise
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            detail = "学习任务数据表尚未初始化"
        else:
            detail = "学习任务保存失败，请稍后重试"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        ) from exc


@router.get("/platform-practice-trend", response_model=PlatformPracticeTrendResponse)
def platform_practice_trend() -> PlatformPracticeTrendResponse:
    """Public, privacy-safe daily count of unique users who submitted answers."""

    try:
        items = fetch_platform_practice_trend(get_supabase_admin())
        return PlatformPracticeTrendResponse(items=items)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="刷题人数统计暂时不可用，请稍后重试",
        ) from exc


@router.get("/study-advice", response_model=StudyAdviceResponse)
async def study_advice(
    user_id: str = Depends(get_current_user_id),
    exam_code: str | None = None,
) -> StudyAdviceResponse:
    supabase = get_supabase_admin()
    resolved_exam_code = normalize_exam_code(exam_code)
    ability_rows = fetch_study_ability_rows(supabase, user_id, resolved_exam_code)
    wrong_rows = fetch_study_wrong_rows(supabase, user_id, resolved_exam_code)
    fallback = build_rule_study_advice(resolved_exam_code, ability_rows, wrong_rows)

    try:
        parsed = await call_deepseek_study_advice(resolved_exam_code, ability_rows, wrong_rows, fallback)
        return sanitize_study_advice(parsed, fallback, EXAM_SUBJECTS[resolved_exam_code])
    except Exception:
        return fallback


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

    # Reuse the module-level fallback so Windows builds without tzdata do not
    # turn the leaderboard into a 500 response.
    now = datetime.now(APP_TIMEZONE)
    week_start = datetime.combine(
        (now - timedelta(days=now.weekday())).date(),
        datetime.min.time(),
        tzinfo=APP_TIMEZONE,
    ).astimezone(timezone.utc)
    weekly_rows = fetch_weekly_answer_rows(supabase, week_start, exam_code)
    weekly_by_user: dict[str, int] = {}
    for row in weekly_rows:
        if exam_code and not belongs_to_exam(
            row.get("questions"),
            exam_code,
            stats_exam_code=row.get("stats_exam_code"),
        ):
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


@router.get("/daily-study-leaderboard", response_model=DailyStudyLeaderboardResponse)
def daily_study_leaderboard(
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
) -> DailyStudyLeaderboardResponse:
    """Return today's privacy-safe ranking by effective answer time in Asia/Shanghai."""

    local_now, start_at, end_at = build_daily_study_window()
    try:
        supabase = get_supabase_admin()
        rows = fetch_daily_study_rows(supabase, start_at, end_at)
        profiles = fetch_user_profiles(supabase)
        return build_daily_study_leaderboard(
            rows,
            profiles,
            user_id,
            limit=limit,
            offset=offset,
            now=local_now,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="今日学习榜暂时不可用，请稍后重试",
        ) from exc
