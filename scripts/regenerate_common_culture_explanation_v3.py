"""Offline orchestration for full-bank Chinese-culture V3 regeneration.

The active snapshot is the immutable question baseline.  This entry point may
call the explanation-only six-question service, but it never imports a
database client and never emits question mutations.  Its candidate artifact
contains root-level ``updates`` whose items contain only ``id`` and
``culture_v3``; publication and every human review gate remain locked.

The checkpoint is authoritative for resuming.  Attempts are atomically
recorded *before* each model call, so a process interruption cannot silently
exceed the per-question retry ceiling.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import sys
import tempfile
from collections import Counter
from collections.abc import Awaitable, Callable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.culture_explanation_regeneration import (  # noqa: E402
    MAX_REGENERATION_BATCH_SIZE,
    feedback_by_id_from_rejections,
    parse_culture_explanation_regeneration_response,
    regenerate_culture_explanation_batch,
)
from app.services.culture_explanation_codex_cli import (  # noqa: E402
    CodexCLIOutputError,
    preflight_culture_explanation_codex_cli,
    regenerate_culture_explanation_batch_with_codex_cli,
)


SNAPSHOT_PATH = ROOT / "data" / "common_culture_active_snapshot.json"
CANDIDATE_PATH = ROOT / "data" / "common_culture_explanation_v3_regeneration_candidates.json"
CHECKPOINT_PATH = ROOT / "data" / "common_culture_explanation_v3_regeneration_checkpoint.json"
REVIEW_REPORT_PATH = ROOT / "reports" / "common_culture_explanation_v3_regeneration_review.json"

SUBJECT = "中华文化"
BATCH_SIZE = 6
DEFAULT_MAX_ATTEMPTS = 3
MAX_ALLOWED_ATTEMPTS = 10
PROVIDERS = ("deepseek", "codex-cli")
DEFAULT_PROVIDER = "deepseek"
MEMORY_GATE_REQUIRED_CODE = "culture_v3_memory_strategy_required"
MEMORY_GATE_MIGRATION_MAX_EXTRA_ATTEMPTS = 1

if MAX_REGENERATION_BATCH_SIZE != BATCH_SIZE:
    raise RuntimeError(
        "culture explanation service batch contract changed: "
        f"expected {BATCH_SIZE}, received {MAX_REGENERATION_BATCH_SIZE}"
    )

# Matches the fixed-question baseline used by the V3 pilot.  Explanation and
# workflow/status fields are intentionally absent: the model is permitted to
# supply culture_v3 only, and this runner never constructs a database patch.
IMMUTABLE_BASELINE_FIELDS = (
    "id",
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
    "difficulty",
    "source_type",
    "source_year",
    "passage_id",
)

CHECKPOINT_SCHEMA = "common_culture_explanation_v3_regeneration_checkpoint_v2"
CANDIDATE_SCHEMA = "common_culture_explanation_v3_regeneration_candidates_v1"
REVIEW_SCHEMA = "common_culture_explanation_v3_regeneration_review_v1"

BatchGenerator = Callable[..., Awaitable[dict[str, object]]]


def _generator_for_provider(provider: str) -> BatchGenerator:
    if provider == "deepseek":
        return regenerate_culture_explanation_batch
    if provider == "codex-cli":
        return regenerate_culture_explanation_batch_with_codex_cli
    raise ValueError(f"unsupported regeneration provider: {provider}")


class CheckpointRunLock:
    """Hold an OS-released exclusive lock for one checkpoint/run pair."""

    def __init__(self, checkpoint_path: Path) -> None:
        self.path = checkpoint_path.resolve().with_suffix(checkpoint_path.suffix + ".lock")
        self._handle = None

    def __enter__(self) -> "CheckpointRunLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        if handle.seek(0, os.SEEK_END) == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            handle.close()
            raise RuntimeError(
                "another regeneration run already owns checkpoint lock: "
                f"{_portable_path(self.path)}"
            ) from exc

        metadata = json.dumps(
            {"pid": os.getpid(), "acquired_at": _now()},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        handle.seek(1)
        handle.truncate()
        handle.write(metadata)
        handle.flush()
        os.fsync(handle.fileno())
        self._handle = handle
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        handle = self._handle
        self._handle = None
        if handle is None:
            return
        try:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clean_id(value: object) -> str:
    return str(value or "").strip()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest().upper()


def _raw_digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _portable_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def atomic_write_json(path: Path, payload: object) -> None:
    """Write one JSON artifact via a same-directory fsync + replace."""

    destination = path.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=destination.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"required file is missing: {_portable_path(path)}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON in {_portable_path(path)}: {exc}") from exc


def _baseline_payload(question: Mapping[str, object]) -> dict[str, object]:
    return {field: question.get(field) for field in IMMUTABLE_BASELINE_FIELDS}


def baseline_sha256(question: Mapping[str, object]) -> str:
    return _digest(_baseline_payload(question))


def _load_snapshot(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON in {_portable_path(path)}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise RuntimeError("active snapshot root must be a JSON object")
    rows = payload.get("questions")
    if not isinstance(rows, list):
        raise RuntimeError("active snapshot does not contain a questions array")
    if any(not isinstance(row, Mapping) for row in rows):
        raise RuntimeError("active snapshot contains a non-object question")

    questions = [dict(row) for row in rows]
    declared_count = payload.get("question_count")
    if declared_count is not None and declared_count != len(questions):
        raise RuntimeError(
            "active snapshot question_count does not match questions array: "
            f"{declared_count!r} != {len(questions)}"
        )
    ids = [_clean_id(row.get("id")) for row in questions]
    duplicate_ids = sorted(
        question_id
        for question_id, count in Counter(ids).items()
        if not question_id or count > 1
    )
    if duplicate_ids:
        raise RuntimeError(
            "active snapshot contains blank or duplicate ids: "
            + ", ".join(duplicate_ids[:10])
        )

    culture_questions = [
        row for row in questions if str(row.get("subject") or "").strip() == SUBJECT
    ]
    return {
        "payload": dict(payload),
        "questions": questions,
        "culture_questions": culture_questions,
        "by_id": {question_id: row for question_id, row in zip(ids, questions)},
        "raw_file_sha256": _raw_digest(raw),
        "canonical_json_sha256": _digest(payload),
    }


def parse_ids(values: Sequence[str] | None) -> list[str] | None:
    if values is None:
        return None
    parsed: list[str] = []
    for value in values:
        parsed.extend(part.strip() for part in str(value).split(",") if part.strip())
    if not parsed:
        raise ValueError("--ids requires at least one non-empty id")
    duplicates = [key for key, count in Counter(parsed).items() if count > 1]
    if duplicates:
        raise ValueError("--ids contains duplicates: " + ", ".join(sorted(duplicates)))
    return parsed


def _select_questions(
    snapshot: Mapping[str, object],
    *,
    requested_ids: Sequence[str] | None,
    limit: int | None,
) -> list[dict[str, object]]:
    if limit is not None and limit < 1:
        raise ValueError("--limit must be at least 1")

    culture_questions = list(snapshot["culture_questions"])
    by_id = snapshot["by_id"]
    if not isinstance(by_id, Mapping):
        raise RuntimeError("internal snapshot id map is invalid")

    if requested_ids is None:
        selected = culture_questions
    else:
        missing = [question_id for question_id in requested_ids if question_id not in by_id]
        if missing:
            raise ValueError("--ids contains ids missing from the snapshot: " + ", ".join(missing))
        wrong_subject = [
            question_id
            for question_id in requested_ids
            if str(by_id[question_id].get("subject") or "").strip() != SUBJECT
        ]
        if wrong_subject:
            raise ValueError(
                "--ids contains questions outside subject=中华文化: "
                + ", ".join(wrong_subject)
            )
        selected = [dict(by_id[question_id]) for question_id in requested_ids]

    if limit is not None:
        selected = selected[:limit]
    if not selected:
        raise RuntimeError("selection contains no subject=中华文化 questions")
    return [dict(row) for row in selected]


def _new_checkpoint(
    *,
    snapshot_path: Path,
    checkpoint_path: Path,
    output_path: Path,
    report_path: Path,
    snapshot: Mapping[str, object],
    selected: Sequence[Mapping[str, object]],
    requested_ids: Sequence[str] | None,
    limit: int | None,
    max_attempts: int,
    provider: str,
    provider_runtime: Mapping[str, object],
) -> dict[str, object]:
    created_at = _now()
    selected_ids = [_clean_id(row.get("id")) for row in selected]
    return {
        "schema_version": CHECKPOINT_SCHEMA,
        "created_at": created_at,
        "updated_at": created_at,
        "run_status": "in_progress",
        "source": {
            "path": _portable_path(snapshot_path),
            "raw_file_sha256": snapshot["raw_file_sha256"],
            "canonical_json_sha256": snapshot["canonical_json_sha256"],
            "question_count": len(snapshot["questions"]),
            "culture_question_count": len(snapshot["culture_questions"]),
        },
        "artifacts": {
            "checkpoint_path": _portable_path(checkpoint_path),
            "candidate_path": _portable_path(output_path),
            "review_report_path": _portable_path(report_path),
        },
        "selection": {
            "subject": SUBJECT,
            "requested_ids": list(requested_ids) if requested_ids is not None else None,
            "limit": limit,
            "selected_count": len(selected),
            "selected_ids_sha256": _digest(selected_ids),
            "selected_ids": selected_ids,
        },
        "batch_size": BATCH_SIZE,
        "provider": provider,
        "provider_runtime": dict(provider_runtime),
        "max_attempts_per_question": max_attempts,
        "immutable_baseline_fields": list(IMMUTABLE_BASELINE_FIELDS),
        "read_only_source": True,
        "database_writes": 0,
        "ready_for_publish": False,
        "batch_call_count": 0,
        "recovered_interrupted_attempt_count": 0,
        "static_reaudit_events": [],
        "memory_gate_migration_events": [],
        "batch_events": [],
        "items": [
            {
                "id": question_id,
                "baseline_sha256": baseline_sha256(row),
                "baseline_verified": True,
                "state": "pending",
                "attempts": 0,
                "feedback": [],
                "failures": [],
                "culture_v3": None,
                "audit": None,
                "model": None,
                "in_flight": None,
                "last_failure_category": None,
                "terminal_category": None,
                "last_rejected_culture_v3": None,
                "migration_extra_attempts_granted": 0,
            }
            for question_id, row in zip(selected_ids, selected)
        ],
    }


def _checkpoint_item_map(checkpoint: Mapping[str, object]) -> dict[str, dict[str, object]]:
    raw_items = checkpoint.get("items")
    if not isinstance(raw_items, list) or any(not isinstance(item, Mapping) for item in raw_items):
        raise RuntimeError("checkpoint items must be an array of objects")
    items = [dict(item) for item in raw_items]
    ids = [_clean_id(item.get("id")) for item in items]
    if any(not question_id for question_id in ids) or len(ids) != len(set(ids)):
        raise RuntimeError("checkpoint contains blank or duplicate item ids")
    return {question_id: item for question_id, item in zip(ids, items)}


def _validate_resume_checkpoint(
    checkpoint: dict[str, object],
    *,
    snapshot: Mapping[str, object],
    checkpoint_path: Path,
    output_path: Path,
    report_path: Path,
    selected: Sequence[Mapping[str, object]] | None,
    requested_max_attempts: int | None,
    requested_provider: str,
    requested_provider_runtime: Mapping[str, object] | None,
) -> tuple[list[dict[str, object]], int]:
    if checkpoint.get("schema_version") != CHECKPOINT_SCHEMA:
        raise RuntimeError("checkpoint schema_version is invalid")
    if (
        checkpoint.get("read_only_source") is not True
        or checkpoint.get("database_writes") != 0
        or checkpoint.get("ready_for_publish") is not False
    ):
        raise RuntimeError("checkpoint safety lock is invalid")
    if checkpoint.get("batch_size") != BATCH_SIZE:
        raise RuntimeError("checkpoint batch_size does not match the six-question service")
    checkpoint_provider = str(checkpoint.get("provider") or "").strip()
    if checkpoint_provider not in PROVIDERS:
        raise RuntimeError("checkpoint provider is invalid")
    if checkpoint_provider != requested_provider:
        raise RuntimeError(
            f"--provider does not match checkpoint provider={checkpoint_provider}"
        )
    checkpoint_provider_runtime = checkpoint.get("provider_runtime")
    if not isinstance(checkpoint_provider_runtime, Mapping):
        raise RuntimeError("checkpoint provider runtime is invalid")
    if (
        requested_provider_runtime is not None
        and dict(checkpoint_provider_runtime) != dict(requested_provider_runtime)
    ):
        raise RuntimeError("provider runtime does not match the checkpoint")
    if checkpoint.get("immutable_baseline_fields") != list(IMMUTABLE_BASELINE_FIELDS):
        raise RuntimeError("checkpoint immutable baseline field contract changed")
    artifacts = checkpoint.get("artifacts")
    expected_artifacts = {
        "checkpoint_path": _portable_path(checkpoint_path),
        "candidate_path": _portable_path(output_path),
        "review_report_path": _portable_path(report_path),
    }
    if not isinstance(artifacts, Mapping) or dict(artifacts) != expected_artifacts:
        raise RuntimeError("checkpoint artifact paths do not match this resume command")
    batch_call_count = checkpoint.get("batch_call_count")
    if not isinstance(batch_call_count, int) or batch_call_count < 0:
        raise RuntimeError("checkpoint batch_call_count is invalid")
    batch_events = checkpoint.get("batch_events")
    if not isinstance(batch_events, list) or any(
        not isinstance(event, Mapping) for event in batch_events
    ):
        raise RuntimeError("checkpoint batch_events is invalid")
    static_reaudit_events = checkpoint.get("static_reaudit_events", [])
    if not isinstance(static_reaudit_events, list) or any(
        not isinstance(event, Mapping) for event in static_reaudit_events
    ):
        raise RuntimeError("checkpoint static_reaudit_events is invalid")
    memory_gate_migration_events = checkpoint.get("memory_gate_migration_events", [])
    if not isinstance(memory_gate_migration_events, list) or any(
        not isinstance(event, Mapping) for event in memory_gate_migration_events
    ):
        raise RuntimeError("checkpoint memory_gate_migration_events is invalid")

    source = checkpoint.get("source")
    selection = checkpoint.get("selection")
    if not isinstance(source, Mapping) or not isinstance(selection, Mapping):
        raise RuntimeError("checkpoint source or selection metadata is missing")
    if source.get("raw_file_sha256") != snapshot["raw_file_sha256"]:
        raise RuntimeError("active snapshot raw-file SHA-256 changed; refusing resume")
    if source.get("canonical_json_sha256") != snapshot["canonical_json_sha256"]:
        raise RuntimeError("active snapshot canonical JSON SHA-256 changed; refusing resume")
    if selection.get("subject") != SUBJECT:
        raise RuntimeError("checkpoint subject lock is invalid")

    selected_ids = selection.get("selected_ids")
    if not isinstance(selected_ids, list) or any(not isinstance(item, str) for item in selected_ids):
        raise RuntimeError("checkpoint selected_ids is invalid")
    if len(selected_ids) != len(set(selected_ids)):
        raise RuntimeError("checkpoint selected_ids contains duplicates")
    if selection.get("selected_count") != len(selected_ids):
        raise RuntimeError("checkpoint selected_count does not match selected_ids")
    if selection.get("selected_ids_sha256") != _digest(selected_ids):
        raise RuntimeError("checkpoint selected_ids SHA-256 mismatch")
    if selected is not None:
        requested_selection = [_clean_id(row.get("id")) for row in selected]
        if requested_selection != selected_ids:
            raise RuntimeError("--ids/--limit selection does not match the checkpoint")

    configured_attempts = checkpoint.get("max_attempts_per_question")
    if not isinstance(configured_attempts, int) or not 1 <= configured_attempts <= MAX_ALLOWED_ATTEMPTS:
        raise RuntimeError("checkpoint max_attempts_per_question is invalid")
    if requested_max_attempts is not None and requested_max_attempts != configured_attempts:
        raise RuntimeError("--max-attempts does not match the checkpoint")

    item_map = _checkpoint_item_map(checkpoint)
    if list(item_map) != selected_ids:
        raise RuntimeError("checkpoint item order or ids do not match selection")
    snapshot_by_id = snapshot["by_id"]
    resumed_rows: list[dict[str, object]] = []
    for question_id in selected_ids:
        row = snapshot_by_id.get(question_id)
        if not isinstance(row, Mapping):
            raise RuntimeError(f"checkpoint id is missing from active snapshot: {question_id}")
        if str(row.get("subject") or "").strip() != SUBJECT:
            raise RuntimeError(f"checkpoint id no longer belongs to subject=中华文化: {question_id}")
        item = item_map[question_id]
        if item.get("baseline_sha256") != baseline_sha256(row):
            raise RuntimeError(f"immutable baseline changed for checkpoint id: {question_id}")
        extra_attempts = item.get("migration_extra_attempts_granted", 0)
        if (
            not isinstance(extra_attempts, int)
            or not 0 <= extra_attempts <= MEMORY_GATE_MIGRATION_MAX_EXTRA_ATTEMPTS
        ):
            raise RuntimeError(f"invalid migration attempt grant for checkpoint id: {question_id}")
        attempts = item.get("attempts")
        if (
            not isinstance(attempts, int)
            or attempts < 0
            or attempts > configured_attempts + extra_attempts
        ):
            raise RuntimeError(f"invalid attempt count for checkpoint id: {question_id}")
        state = item.get("state")
        if state not in {"pending", "accepted", "exhausted"}:
            raise RuntimeError(f"invalid checkpoint state for id: {question_id}")
        in_flight = item.get("in_flight")
        if in_flight is not None and not isinstance(in_flight, Mapping):
            raise RuntimeError(f"invalid in_flight marker for checkpoint id: {question_id}")
        if state != "pending" and in_flight is not None:
            raise RuntimeError(f"non-pending checkpoint item is marked in-flight: {question_id}")
        metadata = item.get("culture_v3")
        if state == "accepted" and not isinstance(metadata, Mapping):
            raise RuntimeError(f"accepted checkpoint item lacks culture_v3: {question_id}")
        if state != "accepted" and metadata is not None:
            raise RuntimeError(f"non-accepted checkpoint item contains culture_v3: {question_id}")
        resumed_rows.append(dict(row))
    return resumed_rows, configured_attempts


def _immutable_changes(
    original: Mapping[str, object],
    returned: Mapping[str, object],
) -> list[str]:
    return [
        field
        for field in IMMUTABLE_BASELINE_FIELDS
        if returned.get(field) != original.get(field)
    ]


def _clean_list(value: object, *, fallback: str) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return [fallback]
    cleaned: list[str] = []
    for item in value:
        text = re.sub(r"\s+", " ", str(item or "")).strip()[:240]
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned or [fallback]


def _normalize_batch_result(
    result: Mapping[str, object],
    batch_rows: Sequence[Mapping[str, object]],
) -> tuple[
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
    list[dict[str, object]],
]:
    raw_accepted = result.get("accepted")
    raw_rejected = result.get("rejected")
    if not isinstance(raw_accepted, list) or not isinstance(raw_rejected, list):
        raise ValueError("batch result must contain accepted and rejected arrays")

    batch_by_id = {_clean_id(row.get("id")): row for row in batch_rows}
    accepted: dict[str, dict[str, object]] = {}
    rejected: dict[str, dict[str, object]] = {}
    protocol_issues: list[dict[str, object]] = []

    def reject(question_id: str, code: str, reason: str) -> None:
        bucket = rejected.setdefault(question_id, {"id": question_id, "codes": [], "reasons": []})
        if code not in bucket["codes"]:
            bucket["codes"].append(code)
        if reason not in bucket["reasons"]:
            bucket["reasons"].append(reason)

    for position, raw in enumerate(raw_accepted, start=1):
        if not isinstance(raw, Mapping):
            protocol_issues.append(
                {"position": position, "code": "regeneration_accepted_not_object"}
            )
            continue
        question_id = _clean_id(raw.get("id"))
        if question_id not in batch_by_id:
            protocol_issues.append(
                {
                    "position": position,
                    "id": question_id,
                    "code": "regeneration_accepted_unknown_id",
                }
            )
            continue
        if question_id in accepted:
            accepted.pop(question_id, None)
            reject(
                question_id,
                "regeneration_duplicate_accepted_id",
                "同一 id 在 accepted 中重复出现",
            )
            continue
        metadata = raw.get("culture_v3")
        audit = raw.get("audit")
        returned_question = raw.get("question")
        if not isinstance(metadata, Mapping):
            reject(question_id, "regeneration_missing_culture_v3", "accepted 项缺少 culture_v3")
            continue
        audit_blocking_codes = audit.get("blocking_codes") if isinstance(audit, Mapping) else None
        audit_issues = audit.get("issues") if isinstance(audit, Mapping) else None
        blocking_issue_present = bool(
            isinstance(audit_issues, list)
            and any(
                isinstance(issue, Mapping)
                and str(issue.get("severity") or "").strip().lower() in {"critical", "high"}
                for issue in audit_issues
            )
        )
        if (
            not isinstance(audit, Mapping)
            or audit.get("valid_for_generation") is not True
            or not isinstance(audit_blocking_codes, list)
            or bool(audit_blocking_codes)
            or not isinstance(audit_issues, list)
            or blocking_issue_present
        ):
            reject(
                question_id,
                "regeneration_static_gate_not_passed",
                "accepted 项未以严格布尔值和空阻断项证明通过确定性静态质量门",
            )
            continue
        if not isinstance(returned_question, Mapping):
            reject(
                question_id,
                "regeneration_missing_rendered_question",
                "accepted 项缺少用于不可变字段复核的 question",
            )
            continue
        changed = _immutable_changes(batch_by_id[question_id], returned_question)
        if changed:
            reject(
                question_id,
                "regeneration_immutable_field_changed",
                "返回结果改动了不可变字段：" + "、".join(changed),
            )
            continue
        accepted[question_id] = {
            "id": question_id,
            "culture_v3": dict(metadata),
            "audit": {
                "valid_for_generation": True,
                "blocking_codes": [],
                "issue_count": len(audit_issues),
            },
        }

    for position, raw in enumerate(raw_rejected, start=1):
        if not isinstance(raw, Mapping):
            protocol_issues.append(
                {"position": position, "code": "regeneration_rejected_not_object"}
            )
            continue
        question_id = _clean_id(raw.get("id"))
        if question_id not in batch_by_id:
            protocol_issues.append(
                {
                    "position": position,
                    "id": question_id,
                    "code": "regeneration_rejected_unknown_id",
                }
            )
            continue
        codes = _clean_list(raw.get("codes"), fallback="regeneration_static_gate_rejected")
        reasons = _clean_list(raw.get("reasons"), fallback="确定性静态质量门未通过")
        for code in codes:
            reject(question_id, code, reasons[0])
        for reason in reasons[1:]:
            reject(question_id, codes[0], reason)
        rejected_metadata = raw.get("culture_v3")
        if isinstance(rejected_metadata, Mapping):
            rejected[question_id]["culture_v3"] = dict(rejected_metadata)

    for question_id in list(accepted):
        if question_id in rejected:
            accepted.pop(question_id, None)
            reject(
                question_id,
                "regeneration_conflicting_result",
                "同一 id 同时出现在 accepted 和 rejected 中",
            )
    for question_id in batch_by_id:
        if question_id not in accepted and question_id not in rejected:
            reject(
                question_id,
                "regeneration_missing_batch_result",
                "批响应没有给出该固定题目的有效结果",
            )
    return accepted, rejected, protocol_issues


def _merge_feedback(existing: Sequence[object], new: Sequence[object]) -> list[str]:
    merged: list[str] = []
    for value in (*existing, *new):
        text = re.sub(r"\s+", " ", str(value or "")).strip()[:240]
        if text and text not in merged:
            merged.append(text)
        if len(merged) >= 10:
            break
    return merged


def _failure_category(codes: Sequence[str]) -> str:
    if "regeneration_interrupted_attempt" in codes:
        return "interrupted_attempt"
    if "regeneration_batch_call_failed" in codes:
        return "batch_call_failed"
    if any(
        code.startswith("culture_v3_") or code == "regeneration_static_gate_not_passed"
        for code in codes
    ):
        return "static_gate_failed"
    return "generation_contract_failed"


def _attempt_ceiling(item: Mapping[str, object], max_attempts: int) -> int:
    extra = item.get("migration_extra_attempts_granted", 0)
    if not isinstance(extra, int) or not 0 <= extra <= MEMORY_GATE_MIGRATION_MAX_EXTRA_ATTEMPTS:
        raise RuntimeError(f"invalid migration attempt grant for id: {item.get('id')}")
    return max_attempts + extra


def _apply_failure(
    item: dict[str, object],
    rejection: Mapping[str, object],
    *,
    max_attempts: int,
) -> None:
    codes = _clean_list(rejection.get("codes"), fallback="regeneration_failed")
    reasons = _clean_list(rejection.get("reasons"), fallback="解析候选未通过")
    failures = item.setdefault("failures", [])
    if not isinstance(failures, list):
        raise RuntimeError(f"checkpoint failures is invalid for id: {item.get('id')}")
    failures.append(
        {
            "attempt": item["attempts"],
            "codes": codes,
            "reasons": reasons,
        }
    )
    category = _failure_category(codes)
    generated_feedback = []
    if category == "static_gate_failed":
        generated_feedback = feedback_by_id_from_rejections(
            [{"id": item["id"], "reasons": reasons}]
        ).get(str(item["id"]), [])
    existing_feedback = item.get("feedback")
    if not isinstance(existing_feedback, list):
        existing_feedback = []
    item["feedback"] = _merge_feedback(existing_feedback, generated_feedback)
    item["last_failure_codes"] = codes
    item["last_failure_category"] = category
    exhausted = int(item["attempts"]) >= _attempt_ceiling(item, max_attempts)
    item["state"] = "exhausted" if exhausted else "pending"
    item["terminal_category"] = category if exhausted else None
    item["culture_v3"] = None
    item["audit"] = None
    rejected_metadata = rejection.get("culture_v3")
    if isinstance(rejected_metadata, Mapping):
        item["last_rejected_culture_v3"] = dict(rejected_metadata)
    elif category == "static_gate_failed":
        # A static-gate failure describes the current candidate.  If that
        # candidate is absent, do not keep an older candidate under the newer
        # static-failure audit record.
        item["last_rejected_culture_v3"] = None
    else:
        # Provider, protocol and interrupted failures have no newer candidate
        # to replace an earlier static-gate rejection.  Preserve that exact
        # payload so a later deterministic re-audit can still inspect it.
        item.setdefault("last_rejected_culture_v3", None)
    item["in_flight"] = None


def _mark_retry_ceiling(checkpoint: dict[str, object], max_attempts: int) -> None:
    for item in checkpoint["items"]:
        if (
            item.get("state") == "pending"
            and int(item.get("attempts") or 0) >= _attempt_ceiling(item, max_attempts)
        ):
            item["state"] = "exhausted"
            item["terminal_category"] = (
                item.get("last_failure_category") or "retry_ceiling_without_result"
            )


def _recover_interrupted_attempts(
    checkpoint: dict[str, object],
    *,
    max_attempts: int,
) -> int:
    """Turn pre-call reservations left by a hard stop into audited failures."""

    recovered = 0
    events_by_call = {
        event.get("call_index"): event
        for event in checkpoint.get("batch_events", [])
        if isinstance(event, dict)
    }
    for item in checkpoint["items"]:
        marker = item.get("in_flight")
        if item.get("state") != "pending" or not isinstance(marker, Mapping):
            continue
        call_index = marker.get("call_index")
        _apply_failure(
            item,
            {
                "id": item["id"],
                "codes": ["regeneration_interrupted_attempt"],
                "reasons": ["上一轮调用在候选返回前中断；该次尝试已保守计入上限"],
            },
            max_attempts=max_attempts,
        )
        event = events_by_call.get(call_index)
        if isinstance(event, dict) and event.get("status") == "in_flight":
            event["status"] = "interrupted"
            rejected_ids = event.setdefault("rejected_ids", [])
            if item["id"] not in rejected_ids:
                rejected_ids.append(item["id"])
            event["interrupted_recovered_at"] = _now()
        recovered += 1
    if recovered:
        checkpoint["recovered_interrupted_attempt_count"] = int(
            checkpoint.get("recovered_interrupted_attempt_count") or 0
        ) + recovered
        checkpoint["updated_at"] = _now()
    return recovered


def _reaudit_saved_candidates(
    checkpoint: dict[str, object],
    *,
    selected_by_id: Mapping[str, Mapping[str, object]],
    include_accepted: bool = False,
) -> dict[str, int]:
    """Re-run the current deterministic gate without spending a model attempt.

    By default this is limited to exhausted static-gate failures that retain the
    exact rejected ``culture_v3`` payload.  ``include_accepted`` also checks saved
    accepted candidates after a deterministic-gate change and demotes stale
    candidates that no longer pass.  A later provider, protocol or interrupted
    failure may be the terminal event, but an exact candidate saved by an earlier
    static-gate failure remains eligible.  Previous attempts, failures and the
    true terminal category remain auditable.
    """

    events = checkpoint.setdefault("static_reaudit_events", [])
    if not isinstance(events, list):
        raise RuntimeError("checkpoint static_reaudit_events is invalid")

    counts = {"checked": 0, "passed": 0, "promoted": 0, "demoted": 0, "failed": 0}
    for item in checkpoint["items"]:
        failures = item.get("failures")
        has_historical_static_failure = bool(
            isinstance(failures, list)
            and any(
                isinstance(failure, Mapping)
                and _failure_category(
                    _clean_list(failure.get("codes"), fallback="regeneration_failed")
                )
                == "static_gate_failed"
                for failure in failures
            )
        )
        saved_rejection = bool(
            item.get("state") == "exhausted"
            and isinstance(item.get("last_rejected_culture_v3"), Mapping)
            and (
                item.get("terminal_category") == "static_gate_failed"
                or has_historical_static_failure
            )
        )
        saved_acceptance = bool(
            include_accepted
            and item.get("state") == "accepted"
            and isinstance(item.get("culture_v3"), Mapping)
        )
        if not (saved_rejection or saved_acceptance):
            continue

        question_id = str(item["id"])
        row = selected_by_id.get(question_id)
        if not isinstance(row, Mapping):
            raise RuntimeError(f"reaudit id is missing from selected baseline: {question_id}")
        previous_state = str(item.get("state"))
        metadata_source = "culture_v3" if saved_acceptance else "last_rejected_culture_v3"
        metadata = dict(item[metadata_source])
        event: dict[str, object] = {
            "id": question_id,
            "reaudited_at": _now(),
            "source": metadata_source,
            "metadata_sha256": _digest(metadata),
            "attempts_preserved": int(item.get("attempts") or 0),
            "provider_calls": 0,
            "previous_state": previous_state,
            "previous_terminal_category": item.get("terminal_category"),
            "result": "failed",
            "codes": [],
            "reasons": [],
        }
        counts["checked"] += 1
        try:
            parsed = parse_culture_explanation_regeneration_response(
                json.dumps(
                    {"updates": [{"id": question_id, "culture_v3": metadata}]},
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                {question_id: row},
            )
            accepted, rejected, protocol_issues = _normalize_batch_result(parsed, [row])
        except Exception as exc:
            event["codes"] = ["regeneration_static_reaudit_error"]
            event["reasons"] = [
                re.sub(r"\s+", " ", f"{type(exc).__name__}: {exc}").strip()[:240]
                or "保存候选复审失败"
            ]
            events.append(event)
            counts["failed"] += 1
            continue

        event["protocol_issues"] = protocol_issues
        accepted_item = accepted.get(question_id)
        if accepted_item is None:
            rejection = rejected.get(
                question_id,
                {
                    "codes": ["regeneration_static_reaudit_rejected"],
                    "reasons": ["保存候选仍未通过当前静态质量门"],
                },
            )
            event["codes"] = _clean_list(
                rejection.get("codes"), fallback="regeneration_static_reaudit_rejected"
            )
            event["reasons"] = _clean_list(
                rejection.get("reasons"), fallback="保存候选仍未通过当前静态质量门"
            )
            if saved_acceptance:
                item["state"] = "exhausted"
                item["culture_v3"] = None
                item["audit"] = None
                item["last_rejected_culture_v3"] = metadata
                item["last_failure_codes"] = list(event["codes"])
                item["last_failure_category"] = "static_gate_failed"
                item["terminal_category"] = "static_gate_failed"
                item["in_flight"] = None
                item["accepted_via"] = None
                item["static_reaudited_at"] = event["reaudited_at"]
                item.pop("accepted_at", None)
                generated_feedback = feedback_by_id_from_rejections(
                    [{"id": question_id, "reasons": event["reasons"]}]
                ).get(question_id, [])
                item["feedback"] = _merge_feedback(
                    item.get("feedback") if isinstance(item.get("feedback"), list) else [],
                    generated_feedback,
                )
                event["result"] = "demoted"
                counts["demoted"] += 1
            else:
                counts["failed"] += 1
            events.append(event)
            continue

        was_rejected = saved_rejection
        item["state"] = "accepted"
        item["culture_v3"] = accepted_item["culture_v3"]
        item["audit"] = accepted_item["audit"]
        item["model"] = checkpoint.get("provider")
        item["last_failure_codes"] = []
        item["last_failure_category"] = None
        item["terminal_category"] = None
        item["in_flight"] = None
        item["last_rejected_culture_v3"] = None
        if was_rejected:
            item["accepted_at"] = _now()
            item["accepted_via"] = "saved_candidate_static_reaudit"
        item["static_reaudited_at"] = event["reaudited_at"]
        event["result"] = "passed"
        events.append(event)
        counts["passed"] += 1
        if was_rejected:
            counts["promoted"] += 1

    if counts["checked"]:
        checkpoint["updated_at"] = _now()
    return counts


def _requeue_memory_gate_only_failures(
    checkpoint: dict[str, object],
    *,
    events_start_index: int,
    max_attempts: int,
) -> dict[str, int]:
    """Requeue only candidates newly blocked by the memory-value gate.

    Existing attempts and failure history remain untouched. Questions already
    at the normal ceiling receive one auditable migration attempt, without
    changing the checkpoint-wide retry limit.
    """

    reaudit_events = checkpoint.get("static_reaudit_events", [])
    migration_events = checkpoint.setdefault("memory_gate_migration_events", [])
    if not isinstance(reaudit_events, list) or not isinstance(migration_events, list):
        raise RuntimeError("checkpoint migration audit arrays are invalid")
    already_migrated = {
        str(event.get("id"))
        for event in migration_events
        if isinstance(event, Mapping) and event.get("result") == "requeued"
    }
    items_by_id = {str(item["id"]): item for item in checkpoint["items"]}
    counts = {"eligible": 0, "requeued": 0, "extra_attempt_granted": 0, "skipped": 0}

    for reaudit_event in reaudit_events[events_start_index:]:
        if not isinstance(reaudit_event, Mapping):
            continue
        codes = _clean_list(
            reaudit_event.get("codes"), fallback="regeneration_static_reaudit_rejected"
        )
        if set(codes) != {MEMORY_GATE_REQUIRED_CODE}:
            continue
        question_id = str(reaudit_event.get("id") or "")
        counts["eligible"] += 1
        item = items_by_id.get(question_id)
        migration_event: dict[str, object] = {
            "id": question_id,
            "migrated_at": _now(),
            "reason_code": MEMORY_GATE_REQUIRED_CODE,
            "source_reaudit_result": reaudit_event.get("result"),
            "attempts_preserved": int(item.get("attempts") or 0) if item else None,
            "failure_count_preserved": len(item.get("failures") or []) if item else None,
            "checkpoint_max_attempts_unchanged": max_attempts,
            "provider_calls": 0,
            "extra_attempt_granted": 0,
            "result": "skipped",
        }
        if item is None or item.get("state") != "exhausted" or question_id in already_migrated:
            migration_event["skip_reason"] = (
                "already_migrated"
                if question_id in already_migrated
                else "candidate_not_exhausted"
            )
            migration_events.append(migration_event)
            counts["skipped"] += 1
            continue

        attempts = int(item.get("attempts") or 0)
        current_grant = int(item.get("migration_extra_attempts_granted") or 0)
        if attempts >= max_attempts and current_grant == 0:
            item["migration_extra_attempts_granted"] = 1
            migration_event["extra_attempt_granted"] = 1
            counts["extra_attempt_granted"] += 1
        if attempts >= _attempt_ceiling(item, max_attempts):
            migration_event["skip_reason"] = "migration_attempt_ceiling_reached"
            migration_events.append(migration_event)
            counts["skipped"] += 1
            continue

        reasons = _clean_list(
            reaudit_event.get("reasons"), fallback="本题缺少有价值的记忆方法"
        )
        generated_feedback = feedback_by_id_from_rejections(
            [{"id": question_id, "reasons": reasons}]
        ).get(question_id, [])
        item["state"] = "pending"
        item["terminal_category"] = None
        item["in_flight"] = None
        item["feedback"] = _merge_feedback(
            item.get("feedback") if isinstance(item.get("feedback"), list) else [],
            generated_feedback,
        )
        item["memory_gate_migration_pending"] = True
        migration_event["result"] = "requeued"
        migration_events.append(migration_event)
        already_migrated.add(question_id)
        counts["requeued"] += 1

    if counts["eligible"]:
        checkpoint["updated_at"] = _now()
    return counts


def _candidate_payload(
    checkpoint: Mapping[str, object],
    *,
    output_path: Path,
    report_path: Path,
) -> dict[str, object]:
    items = checkpoint["items"]
    updates = [
        {"id": item["id"], "culture_v3": item["culture_v3"]}
        for item in items
        if item.get("state") == "accepted"
    ]
    if any(set(update) != {"id", "culture_v3"} for update in updates):
        raise RuntimeError("candidate update contract was widened")
    selected_count = len(items)
    exhausted_count = sum(item.get("state") == "exhausted" for item in items)
    static_failed_count = sum(
        item.get("state") == "exhausted"
        and item.get("terminal_category") == "static_gate_failed"
        for item in items
    )
    static_not_reached_count = sum(
        item.get("state") == "exhausted"
        and item.get("terminal_category") != "static_gate_failed"
        for item in items
    )
    return {
        "schema_version": CANDIDATE_SCHEMA,
        "generated_at": _now(),
        "scope": "中华文化 active 固定题目解析 V3 离线候选",
        "source": checkpoint["source"],
        "selection": checkpoint["selection"],
        "immutable_baseline_fields": list(IMMUTABLE_BASELINE_FIELDS),
        "batch_size": BATCH_SIZE,
        "provider": checkpoint["provider"],
        "provider_runtime": checkpoint["provider_runtime"],
        "max_attempts_per_question": checkpoint["max_attempts_per_question"],
        "candidate_path": _portable_path(output_path),
        "review_report_path": _portable_path(report_path),
        "read_only_source": True,
        "database_writes": 0,
        "ready_for_publish": False,
        "complete": not any(item.get("state") == "pending" for item in items),
        "completed_with_rejections": exhausted_count > 0,
        "selected_count": selected_count,
        "accepted_count": len(updates),
        "rejected_count": exhausted_count,
        "review_gates": {
            "static_gate": {
                "passed_count": len(updates),
                "failed_count": static_failed_count,
                "not_reached_count": static_not_reached_count,
            },
            "blind_answer_review": "pending",
            "teaching_review": "pending",
            "user_review": "pending",
        },
        "updates_sha256": _digest(updates),
        "updates": updates,
    }


def _review_payload(
    checkpoint: Mapping[str, object],
    candidate: Mapping[str, object],
    *,
    checkpoint_path: Path,
    output_path: Path,
) -> dict[str, object]:
    items = checkpoint["items"]
    states = Counter(str(item.get("state")) for item in items)
    terminal_categories = Counter(
        str(item.get("terminal_category"))
        for item in items
        if item.get("state") == "exhausted"
    )
    replayed_ids = {
        str(question_id)
        for event in checkpoint.get("batch_events", [])
        if isinstance(event, Mapping)
        for question_id in event.get("feedback_ids", [])
    }
    feedback_replay_count = sum(
        len(event.get("feedback_ids", []))
        for event in checkpoint.get("batch_events", [])
        if isinstance(event, Mapping) and isinstance(event.get("feedback_ids", []), list)
    )
    immutable_failure_count = sum(
        "regeneration_immutable_field_changed" in failure.get("codes", [])
        for item in items
        for failure in item.get("failures", [])
    )
    report_items = []
    for index, item in enumerate(items, start=1):
        audit = item.get("audit") if isinstance(item.get("audit"), Mapping) else {}
        report_items.append(
            {
                "index": index,
                "id": item["id"],
                "baseline_sha256": item["baseline_sha256"],
                "baseline_verified": bool(item.get("baseline_verified")),
                "state": item["state"],
                "attempts": item["attempts"],
                "migration_extra_attempts_granted": int(
                    item.get("migration_extra_attempts_granted") or 0
                ),
                "memory_gate_migration_pending": bool(
                    item.get("memory_gate_migration_pending")
                ),
                "static_gate": (
                    "passed"
                    if item["state"] == "accepted"
                    else "failed"
                    if item.get("terminal_category") == "static_gate_failed"
                    else "not_reached"
                ),
                "terminal_category": item.get("terminal_category"),
                "retry_feedback": list(item.get("feedback") or []),
                "failure_count": len(item.get("failures") or []),
                "failures": list(item.get("failures") or []),
                "audit": dict(audit),
                "model": item.get("model"),
                "accepted_via": item.get("accepted_via"),
                "last_rejected_culture_v3": (
                    item.get("last_rejected_culture_v3")
                    if item.get("state") == "exhausted"
                    else None
                ),
            }
        )
    selected_ids = [str(item["id"]) for item in items]
    return {
        "schema_version": REVIEW_SCHEMA,
        "generated_at": _now(),
        "scope": "中华文化 active 固定题目解析 V3 离线候选审核",
        "source": checkpoint["source"],
        "selection": checkpoint["selection"],
        "checkpoint_path": _portable_path(checkpoint_path),
        "candidate_path": _portable_path(output_path),
        "read_only_source": True,
        "database_writes": 0,
        "ready_for_publish": False,
        "candidate_contract": {
            "root_updates": True,
            "allowed_update_fields": ["id", "culture_v3"],
            "updates_sha256": candidate["updates_sha256"],
        },
        "provider": checkpoint["provider"],
        "provider_runtime": checkpoint["provider_runtime"],
        "baseline_lock": {
            "immutable_fields": list(IMMUTABLE_BASELINE_FIELDS),
            "snapshot_raw_file_sha256": checkpoint["source"]["raw_file_sha256"],
            "snapshot_canonical_json_sha256": checkpoint["source"]["canonical_json_sha256"],
            "immutable_field_failure_count": immutable_failure_count,
        },
        "index_id_integrity": {
            "expected_count": checkpoint["selection"]["selected_count"],
            "actual_count": len(items),
            "indices_1_to_n": True,
            "ids_nonempty": all(selected_ids),
            "ids_unique": len(selected_ids) == len(set(selected_ids)),
            "selected_ids_sha256": _digest(selected_ids),
        },
        "summary": {
            "selected_count": len(items),
            "accepted_count": states["accepted"],
            "rejected_count": states["exhausted"],
            "pending_count": states["pending"],
            "total_attempts": sum(int(item.get("attempts") or 0) for item in items),
            "batch_call_count": checkpoint["batch_call_count"],
            "recovered_interrupted_attempt_count": checkpoint.get(
                "recovered_interrupted_attempt_count", 0
            ),
            "static_reaudit_event_count": len(checkpoint.get("static_reaudit_events", [])),
            "static_reaudit_passed_count": sum(
                event.get("result") == "passed"
                for event in checkpoint.get("static_reaudit_events", [])
                if isinstance(event, Mapping)
            ),
            "static_reaudit_failed_count": sum(
                event.get("result") != "passed"
                for event in checkpoint.get("static_reaudit_events", [])
                if isinstance(event, Mapping)
            ),
            "static_reaudit_demoted_count": sum(
                event.get("result") == "demoted"
                for event in checkpoint.get("static_reaudit_events", [])
                if isinstance(event, Mapping)
            ),
            "memory_gate_migration_event_count": len(
                checkpoint.get("memory_gate_migration_events", [])
            ),
            "memory_gate_migration_requeued_count": sum(
                event.get("result") == "requeued"
                for event in checkpoint.get("memory_gate_migration_events", [])
                if isinstance(event, Mapping)
            ),
            "memory_gate_migration_extra_attempt_granted_count": sum(
                int(event.get("extra_attempt_granted") or 0)
                for event in checkpoint.get("memory_gate_migration_events", [])
                if isinstance(event, Mapping)
            ),
            "retried_question_count": sum(int(item.get("attempts") or 0) > 1 for item in items),
            "feedback_replayed_count": feedback_replay_count,
            "feedback_replayed_question_count": len(replayed_ids),
            "feedback_replayed_ids": sorted(replayed_ids),
            "terminal_category_counts": dict(terminal_categories),
        },
        "review_gates": candidate["review_gates"],
        "items": report_items,
    }


def _validate_output_paths(
    snapshot_path: Path,
    checkpoint_path: Path,
    output_path: Path,
    report_path: Path,
) -> None:
    resolved = [path.resolve() for path in (snapshot_path, checkpoint_path, output_path, report_path)]
    if len(resolved) != len(set(resolved)):
        raise ValueError("snapshot, checkpoint, candidate and report paths must be distinct")


def _validate_limited_run_artifacts(
    *,
    requested_ids: Sequence[str] | None,
    limit: int | None,
    checkpoint_path: Path,
    output_path: Path,
    report_path: Path,
) -> None:
    """Keep smoke or focused selections away from the full-bank artifacts."""

    if requested_ids is None and limit is None:
        return
    configured = (checkpoint_path.resolve(), output_path.resolve(), report_path.resolve())
    defaults = (CHECKPOINT_PATH.resolve(), CANDIDATE_PATH.resolve(), REVIEW_REPORT_PATH.resolve())
    reused = [name for name, actual, default in zip(("checkpoint", "output", "report"), configured, defaults) if actual == default]
    if reused:
        raise ValueError(
            "--ids/--limit requires independent artifact paths; default paths reused: "
            + ", ".join(reused)
        )


async def _run_regeneration_locked(
    *,
    snapshot_path: Path = SNAPSHOT_PATH,
    checkpoint_path: Path = CHECKPOINT_PATH,
    output_path: Path = CANDIDATE_PATH,
    report_path: Path = REVIEW_REPORT_PATH,
    requested_ids: Sequence[str] | None = None,
    limit: int | None = None,
    resume: bool = False,
    max_attempts: int | None = None,
    provider: str = DEFAULT_PROVIDER,
    batch_generator: BatchGenerator | None = None,
    reaudit_rejected: bool = False,
    reaudit_all: bool = False,
    migrate_memory_gate: bool = False,
) -> tuple[dict[str, object], dict[str, object]]:
    """Generate candidates and a review report without any database writes."""

    snapshot_path = snapshot_path.resolve()
    checkpoint_path = checkpoint_path.resolve()
    output_path = output_path.resolve()
    report_path = report_path.resolve()
    _validate_output_paths(snapshot_path, checkpoint_path, output_path, report_path)

    if provider not in PROVIDERS:
        raise ValueError(f"--provider must be one of: {', '.join(PROVIDERS)}")
    if migrate_memory_gate and (reaudit_rejected or reaudit_all):
        raise ValueError("--migrate-memory-gate cannot be combined with other re-audit modes")
    reaudit_only = reaudit_rejected or reaudit_all or migrate_memory_gate
    if reaudit_only and not resume:
        raise ValueError("re-audit or migration mode requires --resume")
    provider_runtime: dict[str, object] | None = None if reaudit_only else {}
    if provider == "codex-cli" and batch_generator is None and not reaudit_only:
        preflight = preflight_culture_explanation_codex_cli()
        provider_runtime = {"codex_cli_version": preflight["version"]}
    if max_attempts is not None and not 1 <= max_attempts <= MAX_ALLOWED_ATTEMPTS:
        raise ValueError(f"--max-attempts must be between 1 and {MAX_ALLOWED_ATTEMPTS}")
    snapshot = _load_snapshot(snapshot_path)

    if resume:
        if not checkpoint_path.is_file():
            raise RuntimeError(f"--resume checkpoint is missing: {_portable_path(checkpoint_path)}")
        checkpoint = _read_json(checkpoint_path)
        if not isinstance(checkpoint, dict):
            raise RuntimeError("checkpoint root must be an object")
        explicit_selection = None
        if requested_ids is not None or limit is not None:
            explicit_selection = _select_questions(
                snapshot,
                requested_ids=requested_ids,
                limit=limit,
            )
        selected, configured_attempts = _validate_resume_checkpoint(
            checkpoint,
            snapshot=snapshot,
            checkpoint_path=checkpoint_path,
            output_path=output_path,
            report_path=report_path,
            selected=explicit_selection,
            requested_max_attempts=max_attempts,
            requested_provider=provider,
            requested_provider_runtime=provider_runtime,
        )
        max_attempts = configured_attempts
    else:
        if checkpoint_path.exists():
            raise RuntimeError(
                f"checkpoint already exists; use --resume or a different path: {_portable_path(checkpoint_path)}"
            )
        if output_path.exists() or report_path.exists():
            raise RuntimeError("candidate or review report already exists; use distinct output paths")
        max_attempts = max_attempts or DEFAULT_MAX_ATTEMPTS
        assert provider_runtime is not None
        selected = _select_questions(
            snapshot,
            requested_ids=requested_ids,
            limit=limit,
        )
        checkpoint = _new_checkpoint(
            snapshot_path=snapshot_path,
            checkpoint_path=checkpoint_path,
            output_path=output_path,
            report_path=report_path,
            snapshot=snapshot,
            selected=selected,
            requested_ids=requested_ids,
            limit=limit,
            max_attempts=max_attempts,
            provider=provider,
            provider_runtime=provider_runtime,
        )
        atomic_write_json(checkpoint_path, checkpoint)

    assert max_attempts is not None
    selected_by_id = {_clean_id(row.get("id")): row for row in selected}
    checkpoint_changed = bool(
        _recover_interrupted_attempts(checkpoint, max_attempts=max_attempts)
    )
    if reaudit_only:
        events_start_index = len(checkpoint.get("static_reaudit_events", []))
        _reaudit_saved_candidates(
            checkpoint,
            selected_by_id=selected_by_id,
            include_accepted=reaudit_all or migrate_memory_gate,
        )
        if migrate_memory_gate:
            _requeue_memory_gate_only_failures(
                checkpoint,
                events_start_index=events_start_index,
                max_attempts=max_attempts,
            )
        checkpoint_changed = True
    if checkpoint_changed:
        atomic_write_json(checkpoint_path, checkpoint)

    generator = None if reaudit_only else (batch_generator or _generator_for_provider(provider))

    checkpoint["run_status"] = "in_progress"
    checkpoint["pause_reason"] = None
    provider_error_reason: str | None = None
    while not reaudit_only:
        _mark_retry_ceiling(checkpoint, max_attempts)
        eligible = [
            item
            for item in checkpoint["items"]
            if item.get("state") == "pending"
            and int(item.get("attempts") or 0) < _attempt_ceiling(item, max_attempts)
        ]
        if not eligible:
            break
        batch_items = eligible[:BATCH_SIZE]
        batch_rows = [selected_by_id[str(item["id"])] for item in batch_items]

        for item, row in zip(batch_items, batch_rows):
            current_baseline = baseline_sha256(row)
            if current_baseline != item.get("baseline_sha256"):
                raise RuntimeError(f"immutable baseline changed during run for id: {item['id']}")
            item["baseline_verified"] = True
            item["attempts"] = int(item.get("attempts") or 0) + 1

        checkpoint["batch_call_count"] = int(checkpoint.get("batch_call_count") or 0) + 1
        call_index = int(checkpoint["batch_call_count"])
        feedback = {
            str(item["id"]): list(item.get("feedback") or [])
            for item in batch_items
            if item.get("feedback")
        }
        event: dict[str, object] = {
            "call_index": call_index,
            "status": "in_flight",
            "ids": [str(item["id"]) for item in batch_items],
            "attempts": {str(item["id"]): item["attempts"] for item in batch_items},
            "feedback_ids": sorted(feedback),
            "accepted_ids": [],
            "rejected_ids": [],
            "protocol_issues": [],
            "model": None,
        }
        checkpoint["batch_events"].append(event)
        for item in batch_items:
            item["in_flight"] = {
                "call_index": call_index,
                "attempt": item["attempts"],
                "reserved_at": _now(),
            }
        checkpoint["updated_at"] = _now()
        # Count the attempt and persist its in-flight audit event before the
        # external call.  A hard interruption is recovered explicitly later.
        atomic_write_json(checkpoint_path, checkpoint)

        try:
            assert generator is not None
            result = await generator(batch_rows, feedback_by_id=feedback)
        except CodexCLIOutputError as exc:
            reason = re.sub(r"\s+", " ", f"{type(exc).__name__}: {exc}").strip()[:240]
            rejections = {
                str(item["id"]): {
                    "id": item["id"],
                    "codes": ["regeneration_provider_output_invalid"],
                    "reasons": [reason or "模型输出不符合固定解析协议"],
                }
                for item in batch_items
            }
            accepted = {}
            protocol_issues = []
            event["batch_error"] = reason
            event["status"] = "output_invalid"
        except Exception as exc:
            reason = re.sub(r"\s+", " ", f"{type(exc).__name__}: {exc}").strip()[:240]
            provider_error_reason = reason or "批生成调用失败"
            rejections = {
                str(item["id"]): {
                    "id": item["id"],
                    "codes": ["regeneration_batch_call_failed"],
                    "reasons": [reason or "批生成调用失败"],
                }
                for item in batch_items
            }
            accepted: dict[str, dict[str, object]] = {}
            protocol_issues: list[dict[str, object]] = []
            event["batch_error"] = reason
            event["status"] = "call_failed"
        else:
            try:
                if not isinstance(result, Mapping):
                    raise ValueError("batch generator returned a non-object result")
                accepted, rejections, protocol_issues = _normalize_batch_result(result, batch_rows)
                event["model"] = result.get("model")
                event["status"] = "completed"
            except Exception as exc:
                reason = re.sub(r"\s+", " ", f"{type(exc).__name__}: {exc}").strip()[:240]
                accepted = {}
                protocol_issues = []
                rejections = {
                    str(item["id"]): {
                        "id": item["id"],
                        "codes": ["regeneration_batch_result_invalid"],
                        "reasons": [reason or "批生成结果结构无效"],
                    }
                    for item in batch_items
                }
                event["batch_error"] = reason
                event["status"] = "result_invalid"

        for item in batch_items:
            question_id = str(item["id"])
            if question_id in accepted:
                accepted_item = accepted[question_id]
                item["state"] = "accepted"
                item["culture_v3"] = accepted_item["culture_v3"]
                item["audit"] = accepted_item["audit"]
                item["model"] = event.get("model")
                item["last_failure_codes"] = []
                item["last_failure_category"] = None
                item["terminal_category"] = None
                item["in_flight"] = None
                item["last_rejected_culture_v3"] = None
                item["accepted_at"] = _now()
                item["memory_gate_migration_pending"] = False
                event["accepted_ids"].append(question_id)
            else:
                rejection = rejections[question_id]
                _apply_failure(item, rejection, max_attempts=max_attempts)
                event["rejected_ids"].append(question_id)
        event["protocol_issues"] = protocol_issues
        event["completed_at"] = _now()
        checkpoint["updated_at"] = _now()
        atomic_write_json(checkpoint_path, checkpoint)
        if provider_error_reason is not None:
            break

    _mark_retry_ceiling(checkpoint, max_attempts)
    pending_count = sum(item.get("state") == "pending" for item in checkpoint["items"])
    exhausted_count = sum(item.get("state") == "exhausted" for item in checkpoint["items"])
    checkpoint["run_status"] = "completed_with_rejections" if exhausted_count else "completed"
    if pending_count:
        if migrate_memory_gate:
            checkpoint["run_status"] = "paused_memory_gate_migration"
        elif reaudit_only:
            checkpoint["run_status"] = "paused_reaudit_only"
        else:
            checkpoint["run_status"] = (
                "paused_provider_error" if provider_error_reason is not None else "in_progress"
            )
    checkpoint["pause_reason"] = (
        "memory-value gate migration completed without provider calls"
        if migrate_memory_gate and pending_count
        else "reaudit-only mode completed without provider calls"
        if reaudit_only and pending_count
        else provider_error_reason
    )
    checkpoint["completed_at"] = _now() if not pending_count else None
    checkpoint["updated_at"] = _now()
    atomic_write_json(checkpoint_path, checkpoint)

    candidate = _candidate_payload(
        checkpoint,
        output_path=output_path,
        report_path=report_path,
    )
    report = _review_payload(
        checkpoint,
        candidate,
        checkpoint_path=checkpoint_path,
        output_path=output_path,
    )
    atomic_write_json(output_path, candidate)
    atomic_write_json(report_path, report)
    return candidate, report


async def run_regeneration(
    *,
    snapshot_path: Path = SNAPSHOT_PATH,
    checkpoint_path: Path = CHECKPOINT_PATH,
    output_path: Path = CANDIDATE_PATH,
    report_path: Path = REVIEW_REPORT_PATH,
    requested_ids: Sequence[str] | None = None,
    limit: int | None = None,
    resume: bool = False,
    max_attempts: int | None = None,
    provider: str = DEFAULT_PROVIDER,
    batch_generator: BatchGenerator | None = None,
    reaudit_rejected: bool = False,
    reaudit_all: bool = False,
    migrate_memory_gate: bool = False,
) -> tuple[dict[str, object], dict[str, object]]:
    """Run one checkpoint owner at a time; the OS releases the lock on crash."""

    with CheckpointRunLock(checkpoint_path):
        return await _run_regeneration_locked(
            snapshot_path=snapshot_path,
            checkpoint_path=checkpoint_path,
            output_path=output_path,
            report_path=report_path,
            requested_ids=requested_ids,
            limit=limit,
            resume=resume,
            max_attempts=max_attempts,
            provider=provider,
            batch_generator=batch_generator,
            reaudit_rejected=reaudit_rejected,
            reaudit_all=reaudit_all,
            migrate_memory_gate=migrate_memory_gate,
        )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Regenerate Chinese-culture V3 explanation candidates in fixed six-question "
            "batches. This command never writes the database or publishes candidates."
        )
    )
    parser.add_argument("--limit", type=int, help="Process only the first N selected culture questions.")
    parser.add_argument(
        "--ids",
        nargs="+",
        help="Process only these fixed snapshot IDs; comma-separated tokens are also accepted.",
    )
    parser.add_argument("--resume", action="store_true", help="Resume the existing atomic checkpoint.")
    parser.add_argument(
        "--reaudit-rejected",
        action="store_true",
        help=(
            "With --resume, re-run the current deterministic gate against saved "
            "static-gate rejections without calling the generation provider."
        ),
    )
    parser.add_argument(
        "--reaudit-all",
        action="store_true",
        help=(
            "With --resume, re-run the current deterministic gate against both accepted "
            "and saved static-gate-rejected candidates without provider calls."
        ),
    )
    parser.add_argument(
        "--migrate-memory-gate",
        action="store_true",
        help=(
            "With --resume, re-audit all saved candidates and requeue only those "
            "blocked solely by the new memory-value gate. This mode makes no provider calls."
        ),
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=None,
        help=f"Per-question attempt ceiling (default {DEFAULT_MAX_ATTEMPTS}, max {MAX_ALLOWED_ATTEMPTS}).",
    )
    parser.add_argument(
        "--provider",
        choices=PROVIDERS,
        default=DEFAULT_PROVIDER,
        help="Generation provider. Use codex-cli to reuse the current Codex login without a DeepSeek key.",
    )
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINT_PATH)
    parser.add_argument("--output", type=Path, default=CANDIDATE_PATH)
    parser.add_argument("--report", type=Path, default=REVIEW_REPORT_PATH)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    requested_ids = parse_ids(args.ids)
    _validate_limited_run_artifacts(
        requested_ids=requested_ids,
        limit=args.limit,
        checkpoint_path=args.checkpoint,
        output_path=args.output,
        report_path=args.report,
    )
    candidate, report = asyncio.run(
        run_regeneration(
            checkpoint_path=args.checkpoint,
            output_path=args.output,
            report_path=args.report,
            requested_ids=requested_ids,
            limit=args.limit,
            resume=args.resume,
            max_attempts=args.max_attempts,
            provider=args.provider,
            reaudit_rejected=args.reaudit_rejected,
            reaudit_all=args.reaudit_all,
            migrate_memory_gate=args.migrate_memory_gate,
        )
    )
    print(
        json.dumps(
            {
                "candidate": _portable_path(args.output),
                "review_report": _portable_path(args.report),
                "checkpoint": _portable_path(args.checkpoint),
                "selected_count": candidate["selected_count"],
                "accepted_count": candidate["accepted_count"],
                "rejected_count": candidate["rejected_count"],
                "batch_call_count": report["summary"]["batch_call_count"],
                "static_reaudit_passed_count": report["summary"][
                    "static_reaudit_passed_count"
                ],
                "static_reaudit_demoted_count": report["summary"][
                    "static_reaudit_demoted_count"
                ],
                "memory_gate_migration_requeued_count": report["summary"][
                    "memory_gate_migration_requeued_count"
                ],
                "memory_gate_migration_extra_attempt_granted_count": report["summary"][
                    "memory_gate_migration_extra_attempt_granted_count"
                ],
                "provider": args.provider,
                "complete": candidate["complete"],
                "pending_count": report["summary"]["pending_count"],
                "ready_for_publish": False,
                "database_writes": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    succeeded = bool(
        candidate["complete"]
        and candidate["accepted_count"] == candidate["selected_count"]
        and candidate["rejected_count"] == 0
    )
    return 0 if succeeded else 2


if __name__ == "__main__":
    raise SystemExit(main())
