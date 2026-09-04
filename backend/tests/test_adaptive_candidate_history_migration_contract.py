from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = (
    PROJECT_ROOT / "database" / "adaptive_candidate_history_lookup_v1.sql"
)


class AdaptiveCandidateHistoryMigrationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = MIGRATION_PATH.read_text(encoding="utf-8").lower()

    @staticmethod
    def compact(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    def test_lookup_is_additive_bounded_and_service_role_only(self):
        compact = self.compact(self.sql)

        self.assertIn("create function public.get_adaptive_candidate_history_v1", compact)
        self.assertIn("stable security invoker", compact)
        self.assertIn("if candidate_count > 3000", compact)
        self.assertIn(
            "revoke all on function public.get_adaptive_candidate_history_v1( "
            "uuid, text, text, uuid[], integer, boolean ) from public, anon, authenticated",
            compact,
        )
        self.assertIn(
            "grant execute on function public.get_adaptive_candidate_history_v1( "
            "uuid, text, text, uuid[], integer, boolean ) to service_role",
            compact,
        )
        self.assertIn("notify pgrst, 'reload schema'", compact)

    def test_recent_and_review_signals_are_exam_and_subject_isolated(self):
        compact = self.compact(self.sql)

        self.assertIn("answers.stats_exam_code = p_stats_exam_code", compact)
        self.assertIn("questions.subject = p_subject", compact)
        self.assertEqual(
            compact.count("questions.exam_code in ('common', p_stats_exam_code)"),
            3,
        )
        self.assertEqual(
            compact.count(
                "questions.exam_code <> 'common' or questions.subject in "
                "('中华文化', '英语运用')"
            ),
            3,
        )
        self.assertIn(
            "progress.stats_exam_code = p_stats_exam_code and progress.question_id = candidates.question_id",
            compact,
        )
        self.assertIn("limit normalized_recent_limit", compact)
        self.assertIn("order by answers.created_at desc, answers.id desc", compact)

    def test_global_seen_uses_physical_question_ids_without_exam_mixing_ability(self):
        compact = self.compact(self.sql)
        start = compact.index("globally_seen_ids as")
        end = compact.index("scoped_progress as", start)
        globally_seen = compact[start:end]

        self.assertIn("answers.user_id = p_user_id", globally_seen)
        self.assertIn("answers.question_id = candidates.question_id", globally_seen)
        self.assertIn("questions.subject = p_subject", globally_seen)
        self.assertNotIn("answers.stats_exam_code", globally_seen)
        self.assertIn(
            "idx_user_question_progress_user_question_exam",
            compact,
        )


if __name__ == "__main__":
    unittest.main()
