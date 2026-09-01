from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.routes import notifications


class _Response:
    def __init__(self, data=None, count=None):
        self.data = data
        self.count = count


class _TableQuery:
    def __init__(self, client, table_name: str):
        self.client = client
        self.table_name = table_name
        self.operation = "select"
        self.update_values: dict = {}
        self.upsert_rows: list[dict] = []
        self.filters: list[tuple[str, str, object]] = []
        self.orders: list[tuple[str, bool]] = []
        self.limit_value: int | None = None
        self.count_requested = False

    def select(self, *_args, **kwargs):
        self.operation = "select"
        self.count_requested = kwargs.get("count") is not None
        return self

    def update(self, values: dict):
        self.operation = "update"
        self.update_values = dict(values)
        return self

    def upsert(self, rows, **_kwargs):
        self.operation = "upsert"
        self.upsert_rows = [dict(row) for row in rows]
        self.client.upsert_calls.append((self.table_name, self.upsert_rows))
        return self

    def eq(self, field: str, value: object):
        self.filters.append(("eq", field, value))
        return self

    def neq(self, field: str, value: object):
        self.filters.append(("neq", field, value))
        return self

    def is_(self, field: str, value: object):
        self.filters.append(("is", field, value))
        return self

    def in_(self, field: str, values):
        self.filters.append(("in", field, list(values)))
        return self

    def order(self, field: str, desc: bool = False):
        self.orders.append((field, desc))
        return self

    def limit(self, value: int):
        self.limit_value = value
        return self

    def _matches(self, row: dict) -> bool:
        for kind, field, value in self.filters:
            if kind == "eq" and row.get(field) != value:
                return False
            if kind == "neq" and row.get(field) == value:
                return False
            if kind == "is" and value == "null" and row.get(field) is not None:
                return False
            if kind == "in" and row.get(field) not in value:
                return False
        return True

    def execute(self):
        rows = self.client.tables.setdefault(self.table_name, [])
        if self.operation == "upsert":
            result = []
            for payload in self.upsert_rows:
                existing = next(
                    (
                        row
                        for row in rows
                        if row.get("user_id") == payload.get("user_id")
                        and row.get("message_id") == payload.get("message_id")
                    ),
                    None,
                )
                if existing is None:
                    existing = dict(payload)
                    rows.append(existing)
                else:
                    existing.update(payload)
                result.append(dict(existing))
            return _Response(result)

        matched = [row for row in rows if self._matches(row)]
        for field, descending in reversed(self.orders):
            matched.sort(key=lambda row: str(row.get(field) or ""), reverse=descending)
        if self.limit_value is not None:
            matched = matched[: self.limit_value]
        if self.operation == "update":
            for row in matched:
                row.update(self.update_values)
            return _Response([dict(row) for row in matched])
        return _Response([dict(row) for row in matched], count=len(matched) if self.count_requested else None)


class _SupabaseClient:
    def __init__(self, tables: dict[str, list[dict]]):
        self.tables = {name: [dict(row) for row in rows] for name, rows in tables.items()}
        self.upsert_calls: list[tuple[str, list[dict]]] = []

    def table(self, table_name: str):
        return _TableQuery(self, table_name)


def _iso_now_minus(**kwargs) -> str:
    return (datetime.now(timezone.utc) - timedelta(**kwargs)).isoformat()


class NotificationReadAllTests(unittest.TestCase):
    def test_marks_only_current_user_and_visible_official_messages(self):
        client = _SupabaseClient({
            "user_notifications": [
                {"id": "personal-unread", "recipient_user_id": "user-1", "read_at": None},
                {"id": "personal-read", "recipient_user_id": "user-1", "read_at": "old"},
                {"id": "other-user", "recipient_user_id": "user-2", "read_at": None},
            ],
            "official_messages": [
                {"id": "visible-unread", "status": "published", "published_at": _iso_now_minus(days=1), "expires_at": None},
                {"id": "visible-read", "status": "published", "published_at": _iso_now_minus(days=2), "expires_at": None},
                {"id": "future", "status": "published", "published_at": _iso_now_minus(days=-1), "expires_at": None},
                {"id": "expired", "status": "published", "published_at": _iso_now_minus(days=3), "expires_at": _iso_now_minus(days=1)},
                {"id": "draft", "status": "draft", "published_at": None, "expires_at": None},
                {"id": "archived", "status": "archived", "published_at": _iso_now_minus(days=4), "expires_at": None},
            ],
            "user_official_message_reads": [
                {"user_id": "user-1", "message_id": "visible-read", "read_at": "old"},
                {"user_id": "user-2", "message_id": "visible-unread", "read_at": "other"},
            ],
        })

        with patch.object(notifications, "get_supabase_admin", return_value=client):
            result = notifications.mark_all_user_notifications_read(user_id="user-1")

        self.assertEqual(result.updated_count, 2)
        self.assertEqual(result.personal_updated_count, 1)
        self.assertEqual(result.official_updated_count, 1)

        personal = {row["id"]: row for row in client.tables["user_notifications"]}
        self.assertTrue(personal["personal-unread"]["read_at"])
        self.assertEqual(personal["personal-read"]["read_at"], "old")
        self.assertIsNone(personal["other-user"]["read_at"])

        reads = {(row["user_id"], row["message_id"]): row for row in client.tables["user_official_message_reads"]}
        self.assertIn(("user-1", "visible-unread"), reads)
        self.assertEqual(reads[("user-1", "visible-read")]["read_at"], "old")
        self.assertNotIn(("user-1", "future"), reads)
        self.assertNotIn(("user-1", "expired"), reads)
        self.assertNotIn(("user-1", "draft"), reads)
        self.assertNotIn(("user-1", "archived"), reads)
        self.assertEqual(len(client.upsert_calls), 1)

    def test_repeated_calls_are_idempotent_and_skip_empty_upsert(self):
        client = _SupabaseClient({
            "user_notifications": [
                {"id": "personal-unread", "recipient_user_id": "user-1", "read_at": None},
            ],
            "official_messages": [
                {"id": "visible-unread", "status": "published", "published_at": _iso_now_minus(days=1), "expires_at": None},
            ],
            "user_official_message_reads": [],
        })

        with patch.object(notifications, "get_supabase_admin", return_value=client):
            first = notifications.mark_all_user_notifications_read(user_id="user-1")
            second = notifications.mark_all_user_notifications_read(user_id="user-1")

        self.assertEqual(first.updated_count, 2)
        self.assertEqual(second.updated_count, 0)
        self.assertEqual(second.personal_updated_count, 0)
        self.assertEqual(second.official_updated_count, 0)
        self.assertEqual(len(client.upsert_calls), 1)

    def test_all_visible_official_messages_are_marked_even_beyond_list_limit(self):
        client = _SupabaseClient({
            "user_notifications": [],
            "official_messages": [
                {
                    "id": f"visible-{index}",
                    "status": "published",
                    "published_at": _iso_now_minus(days=1),
                    "expires_at": None,
                }
                for index in range(55)
            ],
            "user_official_message_reads": [],
        })

        with patch.object(notifications, "get_supabase_admin", return_value=client):
            result = notifications.mark_all_user_notifications_read(user_id="user-1")

        self.assertEqual(result.personal_updated_count, 0)
        self.assertEqual(result.official_updated_count, 55)
        self.assertEqual(len(client.tables["user_official_message_reads"]), 55)


if __name__ == "__main__":
    unittest.main()
