"""Small, dependency-free guards for transient Supabase outages.

The API is served from Tencent Cloud while authentication and application data
are provided by Supabase. A temporary upstream timeout must not be reported
to a client as an invalid access token, otherwise a healthy user is forced to
log in again.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar


logger = logging.getLogger(__name__)
Result = TypeVar("Result")

_TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}
_TRANSIENT_MARKERS = (
    "timeout",
    "timed out",
    "connect",
    "connection",
    "network",
    "temporarily unavailable",
    "server disconnected",
    "remote protocol error",
)
_AUTH_MARKERS = (
    "invalid jwt",
    "jwt expired",
    "invalid token",
    "invalid login credentials",
    "token has expired",
    "not authenticated",
)


def _provider_status_code(exc: Exception) -> int | None:
    """Read an HTTP status from common Supabase/http client exception shapes."""

    for source in (exc, getattr(exc, "response", None)):
        if source is None:
            continue
        for attribute in ("status_code", "status", "code"):
            value = getattr(source, attribute, None)
            try:
                status_code = int(value)
            except (TypeError, ValueError):
                continue
            if 100 <= status_code <= 599:
                return status_code
    return None


def is_transient_supabase_error(exc: Exception) -> bool:
    status_code = _provider_status_code(exc)
    if status_code is not None:
        return status_code in _TRANSIENT_STATUS_CODES

    text = str(exc).lower()
    error_type = type(exc).__name__.lower()
    return any(marker in text or marker in error_type for marker in _TRANSIENT_MARKERS)


def is_authentication_error(exc: Exception) -> bool:
    """Whether an auth provider rejected credentials instead of being unavailable."""

    status_code = _provider_status_code(exc)
    if status_code in {400, 401, 403}:
        return True
    text = str(exc).lower()
    return any(marker in text for marker in _AUTH_MARKERS)


def call_supabase(operation: Callable[[], Result], *, operation_name: str, attempts: int = 2) -> Result:
    """Run a call with one short retry only for transient upstream failures."""

    for attempt in range(1, max(attempts, 1) + 1):
        try:
            return operation()
        except Exception as exc:
            if attempt >= attempts or not is_transient_supabase_error(exc):
                raise
            logger.warning(
                "Transient Supabase failure during %s; retrying once (error_type=%s)",
                operation_name,
                type(exc).__name__,
            )
            time.sleep(0.35)

    raise RuntimeError("Supabase operation did not return")
