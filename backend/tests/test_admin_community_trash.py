import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.routes import admin, community
from app.schemas.admin import AdminCommunityTrashMutationRequest


ADMIN_ID = "22222222-2222-4222-8222-222222222222"
POST_ID = "33333333-3333-4333-8333-333333333333"


def _trash_row(**overrides):
    row = {
        "id": POST_ID,
        "author_id": "11111111-1111-4111-8111-111111111111",
        "author_name": "研友",
        "author_avatar": "研",
        "post_type": "chat",
        "category": "中华文化",
        "title": "待清理帖子",
        "content": "帖子正文",
        "media": [],
        "like_count": 1,
        "comment_count": 2,
        "view_count": 3,
        "is_published": False,
        "is_featured": False,
        "admin_deleted_at": "2026-09-03T00:00:00Z",
        "admin_deleted_by": ADMIN_ID,
        "admin_purge_after": "2026-09-10T00:00:00Z",
        "created_at": "2026-09-01T00:00:00Z",
        "updated_at": "2026-09-03T00:00:00Z",
    }
    row.update(overrides)
    return row


class _RpcCall:
    def __init__(self, owner, name, args):
        self.owner = owner
        self.name = name
        self.args = dict(args)

    def execute(self):
        self.owner.rpc_calls.append((self.name, self.args))
        return self.owner.rpc_responses.get(self.name, SimpleNamespace(data=[]))


class _RpcSupabase:
    def __init__(self, rpc_responses):
        self.rpc_responses = rpc_responses
        self.rpc_calls = []

    def rpc(self, name, args):
        return _RpcCall(self, name, args)


class _TrashListQuery:
    def __init__(self, response):
        self.response = response
        self.operations = []

    @property
    def not_(self):
        self.operations.append(("not",))
        return self

    def select(self, *args, **kwargs):
        self.operations.append(("select", args, kwargs))
        return self

    def is_(self, *args):
        self.operations.append(("is", args))
        return self

    def eq(self, *args):
        self.operations.append(("eq", args))
        return self

    def or_(self, *args):
        self.operations.append(("or", args))
        return self

    def order(self, *args, **kwargs):
        self.operations.append(("order", args, kwargs))
        return self

    def range(self, *args):
        self.operations.append(("range", args))
        return self

    def execute(self):
        return self.response


class _TrashListSupabase(_RpcSupabase):
    def __init__(self, rows):
        super().__init__({
            "circle_community_purge_expired_admin_trash": SimpleNamespace(data=0),
        })
        self.query = _TrashListQuery(SimpleNamespace(data=rows, count=len(rows)))

    def table(self, name):
        if name != "circle_community_posts":
            raise AssertionError(f"unexpected table: {name}")
        return self.query


class AdminCommunityTrashTests(unittest.TestCase):
    def test_trash_posts_uses_atomic_rpc_and_admin_identity(self):
        supabase = _RpcSupabase({
            "circle_community_admin_trash_posts": SimpleNamespace(data=[{"post_id": POST_ID}]),
        })
        payload = AdminCommunityTrashMutationRequest(ids=[POST_ID, POST_ID])

        with (
            patch.object(admin, "get_supabase_admin", return_value=supabase),
            patch.object(admin, "_log_admin_action") as log_action,
        ):
            result = admin.question_admin_trash_community_posts(payload, {"id": ADMIN_ID})

        self.assertEqual(result.affected_count, 1)
        self.assertEqual(supabase.rpc_calls, [(
            "circle_community_admin_trash_posts",
            {"p_post_ids": [POST_ID], "p_admin_user_id": ADMIN_ID},
        )])
        self.assertEqual(log_action.call_args.kwargs["action"], "trash_community_posts")

    def test_restore_purges_expired_rows_before_restoring(self):
        supabase = _RpcSupabase({
            "circle_community_purge_expired_admin_trash": SimpleNamespace(data=0),
            "circle_community_admin_restore_posts": SimpleNamespace(data=[{"post_id": POST_ID}]),
        })

        with (
            patch.object(admin, "get_supabase_admin", return_value=supabase),
            patch.object(admin, "_log_admin_action"),
        ):
            result = admin.question_admin_restore_community_trash(
                AdminCommunityTrashMutationRequest(ids=[POST_ID]),
                {"id": ADMIN_ID},
            )

        self.assertEqual(result.affected_count, 1)
        self.assertEqual(
            [name for name, _ in supabase.rpc_calls],
            ["circle_community_purge_expired_admin_trash", "circle_community_admin_restore_posts"],
        )

    def test_permanent_delete_only_reports_rows_returned_by_rpc(self):
        supabase = _RpcSupabase({
            "circle_community_admin_purge_posts": SimpleNamespace(data=[{"post_id": POST_ID}]),
        })

        with (
            patch.object(admin, "get_supabase_admin", return_value=supabase),
            patch.object(admin, "_log_admin_action") as log_action,
        ):
            result = admin.question_admin_purge_community_trash(
                AdminCommunityTrashMutationRequest(ids=[POST_ID]),
                {"id": ADMIN_ID},
            )

        self.assertEqual(result.affected_count, 1)
        self.assertEqual(log_action.call_args.kwargs["details"]["post_ids"], [POST_ID])

    def test_trash_list_runs_cleanup_and_filters_for_deleted_rows(self):
        supabase = _TrashListSupabase([_trash_row()])
        with patch.object(admin, "get_supabase_admin", return_value=supabase):
            result = admin.question_admin_community_trash(
                post_type="chat",
                sort_by="expiring_soon",
                search="待清理",
                limit=20,
                offset=0,
                _={},
            )

        self.assertEqual(result.count, 1)
        self.assertEqual(result.items[0].admin_purge_after, "2026-09-10T00:00:00Z")
        self.assertIn(("is", ("admin_deleted_at", "null")), supabase.query.operations)
        self.assertIn(("eq", ("post_type", "chat")), supabase.query.operations)
        self.assertEqual(supabase.rpc_calls[0][0], "circle_community_purge_expired_admin_trash")

    def test_owned_post_lookup_rejects_admin_deleted_post(self):
        class _OwnedQuery:
            def select(self, *_args, **_kwargs): return self
            def eq(self, *_args, **_kwargs): return self
            def limit(self, *_args, **_kwargs): return self
            def execute(self): return SimpleNamespace(data=[_trash_row()])

        class _OwnedSupabase:
            def table(self, _name): return _OwnedQuery()

        with self.assertRaises(HTTPException) as raised:
            community._get_owned_post_row(_OwnedSupabase(), POST_ID, _trash_row()["author_id"])
        self.assertEqual(raised.exception.status_code, 404)

    def test_migration_keeps_seven_day_retention_and_daily_schedule(self):
        migration = (
            Path(__file__).resolve().parents[2]
            / "database"
            / "circle_community_admin_trash.sql"
        ).read_text(encoding="utf-8")
        self.assertIn("interval '7 days'", migration)
        self.assertIn("*/15 * * * *", migration)
        self.assertIn("circle-community-admin-trash-purge", migration)
        self.assertIn("circle_community_admin_purge_posts", migration)


if __name__ == "__main__":
    unittest.main()
