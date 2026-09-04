#!/usr/bin/env python3
"""Offline release gate for adaptive-practice performance traces.

The input is a JSON array or JSONL export produced by a staging load runner and
the matching frontend telemetry. The gate performs no network or database I/O.
It validates both latency targets and the audit evidence needed to trust those
latencies: one candidate build/run, steady-stage windows, independent accounts,
unique events, immutable session ownership, and complete comprehensive manifests.

Example:
    python scripts/validate_adaptive_load_trace.py trace.jsonl \
        --require-vus 50,100,200 --min-samples-per-metric 30

Use ``--self-test`` to run in-memory positive and negative contract checks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


TRACE_SCHEMA_VERSION = 1
LATENCY_GATES_MS: dict[str, dict[str, float]] = {
    "special_answer_feedback": {"p95": 800.0},
    "special_prefetch_transition": {"p95": 100.0},
    "special_online_transition": {"p95": 500.0, "p99": 1200.0},
    "comprehensive_sheet_ready": {"p95": 1500.0},
    "comprehensive_local_transition": {"p95": 50.0},
}
TRANSITION_METRICS = {
    "special_prefetch_transition",
    "special_online_transition",
    "comprehensive_local_transition",
}
SPECIAL_TRANSITION_METRICS = {
    "special_prefetch_transition",
    "special_online_transition",
}
VALID_SCOPE = {
    "Z001": {"中华文化", "英语运用", "逻辑推理"},
    "Z002": {"中华文化", "英语运用", "数学基础"},
}
EXPECTED_OUTCOMES = {"success", "expected_conflict"}
SAMPLE_KINDS = {"natural", "forced_probe", "audit_only"}
DEFAULT_MIN_TRANSITIONS_PER_VU = 1500
DEFAULT_MIN_NATURAL_SPECIAL_TRANSITIONS_PER_VU = 300
DEFAULT_MIN_STABLE_SECONDS = 300.0
MIN_P95_SAMPLES = 100
MIN_P99_SAMPLES = 300
FOREGROUND_BUDGET_MS = 1200.0
STABLE_WINDOW_EDGE_TOLERANCE_SECONDS = 5.0
NETWORK_METRICS = set(LATENCY_GATES_MS).difference({"comprehensive_local_transition"})
CONFLICT_SCENARIOS: dict[str, dict[str, Any]] = {
    "special_update_pending": {
        "status_code": 409,
        "error_code": "ADAPTIVE_UPDATE_PENDING",
        "practice_mode": "special",
    },
    "comprehensive_manifest_conflict": {
        "status_code": 409,
        "error_code": "ADAPTIVE_COMPREHENSIVE_SUBMISSION_CONFLICT",
        "practice_mode": "comprehensive",
    },
}


class TraceError(ValueError):
    """Raised when a trace cannot be evaluated truthfully."""


def _nearest_rank(values: list[float], percentile: float) -> float:
    if not values:
        raise TraceError("cannot calculate a percentile from an empty sample")
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile * len(ordered)))
    return ordered[rank - 1]


def _load_records(path: Path) -> Iterable[dict[str, Any]]:
    """Yield trace records, streaming JSONL inputs one line at a time.

    JSON arrays remain supported for small fixtures, but production traces should
    use JSONL so the raw file and every decoded record are not resident together.
    """

    def iter_records() -> Iterable[dict[str, Any]]:
        try:
            with path.open("r", encoding="utf-8-sig") as handle:
                first_non_empty = ""
                for line in handle:
                    if line.strip():
                        first_non_empty = line
                        break
                if not first_non_empty:
                    raise TraceError("trace is empty")
                handle.seek(0)

                if first_non_empty.lstrip().startswith("["):
                    try:
                        value = json.load(handle)
                    except json.JSONDecodeError as exc:
                        raise TraceError(f"invalid JSON trace: {exc.msg}") from exc
                    if not isinstance(value, list):
                        raise TraceError("JSON trace root must be an array")
                    for record in value:
                        yield record
                    return

                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise TraceError(
                            f"invalid JSON on line {line_number}: {exc.msg}"
                        ) from exc
        except OSError as exc:
            raise TraceError(f"failed to read trace: {exc}") from exc

    return iter_records()


def _required_text(
    record: dict[str, Any],
    field: str,
    *,
    index: int,
    allow_empty: bool = False,
) -> str:
    if field not in record or not isinstance(record[field], str):
        raise TraceError(f"record {index}: {field} must be a string")
    value = record[field].strip()
    if not allow_empty and not value:
        raise TraceError(f"record {index}: {field} must be a non-empty string")
    return value


def _as_non_negative_number(value: Any, *, field: str, index: int) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TraceError(f"record {index}: {field} must be a number")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise TraceError(f"record {index}: {field} must be finite and >= 0")
    return number


def _as_integer(
    value: Any,
    *,
    field: str,
    index: int,
    minimum: int = 0,
) -> int:
    if isinstance(value, bool) or type(value) is not int:
        raise TraceError(f"record {index}: {field} must be an integer")
    if value < minimum:
        raise TraceError(f"record {index}: {field} must be >= {minimum}")
    return value


def _as_boolean(value: Any, *, field: str, index: int) -> bool:
    if not isinstance(value, bool):
        raise TraceError(f"record {index}: {field} must be boolean")
    return value


def _parse_timestamp(value: Any, *, field: str, index: int) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise TraceError(f"record {index}: {field} must be a timezone-aware ISO-8601 string")
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise TraceError(
            f"record {index}: {field} must be a timezone-aware ISO-8601 string"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise TraceError(f"record {index}: {field} must include a timezone offset")
    return parsed.astimezone(timezone.utc)


def _required_sha256(record: dict[str, Any], field: str, *, index: int) -> str:
    value = _required_text(record, field, index=index).lower()
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise TraceError(f"record {index}: {field} must be a lowercase SHA-256 hex digest")
    return value


def _manifest_hash(manifest: tuple[tuple[int, str, str], ...]) -> str:
    canonical = [
        {"position": position, "item_id": item_id, "question_id": question_id}
        for position, item_id, question_id in manifest
    ]
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _metric_sample_floor(metric: str, configured_minimum: int) -> int:
    statistical_floor = (
        MIN_P99_SAMPLES
        if "p99" in LATENCY_GATES_MS[metric]
        else MIN_P95_SAMPLES
    )
    return max(configured_minimum, statistical_floor)


def _latency_summary(values: list[float]) -> dict[str, Any]:
    result: dict[str, Any] = {"count": len(values)}
    if values:
        result.update(
            {
                "p50_ms": round(_nearest_rank(values, 0.50), 3),
                "p95_ms": round(_nearest_rank(values, 0.95), 3),
                "p99_ms": round(_nearest_rank(values, 0.99), 3),
                "max_ms": round(max(values), 3),
            }
        )
    return result


def evaluate(
    records: Iterable[dict[str, Any]],
    *,
    required_vus: set[int],
    minimum_samples: int,
    minimum_transitions_per_vu: int = DEFAULT_MIN_TRANSITIONS_PER_VU,
    minimum_natural_special_transitions_per_vu: int = (
        DEFAULT_MIN_NATURAL_SPECIAL_TRANSITIONS_PER_VU
    ),
    minimum_stable_seconds: float = DEFAULT_MIN_STABLE_SECONDS,
) -> dict[str, Any]:
    if not required_vus:
        raise TraceError("required_vus must contain at least one VU stage")
    if any(type(vus) is not int or vus < 1 for vus in required_vus):
        raise TraceError("required_vus must contain positive integers")
    if minimum_samples < 1:
        raise TraceError("minimum_samples must be >= 1")
    if minimum_transitions_per_vu < 1:
        raise TraceError("minimum_transitions_per_vu must be >= 1")
    if minimum_natural_special_transitions_per_vu < 1:
        raise TraceError("minimum_natural_special_transitions_per_vu must be >= 1")
    if not math.isfinite(minimum_stable_seconds) or minimum_stable_seconds <= 0:
        raise TraceError("minimum_stable_seconds must be finite and > 0")

    metric_durations: dict[str, list[float]] = defaultdict(list)
    stage_metric_durations: dict[tuple[int, str], list[float]] = defaultdict(list)
    stage_counts: dict[int, int] = defaultdict(int)
    stage_performance_users: dict[int, set[str]] = defaultdict(set)
    stage_performance_bounds: dict[tuple[str, int], tuple[datetime, datetime]] = {}
    stage_transition_counts: dict[int, int] = defaultdict(int)
    stage_transition_over_two_seconds: dict[int, int] = defaultdict(int)
    stage_natural_special_hits: dict[int, int] = defaultdict(int)
    stage_natural_special_total: dict[int, int] = defaultdict(int)
    stage_foreground_budget_exceeded: dict[int, int] = defaultdict(int)
    stage_foreground_budget_total: dict[int, int] = defaultdict(int)
    stage_windows: dict[tuple[str, int], tuple[datetime, datetime]] = {}

    failures: list[str] = []
    event_ids: set[str] = set()
    request_metric_keys: set[tuple[str, str]] = set()
    transition_ids: set[str] = set()
    run_ids: set[str] = set()
    candidate_identities: set[tuple[str, str, str, str]] = set()
    session_owners: dict[str, tuple[str, str, str, str, str, int]] = {}
    item_owners: dict[str, tuple[str, int, str]] = {}
    position_map: dict[tuple[str, int], tuple[str, str]] = {}
    session_questions: dict[str, dict[str, int]] = defaultdict(dict)
    session_manifests: dict[str, tuple[tuple[int, str, str], ...]] = {}
    session_manifest_hashes: dict[str, str] = {}
    sheet_manifest_sessions: set[str] = set()
    comprehensive_event_mappings: list[tuple[str, int, str, str]] = []
    manifest_conflict_attempts: list[tuple[int, str, str, str]] = []
    session_next_calls: dict[str, int] = defaultdict(int)
    conflict_scenario_counts: dict[str, int] = defaultdict(int)

    record_count = 0
    unexpected_errors = 0
    scope_mismatches = 0
    invalid_scope_records = 0
    duplicate_event_ids = 0
    duplicate_request_metric_records = 0
    duplicate_transition_ids = 0
    session_ownership_conflicts = 0
    item_ownership_conflicts = 0
    duplicate_position_conflicts = 0
    duplicate_question_conflicts = 0
    manifest_duplicate_positions = 0
    manifest_duplicate_items = 0
    manifest_duplicate_questions = 0
    manifest_incomplete = 0
    manifest_conflicts = 0
    manifest_event_mapping_mismatches = 0
    manifest_conflict_hash_mismatches = 0
    stage_metadata_conflicts = 0
    events_outside_stage_window = 0

    def register_mapping(
        *,
        session_id: str,
        item_id: str,
        question_id: str,
        position: int,
    ) -> None:
        nonlocal item_ownership_conflicts
        nonlocal duplicate_position_conflicts
        nonlocal duplicate_question_conflicts

        item_owner = (session_id, position, question_id)
        previous_item_owner = item_owners.setdefault(item_id, item_owner)
        if previous_item_owner != item_owner:
            item_ownership_conflicts += 1

        position_key = (session_id, position)
        winner = (item_id, question_id)
        previous_winner = position_map.setdefault(position_key, winner)
        if previous_winner != winner:
            duplicate_position_conflicts += 1

        previous_position = session_questions[session_id].setdefault(question_id, position)
        if previous_position != position:
            duplicate_question_conflicts += 1

    for index, record in enumerate(records, start=1):
        record_count = index
        if not isinstance(record, dict):
            raise TraceError("every trace record must be a JSON object")
        schema_version = _as_integer(
            record.get("schema_version"), field="schema_version", index=index, minimum=1
        )
        if schema_version != TRACE_SCHEMA_VERSION:
            raise TraceError(
                f"record {index}: unsupported schema_version {schema_version}; "
                f"expected {TRACE_SCHEMA_VERSION}"
            )

        metric = _required_text(record, "metric", index=index)
        if metric not in LATENCY_GATES_MS:
            raise TraceError(
                f"record {index}: unknown metric {metric!r}; expected one of "
                f"{', '.join(sorted(LATENCY_GATES_MS))}"
            )
        duration_ms = _as_non_negative_number(
            record.get("duration_ms"), field="duration_ms", index=index
        )
        ok = _as_boolean(record.get("ok"), field="ok", index=index)
        status_code = _as_integer(
            record.get("status_code"), field="status_code", index=index, minimum=0
        )
        if status_code > 599:
            raise TraceError(f"record {index}: status_code must be in 0..599")

        event_id = _required_text(record, "event_id", index=index)
        request_id = _required_text(record, "request_id", index=index)
        run_id = _required_text(record, "run_id", index=index)
        stage = _required_text(record, "stage", index=index)
        if stage != "steady":
            raise TraceError(f"record {index}: stage must be 'steady'")
        sample_kind = _required_text(record, "sample_kind", index=index)
        if sample_kind not in SAMPLE_KINDS:
            raise TraceError(
                f"record {index}: sample_kind must be one of {', '.join(sorted(SAMPLE_KINDS))}"
            )
        expected_outcome = _required_text(record, "expected_outcome", index=index)
        if expected_outcome not in EXPECTED_OUTCOMES:
            raise TraceError(
                f"record {index}: expected_outcome must be one of "
                f"{', '.join(sorted(EXPECTED_OUTCOMES))}"
            )
        error_code = _required_text(record, "error_code", index=index, allow_empty=True)
        if status_code >= 400 and not error_code:
            raise TraceError(f"record {index}: error_code is required for status_code >= 400")
        is_expected_conflict = expected_outcome == "expected_conflict"
        if is_expected_conflict != (sample_kind == "audit_only"):
            raise TraceError(
                f"record {index}: sample_kind='audit_only' must be used if and only if "
                "expected_outcome='expected_conflict'"
            )

        conflict_scenario = ""
        conflict_spec: dict[str, Any] | None = None
        attempted_manifest_hash = ""
        reported_authoritative_manifest_hash = ""
        if is_expected_conflict:
            conflict_scenario = _required_text(record, "conflict_scenario", index=index)
            conflict_spec = CONFLICT_SCENARIOS.get(conflict_scenario)
            if conflict_spec is None:
                raise TraceError(
                    f"record {index}: unsupported conflict_scenario {conflict_scenario!r}"
                )
            _required_text(record, "attempt_group_id", index=index)
            _as_integer(record.get("concurrency"), field="concurrency", index=index, minimum=2)
            expected_error_code = _required_text(
                record, "expected_error_code", index=index
            )
            if expected_error_code != conflict_spec["error_code"]:
                raise TraceError(
                    f"record {index}: expected_error_code does not match conflict_scenario"
                )
            if conflict_scenario == "comprehensive_manifest_conflict":
                attempted_manifest_hash = _required_sha256(
                    record, "attempted_manifest_hash", index=index
                )
                reported_authoritative_manifest_hash = _required_sha256(
                    record, "authoritative_manifest_hash", index=index
                )
                if attempted_manifest_hash == reported_authoritative_manifest_hash:
                    raise TraceError(
                        f"record {index}: attempted_manifest_hash must differ from "
                        "authoritative_manifest_hash"
                    )
            outcome_matches = (
                status_code == conflict_spec["status_code"]
                and error_code == expected_error_code
            )
        else:
            success_status_matches = (
                200 <= status_code < 300
                if metric in NETWORK_METRICS
                else status_code == 0
            )
            outcome_matches = success_status_matches
            if ok and error_code:
                raise TraceError(f"record {index}: successful events must have empty error_code")
        if ok and not outcome_matches:
            raise TraceError(
                f"record {index}: ok=true is inconsistent with metric/expected_outcome/status_code"
            )
        if not ok:
            unexpected_errors += 1

        vus = _as_integer(record.get("vus"), field="vus", index=index, minimum=1)
        occurred_at = _parse_timestamp(record.get("occurred_at"), field="occurred_at", index=index)
        stage_started_at = _parse_timestamp(
            record.get("stage_started_at"), field="stage_started_at", index=index
        )
        stage_ended_at = _parse_timestamp(
            record.get("stage_ended_at"), field="stage_ended_at", index=index
        )
        if stage_ended_at <= stage_started_at:
            raise TraceError(f"record {index}: stage_ended_at must be after stage_started_at")
        if not stage_started_at <= occurred_at <= stage_ended_at:
            events_outside_stage_window += 1
        stage_key = (run_id, vus)
        window = (stage_started_at, stage_ended_at)
        previous_window = stage_windows.setdefault(stage_key, window)
        if previous_window != window:
            stage_metadata_conflicts += 1

        practice_mode = _required_text(record, "practice_mode", index=index)
        expected_mode = "comprehensive" if metric.startswith("comprehensive_") else "special"
        if practice_mode != expected_mode:
            scope_mismatches += 1
        if conflict_spec is not None and practice_mode != conflict_spec["practice_mode"]:
            raise TraceError(
                f"record {index}: practice_mode does not match conflict_scenario"
            )

        user_key = _required_text(record, "anonymous_user_key", index=index)
        session_id = _required_text(record, "session_id", index=index)
        expected_exam = _required_text(record, "expected_exam_code", index=index)
        actual_exam = _required_text(record, "actual_exam_code", index=index)
        expected_subject = _required_text(record, "expected_subject", index=index)
        actual_subject = _required_text(record, "actual_subject", index=index)
        if expected_exam != actual_exam:
            scope_mismatches += 1
        if expected_subject != actual_subject:
            scope_mismatches += 1
        if actual_exam not in VALID_SCOPE or actual_subject not in VALID_SCOPE.get(
            actual_exam, set()
        ):
            invalid_scope_records += 1

        strategy_version = _required_text(record, "strategy_version", index=index)
        model_version = _required_text(record, "model_version", index=index)
        _required_text(record, "client_platform", index=index)
        app_version = _required_text(record, "app_version", index=index)
        build_sha = _required_text(record, "build_sha", index=index)

        run_ids.add(run_id)
        candidate_identities.add((build_sha, strategy_version, model_version, app_version))
        stage_counts[vus] += 1

        if event_id in event_ids:
            duplicate_event_ids += 1
            continue
        event_ids.add(event_id)
        request_metric_key = (request_id, metric)
        if request_metric_key in request_metric_keys:
            duplicate_request_metric_records += 1
            continue
        request_metric_keys.add(request_metric_key)
        if conflict_scenario:
            conflict_scenario_counts[conflict_scenario] += 1

        session_owner = (user_key, practice_mode, actual_exam, actual_subject, run_id, vus)
        previous_session_owner = session_owners.setdefault(session_id, session_owner)
        if previous_session_owner != session_owner:
            session_ownership_conflicts += 1

        if metric.startswith("comprehensive_"):
            next_calls = _as_integer(
                record.get("comprehensive_next_calls"),
                field="comprehensive_next_calls",
                index=index,
                minimum=0,
            )
            session_next_calls[session_id] = max(session_next_calls[session_id], next_calls)

        transition_is_unique = True
        foreground_budget_exceeded = False
        if metric in SPECIAL_TRANSITION_METRICS:
            transition_id = _required_text(record, "transition_id", index=index)
            prefetch_hit = _as_boolean(
                record.get("prefetch_hit"), field="prefetch_hit", index=index
            )
            foreground_budget_exceeded = _as_boolean(
                record.get("foreground_budget_exceeded"),
                field="foreground_budget_exceeded",
                index=index,
            )
            expected_budget_exceeded = duration_ms > FOREGROUND_BUDGET_MS
            if foreground_budget_exceeded != expected_budget_exceeded:
                raise TraceError(
                    f"record {index}: foreground_budget_exceeded must equal "
                    f"duration_ms > {FOREGROUND_BUDGET_MS:.0f}"
                )
            if metric == "special_prefetch_transition" and not prefetch_hit:
                raise TraceError(
                    f"record {index}: special_prefetch_transition requires prefetch_hit=true"
                )
            if metric == "special_online_transition" and prefetch_hit:
                raise TraceError(
                    f"record {index}: special_online_transition requires prefetch_hit=false"
                )
            if transition_id in transition_ids:
                duplicate_transition_ids += 1
                transition_is_unique = False
            else:
                transition_ids.add(transition_id)
        elif metric == "comprehensive_local_transition":
            _required_text(record, "navigation_kind", index=index)

        performance_sample = (
            ok
            and outcome_matches
            and expected_outcome == "success"
            and sample_kind != "audit_only"
            and transition_is_unique
        )

        item_id = ""
        question_id = ""
        position: int | None = None
        item_fields_present = any(
            field in record and record.get(field) not in (None, "")
            for field in ("item_id", "question_id", "position")
        )
        item_fields_required = (
            metric != "comprehensive_sheet_ready" and expected_outcome == "success"
        )
        if is_expected_conflict and item_fields_present:
            raise TraceError(
                f"record {index}: expected-conflict records must use attempted/hash fields, "
                "not authoritative item fields"
            )
        if item_fields_required or item_fields_present:
            item_id = _required_text(record, "item_id", index=index)
            question_id = _required_text(record, "question_id", index=index)
            position = _as_integer(
                record.get("position"), field="position", index=index, minimum=1
            )
            register_mapping(
                session_id=session_id,
                item_id=item_id,
                question_id=question_id,
                position=position,
            )
            if metric.startswith("comprehensive_") and expected_outcome == "success":
                comprehensive_event_mappings.append(
                    (session_id, position, item_id, question_id)
                )

        manifest_canonical: tuple[tuple[int, str, str], ...] | None = None
        manifest_required = (
            metric == "comprehensive_sheet_ready"
            and expected_outcome == "success"
            and ok
        )
        manifest_present = "manifest_items" in record or "manifest_question_count" in record
        if manifest_present and not metric.startswith("comprehensive_"):
            raise TraceError(
                f"record {index}: manifests are only valid for comprehensive metrics"
            )
        if manifest_present and is_expected_conflict:
            raise TraceError(
                f"record {index}: expected-conflict records must use manifest hashes, "
                "not authoritative manifest_items"
            )
        if manifest_required or manifest_present:
            manifest_question_count = _as_integer(
                record.get("manifest_question_count"),
                field="manifest_question_count",
                index=index,
                minimum=1,
            )
            manifest_items = record.get("manifest_items")
            if not isinstance(manifest_items, list) or not manifest_items:
                raise TraceError(f"record {index}: manifest_items must be a non-empty array")

            parsed_manifest: list[tuple[int, str, str]] = []
            seen_positions: set[int] = set()
            seen_items: set[str] = set()
            seen_questions: set[str] = set()
            for manifest_index, entry in enumerate(manifest_items, start=1):
                if not isinstance(entry, dict):
                    raise TraceError(
                        f"record {index}: manifest item {manifest_index} must be an object"
                    )
                manifest_item_id = _required_text(entry, "item_id", index=index)
                manifest_question_id = _required_text(entry, "question_id", index=index)
                manifest_position = _as_integer(
                    entry.get("position"),
                    field=f"manifest_items[{manifest_index}].position",
                    index=index,
                    minimum=1,
                )
                if manifest_position in seen_positions:
                    manifest_duplicate_positions += 1
                if manifest_item_id in seen_items:
                    manifest_duplicate_items += 1
                if manifest_question_id in seen_questions:
                    manifest_duplicate_questions += 1
                seen_positions.add(manifest_position)
                seen_items.add(manifest_item_id)
                seen_questions.add(manifest_question_id)
                parsed_manifest.append(
                    (manifest_position, manifest_item_id, manifest_question_id)
                )
                register_mapping(
                    session_id=session_id,
                    item_id=manifest_item_id,
                    question_id=manifest_question_id,
                    position=manifest_position,
                )

            expected_positions = set(range(1, manifest_question_count + 1))
            if (
                len(manifest_items) != manifest_question_count
                or seen_positions != expected_positions
            ):
                manifest_incomplete += 1
            manifest_canonical = tuple(sorted(parsed_manifest))
            calculated_manifest_hash = _manifest_hash(manifest_canonical)
            if metric == "comprehensive_sheet_ready" and expected_outcome == "success" and ok:
                reported_hash = _required_sha256(
                    record, "authoritative_manifest_hash", index=index
                )
                if reported_hash != calculated_manifest_hash:
                    raise TraceError(
                        f"record {index}: authoritative_manifest_hash does not match manifest_items"
                    )
                sheet_manifest_sessions.add(session_id)
            elif "authoritative_manifest_hash" in record:
                reported_hash = _required_sha256(
                    record, "authoritative_manifest_hash", index=index
                )
                if reported_hash != calculated_manifest_hash:
                    raise TraceError(
                        f"record {index}: authoritative_manifest_hash does not match manifest_items"
                    )
            previous_manifest = session_manifests.setdefault(session_id, manifest_canonical)
            if previous_manifest != manifest_canonical:
                manifest_conflicts += 1
            previous_manifest_hash = session_manifest_hashes.setdefault(
                session_id, calculated_manifest_hash
            )
            if previous_manifest_hash != calculated_manifest_hash:
                manifest_conflicts += 1

        if conflict_scenario == "comprehensive_manifest_conflict":
            manifest_conflict_attempts.append(
                (
                    index,
                    session_id,
                    reported_authoritative_manifest_hash,
                    attempted_manifest_hash,
                )
            )

        if performance_sample:
            metric_durations[metric].append(duration_ms)
            stage_metric_durations[(vus, metric)].append(duration_ms)
            stage_performance_users[vus].add(user_key)
            previous_bounds = stage_performance_bounds.get(stage_key)
            if previous_bounds is None:
                stage_performance_bounds[stage_key] = (occurred_at, occurred_at)
            else:
                stage_performance_bounds[stage_key] = (
                    min(previous_bounds[0], occurred_at),
                    max(previous_bounds[1], occurred_at),
                )
            if metric in TRANSITION_METRICS:
                stage_transition_counts[vus] += 1
                stage_transition_over_two_seconds[vus] += int(duration_ms > 2000.0)
            if metric in SPECIAL_TRANSITION_METRICS and sample_kind == "natural":
                stage_natural_special_total[vus] += 1
                stage_natural_special_hits[vus] += int(
                    metric == "special_prefetch_transition"
                )
            if metric in SPECIAL_TRANSITION_METRICS:
                stage_foreground_budget_total[vus] += 1
                stage_foreground_budget_exceeded[vus] += int(
                    foreground_budget_exceeded
                )

    if record_count == 0:
        raise TraceError("trace has no records")

    for session_id, position, item_id, question_id in comprehensive_event_mappings:
        manifest = session_manifests.get(session_id)
        if (
            session_id not in sheet_manifest_sessions
            or manifest is None
            or (position, item_id, question_id) not in manifest
        ):
            manifest_event_mapping_mismatches += 1

    for _, session_id, reported_hash, _ in manifest_conflict_attempts:
        authoritative_hash = session_manifest_hashes.get(session_id)
        if (
            session_id not in sheet_manifest_sessions
            or authoritative_hash is None
            or authoritative_hash != reported_hash
        ):
            manifest_conflict_hash_mismatches += 1

    if len(run_ids) != 1:
        failures.append(f"trace must contain exactly one run_id; found {len(run_ids)}")
    if len(candidate_identities) != 1:
        failures.append(
            "trace mixes build_sha/strategy_version/model_version/app_version candidates"
        )
    if duplicate_event_ids:
        failures.append(f"duplicate event_id records: {duplicate_event_ids}")
    if duplicate_request_metric_records:
        failures.append(
            f"duplicate request_id + metric records: {duplicate_request_metric_records}"
        )
    if duplicate_transition_ids:
        failures.append(f"duplicate transition_id records: {duplicate_transition_ids}")
    if unexpected_errors:
        failures.append(f"unexpected request or UI errors: {unexpected_errors}")
    if scope_mismatches:
        failures.append(f"expected/actual scope or mode mismatches: {scope_mismatches}")
    if invalid_scope_records:
        failures.append(f"invalid exam/subject scope records: {invalid_scope_records}")
    if session_ownership_conflicts:
        failures.append(f"session ownership/scope conflicts: {session_ownership_conflicts}")
    if item_ownership_conflicts:
        failures.append(f"item ownership conflicts: {item_ownership_conflicts}")
    if duplicate_position_conflicts:
        failures.append(f"duplicate position winner conflicts: {duplicate_position_conflicts}")
    if duplicate_question_conflicts:
        failures.append(
            f"duplicate physical questions within a session: {duplicate_question_conflicts}"
        )
    if manifest_duplicate_positions:
        failures.append(f"manifest duplicate positions: {manifest_duplicate_positions}")
    if manifest_duplicate_items:
        failures.append(f"manifest duplicate item IDs: {manifest_duplicate_items}")
    if manifest_duplicate_questions:
        failures.append(f"manifest duplicate question IDs: {manifest_duplicate_questions}")
    if manifest_incomplete:
        failures.append(f"incomplete/non-contiguous manifests: {manifest_incomplete}")
    if manifest_conflicts:
        failures.append(f"immutable manifest conflicts: {manifest_conflicts}")
    if manifest_event_mapping_mismatches:
        failures.append(
            f"comprehensive event/manifest mapping mismatches: {manifest_event_mapping_mismatches}"
        )
    if manifest_conflict_hash_mismatches:
        failures.append(
            "comprehensive conflict/authoritative manifest hash mismatches: "
            f"{manifest_conflict_hash_mismatches}"
        )
    if stage_metadata_conflicts:
        failures.append(f"inconsistent stage windows: {stage_metadata_conflicts}")
    if events_outside_stage_window:
        failures.append(f"events outside declared steady window: {events_outside_stage_window}")

    comprehensive_next_calls = sum(session_next_calls.values())
    if comprehensive_next_calls:
        failures.append(f"comprehensive /next calls: {comprehensive_next_calls}")

    observed_vus = set(stage_counts)
    if observed_vus != required_vus:
        failures.append(
            f"observed VU stages {sorted(observed_vus)} must exactly match "
            f"required VU stages {sorted(required_vus)}"
        )

    stage_latency: dict[str, dict[str, dict[str, Any]]] = {}
    stage_derived: dict[str, dict[str, Any]] = {}
    for vus in sorted(required_vus):
        metric_results: dict[str, dict[str, Any]] = {}
        for metric, gates in LATENCY_GATES_MS.items():
            durations = stage_metric_durations.get((vus, metric), [])
            metric_result = _latency_summary(durations)
            required_metric_samples = _metric_sample_floor(metric, minimum_samples)
            metric_result["required_count"] = required_metric_samples
            metric_results[metric] = metric_result
            if len(durations) < required_metric_samples:
                failures.append(
                    f"VU stage {vus} {metric}: samples {len(durations)} "
                    f"< required {required_metric_samples}"
                )
            if durations:
                for percentile_name, threshold in gates.items():
                    observed_raw = _nearest_rank(
                        durations, float(percentile_name.removeprefix("p")) / 100.0
                    )
                    if observed_raw > threshold:
                        failures.append(
                            f"VU stage {vus} {metric} {percentile_name} "
                            f"{observed_raw:.6f}ms > {threshold:.3f}ms"
                        )
        stage_latency[str(vus)] = metric_results

        window_candidates = [
            window for (_, stage_vus), window in stage_windows.items() if stage_vus == vus
        ]
        stable_seconds = 0.0
        if len(window_candidates) == 1:
            stable_seconds = (window_candidates[0][1] - window_candidates[0][0]).total_seconds()
            if stable_seconds < minimum_stable_seconds:
                failures.append(
                    f"VU stage {vus}: steady window {stable_seconds:.3f}s "
                    f"< required {minimum_stable_seconds:.3f}s"
                )
        elif vus in stage_counts:
            failures.append(f"VU stage {vus}: expected exactly one stable window")

        performance_bounds_candidates = [
            bounds
            for (_, stage_vus), bounds in stage_performance_bounds.items()
            if stage_vus == vus
        ]
        observed_performance_span_seconds = 0.0
        if len(performance_bounds_candidates) == 1:
            observed_performance_span_seconds = (
                performance_bounds_candidates[0][1] - performance_bounds_candidates[0][0]
            ).total_seconds()
            if (
                observed_performance_span_seconds
                + STABLE_WINDOW_EDGE_TOLERANCE_SECONDS
                < minimum_stable_seconds
            ):
                failures.append(
                    f"VU stage {vus}: observed performance span "
                    f"{observed_performance_span_seconds:.3f}s + "
                    f"{STABLE_WINDOW_EDGE_TOLERANCE_SECONDS:.3f}s tolerance "
                    f"< required {minimum_stable_seconds:.3f}s"
                )
        elif vus in stage_counts:
            failures.append(
                f"VU stage {vus}: expected exactly one observed performance time span"
            )

        independent_users = len(stage_performance_users.get(vus, set()))
        if independent_users < vus:
            failures.append(
                f"VU stage {vus}: independent performance users {independent_users} "
                f"< required {vus}"
            )

        natural_total = stage_natural_special_total.get(vus, 0)
        natural_hits = stage_natural_special_hits.get(vus, 0)
        prefetch_hit_rate = natural_hits / natural_total if natural_total else 0.0
        if natural_total < minimum_natural_special_transitions_per_vu:
            failures.append(
                f"VU stage {vus}: natural special transitions {natural_total} "
                f"< required {minimum_natural_special_transitions_per_vu}"
            )
        if prefetch_hit_rate < 0.90:
            failures.append(
                f"VU stage {vus}: special prefetch hit rate {prefetch_hit_rate:.4%} < 90%"
            )

        transition_count = stage_transition_counts.get(vus, 0)
        transitions_over_two_seconds = stage_transition_over_two_seconds.get(vus, 0)
        over_two_seconds_rate = (
            transitions_over_two_seconds / transition_count if transition_count else 0.0
        )
        if transition_count < minimum_transitions_per_vu:
            failures.append(
                f"VU stage {vus}: inter-question transitions {transition_count} "
                f"< required {minimum_transitions_per_vu}"
            )
        if over_two_seconds_rate >= 0.002:
            failures.append(
                f"VU stage {vus}: inter-question transitions over 2s rate "
                f"{over_two_seconds_rate:.4%} >= 0.2%"
            )

        foreground_budget_total = stage_foreground_budget_total.get(vus, 0)
        foreground_budget_exceeded_count = stage_foreground_budget_exceeded.get(vus, 0)
        foreground_budget_exceeded_rate = (
            foreground_budget_exceeded_count / foreground_budget_total
            if foreground_budget_total
            else 0.0
        )

        stage_derived[str(vus)] = {
            "steady_window_seconds": round(stable_seconds, 3),
            "observed_performance_span_seconds": round(
                observed_performance_span_seconds, 3
            ),
            "independent_users": independent_users,
            "natural_special_transition_count": natural_total,
            "special_prefetch_hit_rate": round(prefetch_hit_rate, 6),
            "inter_question_transition_count": transition_count,
            "inter_question_over_2s_count": transitions_over_two_seconds,
            "inter_question_over_2s_rate": round(over_two_seconds_rate, 6),
            "foreground_budget_exceeded_count": foreground_budget_exceeded_count,
            "foreground_budget_exceeded_rate": round(
                foreground_budget_exceeded_rate, 6
            ),
        }

    ordered_required_windows: list[tuple[int, datetime, datetime]] = []
    if len(run_ids) == 1:
        only_run_id = next(iter(run_ids))
        for vus in required_vus:
            window = stage_windows.get((only_run_id, vus))
            if window:
                ordered_required_windows.append((vus, window[0], window[1]))
    ordered_required_windows.sort(key=lambda value: value[1])
    for previous, current in zip(ordered_required_windows, ordered_required_windows[1:]):
        if current[1] < previous[2]:
            failures.append(
                f"VU stages {previous[0]} and {current[0]} have overlapping steady windows"
            )

    samples = {
        metric: _latency_summary(metric_durations.get(metric, []))
        for metric in LATENCY_GATES_MS
    }
    stage_metric_counts = {
        str(vus): {
            metric: len(stage_metric_durations.get((vus, metric), []))
            for metric in sorted(LATENCY_GATES_MS)
        }
        for vus in sorted(stage_counts)
    }
    foreground_budget_total = sum(stage_foreground_budget_total.values())
    foreground_budget_exceeded_count = sum(stage_foreground_budget_exceeded.values())
    foreground_budget_exceeded_rate = (
        foreground_budget_exceeded_count / foreground_budget_total
        if foreground_budget_total
        else 0.0
    )

    return {
        "passed": not failures,
        "schema_version": TRACE_SCHEMA_VERSION,
        "record_count": record_count,
        "unique_event_count": len(event_ids),
        "required_vus": sorted(required_vus),
        "stage_counts": {str(key): stage_counts[key] for key in sorted(stage_counts)},
        "stage_metric_counts": stage_metric_counts,
        "latency": samples,
        "stage_latency": stage_latency,
        "stage_derived": stage_derived,
        "derived": {
            "unexpected_errors": unexpected_errors,
            "comprehensive_next_calls": comprehensive_next_calls,
            "scope_mismatches": scope_mismatches,
            "invalid_scope_records": invalid_scope_records,
            "duplicate_event_ids": duplicate_event_ids,
            "duplicate_request_metric_records": duplicate_request_metric_records,
            "duplicate_transition_ids": duplicate_transition_ids,
            "session_ownership_conflicts": session_ownership_conflicts,
            "item_ownership_conflicts": item_ownership_conflicts,
            "duplicate_position_winner_conflicts": duplicate_position_conflicts,
            "duplicate_question_conflicts": duplicate_question_conflicts,
            "manifest_duplicate_positions": manifest_duplicate_positions,
            "manifest_duplicate_items": manifest_duplicate_items,
            "manifest_duplicate_questions": manifest_duplicate_questions,
            "manifest_incomplete": manifest_incomplete,
            "manifest_conflicts": manifest_conflicts,
            "manifest_event_mapping_mismatches": manifest_event_mapping_mismatches,
            "manifest_conflict_hash_mismatches": manifest_conflict_hash_mismatches,
            "conflict_scenario_counts": dict(sorted(conflict_scenario_counts.items())),
            "foreground_budget_exceeded_count": foreground_budget_exceeded_count,
            "foreground_budget_exceeded_rate": round(
                foreground_budget_exceeded_rate, 6
            ),
            "stage_metadata_conflicts": stage_metadata_conflicts,
            "events_outside_stage_window": events_outside_stage_window,
        },
        "failures": failures,
    }


def _iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _synthetic_self_test_records(
    *,
    required_vus: set[int] | None = None,
    minimum_samples: int = 30,
    minimum_transitions_per_vu: int = DEFAULT_MIN_TRANSITIONS_PER_VU,
    minimum_natural_special_transitions_per_vu: int = (
        DEFAULT_MIN_NATURAL_SPECIAL_TRANSITIONS_PER_VU
    ),
    minimum_stable_seconds: float = DEFAULT_MIN_STABLE_SECONDS,
) -> list[dict[str, Any]]:
    vus_stages = sorted(required_vus or {50, 100, 200})
    records: list[dict[str, Any]] = []
    base_time = datetime(2026, 9, 4, 0, 0, tzinfo=timezone.utc)
    global_serial = 0

    for stage_index, vus in enumerate(vus_stages):
        stage_seconds = max(360, math.ceil(minimum_stable_seconds) + 60)
        stage_start = base_time + timedelta(seconds=stage_index * (stage_seconds + 120))
        stage_end = stage_start + timedelta(seconds=stage_seconds)
        stage_serial = 0

        def make_record(
            metric: str,
            *,
            user_index: int | None = None,
            session_id: str | None = None,
            **extra: Any,
        ) -> dict[str, Any]:
            nonlocal global_serial, stage_serial
            global_serial += 1
            stage_serial += 1
            resolved_user_index = (
                (stage_serial - 1) % vus if user_index is None else user_index % vus
            )
            comprehensive = metric.startswith("comprehensive_")
            event_time = stage_start + timedelta(
                seconds=1 + (stage_serial % max(1, stage_seconds - 2))
            )
            record: dict[str, Any] = {
                "schema_version": TRACE_SCHEMA_VERSION,
                "event_id": f"synthetic-event-{global_serial}",
                "metric": metric,
                "occurred_at": _iso_z(event_time),
                "duration_ms": {
                    "special_answer_feedback": 320.0,
                    "special_prefetch_transition": 45.0,
                    "special_online_transition": 330.0,
                    "comprehensive_sheet_ready": 900.0,
                    "comprehensive_local_transition": 18.0,
                }[metric],
                "ok": True,
                "status_code": 0 if metric == "comprehensive_local_transition" else 200,
                "error_code": "",
                "expected_outcome": "success",
                "request_id": f"synthetic-request-{global_serial}",
                "run_id": "synthetic-self-test-run",
                "stage": "steady",
                "stage_started_at": _iso_z(stage_start),
                "stage_ended_at": _iso_z(stage_end),
                "sample_kind": "natural",
                "vus": vus,
                "practice_mode": "comprehensive" if comprehensive else "special",
                "anonymous_user_key": f"synthetic-user-{vus}-{resolved_user_index}",
                "session_id": session_id or f"synthetic-session-{global_serial}",
                "expected_exam_code": "Z001",
                "actual_exam_code": "Z001",
                "expected_subject": "逻辑推理",
                "actual_subject": "逻辑推理",
                "strategy_version": "adaptive-v1",
                "model_version": "ability-v1",
                "client_platform": "synthetic",
                "app_version": "self-test",
                "build_sha": "synthetic-build",
            }
            record.update(extra)
            return record

        answer_count = max(
            _metric_sample_floor("special_answer_feedback", minimum_samples),
            vus,
        )
        natural_special_count = max(
            minimum_natural_special_transitions_per_vu,
            math.ceil(
                _metric_sample_floor("special_prefetch_transition", minimum_samples)
                / 0.90
            ),
        )
        special_hit_count = math.ceil(natural_special_count * 0.90)
        special_miss_count = natural_special_count - special_hit_count
        forced_online_count = max(
            0,
            _metric_sample_floor("special_online_transition", minimum_samples)
            - special_miss_count,
        )
        special_transition_count = (
            special_hit_count + special_miss_count + forced_online_count
        )
        comprehensive_local_count = max(
            _metric_sample_floor("comprehensive_local_transition", minimum_samples),
            minimum_transitions_per_vu - special_transition_count,
        )
        sheet_count = _metric_sample_floor("comprehensive_sheet_ready", minimum_samples)

        for serial in range(answer_count):
            records.append(
                make_record(
                    "special_answer_feedback",
                    item_id=f"special-answer-item-{vus}-{serial}",
                    question_id=f"special-answer-question-{vus}-{serial}",
                    position=1,
                )
            )

        for serial in range(special_hit_count):
            records.append(
                make_record(
                    "special_prefetch_transition",
                    item_id=f"special-prefetch-item-{vus}-{serial}",
                    question_id=f"special-prefetch-question-{vus}-{serial}",
                    position=1,
                    transition_id=f"special-transition-hit-{vus}-{serial}",
                    prefetch_hit=True,
                    foreground_budget_exceeded=False,
                )
            )

        for serial in range(special_miss_count):
            records.append(
                make_record(
                    "special_online_transition",
                    item_id=f"special-online-item-{vus}-{serial}",
                    question_id=f"special-online-question-{vus}-{serial}",
                    position=1,
                    transition_id=f"special-transition-miss-{vus}-{serial}",
                    prefetch_hit=False,
                    foreground_budget_exceeded=False,
                )
            )

        for serial in range(forced_online_count):
            records.append(
                make_record(
                    "special_online_transition",
                    item_id=f"special-online-probe-item-{vus}-{serial}",
                    question_id=f"special-online-probe-question-{vus}-{serial}",
                    position=1,
                    transition_id=f"special-transition-probe-{vus}-{serial}",
                    prefetch_hit=False,
                    foreground_budget_exceeded=False,
                    sample_kind="forced_probe",
                )
            )

        comprehensive_sessions: list[tuple[str, int, list[dict[str, Any]]]] = []
        for serial in range(sheet_count):
            user_index = serial % vus
            session_id = f"comprehensive-session-{vus}-{serial}"
            manifest = [
                {
                    "position": position,
                    "item_id": f"comprehensive-item-{vus}-{serial}-{position}",
                    "question_id": f"comprehensive-question-{vus}-{serial}-{position}",
                }
                for position in range(1, 9)
            ]
            comprehensive_sessions.append((session_id, user_index, manifest))
            canonical_manifest = tuple(
                (item["position"], item["item_id"], item["question_id"])
                for item in manifest
            )
            records.append(
                make_record(
                    "comprehensive_sheet_ready",
                    user_index=user_index,
                    session_id=session_id,
                    comprehensive_next_calls=0,
                    manifest_question_count=len(manifest),
                    manifest_items=[dict(item) for item in manifest],
                    authoritative_manifest_hash=_manifest_hash(canonical_manifest),
                )
            )

        for serial in range(comprehensive_local_count):
            session_id, user_index, manifest = comprehensive_sessions[
                serial % len(comprehensive_sessions)
            ]
            manifest_item = manifest[(serial // len(comprehensive_sessions)) % len(manifest)]
            records.append(
                make_record(
                    "comprehensive_local_transition",
                    user_index=user_index,
                    session_id=session_id,
                    item_id=manifest_item["item_id"],
                    question_id=manifest_item["question_id"],
                    position=manifest_item["position"],
                    comprehensive_next_calls=0,
                    navigation_kind="next",
                )
            )

    return records


def _run_self_test(
    *,
    required_vus: set[int],
    minimum_samples: int,
    minimum_transitions_per_vu: int,
    minimum_natural_special_transitions_per_vu: int,
    minimum_stable_seconds: float,
) -> dict[str, Any]:
    def run(records: list[dict[str, Any]]) -> dict[str, Any]:
        return evaluate(
            records,
            required_vus=required_vus,
            minimum_samples=minimum_samples,
            minimum_transitions_per_vu=minimum_transitions_per_vu,
            minimum_natural_special_transitions_per_vu=(
                minimum_natural_special_transitions_per_vu
            ),
            minimum_stable_seconds=minimum_stable_seconds,
        )

    base = _synthetic_self_test_records(
        required_vus=required_vus,
        minimum_samples=minimum_samples,
        minimum_transitions_per_vu=minimum_transitions_per_vu,
        minimum_natural_special_transitions_per_vu=(
            minimum_natural_special_transitions_per_vu
        ),
        minimum_stable_seconds=minimum_stable_seconds,
    )
    cases: dict[str, bool] = {"valid_trace_passes": run(base)["passed"]}

    duplicate_event = list(base)
    duplicate_event.append(dict(base[0]))
    duplicate_result = run(duplicate_event)
    cases["duplicate_event_fails"] = (
        not duplicate_result["passed"]
        and duplicate_result["derived"]["duplicate_event_ids"] == 1
    )

    cross_owner = list(base)
    first = dict(cross_owner[0])
    second = dict(cross_owner[1])
    second["session_id"] = first["session_id"]
    second["anonymous_user_key"] = first["anonymous_user_key"] + "-other"
    cross_owner[1] = second
    owner_result = run(cross_owner)
    cases["cross_owner_session_fails"] = (
        not owner_result["passed"]
        and owner_result["derived"]["session_ownership_conflicts"] > 0
    )

    raw_threshold = list(base)
    first_vus = min(required_vus)
    for record_index, source in enumerate(raw_threshold):
        if source["vus"] == first_vus and source["metric"] == "special_answer_feedback":
            changed = dict(source)
            changed["duration_ms"] = 800.0004
            raw_threshold[record_index] = changed
    threshold_result = run(raw_threshold)
    cases["unrounded_threshold_fails"] = any(
        f"VU stage {first_vus} special_answer_feedback p95" in failure
        for failure in threshold_result["failures"]
    )

    fractional = list(base)
    comp_index = next(
        i
        for i, record in enumerate(fractional)
        if record["metric"] == "comprehensive_local_transition"
    )
    fractional_record = dict(fractional[comp_index])
    fractional_record["comprehensive_next_calls"] = 0.9
    fractional[comp_index] = fractional_record
    try:
        run(fractional)
    except TraceError:
        cases["fractional_integer_rejected"] = True
    else:
        cases["fractional_integer_rejected"] = False

    manifest_duplicate = list(base)
    manifest_index = next(
        i
        for i, record in enumerate(manifest_duplicate)
        if record["metric"] == "comprehensive_sheet_ready"
    )
    changed_manifest_record = dict(manifest_duplicate[manifest_index])
    changed_manifest = [dict(item) for item in changed_manifest_record["manifest_items"]]
    changed_manifest[1]["question_id"] = changed_manifest[0]["question_id"]
    changed_manifest_record["manifest_items"] = changed_manifest
    changed_manifest_record["authoritative_manifest_hash"] = _manifest_hash(
        tuple(
            sorted(
                (item["position"], item["item_id"], item["question_id"])
                for item in changed_manifest
            )
        )
    )
    manifest_duplicate[manifest_index] = changed_manifest_record
    manifest_result = run(manifest_duplicate)
    cases["manifest_duplicate_fails"] = (
        not manifest_result["passed"]
        and manifest_result["derived"]["manifest_duplicate_questions"] > 0
    )

    collapsed_timeline = [
        dict(record, occurred_at=record["stage_started_at"]) for record in base
    ]
    collapsed_result = run(collapsed_timeline)
    cases["collapsed_timeline_fails"] = any(
        "observed performance span" in failure
        for failure in collapsed_result["failures"]
    )

    audit_success = list(base)
    audit_success[0] = dict(audit_success[0], sample_kind="audit_only")
    try:
        run(audit_success)
    except TraceError:
        cases["audit_only_success_rejected"] = True
    else:
        cases["audit_only_success_rejected"] = False

    network_status_zero = list(base)
    network_status_zero[0] = dict(network_status_zero[0], status_code=0)
    try:
        run(network_status_zero)
    except TraceError:
        cases["network_status_zero_rejected"] = True
    else:
        cases["network_status_zero_rejected"] = False

    budget_mismatch = list(base)
    budget_index = next(
        i
        for i, record in enumerate(budget_mismatch)
        if record["metric"] in SPECIAL_TRANSITION_METRICS
    )
    budget_mismatch[budget_index] = dict(
        budget_mismatch[budget_index], foreground_budget_exceeded=True
    )
    try:
        run(budget_mismatch)
    except TraceError:
        cases["foreground_budget_mismatch_rejected"] = True
    else:
        cases["foreground_budget_mismatch_rejected"] = False

    extra_vu = dict(
        base[0],
        event_id="synthetic-extra-vu-event",
        request_id="synthetic-extra-vu-request",
        session_id="synthetic-extra-vu-session",
        item_id="synthetic-extra-vu-item",
        question_id="synthetic-extra-vu-question",
        anonymous_user_key="synthetic-extra-vu-user",
        vus=max(required_vus) + 1,
    )
    extra_vu_result = run([*base, extra_vu])
    cases["extra_vu_stage_fails"] = any(
        "must exactly match required VU stages" in failure
        for failure in extra_vu_result["failures"]
    )

    one_performance_user = [
        (
            dict(record, anonymous_user_key=f"single-performance-user-{first_vus}")
            if record["vus"] == first_vus
            else record
        )
        for record in base
    ]
    conflict_seed = next(
        record
        for record in base
        if record["vus"] == first_vus
        and record["metric"] == "special_online_transition"
    )
    for serial in range(first_vus - 1):
        audit_record = dict(
            conflict_seed,
            event_id=f"synthetic-audit-user-event-{serial}",
            request_id=f"synthetic-audit-user-request-{serial}",
            transition_id=f"synthetic-audit-user-transition-{serial}",
            session_id=f"synthetic-audit-user-session-{serial}",
            anonymous_user_key=f"synthetic-audit-only-user-{serial}",
            sample_kind="audit_only",
            expected_outcome="expected_conflict",
            status_code=409,
            error_code="ADAPTIVE_UPDATE_PENDING",
            conflict_scenario="special_update_pending",
            attempt_group_id=f"synthetic-audit-group-{serial}",
            concurrency=2,
            expected_error_code="ADAPTIVE_UPDATE_PENDING",
        )
        for field in ("item_id", "question_id", "position"):
            audit_record.pop(field, None)
        one_performance_user.append(audit_record)
    one_user_result = run(one_performance_user)
    cases["audit_users_do_not_inflate_performance_users"] = (
        one_user_result["stage_derived"][str(first_vus)]["independent_users"] == 1
        and any(
            "independent performance users 1" in failure
            for failure in one_user_result["failures"]
        )
    )

    manifest_sheet = next(
        record
        for record in base
        if record["vus"] == first_vus
        and record["metric"] == "comprehensive_sheet_ready"
    )
    valid_manifest_conflict = dict(
        manifest_sheet,
        event_id="synthetic-manifest-conflict-event",
        request_id="synthetic-manifest-conflict-request",
        sample_kind="audit_only",
        expected_outcome="expected_conflict",
        status_code=409,
        error_code="ADAPTIVE_COMPREHENSIVE_SUBMISSION_CONFLICT",
        conflict_scenario="comprehensive_manifest_conflict",
        attempt_group_id="synthetic-manifest-conflict-group",
        concurrency=2,
        expected_error_code="ADAPTIVE_COMPREHENSIVE_SUBMISSION_CONFLICT",
        attempted_manifest_hash=hashlib.sha256(b"different-manifest").hexdigest(),
    )
    for field in ("manifest_items", "manifest_question_count"):
        valid_manifest_conflict.pop(field, None)
    valid_conflict_result = run([*base, valid_manifest_conflict])
    cases["manifest_conflict_hash_contract_passes"] = valid_conflict_result["passed"]

    wrong_conflict_code = dict(
        valid_manifest_conflict,
        event_id="synthetic-wrong-conflict-event",
        request_id="synthetic-wrong-conflict-request",
        error_code="UNRELATED_CONFLICT",
    )
    try:
        run([*base, wrong_conflict_code])
    except TraceError:
        cases["wrong_conflict_code_rejected"] = True
    else:
        cases["wrong_conflict_code_rejected"] = False

    try:
        evaluate(
            base,
            required_vus=set(),
            minimum_samples=minimum_samples,
            minimum_transitions_per_vu=minimum_transitions_per_vu,
            minimum_natural_special_transitions_per_vu=(
                minimum_natural_special_transitions_per_vu
            ),
            minimum_stable_seconds=minimum_stable_seconds,
        )
    except TraceError:
        cases["empty_required_vus_rejected"] = True
    else:
        cases["empty_required_vus_rejected"] = False

    return {
        "passed": all(cases.values()),
        "record_count": len(base),
        "cases": cases,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", nargs="?", type=Path, help="JSONL or JSON-array trace")
    parser.add_argument(
        "--require-vus",
        default="50,100,200",
        help="comma-separated VU stages that must be represented (default: 50,100,200)",
    )
    parser.add_argument(
        "--min-samples-per-metric",
        type=int,
        default=30,
        help=(
            "configured minimum observations per metric/VU; effective floor is max(value, "
            "100 for p95 metrics, 300 for the online p99 metric) (default: 30)"
        ),
    )
    parser.add_argument(
        "--min-transitions-per-vu",
        type=int,
        default=DEFAULT_MIN_TRANSITIONS_PER_VU,
        help="minimum inter-question transitions per required VU stage (default: 1500)",
    )
    parser.add_argument(
        "--min-natural-special-transitions-per-vu",
        type=int,
        default=DEFAULT_MIN_NATURAL_SPECIAL_TRANSITIONS_PER_VU,
        help="minimum natural special transitions used for hit rate per VU stage (default: 300)",
    )
    parser.add_argument(
        "--min-stable-seconds",
        type=float,
        default=DEFAULT_MIN_STABLE_SECONDS,
        help="minimum declared steady-stage duration per VU stage (default: 300)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run in-memory positive and negative gate checks; performs no file or network I/O",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        required_vus = {
            int(value.strip())
            for value in str(args.require_vus).split(",")
            if value.strip()
        }
    except ValueError:
        print("--require-vus must contain positive comma-separated integers", file=sys.stderr)
        return 2
    if not required_vus or any(value < 1 for value in required_vus):
        print("--require-vus must contain at least one positive integer", file=sys.stderr)
        return 2
    if args.min_samples_per_metric < 1:
        print("--min-samples-per-metric must be >= 1", file=sys.stderr)
        return 2
    if args.min_transitions_per_vu < 1:
        print("--min-transitions-per-vu must be >= 1", file=sys.stderr)
        return 2
    if args.min_natural_special_transitions_per_vu < 1:
        print("--min-natural-special-transitions-per-vu must be >= 1", file=sys.stderr)
        return 2
    if not math.isfinite(args.min_stable_seconds) or args.min_stable_seconds <= 0:
        print("--min-stable-seconds must be finite and > 0", file=sys.stderr)
        return 2
    if args.self_test and args.trace is not None:
        print("provide either a trace path or --self-test, not both", file=sys.stderr)
        return 2
    if not args.self_test and args.trace is None:
        print("a trace path is required unless --self-test is used", file=sys.stderr)
        return 2

    try:
        if args.self_test:
            result = _run_self_test(
                required_vus=required_vus,
                minimum_samples=args.min_samples_per_metric,
                minimum_transitions_per_vu=args.min_transitions_per_vu,
                minimum_natural_special_transitions_per_vu=(
                    args.min_natural_special_transitions_per_vu
                ),
                minimum_stable_seconds=args.min_stable_seconds,
            )
        else:
            records = _load_records(args.trace)
            result = evaluate(
                records,
                required_vus=required_vus,
                minimum_samples=args.min_samples_per_metric,
                minimum_transitions_per_vu=args.min_transitions_per_vu,
                minimum_natural_special_transitions_per_vu=(
                    args.min_natural_special_transitions_per_vu
                ),
                minimum_stable_seconds=args.min_stable_seconds,
            )
    except TraceError as exc:
        print(json.dumps({"passed": False, "trace_error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
