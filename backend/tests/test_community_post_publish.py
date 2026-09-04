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

    def update(self, payload):
        self.action = "update"
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

        if self.action == "update":
            self.store.update_attempts.append(dict(self.payload))
            current = self.store.rows[0] if self.store.rows else _post_row()
            updated = {**current, **self.payload}
            self.store.rows = [updated]
            return SimpleNamespace(data=[updated])

        raise AssertionError("Unexpected fake query action")


class _FakeSupabase:
    def __init__(self, *, missing_columns=None, rows=None, duplicate_once=False):
        self.missing_columns = set(missing_columns or [])
        self.rows = list(rows or [])
        self.duplicate_once = duplicate_once
        self.lookup_count = 0
        self.insert_attempts = []
        self.update_attempts = []

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
            patch.object(community, "_current_author", return_value=("账号昵称", "账", "https://example.com/account-avatar.png")),
            patch.object(community, "_current_verified_mentor_author", return_value=mentor),
        ):
            return community.create_community_post(payload, AUTHOR_ID)

    def test_migrated_experience_post_uses_columns_without_media_marker(self):
        store = _FakeSupabase()
        payload = CommunityCreatePostRequest(
            post_type="experience",
            category="申请制",
            experience_stages=["复试"],
            client_request_id=REQUEST_ID,
            title="备考经验",
            content="完整经验内容",
        )

        result = self._create(store, payload)

        self.assertEqual(result.category, "申请制")
        self.assertEqual(result.experience_stages, ["复试"])
        self.assertEqual(len(store.insert_attempts), 1)
        inserted = store.insert_attempts[0]
        self.assertEqual(inserted["client_request_id"], str(REQUEST_ID))
        self.assertEqual(inserted["category"], "申请制")
        self.assertEqual(inserted["experience_stages"], ["复试"])
        self.assertEqual(inserted["author_name"], "账号昵称")
        self.assertEqual(inserted["author_avatar"], "账")
        self.assertEqual(inserted["author_tone"], "blue")
        self.assertEqual(result.author, "账号昵称")
        self.assertEqual(result.avatar_url, "https://example.com/account-avatar.png")
        self.assertNotIn(community.COMMUNITY_EXPERIENCE_STAGES_MARKER_KEY, str(inserted["media"]))

    def test_existing_experience_post_prefers_current_account_nickname(self):
        row = _post_row(
            post_type="experience",
            author_name="审核档案姓名",
            author_avatar="审",
            category="Z001",
        )

        result = community._post_item(
            row,
            set(),
            {},
            {AUTHOR_ID: {"nickname": "当前账号昵称", "avatar_url": "https://example.com/current-avatar.png"}},
            {AUTHOR_ID},
        )

        self.assertEqual(result.author, "当前账号昵称")
        self.assertEqual(result.avatar, "当")
        self.assertEqual(result.avatar_url, "https://example.com/current-avatar.png")
        self.assertTrue(result.author_verified)

    def test_existing_experience_post_never_falls_back_to_review_name(self):
        row = _post_row(
            post_type="experience",
            author_name="审核档案姓名",
            author_avatar="审",
            category="Z001",
        )

        account_with_email = community._post_item(
            row,
            set(),
            {},
            {AUTHOR_ID: {"nickname": "", "email": "account-name@example.com"}},
            {AUTHOR_ID},
        )
        account_without_public_name = community._post_item(
            row,
            set(),
            {},
            {AUTHOR_ID: {"nickname": "", "email": ""}},
            {AUTHOR_ID},
        )

        self.assertEqual(account_with_email.author, "account-name")
        self.assertEqual(account_without_public_name.author, "研友")
        self.assertNotEqual(account_without_public_name.author, "审核档案姓名")

    def test_owner_can_edit_chat_post_without_review_state(self):
        current = _post_row()
        store = _FakeSupabase(rows=[current])
        payload = CommunityCreatePostRequest(
            post_type="chat",
            category="中华文化",
            client_request_id=REQUEST_ID,
            title="修改后的标题",
            content="修改后的正文",
        )

        with (
            patch.object(community, "get_supabase_admin", return_value=store),
            patch.object(community, "_get_owned_post_row", return_value=current),
            patch.object(community, "_ensure_owned_post_editable"),
            patch.object(
                community,
                "_fetch_community_profiles",
                return_value={AUTHOR_ID: {"nickname": "账号昵称"}},
            ),
        ):
            result = community.update_my_community_post(current["id"], payload, AUTHOR_ID)

        updated = store.update_attempts[0]
        self.assertEqual(updated["category"], "中华文化")
        self.assertNotIn("review_status", updated)
        self.assertEqual(result.title, "修改后的标题")
        self.assertTrue(result.is_mine)

    def test_owner_experience_edit_returns_to_review(self):
        current = _post_row(
            post_type="experience",
            category="Z001",
            experience_stages=["初试"],
            review_status="approved",
            review_version=2,
            is_published=True,
        )
        store = _FakeSupabase(rows=[current])
        payload = CommunityCreatePostRequest(
            post_type="experience",
            category="申请制",
            experience_stages=["复试"],
            client_request_id=REQUEST_ID,
            title="修改后的经验",
            content="修改后的经验正文",
        )

        with (
            patch.object(community, "get_supabase_admin", return_value=store),
            patch.object(community, "_get_owned_post_row", return_value=current),
            patch.object(community, "_ensure_owned_post_editable"),
            patch.object(community, "_current_verified_mentor_author", return_value={"verified": True}),
            patch.object(
                community,
                "_fetch_community_profiles",
                return_value={AUTHOR_ID: {"nickname": "账号昵称"}},
            ),
        ):
            result = community.update_my_community_post(current["id"], payload, AUTHOR_ID)

        updated = store.update_attempts[0]
        self.assertFalse(updated["is_published"])
        self.assertEqual(updated["review_status"], "pending")
        self.assertEqual(updated["review_version"], 3)
        self.assertEqual(result.category, "申请制")
        self.assertEqual(result.experience_stages, ["复试"])
        self.assertTrue(result.is_mine)

    def test_reported_post_cannot_be_edited(self):
        with patch.object(
            community,
            "call_supabase",
            side_effect=[SimpleNamespace(data=[{"id": "report-id"}]), SimpleNamespace(data=[])],
        ):
            with self.assertRaises(HTTPException) as raised:
                community._ensure_owned_post_editable(object(), _post_row()["id"])

        self.assertEqual(raised.exception.status_code, 409)
        self.assertIn("暂不能编辑", raised.exception.detail)

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
