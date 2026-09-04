from __future__ import annotations

import unittest
from decimal import Decimal
from types import SimpleNamespace

from pydantic import ValidationError

from app.config import Settings
from app.schemas.adaptive_practice import CreateAdaptivePracticeSessionRequest
from app.services.adaptive_rollout import (
    ROLLOUT_BUCKET_COUNT,
    adaptive_rollout_allows_user,
    parse_rollout_user_ids,
    stable_rollout_bucket,
)


def _settings(**overrides):
    values = {
        "adaptive_practice_enabled": True,
        "adaptive_practice_rollout_percent": 0,
        "adaptive_practice_rollout_user_ids": "",
        "adaptive_practice_rollout_salt": "test-v1",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class AdaptiveRolloutTests(unittest.TestCase):
    def test_invalid_percentage_does_not_prevent_settings_startup(self):
        settings = Settings(
            _env_file=None,
            supabase_url="https://example.supabase.co",
            supabase_anon_key="anon-test",
            supabase_service_role_key="service-test",
            adaptive_practice_enabled=True,
            adaptive_practice_rollout_percent="invalid",
        )
        self.assertFalse(adaptive_rollout_allows_user(settings, "user-any"))

    def test_resume_marker_requires_client_session_id(self):
        with self.assertRaises(ValidationError):
            CreateAdaptivePracticeSessionRequest(
                exam_code="Z001",
                subject="逻辑推理",
                practice_mode="special",
                scopes=[{"module": "模块一"}],
                resume_existing_session=True,
            )

    def test_global_switch_is_an_emergency_kill_switch(self):
        settings = _settings(
            adaptive_practice_enabled=False,
            adaptive_practice_rollout_percent=100,
            adaptive_practice_rollout_user_ids="internal-user",
        )
        self.assertFalse(adaptive_rollout_allows_user(settings, "internal-user"))

    def test_zero_percent_still_allows_explicit_internal_users(self):
        settings = _settings(
            adaptive_practice_rollout_user_ids=" user-a, user-b, user-a "
        )
        self.assertEqual(
            parse_rollout_user_ids(settings.adaptive_practice_rollout_user_ids),
            {"user-a", "user-b"},
        )
        self.assertTrue(adaptive_rollout_allows_user(settings, "user-a"))
        self.assertFalse(adaptive_rollout_allows_user(settings, "user-c"))

    def test_percentage_cohort_is_stable_and_bounded(self):
        first = stable_rollout_bucket("user-42", salt="test-v1")
        second = stable_rollout_bucket("user-42", salt="test-v1")
        self.assertEqual(first, second)
        self.assertGreaterEqual(first, 0)
        self.assertLess(first, ROLLOUT_BUCKET_COUNT)

    def test_percentage_boundary_matches_bucket_threshold(self):
        user_id = "user-at-known-bucket"
        bucket = stable_rollout_bucket(user_id, salt="test-v1")
        miss_percent = Decimal(bucket) / Decimal(100)
        hit_percent = Decimal(bucket + 1) / Decimal(100)

        self.assertFalse(
            adaptive_rollout_allows_user(
                _settings(adaptive_practice_rollout_percent=str(miss_percent)),
                user_id,
            )
        )
        self.assertTrue(
            adaptive_rollout_allows_user(
                _settings(adaptive_practice_rollout_percent=str(hit_percent)),
                user_id,
            )
        )

    def test_full_rollout_allows_every_authenticated_user(self):
        settings = _settings(adaptive_practice_rollout_percent=100)
        self.assertTrue(adaptive_rollout_allows_user(settings, "user-any"))
        self.assertFalse(adaptive_rollout_allows_user(settings, ""))

    def test_partial_rollout_without_salt_fails_closed(self):
        settings = _settings(
            adaptive_practice_rollout_percent=1,
            adaptive_practice_rollout_salt="",
        )
        self.assertFalse(adaptive_rollout_allows_user(settings, "user-any"))

    def test_invalid_or_out_of_range_percentage_fails_closed(self):
        for value in ("invalid", "NaN", "-1", "100.01"):
            with self.subTest(value=value):
                settings = _settings(adaptive_practice_rollout_percent=value)
                self.assertFalse(adaptive_rollout_allows_user(settings, "user-any"))


if __name__ == "__main__":
    unittest.main()
