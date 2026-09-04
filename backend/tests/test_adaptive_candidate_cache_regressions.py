from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pydantic import ValidationError

from app.schemas.adaptive_practice import CreateAdaptivePracticeSessionRequest
from app.services import adaptive_practice
from app.services.adaptive_engine import AbilityState, TargetPlan, TargetZone


def _question(question_id: str, difficulty: int) -> dict:
    return {
        "id": question_id,
        "exam_code": "Z001",
        "subject": "逻辑推理",
        "module": "模块一",
        "submodule": "考点一",
        "question_type": "single_choice",
        "stem": f"题目 {question_id}",
        "option_a": "A",
        "option_b": "B",
        "option_c": "C",
        "option_d": "D",
        "answer": "A",
        "explanation": "解析",
        "difficulty": difficulty,
        "source_type": "manual",
        "source_year": None,
        "passage_id": None,
        "skill_tags": [],
        "solution_type": None,
        "estimated_time_sec": 60,
        "status": "active",
    }


class _NoReadClient:
    def table(self, table_name):
        raise AssertionError(f"unexpected database read: {table_name}")


class _ClaimClient:
    def __init__(self):
        self.payload = None

    def rpc(self, name, payload):
        if name != "claim_next_adaptive_practice_item":
            raise AssertionError(name)
        self.payload = payload
        return self

    def execute(self):
        item = dict(self.payload["p_item"])
        item.update(
            {
                "id": "item-1",
                "session_id": self.payload["p_session_id"],
                "question_id": self.payload["p_question_id"],
                "position": self.payload["p_position"],
                "item_status": "SELECTED",
            }
        )
        return SimpleNamespace(data=item)


class AdaptiveCandidateCacheRegressionTests(unittest.TestCase):
    def setUp(self):
        adaptive_practice._clear_candidate_caches()

    def tearDown(self):
        adaptive_practice._clear_candidate_caches()

    def test_scope_input_is_trimmed_and_blank_module_is_rejected(self):
        payload = CreateAdaptivePracticeSessionRequest(
            exam_code="Z001",
            subject="逻辑推理",
            practice_mode="special",
            scopes=[{"module": " 模块一 ", "submodule": " 考点一 "}],
        )
        self.assertEqual(payload.scopes[0].module, "模块一")
        self.assertEqual(payload.scopes[0].submodule, "考点一")

        with self.assertRaises(ValidationError):
            CreateAdaptivePracticeSessionRequest(
                exam_code="Z001",
                subject="逻辑推理",
                practice_mode="special",
                scopes=[{"module": "   "}],
            )

    def test_invalid_legacy_scope_does_not_poison_comprehensive_cache(self):
        invalid = {
            "stats_exam_code": "Z001",
            "subject": "逻辑推理",
            "scope_filter": [{"module": "   "}],
        }
        comprehensive = {
            "stats_exam_code": "Z001",
            "subject": "逻辑推理",
            "scope_filter": [],
        }
        self.assertEqual(
            adaptive_practice._fetch_candidate_questions(_NoReadClient(), invalid),
            [],
        )
        self.assertIsNone(
            adaptive_practice._read_cached_candidate_questions(comprehensive)
        )
        adaptive_practice._store_cached_candidate_questions(
            comprehensive, [_question("broad", 2)]
        )
        self.assertEqual(
            adaptive_practice._fetch_candidate_questions(_NoReadClient(), invalid),
            [],
        )

    def test_empty_candidate_ids_do_not_scan_or_cache_all_calibrations(self):
        session = {
            "stats_exam_code": "Z001",
            "subject": "逻辑推理",
            "scope_filter": [{"module": "不存在"}],
        }
        self.assertEqual(
            adaptive_practice._load_candidate_calibration_map(
                _NoReadClient(), session, []
            ),
            {},
        )
        self.assertEqual(
            adaptive_practice._load_calibration_map(_NoReadClient(), "Z001", []),
            {},
        )

    def test_preflight_witness_is_request_local_bounded_and_does_not_renew_ttl(self):
        session = {
            "stats_exam_code": "Z001",
            "subject": "逻辑推理",
            "scope_filter": [{"module": "模块一"}],
            "strategy_config": {},
        }
        base = _question("base", 2)
        witness = _question("witness", 4)
        calibration = {
            "question_id": "witness",
            "quality_status": "APPROVED",
            "quality_weight": 1.0,
            "is_diagnostic_candidate": True,
        }
        with patch.object(adaptive_practice, "monotonic", return_value=0):
            adaptive_practice._store_cached_candidate_questions(session, [base])
        cache_key = adaptive_practice._candidate_cache_key(session)
        original_expiry = adaptive_practice._candidate_question_cache[cache_key][1]

        with (
            patch.object(adaptive_practice, "monotonic", return_value=80),
            patch.object(
                adaptive_practice,
                "_find_fresh_approved_diagnostic_d4",
                return_value=(witness, calibration),
            ),
            patch.object(
                adaptive_practice,
                "_load_calibration_map",
                return_value={"witness": calibration},
            ),
            patch.object(
                adaptive_practice,
                "_load_ever_answered_question_ids",
                return_value=set(),
            ),
            patch.object(adaptive_practice, "MAX_CANDIDATE_ROWS", 1),
        ):
            adaptive_practice._prepare_initial_diagnostic_pool(
                object(), user_id="user-1", session=session
            )

        self.assertEqual(
            adaptive_practice._candidate_question_cache[cache_key][1],
            original_expiry,
        )
        self.assertEqual(
            adaptive_practice._candidate_calibration_cache[cache_key][0],
            frozenset({"base"}),
        )
        with patch.object(adaptive_practice, "monotonic", return_value=80):
            cached_questions = adaptive_practice._read_cached_candidate_questions(
                session
            )
        self.assertEqual([row["id"] for row in cached_questions], ["base"])
        self.assertEqual(
            [row["id"] for row in session["_prefetched_candidate_questions"]],
            ["witness"],
        )
        self.assertEqual(
            session["strategy_config"][adaptive_practice.INITIAL_DIAGNOSTIC_D4_KEY],
            "witness",
        )

    def test_later_selector_recovers_cap_exempt_session_witness(self):
        base = _question("base", 2)
        witness = _question("witness", 4)
        calibration = {
            "question_id": "witness",
            "quality_status": "APPROVED",
            "quality_weight": 1.0,
            "is_diagnostic_candidate": True,
        }
        session = {
            "id": "session-1",
            "stats_exam_code": "Z001",
            "subject": "逻辑推理",
            "requested_question_count": 8,
            "user_preference": "standard",
            "scope_filter": [{"module": "模块一"}],
            "state_snapshot": {
                "diagnostic_status": "NEW",
                "reliable_first_attempt_count": 0,
            },
            "strategy_config": {
                adaptive_practice.INITIAL_DIAGNOSTIC_D4_KEY: "witness"
            },
        }
        client = _ClaimClient()
        with (
            patch.object(adaptive_practice, "_load_session_items", return_value=[]),
            patch.object(
                adaptive_practice, "load_subject_state", return_value=AbilityState()
            ),
            patch.object(adaptive_practice, "load_topic_state_map", return_value={}),
            patch.object(adaptive_practice, "_observations_from_items", return_value=[]),
            patch.object(
                adaptive_practice,
                "plan_next_target",
                return_value=TargetPlan(
                    4,
                    TargetZone.CHALLENGE,
                    ("complete_warmup_difficulty_coverage",),
                    False,
                    True,
                ),
            ),
            patch.object(adaptive_practice, "_fetch_candidate_questions", return_value=[base]),
            patch.object(
                adaptive_practice,
                "_load_initial_diagnostic_d4_witness",
                return_value=(witness, calibration),
            ) as reload_witness,
            patch.object(
                adaptive_practice,
                "_load_candidate_calibration_map",
                return_value={},
            ) as load_calibrations,
            patch.object(
                adaptive_practice,
                "_load_candidate_history_snapshot",
                return_value={
                    "recent_question_ids": set(),
                    "ever_answered_question_ids": set(),
                    "due_review_values": {},
                },
            ),
            patch.object(adaptive_practice, "warm_submission_questions"),
        ):
            result = adaptive_practice._select_and_insert_next(
                client, "user-1", session
            )

        reload_witness.assert_called_once()
        self.assertEqual(load_calibrations.call_args.args[2], ["base"])
        self.assertEqual(result["question"]["id"], "witness")
        self.assertEqual(client.payload["p_question_id"], "witness")

    def test_existing_comprehensive_session_recovers_cap_exempt_d4_witness(self):
        base_questions = [
            _question("difficulty-1", 1),
            _question("difficulty-2", 2),
            _question("difficulty-3", 3),
        ]
        base_calibrations = {
            question["id"]: {
                "question_id": question["id"],
                "quality_status": "APPROVED",
                "quality_weight": 1.0,
                "is_diagnostic_candidate": True,
            }
            for question in base_questions
        }
        witness = _question("persisted-d4-witness", 4)
        witness_calibration = {
            "question_id": witness["id"],
            "quality_status": "APPROVED",
            "quality_weight": 1.0,
            "is_diagnostic_candidate": True,
        }
        session = {
            "id": "session-1",
            "stats_exam_code": "Z001",
            "subject": "逻辑推理",
            "requested_question_count": 4,
            "user_preference": "standard",
            "scope_filter": [{"module": "模块一"}],
            "strategy_config": {
                adaptive_practice.INITIAL_DIAGNOSTIC_D4_KEY: witness["id"]
            },
        }

        with (
            patch.object(
                adaptive_practice,
                "_fetch_candidate_questions",
                return_value=base_questions,
            ),
            patch.object(
                adaptive_practice,
                "_load_candidate_calibration_map",
                return_value=base_calibrations,
            ) as load_calibrations,
            patch.object(
                adaptive_practice,
                "_load_initial_diagnostic_d4_witness",
                return_value=(witness, witness_calibration),
            ) as reload_witness,
            patch.object(
                adaptive_practice,
                "_find_fresh_approved_diagnostic_d4",
            ) as find_replacement,
            patch.object(
                adaptive_practice,
                "_load_candidate_history_snapshot",
                return_value={
                    "recent_question_ids": set(),
                    "ever_answered_question_ids": set(),
                    "due_review_values": {},
                },
            ) as load_history,
            patch.object(adaptive_practice, "load_topic_state_map", return_value={}),
        ):
            claims = adaptive_practice._plan_comprehensive_claims(
                object(),
                user_id="user-1",
                session=session,
                subject_state=AbilityState(),
            )

        reload_witness.assert_called_once_with(
            unittest.mock.ANY,
            session=session,
            question_id=witness["id"],
        )
        find_replacement.assert_not_called()
        self.assertEqual(
            load_calibrations.call_args.args[2],
            ["difficulty-1", "difficulty-2", "difficulty-3"],
        )
        self.assertIn(witness["id"], load_history.call_args.kwargs["question_ids"])
        self.assertEqual([claim["position"] for claim in claims], [1, 2, 3, 4])
        self.assertEqual(claims[3]["question_id"], witness["id"])
        self.assertTrue(claims[3]["item"]["is_diagnostic"])


if __name__ == "__main__":
    unittest.main()
