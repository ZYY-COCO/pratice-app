import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID

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
        self.update_values = {}
        self.in_filters = {}
        self.eq_filters = {}
        self.is_filters = {}
        self.limit_value = None

    def select(self, columns):
        self.action = "select"
        self.selected_columns = columns
        return self

    def delete(self):
        self.action = "delete"
        return self

    def update(self, values):
        self.action = "update"
        self.update_values = dict(values)
        return self

    def in_(self, field, values):
        self.in_filters[field] = list(values)
        return self

    def eq(self, field, value):
        self.eq_filters[field] = value
        return self

    def is_(self, field, value):
        self.is_filters[field] = value
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def execute(self):
        self.store.executed_queries.append({
            "table": self.table_name,
            "action": self.action,
            "selected_columns": self.selected_columns,
            "update_values": dict(self.update_values),
            "in_filters": dict(self.in_filters),
            "eq_filters": dict(self.eq_filters),
            "is_filters": dict(self.is_filters),
            "limit": self.limit_value,
        })
        if self.table_name == "circle_community_posts" and self.action == "select":
            return SimpleNamespace(data=list(self.store.legacy_rows))
        if self.table_name == "circle_community_posts" and self.action == "update":
            if self.store.update_error and "author_deleted_at" in self.update_values:
                raise self.store.update_error
            post_id = str(self.eq_filters.get("id") or "")
            if post_id:
                return SimpleNamespace(data=[{"id": post_id}])
            return SimpleNamespace(data=list(self.store.updated_rows))
        raise AssertionError(f"Unexpected query: {self.table_name} {self.action}")


class _FakeSupabase:
    def __init__(self, *, updated_rows=None, update_error=None, legacy_rows=None):
        self.updated_rows = list(updated_rows or [])
        self.update_error = update_error
        self.legacy_rows = list(legacy_rows or [])
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
        original_column_state = community._community_author_deleted_column_available
        try:
            with (
                patch.object(community, "get_supabase_admin", return_value=store),
                patch.object(community, "call_supabase", side_effect=_execute_immediately),
            ):
                return community.delete_my_community_posts(payload, AUTHOR_ID)
        finally:
            community._community_author_deleted_column_available = original_column_state

    def test_deduplicates_ids_and_scopes_author_delete_to_current_user(self):
        store = _FakeSupabase(
            updated_rows=[{"id": POST_ID_A}, {"id": POST_ID_B}],
        )

        result = self._delete(store, [POST_ID_A, POST_ID_A, POST_ID_B])

        update_queries = [
            query
            for query in store.executed_queries
            if query["table"] == "circle_community_posts" and query["action"] == "update"
        ]
        self.assertEqual(len(update_queries), 1)
        query = update_queries[0]
        self.assertEqual(query["in_filters"], {"id": [POST_ID_A, POST_ID_B]})
        self.assertEqual(query["eq_filters"], {"author_id": AUTHOR_ID})
        self.assertEqual(query["is_filters"], {"author_deleted_at": "null"})
        self.assertFalse(query["update_values"]["is_published"])
        self.assertFalse(query["update_values"]["is_featured"])
        self.assertTrue(query["update_values"]["author_deleted_at"])
        self.assertEqual(
            query["update_values"]["updated_at"],
            query["update_values"]["author_deleted_at"],
        )
        self.assertEqual(result.deleted_post_ids, [POST_ID_A, POST_ID_B])
        self.assertEqual(result.deleted_count, 2)

    def test_author_delete_does_not_query_or_remove_governance_records(self):
        store = _FakeSupabase(updated_rows=[{"id": POST_ID_A}])

        result = self._delete(store, [POST_ID_A])

        self.assertEqual(result.deleted_post_ids, [POST_ID_A])
        self.assertEqual(
            {query["table"] for query in store.executed_queries},
            {"circle_community_posts"},
        )
        self.assertFalse(any(query["action"] == "delete" for query in store.executed_queries))

    def test_response_contains_only_rows_actually_author_deleted(self):
        store = _FakeSupabase(updated_rows=[{"id": POST_ID_B}])

        result = self._delete(store, [POST_ID_A, POST_ID_B])

        self.assertEqual(result.deleted_post_ids, [POST_ID_B])
        self.assertEqual(result.deleted_count, 1)

    def test_missing_migration_uses_non_destructive_author_delete_marker(self):
        store = _FakeSupabase(
            update_error=RuntimeError("column circle_community_posts.author_deleted_at does not exist"),
            legacy_rows=[{"id": POST_ID_A, "media": [{"imageUrl": "https://example.test/a.jpg"}]}],
        )

        result = self._delete(store, [POST_ID_A])

        self.assertEqual(result.deleted_post_ids, [POST_ID_A])
        fallback_updates = [
            query
            for query in store.executed_queries
            if query["action"] == "update" and "media" in query["update_values"]
        ]
        self.assertEqual(len(fallback_updates), 1)
        fallback = fallback_updates[0]
        self.assertFalse(fallback["update_values"]["is_published"])
        self.assertFalse(fallback["update_values"]["is_featured"])
        self.assertEqual(fallback["eq_filters"], {"id": POST_ID_A, "author_id": AUTHOR_ID})
        self.assertIn(
            community.COMMUNITY_AUTHOR_DELETED_MARKER_KEY,
            fallback["update_values"]["media"][0],
        )
        self.assertEqual(
            fallback["update_values"]["media"][1],
            {"imageUrl": "https://example.test/a.jpg"},
        )
        self.assertFalse(any(query["action"] == "delete" for query in store.executed_queries))

    def test_legacy_author_delete_is_idempotent(self):
        store = _FakeSupabase(
            update_error=RuntimeError("column circle_community_posts.author_deleted_at does not exist"),
            legacy_rows=[{
                "id": POST_ID_A,
                "media": [{community.COMMUNITY_AUTHOR_DELETED_MARKER_KEY: "2026-09-03T00:00:00+00:00"}],
            }],
        )

        result = self._delete(store, [POST_ID_A])

        self.assertEqual(result.deleted_post_ids, [])
        self.assertEqual(result.deleted_count, 0)
        self.assertEqual(
            len([query for query in store.executed_queries if query["action"] == "update"]),
            1,
        )

    def test_author_delete_marker_is_never_exposed_as_media(self):
        visible_media = community._normalise_media([
            {"imageUrl": "https://example.test/a.jpg"},
            {community.COMMUNITY_AUTHOR_DELETED_MARKER_KEY: "2026-09-03T00:00:00+00:00"},
        ])

        self.assertEqual(visible_media, [{"imageUrl": "https://example.test/a.jpg"}])

    def test_owner_detail_returns_unpublished_pending_post_content(self):
        pending_post = {
            "id": POST_ID_A,
            "author_id": AUTHOR_ID,
            "author_name": "研友",
            "author_avatar": "研",
            "post_type": "experience",
            "category": "Z001",
            "experience_stages": ["初试"],
            "title": "待审核经验贴",
            "content": "只有作者本人可以预览的完整正文。",
            "media": [],
            "is_published": False,
            "review_status": "pending",
        }

        with (
            patch.object(community, "get_supabase_admin", return_value=object()),
            patch.object(community, "_get_owned_post_row", return_value=pending_post),
            patch.object(community, "_fetch_community_profiles", return_value={}),
            patch.object(community, "_fetch_verified_mentor_owner_ids", return_value=set()),
            patch.object(community, "_fetch_experience_review_history", return_value=[]),
        ):
            result = community.get_my_community_post(POST_ID_A, AUTHOR_ID)

        self.assertEqual(result.post.id, POST_ID_A)
        self.assertTrue(result.post.is_mine)
        self.assertFalse(result.post.is_published)
        self.assertEqual(result.post.review_status, "pending")
        self.assertEqual(result.post.content, "只有作者本人可以预览的完整正文。")


if __name__ == "__main__":
    unittest.main()
