import unittest
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID

from fastapi import BackgroundTasks
from PIL import Image

from app.routes import community
from app.schemas.community import CommunityCreateCommentRequest


POST_ID = "11111111-1111-4111-8111-111111111111"
USER_ID = "22222222-2222-4222-8222-222222222222"
COMMENT_ID = "33333333-3333-4333-8333-333333333333"
REQUEST_ID = UUID("44444444-4444-4444-8444-444444444444")


class _RpcCall:
    def __init__(self, data):
        self.data = data

    def execute(self):
        return SimpleNamespace(data=self.data)


class _RpcSupabase:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def rpc(self, name, params):
        self.calls.append((name, params))
        return _RpcCall(self.responses[name])


class _AmbiguousColumnError(Exception):
    code = "42702"


class _FailingRpcCall:
    def execute(self):
        raise _AmbiguousColumnError(
            'column reference "author_id" is ambiguous; it could refer to either a variable or a table column'
        )


class _InsertCall:
    def __init__(self, store):
        self.store = store

    def insert(self, data):
        self.store.insert_data = data
        return self

    def execute(self):
        return SimpleNamespace(data=[{
            "id": COMMENT_ID,
            "post_id": POST_ID,
            "author_id": USER_ID,
            "author_name": "账号昵称",
            "author_avatar": "账",
            "content": self.store.insert_data["content"],
            "created_at": "2026-09-03T08:00:00+00:00",
            "like_count": 0,
        }])


class _AmbiguousRpcSupabase:
    def __init__(self):
        self.insert_data = None

    def rpc(self, _name, _params):
        return _FailingRpcCall()

    def table(self, name):
        if name != "circle_community_comments":
            raise AssertionError(f"Unexpected table: {name}")
        return _InsertCall(self)


class CommunityInteractionPerformanceTests(unittest.TestCase):
    def setUp(self):
        self.original_flags = (
            community._community_comment_create_rpc_available,
            community._community_set_like_rpc_available,
            community._community_set_comment_like_rpc_available,
        )
        community._community_comment_create_rpc_available = None
        community._community_set_like_rpc_available = None
        community._community_set_comment_like_rpc_available = None

    def tearDown(self):
        (
            community._community_comment_create_rpc_available,
            community._community_set_like_rpc_available,
            community._community_set_comment_like_rpc_available,
        ) = self.original_flags

    def test_compact_feed_item_omits_full_body_and_extra_media(self):
        content = "长" * 600
        row = {
            "id": POST_ID,
            "author_id": USER_ID,
            "author_name": "研友",
            "post_type": "chat",
            "category": "备考日常",
            "title": "长文章",
            "content": content,
            "media": [{"imageUrl": f"https://example.com/{index}.jpg"} for index in range(5)],
            "media_count": 5,
            "is_published": True,
        }

        item = community._post_item(row, set(), {}, {}, compact=True, current_user_id=USER_ID)

        self.assertEqual(item.content, "")
        self.assertEqual(len(item.summary), 320)
        self.assertEqual(len(item.media), 2)
        self.assertEqual(item.media_count, 5)
        self.assertTrue(item.is_mine)

    def test_thumbnail_keeps_original_workflow_and_bounds_feed_dimensions(self):
        source = BytesIO()
        Image.new("RGB", (1600, 1000), color=(52, 120, 246)).save(source, format="JPEG", quality=92)

        thumbnail = community._build_community_thumbnail(source.getvalue())

        self.assertIsNotNone(thumbnail)
        with Image.open(BytesIO(thumbnail)) as image:
            self.assertEqual(image.format, "WEBP")
            self.assertLessEqual(max(image.size), 720)

    def test_explicit_like_target_uses_atomic_rpc(self):
        store = _RpcSupabase({
            "circle_community_set_like": [{
                "is_liked": True,
                "like_count": 7,
                "changed": False,
            }]
        })

        result = community._set_community_like(
            store,
            post_id=POST_ID,
            user_id=USER_ID,
            desired_liked=True,
        )

        self.assertEqual(result, (True, 7, False))
        self.assertEqual(store.calls[0][0], "circle_community_set_like")
        self.assertTrue(store.calls[0][1]["p_is_liked"])

    def test_comment_create_rpc_preserves_request_id_and_reports_created(self):
        store = _RpcSupabase({
            "circle_community_create_comment": [{
                "comment_id": COMMENT_ID,
                "post_id": POST_ID,
                "author_id": USER_ID,
                "author_name": "账号昵称",
                "author_avatar": "账",
                "author_avatar_url": "https://example.com/avatar.png",
                "content": "这是一条评论",
                "created_at": "2026-09-03T08:00:00+00:00",
                "like_count": 0,
                "comment_count": 3,
                "post_author_id": "55555555-5555-4555-8555-555555555555",
                "post_title": "帖子标题",
                "post_type": "chat",
                "created": True,
            }]
        })
        payload = CommunityCreateCommentRequest(
            client_request_id=REQUEST_ID,
            content="这是一条评论",
        )

        comment, count, created, post, avatar_url, author_name = community._create_community_comment_record(
            store,
            post_id=POST_ID,
            user_id=USER_ID,
            payload=payload,
        )

        self.assertEqual(comment["id"], COMMENT_ID)
        self.assertEqual(count, 3)
        self.assertTrue(created)
        self.assertEqual(post["title"], "帖子标题")
        self.assertEqual(avatar_url, "https://example.com/avatar.png")
        self.assertEqual(author_name, "账号昵称")
        self.assertEqual(store.calls[0][1]["p_client_request_id"], str(REQUEST_ID))

    def test_ambiguous_comment_rpc_falls_back_to_compatible_insert(self):
        store = _AmbiguousRpcSupabase()
        payload = CommunityCreateCommentRequest(
            client_request_id=REQUEST_ID,
            content="兼容路径评论",
        )
        post = {
            "id": POST_ID,
            "author_id": "55555555-5555-4555-8555-555555555555",
            "title": "帖子标题",
            "post_type": "chat",
            "comment_count": 0,
        }

        with (
            patch.object(community, "_get_post_row", side_effect=[post, {**post, "comment_count": 1}]),
            patch.object(community, "_current_author", return_value=("账号昵称", "账", None)),
            patch.object(community, "_find_community_comment_by_request_id", return_value=None),
            patch.object(community, "_community_comment_client_request_id_column_available", None),
        ):
            comment, count, created, _, _, _ = community._create_community_comment_record(
                store,
                post_id=POST_ID,
                user_id=USER_ID,
                payload=payload,
            )

        self.assertTrue(created)
        self.assertEqual(comment["content"], "兼容路径评论")
        self.assertEqual(count, 1)
        self.assertEqual(store.insert_data["client_request_id"], str(REQUEST_ID))
        self.assertFalse(community._community_comment_create_rpc_available)

    def test_retry_response_does_not_enqueue_duplicate_notification(self):
        payload = CommunityCreateCommentRequest(
            client_request_id=REQUEST_ID,
            content="重复请求",
        )
        comment = {
            "id": COMMENT_ID,
            "author_id": USER_ID,
            "author_name": "账号昵称",
            "author_avatar": "账",
            "content": "重复请求",
        }
        post = {
            "id": POST_ID,
            "author_id": "55555555-5555-4555-8555-555555555555",
            "title": "帖子标题",
            "post_type": "chat",
        }
        background_tasks = BackgroundTasks()

        with (
            patch.object(community, "get_supabase_admin", return_value=object()),
            patch.object(
                community,
                "_create_community_comment_record",
                return_value=(comment, 3, False, post, None, "账号昵称"),
            ),
        ):
            response = community.create_community_comment(
                POST_ID,
                payload,
                USER_ID,
                background_tasks,
            )

        self.assertFalse(response.created)
        self.assertEqual(len(background_tasks.tasks), 0)

    def test_comment_delete_returns_refreshed_count(self):
        with (
            patch.object(community, "get_supabase_admin", return_value=object()),
            patch.object(
                community,
                "_get_post_row",
                side_effect=[{"id": POST_ID}, {"id": POST_ID, "comment_count": 2}],
            ),
            patch.object(community, "_get_comment_row", return_value={"id": COMMENT_ID, "author_id": USER_ID}),
            patch.object(
                community,
                "call_supabase",
                side_effect=[
                    SimpleNamespace(data=[]),
                    SimpleNamespace(data=[]),
                    SimpleNamespace(data=[{"id": COMMENT_ID}]),
                ],
            ),
        ):
            response = community.delete_community_comment(POST_ID, COMMENT_ID, USER_ID)

        self.assertEqual(response.comment_id, COMMENT_ID)
        self.assertEqual(response.comment_count, 2)


if __name__ == "__main__":
    unittest.main()
