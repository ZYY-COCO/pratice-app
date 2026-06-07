import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import aiohttp
from fastapi import APIRouter, Depends, Query

from app.config import get_settings
from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.reports import (
    AbilityReportResponse,
    AbilityStatItem,
    LeaderboardItem,
    LeaderboardResponse,
    LearningSummaryResponse,
    StudyAdviceResponse,
    StudySubjectAdvice,
)
from app.services.question_sources import is_ai_generated_question
from app.services.reports import build_ability_item

router = APIRouter(prefix="/report", tags=["能力报告"])

PUBLIC_SUBJECTS = {"中华文化", "英语运用"}
VERSION_EXAM_CODES = {"Z001", "Z002"}
EXAM_SUBJECTS = {
    "Z001": ["中华文化", "英语运用", "逻辑推理"],
    "Z002": ["中华文化", "英语运用", "数学基础"],
}
PAGE_SIZE = 1000


def belongs_to_exam(question: dict | None, exam_code: str | None) -> bool:
    if not exam_code:
        return True
    question = question or {}
    question_exam_code = question.get("exam_code")
    if question_exam_code == exam_code:
        return True
    return question_exam_code in {"COMMON", *VERSION_EXAM_CODES} and question.get("subject") in PUBLIC_SUBJECTS


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
            .select("id, email, phone, nickname, avatar_url")
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
        .select("id, questions(exam_code, subject, source_type)")
        .eq("user_id", user_id)
        .limit(1000)
        .execute()
    )
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
        weekly_answers=weekly_answers,
        weekly_correct_answers=weekly_correct_answers,
        weekly_accuracy=weekly_accuracy,
    )


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
