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
    "question_type",
    "difficulty",
    "estimated_time_sec",
    "answer",
    "explanation",
)
_SUBMISSION_QUESTION_CACHE_TTL_SECONDS = 10 * 60.0
_SUBMISSION_QUESTION_CACHE_MAX_ENTRIES = 3000
_submission_question_cache: OrderedDict[str, tuple[dict, float]] = OrderedDict()
_submission_question_cache_lock = Lock()


def _submission_question_cache_key(
    question_id: str,
    practice_session_item_id: str | None = None,
    user_id: str | None = None,
) -> str:
    if practice_session_item_id:
        return f"adaptive:{user_id}:{practice_session_item_id}:{question_id}"
    return f"question:{question_id}"


def _cache_submission_question(
    question: dict,
    *,
    practice_session_item_id: str | None = None,
    user_id: str | None = None,
) -> None:
    question_id = str(question.get("id") or "")
    if not question_id or not question.get("answer"):
        return

    if practice_session_item_id and not user_id:
        return
    cache_key = _submission_question_cache_key(
        question_id,
        practice_session_item_id,
        user_id,
    )
    cached_question = {field: question.get(field) for field in _SUBMISSION_QUESTION_FIELDS}
    with _submission_question_cache_lock:
        _submission_question_cache[cache_key] = (
            cached_question,
            monotonic() + _SUBMISSION_QUESTION_CACHE_TTL_SECONDS,
        )
        _submission_question_cache.move_to_end(cache_key)
        while len(_submission_question_cache) > _SUBMISSION_QUESTION_CACHE_MAX_ENTRIES:
            _submission_question_cache.popitem(last=False)


def warm_submission_questions(
    questions: list[dict],
    *,
    practice_session_item_id: str | None = None,
    user_id: str | None = None,
) -> None:
    """Warm grading data from question-list rows without exposing answers."""

    for question in questions:
        _cache_submission_question(
            question,
            practice_session_item_id=practice_session_item_id,
            user_id=user_id,
        )


def _get_cached_submission_question(
    question_id: str,
    practice_session_item_id: str | None = None,
    user_id: str | None = None,
) -> dict | None:
    key = _submission_question_cache_key(
        str(question_id),
        practice_session_item_id,
        user_id,
    )
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


def assert_single_answer_feedback_allowed(
    supabase: Client,
    *,
    user_id: str,
    question_id: str,
    practice_session_item_id: str | None = None,
) -> None:
    """Keep fixed comprehensive rounds behind their one batch hand-in channel.

    The check deliberately runs before the grading cache is consulted.  Checking
    only ``practice_session_item_id`` is insufficient because a client already
    knows the question id and could otherwise omit the item id when calling a
    legacy grade/submit endpoint.
    """

    try:
        response = call_supabase(
            lambda: supabase.rpc(
                "assert_single_answer_feedback_allowed",
                {
                    "p_user_id": user_id,
                    "p_question_id": question_id,
                    "p_practice_session_item_id": practice_session_item_id,
                },
            ).execute(),
            operation_name="check comprehensive answer embargo",
        )
    except Exception as exc:
        if "adaptive_comprehensive_batch_required" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ADAPTIVE_COMPREHENSIVE_BATCH_REQUIRED",
                    "message": "综合刷题须在整轮交卷后统一查看答案与解析",
                },
            ) from exc
        # During a rolling deployment the assertion RPC can be absent before
        # comprehensive sessions are enabled.  The atomic answer RPC below is
        # still the authoritative write barrier after the migration lands.
        if is_missing_supabase_relation_error(exc):
            return
        raise

    data = response.data
    if isinstance(data, list):
        data = data[0] if data else None
    if data is not True and not (isinstance(data, dict) and data.get("allowed") is True):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="作答反馈状态暂时未能确认",
        )


def get_submission_question_or_404(
    supabase: Client,
    question_id: str,
    *,
    practice_session_item_id: str | None = None,
    user_id: str | None = None,
) -> dict:
    """Fetch only the fields needed to grade and explain one submitted answer."""
    if practice_session_item_id and not user_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="个性化题目缺少用户作用域",
        )
    if user_id:
        assert_single_answer_feedback_allowed(
            supabase,
            user_id=user_id,
            question_id=question_id,
            practice_session_item_id=practice_session_item_id,
        )
    cached_question = _get_cached_submission_question(
        question_id,
        practice_session_item_id,
        user_id,
    )
    if cached_question:
        return cached_question

    if practice_session_item_id:
        try:
            response = call_supabase(
                lambda: supabase.rpc(
                    "get_adaptive_question_snapshot",
                    {
                        "p_user_id": user_id,
                        "p_practice_session_item_id": practice_session_item_id,
                        "p_question_id": question_id,
                    },
                ).execute(),
                operation_name="load adaptive grading snapshot",
            )
        except Exception as exc:
            if "adaptive_comprehensive_batch_required" in str(exc).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "ADAPTIVE_COMPREHENSIVE_BATCH_REQUIRED",
                        "message": "综合刷题须在整轮交卷后统一查看答案与解析",
                    },
                ) from exc
            if "adaptive_question_snapshot_not_found" in str(exc).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="个性化题目版本与当前题位不一致",
                ) from exc
            raise
        question = response.data
        if isinstance(question, list):
            question = question[0] if question else None
        if not isinstance(question, dict) or str(question.get("id") or "") != str(question_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="个性化题目版本与当前题位不一致",
            )
        _cache_submission_question(
            question,
            practice_session_item_id=practice_session_item_id,
            user_id=user_id,
        )
        return question

    response = (
        supabase.table("questions")
        .select(
            "id, exam_code, subject, module, submodule, source_type, question_type, "
            "difficulty, estimated_time_sec, answer, explanation"
        )
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
    if question_exam_code == "COMMON" and question.get("subject") not in PUBLIC_SUBJECTS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="题目不属于可跨考试版本复用的公共学科",
        )
    if requested_exam_code in VERSION_EXAM_CODES:
        if question_exam_code not in {"COMMON", requested_exam_code}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="题目不属于当前考试版本",
            )
        return requested_exam_code

    if question_exam_code != "COMMON":
        return question_exam_code

    if requested_exam_code in VERSION_EXAM_CODES:
        return requested_exam_code

    return resolve_user_exam_code(supabase, user_id, requested_exam_code)


def resolve_user_exam_code(
    supabase: Client,
    user_id: str,
    requested_exam_code: str | None = None,
) -> str:
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
    practice_session_item_id: str | None = None,
    comprehensive_session_id: str | None = None,
    comprehensive_client_submission_id: str | None = None,
    comprehensive_manifest_hash: str | None = None,
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
    if practice_session_item_id:
        rpc_payload["p_practice_session_item_id"] = str(practice_session_item_id)
    if comprehensive_session_id or comprehensive_client_submission_id or comprehensive_manifest_hash:
        if not (
            practice_session_item_id
            and comprehensive_session_id
            and comprehensive_client_submission_id
            and comprehensive_manifest_hash
        ):
            raise ValueError("comprehensive answer persistence context is incomplete")
        rpc_payload.update(
            {
                "p_submission_kind": "comprehensive_batch",
                "p_comprehensive_session_id": str(comprehensive_session_id),
                "p_comprehensive_client_submission_id": str(
                    comprehensive_client_submission_id
                ),
                "p_comprehensive_manifest_hash": str(comprehensive_manifest_hash),
            }
        )

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
        if "adaptive_comprehensive_" in error_text or any(
            marker in error_text
            for marker in (
                "answer_submission_scope_mismatch",
                "adaptive_session_item_scope_mismatch",
                "adaptive_session_item_answer_conflict",
                "adaptive_session_item_already_skipped",
                "adaptive_session_not_active",
                "adaptive_answer_requires_client_submission_id",
                "adaptive_answer_already_attached",
                "adaptive_scope_mismatch",
                "adaptive_question_snapshot_not_found",
                "adaptive_question_snapshot_invalid",
            )
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="作答与当前个性化练习作用域不一致",
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

        if comprehensive_manifest_hash:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="综合刷题交卷迁移尚未启用",
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
    practice_session_item_id: str | None = None,
) -> dict:
    question = get_submission_question_or_404(
        supabase,
        question_id,
        practice_session_item_id=practice_session_item_id,
        user_id=user_id,
    )
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
        "question_type": question.get("question_type"),
        "difficulty": question.get("difficulty"),
        "estimated_time_sec": question.get("estimated_time_sec"),
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
    practice_session_item_id: str | None = None,
) -> dict:
    question = get_submission_question_or_404(
        supabase,
        question_id,
        practice_session_item_id=practice_session_item_id,
        user_id=user_id,
    )
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
        "question_type": question.get("question_type"),
        "difficulty": question.get("difficulty"),
        "estimated_time_sec": question.get("estimated_time_sec"),
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
    exam_code: str | None = None,
    subject: str | None = None,
    limit: int = 30,
    offset: int = 0,
) -> dict:
    """Return recent answer records with question details for the practice history page."""

    normalized_exam_code = str(exam_code or "").strip().upper() or None
    normalized_subject = str(subject or "").strip() or None

    def build_query(fields: str, *, scoped_columns: bool):
        query = (
            supabase.table("user_answers")
            .select(fields)
            .eq("user_id", user_id)
        )
        if normalized_exam_code:
            if scoped_columns:
                query = query.eq("stats_exam_code", normalized_exam_code)
                query = query.in_("questions.exam_code", [normalized_exam_code, "COMMON"])
            else:
                legacy_codes = [normalized_exam_code, "COMMON"]
                query = query.in_("questions.exam_code", legacy_codes)
        if normalized_subject:
            query = query.eq("questions.subject", normalized_subject)
        if status_filter == "correct":
            query = query.eq("is_correct", True)
        elif status_filter == "wrong":
            query = query.eq("is_correct", False)
        return query.order("created_at", desc=True).range(offset, offset + limit - 1)

    try:
        response = build_query(
            "id,question_id,client_submission_id,stats_exam_code,attempt_number,is_first_attempt,"
            "scope_attempt_number,is_first_attempt_in_scope,selected_answer,is_correct,used_time,"
            "created_at,questions!inner(*)",
            scoped_columns=True,
        ).execute()
    except Exception as exc:
        if not is_missing_supabase_relation_error(exc):
            raise
        response = build_query(
            "id,question_id,selected_answer,is_correct,used_time,created_at,questions!inner(*)",
            scoped_columns=False,
        ).execute()
    items: list[dict] = []
    for row in response.data or []:
        question = row.get("questions")
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
                "scope_attempt_number": row.get("scope_attempt_number"),
                "is_first_attempt_in_scope": row.get("is_first_attempt_in_scope"),
                "created_at": row["created_at"],
                "question": question,
            }
        )

    return {"items": items, "count": len(items)}
