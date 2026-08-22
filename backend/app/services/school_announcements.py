from __future__ import annotations

import gzip
from hashlib import sha1
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from app.db import get_supabase_admin
from app.services.supabase_resilience import call_supabase, is_missing_supabase_relation_error


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "school_announcements.json.gz"
NOTICE_TYPES = {"brochure", "scoreline_retest"}


class SchoolAnnouncementUnavailableError(RuntimeError):
    pass


def _announcement_data_signature() -> tuple[int, int]:
    if not DATA_PATH.is_file():
        raise SchoolAnnouncementUnavailableError("院校公告数据尚未生成")
    try:
        stat = DATA_PATH.stat()
    except OSError as error:
        raise SchoolAnnouncementUnavailableError("院校公告索引读取失败") from error
    return stat.st_mtime_ns, stat.st_size


@lru_cache(maxsize=2)
def _load_announcement_index(data_signature: tuple[int, int]) -> dict[str, Any]:
    """Load one specific version of the generated announcement index."""
    try:
        with gzip.open(DATA_PATH, "rt", encoding="utf-8") as data_file:
            return json.load(data_file)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise SchoolAnnouncementUnavailableError("院校公告索引读取失败") from error


def get_announcement_index() -> dict[str, Any]:
    """Return the published operations snapshot, or the bundled baseline."""
    database_index = _load_published_database_index()
    if database_index is not None:
        return database_index
    return _load_announcement_index(_announcement_data_signature())


def get_bundled_announcement_index() -> dict[str, Any]:
    """Return the local generated snapshot without consulting published data."""
    return _load_announcement_index(_announcement_data_signature())


def _database_school_id(region: str, school_name: str) -> str:
    digest = sha1(f"{region}\n{school_name}".encode("utf-8")).hexdigest()[:16]
    return f"ops-{digest}"


def _load_published_database_index() -> dict[str, Any] | None:
    """Use a published admin batch when the operations migration is available."""
    try:
        supabase = get_supabase_admin()
        run_response = call_supabase(
            lambda: (
                supabase.table("school_announcement_import_runs")
                .select("id")
                .eq("status", "published")
                .order("published_at", desc=True)
                .limit(1)
                .execute()
            ),
            operation_name="published school announcement run",
        )
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            return None
        raise SchoolAnnouncementUnavailableError("院校公告公开版本读取失败") from exc

    run_rows = run_response.data or []
    if not run_rows:
        return None
    published_run_id = str(run_rows[0].get("id") or "")
    if not published_run_id:
        return None
    try:
        response = call_supabase(
            lambda: (
                supabase.table("school_announcement_records")
                .select("*")
                .eq("import_run_id", published_run_id)
                .eq("status", "published")
                .order("sort_order")
                .order("notice_date", desc=True)
                .execute()
            ),
            operation_name="published school announcement snapshot",
        )
    except Exception as exc:
        raise SchoolAnnouncementUnavailableError("院校公告公开快照读取失败") from exc

    rows = [row for row in (response.data or []) if isinstance(row, dict)]

    announcements: dict[str, dict[str, Any]] = {}
    schools: dict[str, dict[str, Any]] = {}
    regions: dict[str, dict[str, Any]] = {}
    for row in rows:
        region = str(row.get("region") or "")
        school_name = str(row.get("school_name") or "")
        announcement_id = str(row.get("id") or "")
        if not region or not school_name or not announcement_id:
            continue
        school_id = _database_school_id(region, school_name)
        schools.setdefault(school_id, {"id": school_id, "name": school_name, "region": region})
        regions.setdefault(region, {"name": region})
        announcements[announcement_id] = {
            "id": announcement_id,
            "year": str(row.get("notice_year") or ""),
            "region": region,
            "school_id": school_id,
            "school_name": school_name,
            "unit_name": str(row.get("unit_name") or ""),
            "notice_type": str(row.get("notice_type") or ""),
            "title": str(row.get("title") or ""),
            "summary": str(row.get("summary") or ""),
            "notice_date": row.get("notice_date"),
            "source_url": row.get("source_url"),
            "content_text": str(row.get("content_text") or ""),
            "notice_level": "school",
            "content_mode": "text",
            "sort_order": int(row.get("sort_order") or 0),
        }

    return {
        "version": f"operations-published-{published_run_id}",
        "regions": [regions[name] for name in sorted(regions)],
        "schools": schools,
        "announcements": announcements,
        "statistics": {
            "school_count": len(schools),
            "announcement_count": len(announcements),
            "region_count": len(regions),
        },
    }


def _normalized_year(year: str | None) -> str:
    return (year or "").strip()


def _normalized_type(notice_type: str | None) -> str:
    value = (notice_type or "").strip()
    return value if value in NOTICE_TYPES else ""


def _all_announcements() -> Iterable[dict[str, Any]]:
    return get_announcement_index().get("announcements", {}).values()


def _matches(
    announcement: dict[str, Any],
    *,
    year: str = "",
    notice_type: str = "",
    region: str = "",
    school_id: str = "",
    keyword: str = "",
) -> bool:
    if year and announcement.get("year") != year:
        return False
    if notice_type and announcement.get("notice_type") != notice_type:
        return False
    if region and announcement.get("region") != region:
        return False
    if school_id and announcement.get("school_id") != school_id:
        return False
    if keyword:
        haystack = "\n".join(
            str(announcement.get(field) or "")
            for field in ("school_name", "unit_name", "title", "summary", "content_text")
        ).casefold()
        if keyword.casefold() not in haystack:
            return False
    return True


def _filtered(
    *,
    year: str | None = None,
    notice_type: str | None = None,
    region: str | None = None,
    school_id: str | None = None,
    keyword: str | None = None,
) -> list[dict[str, Any]]:
    normalized_year = _normalized_year(year)
    normalized_type = _normalized_type(notice_type)
    normalized_region = (region or "").strip()
    normalized_school_id = (school_id or "").strip()
    normalized_keyword = (keyword or "").strip()
    return [
        item
        for item in _all_announcements()
        if _matches(
            item,
            year=normalized_year,
            notice_type=normalized_type,
            region=normalized_region,
            school_id=normalized_school_id,
            keyword=normalized_keyword,
        )
    ]


def _notice_summary(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if key != "content_text"}


def _school_summary(
    school: dict[str, Any],
    notices: list[dict[str, Any]],
    *,
    region: str = "",
) -> dict[str, Any]:
    return {
        "id": school.get("id") or "",
        "name": school.get("name") or "",
        # 跨校区公告以用户当前浏览地域为准，避免从广东的深圳校区公告
        # 进入详情后又被主校区地域覆盖。
        "region": region or school.get("region") or "",
        "announcement_count": len(notices),
        "brochure_count": sum(1 for item in notices if item.get("notice_type") == "brochure"),
        "scoreline_count": sum(1 for item in notices if item.get("notice_type") == "scoreline_retest"),
        "image_only_count": sum(1 for item in notices if item.get("content_mode") == "image_only"),
    }


def list_published_announcement_records(
    *,
    year: str | None = None,
    notice_type: str | None = None,
    region: str | None = None,
    school_id: str | None = None,
    keyword: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Return the published announcement records and filter options used by students."""
    index = get_announcement_index()
    normalized_year = _normalized_year(year)
    normalized_type = _normalized_type(notice_type)
    normalized_region = (region or "").strip()
    normalized_school_id = (school_id or "").strip()
    normalized_keyword = (keyword or "").strip()
    visible_notices = _filtered(
        year=normalized_year,
        notice_type=normalized_type,
        region=normalized_region,
        school_id=normalized_school_id,
        keyword=normalized_keyword,
    )
    filter_notices = _filtered(year=normalized_year, notice_type=normalized_type)
    records = [
        {
            "id": item.get("id") or "",
            "notice_year": item.get("year") or "",
            "region": item.get("region") or "",
            "school_id": item.get("school_id") or "",
            "school_name": item.get("school_name") or "",
            "unit_name": item.get("unit_name") or "",
            "notice_type": item.get("notice_type") or "",
            "title": item.get("title") or "",
            "summary": item.get("summary") or "",
            "notice_date": item.get("notice_date"),
            "source_url": item.get("source_url"),
            "content_text": item.get("content_text") or "",
            "sort_order": int(item.get("sort_order") or 0),
            "status": "published",
            "is_published": True,
        }
        for item in visible_notices
        if item.get("id") and item.get("school_name")
    ]
    records.sort(key=lambda item: str(item.get("notice_date") or ""), reverse=True)
    records.sort(key=lambda item: int(item.get("sort_order") or 0))
    schools = {
        (
            str(item.get("school_id") or ""),
            str(item.get("region") or ""),
            str(item.get("school_name") or ""),
        )
        for item in filter_notices
        if item.get("school_id") and item.get("region") and item.get("school_name")
    }
    return {
        "items": records[offset : offset + limit],
        "count": len(records),
        "filter_years": sorted({str(item.get("year") or "") for item in filter_notices if item.get("year")}, reverse=True),
        "filter_regions": sorted({str(item.get("region") or "") for item in filter_notices if item.get("region")}),
        "filter_schools": [
            {"id": school_id, "region": school_region, "name": school_name}
            for school_id, school_region, school_name in sorted(schools, key=lambda item: (item[1], item[2], item[0]))
        ],
        "statistics": index.get("statistics") or {},
    }


def list_regions(year: str | None = None, notice_type: str | None = None) -> dict[str, Any]:
    index = get_announcement_index()
    notices = _filtered(year=year, notice_type=notice_type)
    notices_by_region: dict[str, list[dict[str, Any]]] = {}
    for item in notices:
        notices_by_region.setdefault(str(item.get("region") or ""), []).append(item)

    items = []
    for region in index.get("regions") or []:
        name = str(region.get("name") or "")
        region_notices = notices_by_region.get(name, [])
        if not region_notices:
            continue
        items.append(
            {
                "name": name,
                "school_count": len({item.get("school_id") for item in region_notices}),
                "announcement_count": len(region_notices),
                "brochure_count": sum(1 for item in region_notices if item.get("notice_type") == "brochure"),
                "scoreline_count": sum(
                    1 for item in region_notices if item.get("notice_type") == "scoreline_retest"
                ),
            }
        )
    return {
        "version": index.get("version") or "",
        "year": _normalized_year(year),
        "notice_type": _normalized_type(notice_type),
        "items": items,
        "total_count": len(items),
        "statistics": index.get("statistics") or {},
    }


def list_schools(
    region: str | None = None,
    year: str | None = None,
    notice_type: str | None = None,
    keyword: str | None = None,
) -> dict[str, Any]:
    index = get_announcement_index()
    notices = _filtered(region=region, year=year, notice_type=notice_type, keyword=keyword)
    notices_by_school: dict[str, list[dict[str, Any]]] = {}
    for item in notices:
        notices_by_school.setdefault(str(item.get("school_id") or ""), []).append(item)
    schools = index.get("schools") or {}
    normalized_region = (region or "").strip()
    items = [
        _school_summary(schools[school_id], school_notices, region=normalized_region)
        for school_id, school_notices in notices_by_school.items()
        if school_id in schools
    ]
    items.sort(key=lambda item: (item["region"], item["name"]))
    return {
        "region": (region or "").strip(),
        "year": _normalized_year(year),
        "notice_type": _normalized_type(notice_type),
        "items": items,
        "total_count": len(items),
    }


def search_announcements(
    keyword: str,
    region: str | None = None,
    school_id: str | None = None,
    year: str | None = None,
    notice_type: str | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    notices = _filtered(
        keyword=keyword,
        region=region,
        school_id=school_id,
        year=year,
        notice_type=notice_type,
    )
    notices.sort(
        key=lambda item: (
            item.get("region") or "",
            item.get("school_name") or "",
            0 if item.get("notice_type") == "brochure" else 1,
            item.get("unit_name") or "",
            item.get("title") or "",
        )
    )
    total_count = len(notices)
    return {
        "keyword": (keyword or "").strip(),
        "items": [_notice_summary(item) for item in notices[:limit]],
        "total_count": total_count,
        "truncated": total_count > limit,
    }


def get_school_announcements(
    school_id: str,
    region: str | None = None,
    year: str | None = None,
    notice_type: str | None = None,
    keyword: str | None = None,
) -> dict[str, Any]:
    index = get_announcement_index()
    school = (index.get("schools") or {}).get(school_id)
    if not school:
        raise KeyError(school_id)
    notices = _filtered(
        school_id=school_id,
        region=region,
        year=year,
        notice_type=notice_type,
        keyword=keyword,
    )
    notices.sort(
        key=lambda item: (
            0 if item.get("notice_type") == "brochure" else 1,
            0 if item.get("notice_level") == "school" else 1,
            item.get("unit_name") or "",
            item.get("title") or "",
        )
    )
    return {
        "school": _school_summary(school, notices, region=(region or "").strip()),
        "items": [_notice_summary(item) for item in notices],
        "total_count": len(notices),
    }


def get_announcement(announcement_id: str) -> dict[str, Any]:
    announcement = (get_announcement_index().get("announcements") or {}).get(announcement_id)
    if not announcement:
        raise KeyError(announcement_id)
    return announcement
