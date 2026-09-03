from __future__ import annotations

import unittest
import inspect
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.params import Depends
from pydantic import ValidationError

from app.schemas.major_catalog import (
    MajorCatalogFavoriteRef,
    MajorCatalogFavoriteStatusRequest,
)
from app.services import major_catalog_favorites
from app.services import major_catalog as major_catalog_service
from app.routes import major_catalog
from app.dependencies import get_current_user_id


USER_ID = "11111111-1111-4111-8111-111111111111"
OTHER_USER_ID = "22222222-2222-4222-8222-222222222222"
FAVORITE_ID_A = "33333333-3333-4333-8333-333333333333"
FAVORITE_ID_B = "44444444-4444-4444-8444-444444444444"
FAVORITE_ID_C = "55555555-5555-4555-8555-555555555555"


class _FavoriteQuery:
    def __init__(self, client, table_name: str):
        self.client = client
        self.table_name = table_name
        self.action = "select"
        self.payload: dict = {}
        self.filters: list[tuple[str, object]] = []
        self.in_filters: list[tuple[str, set[object]]] = []
        self.orders: list[tuple[str, bool]] = []
        self.limit_value: int | None = None
        self.cursor_applied = False
        self.on_conflict = ""

    def select(self, *_args, **_kwargs):
        self.action = "select"
        return self

    def upsert(self, payload: dict, *, on_conflict: str):
        self.action = "upsert"
        self.payload = dict(payload)
        self.on_conflict = on_conflict
        return self

    def delete(self):
        self.action = "delete"
        return self

    def eq(self, field: str, value: object):
        self.filters.append((field, value))
        return self

    def in_(self, field: str, values):
        self.in_filters.append((field, set(values)))
        return self

    def or_(self, _expression: str):
        self.cursor_applied = True
        return self

    def order(self, field: str, *, desc: bool = False):
        self.orders.append((field, desc))
        return self

    def limit(self, value: int):
        self.limit_value = value
        return self

    def _matches(self, row: dict) -> bool:
        return (
            all(row.get(field) == value for field, value in self.filters)
            and all(row.get(field) in values for field, values in self.in_filters)
        )

    def execute(self):
        if self.table_name != major_catalog_favorites.FAVORITE_TABLE:
            raise AssertionError(f"unexpected table: {self.table_name}")
        self.client.queries.append(self)
        rows = self.client.rows
        if self.action == "upsert":
            key = tuple(self.payload.get(field) for field in self.on_conflict.split(","))
            matched = next(
                (
                    row
                    for row in rows
                    if tuple(row.get(field) for field in self.on_conflict.split(",")) == key
                ),
                None,
            )
            if matched is None:
                matched = {
                    "id": f"generated-{len(rows) + 1}",
                    "created_at": "2026-09-04T08:00:00+00:00",
                    "updated_at": "2026-09-04T08:00:00+00:00",
                    **self.payload,
                }
                rows.append(matched)
            else:
                matched.update(self.payload)
            return SimpleNamespace(data=[dict(matched)], count=None)

        matching = [row for row in rows if self._matches(row)]
        for field, descending in reversed(self.orders):
            matching.sort(key=lambda row: str(row.get(field) or ""), reverse=descending)
        if self.cursor_applied:
            # The fixture rows are strictly ordered; the first page is sufficient
            # to ensure a cursor query follows the keyset branch.
            matching = matching[1:]
        count = len(matching)
        if self.limit_value is not None:
            matching = matching[: self.limit_value]
        if self.action == "delete":
            deleted = [dict(row) for row in matching]
            self.client.rows[:] = [row for row in rows if row not in matching]
            return SimpleNamespace(data=deleted, count=None)
        return SimpleNamespace(data=[dict(row) for row in matching], count=count)


class _FavoriteClient:
    def __init__(self, rows: list[dict] | None = None):
        self.rows = [dict(row) for row in (rows or [])]
        self.queries: list[_FavoriteQuery] = []

    def table(self, table_name: str):
        return _FavoriteQuery(self, table_name)


def _favorite_row(
    *,
    favorite_id: str,
    target_id: str,
    created_at: str,
    user_id: str = USER_ID,
    target_type: str = "school",
) -> dict:
    return {
        "id": favorite_id,
        "user_id": user_id,
        "catalog_year": "2026",
        "target_type": target_type,
        "target_id": target_id,
        "school_id": "school-1",
        "snapshot": {"school_id": "school-1", "school_name": "示例大学"},
        "created_at": created_at,
        "updated_at": created_at,
    }


class MajorCatalogFavoriteSchemaTests(unittest.TestCase):
    def test_favorite_reference_accepts_school_or_program_with_catalog_year(self):
        school = MajorCatalogFavoriteRef(
            catalog_year="2026",
            target_type="school",
            target_id="school-1",
        )
        program = MajorCatalogFavoriteRef(
            catalog_year="2025",
            target_type="program",
            target_id="2025::program-1",
        )

        self.assertEqual(school.target_type, "school")
        self.assertEqual(program.target_type, "program")

    def test_favorite_reference_rejects_invalid_year_type_and_empty_target(self):
        for payload in (
            {"catalog_year": "26", "target_type": "school", "target_id": "school-1"},
            {"catalog_year": "2026", "target_type": "department", "target_id": "dept-1"},
            {"catalog_year": "2026", "target_type": "program", "target_id": ""},
        ):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                MajorCatalogFavoriteRef(**payload)

    def test_status_request_caps_batch_at_two_hundred_targets(self):
        item = {"catalog_year": "2026", "target_type": "school", "target_id": "school-1"}
        request = MajorCatalogFavoriteStatusRequest(items=[item] * 200)
        self.assertEqual(len(request.items), 200)

        with self.assertRaises(ValidationError):
            MajorCatalogFavoriteStatusRequest(items=[item] * 201)

    def test_status_request_accepts_the_frontend_refs_contract(self):
        item = {"catalog_year": "2026", "target_type": "school", "target_id": "school-1"}

        request = MajorCatalogFavoriteStatusRequest.model_validate({"refs": [item]})

        self.assertEqual(request.items[0].target_id, "school-1")
        self.assertIn("refs", request.model_dump(by_alias=True))


class MajorCatalogFavoriteServiceTests(unittest.TestCase):
    def test_catalog_file_fallback_resolves_school_and_program_snapshots(self):
        catalog = {
            "schools": {
                "school-1": {
                    "id": "school-1",
                    "name": "示例大学",
                    "region": "北京",
                    "exam_codes": ["Z001", "Z002"],
                    "departments": [{
                        "id": "department-1",
                        "name": "经济学院",
                        "programs": [{
                            "id": "program-1",
                            "department_id": "department-1",
                            "name": "应用经济学",
                            "code": "020200",
                            "exam_codes": ["Z002"],
                            "degree_options": ["学术学位"],
                            "study_mode_options": ["全日制"],
                            "direction_count": 2,
                        }],
                    }],
                },
            },
        }
        database_unavailable = major_catalog_service.MajorCatalogDatabaseUnavailableError(
            "专业目录尚未完成同步"
        )
        references = [
            {"catalog_year": "2026", "target_type": "school", "target_id": "school-1"},
            {"catalog_year": "2026", "target_type": "program", "target_id": "program-1"},
        ]
        with (
            patch.object(
                major_catalog_service,
                "_resolve_major_catalog_favorite_targets_from_database",
                side_effect=database_unavailable,
            ),
            patch.object(major_catalog_service, "get_major_catalog", return_value=catalog),
        ):
            resolved = major_catalog_service.resolve_major_catalog_favorite_targets(references)

        school = resolved[("2026", "school", "school-1")]
        program = resolved[("2026", "program", "program-1")]
        self.assertEqual(school["school_name"], "示例大学")
        self.assertEqual(school["department_count"], 1)
        self.assertEqual(school["program_count"], 1)
        self.assertEqual(program["school_id"], "school-1")
        self.assertEqual(program["department_name"], "经济学院")
        self.assertEqual(program["program_name"], "应用经济学")
        self.assertEqual(program["program_code"], "020200")

    def test_save_is_idempotent_and_uses_unique_conflict_key(self):
        client = _FavoriteClient()
        snapshot = {"school_id": "school-1", "school_name": "示例大学"}
        with (
            patch.object(major_catalog_favorites, "get_supabase_admin", return_value=client),
            patch.object(
                major_catalog_favorites,
                "resolve_major_catalog_favorite_target",
                return_value=snapshot,
            ),
        ):
            first = major_catalog_favorites.save_major_catalog_favorite(
                user_id=USER_ID,
                catalog_year="2026",
                target_type="school",
                target_id="school-1",
            )
            second = major_catalog_favorites.save_major_catalog_favorite(
                user_id=USER_ID,
                catalog_year="2026",
                target_type="school",
                target_id="school-1",
            )

        self.assertTrue(first["is_favorited"])
        self.assertTrue(second["is_favorited"])
        self.assertEqual(len(client.rows), 1)
        upserts = [query for query in client.queries if query.action == "upsert"]
        self.assertEqual(len(upserts), 2)
        self.assertTrue(all(
            query.on_conflict == "user_id,catalog_year,target_type,target_id"
            for query in upserts
        ))

    def test_save_rejects_target_that_is_not_in_the_requested_catalog_year(self):
        client = _FavoriteClient()
        with (
            patch.object(major_catalog_favorites, "get_supabase_admin", return_value=client),
            patch.object(major_catalog_favorites, "resolve_major_catalog_favorite_target", return_value=None),
            self.assertRaises(KeyError),
        ):
            major_catalog_favorites.save_major_catalog_favorite(
                user_id=USER_ID,
                catalog_year="2025",
                target_type="program",
                target_id="2025::missing-program",
            )

        self.assertEqual(client.rows, [])

    def test_delete_is_idempotent_and_never_removes_another_users_favorite(self):
        client = _FavoriteClient([
            _favorite_row(
                favorite_id=FAVORITE_ID_A,
                target_id="school-1",
                created_at="2026-09-04T10:00:00+00:00",
            ),
            _favorite_row(
                favorite_id=FAVORITE_ID_B,
                target_id="school-1",
                user_id=OTHER_USER_ID,
                created_at="2026-09-04T09:00:00+00:00",
            ),
        ])
        with patch.object(major_catalog_favorites, "get_supabase_admin", return_value=client):
            first = major_catalog_favorites.delete_major_catalog_favorite(
                user_id=USER_ID,
                catalog_year="2026",
                target_type="school",
                target_id="school-1",
            )
            second = major_catalog_favorites.delete_major_catalog_favorite(
                user_id=USER_ID,
                catalog_year="2026",
                target_type="school",
                target_id="school-1",
            )

        self.assertFalse(first["is_favorited"])
        self.assertFalse(second["is_favorited"])
        self.assertEqual([row["user_id"] for row in client.rows], [OTHER_USER_ID])
        deletes = [query for query in client.queries if query.action == "delete"]
        self.assertEqual(len(deletes), 2)
        self.assertTrue(all(("user_id", USER_ID) in query.filters for query in deletes))

    def test_list_uses_keyset_cursor_and_resolves_current_catalog_targets_in_bulk(self):
        client = _FavoriteClient([
            _favorite_row(
                favorite_id=FAVORITE_ID_A,
                target_id="school-1",
                created_at="2026-09-04T10:00:00+00:00",
            ),
            _favorite_row(
                favorite_id=FAVORITE_ID_B,
                target_id="school-2",
                created_at="2026-09-04T09:00:00+00:00",
            ),
            _favorite_row(
                favorite_id=FAVORITE_ID_C,
                target_id="school-3",
                created_at="2026-09-04T08:00:00+00:00",
            ),
        ])
        resolved = {
            ("2026", "school", "school-1"): {"school_id": "school-1", "school_name": "示例大学"},
            ("2026", "school", "school-2"): {"school_id": "school-2", "school_name": "示例大学二"},
            ("2026", "school", "school-3"): {"school_id": "school-3", "school_name": "示例大学三"},
        }
        with (
            patch.object(major_catalog_favorites, "get_supabase_admin", return_value=client),
            patch.object(
                major_catalog_favorites,
                "resolve_major_catalog_favorite_targets",
                return_value=resolved,
            ) as resolve_targets,
        ):
            first = major_catalog_favorites.list_major_catalog_favorites(
                user_id=USER_ID,
                limit=1,
            )
            second = major_catalog_favorites.list_major_catalog_favorites(
                user_id=USER_ID,
                limit=1,
                cursor=first["next_cursor"],
            )

        self.assertTrue(first["has_more"])
        self.assertEqual(first["items"][0]["id"], FAVORITE_ID_A)
        self.assertEqual(second["items"][0]["id"], FAVORITE_ID_B)
        self.assertNotEqual(first["items"][0]["id"], second["items"][0]["id"])
        self.assertTrue(any(query.cursor_applied for query in client.queries))
        self.assertEqual(resolve_targets.call_count, 2)
        self.assertEqual([query.limit_value for query in client.queries if query.action == "select"], [2, 2])

    def test_statuses_query_a_full_screen_batch_without_per_target_database_queries(self):
        references = [
            {"catalog_year": "2026", "target_type": "school", "target_id": f"school-{index}"}
            for index in range(200)
        ]
        client = _FavoriteClient([
            _favorite_row(
                favorite_id=FAVORITE_ID_A,
                target_id="school-0",
                created_at="2026-09-04T10:00:00+00:00",
            ),
        ])
        resolved = {
            ("2026", "school", f"school-{index}"): {
                "school_id": f"school-{index}",
                "school_name": f"示例大学 {index}",
            }
            for index in range(200)
        }
        with (
            patch.object(major_catalog_favorites, "get_supabase_admin", return_value=client),
            patch.object(
                major_catalog_favorites,
                "resolve_major_catalog_favorite_targets",
                return_value=resolved,
            ) as resolve_targets,
        ):
            result = major_catalog_favorites.get_major_catalog_favorite_statuses(
                user_id=USER_ID,
                references=references,
            )

        self.assertEqual(len(result["items"]), 200)
        self.assertTrue(result["items"][0]["is_favorited"])
        self.assertTrue(result["items"][0]["available"])
        self.assertFalse(result["items"][1]["is_favorited"])
        self.assertEqual(resolve_targets.call_count, 1)
        status_queries = [query for query in client.queries if query.action == "select"]
        self.assertEqual(len(status_queries), 1)
        self.assertEqual(len(status_queries[0].in_filters[0][1]), 200)

    def test_missing_favorites_table_is_reported_as_migration_required(self):
        with (
            patch.object(major_catalog_favorites, "get_supabase_admin", return_value=_FavoriteClient()),
            patch.object(
                major_catalog_favorites,
                "call_supabase",
                side_effect=RuntimeError("relation major_catalog_favorites does not exist"),
            ),
            self.assertRaises(major_catalog_favorites.MajorCatalogFavoritesMigrationRequiredError),
        ):
            major_catalog_favorites.delete_major_catalog_favorite(
                user_id=USER_ID,
                catalog_year="2026",
                target_type="school",
                target_id="school-1",
            )


class MajorCatalogFavoriteRouteTests(unittest.TestCase):
    def test_all_favorite_routes_obtain_the_user_from_the_auth_dependency(self):
        for endpoint in (
            major_catalog.list_major_catalog_favorites,
            major_catalog.get_major_catalog_favorite_statuses,
            major_catalog.save_major_catalog_favorite,
            major_catalog.delete_major_catalog_favorite,
        ):
            with self.subTest(endpoint=endpoint.__name__):
                user_parameter = inspect.signature(endpoint).parameters["user_id"]
                self.assertIsInstance(user_parameter.default, Depends)
                self.assertIs(user_parameter.default.dependency, get_current_user_id)

    def test_list_route_forwards_current_user_filters_and_cursor_to_service(self):
        result = {
            "items": [{
                "id": FAVORITE_ID_A,
                "catalog_year": "2026",
                "target_type": "school",
                "target_id": "school-1",
                "school_id": "school-1",
                "snapshot": {"school_id": "school-1", "school_name": "示例大学"},
                "available": True,
                "created_at": "2026-09-04T10:00:00+00:00",
                "updated_at": "2026-09-04T10:00:00+00:00",
            }],
            "count": 1,
            "next_cursor": "cursor-1",
            "has_more": True,
        }
        with patch.object(major_catalog, "list_major_catalog_favorite_records", return_value=result) as service:
            response = major_catalog.list_major_catalog_favorites(
                target_type="school",
                catalog_year="2026",
                limit=20,
                cursor="cursor-0",
                user_id=USER_ID,
            )

        self.assertEqual(response.items[0].id, FAVORITE_ID_A)
        self.assertTrue(response.has_more)
        service.assert_called_once_with(
            user_id=USER_ID,
            limit=20,
            cursor="cursor-0",
            target_type="school",
            catalog_year="2026",
        )

    def test_status_route_serializes_all_request_items_for_one_scoped_service_call(self):
        payload = MajorCatalogFavoriteStatusRequest(items=[
            {"catalog_year": "2026", "target_type": "school", "target_id": "school-1"},
            {"catalog_year": "2025", "target_type": "program", "target_id": "2025::program-1"},
        ])
        result = {
            "items": [
                {**item.model_dump(), "is_favorited": False, "available": True}
                for item in payload.items
            ]
        }
        with patch.object(major_catalog, "get_major_catalog_favorite_status_records", return_value=result) as service:
            response = major_catalog.get_major_catalog_favorite_statuses(payload, user_id=USER_ID)

        self.assertEqual(len(response.items), 2)
        self.assertTrue(all(item.available for item in response.items))
        service.assert_called_once_with(
            user_id=USER_ID,
            references=[item.model_dump() for item in payload.items],
        )

    def test_save_route_maps_unknown_catalog_target_to_not_found(self):
        with (
            patch.object(major_catalog, "save_major_catalog_favorite_record", side_effect=KeyError("missing")),
            self.assertRaises(HTTPException) as raised,
        ):
            major_catalog.save_major_catalog_favorite(
                catalog_year="2026",
                target_type="program",
                target_id="missing",
                user_id=USER_ID,
            )

        self.assertEqual(raised.exception.status_code, 404)

    def test_favorites_migration_error_maps_to_clear_service_unavailable(self):
        error = major_catalog.MajorCatalogFavoritesMigrationRequiredError("missing relation")
        with (
            patch.object(major_catalog, "delete_major_catalog_favorite_record", side_effect=error),
            self.assertRaises(HTTPException) as raised,
        ):
            major_catalog.delete_major_catalog_favorite(
                catalog_year="2026",
                target_type="school",
                target_id="school-1",
                user_id=USER_ID,
            )

        self.assertEqual(raised.exception.status_code, 503)
        self.assertIn("数据库升级", raised.exception.detail)


if __name__ == "__main__":
    unittest.main()
