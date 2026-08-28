from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.routes.reports import (
    APP_TIMEZONE,
    DAILY_STUDY_MAX_SECONDS_PER_ANSWER,
    build_daily_study_leaderboard,
    build_daily_study_window,
)


class DailyStudyLeaderboardTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 8, 28, 12, 30, tzinfo=APP_TIMEZONE)
        self.profiles = [
            {"id": "user-1", "nickname": "研友一", "role": "user", "disabled_at": None},
            {"id": "user-2", "nickname": "研友二", "role": "user", "disabled_at": None},
            {"id": "admin-1", "nickname": "管理员", "role": "admin", "disabled_at": None},
            {"id": "disabled-1", "nickname": "停用用户", "role": "user", "disabled_at": "2026-08-20T00:00:00Z"},
        ]

    def test_daily_window_uses_shanghai_calendar_day(self):
        local_now, start_at, end_at = build_daily_study_window(self.now)

        self.assertEqual(local_now.date().isoformat(), "2026-08-28")
        self.assertEqual(start_at.astimezone(timezone.utc).isoformat(), "2026-08-27T16:00:00+00:00")
        self.assertEqual(end_at.astimezone(timezone.utc).isoformat(), "2026-08-28T16:00:00+00:00")

    def test_ranking_caps_single_answer_and_filters_ineligible_profiles(self):
        rows = [
            {"user_id": "user-1", "used_time": 120, "is_correct": True, "created_at": "2026-08-28T01:00:00Z"},
            {"user_id": "user-1", "used_time": 180, "is_correct": False, "created_at": "2026-08-28T02:00:00Z"},
            {"user_id": "user-2", "used_time": 5000, "is_correct": True, "created_at": "2026-08-28T03:00:00Z"},
            {"user_id": "admin-1", "used_time": 8000, "is_correct": True, "created_at": "2026-08-28T03:00:00Z"},
            {"user_id": "disabled-1", "used_time": 8000, "is_correct": True, "created_at": "2026-08-28T03:00:00Z"},
        ]

        response = build_daily_study_leaderboard(
            rows,
            self.profiles,
            "user-1",
            limit=3,
            now=self.now,
        )

        self.assertEqual(response.total_users, 2)
        self.assertEqual([item.user_id for item in response.items], ["user-2", "user-1"])
        self.assertEqual(response.items[0].study_seconds, DAILY_STUDY_MAX_SECONDS_PER_ANSWER)
        self.assertEqual(response.current_user.rank, 2)
        self.assertEqual(response.current_user.answer_count, 2)
        self.assertEqual(response.current_user.accuracy, 50)

    def test_ties_use_question_count_then_earlier_completion(self):
        profiles = self.profiles + [
            {"id": "user-3", "nickname": "研友三", "role": "user", "disabled_at": None},
        ]
        rows = [
            {"user_id": "user-1", "used_time": 150, "is_correct": True, "created_at": "2026-08-28T02:00:00Z"},
            {"user_id": "user-1", "used_time": 150, "is_correct": True, "created_at": "2026-08-28T03:00:00Z"},
            {"user_id": "user-2", "used_time": 300, "is_correct": True, "created_at": "2026-08-28T01:00:00Z"},
            {"user_id": "user-3", "used_time": 150, "is_correct": True, "created_at": "2026-08-28T01:00:00Z"},
            {"user_id": "user-3", "used_time": 150, "is_correct": True, "created_at": "2026-08-28T02:00:00Z"},
        ]

        response = build_daily_study_leaderboard(
            rows,
            profiles,
            "user-1",
            limit=2,
            now=self.now,
        )

        self.assertEqual([item.user_id for item in response.items], ["user-3", "user-1"])
        self.assertTrue(response.has_more)


if __name__ == "__main__":
    unittest.main()
