import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID

from fastapi import HTTPException

from app.routes import community
from app.schemas.community import CommunityDeletePostsRequest


AUTHOR_ID = "11111111-1111-4111-8111-111111111111"
POST_ID_A = "22222222-2222-4222-8222-222222222222"
POST_ID_B = "33333333-3333-4333-8333-333333333333"


class _FakeQuery:
    def __init__(self, store, table_name):
        self.store = store
        self.table_name = table_name
        self.action = ""
        self.selected_columns = ""
        self.in_filters = {}
        self.eq_filters = {}
        self.limit_value = None

    def select(self, columns):
        self.action = "select"
        self.selected_columns = columns
        return self

    def delete(self):
        self.action = "delete"
        return self

    def in_(self, field, values):
        self.in_filters[field] = list(values)
        return self

    def eq(self, field, value):
        self.eq_filters[field] = value
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def execute(self):
        self.store.executed_queries.append({
            "table": self.table_name,
            "action": self.action,
            "selected_columns": self.selected_columns,
            "in_filters": dict(self.in_filters),
            "eq_filters": dict(self.eq_filters),
            "limit": self.limit_value,
        })
        if self.table_name == "circle_community_reports" and self.action == "select":
            return SimpleNamespace(data=list(self.store.report_rows))
        if self.table_name == "circle_community_appeals" and self.action == "select":
            return SimpleNamespace(data=list(self.store.appeal_rows))
        if self.table_name == "circle_community_posts" and self.action == "delete":
            return SimpleNamespace(data=list(self.store.deleted_rows))
        raise AssertionError(f"Unexpected query: {self.table_name} {self.action}")


class _FakeSupabase:
    def __init__(self, *, report_rows=None, appeal_rows=None, deleted_rows=None):
        self.report_rows = list(report_rows or [])
        self.appeal_rows = list(appeal_rows or [])
        self.deleted_rows = list(deleted_rows or [])
        self.executed_queries = []

    def table(self, table_name):
        return _FakeQuery(self, table_name)


def _execute_immediately(operation, **_kwargs):
    return operation()


class CommunityMyPostsDeleteTests(unittest.TestCase):
    def _delete(self, store, post_ids):
        payload = CommunityDeletePostsRequest(
            post_ids=[UUID(post_id) for post_id in post_ids]
        )
        with (
            patch.object(community, "get_supabase_admin", return_value=store),
            patch.object(community, "call_supabase", side_effect=_execute_immediately),
        ):
            return community.delete_my_community_posts(payload, AUTHOR_ID)

    def test_deduplicates_ids_and_scopes_delete_to_current_author(self):
        store = _FakeSupabase(
            deleted_rows=[{"id": POST_ID_A}, {"id": POST_ID_B}],
        )

        result = self._delete(store, [POST_ID_A, POST_ID_A, POST_ID_B])

        delete_queries = [
            query
            for query in store.executed_queries
            if query["table"] == "circle_community_posts" and query["action"] == "delete"
        ]
        self.assertEqual(len(delete_queries), 1)
        self.assertEqual(delete_queries[0]["in_filters"], {"id": [POST_ID_A, POST_ID_B]})
        self.assertEqual(delete_queries[0]["eq_filters"], {"author_id": AUTHOR_ID})
        self.assertEqual(result.deleted_post_ids, [POST_ID_A, POST_ID_B])
        self.assertEqual(result.deleted_count, 2)

    def test_reported_post_is_protected_before_delete(self):
        store = _FakeSupabase(report_rows=[{"post_id": POST_ID_A}])

        with self.assertRaises(HTTPException) as raised:
            self._delete(store, [POST_ID_A])

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(raised.exception.detail, "包含已进入平台处理的帖子，暂不能删除")
        self.assertFalse(any(query["action"] == "delete" for query in store.executed_queries))
        self.assertFalse(any(query["table"] == "circle_community_appeals" for query in store.executed_queries))

    def test_appealed_post_is_protected_before_delete(self):
        store = _FakeSupabase(appeal_rows=[{"post_id": POST_ID_A}])

        with self.assertRaises(HTTPException) as raised:
            self._delete(store, [POST_ID_A])

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(
            raised.exception.detail,
            "包含已有内容申诉留档的帖子，为保留平台处理记录暂不能删除",
        )
        self.assertFalse(any(query["action"] == "delete" for query in store.executed_queries))

    def test_response_contains_only_rows_actually_deleted(self):
        store = _FakeSupabase(deleted_rows=[{"id": POST_ID_B}])

        result = self._delete(store, [POST_ID_A, POST_ID_B])

        self.assertEqual(result.deleted_post_ids, [POST_ID_B])
        self.assertEqual(result.deleted_count, 1)


if __name__ == "__main__":
    unittest.main()
