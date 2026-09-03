"""Authenticated persistence helpers for professional-directory favorites."""

from __future__ import annotations

from typing import Any

from app.db import get_supabase_admin
from app.services.major_catalog import (
    MajorCatalogFavoriteTargetType,
    resolve_major_catalog_favorite_target,
    resolve_major_catalog_favorite_targets,
)
from app.services.supabase_resilience import (
    call_supabase,
    is_missing_supabase_relation_error,
)
from app.utils.cursor_pagination import (
    build_keyset_filter,
    cursor_datetime,
    cursor_uuid,
    decode_page_cursor,
    encode_page_cursor,
)


FAVORITE_TABLE = "major_catalog_favorites"
FAVORITE_FIELDS = (
    "id,user_id,catalog_year,target_type,target_id,school_id,snapshot,created_at,updated_at"
)
FAVORITE_CURSOR_KIND = "major_catalog_favorites"


class MajorCatalogFavoritesUnavailableError(RuntimeError):
    """Raised when persisted favorites cannot currently be read or changed."""


class MajorCatalogFavoritesMigrationRequiredError(MajorCatalogFavoritesUnavailableError):
    """Raised when the favorites table has not been installed in Supabase."""


def _execute_favorite_query(operation: Any, *, operation_name: str) -> Any:
    try:
        return call_supabase(operation, operation_name=operation_name)
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            raise MajorCatalogFavoritesMigrationRequiredError(
                "major_catalog_favorites migration has not been applied"
            ) from exc
        raise MajorCatalogFavoritesUnavailableError("major catalog favorites unavailable") from exc


def _reference_key(reference: dict[str, Any]) -> tuple[str, MajorCatalogFavoriteTargetType, str]:
    return (
        str(reference.get("catalog_year") or ""),
        str(reference.get("target_type") or ""),  # type: ignore[return-value]
        str(reference.get("target_id") or ""),
    )


def _effective_snapshot(
    row: dict[str, Any],
    resolved_targets: dict[tuple[str, MajorCatalogFavoriteTargetType, str], dict[str, Any]],
) -> tuple[dict[str, Any], bool]:
    current = resolved_targets.get(_reference_key(row))
    if current is not None:
        return current, True
    saved = row.get("snapshot")
    return (dict(saved) if isinstance(saved, dict) else {}), False


def _serialize_favorite(
    row: dict[str, Any],
    resolved_targets: dict[tuple[str, MajorCatalogFavoriteTargetType, str], dict[str, Any]],
) -> dict[str, Any]:
    snapshot, available = _effective_snapshot(row, resolved_targets)
    return {
        "id": str(row.get("id") or ""),
        "catalog_year": str(row.get("catalog_year") or ""),
        "target_type": str(row.get("target_type") or ""),
        "target_id": str(row.get("target_id") or ""),
        "school_id": str(row.get("school_id") or snapshot.get("school_id") or ""),
        "snapshot": snapshot,
        "available": available,
        "created_at": str(row.get("created_at") or ""),
        "updated_at": str(row.get("updated_at") or row.get("created_at") or ""),
    }


def list_major_catalog_favorites(
    *,
    user_id: str,
    limit: int = 30,
    cursor: str | None = None,
    target_type: MajorCatalogFavoriteTargetType | None = None,
    catalog_year: str | None = None,
) -> dict[str, Any]:
    normalized_year = str(catalog_year or "").strip()
    cursor_context = {
        "target_type": str(target_type or ""),
        "catalog_year": normalized_year,
    }
    cursor_payload = decode_page_cursor(
        cursor,
        kind=FAVORITE_CURSOR_KIND,
        context=cursor_context,
    )
    supabase = get_supabase_admin()
    query = (
        supabase.table(FAVORITE_TABLE)
        .select(FAVORITE_FIELDS, count="exact")
        .eq("user_id", user_id)
    )
    if target_type:
        query = query.eq("target_type", target_type)
    if normalized_year:
        query = query.eq("catalog_year", normalized_year)
    if cursor_payload:
        query = query.or_(
            build_keyset_filter(
                [
                    ("created_at", "desc", cursor_datetime(cursor_payload, "created_at")),
                    ("id", "desc", cursor_uuid(cursor_payload, "id")),
                ]
            )
        )
    response = _execute_favorite_query(
        lambda: (
            query.order("created_at", desc=True)
            .order("id", desc=True)
            .limit(limit + 1)
            .execute()
        ),
        operation_name="major catalog favorite list",
    )
    rows = list(response.data or [])
    has_more = len(rows) > limit
    page_rows = rows[:limit]
    resolved_targets = resolve_major_catalog_favorite_targets(page_rows)
    next_cursor = None
    if has_more and page_rows:
        anchor = page_rows[-1]
        next_cursor = encode_page_cursor(
            FAVORITE_CURSOR_KIND,
            {
                **cursor_context,
                "created_at": str(anchor.get("created_at") or ""),
                "id": str(anchor.get("id") or ""),
            },
        )
    response_count = getattr(response, "count", None)
    return {
        "items": [_serialize_favorite(row, resolved_targets) for row in page_rows],
        "count": int(response_count if response_count is not None else len(page_rows)),
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


def get_major_catalog_favorite_statuses(
    *,
    user_id: str,
    references: list[dict[str, str]],
) -> dict[str, Any]:
    resolved_targets = resolve_major_catalog_favorite_targets(references)
    grouped: dict[tuple[str, str], list[str]] = {}
    for reference in references:
        group_key = (
            str(reference.get("catalog_year") or ""),
            str(reference.get("target_type") or ""),
        )
        grouped.setdefault(group_key, []).append(str(reference.get("target_id") or ""))

    supabase = get_supabase_admin()
    favorite_keys: set[tuple[str, str, str]] = set()
    for (catalog_year, target_type), target_ids in grouped.items():
        unique_target_ids = list(dict.fromkeys(target_ids))
        response = _execute_favorite_query(
            lambda catalog_year=catalog_year, target_type=target_type, unique_target_ids=unique_target_ids: (
                supabase.table(FAVORITE_TABLE)
                .select("catalog_year,target_type,target_id")
                .eq("user_id", user_id)
                .eq("catalog_year", catalog_year)
                .eq("target_type", target_type)
                .in_("target_id", unique_target_ids)
                .execute()
            ),
            operation_name="major catalog favorite status",
        )
        favorite_keys.update(
            (
                str(row.get("catalog_year") or ""),
                str(row.get("target_type") or ""),
                str(row.get("target_id") or ""),
            )
            for row in (response.data or [])
        )

    return {
        "items": [
            {
                **reference,
                "is_favorited": _reference_key(reference) in favorite_keys,
                "available": _reference_key(reference) in resolved_targets,
            }
            for reference in references
        ]
    }


def save_major_catalog_favorite(
    *,
    user_id: str,
    catalog_year: str,
    target_type: MajorCatalogFavoriteTargetType,
    target_id: str,
) -> dict[str, Any]:
    snapshot = resolve_major_catalog_favorite_target(
        catalog_year=catalog_year,
        target_type=target_type,
        target_id=target_id,
    )
    if snapshot is None:
        raise KeyError(target_id)
    school_id = str(snapshot.get("school_id") or "")
    if not school_id:
        raise KeyError(target_id)

    supabase = get_supabase_admin()
    payload = {
        "user_id": user_id,
        "catalog_year": catalog_year,
        "target_type": target_type,
        "target_id": target_id,
        "school_id": school_id,
        "snapshot": snapshot,
    }
    _execute_favorite_query(
        lambda: (
            supabase.table(FAVORITE_TABLE)
            .upsert(
                payload,
                on_conflict="user_id,catalog_year,target_type,target_id",
            )
            .execute()
        ),
        operation_name="major catalog favorite save",
    )
    return {
        "catalog_year": catalog_year,
        "target_type": target_type,
        "target_id": target_id,
        "is_favorited": True,
        "available": True,
        "snapshot": snapshot,
    }


def delete_major_catalog_favorite(
    *,
    user_id: str,
    catalog_year: str,
    target_type: MajorCatalogFavoriteTargetType,
    target_id: str,
) -> dict[str, Any]:
    supabase = get_supabase_admin()
    _execute_favorite_query(
        lambda: (
            supabase.table(FAVORITE_TABLE)
            .delete()
            .eq("user_id", user_id)
            .eq("catalog_year", catalog_year)
            .eq("target_type", target_type)
            .eq("target_id", target_id)
            .execute()
        ),
        operation_name="major catalog favorite delete",
    )
    return {
        "catalog_year": catalog_year,
        "target_type": target_type,
        "target_id": target_id,
        "is_favorited": False,
    }
