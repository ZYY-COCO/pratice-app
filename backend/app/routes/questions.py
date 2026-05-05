import re
import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.questions import Passage, Question, QuestionListResponse, QuestionProgressResponse

router = APIRouter(tags=["题目"])

PUBLIC_SUBJECTS = {"中华文化", "英语运用"}
VERSION_EXAM_CODES = {"Z001", "Z002"}
EBBINGHAUS_REVIEW_DAYS = [1, 2, 4, 7, 15, 30]
CULTURE_SUBJECT = "中华文化"


def get_question_exam_codes(exam_code: str | None, subject: str | None) -> list[str]:
    """公共科目使用 COMMON 题库，同时兼容旧的版本专属题。"""
    if not exam_code:
        return []
    if exam_code == "COMMON":
        return ["COMMON"]
    if subject == CULTURE_SUBJECT and exam_code in VERSION_EXAM_CODES:
        return ["COMMON", "Z001"]
    if subject in PUBLIC_SUBJECTS and exam_code in VERSION_EXAM_CODES:
        return ["COMMON", exam_code]
    return [exam_code]


def hide_answer(row: dict, include_answer: bool = False) -> dict:
    if include_answer:
        return row
    return {**row, "answer": None, "explanation": None}


def normalize_stem_key(value: object) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[，。！？；：,.!?;:()\[\]（）【】“”‘’\"']", "", text)
    return text.lower()


def deduplicate_question_rows(rows: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique_rows: list[dict] = []
    for row in rows:
        stem_key = normalize_stem_key(row.get("stem"))
        fallback_key = str(row.get("id") or "")
        key = stem_key or fallback_key
        if key in seen:
            continue
        seen.add(key)
        unique_rows.append(row)
    return unique_rows


def parse_supabase_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def fetch_subject_question_rows(supabase, exam_code: str, subject: str) -> list[dict]:
    query = supabase.table("questions").select("*")
    exam_codes = get_question_exam_codes(exam_code, subject)
    if len(exam_codes) > 1:
        query = query.in_("exam_code", exam_codes)
    else:
        query = query.eq("exam_code", exam_codes[0])
    response = query.eq("subject", subject).range(0, 4999).execute()
    return deduplicate_question_rows(response.data or [])


def build_progress_summary(supabase, user_id: str, exam_code: str, subject: str) -> dict:
    questions = fetch_subject_question_rows(supabase, exam_code, subject)
    question_ids = {row["id"] for row in questions}
    total_questions = len(questions)

    if not question_ids:
        return {
            "total_questions": 0,
            "mastered_questions": 0,
            "progress_percent": 0,
            "review_due_count": 0,
            "review_due_ids": [],
        }

    response = (
        supabase.table("user_answers")
        .select("question_id, is_correct, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=False)
        .range(0, 9999)
        .execute()
    )

    stats_by_question: dict[str, dict] = {}
    for row in response.data or []:
        question_id = row.get("question_id")
        if question_id not in question_ids:
            continue
        created_at = parse_supabase_datetime(row.get("created_at"))
        stats = stats_by_question.setdefault(
            question_id,
            {
                "attempt_count": 0,
                "correct_count": 0,
                "first_is_correct": None,
                "last_is_correct": False,
                "last_answer_at": created_at,
            },
        )
        if stats["attempt_count"] == 0:
            stats["first_is_correct"] = bool(row.get("is_correct"))
        stats["attempt_count"] += 1
        if row.get("is_correct"):
            stats["correct_count"] += 1
        stats["last_is_correct"] = bool(row.get("is_correct"))
        stats["last_answer_at"] = created_at

    now = datetime.now(timezone.utc)
    mastered_questions = sum(
        1
        for stats in stats_by_question.values()
        if stats["first_is_correct"] is True or int(stats["correct_count"]) >= 2
    )
    review_due: list[tuple[datetime, str]] = []
    for question_id, stats in stats_by_question.items():
        last_answer_at = stats["last_answer_at"]
        if not stats["last_is_correct"]:
            review_due.append((last_answer_at, question_id))
            continue

        correct_count = max(1, int(stats["correct_count"]))
        interval_days = EBBINGHAUS_REVIEW_DAYS[min(correct_count - 1, len(EBBINGHAUS_REVIEW_DAYS) - 1)]
        due_at = last_answer_at + timedelta(days=interval_days)
        if due_at <= now:
            review_due.append((due_at, question_id))

    review_due_ids = [question_id for _, question_id in sorted(review_due, key=lambda item: item[0])]
    progress_percent = round((mastered_questions / total_questions) * 100) if total_questions else 0

    return {
        "total_questions": total_questions,
        "mastered_questions": mastered_questions,
        "progress_percent": progress_percent,
        "review_due_count": len(review_due_ids),
        "review_due_ids": review_due_ids,
    }


@router.get("/questions", response_model=QuestionListResponse)
def list_questions(
    _: str = Depends(get_current_user_id),
    exam_code: str | None = Query(default=None, pattern="^(Z001|Z002|COMMON)$"),
    subject: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    randomize: bool = Query(default=False),
) -> QuestionListResponse:
    supabase = get_supabase_admin()
    query = supabase.table("questions").select("*")
    exam_codes = get_question_exam_codes(exam_code, subject)
    if len(exam_codes) > 1:
        query = query.in_("exam_code", exam_codes)
    elif len(exam_codes) == 1:
        query = query.eq("exam_code", exam_codes[0])
    if subject:
        query = query.eq("subject", subject)
    if randomize:
        query = query.order("created_at", desc=False)

    response = query.limit(1000 if randomize else limit).execute()
    rows = response.data or []
    if randomize:
        rows = deduplicate_question_rows(rows)
        rows = random.sample(rows, min(limit, len(rows)))
    items = [Question(**hide_answer(row)) for row in rows]
    return QuestionListResponse(items=items, count=len(items))


@router.get("/questions/by-module", response_model=QuestionListResponse)
def list_questions_by_module(
    _: str = Depends(get_current_user_id),
    exam_code: str = Query(pattern="^(Z001|Z002|COMMON)$"),
    subject: str = Query(min_length=1),
    module: str = Query(min_length=1),
    submodule: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=50),
) -> QuestionListResponse:
    supabase = get_supabase_admin()
    query = supabase.table("questions").select("*")
    exam_codes = get_question_exam_codes(exam_code, subject)
    if len(exam_codes) > 1:
        query = query.in_("exam_code", exam_codes)
    else:
        query = query.eq("exam_code", exam_codes[0])
    response = query.eq("subject", subject).eq("module", module).eq("submodule", submodule).limit(200).execute()
    rows = deduplicate_question_rows(response.data or [])[:limit]
    items = [Question(**hide_answer(row)) for row in rows]
    return QuestionListResponse(items=items, count=len(items))


@router.get("/questions/progress", response_model=QuestionProgressResponse)
def get_question_progress(
    user_id: str = Depends(get_current_user_id),
    exam_code: str = Query(pattern="^(Z001|Z002|COMMON)$"),
    subject: str = Query(min_length=1),
) -> QuestionProgressResponse:
    supabase = get_supabase_admin()
    summary = build_progress_summary(supabase, user_id, exam_code, subject)
    return QuestionProgressResponse(
        exam_code=exam_code,
        subject=subject,
        total_questions=summary["total_questions"],
        mastered_questions=summary["mastered_questions"],
        progress_percent=summary["progress_percent"],
        review_due_count=summary["review_due_count"],
        next_review_label="按 1/2/4/7/15/30 天复习",
        review_days=EBBINGHAUS_REVIEW_DAYS,
    )


@router.get("/questions/review-due", response_model=QuestionListResponse)
def list_review_due_questions(
    user_id: str = Depends(get_current_user_id),
    exam_code: str = Query(pattern="^(Z001|Z002|COMMON)$"),
    subject: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=30),
) -> QuestionListResponse:
    supabase = get_supabase_admin()
    summary = build_progress_summary(supabase, user_id, exam_code, subject)
    due_ids = summary["review_due_ids"][:limit]
    if not due_ids:
        return QuestionListResponse(items=[], count=0)

    response = supabase.table("questions").select("*").in_("id", due_ids).execute()
    row_by_id = {row["id"]: row for row in response.data or []}
    rows = [row_by_id[question_id] for question_id in due_ids if question_id in row_by_id]
    items = [Question(**hide_answer(row)) for row in rows]
    return QuestionListResponse(items=items, count=len(items))


@router.get("/passages/{passage_id}", response_model=Passage)
def get_passage(passage_id: str, _: str = Depends(get_current_user_id)) -> Passage:
    supabase = get_supabase_admin()
    response = supabase.table("passages").select("*").eq("id", passage_id).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passage not found")
    return Passage(**response.data[0])
