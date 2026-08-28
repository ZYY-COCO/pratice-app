import unittest

from pydantic import ValidationError

from app.routes.reports import calculate_study_seconds
from app.schemas.reports import StudyGoalUpdateRequest


class StudyGoalTests(unittest.TestCase):
    def test_request_accepts_supported_product_values(self) -> None:
        request = StudyGoalUpdateRequest(
            exam_code="Z001",
            daily_minutes=60,
            weekly_question_target=300,
        )

        self.assertEqual(request.daily_minutes, 60)
        self.assertEqual(request.weekly_question_target, 300)

    def test_request_enforces_product_ranges_and_steps(self) -> None:
        invalid_payloads = (
            {"daily_minutes": 15, "weekly_question_target": 300},
            {"daily_minutes": 65, "weekly_question_target": 300},
            {"daily_minutes": 190, "weekly_question_target": 300},
            {"daily_minutes": 60, "weekly_question_target": 25},
            {"daily_minutes": 60, "weekly_question_target": 325},
            {"daily_minutes": 60, "weekly_question_target": 2050},
        )

        for values in invalid_payloads:
            with self.subTest(values=values), self.assertRaises(ValidationError):
                StudyGoalUpdateRequest(exam_code="Z001", **values)

    def test_today_study_time_uses_persisted_non_negative_seconds(self) -> None:
        self.assertEqual(
            calculate_study_seconds([
                {"used_time": 35},
                {"used_time": "70"},
                {"used_time": -10},
                {"used_time": None},
            ]),
            105,
        )

if __name__ == "__main__":
    unittest.main()
