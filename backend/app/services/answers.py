from collections import OrderedDict
from datetime import datetime, timezone
import logging
from threading import Lock
from time import monotonic

from fastapi import HTTPException, status
from supabase import Client

from app.db import get_supabase_admin
from app.services.question_sources import is_ai_generated_question
from app.services.supabase_resilience import call_supabase, is_missing_supabase_relation_error

VERSION_EXAM_CODES = {"Z001", "Z002"}
PUBLIC_SUBJECTS = {"中华文化", "英语运用"}
logger = logging.getLogger(__name__)

# Question lists already read complete active question records before answers
# are stripped from the API response.  Retain only the grading fields in a
# short-lived server-side cache so the submit endpoint can return the result
# without repeating that database lookup.  Nothing from this cache is exposed
# before the learner submits an answer.
_SUBMISSION_QUESTION_FIELDS = (
    "id",
    "exam_code",
    "subject",
    "module",
    "submodule",
    "source_type",
    "answer",
    "explanation",
)
_SUBMISSION_QUESTION_CACHE_TTL_SECONDS = 10 * 60.0
_SUBMISSION_QUESTION_CACHE_MAX_ENTRIES = 3000
_submission_question_cache: OrderedDict[str, tuple[dict, float]] = OrderedDict()
_submission_question_cache_lock = Lock()


def _cache_submission_question(question: dict) -> None:
    question_id = str(question.get("id") or "")
    if not question_id or not question.get("answer"):
        return

    cached_question = {field: question.get(field) for field in _SUBMISSION_QUESTION_FIELDS}
    with _submission_question_cache_lock:
        _submission_question_cache[question_id] = (
            cached_question,
            monotonic() + _SUBMISSION_QUESTION_CACHE_TTL_SECONDS,
        )
        _submission_question_cache.move_to_end(question_id)
        while len(_submission_question_cache) > _SUBMISSION_QUESTION_CACHE_MAX_ENTRIES:
            _submission_question_cache.popitem(last=False)


def warm_submission_questions(questions: list[dict]) -> None:
    """Warm grading data from question-list rows without exposing answers."""

    for question in questions:
        _cache_submission_question(question)


def _get_cached_submission_question(question_id: str) -> dict | None:
    key = str(question_id)
    now = monotonic()
    with _submission_question_cache_lock:
        cached = _submission_question_cache.get(key)
        if not cached:
            return None

        question, expires_at = cached
        if expires_at <= now:
            _submission_question_cache.pop(key, None)
            return None

        _submission_question_cache.move_to_end(key)
        return dict(question)


def get_question_or_404(supabase: Client, question_id: str) -> dict:
    response = supabase.table("questions").select("*").eq("id", question_id).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return response.data[0]


def get_submission_question_or_404(supabase: Client, question_id: str) -> dict:
    """Fetch only the fields needed to grade and explain one submitted answer."""
    cached_question = _get_cached_submission_question(question_id)
    if cached_question:
        return cached_question

    response = (
        supabase.table("questions")
        .select("id, exam_code, subject, module, submodule, source_type, answer, explanation")
        .eq("id", question_id)
        .limit(1)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    question = response.data[0]
    _cache_submission_question(question)
    return question


def has_answer_submission(supabase: Client, user_id: str, question_id: str) -> bool:
    response = (
        supabase.table("user_answers")
        .select("id")
        .eq("user_id", user_id)
        .eq("question_id", question_id)
        .limit(1)
        .execute()
    )
    return bool(response.data)


def require_answer_disclosure_allowed(supabase: Client, user_id: str, question_id: str) -> None:
    if not has_answer_submission(supabase, user_id, question_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Submit this question before viewing the answer explanation",
        )


def resolve_stats_exam_code(
    supabase: Client,
    user_id: str,
    question: dict,
    requested_exam_code: str | None = None,
) -> str:
    """COMMON 公共题按用户当前版本写入能力统计，避免报告里出现 COMMON 分组。"""
    question_exam_code = question["exam_code"]
    if question.get("subject") in PUBLIC_SUBJECTS and requested_exam_code in VERSION_EXAM_CODES:
        return requested_exam_code

    if question_exam_code != "COMMON":
        return question_exam_code

    if requested_exam_code in VERSION_EXAM_CODES:
        return requested_exam_code

    response = supabase.table("users").select("exam_target").eq("id", user_id).limit(1).execute()
    profile = response.data[0] if response.data else {}
    exam_target = profile.get("exam_target")
    return exam_target if exam_target in VERSION_EXAM_CODES else "Z001"


def record_wrong_question(supabase: Client, user_id: str, question_id: str) -> None:
    existing = (
        supabase.table("wrong_questions")
        .select("id, wrong_count")
        .eq("user_id", user_id)
        .eq("question_id", question_id)
        .limit(1)
        .execute()
    )
    if existing.data:
        row = existing.data[0]
        supabase.table("wrong_questions").update(
            {"wrong_count": int(row["wrong_count"]) + 1, "last_wrong_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", row["id"]).execute()
        return

    supabase.table("wrong_questions").insert({"user_id": user_id, "question_id": question_id}).execute()


def update_ability_stats(supabase: Client, user_id: str, question: dict, is_correct: bool) -> dict:
    filters = {
        "user_id": user_id,
        "exam_code": question["exam_code"],
        "subject": question["subject"],
        "module": question["module"],
        "submodule": question["submodule"],
    }
    query = supabase.table("ability_stats").select("*")
    for key, value in filters.items():
        query = query.eq(key, value)
    current = query.limit(1).execute()

    if current.data:
        row = current.data[0]
        total_count = int(row["total_count"]) + 1
        correct_count = int(row["correct_count"]) + (1 if is_correct else 0)
        accuracy = round(correct_count / total_count * 100, 2)
        updated = (
            supabase.table("ability_stats")
            .update({"total_count": total_count, "correct_count": correct_count, "accuracy": accuracy})
            .eq("id", row["id"])
            .execute()
        )
        return updated.data[0]

    total_count = 1
    correct_count = 1 if is_correct else 0
    accuracy = round(correct_count / total_count * 100, 2)
    inserted = (
        supabase.table("ability_stats")
        .insert({**filters, "total_count": total_count, "correct_count": correct_count, "accuracy": accuracy})
        .execute()
    )
    return inserted.data[0]


def get_current_ability_stats(supabase: Client, user_id: str, question: dict) -> dict | None:
    filters = {
        "user_id": user_id,
        "exam_code": question["exam_code"],
        "subject": question["subject"],
        "module": question["module"],
        "submodule": question["submodule"],
    }
    query = supabase.table("ability_stats").select("*")
    for key, value in filters.items():
        query = query.eq(key, value)
    current = query.limit(1).execute()
    return current.data[0] if current.data else None


def calculate_next_accuracy(current: dict | None, is_correct: bool) -> float:
    if current:
        total_count = int(current["total_count"]) + 1
        correct_count = int(current["correct_count"]) + (1 if is_correct else 0)
    else:
        total_count = 1
        correct_count = 1 if is_correct else 0
    return round(correct_count / total_count * 100, 2)


def pick_wrong_answer(correct_answer: str) -> str:
    for option in ("A", "B", "C", "D"):
        if option != correct_answer:
            return option
    return "A"


def persist_answer_submission(
    user_id: str,
    question: dict,
    selected_answer: str,
    used_time: int,
    is_correct: bool,
    client_submission_id: str | None = None,
) -> dict:
    """Persist one answer synchronously and return its durable submission facts.

    The third-batch migration exposes one transaction RPC.  A small synchronous
    compatibility path remains for a rolling local deployment before that SQL is
    applied; it keeps the UI usable while clearly logging that atomic guarantees
    start after the migration.
    """

    supabase = get_supabase_admin()
    question_id = str(question["id"])
    normalized_client_id = str(client_submission_id or "").strip() or None
    rpc_payload = {
        "p_user_id": user_id,
        "p_question_id": question_id,
        "p_client_submission_id": normalized_client_id,
        "p_selected_answer": selected_answer,
        "p_is_correct": bool(is_correct),
        "p_used_time": int(used_time or 0),
        "p_exam_code": str(question.get("exam_code") or ""),
        "p_subject": str(question.get("subject") or ""),
        "p_module": str(question.get("module") or ""),
        "p_submodule": str(question.get("submodule") or ""),
        "p_is_ai_generated": is_ai_generated_question(question),
    }

    try:
        response = call_supabase(
            lambda: supabase.rpc("record_answer_submission", rpc_payload).execute(),
            operation_name="answer submission atomic record",
        )
        data = response.data
        if isinstance(data, list):
            data = data[0] if data else None
        if not isinstance(data, dict):
            raise RuntimeError("answer submission RPC returned no result")
        return data
    except HTTPException:
        raise
    except Exception as exc:
        error_text = str(exc).lower()
        if "answer_submission_conflict" in error_text:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="同一提交标识已用于不同答案，请生成新的提交标识后重试",
            ) from exc
        if not is_missing_supabase_relation_error(exc):
            logger.warning(
                "Atomic answer submission failed (question_id=%s error_type=%s)",
                question_id,
                type(exc).__name__,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="作答记录暂时无法保存，请稍后重试",
            ) from exc

        logger.warning(
            "Answer reliability migration is not deployed; using compatibility persistence "
            "(question_id=%s)",
            question_id,
        )
        return _persist_answer_submission_compatibility(
            supabase=supabase,
            user_id=user_id,
            question=question,
            selected_answer=selected_answer,
            used_time=used_time,
            is_correct=is_correct,
            client_submission_id=normalized_client_id,
        )


def _persist_answer_submission_compatibility(
    *,
    supabase: Client,
    user_id: str,
    question: dict,
    selected_answer: str,
    used_time: int,
    is_correct: bool,
    client_submission_id: str | None,
) -> dict:
    """Rolling-deployment fallback; the migration RPC is the production path."""

    question_id = str(question["id"])
    client_column_available = True
    existing = []
    if client_submission_id:
        try:
            existing = (
                supabase.table("user_answers")
                .select("id,question_id,stats_exam_code,selected_answer,is_correct,used_time,client_submission_id,attempt_number,is_first_attempt")
                .eq("user_id", user_id)
                .eq("client_submission_id", client_submission_id)
                .limit(1)
                .execute()
                .data
                or []
            )
        except Exception as exc:
            if not is_missing_supabase_relation_error(exc):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="作答记录暂时无法保存，请稍后重试",
                ) from exc
            client_column_available = False

    if existing:
        row = existing[0]
        if (
            str(row.get("question_id")) != question_id
            or str(row.get("stats_exam_code")) != str(question.get("exam_code") or "")
            or str(row.get("selected_answer")) != str(selected_answer)
            or bool(row.get("is_correct")) != bool(is_correct)
            or int(row.get("used_time") or 0) != int(used_time or 0)
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="同一提交标识已用于不同答案，请生成新的提交标识后重试",
            )
        current = get_current_ability_stats(supabase, user_id, question)
        return {
            "submission_id": row.get("id"),
            "client_submission_id": row.get("client_submission_id") or client_submission_id,
            "stats_exam_code": row.get("stats_exam_code") or question.get("exam_code"),
            "idempotent": True,
            "persisted": True,
            "is_first_attempt": row.get("is_first_attempt"),
            "attempt_number": row.get("attempt_number"),
            "ability_accuracy": float(current["accuracy"]) if current else 0,
        }

    prior_response = (
        supabase.table("user_answers")
        .select("id,is_correct,created_at", count="exact")
        .eq("user_id", user_id)
        .eq("question_id", question_id)
        .order("created_at", desc=False)
        .limit(1)
        .execute()
    )
    is_first_attempt = not bool(prior_response.data)
    prior_attempt_count = int(prior_response.count or len(prior_response.data or []))
    answer_payload = {
        "user_id": user_id,
        "question_id": question_id,
        "selected_answer": selected_answer,
        "is_correct": bool(is_correct),
        "used_time": int(used_time or 0),
    }
    if client_column_available and client_submission_id:
        answer_payload["client_submission_id"] = client_submission_id
    if client_column_available:
        answer_payload.update({
            "stats_exam_code": str(question.get("exam_code") or ""),
            "attempt_number": prior_attempt_count + 1,
            "is_first_attempt": is_first_attempt,
        })

    try:
        inserted = supabase.table("user_answers").insert(answer_payload).execute()
    except Exception as exc:
        if client_submission_id and client_column_available and "duplicate" in str(exc).lower():
            return _persist_answer_submission_compatibility(
                supabase=supabase,
                user_id=user_id,
                question=question,
                selected_answer=selected_answer,
                used_time=used_time,
                is_correct=is_correct,
                client_submission_id=client_submission_id,
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="作答记录暂时无法保存，请稍后重试",
        ) from exc

    if not inserted.data:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="作答记录暂时无法保存，请稍后重试")
    if not is_correct and not is_ai_generated_question(question):
        record_wrong_question(supabase, user_id, question_id)
    stats = update_ability_stats(supabase, user_id, question, is_correct)
    return {
        "submission_id": inserted.data[0].get("id"),
        "client_submission_id": inserted.data[0].get("client_submission_id") or client_submission_id,
        "stats_exam_code": inserted.data[0].get("stats_exam_code") or question.get("exam_code"),
        "idempotent": False,
        "persisted": True,
        "is_first_attempt": is_first_attempt,
        "attempt_number": answer_payload.get("attempt_number"),
        "ability_accuracy": float(stats.get("accuracy") or 0),
    }


def submit_answer(
    supabase: Client,
    user_id: str,
    question_id: str,
    selected_answer: str,
    used_time: int,
    requested_exam_code: str | None = None,
    include_ability_accuracy: bool = True,
) -> dict:
    question = get_submission_question_or_404(supabase, question_id)
    stats_exam_code = resolve_stats_exam_code(supabase, user_id, question, requested_exam_code)
    stats_question = {**question, "exam_code": stats_exam_code}
    is_correct = selected_answer == question["answer"]
    current_ability = get_current_ability_stats(supabase, user_id, stats_question) if include_ability_accuracy else None

    return {
        "question_id": question_id,
        "exam_code": stats_exam_code,
        "subject": question["subject"],
        "module": question["module"],
        "submodule": question["submodule"],
        "source_type": question.get("source_type"),
        "selected_answer": selected_answer,
        "correct_answer": question["answer"],
        "is_correct": is_correct,
        "explanation": question["explanation"],
        "added_to_wrong_questions": not is_correct and not is_ai_generated_question(question),
        "ability_accuracy": calculate_next_accuracy(current_ability, is_correct) if include_ability_accuracy else None,
    }


def mark_unfamiliar_answer(
    supabase: Client,
    user_id: str,
    question_id: str,
    requested_exam_code: str | None = None,
) -> dict:
    question = get_question_or_404(supabase, question_id)
    stats_exam_code = resolve_stats_exam_code(supabase, user_id, question, requested_exam_code)
    stats_question = {**question, "exam_code": stats_exam_code}
    current_ability = get_current_ability_stats(supabase, user_id, stats_question)
    selected_answer = pick_wrong_answer(question["answer"])

    return {
        "question_id": question_id,
        "exam_code": stats_exam_code,
        "subject": question["subject"],
        "module": question["module"],
        "submodule": question["submodule"],
        "source_type": question.get("source_type"),
        "selected_answer": selected_answer,
        "correct_answer": question["answer"],
        "is_correct": False,
        "explanation": question["explanation"],
        "added_to_wrong_questions": not is_ai_generated_question(question),
        "ability_accuracy": calculate_next_accuracy(current_ability, False),
    }


def list_answer_history(
    supabase: Client,
    user_id: str,
    status_filter: str = "all",
    subject: str | None = None,
    limit: int = 30,
    offset: int = 0,
) -> dict:
    """Return recent answer records with question details for the practice history page."""

    def build_query(fields: str):
        query = (
            supabase.table("user_answers")
            .select(fields)
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        if status_filter == "correct":
            query = query.eq("is_correct", True)
        elif status_filter == "wrong":
            query = query.eq("is_correct", False)
        return query

    try:
        response = build_query(
            "id,question_id,client_submission_id,stats_exam_code,attempt_number,is_first_attempt,"
            "selected_answer,is_correct,used_time,created_at,questions(*)"
        ).execute()
    except Exception as exc:
        if not is_missing_supabase_relation_error(exc):
            raise
        response = build_query(
            "id,question_id,selected_answer,is_correct,used_time,created_at,questions(*)"
        ).execute()
    items: list[dict] = []
    for row in response.data or []:
        question = row.get("questions")
        if subject and question and question.get("subject") != subject:
            continue
        items.append(
            {
                "id": row["id"],
                "question_id": row["question_id"],
                "selected_answer": row["selected_answer"],
                "is_correct": row["is_correct"],
                "used_time": row.get("used_time", 0),
                "client_submission_id": row.get("client_submission_id"),
                "stats_exam_code": row.get("stats_exam_code"),
                "attempt_number": int(row.get("attempt_number") or 1),
                "is_first_attempt": bool(row.get("is_first_attempt")),
                "created_at": row["created_at"],
                "question": question,
            }
        )

    return {"items": items, "count": len(items)}
