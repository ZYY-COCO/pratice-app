from __future__ import annotations

import base64
import json
from datetime import datetime
from typing import Any, Literal, Sequence
from uuid import UUID

from fastapi import HTTPException, status


CURSOR_VERSION = 1
MAX_CURSOR_LENGTH = 2048


def encode_page_cursor(kind: str, payload: dict[str, Any]) -> str:
    """Return a compact opaque cursor that is safe in a query string."""

    document = {
        "v": CURSOR_VERSION,
        "k": str(kind),
        "d": payload,
    }
    raw = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_page_cursor(
    cursor: str | None,
    *,
    kind: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Decode and validate a cursor, including the query context it belongs to."""

    if not cursor:
        return None
    normalized = str(cursor).strip()
    if not normalized or len(normalized) > MAX_CURSOR_LENGTH:
        _raise_invalid_cursor()

    try:
        padding = "=" * (-len(normalized) % 4)
        document = json.loads(base64.urlsafe_b64decode(normalized + padding).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        _raise_invalid_cursor()

    if (
        not isinstance(document, dict)
        or document.get("v") != CURSOR_VERSION
        or document.get("k") != kind
        or not isinstance(document.get("d"), dict)
    ):
        _raise_invalid_cursor()

    payload = document["d"]
    for key, expected in (context or {}).items():
        if payload.get(key) != expected:
            _raise_invalid_cursor("分页条件已变化，请刷新列表后重试")
    return payload


def cursor_datetime(payload: dict[str, Any], key: str) -> str:
    value = str(payload.get(key) or "").strip()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        _raise_invalid_cursor()
    if not value or parsed.tzinfo is None:
        _raise_invalid_cursor()
    return value


def cursor_uuid(payload: dict[str, Any], key: str) -> str:
    value = str(payload.get(key) or "").strip()
    try:
        return str(UUID(value))
    except (ValueError, AttributeError):
        _raise_invalid_cursor()


def cursor_integer(payload: dict[str, Any], key: str, *, minimum: int = 0) -> int:
    value = payload.get(key)
    if isinstance(value, bool):
        _raise_invalid_cursor()
    try:
        result = int(value)
    except (TypeError, ValueError):
        _raise_invalid_cursor()
    if result < minimum or str(result) != str(value):
        _raise_invalid_cursor()
    return result


def build_keyset_filter(
    fields: Sequence[tuple[str, Literal["asc", "desc"], str | int]],
) -> str:
    """Build a PostgREST OR expression for a compound keyset cursor."""

    branches: list[str] = []
    equal_prefix: list[str] = []
    for field, direction, value in fields:
        if not field.replace("_", "").isalnum():
            raise ValueError("Invalid keyset field")
        rendered = _render_postgrest_value(value)
        comparator = "gt" if direction == "asc" else "lt"
        conditions = [*equal_prefix, f"{field}.{comparator}.{rendered}"]
        branches.append(conditions[0] if len(conditions) == 1 else f"and({','.join(conditions)})")
        equal_prefix.append(f"{field}.eq.{rendered}")
    return ",".join(branches)


def _render_postgrest_value(value: str | int) -> str:
    rendered = str(value)
    if not rendered or any(character in rendered for character in ",()\n\r"):
        _raise_invalid_cursor()
    return rendered


def _raise_invalid_cursor(detail: str = "分页游标无效，请刷新列表后重试") -> None:
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)
