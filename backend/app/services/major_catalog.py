"""Read-only Supabase lookup helpers for the 港澳台研究生专业目录."""

from __future__ import annotations

from collections import defaultdict
import gzip
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator

from app.db import get_supabase_admin
from app.services.supabase_resilience import is_missing_supabase_relation_error


VALID_EXAM_CODES = {"Z001", "Z002"}
EXAM_CODE_ORDER = ("Z001", "Z002")
PAGE_SIZE = 1000
SEARCH_RESULT_LIMIT = 80
CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "major_catalog.json.gz"


class MajorCatalogUnavailableError(RuntimeError):
    """Raised when the catalog migration or its latest import is unavailable."""


class MajorCatalogDatabaseUnavailableError(MajorCatalogUnavailableError):
    """Raised when Supabase has no completed catalog import yet."""


def _can_use_catalog_file_fallback(error: MajorCatalogDatabaseUnavailableError) -> bool:
    if str(error) == "专业目录尚未完成同步":
        return True
    cause = error.__cause__
    return bool(cause and is_missing_supabase_relation_error(cause))


def normalize_exam_code(exam_code: str | None) -> str:
    normalized = (exam_code or "").strip().upper()
    return normalized if normalized in VALID_EXAM_CODES else ""


def normalize_catalog_year(catalog_year: str | None) -> str:
    normalized = (catalog_year or "").strip()
    if not normalized:
        return ""
    return normalized if len(normalized) == 4 and normalized.isdigit() else "__invalid__"


def _ordered_exam_codes(codes: Iterable[str]) -> list[str]:
    values = {str(code or "") for code in codes}
    return [code for code in EXAM_CODE_ORDER if code in values]


def _execute(query_factory: Callable[[], Any]) -> Any:
    try:
        return query_factory().execute()
    except Exception as exc:
        raise MajorCatalogDatabaseUnavailableError("专业目录数据读取失败") from exc


def _get_supabase() -> Any:
    try:
        return get_supabase_admin()
    except Exception as exc:
        raise MajorCatalogDatabaseUnavailableError("专业目录数据库暂不可用") from exc


def _fetch_all(query_factory: Callable[[], Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        response = _execute(lambda: query_factory().range(offset, offset + PAGE_SIZE - 1))
        page = response.data or []
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            return rows
        offset += PAGE_SIZE


def _current_import(catalog_year: str = "") -> dict[str, Any]:
    """Return the latest completed import for the requested catalogue year.

    The original directory tables use a single ``sync_run_id`` for each
    snapshot.  Historical catalogues are stored in their own completed run, so
    choosing 2025 must never fall through to the most recent 2026 snapshot.
    ``全部目录`` retains its existing meaning: the full 2026 baseline plus its
    verified 2026 overlay.
    """
    supabase = _get_supabase()
    selected_year = catalog_year or "2026"
    response = _execute(
        lambda: (
            supabase.table("major_catalog_import_runs")
            .select("id,source_version,source_statistics,completed_at")
            .eq("status", "completed")
            .ilike("source_version", f"{selected_year}-%")
            .order("completed_at", desc=True)
            .limit(1)
        )
    )
    rows = response.data or []
    if not rows:
        raise MajorCatalogDatabaseUnavailableError("专业目录尚未完成同步")
    return rows[0]


def _uses_isolated_catalog_keys(catalog_year: str) -> bool:
    return bool(catalog_year and catalog_year != "2026" and catalog_year != "__invalid__")


def _stored_region_name(catalog_year: str, region_name: str) -> str:
    if not _uses_isolated_catalog_keys(catalog_year):
        return region_name
    return f"{catalog_year}::region::{region_name}"


def _display_region_name(catalog_year: str, region_name: str) -> str:
    prefix = f"{catalog_year}::region::"
    if _uses_isolated_catalog_keys(catalog_year) and region_name.startswith(prefix):
        return region_name[len(prefix) :]
    return region_name


def _database_catalog_year_school_ids(catalog_year: str) -> set[str] | None:
    # 2026 remains a verified overlay on the comprehensive baseline.  A
    # historical import is already an exact year-specific catalogue and must
    # not be filtered by the local 2026 overlay list.
    if catalog_year == "2026":
        return _catalog_year_school_ids(catalog_year)
    if catalog_year == "__invalid__":
        return set()
    return None


def _school_summary(school: dict[str, Any], exam_code: str = "", catalog_year: str = "") -> dict[str, Any]:
    suffix = f"_{exam_code.lower()}" if exam_code else ""
    return {
        "id": school.get("id") or "",
        "name": school.get("name") or "",
        "region": _display_region_name(catalog_year, school.get("region_name") or ""),
        "department_count": int(school.get(f"department_count{suffix}") or 0),
        "program_count": int(school.get(f"program_count{suffix}") or 0),
        "exam_codes": _ordered_exam_codes(school.get("exam_codes") or []),
    }


def _list_regions_from_database(exam_code: str | None = None, catalog_year: str | None = None) -> dict[str, Any]:
    normalized_exam_code = normalize_exam_code(exam_code)
    normalized_catalog_year = normalize_catalog_year(catalog_year)
    current_import = _current_import(normalized_catalog_year)
    allowed_school_ids = _database_catalog_year_school_ids(normalized_catalog_year)
    suffix = f"_{normalized_exam_code.lower()}" if normalized_exam_code else ""
    supabase = _get_supabase()
    regions = _fetch_all(
        lambda: (
            supabase.table("major_catalog_regions")
            .select(
                "name,sort_order,school_count,program_count,school_count_z001,school_count_z002,"
                "program_count_z001,program_count_z002"
            )
            .eq("sync_run_id", current_import["id"])
            .order("sort_order")
            .order("name")
        )
    )
    if allowed_school_ids is None:
        items = [
            {
                "name": _display_region_name(normalized_catalog_year, region.get("name") or ""),
                "school_count": int(region.get(f"school_count{suffix}") or 0),
                "program_count": int(region.get(f"program_count{suffix}") or 0),
            }
            for region in regions
            if int(region.get(f"school_count{suffix}") or 0) > 0
        ]
    else:
        schools = _fetch_all(
            lambda: (
                supabase.table("major_catalog_schools")
                .select(
                    "id,region_name,exam_codes,program_count,program_count_z001,program_count_z002"
                )
                .eq("sync_run_id", current_import["id"])
                .order("sort_order")
                .order("name")
            )
        )
        schools_by_region: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for school in schools:
            if school.get("id") not in allowed_school_ids:
                continue
            if normalized_exam_code and normalized_exam_code not in (school.get("exam_codes") or []):
                continue
            schools_by_region[school.get("region_name") or ""].append(school)
        items = [
            {
                "name": _display_region_name(normalized_catalog_year, region.get("name") or ""),
                "school_count": len(schools_by_region.get(region.get("name") or "", [])),
                "program_count": sum(
                    int(school.get(f"program_count{suffix}") or 0)
                    for school in schools_by_region.get(region.get("name") or "", [])
                ),
            }
            for region in regions
            if schools_by_region.get(region.get("name") or "")
        ]
    return {
        "version": current_import.get("source_version") or "",
        "statistics": current_import.get("source_statistics") or {},
        "catalog_year": normalized_catalog_year,
        "items": items,
    }


def _list_schools_from_database(
    region: str | None = None,
    keyword: str | None = None,
    exam_code: str | None = None,
    catalog_year: str | None = None,
) -> dict[str, Any]:
    normalized_region = (region or "").strip()
    normalized_keyword = (keyword or "").strip().lower()
    normalized_exam_code = normalize_exam_code(exam_code)
    normalized_catalog_year = normalize_catalog_year(catalog_year)
    current_import = _current_import(normalized_catalog_year)
    allowed_school_ids = _database_catalog_year_school_ids(normalized_catalog_year)
    stored_region = _stored_region_name(normalized_catalog_year, normalized_region) if normalized_region else ""
    supabase = _get_supabase()

    if normalized_region:
        existing_region = _execute(
            lambda: (
                supabase.table("major_catalog_regions")
                .select("name")
                .eq("sync_run_id", current_import["id"])
                .eq("name", stored_region)
                .limit(1)
            )
        )
        if not existing_region.data:
            raise KeyError(normalized_region)

    def build_query() -> Any:
        query = (
            supabase.table("major_catalog_schools")
            .select(
                "id,region_name,name,sort_order,exam_codes,department_count,program_count,"
                "department_count_z001,department_count_z002,program_count_z001,program_count_z002"
            )
            .eq("sync_run_id", current_import["id"])
        )
        if stored_region:
            query = query.eq("region_name", stored_region)
        return query.order("sort_order").order("name")

    schools = _fetch_all(build_query)
    items = [
        _school_summary(school, normalized_exam_code, normalized_catalog_year)
        for school in schools
        if (allowed_school_ids is None or school.get("id") in allowed_school_ids)
        and (not normalized_exam_code or normalized_exam_code in (school.get("exam_codes") or []))
        and (not normalized_keyword or normalized_keyword in str(school.get("name") or "").lower())
    ]
    return {
        "region": normalized_region,
        "exam_code": normalized_exam_code,
        "catalog_year": normalized_catalog_year,
        "count": len(items),
        "items": items,
    }


def _direction_matches_exam(direction: dict[str, Any], exam_code: str) -> bool:
    return not exam_code or direction.get("exam_code") == exam_code


def _program_matches_keyword(program: dict[str, Any], department_name: str, directions: list[dict[str, Any]], keyword: str) -> bool:
    if not keyword:
        return True
    values = [program.get("name") or "", program.get("code") or "", department_name]
    for direction in directions:
        values.extend([direction.get("name") or "", direction.get("tutor") or ""])
    return any(keyword in str(value).lower() for value in values)


def _ordered_match_scopes(scopes: Iterable[str]) -> list[str]:
    scope_order = ("专业", "专业代码", "研究方向", "导师")
    values = {str(scope or "") for scope in scopes}
    return [scope for scope in scope_order if scope in values]


def _catalog_search_result(
    *,
    school: dict[str, Any],
    program: dict[str, Any],
    department_name: str,
    scopes: Iterable[str],
    matched_directions: Iterable[str],
    exam_code: str,
    direction_count: int,
    catalog_year: str = "",
) -> dict[str, Any]:
    return {
        "school_id": school.get("id") or "",
        "school_name": school.get("name") or "",
        "region": _display_region_name(catalog_year, school.get("region_name") or school.get("region") or ""),
        "department_name": department_name or "未区分院系所",
        "program_id": program.get("id") or "",
        "program_name": program.get("name") or "",
        "program_code": program.get("code") or "",
        "exam_codes": _ordered_exam_codes(program.get("exam_codes") or []),
        "direction_count": direction_count,
        "match_scopes": _ordered_match_scopes(scopes),
        "matched_directions": list(dict.fromkeys(item for item in matched_directions if item))[:3],
        "exam_code": exam_code,
    }


def _get_school_programs_from_database(
    school_id: str,
    keyword: str | None = None,
    exam_code: str | None = None,
    catalog_year: str | None = None,
) -> dict[str, Any]:
    normalized_keyword = (keyword or "").strip().lower()
    normalized_exam_code = normalize_exam_code(exam_code)
    normalized_catalog_year = normalize_catalog_year(catalog_year)
    current_import = _current_import(normalized_catalog_year)
    allowed_school_ids = _database_catalog_year_school_ids(normalized_catalog_year)
    supabase = _get_supabase()
    school_response = _execute(
        lambda: (
            supabase.table("major_catalog_schools")
            .select(
                "id,region_name,name,exam_codes,department_count,program_count,"
                "department_count_z001,department_count_z002,program_count_z001,program_count_z002"
            )
            .eq("sync_run_id", current_import["id"])
            .eq("id", school_id)
            .limit(1)
        )
    )
    school_rows = school_response.data or []
    if not school_rows:
        raise KeyError(school_id)
    school = school_rows[0]
    if allowed_school_ids is not None and school_id not in allowed_school_ids:
        raise KeyError(school_id)

    departments = _fetch_all(
        lambda: (
            supabase.table("major_catalog_departments")
            .select("id,name,sort_order")
            .eq("sync_run_id", current_import["id"])
            .eq("school_id", school_id)
            .order("sort_order")
            .order("name")
        )
    )
    programs = _fetch_all(
        lambda: (
            supabase.table("major_catalog_programs")
            .select("id,department_id,name,code,sort_order,exam_codes,degree_options,study_mode_options,direction_count")
            .eq("sync_run_id", current_import["id"])
            .eq("school_id", school_id)
            .order("sort_order")
            .order("name")
        )
    )
    directions = _fetch_all(
        lambda: (
            supabase.table("major_catalog_directions")
            .select("program_id,name,tutor,exam_code,degree,study_mode,sort_order")
            .eq("sync_run_id", current_import["id"])
            .eq("school_id", school_id)
            .order("program_id")
            .order("sort_order")
        )
    )
    directions_by_program: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for direction in directions:
        directions_by_program[direction.get("program_id") or ""].append(direction)

    programs_by_department: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for program in programs:
        program_directions = [
            direction
            for direction in directions_by_program.get(program.get("id") or "", [])
            if _direction_matches_exam(direction, normalized_exam_code)
        ]
        if not program_directions:
            continue
        department_name = next(
            (item.get("name") or "未区分院系所" for item in departments if item.get("id") == program.get("department_id")),
            "未区分院系所",
        )
        if not _program_matches_keyword(program, department_name, program_directions, normalized_keyword):
            continue
        programs_by_department[program.get("department_id") or ""].append(
            {
                "id": program.get("id") or "",
                "name": program.get("name") or "",
                "code": program.get("code") or "",
                "exam_codes": _ordered_exam_codes(direction.get("exam_code") or "" for direction in program_directions),
                "degree_options": program.get("degree_options") or [],
                "study_mode_options": program.get("study_mode_options") or [],
                "direction_count": len(program_directions),
                "directions": [
                    {
                        "name": direction.get("name") or "",
                        "tutor": direction.get("tutor") or "",
                        "exam_code": direction.get("exam_code") or "",
                        "degree": direction.get("degree") or "",
                        "study_mode": direction.get("study_mode") or "",
                    }
                    for direction in program_directions
                ],
            }
        )

    result_departments: list[dict[str, Any]] = []
    for department in departments:
        department_programs = programs_by_department.get(department.get("id") or "", [])
        if department_programs:
            result_departments.append(
                {
                    "name": department.get("name") or "未区分院系所",
                    "program_count": len(department_programs),
                    "programs": department_programs,
                }
            )
    program_count = sum(item["program_count"] for item in result_departments)
    return {
        "school": {
            **_school_summary(school, normalized_exam_code, normalized_catalog_year),
            "department_count": len(result_departments),
            "program_count": program_count,
        },
        "exam_code": normalized_exam_code,
        "catalog_year": normalized_catalog_year,
        "keyword": normalized_keyword,
        "departments": result_departments,
    }


def _search_catalog_from_database(
    keyword: str,
    region: str | None = None,
    exam_code: str | None = None,
    catalog_year: str | None = None,
) -> dict[str, Any]:
    normalized_keyword = keyword.strip().lower()
    normalized_region = (region or "").strip()
    normalized_exam_code = normalize_exam_code(exam_code)
    normalized_catalog_year = normalize_catalog_year(catalog_year)
    current_import = _current_import(normalized_catalog_year)
    allowed_school_ids = _database_catalog_year_school_ids(normalized_catalog_year)
    stored_region = _stored_region_name(normalized_catalog_year, normalized_region) if normalized_region else ""
    supabase = _get_supabase()

    schools = _fetch_all(
        lambda: (
            supabase.table("major_catalog_schools")
            .select(
                "id,region_name,name,sort_order,exam_codes,department_count,program_count,"
                "department_count_z001,department_count_z002,program_count_z001,program_count_z002"
            )
            .eq("sync_run_id", current_import["id"])
            .order("sort_order")
            .order("name")
        )
    )
    all_regions = {
        _display_region_name(normalized_catalog_year, str(school.get("region_name") or ""))
        for school in schools
    }
    if normalized_region and normalized_region not in all_regions:
        raise KeyError(normalized_region)

    eligible_schools = [
        school
        for school in schools
        if (allowed_school_ids is None or school.get("id") in allowed_school_ids)
        and (not stored_region or school.get("region_name") == stored_region)
        and (not normalized_exam_code or normalized_exam_code in (school.get("exam_codes") or []))
    ]
    school_by_id = {str(school.get("id") or ""): school for school in eligible_schools}
    eligible_school_ids = set(school_by_id)
    if not eligible_school_ids:
        return {
            "keyword": normalized_keyword,
            "region": normalized_region,
            "exam_code": normalized_exam_code,
            "catalog_year": normalized_catalog_year,
            "school_count": 0,
            "program_count": 0,
            "total_count": 0,
            "truncated": False,
            "schools": [],
            "programs": [],
        }

    like_keyword = f"%{normalized_keyword}%"
    programs_by_id: dict[str, dict[str, Any]] = {}
    program_matches: dict[str, dict[str, Any]] = {}

    def keep_program(program: dict[str, Any]) -> bool:
        return (
            program.get("school_id") in eligible_school_ids
            and (not normalized_exam_code or normalized_exam_code in (program.get("exam_codes") or []))
        )

    def add_program_match(program: dict[str, Any], scope: str, direction_name: str = "") -> None:
        program_id = str(program.get("id") or "")
        if not program_id:
            return
        programs_by_id[program_id] = program
        match = program_matches.setdefault(program_id, {"scopes": set(), "matched_directions": []})
        match["scopes"].add(scope)
        if direction_name:
            match["matched_directions"].append(direction_name)

    matching_program_names = _fetch_all(
        lambda: (
            supabase.table("major_catalog_programs")
            .select("id,school_id,department_id,name,code,sort_order,exam_codes,direction_count")
            .eq("sync_run_id", current_import["id"])
            .ilike("name", like_keyword)
            .order("sort_order")
            .order("name")
        )
    )
    for program in matching_program_names:
        if keep_program(program):
            add_program_match(program, "专业")

    matching_program_codes = _fetch_all(
        lambda: (
            supabase.table("major_catalog_programs")
            .select("id,school_id,department_id,name,code,sort_order,exam_codes,direction_count")
            .eq("sync_run_id", current_import["id"])
            .ilike("code", like_keyword)
            .order("sort_order")
            .order("name")
        )
    )
    for program in matching_program_codes:
        if keep_program(program):
            add_program_match(program, "专业代码")

    matching_direction_names = _fetch_all(
        lambda: (
            supabase.table("major_catalog_directions")
            .select("program_id,school_id,name,tutor,exam_code")
            .eq("sync_run_id", current_import["id"])
            .ilike("name", like_keyword)
            .order("sort_order")
        )
    )
    matching_direction_tutors = _fetch_all(
        lambda: (
            supabase.table("major_catalog_directions")
            .select("program_id,school_id,name,tutor,exam_code")
            .eq("sync_run_id", current_import["id"])
            .ilike("tutor", like_keyword)
            .order("sort_order")
        )
    )
    matching_directions = [
        *matching_direction_names,
        *matching_direction_tutors,
    ]
    missing_program_ids = {
        str(direction.get("program_id") or "")
        for direction in matching_directions
        if direction.get("school_id") in eligible_school_ids
        and _direction_matches_exam(direction, normalized_exam_code)
        and str(direction.get("program_id") or "") not in programs_by_id
    }
    missing_program_id_list = list(missing_program_ids)
    for start in range(0, len(missing_program_id_list), 150):
        program_ids = missing_program_id_list[start : start + 150]
        if not program_ids:
            continue
        related_programs = _fetch_all(
            lambda program_ids=program_ids: (
                supabase.table("major_catalog_programs")
                .select("id,school_id,department_id,name,code,sort_order,exam_codes,direction_count")
                .eq("sync_run_id", current_import["id"])
                .in_("id", program_ids)
            )
        )
        for program in related_programs:
            if keep_program(program):
                programs_by_id[str(program.get("id") or "")] = program

    directions_by_program: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for direction in matching_directions:
        program_id = str(direction.get("program_id") or "")
        if (
            direction.get("school_id") not in eligible_school_ids
            or not _direction_matches_exam(direction, normalized_exam_code)
            or program_id not in programs_by_id
        ):
            continue
        directions_by_program[program_id].append(direction)
        if normalized_keyword in str(direction.get("name") or "").lower():
            add_program_match(programs_by_id[program_id], "研究方向", str(direction.get("name") or ""))
        if normalized_keyword in str(direction.get("tutor") or "").lower():
            add_program_match(programs_by_id[program_id], "导师", str(direction.get("name") or ""))

    matching_program_ids = set(program_matches)
    department_by_id: dict[str, dict[str, Any]] = {}
    if matching_program_ids:
        department_ids = {str(programs_by_id[program_id].get("department_id") or "") for program_id in matching_program_ids}
        for start in range(0, len(department_ids), 150):
            ids = list(department_ids)[start : start + 150]
            if not ids:
                continue
            departments = _fetch_all(
                lambda ids=ids: (
                    supabase.table("major_catalog_departments")
                    .select("id,name,sort_order")
                    .eq("sync_run_id", current_import["id"])
                    .in_("id", ids)
                )
            )
            department_by_id.update({str(item.get("id") or ""): item for item in departments})

    school_matches = [
        _school_summary(school, normalized_exam_code, normalized_catalog_year)
        for school in eligible_schools
        if normalized_keyword in str(school.get("name") or "").lower()
    ]
    program_items = [
        _catalog_search_result(
            school=school_by_id[str(program.get("school_id") or "")],
            program=program,
            department_name=(department_by_id.get(str(program.get("department_id") or "")) or {}).get("name") or "未区分院系所",
            scopes=match["scopes"],
            matched_directions=match["matched_directions"],
            exam_code=normalized_exam_code,
            direction_count=len(directions_by_program.get(program_id) or []) or int(program.get("direction_count") or 0),
            catalog_year=normalized_catalog_year,
        )
        for program_id, match in program_matches.items()
        if (program := programs_by_id.get(program_id))
        and str(program.get("school_id") or "") in school_by_id
    ]
    program_items.sort(
        key=lambda item: (
            int(school_by_id[item["school_id"]].get("sort_order") or 0),
            int((department_by_id.get(str(programs_by_id[item["program_id"]].get("department_id") or "")) or {}).get("sort_order") or 0),
            int(programs_by_id[item["program_id"]].get("sort_order") or 0),
            item["program_name"],
        )
    )
    return {
        "keyword": normalized_keyword,
        "region": normalized_region,
        "exam_code": normalized_exam_code,
        "catalog_year": normalized_catalog_year,
        "school_count": len(school_matches),
        "program_count": len(program_items),
        "total_count": len(school_matches) + len(program_items),
        "truncated": len(school_matches) > SEARCH_RESULT_LIMIT or len(program_items) > SEARCH_RESULT_LIMIT,
        "schools": school_matches[:SEARCH_RESULT_LIMIT],
        "programs": program_items[:SEARCH_RESULT_LIMIT],
    }


@lru_cache(maxsize=1)
def get_major_catalog() -> dict[str, Any]:
    """Load the pre-existing generated index while the database is not ready."""

    if not CATALOG_PATH.is_file():
        raise MajorCatalogUnavailableError("专业目录数据尚未生成")
    try:
        with gzip.open(CATALOG_PATH, "rt", encoding="utf-8") as catalog_file:
            return json.load(catalog_file)
    except (OSError, json.JSONDecodeError) as exc:
        raise MajorCatalogUnavailableError("专业目录本地索引读取失败") from exc


def _catalog_year_school_ids(catalog_year: str) -> set[str] | None:
    if not catalog_year:
        return None
    filters = get_major_catalog().get("year_filters") or {}
    details = filters.get(catalog_year) if isinstance(filters, dict) else None
    if not isinstance(details, dict):
        return set()
    return {str(school_id) for school_id in details.get("school_ids") or [] if str(school_id)}


def _catalog_schools(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return catalog.get("schools") or {}


def _file_program_matches_exam(program: dict[str, Any], exam_code: str) -> bool:
    return not exam_code or exam_code in (program.get("exam_codes") or [])


def _iter_file_programs(school: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for department in school.get("departments") or []:
        yield from department.get("programs") or []


def _file_school_matches_exam(school: dict[str, Any], exam_code: str) -> bool:
    return not exam_code or exam_code in (school.get("exam_codes") or [])


def _file_school_summary(school: dict[str, Any], exam_code: str = "") -> dict[str, Any]:
    matching_programs = [program for program in _iter_file_programs(school) if _file_program_matches_exam(program, exam_code)]
    matching_departments = sum(
        1
        for department in school.get("departments") or []
        if any(_file_program_matches_exam(program, exam_code) for program in department.get("programs") or [])
    )
    matching_exam_codes = _ordered_exam_codes(
        code for program in matching_programs for code in (program.get("exam_codes") or [])
    )
    return {
        "id": school.get("id") or "",
        "name": school.get("name") or "",
        "region": school.get("region") or "",
        "department_count": matching_departments,
        "program_count": len(matching_programs),
        "exam_codes": matching_exam_codes,
    }


def _list_regions_from_file(exam_code: str | None = None, catalog_year: str | None = None) -> dict[str, Any]:
    catalog = get_major_catalog()
    normalized_exam_code = normalize_exam_code(exam_code)
    normalized_catalog_year = normalize_catalog_year(catalog_year)
    allowed_school_ids = _catalog_year_school_ids(normalized_catalog_year)
    schools = _catalog_schools(catalog)
    items: list[dict[str, Any]] = []
    for region in catalog.get("regions") or []:
        region_schools = [
            schools[school_id]
            for school_id in region.get("school_ids") or []
            if school_id in schools and (allowed_school_ids is None or school_id in allowed_school_ids)
        ]
        region_schools = [school for school in region_schools if _file_school_matches_exam(school, normalized_exam_code)]
        if not region_schools:
            continue
        items.append(
            {
                "name": region.get("name") or "",
                "school_count": len(region_schools),
                "program_count": sum(
                    1
                    for school in region_schools
                    for program in _iter_file_programs(school)
                    if _file_program_matches_exam(program, normalized_exam_code)
                ),
            }
        )
    return {
        "version": catalog.get("version") or "",
        "statistics": catalog.get("statistics") or {},
        "catalog_year": normalized_catalog_year,
        "items": items,
    }


def _list_schools_from_file(
    region: str | None = None,
    keyword: str | None = None,
    exam_code: str | None = None,
    catalog_year: str | None = None,
) -> dict[str, Any]:
    catalog = get_major_catalog()
    schools = _catalog_schools(catalog)
    normalized_region = (region or "").strip()
    normalized_keyword = (keyword or "").strip().lower()
    normalized_exam_code = normalize_exam_code(exam_code)
    normalized_catalog_year = normalize_catalog_year(catalog_year)
    allowed_school_ids = _catalog_year_school_ids(normalized_catalog_year)
    if normalized_region:
        selected_region = next((item for item in catalog.get("regions") or [] if item.get("name") == normalized_region), None)
        if selected_region is None:
            raise KeyError(normalized_region)
        school_ids = selected_region.get("school_ids") or []
    else:
        school_ids = [school_id for item in catalog.get("regions") or [] for school_id in item.get("school_ids") or []]
    items = [
        _file_school_summary(school, normalized_exam_code)
        for school_id in school_ids
        if (school := schools.get(school_id))
        and (allowed_school_ids is None or school_id in allowed_school_ids)
        and _file_school_matches_exam(school, normalized_exam_code)
        and (not normalized_keyword or normalized_keyword in str(school.get("name") or "").lower())
    ]
    return {
        "region": normalized_region,
        "exam_code": normalized_exam_code,
        "catalog_year": normalized_catalog_year,
        "count": len(items),
        "items": items,
    }


def _get_school_programs_from_file(
    school_id: str,
    keyword: str | None = None,
    exam_code: str | None = None,
    catalog_year: str | None = None,
) -> dict[str, Any]:
    catalog = get_major_catalog()
    school = _catalog_schools(catalog).get(school_id)
    normalized_catalog_year = normalize_catalog_year(catalog_year)
    allowed_school_ids = _catalog_year_school_ids(normalized_catalog_year)
    if school is None or (allowed_school_ids is not None and school_id not in allowed_school_ids):
        raise KeyError(school_id)
    normalized_keyword = (keyword or "").strip().lower()
    normalized_exam_code = normalize_exam_code(exam_code)
    departments: list[dict[str, Any]] = []
    program_count = 0
    for department in school.get("departments") or []:
        department_name = department.get("name") or "未区分院系所"
        programs: list[dict[str, Any]] = []
        for program in department.get("programs") or []:
            if not _file_program_matches_exam(program, normalized_exam_code):
                continue
            directions = [
                direction
                for direction in program.get("directions") or []
                if _direction_matches_exam(direction, normalized_exam_code)
            ]
            if not directions or not _program_matches_keyword(program, department_name, directions, normalized_keyword):
                continue
            programs.append(
                {
                    "id": program.get("id") or "",
                    "name": program.get("name") or "",
                    "code": program.get("code") or "",
                    "exam_codes": _ordered_exam_codes(direction.get("exam_code") or "" for direction in directions),
                    "degree_options": program.get("degree_options") or [],
                    "study_mode_options": program.get("study_mode_options") or [],
                    "direction_count": len(directions),
                    "directions": directions,
                }
            )
        if programs:
            program_count += len(programs)
            departments.append({"name": department_name, "program_count": len(programs), "programs": programs})
    return {
        "school": {
            **_file_school_summary(school, normalized_exam_code),
            "department_count": len(departments),
            "program_count": program_count,
        },
        "exam_code": normalized_exam_code,
        "catalog_year": normalized_catalog_year,
        "keyword": normalized_keyword,
        "departments": departments,
    }


def _search_catalog_from_file(
    keyword: str,
    region: str | None = None,
    exam_code: str | None = None,
    catalog_year: str | None = None,
) -> dict[str, Any]:
    catalog = get_major_catalog()
    schools = _catalog_schools(catalog)
    normalized_keyword = keyword.strip().lower()
    normalized_region = (region or "").strip()
    normalized_exam_code = normalize_exam_code(exam_code)
    normalized_catalog_year = normalize_catalog_year(catalog_year)
    allowed_school_ids = _catalog_year_school_ids(normalized_catalog_year)
    known_regions = {str(item.get("name") or "") for item in catalog.get("regions") or []}
    if normalized_region and normalized_region not in known_regions:
        raise KeyError(normalized_region)

    eligible_schools: list[dict[str, Any]] = []
    school_order: dict[str, int] = {}
    for position, region_item in enumerate(catalog.get("regions") or []):
        for school_position, school_id in enumerate(region_item.get("school_ids") or []):
            school = schools.get(school_id)
            if (
                school is None
                or (allowed_school_ids is not None and school_id not in allowed_school_ids)
                or (normalized_region and school.get("region") != normalized_region)
                or not _file_school_matches_exam(school, normalized_exam_code)
            ):
                continue
            eligible_schools.append(school)
            school_order[str(school_id)] = position * 1000 + school_position

    school_matches = [
        _file_school_summary(school, normalized_exam_code)
        for school in eligible_schools
        if normalized_keyword in str(school.get("name") or "").lower()
    ]
    program_items_with_order: list[tuple[tuple[int, int, int, str], dict[str, Any]]] = []
    for school in eligible_schools:
        school_id = str(school.get("id") or "")
        for department_position, department in enumerate(school.get("departments") or []):
            department_name = department.get("name") or "未区分院系所"
            for program_position, program in enumerate(department.get("programs") or []):
                if not _file_program_matches_exam(program, normalized_exam_code):
                    continue
                scopes: set[str] = set()
                matched_directions: list[str] = []
                if normalized_keyword in str(program.get("name") or "").lower():
                    scopes.add("专业")
                if normalized_keyword in str(program.get("code") or "").lower():
                    scopes.add("专业代码")
                filtered_directions = [
                    direction
                    for direction in program.get("directions") or []
                    if _direction_matches_exam(direction, normalized_exam_code)
                ]
                for direction in filtered_directions:
                    direction_name = str(direction.get("name") or "")
                    tutor = str(direction.get("tutor") or "")
                    if normalized_keyword in direction_name.lower():
                        scopes.add("研究方向")
                        matched_directions.append(direction_name)
                    if tutor and normalized_keyword in tutor.lower():
                        scopes.add("导师")
                        matched_directions.append(direction_name)
                if not scopes:
                    continue
                item = _catalog_search_result(
                    school=school,
                    program=program,
                    department_name=department_name,
                    scopes=scopes,
                    matched_directions=matched_directions,
                    exam_code=normalized_exam_code,
                    direction_count=len(filtered_directions),
                )
                program_items_with_order.append(
                    (
                        (school_order.get(school_id, 0), department_position, program_position, item["program_name"]),
                        item,
                    )
                )
    program_items_with_order.sort(key=lambda item: item[0])
    program_items = [item for _, item in program_items_with_order]
    return {
        "keyword": normalized_keyword,
        "region": normalized_region,
        "exam_code": normalized_exam_code,
        "catalog_year": normalized_catalog_year,
        "school_count": len(school_matches),
        "program_count": len(program_items),
        "total_count": len(school_matches) + len(program_items),
        "truncated": len(school_matches) > SEARCH_RESULT_LIMIT or len(program_items) > SEARCH_RESULT_LIMIT,
        "schools": school_matches[:SEARCH_RESULT_LIMIT],
        "programs": program_items[:SEARCH_RESULT_LIMIT],
    }


def list_regions(exam_code: str | None = None, catalog_year: str | None = None) -> dict[str, Any]:
    try:
        return _list_regions_from_database(exam_code=exam_code, catalog_year=catalog_year)
    except MajorCatalogDatabaseUnavailableError as error:
        if _can_use_catalog_file_fallback(error):
            return _list_regions_from_file(exam_code=exam_code, catalog_year=catalog_year)
        raise


def list_schools(
    region: str | None = None,
    keyword: str | None = None,
    exam_code: str | None = None,
    catalog_year: str | None = None,
) -> dict[str, Any]:
    try:
        return _list_schools_from_database(
            region=region,
            keyword=keyword,
            exam_code=exam_code,
            catalog_year=catalog_year,
        )
    except MajorCatalogDatabaseUnavailableError as error:
        if _can_use_catalog_file_fallback(error):
            return _list_schools_from_file(
                region=region,
                keyword=keyword,
                exam_code=exam_code,
                catalog_year=catalog_year,
            )
        raise


def search_catalog(
    keyword: str,
    region: str | None = None,
    exam_code: str | None = None,
    catalog_year: str | None = None,
) -> dict[str, Any]:
    try:
        return _search_catalog_from_database(
            keyword=keyword,
            region=region,
            exam_code=exam_code,
            catalog_year=catalog_year,
        )
    except MajorCatalogDatabaseUnavailableError as error:
        if _can_use_catalog_file_fallback(error):
            return _search_catalog_from_file(
                keyword=keyword,
                region=region,
                exam_code=exam_code,
                catalog_year=catalog_year,
            )
        raise


def get_school_programs(
    school_id: str,
    keyword: str | None = None,
    exam_code: str | None = None,
    catalog_year: str | None = None,
) -> dict[str, Any]:
    try:
        return _get_school_programs_from_database(
            school_id=school_id,
            keyword=keyword,
            exam_code=exam_code,
            catalog_year=catalog_year,
        )
    except MajorCatalogDatabaseUnavailableError as error:
        if _can_use_catalog_file_fallback(error):
            return _get_school_programs_from_file(
                school_id=school_id,
                keyword=keyword,
                exam_code=exam_code,
                catalog_year=catalog_year,
            )
        raise
