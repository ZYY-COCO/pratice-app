from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = PROJECT_ROOT / "database" / "adaptive_question_delivery_v1.sql"


class AdaptiveTrustedClaimContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sql = MIGRATION_PATH.read_text(encoding="utf-8").lower()
        marker = "create or replace function public.claim_next_adaptive_practice_item("
        start = sql.index(marker)
        body_start = sql.index("as $$", start)
        end = sql.index("\n$$;", body_start) + len("\n$$;")
        cls.claim = sql[start:end]
        cls.compact_claim = re.sub(r"\s+", " ", cls.claim).strip()

    def test_claim_persists_and_returns_locked_authoritative_question_snapshot(self):
        gate_start = self.claim.index("if is_diagnostic or target_zone = 'verify' then")
        insert_start = self.claim.index("insert into public.practice_session_items")
        gate = self.claim[gate_start:insert_start]
        compact_gate = re.sub(r"\s+", " ", gate).strip()

        self.assertLess(gate_start, insert_start)
        self.assertIn(
            "select * into question_row from public.questions "
            "where id = p_question_id for share;",
            self.compact_claim,
        )
        self.assertIn(
            "select * into trusted_calibration_row from public.question_calibration "
            "where question_id = p_question_id "
            "and stats_exam_code = session_row.stats_exam_code for share;",
            compact_gate,
        )
        self.assertIn(
            "insert into public.practice_session_item_question_snapshots",
            self.claim,
        )
        self.assertIn(
            "persisted_question_snapshot := to_jsonb(question_row)",
            self.compact_claim,
        )
        self.assertIn(
            "from public.practice_session_item_question_snapshots snapshot",
            self.claim,
        )
        self.assertEqual(
            self.compact_claim.count(
                "'question_snapshot', persisted_question_snapshot"
            ),
            2,
        )

    def test_trusted_gate_rechecks_active_question_and_full_session_scope(self):
        gate_start = self.claim.index("if is_diagnostic or target_zone = 'verify' then")
        gate_end = self.claim.index("if exists (", gate_start)
        gate = self.claim[gate_start:gate_end]

        self.assertIn("question_row.subject <> session_row.subject", gate)
        self.assertIn(
            "question_row.exam_code not in ('common', session_row.stats_exam_code)",
            gate,
        )
        self.assertIn("to_jsonb(question_row)->>'status'", gate)
        self.assertIn("session_row.mode = 'special'", gate)
        self.assertIn("jsonb_array_elements(session_row.scope_filter)", gate)
        self.assertIn("question_row.module", gate)
        self.assertIn("question_row.submodule", gate)

    def test_diagnostic_and_verify_use_distinct_calibration_contracts(self):
        self.assertIn("trusted_calibration_row.quality_status <> 'approved'", self.claim)
        self.assertIn("trusted_calibration_row.quality_weight < 0.7", self.claim)
        self.assertIn("target_zone <> 'verify'", self.claim)
        self.assertIn(
            "not trusted_calibration_row.is_diagnostic_candidate",
            self.claim,
        )

    def test_diagnostic_manual_difficulty_is_validated_against_locked_question(self):
        gate_start = self.claim.index("if is_diagnostic or target_zone = 'verify' then")
        gate_end = self.claim.index("if exists (", gate_start)
        gate = self.claim[gate_start:gate_end]
        compact_gate = re.sub(r"\s+", " ", gate).strip()

        self.assertIn("if target_zone <> 'verify' then", compact_gate)
        self.assertIn(
            "jsonb_typeof(strategy_metadata->'manual_difficulty') "
            "is distinct from 'number'",
            compact_gate,
        )
        self.assertIn(
            "(strategy_metadata->>'manual_difficulty') !~ '^[1-5]$'",
            compact_gate,
        )
        self.assertIn(
            "question_row.difficulty <> trusted_expected_difficulty",
            compact_gate,
        )
        self.assertEqual(
            compact_gate.count(
                "raise exception 'adaptive_trusted_candidate_changed'"
            ),
            5,
        )

    def test_every_trusted_eligibility_failure_uses_one_retry_marker(self):
        gate_start = self.claim.index("if is_diagnostic or target_zone = 'verify' then")
        gate_end = self.claim.index("if exists (", gate_start)
        gate = self.claim[gate_start:gate_end]

        self.assertEqual(gate.count("raise exception"), 5)
        self.assertEqual(
            gate.count("raise exception 'adaptive_trusted_candidate_changed'"),
            5,
        )
        self.assertNotIn("adaptive_question_not_active", gate)
        self.assertNotIn("adaptive_session_item_outside_selected_scope", gate)


if __name__ == "__main__":
    unittest.main()
