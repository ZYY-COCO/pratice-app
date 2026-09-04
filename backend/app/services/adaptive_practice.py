"""Persistence orchestration for adaptive practice V1.

The math and sequencing primitives live in :mod:`adaptive_engine`.  This module
owns scope validation, Supabase reads/writes, recommendation audit rows and the
idempotent link from a durable answer to one model update.
"""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
import re
from threading import Lock
from time import monotonic
from typing import Any

from fastapi import HTTPException, status

from app.schemas.adaptive_practice import (
    CreateAdaptivePracticeSessionRequest,
    SubmitAdaptiveComprehensiveSessionRequest,
)
from app.services.adaptive_engine import (
    MODEL_VERSION,
    STRATEGY_VERSION,
    AbilityState,
    Candidate,
    DiagnosticStatus,
    EvidenceContext,
    Observation,
    TargetZone,
    compute_evidence_weight,
    confidence_label,
    detect_inversion,
    difficulty_to_theta,
    level_range,
    plan_comprehensive_targets,
    plan_next_target,
    score_candidate,
    select_top_k_weighted,
    update_ability,
    validate_scope,
)
from app.services.answers import (
    persist_answer_submission,
    warm_submission_questions,
)
from app.services.question_sources import exclude_ai_generated_questions
from app.services.supabase_resilience import (
    call_supabase,
    is_missing_supabase_relation_error,
)


logger = logging.getLogger(__name__)
PUBLIC_SUBJECTS = {"中华文化", "英语运用"}
MAX_CANDIDATE_ROWS = 3000
PAGE_SIZE = 1000
PROGRESS_QUERY_BATCH_SIZE = 200
HISTORY_LOOKUP_BATCH_SIZE = 200
RECENT_QUESTION_LIMIT = 100
MAX_STATS_EXAM_SCOPES = 2
REVIEW_INTERVAL_DAYS = (1, 2, 4, 7, 15, 30)
CANDIDATE_CACHE_TTL_SECONDS = 90.0
CANDIDATE_CACHE_MAX_ENTRIES = 8
INITIAL_DIAGNOSTIC_D4_KEY = "initial_diagnostic_d4_question_id"
RETRYABLE_ADAPTIVE_UPDATE_ERRORS = (
    "adaptive_state_conflict",
    "adaptive_conflict_verification_snapshot_mismatch",
    "adaptive_conflict_verification_difficulty_mismatch",
)
_UNSET = object()

# Candidate rows and their calibration metadata change far less frequently than
# a learner's state.  Keep a short, process-local snapshot so the expensive
# scope scan performed for the first item can be reused by the following /next
# requests.  Values are always copied at both boundaries: selection code may
# attach request-local metadata and must never mutate a later request's view.
_candidate_cache_lock = Lock()
_candidate_question_cache: OrderedDict[
    tuple[str, str, tuple[tuple[str, str], ...]],
    tuple[list[dict], float],
] = OrderedDict()
_candidate_calibration_cache: OrderedDict[
    tuple[str, str, tuple[tuple[str, str], ...]],
    tuple[frozenset[str], dict[str, dict], float],
] = OrderedDict()


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_datetime(value: object) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _normalize_stem(value: object) -> str:
    text = re.sub(r"\s+", "", str(value or "")).lower()
    return re.sub(r"[，。！？；：,.!?;:()\[\]（）【】“”‘’\"']", "", text)


def _is_retryable_adaptive_update_error(exc: Exception) -> bool:
    error_text = str(exc).lower()
    return any(marker in error_text for marker in RETRYABLE_ADAPTIVE_UPDATE_ERRORS)


def _question_exam_codes(exam_code: str, subject: str) -> list[str]:
    if subject in PUBLIC_SUBJECTS:
        return ["COMMON", exam_code]
    return [exam_code]


def _query_one(query, *, operation_name: str) -> dict | None:
    response = call_supabase(lambda: query.limit(1).execute(), operation_name=operation_name)
    rows = response.data or []
    return rows[0] if rows else None


def _state_from_row(row: dict | None, *, topic_default_theta: float = 0.0) -> AbilityState:
    if not row:
        return AbilityState(theta=topic_default_theta)
    raw_status = str(row.get("diagnostic_status") or "NEW").upper()
    try:
        diagnostic_status = DiagnosticStatus(raw_status)
    except ValueError:
        diagnostic_status = DiagnosticStatus.NEW
    return AbilityState(
        theta=float(row.get("theta") or 0.0),
        uncertainty=float(row.get("uncertainty") or 1.6),
        effective_evidence=float(row.get("effective_evidence") or 0.0),
        reliable_first_attempt_count=int(row.get("reliable_first_attempt_count") or 0),
        diagnostic_status=diagnostic_status,
        pending_conflict_count=int(row.get("pending_conflict_count") or 0),
        state_version=int(row.get("state_version") or 0),
    )


def _load_subject_state_row(supabase, user_id: str, exam_code: str, subject: str) -> dict | None:
    return _query_one(
        supabase.table("user_subject_state")
        .select("*")
        .eq("user_id", user_id)
        .eq("stats_exam_code", exam_code)
        .eq("subject", subject),
        operation_name="load adaptive subject state",
    )


def load_subject_state(supabase, user_id: str, exam_code: str, subject: str) -> AbilityState:
    validate_scope(exam_code, subject)
    try:
        row = _load_subject_state_row(supabase, user_id, exam_code, subject)
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            return AbilityState()
        raise
    return _state_from_row(row)


def load_topic_state(
    supabase,
    user_id: str,
    exam_code: str,
    subject: str,
    module: str,
    submodule: str,
    *,
    subject_theta: float,
) -> AbilityState:
    try:
        row = _query_one(
            supabase.table("user_topic_state")
            .select("*")
            .eq("user_id", user_id)
            .eq("stats_exam_code", exam_code)
            .eq("subject", subject)
            .eq("module", module)
            .eq("submodule", submodule),
            operation_name="load adaptive topic state",
        )
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            return AbilityState(theta=subject_theta)
        raise
    return _state_from_row(row, topic_default_theta=subject_theta)


def load_topic_state_map(supabase, user_id: str, exam_code: str, subject: str) -> dict[tuple[str, str], AbilityState]:
    try:
        response = call_supabase(
            lambda: (
                supabase.table("user_topic_state")
                .select("*")
                .eq("user_id", user_id)
                .eq("stats_exam_code", exam_code)
                .eq("subject", subject)
                .execute()
            ),
            operation_name="load adaptive topic states",
        )
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            return {}
        raise
    result: dict[tuple[str, str], AbilityState] = {}
    for row in response.data or []:
        result[(str(row.get("module") or ""), str(row.get("submodule") or ""))] = _state_from_row(row)
    return result


def _is_duplicate_key_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "23505" in text or "duplicate key" in text or "unique constraint" in text


def _bootstrap_state_row(
    *,
    user_id: str,
    exam_code: str,
    subject: str,
    state: AbilityState,
    last_answered_at: str | None,
) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "stats_exam_code": exam_code,
        "subject": subject,
        "theta": state.theta,
        "uncertainty": state.uncertainty,
        "effective_evidence": state.effective_evidence,
        "reliable_first_attempt_count": state.reliable_first_attempt_count,
        "pending_conflict_count": state.pending_conflict_count,
        "state_version": state.state_version,
        "model_version": f"{MODEL_VERSION}-bootstrap",
        "last_answered_at": last_answered_at,
    }


def bootstrap_subject_state_if_needed(
    supabase,
    *,
    user_id: str,
    exam_code: str,
    subject: str,
    history_limit: int = 500,
) -> tuple[AbilityState, dict[str, Any]]:
    """Lazily replay legacy reliable answers only when this scope has no state.

    The history query is filtered by the actual stats exam code and subject in
    PostgREST before its limit is applied. No synthetic model-update audit rows
    are created for this one-time bootstrap.
    """

    exam_code, subject = validate_scope(exam_code, subject)
    try:
        existing = _load_subject_state_row(supabase, user_id, exam_code, subject)
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            return AbilityState(), {"bootstrap_applied": False, "migration_pending": True}
        raise
    if existing:
        return _state_from_row(existing), {"bootstrap_applied": False, "bootstrap_count": 0}

    query = (
        supabase.table("user_answers")
        .select(
            "id,is_correct,used_time,created_at,questions!inner("
            "id,subject,module,submodule,question_type,difficulty,estimated_time_sec,source_type)"
        )
        .eq("user_id", user_id)
        .eq("stats_exam_code", exam_code)
        .eq("is_first_attempt", True)
        .eq("questions.subject", subject)
    )
    physical_exam_codes = _question_exam_codes(exam_code, subject)
    query = (
        query.in_("questions.exam_code", physical_exam_codes)
        if len(physical_exam_codes) > 1
        else query.eq("questions.exam_code", physical_exam_codes[0])
    )
    query = (
        query.order("created_at", desc=True)
        .order("id", desc=True)
        .limit(max(1, min(int(history_limit), 500)))
    )
    query = exclude_ai_generated_questions(query, reference_table="questions")
    try:
        response = call_supabase(
            lambda: query.execute(),
            operation_name="load scoped adaptive bootstrap history",
        )
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            return AbilityState(), {"bootstrap_applied": False, "migration_pending": True}
        raise

    descending_rows = list(response.data or [])
    rows = list(reversed(descending_rows))
    if not rows:
        return AbilityState(), {"bootstrap_applied": False, "bootstrap_count": 0}

    calibrations = _load_calibration_map(
        supabase,
        exam_code,
        [str((row.get("questions") or {}).get("id") or "") for row in rows],
    )
    subject_state = AbilityState()
    topic_states: dict[tuple[str, str], AbilityState] = {}
    covered_topics: set[tuple[str, str]] = set()
    replayed_count = 0
    last_answered_at: str | None = None

    for row in rows:
        question = row.get("questions") or {}
        question_id = str(question.get("id") or "")
        module = str(question.get("module") or "")
        submodule = str(question.get("submodule") or "")
        if not question_id or not module or not submodule:
            continue
        calibration = calibrations.get(question_id) or {}
        raw_quality_weight = calibration.get("quality_weight")
        quality_weight = 0.7 if raw_quality_weight is None else float(raw_quality_weight)
        evidence = compute_evidence_weight(
            EvidenceContext(
                is_first_attempt=True,
                answer_seen=False,
                question_valid=str(calibration.get("quality_status") or "") != "EXCLUDED",
                quality_weight=quality_weight,
                used_time=row.get("used_time"),
                estimated_time=question.get("estimated_time_sec"),
            )
        )
        if evidence.weight <= 0:
            continue
        topic_key = (module, submodule)
        topic_state = topic_states.get(topic_key, AbilityState(theta=subject_state.theta))
        if evidence.reliable_first_attempt:
            covered_topics.add(topic_key)
        update = update_ability(
            subject_state,
            topic_state,
            difficulty=int(question.get("difficulty") or 2),
            is_correct=bool(row.get("is_correct")),
            evidence=evidence,
            empirical_difficulty=(
                float(calibration["item_difficulty"])
                if calibration.get("item_difficulty") is not None
                else None
            ),
            subject_coverage_ready=len(covered_topics) >= 2,
        )
        subject_state = update.subject_after
        topic_states[topic_key] = update.topic_after
        replayed_count += 1
        last_answered_at = str(row.get("created_at") or last_answered_at or "") or None

    if replayed_count == 0:
        return AbilityState(), {"bootstrap_applied": False, "bootstrap_count": 0}

    for (module, submodule), topic_state in topic_states.items():
        topic_row = {
            **_bootstrap_state_row(
                user_id=user_id,
                exam_code=exam_code,
                subject=subject,
                state=topic_state,
                last_answered_at=last_answered_at,
            ),
            "module": module,
            "submodule": submodule,
        }
        topic_row.pop("diagnostic_status", None)
        try:
            call_supabase(
                lambda topic_row=topic_row: supabase.table("user_topic_state").insert(topic_row).execute(),
                operation_name="insert adaptive bootstrap topic state",
                attempts=1,
            )
        except Exception as exc:
            if not _is_duplicate_key_error(exc):
                raise

    subject_row = {
        **_bootstrap_state_row(
            user_id=user_id,
            exam_code=exam_code,
            subject=subject,
            state=subject_state,
            last_answered_at=last_answered_at,
        ),
        "diagnostic_status": subject_state.diagnostic_status.value,
    }
    try:
        call_supabase(
            lambda: supabase.table("user_subject_state").insert(subject_row).execute(),
            operation_name="insert adaptive bootstrap subject state",
            attempts=1,
        )
    except Exception as exc:
        if not _is_duplicate_key_error(exc):
            raise

    winning_row = _load_subject_state_row(supabase, user_id, exam_code, subject)
    winning_state = _state_from_row(winning_row) if winning_row else subject_state
    return winning_state, {
        "bootstrap_applied": True,
        "bootstrap_count": replayed_count,
        "bootstrap_history_limit": max(1, min(int(history_limit), 500)),
        "bootstrap_truncated": len(descending_rows) >= max(1, min(int(history_limit), 500)),
        "bootstrap_cutoff": str(rows[0].get("created_at") or "") or None,
    }


def serialize_state(state: AbilityState) -> dict[str, Any]:
    low, high = level_range(state.theta, state.uncertainty)
    level_text = f"D{low}" if low == high else f"D{low}–D{high}"
    return {
        "theta": state.theta,
        "uncertainty": state.uncertainty,
        "effective_evidence": state.effective_evidence,
        "reliable_first_attempt_count": state.reliable_first_attempt_count,
        "diagnostic_status": state.diagnostic_status.value,
        "pending_conflicts": state.pending_conflict_count,
        "confidence_label": confidence_label(state),
        "initial_level_range": level_text,
    }


def _session_view(row: dict) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "exam_code": str(row["stats_exam_code"]),
        "subject": str(row["subject"]),
        "practice_mode": str(row["mode"]),
        "question_count": int(row["requested_question_count"]),
        "preference": str(row.get("user_preference") or "standard"),
        "status": str(row.get("status") or "ACTIVE"),
        "diagnostic_status": str(row.get("diagnostic_status") or "NEW"),
        "strategy_version": str(row.get("strategy_version") or STRATEGY_VERSION),
        "model_version": str(row.get("model_version") or MODEL_VERSION),
    }


def _safe_question(row: dict) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "exam_code": str(row.get("exam_code") or ""),
        "subject": str(row.get("subject") or ""),
        "module": str(row.get("module") or ""),
        "submodule": str(row.get("submodule") or ""),
        "question_type": str(row.get("question_type") or "single_choice"),
        "stem": str(row.get("stem") or ""),
        "option_a": str(row.get("option_a") or ""),
        "option_b": str(row.get("option_b") or ""),
        "option_c": str(row.get("option_c") or ""),
        "option_d": str(row.get("option_d") or ""),
        "answer": None,
        "explanation": None,
        "difficulty": int(row.get("difficulty") or 2),
        "source_type": row.get("source_type"),
        "source_year": row.get("source_year"),
        "passage_id": row.get("passage_id"),
    }


def _verification_slot_expired(item: dict) -> bool:
    """Return whether a former VERIFY reservation has lost its lease."""

    metadata = item.get("strategy_metadata") or {}
    return metadata.get("verification_slot_expired") is True


def _item_view(item: dict, question: dict) -> dict[str, Any]:
    metadata = item.get("strategy_metadata") or {}
    reason_codes = metadata.get("reason_codes") or [item.get("selection_reason")]
    reason_codes = [str(value) for value in reason_codes if value]
    return {
        "id": str(item["id"]),
        "session_id": str(item["session_id"]),
        "position": int(item["position"]),
        "reason_codes": reason_codes,
        "target_zone": str(item.get("target_zone") or "main"),
        "predicted_correct_probability": item.get("predicted_probability"),
        "is_diagnostic": bool(item.get("is_diagnostic")),
        "is_challenge": bool(item.get("is_challenge")),
        "question": _safe_question(question),
    }


def _normalized_scope_pairs(scopes: list[dict]) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            {
                (
                    str(scope.get("module") or "").strip(),
                    str(scope.get("submodule") or "").strip(),
                )
                for scope in scopes
                if str(scope.get("module") or "").strip()
            }
        )
    )


def _scope_matches(question: dict, scopes: list[dict]) -> bool:
    if not scopes:
        return True
    normalized_scopes = _normalized_scope_pairs(scopes)
    if not normalized_scopes:
        return False
    module = str(question.get("module") or "")
    submodule = str(question.get("submodule") or "")
    return any(
        module == scope_module
        and (
            not scope_submodule
            or submodule == scope_submodule
        )
        for scope_module, scope_submodule in normalized_scopes
    )


def _candidate_cache_key(
    session: dict,
) -> tuple[str, str, tuple[tuple[str, str], ...]]:
    """Return the immutable bank-snapshot scope for one adaptive session."""

    normalized_scopes = _normalized_scope_pairs(
        list(session.get("scope_filter") or [])
    )
    return (
        str(session.get("stats_exam_code") or "").strip().upper(),
        str(session.get("subject") or "").strip(),
        normalized_scopes,
    )


def _clear_candidate_caches() -> None:
    """Reset process-local snapshots (used by tests and controlled reloads)."""

    with _candidate_cache_lock:
        _candidate_question_cache.clear()
        _candidate_calibration_cache.clear()


def _invalidate_candidate_cache(session: dict) -> None:
    """Drop one bank-scope snapshot after a trusted item fails revalidation."""

    key = _candidate_cache_key(session)
    with _candidate_cache_lock:
        _candidate_question_cache.pop(key, None)
        _candidate_calibration_cache.pop(key, None)


def _read_cached_candidate_questions(session: dict) -> list[dict] | None:
    key = _candidate_cache_key(session)
    now = monotonic()
    with _candidate_cache_lock:
        cached = _candidate_question_cache.get(key)
        if not cached:
            return None
        rows, expires_at = cached
        if expires_at <= now:
            _candidate_question_cache.pop(key, None)
            _candidate_calibration_cache.pop(key, None)
            return None
        _candidate_question_cache.move_to_end(key)
        return deepcopy(rows)


def _store_cached_candidate_questions(session: dict, rows: list[dict]) -> None:
    key = _candidate_cache_key(session)
    snapshot = deepcopy(list(rows))
    with _candidate_cache_lock:
        _candidate_question_cache[key] = (
            snapshot,
            monotonic() + CANDIDATE_CACHE_TTL_SECONDS,
        )
        _candidate_question_cache.move_to_end(key)
        while len(_candidate_question_cache) > CANDIDATE_CACHE_MAX_ENTRIES:
            evicted_key, _ = _candidate_question_cache.popitem(last=False)
            _candidate_calibration_cache.pop(evicted_key, None)


def _read_cached_candidate_calibrations(
    session: dict,
    question_ids: list[str],
) -> dict[str, dict] | None:
    key = _candidate_cache_key(session)
    expected_ids = frozenset(str(value) for value in question_ids if value)
    now = monotonic()
    with _candidate_cache_lock:
        cached = _candidate_calibration_cache.get(key)
        if not cached:
            return None
        cached_ids, calibrations, expires_at = cached
        if expires_at <= now:
            _candidate_calibration_cache.pop(key, None)
            return None
        if cached_ids != expected_ids:
            return None
        _candidate_calibration_cache.move_to_end(key)
        return deepcopy(calibrations)


def _store_cached_candidate_calibrations(
    session: dict,
    question_ids: list[str],
    calibrations: dict[str, dict],
) -> None:
    key = _candidate_cache_key(session)
    cached_ids = frozenset(str(value) for value in question_ids if value)
    snapshot = deepcopy(dict(calibrations))
    with _candidate_cache_lock:
        _candidate_calibration_cache[key] = (
            cached_ids,
            snapshot,
            monotonic() + CANDIDATE_CACHE_TTL_SECONDS,
        )
        _candidate_calibration_cache.move_to_end(key)
        while len(_candidate_calibration_cache) > CANDIDATE_CACHE_MAX_ENTRIES:
            evicted_key, _ = _candidate_calibration_cache.popitem(last=False)
            _candidate_question_cache.pop(evicted_key, None)


def _fetch_candidate_questions(supabase, session: dict) -> list[dict]:
    raw_scopes = list(session.get("scope_filter") or [])
    scope_keys = [
        (module, submodule or None)
        for module, submodule in _normalized_scope_pairs(raw_scopes)
    ]
    if raw_scopes and not scope_keys:
        return []
    cached = _read_cached_candidate_questions(session)
    if cached is not None:
        return cached

    exam_codes = _question_exam_codes(session["stats_exam_code"], session["subject"])
    fields = (
        "id,exam_code,subject,module,submodule,question_type,stem,option_a,option_b,"
        "option_c,option_d,answer,explanation,difficulty,source_type,source_year,passage_id,"
        "skill_tags,solution_type,estimated_time_sec,status"
    )
    query_scopes: list[tuple[str | None, str | None]] = (
        scope_keys if scope_keys else [(None, None)]
    )
    per_scope_limit = (
        MAX_CANDIDATE_ROWS
        if len(query_scopes) == 1
        else max(60, MAX_CANDIDATE_ROWS // len(query_scopes))
    )
    rows: list[dict] = []
    for module, submodule in query_scopes:
        scope_rows: list[dict] = []
        for offset in range(0, per_scope_limit, PAGE_SIZE):
            page_size = min(PAGE_SIZE, per_scope_limit - offset)
            query = exclude_ai_generated_questions(
                supabase.table("questions").select(fields).eq("subject", session["subject"])
            ).eq("status", "active")
            query = (
                query.in_("exam_code", exam_codes)
                if len(exam_codes) > 1
                else query.eq("exam_code", exam_codes[0])
            )
            if module:
                query = query.eq("module", module)
            if submodule:
                query = query.eq("submodule", submodule)
            query = query.order("id", desc=False)
            response = call_supabase(
                lambda query=query, offset=offset, page_size=page_size: query.range(
                    offset,
                    offset + page_size - 1,
                ).execute(),
                operation_name="load adaptive question candidates",
            )
            chunk = response.data or []
            scope_rows.extend(chunk)
            if len(chunk) < page_size:
                break
        rows.extend(scope_rows)

    scopes = [
        {"module": module, "submodule": submodule}
        for module, submodule in scope_keys
    ]
    seen_stems: set[str] = set()
    filtered: list[dict] = []
    for row in rows:
        if not _scope_matches(row, scopes):
            continue
        stem_key = _normalize_stem(row.get("stem")) or str(row.get("id") or "")
        if stem_key in seen_stems:
            continue
        seen_stems.add(stem_key)
        filtered.append(row)
    _store_cached_candidate_questions(session, filtered)
    return deepcopy(filtered)


def _load_calibration_map(
    supabase,
    exam_code: str,
    question_ids: list[str] | None = None,
) -> dict[str, dict]:
    unique_ids = list(dict.fromkeys(str(value) for value in (question_ids or []) if value))
    if question_ids is not None and not unique_ids:
        return {}
    try:
        rows: list[dict] = []
        if unique_ids:
            for start in range(0, len(unique_ids), PROGRESS_QUERY_BATCH_SIZE):
                batch = unique_ids[start : start + PROGRESS_QUERY_BATCH_SIZE]
                response = call_supabase(
                    lambda batch=batch: (
                        supabase.table("question_calibration")
                        .select("*")
                        .eq("stats_exam_code", exam_code)
                        .in_("question_id", batch)
                        .limit(len(batch))
                        .execute()
                    ),
                    operation_name="load candidate question calibration",
                )
                rows.extend(response.data or [])
        else:
            offset = 0
            while True:
                response = call_supabase(
                    lambda offset=offset: (
                        supabase.table("question_calibration")
                        .select("*")
                        .eq("stats_exam_code", exam_code)
                        .order("question_id", desc=False)
                        .range(offset, offset + PAGE_SIZE - 1)
                        .execute()
                    ),
                    operation_name="load question calibration",
                )
                chunk = response.data or []
                rows.extend(chunk)
                if len(chunk) < PAGE_SIZE:
                    break
                offset += PAGE_SIZE
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            return {}
        raise
    return {str(row["question_id"]): row for row in rows}


def _load_candidate_calibration_map(
    supabase,
    session: dict,
    question_ids: list[str],
) -> dict[str, dict]:
    unique_ids = list(dict.fromkeys(str(value) for value in question_ids if value))
    if not unique_ids:
        return {}
    cached = _read_cached_candidate_calibrations(session, unique_ids)
    if cached is not None:
        return cached
    calibrations = _load_calibration_map(
        supabase,
        str(session["stats_exam_code"]),
        unique_ids,
    )
    _store_cached_candidate_calibrations(session, unique_ids, calibrations)
    return deepcopy(calibrations)


def _selected_trusted_candidate_is_current(
    supabase,
    *,
    session: dict,
    question_id: str,
    expected_difficulty: int,
    require_diagnostic_candidate: bool,
) -> bool:
    """Revalidate a diagnostic/VERIFY item immediately before its claim.

    The broad candidate snapshot is deliberately cached for latency.  Trusted
    evidence cannot inherit that staleness: an editor may deactivate a question
    or revoke its calibration during the short cache window.  This single-row
    read keeps those state changes authoritative without rescanning the bank.
    """

    exam_code, subject = validate_scope(
        str(session.get("stats_exam_code") or ""),
        str(session.get("subject") or ""),
    )
    fields = (
        "question_id,stats_exam_code,quality_status,quality_weight,"
        "is_diagnostic_candidate,questions!inner("
        "id,exam_code,subject,module,submodule,difficulty,status)"
    )
    try:
        row = _query_one(
            supabase.table("question_calibration")
            .select(fields)
            .eq("stats_exam_code", exam_code)
            .eq("question_id", question_id),
            operation_name="revalidate selected adaptive candidate",
        )
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            return False
        raise
    if not row or str(row.get("question_id") or "") != question_id:
        return False
    if str(row.get("quality_status") or "").upper() != "APPROVED":
        return False
    try:
        quality_weight = float(row.get("quality_weight"))
    except (TypeError, ValueError):
        return False
    if quality_weight < 0.7:
        return False
    if require_diagnostic_candidate and row.get("is_diagnostic_candidate") is not True:
        return False

    question = row.get("questions") or {}
    allowed_exam_codes = set(_question_exam_codes(exam_code, subject))
    return bool(
        str(question.get("id") or "") == question_id
        and str(question.get("status") or "").lower() == "active"
        and str(question.get("subject") or "") == subject
        and str(question.get("exam_code") or "") in allowed_exam_codes
        and int(question.get("difficulty") or 0) == int(expected_difficulty)
        and _scope_matches(question, list(session.get("scope_filter") or []))
    )


def _find_fresh_approved_diagnostic_d4(
    supabase,
    *,
    user_id: str,
    session: dict,
) -> tuple[dict, dict] | None:
    """Find one trusted D4 without relying on the general candidate cap.

    The ordinary ranking pool is intentionally bounded.  A cold-start readiness
    gate is an existence check, however, so truncating that pool could report a
    false shortage when an approved D4 sorts after the cap.  Query the partial
    diagnostic index directly and stop at the first globally fresh in-scope
    physical question.
    """

    exam_code, subject = validate_scope(
        str(session["stats_exam_code"]),
        str(session["subject"]),
    )
    exam_codes = _question_exam_codes(exam_code, subject)
    fields = (
        "question_id,stats_exam_code,item_difficulty,difficulty_uncertainty,"
        "discrimination,reliable_attempt_count,reliable_correct_count,"
        "empirical_accuracy,quality_weight,quality_status,is_diagnostic_candidate,"
        "diagnostic_priority,model_version,questions!inner("
        "id,exam_code,subject,module,submodule,question_type,stem,option_a,option_b,"
        "option_c,option_d,answer,explanation,difficulty,source_type,source_year,passage_id,skill_tags,"
        "solution_type,estimated_time_sec,status)"
    )
    scopes = list(session.get("scope_filter") or [])
    offset = 0
    while True:
        query = (
            supabase.table("question_calibration")
            .select(fields)
            .eq("stats_exam_code", exam_code)
            .eq("quality_status", "APPROVED")
            .eq("is_diagnostic_candidate", True)
            .gte("quality_weight", 0.7)
            .eq("questions.subject", subject)
            .eq("questions.difficulty", 4)
            .eq("questions.status", "active")
        )
        query = (
            query.in_("questions.exam_code", exam_codes)
            if len(exam_codes) > 1
            else query.eq("questions.exam_code", exam_codes[0])
        )
        query = exclude_ai_generated_questions(query, reference_table="questions")
        response = call_supabase(
            lambda query=query, offset=offset: (
                query.order("diagnostic_priority", desc=True)
                .order("question_id", desc=False)
                .range(offset, offset + PAGE_SIZE - 1)
                .execute()
            ),
            operation_name="find fresh approved adaptive d4",
        )
        rows = list(response.data or [])
        in_scope: list[tuple[dict, dict]] = []
        for calibration in rows:
            question = calibration.get("questions") or {}
            if not question or not _scope_matches(question, scopes):
                continue
            clean_calibration = dict(calibration)
            clean_calibration.pop("questions", None)
            in_scope.append((question, clean_calibration))
        if in_scope:
            seen_ids = _load_ever_answered_question_ids(
                supabase,
                user_id,
                subject,
                [str(question.get("id") or "") for question, _ in in_scope],
            )
            for question, calibration in in_scope:
                if str(question.get("id") or "") not in seen_ids:
                    return question, calibration
        if len(rows) < PAGE_SIZE:
            return None
        offset += PAGE_SIZE


def _load_initial_diagnostic_d4_witness(
    supabase,
    *,
    session: dict,
    question_id: str,
) -> tuple[dict, dict] | None:
    """Reload a session's cap-exempt D4 witness from authoritative rows."""

    exam_code, subject = validate_scope(
        str(session["stats_exam_code"]),
        str(session["subject"]),
    )
    exam_codes = _question_exam_codes(exam_code, subject)
    fields = (
        "question_id,stats_exam_code,item_difficulty,difficulty_uncertainty,"
        "discrimination,reliable_attempt_count,reliable_correct_count,"
        "empirical_accuracy,quality_weight,quality_status,is_diagnostic_candidate,"
        "diagnostic_priority,model_version,questions!inner("
        "id,exam_code,subject,module,submodule,question_type,stem,option_a,option_b,"
        "option_c,option_d,answer,explanation,difficulty,source_type,source_year,passage_id,skill_tags,"
        "solution_type,estimated_time_sec,status)"
    )
    query = (
        supabase.table("question_calibration")
        .select(fields)
        .eq("question_id", question_id)
        .eq("stats_exam_code", exam_code)
        .eq("quality_status", "APPROVED")
        .eq("is_diagnostic_candidate", True)
        .gte("quality_weight", 0.7)
        .eq("questions.subject", subject)
        .eq("questions.difficulty", 4)
        .eq("questions.status", "active")
    )
    query = (
        query.in_("questions.exam_code", exam_codes)
        if len(exam_codes) > 1
        else query.eq("questions.exam_code", exam_codes[0])
    )
    query = exclude_ai_generated_questions(query, reference_table="questions")
    row = _query_one(
        query,
        operation_name="reload adaptive session d4 witness",
    )
    if not row:
        return None
    question = row.get("questions") or {}
    if not question or not _scope_matches(
        question,
        list(session.get("scope_filter") or []),
    ):
        return None
    calibration = dict(row)
    calibration.pop("questions", None)
    return question, calibration


def _inject_candidate_witness(
    questions: list[dict],
    witness: dict,
) -> list[dict]:
    """Replace one bounded-pool row with a request-local readiness witness."""

    witness_id = str(witness.get("id") or "")
    witness_stem = _normalize_stem(witness.get("stem"))
    filtered = [
        question
        for question in questions
        if str(question.get("id") or "") != witness_id
        and (
            not witness_stem
            or _normalize_stem(question.get("stem")) != witness_stem
        )
    ]
    if len(filtered) >= MAX_CANDIDATE_ROWS:
        filtered = filtered[: max(0, MAX_CANDIDATE_ROWS - 1)]
    filtered.append(witness)
    return filtered


def _candidate_history_ids(question_ids: list[str]) -> list[str]:
    unique_ids = list(dict.fromkeys(str(value) for value in question_ids if value))
    if len(unique_ids) > MAX_CANDIDATE_ROWS:
        raise ValueError("adaptive candidate history lookup exceeds bounded pool")
    return unique_ids


def _load_recent_question_ids(supabase, user_id: str, exam_code: str, subject: str) -> set[str]:
    """Load one fixed-size, exam-and-subject-scoped exposure window."""

    try:
        response = call_supabase(
            lambda: (
                supabase.table("user_answers")
                .select("question_id,questions!inner(subject)")
                .eq("user_id", user_id)
                .eq("stats_exam_code", exam_code)
                .eq("questions.subject", subject)
                .order("created_at", desc=True)
                .order("id", desc=True)
                .limit(RECENT_QUESTION_LIMIT)
                .execute()
            ),
            operation_name="load recent adaptive answers",
        )
    except Exception:
        return set()
    return {str(row.get("question_id")) for row in response.data or [] if row.get("question_id")}


def _load_candidate_progress_rows(
    supabase,
    user_id: str,
    subject: str,
    question_ids: list[str],
    *,
    exam_code: str | None,
) -> list[dict]:
    """Read progress by bounded candidate-ID batches, never by history pages."""

    unique_ids = _candidate_history_ids(question_ids)
    if not unique_ids:
        return []
    rows: list[dict] = []
    seen_keys: set[tuple[str, str]] = set()
    for start in range(0, len(unique_ids), HISTORY_LOOKUP_BATCH_SIZE):
        batch = unique_ids[start : start + HISTORY_LOOKUP_BATCH_SIZE]
        query = (
            supabase.table("user_question_progress")
            .select(
                "question_id,stats_exam_code,correct_count,last_is_correct,last_answered_at,"
                "questions!inner(subject)"
            )
            .eq("user_id", user_id)
            .eq("questions.subject", subject)
            .in_("question_id", batch)
        )
        row_limit = len(batch) * MAX_STATS_EXAM_SCOPES
        if exam_code is not None:
            query = query.eq("stats_exam_code", exam_code)
            row_limit = len(batch)
        response = call_supabase(
            lambda query=query, row_limit=row_limit: (
                query.order("question_id", desc=False)
                .order("stats_exam_code", desc=False)
                .limit(row_limit)
                .execute()
            ),
            operation_name="load bounded adaptive candidate progress",
        )
        batch_ids = set(batch)
        for row in response.data or []:
            question_id = str(row.get("question_id") or "")
            row_exam_code = str(row.get("stats_exam_code") or "")
            if question_id not in batch_ids:
                continue
            if exam_code is not None and row_exam_code and row_exam_code != exam_code:
                continue
            key = (question_id, row_exam_code)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            rows.append(row)
    return rows


def _load_answered_ids_from_answers(
    supabase,
    user_id: str,
    subject: str,
    question_ids: list[str],
) -> set[str]:
    """Compatibility path for deployments without scoped progress rows."""

    unique_ids = _candidate_history_ids(question_ids)
    seen: set[str] = set()
    for start in range(0, len(unique_ids), HISTORY_LOOKUP_BATCH_SIZE):
        batch = unique_ids[start : start + HISTORY_LOOKUP_BATCH_SIZE]
        response = call_supabase(
            lambda batch=batch: (
                supabase.table("user_answers")
                .select("question_id,questions!inner(subject)")
                .eq("user_id", user_id)
                .eq("questions.subject", subject)
                .eq("is_first_attempt", True)
                .in_("question_id", batch)
                .limit(len(batch))
                .execute()
            ),
            operation_name="load bounded adaptive candidate answer presence",
        )
        batch_ids = set(batch)
        seen.update(
            question_id
            for row in response.data or []
            if (question_id := str(row.get("question_id") or "")) in batch_ids
        )
    return seen


def _load_ever_answered_question_ids(
    supabase,
    user_id: str,
    subject: str,
    question_ids: list[str],
) -> set[str]:
    """Return globally seen physical question IDs for reliable evidence gates.

    This deliberately has no exam-code filter.  A COMMON question remembered
    from Z001 is not fresh diagnostic evidence when the same person later sees
    it under Z002, even though the two ability states remain fully isolated.
    """

    unique_ids = _candidate_history_ids(question_ids)
    if not unique_ids:
        return set()
    try:
        rows = _load_candidate_progress_rows(
            supabase,
            user_id,
            subject,
            unique_ids,
            exam_code=None,
        )
    except Exception as exc:
        if not is_missing_supabase_relation_error(exc):
            raise
        return _load_answered_ids_from_answers(
            supabase,
            user_id,
            subject,
            unique_ids,
        )
    return {str(row["question_id"]) for row in rows if row.get("question_id")}


def _conflict_is_in_session_scope(conflict: dict | None, session: dict) -> bool:
    if not conflict:
        return False
    return _scope_matches(
        {
            "module": str(conflict.get("module") or ""),
            "submodule": str(conflict.get("submodule") or ""),
        },
        list(session.get("scope_filter") or []),
    )


def _load_due_review_values(
    supabase,
    user_id: str,
    exam_code: str,
    subject: str,
    question_ids: list[str],
) -> dict[str, float]:
    """Load due/near-due values without ever crossing the actual exam scope."""

    unique_ids = _candidate_history_ids(question_ids)
    if not unique_ids:
        return {}
    try:
        rows = _load_candidate_progress_rows(
            supabase,
            user_id,
            subject,
            unique_ids,
            exam_code=exam_code,
        )
    except Exception as exc:
        # Before the V1 migration there is no trustworthy exam-scoped progress
        # for a COMMON question, so the conservative fallback is no review boost.
        if is_missing_supabase_relation_error(exc):
            return {}
        raise

    return _due_review_values_from_rows(rows)


def _due_review_values_from_rows(rows: list[dict]) -> dict[str, float]:
    """Convert already-scoped progress rows into deterministic review weights."""

    now = datetime.now(timezone.utc)
    values: dict[str, float] = {}
    for row in rows:
        question_id = str(row.get("question_id") or "")
        if not question_id:
            continue
        if row.get("last_is_correct") is not True:
            values[question_id] = 1.0
            continue
        answered_at = _parse_datetime(row.get("last_answered_at"))
        if answered_at is None:
            continue
        correct_count = max(1, int(row.get("correct_count") or 1))
        interval_days = REVIEW_INTERVAL_DAYS[min(correct_count - 1, len(REVIEW_INTERVAL_DAYS) - 1)]
        due_at = answered_at + timedelta(days=interval_days)
        if due_at <= now:
            values[question_id] = 1.0
            continue
        interval_seconds = max(1.0, float(interval_days * 86400))
        elapsed_ratio = max(0.0, (now - answered_at).total_seconds()) / interval_seconds
        if elapsed_ratio >= 0.5:
            values[question_id] = round(min(1.0, (elapsed_ratio - 0.5) * 2.0), 6)
    return values


def _load_candidate_history_via_rpc(
    supabase,
    *,
    user_id: str,
    exam_code: str,
    subject: str,
    question_ids: list[str],
    include_global_seen: bool,
) -> dict:
    response = call_supabase(
        lambda: supabase.rpc(
            "get_adaptive_candidate_history_v1",
            {
                "p_user_id": user_id,
                "p_stats_exam_code": exam_code,
                "p_subject": subject,
                "p_question_ids": question_ids,
                "p_recent_limit": RECENT_QUESTION_LIMIT,
                "p_include_global_seen": include_global_seen,
            },
        ).execute(),
        operation_name="load adaptive candidate history snapshot",
    )
    data = response.data
    if isinstance(data, list):
        data = data[0] if data else None
    if not isinstance(data, dict):
        raise RuntimeError("adaptive candidate history RPC returned an invalid payload")
    return data


def _load_candidate_history_snapshot(
    supabase,
    *,
    user_id: str,
    exam_code: str,
    subject: str,
    question_ids: list[str],
    include_global_seen: bool,
) -> dict[str, Any]:
    """Load all per-request history signals in one database round trip.

    The primary RPC keeps latency independent of lifetime answer count. During a
    rolling deployment, candidate-targeted progress batches preserve the same
    semantics with a query count bounded only by ``MAX_CANDIDATE_ROWS``.
    """

    exam_code, subject = validate_scope(exam_code, subject)
    unique_ids = _candidate_history_ids(question_ids)
    try:
        data = _load_candidate_history_via_rpc(
            supabase,
            user_id=user_id,
            exam_code=exam_code,
            subject=subject,
            question_ids=unique_ids,
            include_global_seen=include_global_seen,
        )
    except Exception as exc:
        if not is_missing_supabase_relation_error(exc):
            raise
        recent_ids = _load_recent_question_ids(
            supabase,
            user_id,
            exam_code,
            subject,
        )
        try:
            progress_rows = _load_candidate_progress_rows(
                supabase,
                user_id,
                subject,
                unique_ids,
                exam_code=None if include_global_seen else exam_code,
            )
        except Exception as progress_exc:
            if not is_missing_supabase_relation_error(progress_exc):
                raise
            ever_answered_ids = (
                _load_answered_ids_from_answers(
                    supabase,
                    user_id,
                    subject,
                    unique_ids,
                )
                if include_global_seen
                else set()
            )
            return {
                "recent_question_ids": recent_ids,
                "ever_answered_question_ids": ever_answered_ids,
                "due_review_values": {},
            }
        ever_answered_ids = (
            {str(row["question_id"]) for row in progress_rows if row.get("question_id")}
            if include_global_seen
            else set()
        )
        scoped_rows = [
            row
            for row in progress_rows
            if not row.get("stats_exam_code")
            or str(row.get("stats_exam_code")) == exam_code
        ]
        return {
            "recent_question_ids": recent_ids,
            "ever_answered_question_ids": ever_answered_ids,
            "due_review_values": _due_review_values_from_rows(scoped_rows),
        }

    candidate_ids = set(unique_ids)
    recent_values = data.get("recent_question_ids") or []
    ever_values = data.get("ever_answered_question_ids") or []
    progress_values = data.get("progress_rows") or []
    if not isinstance(recent_values, list) or not isinstance(ever_values, list):
        raise RuntimeError("adaptive candidate history RPC returned invalid ID arrays")
    if not isinstance(progress_values, list) or any(
        not isinstance(row, dict) for row in progress_values
    ):
        raise RuntimeError("adaptive candidate history RPC returned invalid progress rows")
    scoped_progress = [
        row
        for row in progress_values
        if str(row.get("question_id") or "") in candidate_ids
        and str(row.get("stats_exam_code") or "") == exam_code
    ]
    return {
        "recent_question_ids": {
            str(value) for value in recent_values if value
        },
        "ever_answered_question_ids": {
            str(value)
            for value in ever_values
            if value and str(value) in candidate_ids
        },
        "due_review_values": _due_review_values_from_rows(scoped_progress),
    }


def _load_session_items(supabase, session_id: str) -> list[dict]:
    response = call_supabase(
        lambda: (
            supabase.table("practice_session_items")
            .select(
                "id,session_id,question_id,position,item_status,selection_reason,target_zone,"
                "predicted_probability,theta_before,item_difficulty,score_components,"
                "strategy_metadata,is_diagnostic,is_challenge,answer_id,presented_at,answered_at,"
                "skipped_at,explanation_viewed_at,answer:user_answers(id,question_id,stats_exam_code,"
                "is_correct,is_first_attempt,used_time,created_at),"
                "persisted_snapshot:practice_session_item_question_snapshots!inner("
                "question_id,question_snapshot)"
            )
            .eq("session_id", session_id)
            .order("position")
            .execute()
        ),
        operation_name="load adaptive session items",
    )
    rows = list(response.data or [])
    for row in rows:
        embedded = row.pop("persisted_snapshot", None)
        if isinstance(embedded, list):
            embedded = embedded[0] if embedded else None
        snapshot = embedded.get("question_snapshot") if isinstance(embedded, dict) else None
        if (
            isinstance(snapshot, dict)
            and str(snapshot.get("id") or "") == str(row.get("question_id") or "")
            and str((embedded or {}).get("question_id") or "") == str(row.get("question_id") or "")
        ):
            row["questions"] = snapshot
    return rows


def _answer_map(supabase, answer_ids: list[str]) -> dict[str, dict]:
    if not answer_ids:
        return {}
    response = call_supabase(
        lambda: (
            supabase.table("user_answers")
            .select(
                "id,question_id,stats_exam_code,is_correct,is_first_attempt,"
                "used_time,created_at"
            )
            .in_("id", answer_ids)
            .execute()
        ),
        operation_name="load adaptive session answers",
    )
    return {str(row["id"]): row for row in response.data or []}


def _answer_was_seen_before_submission(item: dict, answer: dict) -> bool:
    viewed_at = _parse_datetime(item.get("explanation_viewed_at"))
    answered_at = _parse_datetime(answer.get("created_at"))
    return bool(viewed_at and (answered_at is None or viewed_at <= answered_at))


def _observations_from_items(supabase, items: list[dict]) -> list[Observation]:
    answers = {
        str(answer["id"]): answer
        for item in items
        if isinstance((answer := item.get("answer")), dict)
        and answer.get("id")
    }
    missing_answer_ids = list(
        dict.fromkeys(
            str(item["answer_id"])
            for item in items
            if item.get("answer_id") and str(item["answer_id"]) not in answers
        )
    )
    if missing_answer_ids:
        # Compatibility for a rolling API/schema-cache deployment. Once the
        # embedded relation is available, the normal path has no second read.
        answers.update(_answer_map(supabase, missing_answer_ids))
    observations: list[Observation] = []
    for item in items:
        answer = answers.get(str(item.get("answer_id") or ""))
        question = item.get("questions") or {}
        if not answer or not question:
            continue
        metadata = item.get("strategy_metadata") or {}
        raw_quality_weight = metadata.get("quality_weight")
        quality_weight = 0.7 if raw_quality_weight is None else float(raw_quality_weight)
        raw_evidence_weight = metadata.get("evidence_weight")
        if raw_evidence_weight is None:
            evidence = compute_evidence_weight(
                EvidenceContext(
                    is_first_attempt=bool(answer.get("is_first_attempt")),
                    answer_seen=_answer_was_seen_before_submission(item, answer),
                    question_valid=bool(metadata.get("question_valid", True)),
                    quality_weight=quality_weight,
                    used_time=answer.get("used_time"),
                    estimated_time=question.get("estimated_time_sec"),
                )
            )
            evidence_weight = evidence.weight
        else:
            evidence_weight = float(raw_evidence_weight)
        observations.append(
            Observation(
                question_id=str(question.get("id") or item.get("question_id") or ""),
                difficulty=int(question.get("difficulty") or 2),
                is_correct=bool(answer.get("is_correct")),
                module=str(question.get("module") or ""),
                submodule=str(question.get("submodule") or ""),
                question_type=str(question.get("question_type") or "single_choice"),
                evidence_weight=evidence_weight,
                is_first_attempt=bool(answer.get("is_first_attempt")),
                position=int(item.get("position") or 0),
            )
        )
    return observations


def _load_session(supabase, user_id: str, session_id: str, *, for_update: bool = False) -> dict:
    del for_update  # Supabase REST reads do not expose SELECT FOR UPDATE.
    row = _query_one(
        supabase.table("practice_sessions")
        .select("*")
        .eq("id", session_id)
        .eq("user_id", user_id),
        operation_name="load adaptive practice session",
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="个性化练习会话不存在")
    return row


def _build_candidates(
    *,
    questions: list[dict],
    calibrations: dict[str, dict],
    topic_states: dict[tuple[str, str], AbilityState],
    session_items: list[dict],
    recent_question_ids: set[str],
    due_review_values: dict[str, float],
) -> tuple[list[tuple[Candidate, dict]], set[str]]:
    used_ids = {str(item.get("question_id") or "") for item in session_items}
    topic_counts: dict[tuple[str, str], int] = {}
    for item in session_items:
        question = item.get("questions") or {}
        key = (str(question.get("module") or ""), str(question.get("submodule") or ""))
        topic_counts[key] = topic_counts.get(key, 0) + 1
    last_question = (session_items[-1].get("questions") or {}) if session_items else {}
    last_topic = (str(last_question.get("module") or ""), str(last_question.get("submodule") or ""))
    last_type = str(last_question.get("question_type") or "")

    result: list[tuple[Candidate, dict]] = []
    for row in questions:
        question_id = str(row.get("id") or "")
        if not question_id or question_id in used_ids:
            continue
        key = (str(row.get("module") or ""), str(row.get("submodule") or ""))
        topic_state = topic_states.get(key)
        calibration = calibrations.get(question_id) or {}
        quality_status = str(calibration.get("quality_status") or "UNREVIEWED")
        if quality_status == "EXCLUDED":
            continue
        raw_quality_weight = calibration.get("quality_weight")
        quality_weight = 0.7 if raw_quality_weight is None else float(raw_quality_weight)
        if quality_status == "FLAGGED":
            quality_weight = min(quality_weight, 0.4)
        topic_theta = topic_state.theta if topic_state else None
        topic_evidence = topic_state.effective_evidence if topic_state else 0.0
        weak_value = 0.5 if topic_state is None else max(0.0, min(1.0, 0.5 - topic_state.theta / 4.0))
        coverage_value = 1.0 / (1.0 + topic_counts.get(key, 0))
        exploration_value = 1.0 if topic_state is None else max(0.0, min(1.0, topic_state.uncertainty / 1.6))
        candidate = Candidate(
            question_id=question_id,
            difficulty=int(row.get("difficulty") or 2),
            module=key[0],
            submodule=key[1],
            question_type=str(row.get("question_type") or "single_choice"),
            quality_weight=quality_weight,
            is_diagnostic_candidate=(
                bool(calibration.get("is_diagnostic_candidate"))
                and quality_status == "APPROVED"
            ),
            diagnostic_priority=float(calibration.get("diagnostic_priority") or 0) / 100.0,
            empirical_difficulty=(
                float(calibration["item_difficulty"])
                if calibration.get("item_difficulty") is not None
                else None
            ),
            topic_theta=topic_theta,
            topic_evidence=topic_evidence,
            weak_topic_value=weak_value,
            due_review_value=float(due_review_values.get(question_id, 0.0)),
            coverage_value=coverage_value,
            exploration_value=exploration_value,
            recent_exposure_penalty=1.0 if question_id in recent_question_ids else 0.0,
            same_topic_penalty=1.0 if session_items and key == last_topic else 0.0,
            same_type_penalty=(
                1.0 if session_items and str(row.get("question_type") or "single_choice") == last_type else 0.0
            ),
        )
        result.append((candidate, row))
    return result, used_ids


def _select_and_insert_next(
    supabase,
    user_id: str,
    session: dict,
    *,
    _claim_retry: int = 0,
    _defer_verification_slot: bool = False,
    _freshness_retry: int = 0,
    _subject_state: AbilityState | None = None,
) -> dict | None:
    items = _load_session_items(supabase, str(session["id"]))
    for item in items:
        if (
            item.get("item_status") in {"SELECTED", "PRESENTED"}
            and not item.get("answer_id")
        ):
            # Lease expiry releases the cross-session VERIFY reservation; it
            # does not take the currently displayed question away from this
            # session.  A later answer is accepted as ordinary evidence.
            question = item.get("questions") or {}
            warm_submission_questions(
                [question],
                practice_session_item_id=str(item.get("id") or ""),
                user_id=user_id,
            )
            return _item_view(item, question)

    next_position = max((int(item.get("position") or 0) for item in items), default=0) + 1
    if next_position > int(session["requested_question_count"]):
        return None

    exam_code, subject = validate_scope(session["stats_exam_code"], session["subject"])
    subject_state = _subject_state or load_subject_state(
        supabase, user_id, exam_code, subject
    )
    topic_states = load_topic_state_map(supabase, user_id, exam_code, subject)
    pending_conflict = (
        _pending_conflict(supabase, user_id, exam_code, subject)
        if subject_state.pending_conflict_count > 0
        else None
    )
    observations = _observations_from_items(supabase, items)
    strategy_config = session.get("strategy_config") or {}
    previous_was_challenge = bool(items and items[-1].get("is_challenge"))
    previous_was_verification = bool(
        items
        and str(items[-1].get("target_zone") or "") == TargetZone.VERIFY.value
        and not _verification_slot_expired(items[-1])
    )
    wrong_streak = 0
    for observation in reversed(observations):
        if observation.is_correct:
            break
        wrong_streak += 1

    conflict_in_scope = _conflict_is_in_session_scope(pending_conflict, session)
    verification_allowed = bool(
        pending_conflict
        and conflict_in_scope
        and wrong_streak < 3
        and not _defer_verification_slot
    )

    def build_plan(*, allow_verification: bool):
        return plan_next_target(
            position=next_position,
            subject_state=subject_state,
            observations=observations,
            question_count=int(session["requested_question_count"]),
            preference=str(session.get("user_preference") or "standard"),
            accepted_challenge=bool(strategy_config.get("accepted_challenge")),
            previous_was_challenge=previous_was_challenge,
            pending_verification_count=int((pending_conflict or {}).get("verification_count") or 0),
            previous_was_verification=previous_was_verification,
            pending_verification=allow_verification,
        )

    plan = build_plan(allow_verification=verification_allowed)
    fallback_reasons: list[str] = []

    def add_fallback(reason: str) -> None:
        if reason and reason not in fallback_reasons:
            fallback_reasons.append(reason)

    if pending_conflict and not conflict_in_scope:
        add_fallback("verification_deferred_out_of_scope")
    elif pending_conflict and wrong_streak >= 3:
        add_fallback("verification_deferred_three_wrong_protection")
    elif pending_conflict and _defer_verification_slot:
        add_fallback("verification_deferred_slot_claimed")

    questions = list(session.get("_prefetched_candidate_questions") or [])
    if not questions:
        questions = _fetch_candidate_questions(supabase, session)
    calibrations = dict(session.get("_prefetched_calibrations") or {})
    if not calibrations:
        # Keep the shared calibration snapshot aligned with the shared base
        # question snapshot. A cap-exempt, session-specific D4 witness is added
        # below from its single-row authoritative read; including that ID in the
        # shared cache key would turn a normal cache hit into a 3,000-row reload
        # whenever two users need different witnesses.
        calibrations = _load_candidate_calibration_map(
            supabase,
            session,
            [str(question.get("id") or "") for question in questions],
        )
    witness_calibrations: dict[str, dict] = {}
    configured_witness_id = str(
        strategy_config.get(INITIAL_DIAGNOSTIC_D4_KEY) or ""
    )
    used_question_ids = {
        str(item.get("question_id") or "") for item in items
    }
    pooled_question_ids = {
        str(question.get("id") or "") for question in questions
    }
    if (
        configured_witness_id
        and configured_witness_id not in used_question_ids
        and configured_witness_id not in pooled_question_ids
        and int(plan.difficulty) >= 4
    ):
        witness = _load_initial_diagnostic_d4_witness(
            supabase,
            session=session,
            question_id=configured_witness_id,
        )
        if not witness:
            witness = _find_fresh_approved_diagnostic_d4(
                supabase,
                user_id=user_id,
                session=session,
            )
        if not witness:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "ADAPTIVE_DIAGNOSTIC_POOL_UNAVAILABLE",
                    "message": "当前专项尚未准备好审核通过的高难度诊断题",
                },
            )
        witness_question, witness_calibration = witness
        questions = _inject_candidate_witness(questions, witness_question)
        witness_id = str(witness_question.get("id") or "")
        if witness_id:
            witness_calibrations[witness_id] = witness_calibration
    question_ids = [str(question.get("id") or "") for question in questions]
    calibrations.update(witness_calibrations)
    needs_global_seen = plan.is_diagnostic or plan.zone is TargetZone.VERIFY
    has_prefetched_global_seen = (
        needs_global_seen and "_prefetched_ever_answered_ids" in session
    )
    history_snapshot = _load_candidate_history_snapshot(
        supabase,
        user_id=user_id,
        exam_code=exam_code,
        subject=subject,
        question_ids=question_ids,
        include_global_seen=needs_global_seen and not has_prefetched_global_seen,
    )
    recent_ids = set(history_snapshot["recent_question_ids"])
    due_review_values = dict(history_snapshot["due_review_values"])
    ever_answered_ids: set[str] = set()
    if needs_global_seen:
        ever_answered_ids = (
            set(session.get("_prefetched_ever_answered_ids") or set())
            if has_prefetched_global_seen
            else set(history_snapshot["ever_answered_question_ids"])
        )
    all_candidate_rows, _ = _build_candidates(
        questions=questions,
        calibrations=calibrations,
        topic_states=topic_states,
        session_items=items,
        recent_question_ids=recent_ids,
        due_review_values={},
    )
    candidate_rows = list(all_candidate_rows)

    verification_skill_matched = False
    if plan.zone is TargetZone.VERIFY and pending_conflict and verification_allowed:
        conflict_key = (
            str(pending_conflict.get("module") or ""),
            str(pending_conflict.get("submodule") or ""),
            str(pending_conflict.get("question_type") or "single_choice"),
        )
        conflict_question_ids = {
            str(pending_conflict.get("low_question_id") or ""),
            str(pending_conflict.get("high_question_id") or ""),
        }
        matching_rows = [
            pair
            for pair in candidate_rows
            if (
                pair[0].module,
                pair[0].submodule,
                pair[0].question_type,
            ) == conflict_key
            and pair[0].difficulty == plan.difficulty
            and pair[0].quality_weight >= 0.7
            and str(
                (calibrations.get(pair[0].question_id) or {}).get("quality_status")
                or ""
            ).upper()
            == "APPROVED"
            and pair[0].question_id not in conflict_question_ids
            and pair[0].question_id not in ever_answered_ids
        ]
        if matching_rows:
            candidate_rows = matching_rows
            verification_skill_matched = True
        else:
            # Never disguise another skill/difficulty (or a remembered item) as
            # conflict verification. Keep the conflict pending and issue a
            # normal in-scope training item instead.
            add_fallback("verification_deferred_pool_unavailable")
            plan = build_plan(allow_verification=False)
            candidate_rows = list(all_candidate_rows)
    elif pending_conflict and "verification_interleave" in plan.reason_codes:
        conflict_topic = (
            str(pending_conflict.get("module") or ""),
            str(pending_conflict.get("submodule") or ""),
        )
        non_conflict_rows = [
            pair
            for pair in candidate_rows
            if (pair[0].module, pair[0].submodule) != conflict_topic
        ]
        if non_conflict_rows:
            candidate_rows = non_conflict_rows
        else:
            add_fallback("verification_interleave_topic_relaxed")

    state_snapshot = session.get("state_snapshot") or {}
    initial_status = str(state_snapshot.get("diagnostic_status") or session.get("diagnostic_status") or "").upper()
    initial_reliable_count = int(state_snapshot.get("reliable_first_attempt_count") or 0)
    initial_warmup = initial_reliable_count < 8 or initial_status in {
        DiagnosticStatus.NEW.value,
        DiagnosticStatus.PROBING.value,
        DiagnosticStatus.VERIFYING.value,
    }
    if initial_warmup:
        # D4/D5 in the first calibration round must come from the explicitly
        # approved diagnostic pool. An arbitrary hard item is never promoted to
        # a diagnostic merely because the preferred pool is short.
        candidate_rows = [
            pair
            for pair in candidate_rows
            if pair[0].difficulty < 4
            or (
                pair[0].is_diagnostic_candidate
                and pair[0].quality_weight >= 0.7
            )
        ]

    effective_is_diagnostic = plan.is_diagnostic
    if plan.is_diagnostic:
        globally_fresh = [
            pair for pair in candidate_rows if pair[0].question_id not in ever_answered_ids
        ]
        if globally_fresh:
            candidate_rows = globally_fresh
        else:
            # The item may still be useful practice, but its globally repeated
            # response must not be represented as fresh diagnostic evidence.
            effective_is_diagnostic = False
            plan = replace(
                plan,
                zone=TargetZone.COVERAGE,
                is_diagnostic=False,
                is_challenge=False,
            )
            add_fallback("diagnostic_evidence_deferred_no_fresh_item")

    topic_switch_reason = None
    if wrong_streak >= 3 and observations and plan.zone is not TargetZone.VERIFY:
        previous_topic = (observations[-1].module, observations[-1].submodule)
        switched_topic = [
            pair
            for pair in candidate_rows
            if (pair[0].module, pair[0].submodule) != previous_topic
        ]
        if switched_topic:
            # Apply this before difficulty matching so another valid topic at a
            # nearby difficulty wins over repeating the frustrating topic.
            candidate_rows = switched_topic
            topic_switch_reason = "three_wrong_topic_switch"
        else:
            topic_switch_reason = "three_wrong_topic_switch_relaxed"
            add_fallback(topic_switch_reason)

    if plan.difficulty < 5:
        candidate_rows = [pair for pair in candidate_rows if pair[0].difficulty < 5]
    exact = [pair for pair in candidate_rows if pair[0].difficulty == plan.difficulty]
    eligible = exact
    if (
        effective_is_diagnostic
        and plan.zone is not TargetZone.VERIFY
        and plan.difficulty < 4
    ):
        diagnostic_exact = [
            pair
            for pair in exact
            if pair[0].is_diagnostic_candidate and pair[0].quality_weight >= 0.7
        ]
        if diagnostic_exact:
            eligible = diagnostic_exact
        elif exact:
            # An ordinary same-difficulty item is still useful practice, but it
            # is not a trusted diagnostic merely because the reviewed pool is
            # short. Persist and score it as coverage evidence so downstream
            # ability logic can distinguish the fallback unambiguously.
            downgrade_reason = "diagnostic_evidence_deferred_untrusted_pool"
            effective_is_diagnostic = False
            plan = replace(
                plan,
                zone=TargetZone.COVERAGE,
                reason_codes=(downgrade_reason, *plan.reason_codes),
                is_diagnostic=False,
                is_challenge=False,
            )
            add_fallback(downgrade_reason)
    if not eligible:
        if initial_warmup and plan.difficulty >= 4:
            for fallback_difficulty in range(plan.difficulty - 1, 0, -1):
                eligible = [
                    pair
                    for pair in candidate_rows
                    if pair[0].difficulty == fallback_difficulty
                ]
                if eligible:
                    if plan.difficulty == 5 and fallback_difficulty == 4:
                        add_fallback("d5_diagnostic_pool_unavailable_fallback_d4")
                    elif plan.difficulty == 4 and fallback_difficulty == 3:
                        add_fallback("d4_diagnostic_pool_unavailable_fallback_d3")
                    else:
                        add_fallback(
                            f"diagnostic_d{plan.difficulty}_fallback_d{fallback_difficulty}"
                        )
                    break
        elif plan.zone is not TargetZone.VERIFY:
            fallback_candidates = candidate_rows
            if any(
                reason in {"positive_finish", "challenge_recovery"}
                for reason in plan.reason_codes
            ):
                # A confidence-building finish and the item immediately after a
                # challenge are safety rails, not soft preferences.  If the
                # exact bucket is empty, never turn either slot into a harder
                # question merely because that is the numerically closest one.
                fallback_candidates = [
                    pair
                    for pair in fallback_candidates
                    if pair[0].difficulty <= plan.difficulty
                ]
            distances = sorted(
                {
                    abs(pair[0].difficulty - plan.difficulty)
                    for pair in fallback_candidates
                }
            )
            if distances:
                eligible = [
                    pair
                    for pair in fallback_candidates
                    if abs(pair[0].difficulty - plan.difficulty) == distances[0]
                ]
                add_fallback("difficulty_shortage")
    if not eligible:
        if any(
            reason in {"positive_finish", "challenge_recovery"}
            for reason in plan.reason_codes
        ):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "ADAPTIVE_SAFE_POOL_UNAVAILABLE",
                    "message": "当前专项暂时缺少合适的回稳题，请稍后重试",
                },
            )
        return None

    # Prefer questions not used in the recent scope window. Reliable diagnostic
    # and verification paths already applied the stronger all-time physical-ID
    # exclusion above.
    unseen = [pair for pair in eligible if pair[0].question_id not in recent_ids]
    if unseen:
        eligible = unseen
    else:
        add_fallback("recent_exposure_relaxed")

    if effective_is_diagnostic and plan.zone is not TargetZone.VERIFY:
        trusted_diagnostic = [
            pair
            for pair in eligible
            if pair[0].is_diagnostic_candidate and pair[0].quality_weight >= 0.7
        ]
        if trusted_diagnostic:
            eligible = trusted_diagnostic
        else:
            # The item remains useful practice, but it must not be persisted as
            # diagnostic evidence when the trusted pool is temporarily short.
            effective_is_diagnostic = False
            plan = replace(
                plan,
                zone=TargetZone.COVERAGE,
                is_diagnostic=False,
                is_challenge=False,
            )
            add_fallback("diagnostic_evidence_deferred_untrusted_pool")

    if due_review_values:
        eligible = [
            (replace(candidate, due_review_value=float(due_review_values.get(candidate.question_id, 0.0))), row)
            for candidate, row in eligible
        ]
    scored = [
        score_candidate(
            candidate,
            subject_theta=subject_state.theta,
            plan=plan,
            diagnostic_phase=effective_is_diagnostic or plan.zone is TargetZone.VERIFY,
            wrong_streak=wrong_streak,
            previous_was_challenge=previous_was_challenge,
        )
        for candidate, _ in eligible
    ]
    seed = f"{session['id']}:{next_position}:{subject_state.state_version}:{STRATEGY_VERSION}"
    selected = select_top_k_weighted(scored, seed=seed, top_k=5)
    question = next(row for candidate, row in eligible if candidate.question_id == selected.candidate.question_id)

    trusted_selection = effective_is_diagnostic or (
        plan.zone is TargetZone.VERIFY and verification_skill_matched
    )
    if trusted_selection and not _selected_trusted_candidate_is_current(
        supabase,
        session=session,
        question_id=selected.candidate.question_id,
        expected_difficulty=selected.candidate.difficulty,
        require_diagnostic_candidate=(
            effective_is_diagnostic and plan.zone is not TargetZone.VERIFY
        ),
    ):
        if _freshness_retry < 1:
            _invalidate_candidate_cache(session)
            refreshed_session = dict(session)
            for key in (
                "_prefetched_candidate_questions",
                "_prefetched_calibrations",
                "_prefetched_ever_answered_ids",
            ):
                refreshed_session.pop(key, None)
            return _select_and_insert_next(
                supabase,
                user_id,
                refreshed_session,
                _claim_retry=_claim_retry,
                _defer_verification_slot=_defer_verification_slot,
                _freshness_retry=_freshness_retry + 1,
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "ADAPTIVE_TRUSTED_POOL_CHANGED",
                "message": "题目审核状态刚刚更新，请重新匹配下一题",
                "retryable": True,
            },
        )
    reason_codes = list(plan.reason_codes)
    for fallback_reason in fallback_reasons:
        if fallback_reason not in reason_codes:
            reason_codes.append(fallback_reason)
    if topic_switch_reason and topic_switch_reason not in reason_codes:
        reason_codes.append(topic_switch_reason)

    payload = {
        "session_id": session["id"],
        "question_id": selected.candidate.question_id,
        "position": next_position,
        "item_status": "SELECTED",
        "selection_reason": reason_codes[0],
        "target_zone": plan.zone.value,
        "predicted_probability": selected.predicted_probability,
        "theta_before": subject_state.theta,
        "item_difficulty": (
            selected.candidate.empirical_difficulty
            if selected.candidate.empirical_difficulty is not None
            else difficulty_to_theta(selected.candidate.difficulty)
        ),
        "score_components": selected.score_components,
        "strategy_metadata": {
            "reason_codes": reason_codes,
            "strategy_version": STRATEGY_VERSION,
            "model_version": MODEL_VERSION,
            "seed": seed,
            "manual_difficulty": selected.candidate.difficulty,
            "quality_status": str(
                (calibrations.get(selected.candidate.question_id) or {}).get("quality_status")
                or "UNREVIEWED"
            ).upper(),
            "quality_weight": selected.candidate.quality_weight,
            "question_valid": selected.candidate.quality_weight > 0,
            "verification_skill_matched": verification_skill_matched,
            "verification_conflict_id": (
                str(pending_conflict.get("id"))
                if verification_skill_matched and pending_conflict
                else None
            ),
            "verification_expected_count": (
                int(pending_conflict.get("verification_count") or 0)
                if verification_skill_matched and pending_conflict
                else None
            ),
            "verification_expected_difficulty": (
                int(plan.difficulty) if verification_skill_matched else None
            ),
            "topic_switch_reason": topic_switch_reason,
        },
        "is_diagnostic": effective_is_diagnostic,
        "is_challenge": plan.is_challenge,
        "fallback_reason": fallback_reasons[0] if fallback_reasons else None,
    }
    claim_item = {
        key: payload[key]
        for key in (
            "selection_reason",
            "target_zone",
            "predicted_probability",
            "theta_before",
            "item_difficulty",
            "score_components",
            "strategy_metadata",
            "is_diagnostic",
            "is_challenge",
            "fallback_reason",
        )
    }
    try:
        response = call_supabase(
            lambda: supabase.rpc(
                "claim_next_adaptive_practice_item",
                {
                    "p_user_id": user_id,
                    "p_session_id": session["id"],
                    "p_question_id": selected.candidate.question_id,
                    "p_position": next_position,
                    "p_expected_subject_state_version": subject_state.state_version,
                    "p_item": claim_item,
                },
            ).execute(),
            operation_name="claim next adaptive practice item",
        )
    except Exception as exc:
        error_text = str(exc).lower()
        if is_missing_supabase_relation_error(exc):
            _raise_update_barrier(pending_count=1, migration_pending=True)
        if "adaptive_update_pending" in error_text:
            _raise_update_barrier(pending_count=1)
        candidate_changed = "adaptive_candidate_changed" in error_text or any(
            marker in error_text
            for marker in (
                "adaptive_question_not_found",
                "adaptive_question_not_active",
                "adaptive_session_item_scope_mismatch",
                "adaptive_session_item_outside_selected_scope",
            )
        ) or (
            trusted_selection
            and any(
                marker in error_text
                for marker in (
                    "adaptive_trusted_candidate_changed",
                    "adaptive_conflict_verification_scope_mismatch",
                )
            )
        )
        if candidate_changed:
            if _freshness_retry < 1:
                _invalidate_candidate_cache(session)
                refreshed_session = dict(session)
                for key in (
                    "_prefetched_candidate_questions",
                    "_prefetched_calibrations",
                    "_prefetched_ever_answered_ids",
                ):
                    refreshed_session.pop(key, None)
                return _select_and_insert_next(
                    supabase,
                    user_id,
                    refreshed_session,
                    _claim_retry=_claim_retry,
                    _defer_verification_slot=_defer_verification_slot,
                    _freshness_retry=_freshness_retry + 1,
                )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "ADAPTIVE_TRUSTED_POOL_CHANGED",
                    "message": "题目或校准状态刚刚更新，请重新匹配下一题",
                    "retryable": True,
                },
            ) from exc
        if "adaptive_conflict_verification_slot_claimed" in error_text:
            if not _defer_verification_slot:
                return _select_and_insert_next(
                    supabase,
                    user_id,
                    session,
                    _claim_retry=_claim_retry,
                    _defer_verification_slot=True,
                    _freshness_retry=_freshness_retry,
                )
        if "adaptive_session_not_active" in error_text:
            refreshed_session = _load_session(
                supabase,
                user_id,
                str(session["id"]),
            )
            session.update(refreshed_session)
            return None
        if "adaptive_next_position_out_of_range" in error_text:
            return None
        if "adaptive_previous_item_pending" in error_text:
            refreshed_items = _load_session_items(supabase, str(session["id"]))
            winner = next(
                (
                    item
                    for item in refreshed_items
                    if item.get("item_status") in {"SELECTED", "PRESENTED"}
                    and not item.get("answer_id")
                    and not _verification_slot_expired(item)
                ),
                None,
            )
            if winner:
                winner_question = winner.get("questions") or {}
                warm_submission_questions(
                    [winner_question],
                    practice_session_item_id=str(winner.get("id") or ""),
                    user_id=user_id,
                )
                return _item_view(winner, winner_question)
        retryable_claim_conflict = any(
            marker in error_text
            for marker in (
                "adaptive_state_conflict",
                "adaptive_next_position_conflict",
                "adaptive_conflict_verification_snapshot_mismatch",
                "adaptive_conflict_verification_difficulty_mismatch",
            )
        )
        if retryable_claim_conflict and _claim_retry < 1:
            return _select_and_insert_next(
                supabase,
                user_id,
                session,
                _claim_retry=_claim_retry + 1,
                _defer_verification_slot=_defer_verification_slot,
                _freshness_retry=_freshness_retry,
            )
        if retryable_claim_conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ADAPTIVE_NEXT_STATE_CHANGED",
                    "message": "能力状态刚刚发生变化，正在重新计算下一题",
                    "retryable": True,
                },
            ) from exc
        raise

    inserted = response.data
    if isinstance(inserted, list):
        inserted = inserted[0] if inserted else None
    if not isinstance(inserted, dict):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="个性化题目暂时未能保存")
    persisted_question_id = str(inserted.get("question_id") or "")
    snapshot = inserted.pop("question_snapshot", None)
    authoritative_question = (
        snapshot
        if isinstance(snapshot, dict)
        and str(snapshot.get("id") or "") == persisted_question_id
        else None
    )
    if persisted_question_id != selected.candidate.question_id:
        # Another idempotent caller can win the position with a different
        # candidate.  Return the database winner together with its own question,
        # never the losing caller's in-memory row.
        if authoritative_question:
            inserted["questions"] = authoritative_question
            warm_submission_questions(
                [authoritative_question],
                practice_session_item_id=str(inserted.get("id") or ""),
                user_id=user_id,
            )
            return _item_view(inserted, authoritative_question)
        refreshed_items = _load_session_items(supabase, str(session["id"]))
        winner = next(
            (
                item
                for item in refreshed_items
                if str(item.get("id") or "") == str(inserted.get("id") or "")
                or int(item.get("position") or 0) == next_position
            ),
            None,
        )
        if not winner:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="并发生成的个性化题目暂时未能读取",
            )
        winner_question = winner.get("questions") or {}
        warm_submission_questions(
            [winner_question],
            practice_session_item_id=str(winner.get("id") or ""),
            user_id=user_id,
        )
        return _item_view(winner, winner_question)
    selected_question = authoritative_question or question
    inserted["questions"] = selected_question
    warm_submission_questions(
        [selected_question],
        practice_session_item_id=str(inserted.get("id") or ""),
        user_id=user_id,
    )
    return _item_view(inserted, selected_question)


def _load_pending_adaptive_update_items(
    supabase,
    *,
    user_id: str,
    exam_code: str,
    subject: str,
    session_id: str | None = None,
) -> list[dict]:
    response = call_supabase(
        lambda: supabase.rpc(
            "get_pending_adaptive_update_items",
            {
                "p_user_id": user_id,
                "p_stats_exam_code": exam_code,
                "p_subject": subject,
                "p_session_id": session_id,
                "p_limit": PROGRESS_QUERY_BATCH_SIZE,
            },
        ).execute(),
        operation_name="load pending adaptive model updates",
    )
    rows = response.data or []
    normalized: list[dict] = []
    for row in rows:
        normalized.append(
            {
                "id": row.get("practice_session_item_id"),
                "session_id": row.get("session_id"),
                "question_id": row.get("question_id"),
                "position": row.get("item_position"),
                "answer_id": row.get("answer_id"),
                "answered_at": row.get("answered_at"),
                "answer": {
                    "id": row.get("answer_id"),
                    "stats_exam_code": row.get("answer_stats_exam_code"),
                    "is_correct": row.get("is_correct"),
                    "is_first_attempt": row.get("is_first_attempt"),
                    "used_time": row.get("used_time"),
                    "created_at": row.get("answer_created_at"),
                },
                "questions": {
                    "id": row.get("question_id"),
                    "exam_code": row.get("question_exam_code"),
                    "subject": row.get("question_subject"),
                    "module": row.get("module"),
                    "submodule": row.get("submodule"),
                    "question_type": row.get("question_type"),
                    "difficulty": row.get("difficulty"),
                    "estimated_time_sec": row.get("estimated_time_sec"),
                    "source_type": row.get("source_type"),
                },
            }
        )
    if session_id is not None:
        normalized.sort(
            key=lambda item: (
                int(item.get("position") or 0),
                str(item.get("id") or ""),
            )
        )
    else:
        # The database already returns this order, but repeat the deterministic
        # ordering at the application boundary so mocked clients and rolling
        # PostgREST deployments cannot let a newer answer overtake an older one.
        normalized.sort(
            key=lambda item: (
                str(item.get("answered_at") or ""),
                str(item.get("session_id") or ""),
                int(item.get("position") or 0),
                str(item.get("id") or ""),
            )
        )
    return normalized


def _raise_update_barrier(*, pending_count: int, migration_pending: bool = False) -> None:
    if migration_pending:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "ADAPTIVE_MIGRATION_PENDING",
                "message": "个性化出题数据迁移尚未启用",
            },
        )
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "code": "ADAPTIVE_UPDATE_PENDING",
            "message": "上一题能力状态仍在同步，请稍后重试",
            "pending_count": max(1, int(pending_count)),
        },
    )


def reconcile_pending_adaptive_updates(
    supabase,
    *,
    user_id: str,
    exam_code: str,
    subject: str,
    session_id: str | None = None,
    prefetched_session_items: list[dict] | None = None,
    prefetched_pending_items: list[dict] | None = None,
    prefetched_subject_state: AbilityState | None = None,
    prefetched_topic_state_map: dict[tuple[str, str], AbilityState] | None = None,
    prefetched_pending_conflict: object = _UNSET,
) -> int:
    """Apply every durable-but-unmodeled answer before recommendation advances.

    New-session callers run this before legacy bootstrap.  Consequently an
    answer already bound to an adaptive item is never replayed once by bootstrap
    and then applied a second time by the model-update RPC.
    """

    exam_code, subject = validate_scope(exam_code, subject)
    applied_count = 0
    processed_answer_ids: set[str] = set()
    prefetched_by_id = {
        str(item.get("id") or ""): item
        for item in (prefetched_session_items or [])
        if item.get("id")
    }
    cached_subject_state: AbilityState | None = prefetched_subject_state
    cached_topic_state_map = (
        dict(prefetched_topic_state_map)
        if prefetched_topic_state_map is not None
        else None
    )
    cached_pending_conflict: object = prefetched_pending_conflict
    if prefetched_by_id:
        # A comprehensive sheet can contain 30 answers. Read each scoped state
        # once and advance the immutable state objects from successful RPC
        # results instead of repeating the same subject/topic reads per item.
        if cached_subject_state is None:
            cached_subject_state = load_subject_state(
                supabase, user_id, exam_code, subject
            )
        if cached_topic_state_map is None:
            cached_topic_state_map = load_topic_state_map(
                supabase, user_id, exam_code, subject
            )
        if cached_pending_conflict is _UNSET:
            cached_pending_conflict = (
                _pending_conflict(supabase, user_id, exam_code, subject)
                if cached_subject_state.pending_conflict_count > 0
                else None
            )
    pending_batch = prefetched_pending_items
    while True:
        if pending_batch is not None:
            pending_items = pending_batch
            pending_batch = None
        else:
            try:
                pending_items = _load_pending_adaptive_update_items(
                    supabase,
                    user_id=user_id,
                    exam_code=exam_code,
                    subject=subject,
                    session_id=session_id,
                )
            except Exception as exc:
                if isinstance(exc, HTTPException):
                    raise
                if is_missing_supabase_relation_error(exc):
                    _raise_update_barrier(pending_count=1, migration_pending=True)
                logger.warning("Adaptive update barrier read failed: %s", type(exc).__name__)
                _raise_update_barrier(pending_count=1)

        if not pending_items:
            return applied_count
        for item in pending_items:
            answer_id = str(item.get("answer_id") or "")
            answer = item.get("answer") or {}
            question = item.get("questions") or {}
            if not answer_id or answer_id in processed_answer_ids or not answer or not question:
                _raise_update_barrier(pending_count=len(pending_items))
            prefetched_item = prefetched_by_id.get(str(item.get("id") or ""))
            prefetched_items_for_session = None
            if prefetched_item is not None:
                # Merge database-authored answer facts from the pending-update
                # RPC into the richer, already loaded comprehensive item. The
                # latter carries frozen strategy metadata and the private
                # question snapshot needed by the model calculation.
                prefetched_item["answer_id"] = answer_id
                prefetched_item["answer"] = dict(answer)
                prefetched_item["answered_at"] = (
                    item.get("answered_at") or answer.get("created_at")
                )
                current_session_id = str(item.get("session_id") or "")
                prefetched_items_for_session = [
                    candidate
                    for candidate in prefetched_by_id.values()
                    if str(candidate.get("session_id") or "") == current_session_id
                ]
            try:
                apply_kwargs = {
                    "user_id": user_id,
                    "question": question,
                    "persisted": {
                        "submission_id": answer_id,
                        "stats_exam_code": answer.get("stats_exam_code") or exam_code,
                        "is_first_attempt": bool(answer.get("is_first_attempt")),
                        "is_correct": bool(answer.get("is_correct")),
                        "created_at": answer.get("created_at"),
                    },
                    "used_time": max(0, int(answer.get("used_time") or 0)),
                    "practice_session_item_id": str(item.get("id") or ""),
                }
                if prefetched_item is not None:
                    apply_kwargs.update(
                        {
                            "_prefetched_item": prefetched_item,
                            "_prefetched_session_items": prefetched_items_for_session,
                            "_prefetched_subject_state": cached_subject_state,
                            "_prefetched_topic_state_map": cached_topic_state_map,
                            "_prefetched_pending_conflict": cached_pending_conflict,
                            "_include_planning_context": True,
                        }
                    )
                result = apply_adaptive_answer_update(supabase, **apply_kwargs)
            except HTTPException:
                raise
            except Exception as exc:
                logger.warning(
                    "Adaptive update barrier compensation failed (answer_id=%s error_type=%s)",
                    answer_id,
                    type(exc).__name__,
                )
                _raise_update_barrier(pending_count=len(pending_items))
            if not result or not result.get("adaptive_updated"):
                _raise_update_barrier(
                    pending_count=len(pending_items),
                    migration_pending=bool((result or {}).get("migration_pending")),
                )
            planning_context = (result or {}).get("_planning_context")
            if isinstance(planning_context, dict) and planning_context.get("cache_valid"):
                cached_subject_state = planning_context.get("subject_after")
                cached_topic_state_map = planning_context.get("topic_state_map_after")
                cached_pending_conflict = planning_context.get("pending_conflict_after")
            elif prefetched_item is not None:
                # A compatibility mock or an unexpected database conflict may
                # not provide a safe successor snapshot. Force the next item to
                # reload rather than advancing from an assumed state.
                cached_subject_state = None
                cached_topic_state_map = None
                cached_pending_conflict = _UNSET
            elif prefetched_by_id:
                # An older pending answer from another session advanced this
                # same scope outside the prefetched comprehensive sheet.
                cached_subject_state = None
                cached_topic_state_map = None
                cached_pending_conflict = _UNSET
            processed_answer_ids.add(answer_id)
            applied_count += 1
        if len(pending_items) < PROGRESS_QUERY_BATCH_SIZE:
            return applied_count


def _prepare_initial_diagnostic_pool(
    supabase,
    *,
    user_id: str,
    session: dict,
) -> None:
    """Fail closed before creating a cold-start session with no trusted D4."""

    approved_d4 = _find_fresh_approved_diagnostic_d4(
        supabase,
        user_id=user_id,
        session=session,
    )
    if not approved_d4:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "ADAPTIVE_DIAGNOSTIC_POOL_UNAVAILABLE",
                "message": "当前专项尚未准备好审核通过的高难度诊断题",
            },
        )

    questions = _fetch_candidate_questions(supabase, session)
    calibrations = _load_candidate_calibration_map(
        supabase,
        session,
        [str(question.get("id") or "") for question in questions],
    )
    approved_d4_question, approved_d4_calibration = approved_d4
    approved_d4_id = str(approved_d4_question.get("id") or "")
    if approved_d4_id:
        # Make the readiness witness available to the bounded ranking pool even
        # when it lives after MAX_CANDIDATE_ROWS in creation order.
        questions = _inject_candidate_witness(questions, approved_d4_question)
    question_ids = [str(question.get("id") or "") for question in questions]
    if approved_d4_id:
        calibrations[approved_d4_id] = approved_d4_calibration
    ever_answered_ids = _load_ever_answered_question_ids(
        supabase,
        user_id,
        str(session["subject"]),
        question_ids,
    )
    # The dedicated D4 readiness witness is selected using this user's answer
    # history. Keep the expanded bundle request-local: writing it back into the
    # shared bank cache would leak user-specific pool membership into other
    # sessions and would renew the source snapshot's TTL on every cold start.
    strategy_config = dict(session.get("strategy_config") or {})
    strategy_config[INITIAL_DIAGNOSTIC_D4_KEY] = approved_d4_id
    session["strategy_config"] = strategy_config
    session["_prefetched_candidate_questions"] = questions
    session["_prefetched_calibrations"] = calibrations
    session["_prefetched_ever_answered_ids"] = ever_answered_ids


def _comprehensive_items_from_rows(
    rows: list[dict],
    *,
    user_id: str,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda value: int(value.get("position") or 0)):
        question = row.get("question_snapshot") or row.get("questions") or {}
        if (
            not isinstance(question, dict)
            or not question.get("id")
            or str(question.get("id")) != str(row.get("question_id") or "")
        ):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="综合刷题题目版本暂时未能读取",
            )
        # Comprehensive feedback is embargoed until the whole round is handed
        # in, so unlike special practice these snapshots are intentionally not
        # placed in the single-answer grading cache.
        items.append(_item_view(row, question))
    return items


def _plan_comprehensive_claims(
    supabase,
    *,
    user_id: str,
    session: dict,
    subject_state: AbilityState,
) -> list[dict[str, Any]]:
    question_count = int(session["requested_question_count"])
    strategy_config = session.get("strategy_config") or {}
    plans = plan_comprehensive_targets(
        subject_state=subject_state,
        question_count=question_count,
        preference=str(session.get("user_preference") or "standard"),
        accepted_challenge=bool(strategy_config.get("accepted_challenge")),
    )
    has_prefetched_candidate_bundle = "_prefetched_candidate_questions" in session
    questions = list(session.get("_prefetched_candidate_questions") or [])
    if not questions:
        questions = _fetch_candidate_questions(supabase, session)
    calibrations = dict(session.get("_prefetched_calibrations") or {})
    if not calibrations:
        calibrations = _load_candidate_calibration_map(
            supabase,
            session,
            [str(question.get("id") or "") for question in questions],
        )
    configured_witness_id = str(
        strategy_config.get(INITIAL_DIAGNOSTIC_D4_KEY) or ""
    )
    should_restore_persisted_witness = bool(
        not has_prefetched_candidate_bundle
        and configured_witness_id
        and any(
            plan.is_diagnostic and int(plan.difficulty) == 4 for plan in plans
        )
    )
    restored_witness_id = ""
    if should_restore_persisted_witness:
        # A create request can be interrupted after the session row is inserted
        # but before its fixed comprehensive claims are persisted.  The
        # cap-exempt D4 readiness witness then survives only as an ID in
        # strategy_config, so rebuild that request-local bundle from trusted
        # authoritative rows instead of silently degrading the D4 diagnostic.
        witness = _load_initial_diagnostic_d4_witness(
            supabase,
            session=session,
            question_id=configured_witness_id,
        )
        if witness:
            witness_question, witness_calibration = witness
            questions = _inject_candidate_witness(questions, witness_question)
            restored_witness_id = str(witness_question.get("id") or "")
            if restored_witness_id:
                calibrations[restored_witness_id] = witness_calibration
    exam_code, subject = validate_scope(session["stats_exam_code"], session["subject"])
    question_ids = [str(question.get("id") or "") for question in questions]
    needs_global_seen = any(plan.is_diagnostic for plan in plans)
    has_prefetched_global_seen = (
        needs_global_seen and "_prefetched_ever_answered_ids" in session
    )
    history_snapshot = _load_candidate_history_snapshot(
        supabase,
        user_id=user_id,
        exam_code=exam_code,
        subject=subject,
        question_ids=question_ids,
        include_global_seen=needs_global_seen and not has_prefetched_global_seen,
    )
    recent_ids = set(history_snapshot["recent_question_ids"])
    due_review_values = dict(history_snapshot["due_review_values"])
    ever_answered_ids: set[str] = set()
    if needs_global_seen:
        ever_answered_ids = (
            set(session.get("_prefetched_ever_answered_ids") or set())
            if has_prefetched_global_seen
            else set(history_snapshot["ever_answered_question_ids"])
        )
    if should_restore_persisted_witness and (
        not restored_witness_id or restored_witness_id in ever_answered_ids
    ):
        replacement = _find_fresh_approved_diagnostic_d4(
            supabase,
            user_id=user_id,
            session=session,
        )
        if not replacement:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "ADAPTIVE_DIAGNOSTIC_POOL_UNAVAILABLE",
                    "message": "当前专项尚未准备好审核通过的高难度诊断题",
                },
            )
        witness_question, witness_calibration = replacement
        questions = _inject_candidate_witness(questions, witness_question)
        replacement_id = str(witness_question.get("id") or "")
        if replacement_id:
            calibrations[replacement_id] = witness_calibration
        question_ids = [str(question.get("id") or "") for question in questions]
    topic_states = load_topic_state_map(supabase, user_id, exam_code, subject)
    planned_items: list[dict] = []
    claims: list[dict[str, Any]] = []

    for position, plan in enumerate(plans, start=1):
        candidate_rows, _ = _build_candidates(
            questions=questions,
            calibrations=calibrations,
            topic_states=topic_states,
            session_items=planned_items,
            recent_question_ids=recent_ids,
            due_review_values=due_review_values,
        )
        if plan.difficulty < 5:
            candidate_rows = [
                pair for pair in candidate_rows if pair[0].difficulty < 5
            ]
        fallback_reasons: list[str] = []
        effective_is_diagnostic = plan.is_diagnostic
        eligible = [pair for pair in candidate_rows if pair[0].difficulty == plan.difficulty]
        if plan.is_diagnostic:
            trusted = [
                pair
                for pair in eligible
                if pair[0].is_diagnostic_candidate
                and pair[0].quality_weight >= 0.7
                and pair[0].question_id not in ever_answered_ids
            ]
            if trusted:
                eligible = trusted
            else:
                effective_is_diagnostic = False
                fallback_reasons.append("comprehensive_diagnostic_pool_shortage")
        if not eligible:
            fallback_candidates = list(candidate_rows)
            if "positive_finish" in plan.reason_codes:
                fallback_candidates = [
                    pair
                    for pair in fallback_candidates
                    if pair[0].difficulty <= plan.difficulty
                ]
            distances = sorted(
                {
                    abs(pair[0].difficulty - plan.difficulty)
                    for pair in fallback_candidates
                }
            )
            if distances:
                eligible = [
                    pair
                    for pair in fallback_candidates
                    if abs(pair[0].difficulty - plan.difficulty) == distances[0]
                ]
                fallback_reasons.append("difficulty_shortage")
        if not eligible:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "ADAPTIVE_COMPREHENSIVE_POOL_UNAVAILABLE",
                    "message": "当前学科暂时缺少足够的综合刷题题目",
                },
            )

        unseen = [pair for pair in eligible if pair[0].question_id not in recent_ids]
        if unseen:
            eligible = unseen
        else:
            fallback_reasons.append("recent_exposure_relaxed")
        scored = [
            score_candidate(
                candidate,
                subject_theta=subject_state.theta,
                plan=replace(plan, is_diagnostic=effective_is_diagnostic),
                diagnostic_phase=effective_is_diagnostic,
            )
            for candidate, _ in eligible
        ]
        seed = (
            f"{session['id']}:comprehensive:{position}:"
            f"{subject_state.state_version}:{STRATEGY_VERSION}"
        )
        selected = select_top_k_weighted(scored, seed=seed, top_k=5)
        question = next(
            row
            for candidate, row in eligible
            if candidate.question_id == selected.candidate.question_id
        )
        reason_codes = list(plan.reason_codes)
        for reason in fallback_reasons:
            if reason not in reason_codes:
                reason_codes.append(reason)
        item_payload = {
            "selection_reason": reason_codes[0],
            "target_zone": plan.zone.value,
            "predicted_probability": selected.predicted_probability,
            "theta_before": subject_state.theta,
            "item_difficulty": (
                selected.candidate.empirical_difficulty
                if selected.candidate.empirical_difficulty is not None
                else difficulty_to_theta(selected.candidate.difficulty)
            ),
            "score_components": selected.score_components,
            "strategy_metadata": {
                "reason_codes": reason_codes,
                "strategy_version": STRATEGY_VERSION,
                "model_version": MODEL_VERSION,
                "seed": seed,
                "manual_difficulty": selected.candidate.difficulty,
                "quality_status": str(
                    (calibrations.get(selected.candidate.question_id) or {}).get("quality_status")
                    or "UNREVIEWED"
                ).upper(),
                "quality_weight": selected.candidate.quality_weight,
                "question_valid": selected.candidate.quality_weight > 0,
                "round_policy": "fixed_comprehensive_v1",
            },
            "is_diagnostic": effective_is_diagnostic,
            "is_challenge": plan.is_challenge,
            "fallback_reason": fallback_reasons[0] if fallback_reasons else None,
        }
        claims.append(
            {
                "question_id": selected.candidate.question_id,
                "position": position,
                "item": item_payload,
            }
        )
        planned_items.append(
            {
                "question_id": selected.candidate.question_id,
                "position": position,
                "target_zone": plan.zone.value,
                "is_challenge": plan.is_challenge,
                "questions": question,
            }
        )
    return claims


def _get_or_create_comprehensive_items(
    supabase,
    *,
    user_id: str,
    session: dict,
    subject_state: AbilityState,
    _freshness_retry: int = 0,
) -> list[dict[str, Any]]:
    existing = _load_session_items(supabase, str(session["id"]))
    expected_count = int(session["requested_question_count"])
    if existing:
        if len(existing) != expected_count:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ADAPTIVE_COMPREHENSIVE_ROUND_INCOMPLETE",
                    "message": "综合刷题固定题单尚未完整生成，请重试",
                },
            )
        return _comprehensive_items_from_rows(existing, user_id=user_id)

    claims = _plan_comprehensive_claims(
        supabase,
        user_id=user_id,
        session=session,
        subject_state=subject_state,
    )
    try:
        response = call_supabase(
            lambda: supabase.rpc(
                "claim_adaptive_comprehensive_practice_items",
                {
                    "p_user_id": user_id,
                    "p_session_id": session["id"],
                    "p_expected_subject_state_version": subject_state.state_version,
                    "p_items": claims,
                },
            ).execute(),
            operation_name="claim fixed comprehensive practice items",
        )
    except Exception as exc:
        error_text = str(exc).lower()
        if is_missing_supabase_relation_error(exc):
            _raise_update_barrier(pending_count=1, migration_pending=True)
        if "adaptive_update_pending" in error_text:
            _raise_update_barrier(pending_count=1)
        candidate_changed = any(
            marker in error_text
            for marker in (
                "adaptive_candidate_changed",
                "adaptive_trusted_candidate_changed",
                "adaptive_question_not_found",
                "adaptive_question_not_active",
                "adaptive_session_item_scope_mismatch",
                "adaptive_session_item_outside_selected_scope",
                "adaptive_comprehensive_difficulty_out_of_range",
            )
        )
        if candidate_changed:
            if _freshness_retry < 1:
                _invalidate_candidate_cache(session)
                refreshed_session = dict(session)
                for key in (
                    "_prefetched_candidate_questions",
                    "_prefetched_calibrations",
                    "_prefetched_ever_answered_ids",
                ):
                    refreshed_session.pop(key, None)
                return _get_or_create_comprehensive_items(
                    supabase,
                    user_id=user_id,
                    session=refreshed_session,
                    subject_state=subject_state,
                    _freshness_retry=_freshness_retry + 1,
                )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "ADAPTIVE_COMPREHENSIVE_POOL_CHANGED",
                    "message": "题目或校准状态刚刚更新，请重新生成综合题单",
                    "retryable": True,
                },
            ) from exc
        if "adaptive_state_conflict" in error_text:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ADAPTIVE_NEXT_STATE_CHANGED",
                    "message": "能力状态刚刚发生变化，请重新生成综合题单",
                    "retryable": True,
                },
            ) from exc
        raise
    rows = response.data or []
    if isinstance(rows, dict):
        rows = rows.get("items") or []
    if not isinstance(rows, list) or len(rows) != expected_count:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="综合刷题固定题单保存失败",
        )
    return _comprehensive_items_from_rows(rows, user_id=user_id)


def _normalized_scope_filter(scopes: list[dict]) -> list[tuple[str, str]]:
    return list(_normalized_scope_pairs(scopes))


def _assert_idempotent_session_matches(
    existing: dict,
    *,
    payload: CreateAdaptivePracticeSessionRequest,
    exam_code: str,
    subject: str,
) -> None:
    requested_scopes = [scope.model_dump(mode="json") for scope in payload.scopes]
    snapshot = existing.get("state_snapshot") or {}
    snapshot_status = str(snapshot.get("diagnostic_status") or existing.get("diagnostic_status") or "").upper()
    snapshot_reliable = int(snapshot.get("reliable_first_attempt_count") or 0)
    expected_count = payload.question_count
    if (
        snapshot_reliable < 8
        or snapshot_status
        in {
            DiagnosticStatus.NEW.value,
            DiagnosticStatus.PROBING.value,
            DiagnosticStatus.VERIFYING.value,
        }
    ):
        expected_count = 8
    strategy_config = existing.get("strategy_config") or {}
    matches = (
        str(existing.get("stats_exam_code") or "") == exam_code
        and str(existing.get("subject") or "") == subject
        and str(existing.get("mode") or "") == payload.practice_mode
        and _normalized_scope_filter(list(existing.get("scope_filter") or []))
        == _normalized_scope_filter(requested_scopes)
        and int(existing.get("requested_question_count") or 0) == int(expected_count)
        and str(existing.get("user_preference") or "standard") == payload.preference
        and bool(strategy_config.get("accepted_challenge")) == bool(payload.accepted_challenge)
    )
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "ADAPTIVE_SESSION_ID_CONFLICT",
                "message": "练习会话标识已用于不同的练习参数",
            },
        )


def create_adaptive_session(
    supabase,
    *,
    user_id: str,
    payload: CreateAdaptivePracticeSessionRequest,
    allow_new_session: bool = True,
) -> dict[str, Any]:
    exam_code, subject = validate_scope(payload.exam_code, payload.subject)
    existing = None
    if payload.client_session_id:
        try:
            existing = _query_one(
                supabase.table("practice_sessions")
                .select("*")
                .eq("user_id", user_id)
                .eq("client_session_id", payload.client_session_id),
                operation_name="find idempotent adaptive session",
            )
        except Exception as exc:
            if not allow_new_session:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="个性化出题正在灰度开放",
                ) from exc
            raise
        if existing:
            _assert_idempotent_session_matches(
                existing,
                payload=payload,
                exam_code=exam_code,
                subject=subject,
            )
    if existing is None and not allow_new_session:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="个性化出题正在灰度开放",
        )

    reconcile_pending_adaptive_updates(
        supabase,
        user_id=user_id,
        exam_code=exam_code,
        subject=subject,
    )
    subject_state, bootstrap_metadata = bootstrap_subject_state_if_needed(
        supabase,
        user_id=user_id,
        exam_code=exam_code,
        subject=subject,
    )
    requested_count = payload.question_count
    if (
        subject_state.reliable_first_attempt_count < 8
        or subject_state.diagnostic_status in {
            DiagnosticStatus.NEW,
            DiagnosticStatus.PROBING,
            DiagnosticStatus.VERIFYING,
        }
    ):
        requested_count = 8

    if existing:
        comprehensive_items = []
        next_item = None
        if existing.get("status") == "ACTIVE":
            if payload.practice_mode == "comprehensive":
                comprehensive_items = _get_or_create_comprehensive_items(
                    supabase,
                    user_id=user_id,
                    session=existing,
                    subject_state=subject_state,
                )
            else:
                next_item = _select_and_insert_next(
                    supabase,
                    user_id,
                    existing,
                    _subject_state=subject_state,
                )
        return {
            "session": _session_view(existing),
            "state": serialize_state(subject_state),
            "next_item": next_item,
            "items": comprehensive_items,
        }

    scopes = [scope.model_dump(mode="json") for scope in payload.scopes]
    first_scope = scopes[0] if scopes else {}
    row = {
        "user_id": user_id,
        "client_session_id": payload.client_session_id,
        "stats_exam_code": exam_code,
        "subject": subject,
        "mode": payload.practice_mode,
        "module": first_scope.get("module") if len(scopes) == 1 else None,
        "submodule": first_scope.get("submodule") if len(scopes) == 1 else None,
        "scope_filter": scopes,
        "user_preference": payload.preference,
        "status": "ACTIVE",
        "diagnostic_status": subject_state.diagnostic_status.value,
        "requested_question_count": requested_count,
        "strategy_version": STRATEGY_VERSION,
        "model_version": MODEL_VERSION,
        "experiment_key": "adaptive-practice-v1",
        "experiment_group": "v1",
        "state_snapshot": {**serialize_state(subject_state), **bootstrap_metadata},
        "strategy_config": {
            "accepted_challenge": payload.accepted_challenge,
            "bootstrap": bootstrap_metadata,
        },
    }
    preflight_session = dict(row)
    if (payload.practice_mode == "special" or requested_count >= 4) and (
        subject_state.reliable_first_attempt_count < 8
        or subject_state.diagnostic_status in {
            DiagnosticStatus.NEW,
            DiagnosticStatus.PROBING,
            DiagnosticStatus.VERIFYING,
        }
    ):
        _prepare_initial_diagnostic_pool(
            supabase,
            user_id=user_id,
            session=preflight_session,
        )
        row["strategy_config"] = dict(
            preflight_session.get("strategy_config") or {}
        )
    try:
        response = call_supabase(
            lambda: supabase.table("practice_sessions").insert(row).execute(),
            operation_name="create adaptive practice session",
        )
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="个性化出题数据迁移尚未启用",
            ) from exc
        if payload.client_session_id and _is_duplicate_key_error(exc):
            existing = _query_one(
                supabase.table("practice_sessions")
                .select("*")
                .eq("user_id", user_id)
                .eq("client_session_id", payload.client_session_id),
                operation_name="recover concurrently created adaptive session",
            )
            if existing:
                _assert_idempotent_session_matches(
                    existing,
                    payload=payload,
                    exam_code=exam_code,
                    subject=subject,
                )
                recovered_state = load_subject_state(
                    supabase, user_id, exam_code, subject
                )
                comprehensive_items = []
                next_item = None
                if existing.get("status") == "ACTIVE":
                    if payload.practice_mode == "comprehensive":
                        comprehensive_items = _get_or_create_comprehensive_items(
                            supabase,
                            user_id=user_id,
                            session=existing,
                            subject_state=recovered_state,
                        )
                    else:
                        next_item = _select_and_insert_next(
                            supabase,
                            user_id,
                            existing,
                            _subject_state=recovered_state,
                        )
                return {
                    "session": _session_view(existing),
                    "state": serialize_state(recovered_state),
                    "next_item": next_item,
                    "items": comprehensive_items,
                }
        raise
    session = (response.data or [None])[0]
    if not session:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="个性化练习会话创建失败")
    for key in (
        "_prefetched_candidate_questions",
        "_prefetched_calibrations",
        "_prefetched_ever_answered_ids",
    ):
        if key in preflight_session:
            session[key] = preflight_session[key]
    comprehensive_items = []
    next_item = None
    if payload.practice_mode == "comprehensive":
        comprehensive_items = _get_or_create_comprehensive_items(
            supabase,
            user_id=user_id,
            session=session,
            subject_state=subject_state,
        )
    else:
        next_item = _select_and_insert_next(
            supabase,
            user_id,
            session,
            _subject_state=subject_state,
        )
    return {
        "session": _session_view(session),
        "state": serialize_state(subject_state),
        "next_item": next_item,
        "items": comprehensive_items,
    }


def get_next_adaptive_item(supabase, *, user_id: str, session_id: str) -> dict[str, Any]:
    session = _load_session(supabase, user_id, session_id)
    if str(session.get("mode") or "") == "comprehensive":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "ADAPTIVE_PRACTICE_MODE_MISMATCH",
                "message": "综合刷题使用创建时返回的固定题单，不逐题领取下一题",
            },
        )
    reconcile_pending_adaptive_updates(
        supabase,
        user_id=user_id,
        exam_code=str(session["stats_exam_code"]),
        subject=str(session["subject"]),
    )
    subject_state = load_subject_state(
        supabase,
        user_id,
        str(session["stats_exam_code"]),
        str(session["subject"]),
    )
    if session.get("status") != "ACTIVE":
        return {
            "session": _session_view(session),
            "state": serialize_state(subject_state),
            "next_item": None,
            "finished": True,
        }
    next_item = _select_and_insert_next(
        supabase,
        user_id,
        session,
        _subject_state=subject_state,
    )
    finished = next_item is None
    return {
        "session": _session_view(session),
        "state": serialize_state(subject_state),
        "next_item": next_item,
        "finished": finished,
    }


def record_item_event(
    supabase,
    *,
    user_id: str,
    session_id: str,
    item_id: str,
    event_type: str,
) -> dict[str, Any]:
    try:
        response = call_supabase(
            lambda: supabase.rpc(
                "record_practice_session_item_event",
                {
                    "p_user_id": user_id,
                    "p_session_id": session_id,
                    "p_session_item_id": item_id,
                    "p_event_type": event_type,
                },
            ).execute(),
            operation_name="record adaptive item event",
        )
    except Exception as exc:
        error_text = str(exc).lower()
        if "adaptive_comprehensive_submission_in_progress" in error_text:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ADAPTIVE_COMPREHENSIVE_SUBMISSION_IN_PROGRESS",
                    "message": "综合刷题交卷正在结算，请继续重试原交卷请求",
                },
            ) from exc
        if "adaptive_comprehensive_batch_required" in error_text:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ADAPTIVE_COMPREHENSIVE_BATCH_REQUIRED",
                    "message": "综合刷题跳过状态只随整轮交卷清单提交",
                },
            ) from exc
        raise
    data = response.data
    if isinstance(data, list):
        data = data[0] if data else None
    if not isinstance(data, dict):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="练习事件保存失败")
    return data


def complete_session(
    supabase,
    *,
    user_id: str,
    session_id: str,
    reason: str,
) -> dict[str, Any]:
    session = _load_session(supabase, user_id, session_id)
    if str(session.get("mode") or "") == "comprehensive":
        submission = (session.get("strategy_config") or {}).get(
            "comprehensive_submission"
        )
        submission_phase = _comprehensive_submission_phase(submission)
        session_status = str(session.get("status") or "ACTIVE").upper()

        # A completed batch owns the terminal session transition.  Replaying
        # the legacy completion endpoint must not overwrite that outcome or
        # return a newer subject state after subsequent sessions have run.
        if submission_phase == "COMPLETED" and session_status == "COMPLETED":
            completion_state = _completion_state_view(
                submission.get("completion_state") if isinstance(submission, dict) else None
            )
            if completion_state is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "ADAPTIVE_COMPREHENSIVE_SUBMISSION_STATE_INVALID",
                        "message": "综合刷题结算快照不完整，请重新提交原交卷清单",
                    },
                )
            return {
                "session_id": session_id,
                "status": "COMPLETED",
                "reason": "completed",
                "idempotent": True,
                "state": completion_state,
            }

        if reason == "completed":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ADAPTIVE_COMPREHENSIVE_SUBMISSION_PENDING",
                    "message": "综合刷题必须通过整轮交卷接口完成",
                },
            )

        # Once the immutable manifest is present, abandoning the session would
        # strand durable answers or make an ambiguous network result terminal.
        # Only the batch submit/finalize path may advance a locked manifest.
        if isinstance(submission, dict):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ADAPTIVE_COMPREHENSIVE_SUBMISSION_IN_PROGRESS",
                    "message": "综合刷题交卷正在结算，请继续重试原交卷请求",
                },
            )
    reconcile_pending_adaptive_updates(
        supabase,
        user_id=user_id,
        exam_code=str(session["stats_exam_code"]),
        subject=str(session["subject"]),
    )
    try:
        response = call_supabase(
            lambda: supabase.rpc(
                "complete_practice_session",
                {"p_user_id": user_id, "p_session_id": session_id, "p_reason": reason},
            ).execute(),
            operation_name="complete adaptive practice session",
        )
    except Exception as exc:
        error_text = str(exc).lower()
        if "adaptive_update_pending" in error_text:
            _raise_update_barrier(pending_count=1)
        if "adaptive_comprehensive_submission_in_progress" in error_text:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ADAPTIVE_COMPREHENSIVE_SUBMISSION_IN_PROGRESS",
                    "message": "综合刷题交卷正在结算，请继续重试原交卷请求",
                },
            ) from exc
        if "adaptive_comprehensive_finalize_required" in error_text:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ADAPTIVE_COMPREHENSIVE_SUBMISSION_PENDING",
                    "message": "综合刷题必须通过整轮交卷接口完成",
                },
            ) from exc
        raise
    data = response.data
    if isinstance(data, list):
        data = data[0] if data else None
    if not isinstance(data, dict):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="练习会话结束状态保存失败")
    state = load_subject_state(
        supabase,
        user_id,
        str(session["stats_exam_code"]),
        str(session["subject"]),
    )
    return {**data, "state": serialize_state(state)}


def _comprehensive_submission_phase(submission: object) -> str | None:
    if not isinstance(submission, dict):
        return None
    phase = str(submission.get("phase") or "").strip().upper()
    if phase in {"LOCKED", "COMPLETED"}:
        return phase
    # A manifest written by the immediately preceding migration had no phase.
    # Treat it as locked so rolling deployments cannot abandon it halfway.
    if submission.get("client_submission_id") and submission.get("manifest_hash"):
        return "LOCKED"
    return None


def _completion_state_view(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    required_view_fields = {
        "theta",
        "uncertainty",
        "effective_evidence",
        "reliable_first_attempt_count",
        "diagnostic_status",
        "pending_conflicts",
        "confidence_label",
        "initial_level_range",
    }
    if required_view_fields.issubset(value):
        return {
            "theta": float(value["theta"]),
            "uncertainty": float(value["uncertainty"]),
            "effective_evidence": float(value["effective_evidence"]),
            "reliable_first_attempt_count": int(
                value["reliable_first_attempt_count"]
            ),
            "diagnostic_status": str(value["diagnostic_status"]),
            "pending_conflicts": int(value["pending_conflicts"]),
            "confidence_label": str(value["confidence_label"]),
            "initial_level_range": str(value["initial_level_range"]),
        }

    # The SQL may retain a full user_subject_state row for auditability.  Map
    # that row through the same serializer used by live responses.
    required_state_fields = {
        "theta",
        "uncertainty",
        "effective_evidence",
        "reliable_first_attempt_count",
        "diagnostic_status",
    }
    if not required_state_fields.issubset(value):
        return None
    state_row = dict(value)
    if "pending_conflict_count" not in state_row and "pending_conflicts" in state_row:
        state_row["pending_conflict_count"] = state_row["pending_conflicts"]
    try:
        return serialize_state(_state_from_row(state_row))
    except (TypeError, ValueError):
        return None


def _canonical_comprehensive_answers(
    *,
    items: list[dict],
    payload: SubmitAdaptiveComprehensiveSessionRequest,
) -> list[dict[str, Any]]:
    ordered_items = sorted(items, key=lambda value: int(value.get("position") or 0))
    positions = [int(item.get("position") or 0) for item in ordered_items]
    item_ids = [str(item.get("id") or "") for item in ordered_items]
    if (
        not item_ids
        or any(not item_id for item_id in item_ids)
        or len(set(item_ids)) != len(item_ids)
        or positions != list(range(1, len(ordered_items) + 1))
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "ADAPTIVE_COMPREHENSIVE_ROUND_INCOMPLETE",
                "message": "综合刷题固定题单题位不完整",
            },
        )

    answer_by_item_id = {
        str(answer.practice_session_item_id): answer for answer in payload.answers
    }
    if set(answer_by_item_id) != set(item_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "ADAPTIVE_COMPREHENSIVE_ANSWERS_INCOMPLETE",
                "message": "交卷数据必须覆盖本轮每一个题位，未作答题请提交空答案",
            },
        )

    return [
        {
            "position": position,
            "practice_session_item_id": item_id,
            "selected_answer": answer_by_item_id[item_id].selected_answer,
            "used_time": int(answer_by_item_id[item_id].used_time),
            "client_submission_id": str(
                answer_by_item_id[item_id].client_submission_id
            ).strip(),
        }
        for position, item_id in zip(positions, item_ids, strict=True)
    ]


def _comprehensive_submission_manifest(
    *,
    session_id: str,
    client_submission_id: str,
    canonical_answers: list[dict[str, Any]],
) -> str:
    canonical = json.dumps(
        {
            "session_id": session_id,
            "client_submission_id": client_submission_id,
            "answers": canonical_answers,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _grade_comprehensive_snapshot(
    *,
    session: dict,
    item: dict,
    selected_answer: str | None,
) -> dict[str, Any]:
    question = item.get("questions") or item.get("question_snapshot") or {}
    item_id = str(item.get("id") or "")
    question_id = str(item.get("question_id") or "")
    if (
        not isinstance(question, dict)
        or not item_id
        or not question_id
        or str(question.get("id") or "") != question_id
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="综合刷题私有题目快照暂时未能读取",
        )

    exam_code = str(session.get("stats_exam_code") or "")
    subject = str(session.get("subject") or "")
    physical_exam_code = str(question.get("exam_code") or "")
    if (
        str(question.get("subject") or "") != subject
        or physical_exam_code not in _question_exam_codes(exam_code, subject)
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "ADAPTIVE_COMPREHENSIVE_SNAPSHOT_SCOPE_MISMATCH",
                "message": "综合刷题题目快照与当前学科作用域不一致",
            },
        )

    correct_answer = str(question.get("answer") or "").strip().upper()
    if correct_answer not in {"A", "B", "C", "D"}:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="综合刷题私有题目快照缺少有效答案",
        )
    if selected_answer is not None and selected_answer not in {"A", "B", "C", "D"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="综合刷题答案选项无效",
        )

    return {
        "question": {
            "id": question_id,
            # User state always uses the actual Z001/Z002 scope even when the
            # physical question snapshot is shared as COMMON.
            "exam_code": exam_code,
            "subject": subject,
            "module": str(question.get("module") or ""),
            "submodule": str(question.get("submodule") or ""),
            "source_type": question.get("source_type"),
            "question_type": str(question.get("question_type") or "single_choice"),
            "difficulty": int(question.get("difficulty") or 2),
            "estimated_time_sec": question.get("estimated_time_sec"),
        },
        "result": {
            "practice_session_item_id": item_id,
            "question_id": question_id,
            "position": int(item.get("position") or 0),
            "selected_answer": selected_answer,
            "correct_answer": correct_answer,
            "is_correct": (
                None if selected_answer is None else selected_answer == correct_answer
            ),
            "explanation": str(question.get("explanation") or ""),
        },
    }


def _comprehensive_results_and_summary(
    *,
    session: dict,
    items: list[dict],
    canonical_answers: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    item_by_id = {str(item.get("id") or ""): item for item in items}
    results: list[dict[str, Any]] = []
    for answer in canonical_answers:
        item_id = str(answer["practice_session_item_id"])
        item = item_by_id.get(item_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="综合刷题交卷清单与固定题单不一致",
            )
        graded = _grade_comprehensive_snapshot(
            session=session,
            item=item,
            selected_answer=answer["selected_answer"],
        )
        results.append(graded["result"])

    answered_results = [result for result in results if result["selected_answer"] is not None]
    correct_count = sum(result["is_correct"] is True for result in answered_results)
    answered_count = len(answered_results)
    skipped_count = len(results) - answered_count
    summary = {
        "total_count": len(results),
        "answered_count": answered_count,
        "correct_count": correct_count,
        "wrong_count": answered_count - correct_count,
        "skipped_count": skipped_count,
        "accuracy": round(correct_count / answered_count * 100, 2) if answered_count else 0.0,
        "used_time": sum(int(answer["used_time"]) for answer in canonical_answers),
    }
    return results, summary


def _persist_comprehensive_answers_batch(
    supabase,
    *,
    user_id: str,
    session_id: str,
    client_submission_id: str,
    manifest_hash: str,
    expected_count: int,
) -> dict[str, Any] | None:
    """Persist one locked sheet in a single database transaction.

    ``None`` means only that the incremental optimization RPC is not deployed
    yet. Callers then use the established per-item idempotent path, which keeps
    rolling deployments functional without masking real batch failures.
    """

    try:
        response = call_supabase(
            lambda: supabase.rpc(
                "persist_adaptive_comprehensive_answers_batch",
                {
                    "p_user_id": user_id,
                    "p_session_id": session_id,
                    "p_client_submission_id": client_submission_id,
                    "p_manifest_hash": manifest_hash,
                },
            ).execute(),
            operation_name="persist comprehensive practice answers batch",
        )
    except Exception as exc:
        error_text = str(exc).lower()
        batch_rpc_name = "persist_adaptive_comprehensive_answers_batch"
        batch_rpc_missing = "pgrst202" in error_text or (
            batch_rpc_name in error_text
            and (
                "could not find the function" in error_text
                or ("function" in error_text and "does not exist" in error_text)
            )
        )
        if batch_rpc_missing:
            logger.info(
                "Comprehensive batch persistence RPC is not deployed; using idempotent item fallback"
            )
            return None
        if "adaptive_comprehensive_submission_conflict" in error_text:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ADAPTIVE_COMPREHENSIVE_SUBMISSION_CONFLICT",
                    "message": "本轮综合刷题已经使用另一份交卷内容提交",
                },
            ) from exc
        if "adaptive_comprehensive" in error_text or "adaptive_session" in error_text:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ADAPTIVE_COMPREHENSIVE_SUBMISSION_PENDING",
                    "message": "综合刷题交卷清单与固定题单状态不一致",
                },
            ) from exc
        raise

    data = response.data
    if isinstance(data, list):
        data = data[0] if data else None
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="综合刷题整卷保存未返回有效结果",
        )
    persisted_items = data.get("items")
    item_count = data.get("item_count")
    if (
        str(data.get("phase") or "").upper() != "LOCKED"
        or str(data.get("status") or "").upper() != "ACTIVE"
        or isinstance(item_count, bool)
        or not isinstance(item_count, int)
        or item_count != int(expected_count)
        or not isinstance(persisted_items, list)
        or len(persisted_items) != int(expected_count)
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="综合刷题整卷保存结果不完整",
        )
    return data


def _comprehensive_batch_reconciliation_context(
    batch_result: dict[str, Any],
    *,
    user_id: str,
    exam_code: str,
    subject: str,
    session_id: str,
    session_items: list[dict],
) -> dict[str, Any] | None:
    """Validate the transaction-authored state/pending snapshot for reuse."""

    external_pending_count = batch_result.get("external_pending_count")
    if (
        isinstance(external_pending_count, bool)
        or not isinstance(external_pending_count, int)
        or external_pending_count != 0
    ):
        return None
    subject_row = batch_result.get("subject_state")
    topic_rows = batch_result.get("topic_states")
    pending_conflict = batch_result.get("pending_conflict")
    persisted_items = batch_result.get("items")
    if (
        not isinstance(subject_row, dict)
        or not isinstance(topic_rows, list)
        or not isinstance(persisted_items, list)
        or str(subject_row.get("user_id") or "") != str(user_id)
        or str(subject_row.get("stats_exam_code") or "") != exam_code
        or str(subject_row.get("subject") or "") != subject
    ):
        return None

    try:
        subject_state = _state_from_row(subject_row)
        topic_state_map: dict[tuple[str, str], AbilityState] = {}
        for row in topic_rows:
            if (
                not isinstance(row, dict)
                or str(row.get("user_id") or "") != str(user_id)
                or str(row.get("stats_exam_code") or "") != exam_code
                or str(row.get("subject") or "") != subject
            ):
                return None
            key = (str(row.get("module") or ""), str(row.get("submodule") or ""))
            if not all(key) or key in topic_state_map:
                return None
            topic_state_map[key] = _state_from_row(row)
    except (TypeError, ValueError):
        return None

    if subject_state.pending_conflict_count > 0:
        if (
            not isinstance(pending_conflict, dict)
            or str(pending_conflict.get("user_id") or "") != str(user_id)
            or str(pending_conflict.get("stats_exam_code") or "") != exam_code
            or str(pending_conflict.get("subject") or "") != subject
            or str(pending_conflict.get("status") or "").upper() != "PENDING"
        ):
            return None
    elif pending_conflict is not None:
        return None

    item_by_id: dict[str, dict] = {}
    expected_positions: set[int] = set()
    try:
        for item in session_items:
            if not isinstance(item, dict):
                return None
            item_id = str(item.get("id") or "")
            position = item.get("position")
            if (
                not item_id
                or item_id in item_by_id
                or isinstance(position, bool)
                or not isinstance(position, int)
                or position <= 0
                or position in expected_positions
            ):
                return None
            item_by_id[item_id] = item
            expected_positions.add(position)
    except (TypeError, ValueError):
        return None
    if len(persisted_items) != len(item_by_id):
        return None

    pending_items: list[dict] = []
    seen_item_ids: set[str] = set()
    seen_positions: set[int] = set()
    for persisted_item in persisted_items:
        if not isinstance(persisted_item, dict):
            return None
        item_id = str(persisted_item.get("practice_session_item_id") or "")
        original_item = item_by_id.get(item_id)
        persisted_position = persisted_item.get("position")
        if (
            original_item is None
            or item_id in seen_item_ids
            or isinstance(persisted_position, bool)
            or not isinstance(persisted_position, int)
            or persisted_position in seen_positions
            or str(original_item.get("session_id") or "") != session_id
            or str(original_item.get("question_id") or "")
            != str(persisted_item.get("question_id") or "")
            or original_item.get("position") != persisted_position
        ):
            return None
        seen_item_ids.add(item_id)
        seen_positions.add(persisted_position)
        item_status = str(persisted_item.get("status") or "").upper()
        if item_status == "SKIPPED":
            if persisted_item.get("selected_answer") is not None:
                return None
            continue
        if item_status != "ANSWERED":
            return None
        adaptive_updated = persisted_item.get("adaptive_updated")
        if not isinstance(adaptive_updated, bool):
            return None
        if adaptive_updated:
            continue
        answer_id = str(persisted_item.get("answer_id") or "")
        answer_created_at = persisted_item.get("answer_created_at")
        used_time = persisted_item.get("used_time")
        if (
            not answer_id
            or str(persisted_item.get("stats_exam_code") or "") != exam_code
            or not isinstance(persisted_item.get("is_correct"), bool)
            or not isinstance(persisted_item.get("is_first_attempt"), bool)
            or isinstance(used_time, bool)
            or not isinstance(used_time, int)
            or used_time not in range(0, 86401)
            or not answer_created_at
            or not isinstance(original_item.get("questions"), dict)
            or not original_item.get("questions")
        ):
            return None
        pending_items.append(
            {
                "id": item_id,
                "session_id": session_id,
                "question_id": str(original_item.get("question_id") or ""),
                "position": persisted_position,
                "answer_id": answer_id,
                "answered_at": answer_created_at,
                "answer": {
                    "id": answer_id,
                    "stats_exam_code": exam_code,
                    "is_correct": persisted_item["is_correct"],
                    "is_first_attempt": persisted_item["is_first_attempt"],
                    "used_time": used_time,
                    "created_at": answer_created_at,
                },
                "questions": original_item.get("questions") or {},
            }
        )

    if seen_item_ids != set(item_by_id) or seen_positions != expected_positions:
        return None
    pending_items.sort(key=lambda entry: (entry["position"], entry["id"]))
    return {
        "prefetched_pending_items": pending_items,
        "prefetched_subject_state": subject_state,
        "prefetched_topic_state_map": topic_state_map,
        "prefetched_pending_conflict": pending_conflict,
    }


def _record_comprehensive_skip(
    supabase,
    *,
    user_id: str,
    session_id: str,
    item_id: str,
    client_submission_id: str,
    manifest_hash: str,
) -> dict[str, Any]:
    try:
        response = call_supabase(
            lambda: supabase.rpc(
                "record_adaptive_comprehensive_skip",
                {
                    "p_user_id": user_id,
                    "p_session_id": session_id,
                    "p_session_item_id": item_id,
                    "p_client_submission_id": client_submission_id,
                    "p_manifest_hash": manifest_hash,
                },
            ).execute(),
            operation_name="record comprehensive skipped item",
        )
    except Exception as exc:
        error_text = str(exc).lower()
        if is_missing_supabase_relation_error(exc):
            _raise_update_barrier(pending_count=1, migration_pending=True)
        if "adaptive_comprehensive_submission_conflict" in error_text:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ADAPTIVE_COMPREHENSIVE_SUBMISSION_CONFLICT",
                    "message": "本轮综合刷题已经使用另一份交卷内容提交",
                },
            ) from exc
        if "adaptive_comprehensive" in error_text or "adaptive_session" in error_text:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="跳过题位与已锁定的综合交卷清单不一致",
            ) from exc
        raise
    data = response.data
    if isinstance(data, list):
        data = data[0] if data else None
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="综合刷题跳过状态保存失败",
        )
    return data


def _finalize_comprehensive_submission(
    supabase,
    *,
    user_id: str,
    session_id: str,
    client_submission_id: str,
    manifest_hash: str,
) -> dict[str, Any]:
    try:
        response = call_supabase(
            lambda: supabase.rpc(
                "finalize_adaptive_comprehensive_submission",
                {
                    "p_user_id": user_id,
                    "p_session_id": session_id,
                    "p_client_submission_id": client_submission_id,
                    "p_manifest_hash": manifest_hash,
                },
            ).execute(),
            operation_name="finalize comprehensive practice submission",
        )
    except Exception as exc:
        error_text = str(exc).lower()
        if is_missing_supabase_relation_error(exc):
            _raise_update_barrier(pending_count=1, migration_pending=True)
        if "adaptive_update_pending" in error_text:
            _raise_update_barrier(pending_count=1)
        if "adaptive_comprehensive_submission_conflict" in error_text:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ADAPTIVE_COMPREHENSIVE_SUBMISSION_CONFLICT",
                    "message": "本轮综合刷题已经使用另一份交卷内容提交",
                },
            ) from exc
        if "adaptive_comprehensive" in error_text or "adaptive_session" in error_text:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ADAPTIVE_COMPREHENSIVE_SUBMISSION_PENDING",
                    "message": "综合刷题仍有题位或能力状态尚未结算",
                },
            ) from exc
        raise
    data = response.data
    if isinstance(data, list):
        data = data[0] if data else None
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="综合刷题原子结算失败",
        )
    return data


def submit_comprehensive_session(
    supabase,
    *,
    user_id: str,
    session_id: str,
    payload: SubmitAdaptiveComprehensiveSessionRequest,
) -> dict[str, Any]:
    session = _load_session(supabase, user_id, session_id)
    if str(session.get("mode") or "") != "comprehensive":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "ADAPTIVE_PRACTICE_MODE_MISMATCH",
                "message": "当前会话不是综合刷题",
            },
        )
    items = _load_session_items(supabase, session_id)
    expected_count = int(session.get("requested_question_count") or 0)
    if len(items) != expected_count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "ADAPTIVE_COMPREHENSIVE_ROUND_INCOMPLETE",
                "message": "综合刷题固定题单尚未完整生成",
            },
        )
    canonical_answers = _canonical_comprehensive_answers(items=items, payload=payload)
    manifest_hash = _comprehensive_submission_manifest(
        session_id=session_id,
        client_submission_id=payload.client_submission_id,
        canonical_answers=canonical_answers,
    )
    try:
        begin_response = call_supabase(
            lambda: supabase.rpc(
                "begin_adaptive_comprehensive_submission",
                {
                    "p_user_id": user_id,
                    "p_session_id": session_id,
                    "p_client_submission_id": payload.client_submission_id,
                    "p_manifest_hash": manifest_hash,
                    "p_answers": canonical_answers,
                },
            ).execute(),
            operation_name="lock comprehensive practice submission",
        )
    except Exception as exc:
        error_text = str(exc).lower()
        if "adaptive_comprehensive_submission_conflict" in error_text:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ADAPTIVE_COMPREHENSIVE_SUBMISSION_CONFLICT",
                    "message": "本轮综合刷题已经使用另一份交卷内容提交",
                },
            ) from exc
        if is_missing_supabase_relation_error(exc):
            _raise_update_barrier(pending_count=1, migration_pending=True)
        raise
    begin_data = begin_response.data
    if isinstance(begin_data, list):
        begin_data = begin_data[0] if begin_data else None
    if not isinstance(begin_data, dict):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="综合刷题交卷状态锁定失败",
        )

    begin_phase = str(begin_data.get("phase") or "").strip().upper()
    if not begin_phase:
        begin_phase = (
            "COMPLETED"
            if str(begin_data.get("status") or "").upper() == "COMPLETED"
            else "LOCKED"
        )
    if begin_phase not in {"LOCKED", "COMPLETED"}:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="综合刷题交卷状态无效",
        )

    results, summary = _comprehensive_results_and_summary(
        session=session,
        items=items,
        canonical_answers=canonical_answers,
    )
    if begin_phase == "COMPLETED":
        completion_state = _completion_state_view(begin_data.get("completion_state"))
        if completion_state is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ADAPTIVE_COMPREHENSIVE_SUBMISSION_STATE_INVALID",
                    "message": "综合刷题结算快照不完整，请重试原交卷请求",
                },
            )
        return {
            "session_id": session_id,
            "status": "COMPLETED",
            "reason": "completed",
            "idempotent": True,
            "summary": summary,
            "results": results,
            "state": completion_state,
            "adaptive_settled": True,
        }

    batch_persistence = _persist_comprehensive_answers_batch(
        supabase,
        user_id=user_id,
        session_id=session_id,
        client_submission_id=payload.client_submission_id,
        manifest_hash=manifest_hash,
        expected_count=expected_count,
    )
    if batch_persistence is None:
        item_by_id = {str(item.get("id") or ""): item for item in items}
        for answer in canonical_answers:
            item_id = str(answer["practice_session_item_id"])
            item = item_by_id[item_id]
            if answer["selected_answer"] is None:
                _record_comprehensive_skip(
                    supabase,
                    user_id=user_id,
                    session_id=session_id,
                    item_id=item_id,
                    client_submission_id=payload.client_submission_id,
                    manifest_hash=manifest_hash,
                )
                continue

            graded = _grade_comprehensive_snapshot(
                session=session,
                item=item,
                selected_answer=answer["selected_answer"],
            )
            persist_answer_submission(
                user_id=user_id,
                question=graded["question"],
                selected_answer=str(answer["selected_answer"]),
                used_time=int(answer["used_time"]),
                is_correct=bool(graded["result"]["is_correct"]),
                client_submission_id=str(answer["client_submission_id"]),
                practice_session_item_id=item_id,
                comprehensive_session_id=session_id,
                comprehensive_client_submission_id=payload.client_submission_id,
                comprehensive_manifest_hash=manifest_hash,
            )

    # The durable answer rows are now the recovery source of truth.  Apply
    # model updates in position order before closing the round; a failed update
    # leaves the immutable manifest in place so the exact same request resumes.
    reconcile_kwargs: dict[str, Any] = {
        "user_id": user_id,
        "exam_code": str(session["stats_exam_code"]),
        "subject": str(session["subject"]),
        "prefetched_session_items": items,
    }
    if batch_persistence is not None:
        batch_context = _comprehensive_batch_reconciliation_context(
            batch_persistence,
            user_id=user_id,
            exam_code=str(session["stats_exam_code"]),
            subject=str(session["subject"]),
            session_id=session_id,
            session_items=items,
        )
        if batch_context is not None:
            reconcile_kwargs.update(batch_context)
    reconcile_pending_adaptive_updates(supabase, **reconcile_kwargs)
    completion = _finalize_comprehensive_submission(
        supabase,
        user_id=user_id,
        session_id=session_id,
        client_submission_id=payload.client_submission_id,
        manifest_hash=manifest_hash,
    )
    if (
        str(completion.get("phase") or "COMPLETED").strip().upper() != "COMPLETED"
        or str(completion.get("status") or "COMPLETED").strip().upper()
        != "COMPLETED"
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="综合刷题原子结算未进入完成状态",
        )
    completion_state = _completion_state_view(completion.get("completion_state"))
    if completion_state is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="综合刷题原子结算未返回能力快照",
        )
    return {
        "session_id": session_id,
        "status": str(completion.get("status") or "COMPLETED"),
        "reason": "completed",
        "idempotent": bool(begin_data.get("idempotent")),
        "summary": summary,
        "results": results,
        "state": completion_state,
        "adaptive_settled": True,
    }


def _pending_conflict(supabase, user_id: str, exam_code: str, subject: str) -> dict | None:
    try:
        return _query_one(
            supabase.table("adaptive_conflicts")
            .select("*")
            .eq("user_id", user_id)
            .eq("stats_exam_code", exam_code)
            .eq("subject", subject)
            .eq("status", "PENDING")
            .order("opened_at"),
            operation_name="load pending adaptive conflict",
        )
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            return None
        raise


def _conflict_pair_is_closed(
    supabase,
    *,
    user_id: str,
    exam_code: str,
    subject: str,
    low_question_id: str,
    high_question_id: str,
) -> bool:
    try:
        row = _query_one(
            supabase.table("adaptive_conflicts")
            .select("id")
            .eq("user_id", user_id)
            .eq("stats_exam_code", exam_code)
            .eq("subject", subject)
            .eq("low_question_id", low_question_id)
            .eq("high_question_id", high_question_id)
            .in_("status", ["RESOLVED", "DEFERRED", "CANCELLED"]),
            operation_name="check closed adaptive conflict pair",
        )
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            return False
        raise
    return row is not None


def _detect_unhandled_inversion(
    supabase,
    *,
    user_id: str,
    exam_code: str,
    subject: str,
    observations: list[Observation],
    pending_conflict: dict | None,
):
    inversion = detect_inversion(observations)
    if inversion is None or pending_conflict is not None:
        return None
    if _conflict_pair_is_closed(
        supabase,
        user_id=user_id,
        exam_code=exam_code,
        subject=subject,
        low_question_id=inversion.low_question_id,
        high_question_id=inversion.high_question_id,
    ):
        return None
    return inversion


def _calibration_for_question(supabase, question_id: str, exam_code: str) -> dict:
    try:
        return _query_one(
            supabase.table("question_calibration")
            .select("*")
            .eq("question_id", question_id)
            .eq("stats_exam_code", exam_code),
            operation_name="load answer item calibration",
        ) or {}
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            return {}
        raise


def _conflict_verification_results(
    supabase,
    *,
    user_id: str,
    exam_code: str,
    subject: str,
    conflict_id: str,
) -> list[bool]:
    try:
        response = call_supabase(
            lambda: (
                supabase.table("adaptive_model_updates")
                .select("actual_correct,update_payload,created_at")
                .eq("user_id", user_id)
                .eq("stats_exam_code", exam_code)
                .eq("subject", subject)
                .eq("update_reason", "conflict_recheck")
                .order("created_at", desc=True)
                .limit(20)
                .execute()
            ),
            operation_name="load adaptive conflict verification history",
        )
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            return []
        raise

    matched: list[bool] = []
    for row in response.data or []:
        update_payload = row.get("update_payload") or {}
        # The request payload can be stale.  Only the database-authored result
        # proves that this answer actually consumed a verification slot.
        conflict_result = update_payload.get("conflict_result") or {}
        if (
            str(conflict_result.get("id") or "") == str(conflict_id)
            and str(conflict_result.get("action") or "")
            in {"verify", "resolve", "defer"}
        ):
            matched.append(bool(row.get("actual_correct")))
    matched.reverse()
    return matched


def _conflict_resolution_code(results: list[bool]) -> str:
    if len(results) < 2:
        return "inconclusive"
    low_parallel_correct, transfer_correct = results[-2:]
    if low_parallel_correct and not transfer_correct:
        return "boundary_confirmed"
    if low_parallel_correct and transfer_correct:
        return "likely_initial_lapse"
    if not low_parallel_correct and not transfer_correct:
        return "likely_high_guess"
    return "inconclusive"


def _state_payload(state: AbilityState) -> dict[str, Any]:
    data = asdict(state)
    data["diagnostic_status"] = state.diagnostic_status.value
    return data


def apply_adaptive_answer_update(
    supabase,
    *,
    user_id: str,
    question: dict,
    persisted: dict,
    used_time: int,
    practice_session_item_id: str | None,
    _prefetched_item: dict | None = None,
    _prefetched_session_items: list[dict] | None = None,
    _prefetched_subject_state: AbilityState | None = None,
    _prefetched_topic_state_map: dict[tuple[str, str], AbilityState] | None = None,
    _prefetched_pending_conflict: object = _UNSET,
    _include_planning_context: bool = False,
) -> dict[str, Any] | None:
    """Attach one durable answer to one adaptive model update.

    Ordinary legacy submissions omit ``practice_session_item_id`` and keep the
    existing aggregate statistics unchanged. Adaptive sessions call the
    idempotent RPC after the answer has a durable ``submission_id``.
    """

    if not practice_session_item_id or not persisted.get("submission_id"):
        return None
    exam_code = str(persisted.get("stats_exam_code") or "")

    item = deepcopy(_prefetched_item) if _prefetched_item is not None else None
    if item is None:
        try:
            item = _query_one(
                supabase.table("practice_session_items")
                .select(
                    "*,practice_sessions!inner(user_id,stats_exam_code,subject),"
                    "persisted_snapshot:practice_session_item_question_snapshots!inner("
                    "question_id,question_snapshot)"
                )
                .eq("id", practice_session_item_id)
                .eq("practice_sessions.user_id", user_id),
                operation_name="load answered adaptive item",
            )
        except Exception as exc:
            if is_missing_supabase_relation_error(exc):
                logger.info("Adaptive migration is not deployed; answer remains durably recorded")
                return {"adaptive_updated": False, "migration_pending": True}
            raise
    if not item:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="作答未关联到当前个性化题目")
    if str(item.get("question_id")) != str(question.get("id")):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="作答题目与个性化题目不一致")
    item_session = item.get("practice_sessions") or {}
    if _prefetched_item is not None:
        item_session = item_session or {
            "user_id": user_id,
            "stats_exam_code": exam_code,
            "subject": (item.get("questions") or {}).get("subject"),
        }
        item_question = item.get("questions")
        embedded_snapshot = {
            "question_id": item.get("question_id"),
            "question_snapshot": item_question,
        }
    else:
        embedded_snapshot = item.get("persisted_snapshot")
        if isinstance(embedded_snapshot, list):
            embedded_snapshot = embedded_snapshot[0] if embedded_snapshot else None
        item_question = (
            embedded_snapshot.get("question_snapshot")
            if isinstance(embedded_snapshot, dict)
            else None
        )
    if not isinstance(item_question, dict):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="个性化题目版本缺失")
    if (
        str(item_question.get("id") or "") != str(item.get("question_id") or "")
        or str((embedded_snapshot or {}).get("question_id") or "")
        != str(item.get("question_id") or "")
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="个性化题目版本不一致")
    subject = str(item_question.get("subject") or "")
    validate_scope(exam_code, subject)
    physical_exam_code = str(item_question.get("exam_code") or "")
    if (
        str(item_session.get("user_id") or "") != str(user_id)
        or str(item_session.get("stats_exam_code") or "") != exam_code
        or str(item_session.get("subject") or "") != subject
        or str(item_question.get("subject") or "") != subject
        or physical_exam_code not in _question_exam_codes(exam_code, subject)
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="作答与个性化练习作用域不一致")

    module = str(item_question.get("module") or "")
    submodule = str(item_question.get("submodule") or "")
    selection_metadata = item.get("strategy_metadata") or {}
    raw_quality_weight = selection_metadata.get("quality_weight")
    quality_weight = 0.7 if raw_quality_weight is None else float(raw_quality_weight)
    question_valid = bool(selection_metadata.get("question_valid", True))
    frozen_item_difficulty = (
        float(item["item_difficulty"])
        if item.get("item_difficulty") is not None
        else difficulty_to_theta(int(item_question.get("difficulty") or 2))
    )
    evidence = compute_evidence_weight(
        EvidenceContext(
            is_first_attempt=bool(persisted.get("is_first_attempt")),
            # The answer RPC binds answered_at before the client can reveal the
            # explanation.  Viewing it afterwards must not erase valid answer
            # evidence, including when the model update is retried later.
            answer_seen=_answer_was_seen_before_submission(
                item,
                {"created_at": item.get("answered_at") or persisted.get("created_at")},
            ),
            question_valid=question_valid,
            quality_weight=quality_weight,
            used_time=used_time,
            estimated_time=item_question.get("estimated_time_sec"),
        )
    )

    session_id = str(item.get("session_id") or "")
    session_items = (
        _prefetched_session_items
        if _prefetched_session_items is not None
        else _load_session_items(supabase, session_id)
    )
    current_position = int(item.get("position") or 0)
    previous_observations = [
        observation
        for observation in _observations_from_items(supabase, session_items)
        if observation.position < current_position
    ]
    current_observation = Observation(
        question_id=str(item_question["id"]),
        difficulty=int(item_question.get("difficulty") or 2),
        is_correct=bool(persisted.get("is_correct")),
        module=module,
        submodule=submodule,
        question_type=str(item_question.get("question_type") or "single_choice"),
        evidence_weight=evidence.weight,
        is_first_attempt=bool(persisted.get("is_first_attempt")),
        position=current_position,
    )
    observations = [*previous_observations, current_observation]
    verification_slot_expired = _verification_slot_expired(item)
    selected_conflict_id = str(selection_metadata.get("verification_conflict_id") or "")
    selected_expected_count = selection_metadata.get("verification_expected_count")
    selected_expected_difficulty = selection_metadata.get("verification_expected_difficulty")
    last_error: Exception | None = None
    for attempt in range(2):
        # A competing answer can advance both theta and a pending conflict.  All
        # derived decisions must therefore be rebuilt together on retry; merely
        # swapping in a newer theta would let two stale D2 items masquerade as
        # the required D2 -> D3 verification pair.
        use_prefetched_state = attempt == 0 and _prefetched_subject_state is not None
        subject_state = (
            _prefetched_subject_state
            if use_prefetched_state
            else load_subject_state(supabase, user_id, exam_code, subject)
        )
        topic_state_map = (
            dict(_prefetched_topic_state_map)
            if use_prefetched_state and _prefetched_topic_state_map is not None
            else load_topic_state_map(supabase, user_id, exam_code, subject)
        )
        topic_state = topic_state_map.get(
            (module, submodule),
            AbilityState(theta=subject_state.theta),
        )
        if use_prefetched_state and _prefetched_pending_conflict is not _UNSET:
            pending_conflict = _prefetched_pending_conflict
        else:
            pending_conflict = (
                _pending_conflict(supabase, user_id, exam_code, subject)
                if subject_state.pending_conflict_count > 0
                else None
            )
        inversion = _detect_unhandled_inversion(
            supabase,
            user_id=user_id,
            exam_code=exam_code,
            subject=subject,
            observations=observations,
            pending_conflict=pending_conflict,
        )
        # A lease expiry only releases the scarce verification slot.  The old
        # item can still arrive late and contribute ordinary theta evidence,
        # but it must neither consume nor reopen a conflict workflow.
        open_conflict = (
            inversion is not None
            and pending_conflict is None
            and not verification_slot_expired
        )
        pending_key = (
            str((pending_conflict or {}).get("module") or ""),
            str((pending_conflict or {}).get("submodule") or ""),
            str((pending_conflict or {}).get("question_type") or "single_choice"),
        )
        pending_count = int((pending_conflict or {}).get("verification_count") or 0)
        expected_verification_difficulty = 2 if pending_count % 2 == 0 else 3
        conflict_question_ids = {
            str((pending_conflict or {}).get("low_question_id") or ""),
            str((pending_conflict or {}).get("high_question_id") or ""),
        }
        selection_claim_matches = (
            not verification_slot_expired
            and bool(selected_conflict_id)
            and pending_conflict is not None
            and selected_conflict_id == str(pending_conflict.get("id") or "")
            and selected_expected_count is not None
            and int(selected_expected_count) == pending_count
            and selected_expected_difficulty is not None
            and int(selected_expected_difficulty) == expected_verification_difficulty
        )
        is_matching_verification = (
            selection_claim_matches
            and str(item.get("target_zone") or "") == TargetZone.VERIFY.value
            and current_observation.skill_key == pending_key
            and current_observation.difficulty == expected_verification_difficulty
            and current_observation.question_id not in conflict_question_ids
        )
        is_reliable_verification = (
            is_matching_verification and evidence.reliable_first_attempt
        )
        next_verification_count = pending_count + (1 if is_reliable_verification else 0)
        resolve_conflict = is_reliable_verification and next_verification_count >= 2
        resolution_code = None
        if resolve_conflict and pending_conflict:
            prior_verification_results = _conflict_verification_results(
                supabase,
                user_id=user_id,
                exam_code=exam_code,
                subject=subject,
                conflict_id=str(pending_conflict["id"]),
            )
            resolution_code = _conflict_resolution_code(
                [*prior_verification_results, current_observation.is_correct]
            )

        covered_topics = {
            key
            for key, state in topic_state_map.items()
            if state.reliable_first_attempt_count > 0
        }
        if evidence.reliable_first_attempt:
            covered_topics.add((module, submodule))
        subject_coverage_ready = len(covered_topics) >= 2

        update = update_ability(
            subject_state,
            topic_state,
            difficulty=current_observation.difficulty,
            is_correct=current_observation.is_correct,
            evidence=evidence,
            empirical_difficulty=frozen_item_difficulty,
            inversion_pending=open_conflict,
            conflict_resolved=resolve_conflict,
            subject_coverage_ready=subject_coverage_ready,
        )
        update_reason = "conflict_recheck" if is_matching_verification else "answer"
        conflict_payload: dict[str, Any] = {"action": "none"}
        if open_conflict and inversion:
            conflict_payload = {
                "action": "open",
                "low_question_id": inversion.low_question_id,
                "high_question_id": inversion.high_question_id,
                "module": inversion.skill_key[0],
                "submodule": inversion.skill_key[1],
                "question_type": inversion.skill_key[2],
            }
        elif pending_conflict and is_reliable_verification:
            conflict_payload = {
                "action": (
                    "defer"
                    if resolve_conflict and resolution_code == "inconclusive"
                    else "resolve" if resolve_conflict else "verify"
                ),
                "id": str(pending_conflict["id"]),
                "resolution": resolution_code if resolve_conflict else None,
            }

        rpc_payload = {
            "model_version": MODEL_VERSION,
            "predicted_probability": update.predicted_probability,
            "evidence_weight": update.evidence_weight,
            "item_difficulty": frozen_item_difficulty,
            "update_reason": update_reason,
            "evidence_reasons": list(evidence.reasons),
            "question_valid": question_valid,
            "subject_before": _state_payload(update.subject_before),
            "subject_after": _state_payload(update.subject_after),
            "topic_before": _state_payload(update.topic_before),
            "topic_after": _state_payload(update.topic_after),
            "conflict": conflict_payload,
        }
        try:
            response = call_supabase(
                lambda: supabase.rpc(
                    "apply_adaptive_model_update",
                    {
                        "p_user_id": user_id,
                        "p_answer_id": persisted["submission_id"],
                        "p_session_item_id": practice_session_item_id,
                        "p_update": rpc_payload,
                    },
                ).execute(),
                operation_name="apply adaptive answer update",
                attempts=1,
            )
            data = response.data
            if isinstance(data, list):
                data = data[0] if data else None
            if isinstance(data, dict):
                if _include_planning_context:
                    effective_action = str(data.get("conflict_action") or "none")
                    cache_valid = not bool(data.get("idempotent")) and effective_action in {
                        "none",
                        "open",
                        "verify",
                        "resolve",
                        "defer",
                    }
                    pending_conflict_after = pending_conflict
                    if effective_action == "open" and inversion is not None:
                        pending_conflict_after = {
                            "id": str(data.get("conflict_id") or ""),
                            "module": inversion.skill_key[0],
                            "submodule": inversion.skill_key[1],
                            "question_type": inversion.skill_key[2],
                            "low_question_id": inversion.low_question_id,
                            "high_question_id": inversion.high_question_id,
                            "verification_count": 0,
                            "status": "PENDING",
                        }
                        cache_valid = bool(pending_conflict_after["id"])
                    elif effective_action == "verify" and isinstance(pending_conflict, dict):
                        pending_conflict_after = {
                            **pending_conflict,
                            "verification_count": int(
                                pending_conflict.get("verification_count") or 0
                            )
                            + 1,
                        }
                    elif effective_action in {"resolve", "defer"}:
                        pending_conflict_after = None

                    subject_after = replace(
                        update.subject_after,
                        theta=float(data.get("theta", update.subject_after.theta)),
                        uncertainty=float(
                            data.get("uncertainty", update.subject_after.uncertainty)
                        ),
                        effective_evidence=float(
                            data.get(
                                "effective_evidence",
                                update.subject_after.effective_evidence,
                            )
                        ),
                        diagnostic_status=DiagnosticStatus(
                            str(
                                data.get(
                                    "diagnostic_status",
                                    update.subject_after.diagnostic_status.value,
                                )
                            ).upper()
                        ),
                        pending_conflict_count=int(
                            data.get(
                                "pending_conflicts",
                                update.subject_after.pending_conflict_count,
                            )
                        ),
                    )
                    topic_state_map_after = dict(topic_state_map)
                    topic_state_map_after[(module, submodule)] = update.topic_after
                    data = dict(data)
                    data["_planning_context"] = {
                        "cache_valid": cache_valid,
                        "subject_after": subject_after,
                        "topic_state_map_after": topic_state_map_after,
                        "pending_conflict_after": pending_conflict_after,
                    }
                return data
            raise RuntimeError("adaptive update RPC returned no result")
        except Exception as exc:
            last_error = exc
            if is_missing_supabase_relation_error(exc):
                logger.info("Adaptive migration is not deployed; answer remains durably recorded")
                return {"adaptive_updated": False, "migration_pending": True}
            if not _is_retryable_adaptive_update_error(exc) or attempt > 0:
                break
            # The next loop iteration reloads state, conflict count, expected
            # verification difficulty, resolution history and coverage.

    logger.warning(
        "Adaptive state update failed after durable answer (answer_id=%s error_type=%s)",
        persisted.get("submission_id"),
        type(last_error).__name__ if last_error else "unknown",
    )
    return {
        "adaptive_updated": False,
        "retryable": True,
        "error": "adaptive_state_update_pending",
    }
