"""Public, read-only content feeds for the student homepage.

The administration portal writes the same records it reads.  The student
client only receives published entries, so saved drafts and archived batches
never leak into the public page.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from app.db import get_supabase_admin
from app.services.supabase_resilience import call_supabase, is_missing_supabase_relation_error


router = APIRouter(tags=["首页运营"])


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _is_current(item: dict[str, Any], now: datetime) -> bool:
    starts_at = _parse_timestamp(item.get("starts_at"))
    ends_at = _parse_timestamp(item.get("ends_at"))
    return (not starts_at or starts_at <= now) and (not ends_at or ends_at >= now)


@router.get("/home-content")
def get_home_content() -> dict[str, Any]:
    """Return the published homepage cards in the shape used by the app."""
    try:
        supabase = get_supabase_admin()
        response = call_supabase(
            lambda: (
                supabase.table("home_content_items")
                .select("*")
                .in_("slot", ["focus", "news"])
                .order("sort_order")
                .order("created_at", desc=True)
                .execute()
            ),
            operation_name="public home content list",
        )
    except Exception as exc:
        # The mobile page keeps its built-in cards until the operations migration
        # is applied, which makes this route safe to deploy before the SQL change.
        if not is_missing_supabase_relation_error(exc):
            return {
                "focus": [],
                "news": [],
                "managedSlots": {"focus": True, "news": True},
                "unavailable": True,
            }
        return {
            "focus": [],
            "news": [],
            "managedSlots": {"focus": False, "news": False},
        }

    now = datetime.now(timezone.utc)
    rows = [item for item in (response.data or []) if isinstance(item, dict)]
    managed_slots = {
        "focus": any(item.get("slot") == "focus" for item in rows),
        "news": any(item.get("slot") == "news" for item in rows),
    }
    focus: list[dict[str, Any]] = []
    news: list[dict[str, Any]] = []
    for item in rows:
        if item.get("status") != "published" or not _is_current(item, now):
            continue
        target = {
            "title": str(item.get("title") or ""),
            "url": str(item.get("target_url") or ""),
            "routeKey": str(item.get("route_key") or ""),
        }
        if item.get("slot") == "focus":
            focus.append({
                **target,
                "badge": str(item.get("badge") or ""),
                "subtitle": str(item.get("subtitle") or ""),
                "artLabel": str(item.get("cover_label") or ""),
            })
        elif item.get("slot") == "news":
            news.append({
                **target,
                "source": str(item.get("source") or ""),
                "date": item.get("display_date"),
                "coverLabel": str(item.get("cover_label") or ""),
                "coverTone": str(item.get("tone") or "is-blue"),
            })
    # These limits match the actual first-screen surfaces in the student app.
    # Additional published rows remain available in the admin history but do
    # not silently expand or destabilize the mobile homepage.
    return {
        "focus": focus[:3],
        "news": news[:2],
        "managedSlots": managed_slots,
    }


@router.get("/admission-data/scorelines")
def get_published_scorelines() -> dict[str, Any]:
    """Expose the currently published scoreline snapshot for student views."""
    try:
        supabase = get_supabase_admin()
        run_response = call_supabase(
            lambda: (
                supabase.table("historical_scoreline_import_runs")
                .select("id,created_at,published_at,statistics")
                .eq("status", "published")
                .order("published_at", desc=True)
                .limit(1)
                .execute()
            ),
            operation_name="public scoreline published run",
        )
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            return {"records": [], "regions": [], "years": [], "statistics": {}, "managed": False}
        return {"records": [], "regions": [], "years": [], "statistics": {}, "managed": True, "unavailable": True}

    run_rows = run_response.data or []
    if not run_rows:
        return {"records": [], "regions": [], "years": [], "statistics": {}, "managed": False}
    run = run_rows[0]
    try:
        record_response = call_supabase(
            lambda: (
                supabase.table("historical_scoreline_records")
                .select("score_year,region,school_name,unit_name,score_raw,score_value,score_kind")
                .eq("import_run_id", run.get("id"))
                .eq("is_published", True)
                .order("region")
                .order("school_name")
                .execute()
            ),
            operation_name="public scoreline record list",
        )
    except Exception:
        return {"records": [], "regions": [], "years": [], "statistics": {}, "managed": True, "unavailable": True}

    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    years: set[str] = set()
    for row in record_response.data or []:
        if not isinstance(row, dict):
            continue
        region = str(row.get("region") or "")
        school = str(row.get("school_name") or "")
        unit_name = str(row.get("unit_name") or "")
        year = str(row.get("score_year") or "")
        if not region or not school or not year:
            continue
        key = (region, school, unit_name)
        if key not in grouped:
            grouped[key] = {
                "id": "|".join(key),
                "region": region,
                "school": school,
                "schoolName": school,
                "unitName": unit_name,
                "scores": {},
            }
        numeric = row.get("score_value")
        try:
            score = float(numeric) if numeric is not None else None
        except (TypeError, ValueError):
            score = None
        grouped[key]["scores"][year] = {
            "raw": str(row.get("score_raw") or ""),
            "score": score,
            "kind": str(row.get("score_kind") or "note"),
        }
        years.add(year)

    records = sorted(grouped.values(), key=lambda item: (item["region"], item["school"], item["unitName"]))
    regions: dict[str, int] = defaultdict(int)
    for record in records:
        regions[record["region"]] += 1
    return {
        "records": records,
        "regions": [{"name": name, "count": count} for name, count in sorted(regions.items())],
        "years": sorted(years, reverse=True),
        "statistics": {
            "recordCount": len(records),
            "regionCount": len(regions),
            "runId": str(run.get("id") or ""),
            "publishedAt": run.get("published_at"),
        },
        "managed": True,
    }
