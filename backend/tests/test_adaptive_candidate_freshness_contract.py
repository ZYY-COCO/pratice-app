from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = PROJECT_ROOT / "database" / "adaptive_question_delivery_v1.sql"
INCREMENTAL_PATH = (
    PROJECT_ROOT / "database" / "adaptive_candidate_freshness_hardening.sql"
)


class AdaptiveCandidateFreshnessContractTests(unittest.TestCase):
    @staticmethod
    def _compact(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    @classmethod
    def _function_sql(cls, sql: str) -> str:
        marker = (
            "create or replace function "
            "public.validate_practice_session_item_scope()"
        )
        start = sql.index(marker)
        body_start = sql.index("as $$", start)
        end = sql.index("\n$$;", body_start) + len("\n$$;")
        return sql[start:end]

    @classmethod
    def setUpClass(cls):
        cls.baseline = BASELINE_PATH.read_text(encoding="utf-8").lower()
        cls.incremental = INCREMENTAL_PATH.read_text(encoding="utf-8").lower()

    def test_baseline_and_incremental_lock_current_question_and_calibration(self):
        for name, sql in (
            ("baseline", self.baseline),
            ("incremental", self.incremental),
        ):
            with self.subTest(migration=name):
                function = self._compact(self._function_sql(sql))
                self.assertIn(
                    "select * into question_row from public.questions "
                    "where id = new.question_id for share;",
                    function,
                )
                self.assertIn(
                    "select * into calibration_row from public.question_calibration "
                    "where question_id = new.question_id and stats_exam_code = "
                    "session_row.stats_exam_code for share;",
                    function,
                )

    def test_baseline_and_incremental_reject_every_stale_candidate_dimension(self):
        required_fragments = (
            "manual_difficulty",
            "quality_status",
            "quality_weight",
            "question_valid",
            "item_difficulty",
            "expected_quality_status = 'excluded'",
            "adaptive_candidate_changed",
        )
        for name, sql in (
            ("baseline", self.baseline),
            ("incremental", self.incremental),
        ):
            with self.subTest(migration=name):
                function = self._function_sql(sql)
                for fragment in required_fragments:
                    self.assertIn(fragment, function)
                self.assertIn(
                    "not (new.strategy_metadata ? 'quality_status')",
                    function,
                )
                self.assertGreaterEqual(
                    function.count("raise exception 'adaptive_candidate_changed'"),
                    4,
                )

    def test_manual_difficulty_fallback_uses_the_python_d1_to_d5_theta_scale(self):
        expected = {
            1: "-1.6",
            2: "-0.8",
            3: "0.0",
            4: "0.8",
            5: "1.6",
        }
        for name, sql in (
            ("baseline", self.baseline),
            ("incremental", self.incremental),
        ):
            with self.subTest(migration=name):
                function = self._compact(self._function_sql(sql))
                for difficulty, theta in expected.items():
                    self.assertIn(f"when {difficulty} then {theta}", function)

    def test_trigger_is_insert_time_atomic_boundary_and_not_publicly_executable(self):
        for name, sql in (
            ("baseline", self.baseline),
            ("incremental", self.incremental),
        ):
            with self.subTest(migration=name):
                function = self._function_sql(sql)
                compact_sql = self._compact(sql)
                self.assertIn("if tg_op = 'insert' then", function)
                self.assertIn("security definer", function)
                self.assertIn("set search_path = public, pg_temp", function)
                self.assertIn(
                    "revoke all on function "
                    "public.validate_practice_session_item_scope() "
                    "from public, anon, authenticated, service_role;",
                    compact_sql,
                )

    def test_incremental_migration_is_repeatable_and_transaction_wrapped(self):
        compact = self._compact(self.incremental)
        self.assertTrue(compact.startswith("-- "))
        self.assertIn("begin; create or replace function", compact)
        self.assertTrue(compact.endswith("commit;"))
        self.assertNotIn("insert into public.", self.incremental)
        self.assertNotIn("update public.", self.incremental)
        self.assertNotIn("delete from public.", self.incremental)


if __name__ == "__main__":
    unittest.main()
