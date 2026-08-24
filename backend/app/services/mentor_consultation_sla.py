"""Shared first-response SLA rules for consultation reports and appeals.

The rules live outside of route handlers so the user-facing status, the
backoffice queue and the periodic escalation sweep calculate the same result.
All stored timestamps are UTC ISO strings; presentation is left to the client.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


MENTOR_CONSULTATION_CASE_PRIORITIES = {"normal", "high", "urgent"}
MENTOR_CONSULTATION_OPEN_CASE_STATUSES = {"pending", "reviewing"}

# These are not an automatic verdict.  They only make potentially harmful or
# financial-risk issues appear first in the operations queue.
MENTOR_CONSULTATION_URGENT_REPORT_ISSUE_TYPES = {
    "收费或诱导私下交易",
    "诱导私下交易",
    "骚扰、辱骂或不当言行",
    "泄露隐私",
    "侵犯隐私",
}

_PRIORITY_RANKS = {"normal": 0, "high": 1, "urgent": 2}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def normalize_case_priority(value: object, *, default: str = "normal") -> str:
    normalized = str(value or "").strip().lower()
    if normalized in MENTOR_CONSULTATION_CASE_PRIORITIES:
        return normalized
    return default if default in MENTOR_CONSULTATION_CASE_PRIORITIES else "normal"


def case_priority_rank(value: object) -> int:
    return _PRIORITY_RANKS[normalize_case_priority(value)]


def initial_report_priority(issue_type: object) -> str:
    return "urgent" if str(issue_type or "").strip() in MENTOR_CONSULTATION_URGENT_REPORT_ISSUE_TYPES else "normal"


def first_response_deadline(*, now: datetime | None = None, hours: int = 48) -> str:
    """Return a bounded, UTC first-response deadline for a newly filed case."""

    current_time = now or utc_now()
    safe_hours = max(1, min(int(hours or 48), 24 * 30))
    return (current_time + timedelta(hours=safe_hours)).isoformat()


def serialize_case_sla(
    row: dict,
    *,
    now: datetime | None = None,
    fallback_first_response_hours: int = 48,
    warning_hours: int = 6,
) -> dict:
    """Build an API-safe SLA projection, including legacy-row fallbacks.

    New rows always retain ``first_response_due_at``.  Falling back to the
    creation time keeps older rows readable while a deployment is backfilled.
    """

    current_time = now or utc_now()
    created_at = as_utc_datetime(row.get("created_at")) or current_time
    due_at = as_utc_datetime(row.get("first_response_due_at"))
    if due_at is None:
        due_at = created_at + timedelta(hours=max(1, int(fallback_first_response_hours or 48)))
    first_response_at = as_utc_datetime(row.get("first_response_at"))
    case_status = str(row.get("status") or "pending")
    priority = normalize_case_priority(row.get("priority"))
    escalation_level = max(0, int(row.get("escalation_level") or 0))
    escalated_at = row.get("escalated_at") or None

    if first_response_at is not None:
        sla_status = "responded" if case_status in MENTOR_CONSULTATION_OPEN_CASE_STATUSES else "closed"
    elif case_status not in MENTOR_CONSULTATION_OPEN_CASE_STATUSES:
        sla_status = "closed"
    elif due_at <= current_time:
        sla_status = "overdue"
    elif due_at - current_time <= timedelta(hours=max(1, int(warning_hours or 6))):
        sla_status = "due_soon"
    else:
        sla_status = "on_track"

    return {
        "first_response_due_at": due_at.isoformat(),
        "first_response_at": first_response_at.isoformat() if first_response_at else None,
        "priority": priority,
        "escalation_level": escalation_level,
        "escalated_at": escalated_at,
        "sla_status": sla_status,
    }
