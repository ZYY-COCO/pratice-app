import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID

from fastapi import HTTPException

from app.routes import community
from app.schemas.community import CommunityCreatePostRequest


AUTHOR_ID = "11111111-1111-4111-8111-111111111111"
REQUEST_ID = UUID("22222222-2222-4222-8222-222222222222")


def _post_row(**overrides):
    row = {
        "id": "33333333-3333-4333-8333-333333333333",
        "author_id": AUTHOR_ID,
        "author_name": "研友",
        "author_avatar": "研",
        "author_tone": "blue",
        "post_type": "chat",
        "category": "备考日常",
        "experience_stages": [],
        "client_request_id": str(REQUEST_ID),
        "title": "备考打卡",
        "content": "今天完成了复习计划",
        "media": [],
    }
    row.update(overrides)
    return row


class _FakeQuery:
    def __init__(self, store):
        self.store = store
        self.action = ""
        self.payload = None
        self.filters = {}

    def select(self, _columns):
        self.action = "select"
        return self

    def eq(self, field, value):
        self.filters[field] = value
        return self

    def limit(self, _value):
        return self

    def insert(self, payload):
        self.action = "insert"
        self.payload = dict(payload)
        return self

    def execute(self):
        if self.action == "select":
            if "client_request_id" in self.filters and "client_request_id" in self.store.missing_columns:
                raise RuntimeError("PGRST204: could not find the client_request_id column in the schema cache")
            self.store.lookup_count += 1
            matches = [
                row
                for row in self.store.rows
                if all(str(row.get(key)) == str(value) for key, value in self.filters.items())
            ]
            return SimpleNamespace(data=matches[:1])

        if self.action == "insert":
            self.store.insert_attempts.append(dict(self.payload))
            for column_name in self.store.missing_columns:
                if column_name in self.payload:
                    raise RuntimeError(
                        f"PGRST204: could not find the {column_name} column in the schema cache"
                    )
            if self.store.duplicate_once:
                self.store.duplicate_once = False
                self.store.rows.append(_post_row(**self.payload))
                error = RuntimeError("duplicate key value violates unique constraint (23505)")
                error.code = "23505"
                raise error
            inserted = _post_row(**self.payload)
            self.store.rows.append(inserted)
            return SimpleNamespace(data=[inserted])

        raise AssertionError("Unexpected fake query action")


class _FakeSupabase:
    def __init__(self, *, missing_columns=None, rows=None, duplicate_once=False):
        self.missing_columns = set(missing_columns or [])
        self.rows = list(rows or [])
        self.duplicate_once = duplicate_once
        self.lookup_count = 0
        self.insert_attempts = []

    def table(self, table_name):
        if table_name != "circle_community_posts":
            raise AssertionError(f"Unexpected table: {table_name}")
        return _FakeQuery(self)


class CommunityPostPublishTests(unittest.TestCase):
    def setUp(self):
        self.original_column_states = (
            community._community_post_type_column_available,
            community._community_client_request_id_column_available,
            community._community_experience_stages_column_available,
        )
        community._community_post_type_column_available = None
        community._community_client_request_id_column_available = None
        community._community_experience_stages_column_available = None

    def tearDown(self):
        (
            community._community_post_type_column_available,
            community._community_client_request_id_column_available,
            community._community_experience_stages_column_available,
        ) = self.original_column_states

    def _create(self, store, payload):
        mentor = {
            "display_name": "认证前辈",
            "avatar_label": "认",
            "avatar_tone": "mint",
            "avatar_url": "",
        }
        with (
            patch.object(community, "get_supabase_admin", return_value=store),
            patch.object(community, "_current_author", return_value=("研友", "研", None)),
            patch.object(community, "_current_verified_mentor_author", return_value=mentor),
        ):
            return community.create_community_post(payload, AUTHOR_ID)

    def test_migrated_experience_post_uses_columns_without_media_marker(self):
        store = _FakeSupabase()
        payload = CommunityCreatePostRequest(
            post_type="experience",
            category="Z001",
            experience_stages=["申请制", "复试"],
            client_request_id=REQUEST_ID,
            title="备考经验",
            content="完整经验内容",
        )

        result = self._create(store, payload)

        self.assertEqual(result.experience_stages, ["申请制", "复试"])
        self.assertEqual(len(store.insert_attempts), 1)
        inserted = store.insert_attempts[0]
        self.assertEqual(inserted["client_request_id"], str(REQUEST_ID))
        self.assertEqual(inserted["experience_stages"], ["申请制", "复试"])
        self.assertNotIn(community.COMMUNITY_EXPERIENCE_STAGES_MARKER_KEY, str(inserted["media"]))

    def test_chat_retry_returns_existing_post_and_keeps_empty_stages(self):
        store = _FakeSupabase()
        payload = CommunityCreatePostRequest(
            post_type="chat",
            category="备考日常",
            experience_stages=["初试"],
            client_request_id=REQUEST_ID,
            title="备考打卡",
            content="今天完成了复习计划",
        )

        first = self._create(store, payload)
        second = self._create(store, payload)

        self.assertEqual(first.id, second.id)
        self.assertEqual(len(store.insert_attempts), 1)
        self.assertEqual(store.insert_attempts[0]["experience_stages"], [])

    def test_unique_race_returns_the_post_created_by_the_winner(self):
        store = _FakeSupabase(duplicate_once=True)
        payload = CommunityCreatePostRequest(
            post_type="experience",
            category="Z002",
            experience_stages=["初试"],
            client_request_id=REQUEST_ID,
            title="备考经验",
            content="完整经验内容",
        )

        result = self._create(store, payload)

        self.assertEqual(result.id, "33333333-3333-4333-8333-333333333333")
        self.assertEqual(len(store.insert_attempts), 1)
        self.assertEqual(store.lookup_count, 2)

    def test_unmigrated_columns_fall_back_for_experience_and_chat(self):
        store = _FakeSupabase(missing_columns={"client_request_id", "experience_stages"})
        experience_payload = CommunityCreatePostRequest(
            post_type="experience",
            category="Z001",
            experience_stages=["初试", "复试"],
            client_request_id=REQUEST_ID,
            title="备考经验",
            content="完整经验内容",
        )

        experience = self._create(store, experience_payload)
        final_experience_insert = store.insert_attempts[-1]

        self.assertEqual(experience.experience_stages, ["初试", "复试"])
        self.assertNotIn("client_request_id", final_experience_insert)
        self.assertNotIn("experience_stages", final_experience_insert)
        self.assertEqual(
            final_experience_insert["media"][-1],
            {community.COMMUNITY_EXPERIENCE_STAGES_MARKER_KEY: ["初试", "复试"]},
        )

        chat_payload = CommunityCreatePostRequest(
            post_type="chat",
            category="数学基础",
            client_request_id="44444444-4444-4444-8444-444444444444",
            title="今日打卡",
            content="完成数学基础复习",
        )
        chat = self._create(store, chat_payload)
        final_chat_insert = store.insert_attempts[-1]

        self.assertEqual(chat.post_type, "chat")
        self.assertEqual(chat.experience_stages, [])
        self.assertNotIn("client_request_id", final_chat_insert)
        self.assertNotIn("experience_stages", final_chat_insert)
        self.assertEqual(final_chat_insert["media"], [])

    def test_missing_column_detection_does_not_swallow_other_insert_errors(self):
        unrelated_error = RuntimeError(
            "PGRST204: could not find the unrelated_column column in the schema cache"
        )

        self.assertFalse(
            community._is_missing_community_post_column_error(
                unrelated_error,
                "client_request_id",
            )
        )
        self.assertFalse(
            community._is_missing_community_post_column_error(
                unrelated_error,
                "experience_stages",
            )
        )

    def test_safe_error_log_and_user_messages_distinguish_provider_outage(self):
        payload = CommunityCreatePostRequest(
            post_type="chat",
            category="备考日常",
            client_request_id=REQUEST_ID,
            title="备考打卡",
            content="SECRET_BODY",
            media=[{"imageUrl": "https://example.com/SECRET_IMAGE.jpg"}],
        )

        with self.assertLogs(community.logger.name, level="WARNING") as captured:
            with self.assertRaises(HTTPException) as generic_error:
                community._raise_community_post_create_error(
                    RuntimeError("database rejected insert"),
                    payload=payload,
                    stage="post_insert",
                )
        self.assertEqual(generic_error.exception.detail, "帖子保存失败，请稍后重试")
        self.assertNotIn("SECRET_BODY", captured.output[0])
        self.assertNotIn("SECRET_IMAGE", captured.output[0])

        with self.assertRaises(HTTPException) as upstream_error:
            community._raise_community_post_create_error(
                TimeoutError("provider timed out"),
                payload=payload,
                stage="post_insert",
            )
        self.assertEqual(upstream_error.exception.detail, "考研圈上游服务暂时不可用，请稍后重试")

    def test_create_failures_report_each_publish_stage(self):
        chat_payload = CommunityCreatePostRequest(
            post_type="chat",
            category="备考日常",
            client_request_id=REQUEST_ID,
            title="备考打卡",
            content="今天完成了复习计划",
        )
        experience_payload = CommunityCreatePostRequest(
            post_type="experience",
            category="Z001",
            experience_stages=["初试"],
            client_request_id=REQUEST_ID,
            title="备考经验",
            content="完整经验内容",
        )
        cases = (
            (
                "author_lookup",
                chat_payload,
                {"_current_author": RuntimeError("author failed")},
            ),
            (
                "mentor_verification",
                experience_payload,
                {"_current_verified_mentor_author": RuntimeError("verification failed")},
            ),
            (
                "idempotency_lookup",
                chat_payload,
                {"_lookup_idempotent_community_post": RuntimeError("lookup failed")},
            ),
            (
                "post_insert",
                chat_payload,
                {"_insert_community_post_with_compatibility": RuntimeError("insert failed")},
            ),
            (
                "response",
                chat_payload,
                {"_insert_community_post_with_compatibility": None},
            ),
        )

        for expected_stage, payload, overrides in cases:
            with self.subTest(stage=expected_stage):
                patches = [
                    patch.object(community, "get_supabase_admin", return_value=object()),
                    patch.object(community, "_current_author", return_value=("研友", "研", None)),
                    patch.object(
                        community,
                        "_current_verified_mentor_author",
                        return_value={"display_name": "认证前辈"},
                    ),
                    patch.object(community, "_lookup_idempotent_community_post", return_value=None),
                    patch.object(
                        community,
                        "_insert_community_post_with_compatibility",
                        return_value=_post_row(),
                    ),
                ]
                for target_name, outcome in overrides.items():
                    patches.append(
                        patch.object(community, target_name, side_effect=outcome)
                        if isinstance(outcome, Exception)
                        else patch.object(community, target_name, return_value=outcome)
                    )
                handler = patch.object(
                    community,
                    "_raise_community_post_create_error",
                    side_effect=HTTPException(status_code=503, detail="captured"),
                )
                active = [item.start() for item in patches]
                mocked_handler = handler.start()
                try:
                    with self.assertRaises(HTTPException):
                        community.create_community_post(payload, AUTHOR_ID)
                    self.assertEqual(mocked_handler.call_args.kwargs["stage"], expected_stage)
                finally:
                    handler.stop()
                    for item in reversed(patches):
                        item.stop()

    def test_expected_http_exception_keeps_original_status_and_detail(self):
        payload = CommunityCreatePostRequest(
            post_type="experience",
            category="Z001",
            experience_stages=["初试"],
            client_request_id=REQUEST_ID,
            title="备考经验",
            content="完整经验内容",
        )
        expected = HTTPException(status_code=403, detail="认证状态不符合发布条件")

        with (
            patch.object(community, "get_supabase_admin", return_value=object()),
            patch.object(community, "_current_author", return_value=("研友", "研", None)),
            patch.object(community, "_current_verified_mentor_author", side_effect=expected),
            patch.object(community, "_raise_community_post_create_error") as error_handler,
        ):
            with self.assertRaises(HTTPException) as raised:
                community.create_community_post(payload, AUTHOR_ID)

        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(raised.exception.detail, "认证状态不符合发布条件")
        error_handler.assert_not_called()


if __name__ == "__main__":
    unittest.main()
