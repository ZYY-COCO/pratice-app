import unittest
from uuid import UUID

from pydantic import ValidationError

from app.routes.community import (
    COMMUNITY_EXPERIENCE_STAGES_MARKER_KEY,
    _community_experience_stages,
    _create_post_media,
    _matches_community_experience_stage,
    _normalise_media,
)
from app.schemas.community import CommunityCreatePostRequest


class CommunityExperienceStageTests(unittest.TestCase):
    def test_long_posts_and_nine_images_are_valid_for_both_post_types(self):
        media = [
            {"imageUrl": f"https://example.com/community-{index}.jpg"}
            for index in range(9)
        ]

        chat = CommunityCreatePostRequest(
            post_type="chat",
            category="英语运用",
            title="长文研友聊",
            content="研" * 2999,
            media=media,
        )
        experience = CommunityCreatePostRequest(
            post_type="experience",
            category="Z002",
            experience_stages=["申请制", "初试", "复试"],
            title="长文经验贴",
            content="验" * 2999,
            media=media,
        )

        self.assertEqual(len(chat.media), 9)
        self.assertEqual(chat.experience_stages, [])
        self.assertEqual(len(experience.media), 9)
        self.assertEqual(experience.experience_stages, ["申请制", "初试", "复试"])

    def test_experience_exam_code_is_single_and_stages_are_multi_select(self):
        payload = CommunityCreatePostRequest(
            post_type="experience",
            category="Z001",
            experience_stages=["初试", "复试", "初试"],
            title="备考经验",
            content="完整经验内容",
        )

        self.assertEqual(payload.category, "Z001")
        self.assertEqual(payload.experience_stages, ["初试", "复试"])
        self.assertIsInstance(payload.client_request_id, UUID)

    def test_chat_always_clears_experience_stages(self):
        payload = CommunityCreatePostRequest(
            post_type="chat",
            category="备考日常",
            experience_stages=["申请制", "复试"],
            title="备考打卡",
            content="今天完成了复习计划",
        )

        self.assertEqual(payload.experience_stages, [])

    def test_experience_rejects_legacy_category_and_requires_stage(self):
        with self.assertRaises(ValidationError):
            CommunityCreatePostRequest(
                post_type="experience",
                category="专业课",
                experience_stages=["初试"],
                title="备考经验",
                content="完整经验内容",
            )

        with self.assertRaises(ValidationError):
            CommunityCreatePostRequest(
                post_type="experience",
                category="Z002",
                title="备考经验",
                content="完整经验内容",
            )

    def test_stage_metadata_is_returned_but_not_exposed_as_media(self):
        media = [
            {"imageUrl": "https://example.com/image.jpg"},
            {COMMUNITY_EXPERIENCE_STAGES_MARKER_KEY: ["申请制", "复试"]},
        ]
        row = {"post_type": "experience", "media": media}

        self.assertEqual(_community_experience_stages(row), ["申请制", "复试"])
        self.assertEqual(_normalise_media(media), [{"imageUrl": "https://example.com/image.jpg"}])

    def test_independent_stage_column_has_priority_and_new_media_has_no_marker(self):
        media = [
            {"imageUrl": "https://example.com/image.jpg"},
            {COMMUNITY_EXPERIENCE_STAGES_MARKER_KEY: ["复试"]},
        ]
        row = {
            "post_type": "experience",
            "experience_stages": ["初试", "申请制", "初试"],
            "media": media,
        }

        self.assertEqual(_community_experience_stages(row), ["初试", "申请制"])
        self.assertEqual(
            _create_post_media(
                [{"imageUrl": "https://example.com/new.jpg"}],
                "experience",
                ["初试"],
            ),
            [{"imageUrl": "https://example.com/new.jpg"}],
        )

    def test_legacy_experience_categories_map_to_unified_stage_filters(self):
        legacy_initial = {"post_type": "experience", "category": "专业课", "media": []}
        legacy_retest = {"post_type": "experience", "category": "复试", "media": []}

        self.assertEqual(_community_experience_stages(legacy_initial), ["初试"])
        self.assertEqual(_community_experience_stages(legacy_retest), ["复试"])
        self.assertTrue(_matches_community_experience_stage(legacy_initial, "初试"))
        self.assertFalse(_matches_community_experience_stage(legacy_initial, "复试"))


if __name__ == "__main__":
    unittest.main()
