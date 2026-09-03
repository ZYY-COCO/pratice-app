import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError

from app.routes import admin, community
from app.schemas.admin import AdminCommunityExperienceReviewDecisionRequest
from app.schemas.community import CommunityCreatePostRequest, CommunityResubmitExperiencePostRequest


AUTHOR_ID = "11111111-1111-4111-8111-111111111111"
ADMIN_ID = "22222222-2222-4222-8222-222222222222"
POST_ID = "33333333-3333-4333-8333-333333333333"


def _experience_row(**overrides):
    row = {
        "id": POST_ID,
        "author_id": AUTHOR_ID,
        "author_name": "认证前辈",
        "author_avatar": "前",
        "author_tone": "mint",
        "post_type": "experience",
        "category": "Z001",
        "experience_stages": ["初试"],
        "title": "备考经验",
        "content": "完整经验内容",
        "media": [],
        "is_published": False,
        "is_featured": False,
        "review_status": "pending",
        "review_version": 1,
        "submitted_at": "2026-09-01T00:00:00Z",
        "like_count": 0,
        "comment_count": 0,
        "view_count": 0,
    }
    row.update(overrides)
    return row


class _RpcSupabase:
    def __init__(self, response_row):
        self.response_row = response_row
        self.rpc_name = ""
        self.rpc_args = {}

    def rpc(self, name, args):
        self.rpc_name = name
        self.rpc_args = dict(args)
        return self

    def execute(self):
        return SimpleNamespace(data=[self.response_row])


class _ExperienceReviewListQuery:
    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self


class _ExperienceReviewListSupabase:
    def table(self, _name):
        return _ExperienceReviewListQuery()


class CommunityExperienceReviewTests(unittest.TestCase):
    def test_review_list_accepts_all_category_filter(self):
        with (
            patch.object(admin, "get_supabase_admin", return_value=_ExperienceReviewListSupabase()),
            patch.object(admin, "call_supabase", return_value=SimpleNamespace(data=[], count=0)),
        ):
            result = admin.question_admin_community_experience_reviews(
                review_status="all",
                category="all",
                experience_stage=None,
                search=None,
                date_from=None,
                date_to=None,
                sort_by="newest",
                limit=20,
                offset=0,
                _={},
            )

        self.assertEqual(result.count, 0)
        self.assertEqual(result.items, [])

    def test_admin_review_detail_includes_verified_author_legal_name(self):
        supabase = object()
        with (
            patch.object(admin, "get_supabase_admin", return_value=supabase),
            patch.object(admin, "_community_post_detail_row", return_value=_experience_row()),
            patch.object(
                admin,
                "_fetch_admin_experience_author_legal_name",
                return_value="张三",
            ) as fetch_legal_name,
            patch.object(admin, "_fetch_admin_experience_review_history", return_value=[]),
        ):
            result = admin.question_admin_community_experience_review_detail(POST_ID, _={})

        self.assertEqual(result.author_legal_name, "张三")
        fetch_legal_name.assert_called_once_with(supabase, AUTHOR_ID)

    def test_new_experience_post_is_inserted_as_pending_and_hidden(self):
        payload = CommunityCreatePostRequest(
            post_type="experience",
            category="Z001",
            experience_stages=["初试"],
            title="备考经验",
            content="完整经验内容",
        )
        captured = {}

        def capture_insert(_supabase, **kwargs):
            captured.update(kwargs["post_data"])
            return _experience_row(**kwargs["post_data"])

        with (
            patch.object(community, "get_supabase_admin", return_value=object()),
            patch.object(community, "_current_author", return_value=("研友", "研", None)),
            patch.object(
                community,
                "_current_verified_mentor_author",
                return_value={"display_name": "认证前辈", "avatar_label": "前", "avatar_tone": "mint"},
            ),
            patch.object(community, "_lookup_idempotent_community_post", return_value=None),
            patch.object(community, "_insert_community_post_with_compatibility", side_effect=capture_insert),
        ):
            result = community.create_community_post(payload, AUTHOR_ID)

        self.assertFalse(captured["is_published"])
        self.assertEqual(captured["review_status"], "pending")
        self.assertEqual(captured["review_version"], 1)
        self.assertEqual(result.review_status, "pending")
        self.assertFalse(result.is_published)

    def test_rejection_requires_official_reason_and_note(self):
        with self.assertRaises(ValidationError):
            AdminCommunityExperienceReviewDecisionRequest(decision="rejected")
        with self.assertRaises(ValidationError):
            AdminCommunityExperienceReviewDecisionRequest(
                decision="rejected",
                reason_code="low_quality",
            )

        request = AdminCommunityExperienceReviewDecisionRequest(
            decision="rejected",
            reason_code="low_quality",
            review_note="请补充本人真实备考过程。",
        )
        self.assertEqual(request.review_note, "请补充本人真实备考过程。")

    def test_admin_approval_publishes_and_notifies_author(self):
        approved_row = _experience_row(
            review_status="approved",
            is_published=True,
            reviewed_by=ADMIN_ID,
            reviewed_at="2026-09-01T01:00:00Z",
        )
        payload = AdminCommunityExperienceReviewDecisionRequest(decision="approved")

        with (
            patch.object(admin, "get_supabase_admin", return_value=object()),
            patch.object(admin, "_community_post_detail_row", return_value=_experience_row()),
            patch.object(admin, "call_supabase", return_value=SimpleNamespace(data=[approved_row])),
            patch.object(admin, "create_user_notification") as create_notification,
            patch.object(admin, "_log_admin_action") as log_action,
        ):
            result = admin.question_admin_review_community_experience_post(
                POST_ID,
                payload,
                {"id": ADMIN_ID},
            )

        self.assertEqual(result.review_status, "approved")
        self.assertTrue(result.is_published)
        self.assertEqual(
            create_notification.call_args.kwargs["notification_type"],
            "community_experience_review_approved",
        )
        self.assertIn(f"postId={POST_ID}", create_notification.call_args.kwargs["route_path"])
        log_action.assert_called_once()

    def test_generic_restore_cannot_bypass_experience_review(self):
        payload = admin.AdminCommunityPostVisibilityRequest(is_published=True)
        with (
            patch.object(admin, "get_supabase_admin", return_value=object()),
            patch.object(
                admin,
                "_community_post_detail_row",
                return_value=_experience_row(review_status="rejected"),
            ),
        ):
            with self.assertRaises(HTTPException) as raised:
                admin.question_admin_update_community_post_visibility(
                    POST_ID,
                    payload,
                    {"id": ADMIN_ID},
                )

        self.assertEqual(raised.exception.status_code, 409)

    def test_rejected_post_resubmission_returns_to_pending_with_new_payload(self):
        resubmitted = _experience_row(
            category="Z002",
            experience_stages=["初试", "复试"],
            title="修改后的经验贴",
            content="已经删除引流信息并补充备考过程。",
            review_status="pending",
            review_version=2,
        )
        supabase = _RpcSupabase(resubmitted)
        payload = CommunityResubmitExperiencePostRequest(
            category="Z002",
            experience_stages=["初试", "复试"],
            title="修改后的经验贴",
            content="已经删除引流信息并补充备考过程。",
        )

        with (
            patch.object(community, "get_supabase_admin", return_value=supabase),
            patch.object(
                community,
                "_get_owned_post_row",
                return_value=_experience_row(review_status="rejected", review_version=1),
            ),
            patch.object(community, "_current_verified_mentor_author", return_value={"display_name": "认证前辈"}),
            patch.object(community, "_fetch_community_profiles", return_value={}),
        ):
            result = community.resubmit_my_community_experience_post(POST_ID, payload, AUTHOR_ID)

        self.assertEqual(supabase.rpc_name, "resubmit_circle_community_experience_post")
        self.assertEqual(supabase.rpc_args["p_experience_stages"], ["初试", "复试"])
        self.assertEqual(result.review_status, "pending")
        self.assertEqual(result.review_version, 2)
        self.assertFalse(result.is_published)


if __name__ == "__main__":
    unittest.main()
