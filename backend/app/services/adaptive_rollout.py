"""Deterministic admission control for new adaptive-practice sessions."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from typing import Any


ROLLOUT_BUCKET_COUNT = 10_000


@dataclass(frozen=True)
class AdaptiveRolloutDecision:
    allowed: bool
    decision_source: str
    rollout_basis_points: int
    bucket: int | None = None


def parse_rollout_user_ids(raw_value: str | None) -> frozenset[str]:
    """Parse a comma-separated internal-user allowlist without logging it."""

    return frozenset(
        user_id
        for value in str(raw_value or "").split(",")
        if (user_id := value.strip())
    )


def stable_rollout_bucket(user_id: str, *, salt: str) -> int:
    """Map a server-authenticated user ID to a stable 0..9999 bucket."""

    digest = hmac.new(
        str(salt).encode("utf-8"),
        str(user_id).encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return int.from_bytes(digest[:8], "big") % ROLLOUT_BUCKET_COUNT


def _parse_rollout_basis_points(raw_value: Any) -> int | None:
    try:
        percent = Decimal(str(raw_value).strip())
    except (InvalidOperation, ValueError):
        return None
    if not percent.is_finite() or percent < 0 or percent > 100:
        return None
    return int((percent * 100).to_integral_value(rounding=ROUND_FLOOR))


def evaluate_adaptive_rollout(settings: Any, user_id: str) -> AdaptiveRolloutDecision:
    """Return a sanitized, observable decision for a new adaptive session.

    The global boolean remains the emergency kill switch. With it enabled, an
    explicit user-ID allowlist wins first; everybody else enters through a
    deterministic percentage cohort. Existing-session endpoints deliberately
    do not call this function so an emergency rollout stop never strands a
    session that is already in progress.
    """

    if not bool(getattr(settings, "adaptive_practice_enabled", False)):
        return AdaptiveRolloutDecision(False, "master_off", 0)

    normalized_user_id = str(user_id or "").strip()
    if not normalized_user_id:
        return AdaptiveRolloutDecision(False, "config_invalid", 0)

    allowlist = parse_rollout_user_ids(
        getattr(settings, "adaptive_practice_rollout_user_ids", "")
    )
    if normalized_user_id in allowlist:
        return AdaptiveRolloutDecision(True, "allowlist", 0)

    threshold = _parse_rollout_basis_points(
        getattr(settings, "adaptive_practice_rollout_percent", "0")
    )
    if threshold is None:
        return AdaptiveRolloutDecision(False, "config_invalid", 0)
    if threshold <= 0:
        return AdaptiveRolloutDecision(False, "bucket_miss", threshold)
    if threshold >= ROLLOUT_BUCKET_COUNT:
        return AdaptiveRolloutDecision(True, "bucket_hit", threshold)

    salt = str(getattr(settings, "adaptive_practice_rollout_salt", "") or "").strip()
    if not salt:
        return AdaptiveRolloutDecision(False, "config_invalid", threshold)
    bucket = stable_rollout_bucket(normalized_user_id, salt=salt)
    return AdaptiveRolloutDecision(
        bucket < threshold,
        "bucket_hit" if bucket < threshold else "bucket_miss",
        threshold,
        bucket,
    )


def adaptive_rollout_allows_user(settings: Any, user_id: str) -> bool:
    """Compatibility helper for callers that only need the boolean result."""

    return evaluate_adaptive_rollout(settings, user_id).allowed
