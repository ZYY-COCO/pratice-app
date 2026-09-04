from __future__ import annotations

import re
import unittest
from collections import Counter
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.adaptive_practice import (
    CreateAdaptivePracticeSessionRequest,
    SubmitAdaptiveComprehensiveSessionRequest,
)
from app.services import adaptive_practice
from app.services import answers as answer_service
from app.services.adaptive_engine import AbilityState


def question(question_id: str, *, answer: str = "A") -> dict:
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
        "answer": answer,
        "explanation": f"解析 {question_id}",
        "difficulty": 2,
        "estimated_time_sec": 60,
        "source_type": "official",
        "source_year": 2026,
        "passage_id": None,
    }


def item(position: int, *, answer_id: str | None = None) -> dict:
    q = question(f"q-{position}", answer="A" if position % 2 else "B")
    return {
        "id": f"item-{position}",
        "session_id": "session-1",
        "question_id": q["id"],
        "position": position,
        "item_status": "ANSWERED" if answer_id else "SELECTED",
        "selection_reason": "comprehensive_matched_training",
        "target_zone": "main",
        "predicted_probability": 0.7,
        "item_difficulty": 0.0,
        "strategy_metadata": {
            "reason_codes": ["comprehensive_matched_training"],
            "quality_weight": 0.9,
            "question_valid": True,
        },
        "is_diagnostic": False,
        "is_challenge": False,
        "answer_id": answer_id,
        # _load_session_items maps the service-role-only persisted snapshot to
        # this key; it is not the mutable public questions table relation.
        "questions": q,
    }


def session(*, count: int, status: str = "ACTIVE", submission: dict | None = None) -> dict:
    strategy_config = {}
    if submission is not None:
        strategy_config["comprehensive_submission"] = submission
    return {
        "id": "session-1",
        "stats_exam_code": "Z001",
        "subject": "逻辑推理",
        "mode": "comprehensive",
        "requested_question_count": count,
        "status": status,
        "strategy_config": strategy_config,
    }


def completion_state() -> dict:
    return adaptive_practice.serialize_state(AbilityState())


def submission_payload(
    positions: list[int],
    *,
    skipped: set[int] | None = None,
) -> SubmitAdaptiveComprehensiveSessionRequest:
    skipped = skipped or set()
    return SubmitAdaptiveComprehensiveSessionRequest(
        client_submission_id="round-submit-1",
        answers=[
            {
                "practice_session_item_id": f"item-{position}",
                "selected_answer": None if position in skipped else "A",
                "used_time": position * 10,
                "client_submission_id": f"answer-{position}",
            }
            for position in positions
        ],
    )


class RpcClient:
    def __init__(self, responses: dict[str, list[object] | object]):
        self.responses = {
            name: list(value) if isinstance(value, list) else [value]
            for name, value in responses.items()
        }
        self.calls: list[tuple[str, dict]] = []
        self.pending_name: str | None = None

    def rpc(self, name, payload):
        self.calls.append((name, payload))
        self.pending_name = name
        return self

    def execute(self):
        if self.pending_name is None:
            raise AssertionError("execute called without rpc")
        outcomes = self.responses.get(self.pending_name)
        if not outcomes:
            raise AssertionError(f"unexpected or exhausted rpc: {self.pending_name}")
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(data=outcome)


class AdaptiveComprehensivePracticeTests(unittest.TestCase):
    def test_comprehensive_request_only_allows_standard_without_challenge(self):
        allowed = CreateAdaptivePracticeSessionRequest(
            exam_code="Z001",
            subject="逻辑推理",
            practice_mode="comprehensive",
            preference="standard",
            accepted_challenge=False,
        )
        self.assertEqual(allowed.preference, "standard")
        self.assertFalse(allowed.accepted_challenge)

        for preference, accepted_challenge in (
            ("steady", False),
            ("steady", True),
            ("standard", True),
            ("challenge", False),
            ("challenge", True),
        ):
            with self.subTest(
                preference=preference,
                accepted_challenge=accepted_challenge,
            ):
                with self.assertRaisesRegex(
                    ValidationError,
                    "standard D1-D4 difficulty policy",
                ):
                    CreateAdaptivePracticeSessionRequest(
                        exam_code="Z001",
                        subject="逻辑推理",
                        practice_mode="comprehensive",
                        preference=preference,
                        accepted_challenge=accepted_challenge,
                    )

    def test_special_request_keeps_all_preference_and_challenge_combinations(self):
        for preference in ("steady", "standard", "challenge"):
            for accepted_challenge in (False, True):
                with self.subTest(
                    preference=preference,
                    accepted_challenge=accepted_challenge,
                ):
                    payload = CreateAdaptivePracticeSessionRequest(
                        exam_code="Z001",
                        subject="逻辑推理",
                        practice_mode="special",
                        scopes=[{"module": "模块一", "submodule": "考点一"}],
                        preference=preference,
                        accepted_challenge=accepted_challenge,
                    )
                    self.assertEqual(payload.preference, preference)
                    self.assertEqual(payload.accepted_challenge, accepted_challenge)

    def test_cold_comprehensive_idempotence_uses_the_fixed_eight_question_count(self):
        payload = CreateAdaptivePracticeSessionRequest(
            exam_code="Z001",
            subject="逻辑推理",
            practice_mode="comprehensive",
            question_count=10,
        )
        existing = {
            "stats_exam_code": "Z001",
            "subject": "逻辑推理",
            "mode": "comprehensive",
            "scope_filter": [],
            "requested_question_count": 8,
            "user_preference": "standard",
            "diagnostic_status": "NEW",
            "state_snapshot": {
                "diagnostic_status": "NEW",
                "reliable_first_attempt_count": 0,
            },
            "strategy_config": {"accepted_challenge": False},
        }

        adaptive_practice._assert_idempotent_session_matches(
            existing,
            payload=payload,
            exam_code="Z001",
            subject="逻辑推理",
        )

    def test_comprehensive_replay_uses_private_snapshot_before_any_live_question(self):
        frozen = question("q-1", answer="C")
        row = item(1)
        row["question_snapshot"] = frozen
        row["questions"] = {**frozen, "stem": "后来被编辑的题面", "answer": "D"}

        view = adaptive_practice._comprehensive_items_from_rows(
            [row],
            user_id="user-1",
        )[0]

        self.assertEqual(view["question"]["stem"], frozen["stem"])
        self.assertIsNone(view["question"]["answer"])
        self.assertIsNone(view["question"]["explanation"])

    def test_comprehensive_candidate_change_clears_cache_and_replans_once(self):
        current_session = session(count=1)
        first_claims = [{"question_id": "stale", "position": 1, "item": {}}]
        second_claims = [{"question_id": "fresh", "position": 1, "item": {}}]
        client = RpcClient(
            {
                "claim_adaptive_comprehensive_practice_items": [
                    RuntimeError("adaptive_candidate_changed"),
                    [item(1)],
                ]
            }
        )

        with (
            patch.object(adaptive_practice, "_load_session_items", return_value=[]),
            patch.object(
                adaptive_practice,
                "_plan_comprehensive_claims",
                side_effect=[first_claims, second_claims],
            ) as plan,
            patch.object(adaptive_practice, "_invalidate_candidate_cache") as invalidate,
        ):
            result = adaptive_practice._get_or_create_comprehensive_items(
                client,
                user_id="user-1",
                session=current_session,
                subject_state=AbilityState(state_version=4),
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(plan.call_count, 2)
        invalidate.assert_called_once_with(current_session)
        claim_calls = [
            payload
            for name, payload in client.calls
            if name == "claim_adaptive_comprehensive_practice_items"
        ]
        self.assertEqual(len(claim_calls), 2)
        self.assertEqual(claim_calls[0]["p_items"], first_claims)
        self.assertEqual(claim_calls[1]["p_items"], second_claims)

    def test_repeated_comprehensive_candidate_change_returns_retryable_503(self):
        current_session = session(count=1)
        client = RpcClient(
            {
                "claim_adaptive_comprehensive_practice_items": [
                    RuntimeError("adaptive_candidate_changed"),
                    RuntimeError("adaptive_candidate_changed"),
                ]
            }
        )

        with (
            patch.object(adaptive_practice, "_load_session_items", return_value=[]),
            patch.object(
                adaptive_practice,
                "_plan_comprehensive_claims",
                return_value=[{"question_id": "q-1", "position": 1, "item": {}}],
            ) as plan,
            patch.object(adaptive_practice, "_invalidate_candidate_cache") as invalidate,
        ):
            with self.assertRaises(HTTPException) as raised:
                adaptive_practice._get_or_create_comprehensive_items(
                    client,
                    user_id="user-1",
                    session=current_session,
                    subject_state=AbilityState(state_version=4),
                )

        self.assertEqual(plan.call_count, 2)
        self.assertEqual(invalidate.call_count, 1)
        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(
            raised.exception.detail["code"],
            "ADAPTIVE_COMPREHENSIVE_POOL_CHANGED",
        )
        self.assertTrue(raised.exception.detail["retryable"])

    def test_submit_locks_canonical_answers_and_grades_only_private_snapshots(self):
        fixed_items = [item(3), item(1), item(2)]
        payload = submission_payload([3, 1, 2])
        client = RpcClient(
            {
                "begin_adaptive_comprehensive_submission": {
                    "session_id": "session-1",
                    "phase": "LOCKED",
                    "idempotent": False,
                    "status": "ACTIVE",
                },
                "finalize_adaptive_comprehensive_submission": {
                    "session_id": "session-1",
                    "status": "COMPLETED",
                    "completion_state": completion_state(),
                },
                "persist_adaptive_comprehensive_answers_batch": RuntimeError(
                    "PGRST202 Could not find the function in the schema cache"
                ),
            }
        )
        persisted_order: list[str] = []

        def persist(**kwargs):
            persisted_order.append(kwargs["practice_session_item_id"])
            return {
                "submission_id": kwargs["client_submission_id"],
                "is_correct": kwargs["is_correct"],
                "persisted": True,
            }

        with (
            patch.object(adaptive_practice, "_load_session", return_value=session(count=3)),
            patch.object(adaptive_practice, "_load_session_items", return_value=fixed_items),
            patch.object(adaptive_practice, "persist_answer_submission", side_effect=persist) as persist_mock,
            patch.object(adaptive_practice, "warm_submission_questions") as warm_cache,
            patch.object(answer_service, "submit_answer", side_effect=AssertionError("public grading must not run")) as public_grade,
            patch.object(adaptive_practice, "reconcile_pending_adaptive_updates", return_value=3) as reconcile,
        ):
            result = adaptive_practice.submit_comprehensive_session(
                client,
                user_id="user-1",
                session_id="session-1",
                payload=payload,
            )

        begin_name, begin_payload = client.calls[0]
        self.assertEqual(begin_name, "begin_adaptive_comprehensive_submission")
        self.assertEqual(
            begin_payload["p_answers"],
            [
                {
                    "position": 1,
                    "practice_session_item_id": "item-1",
                    "selected_answer": "A",
                    "used_time": 10,
                    "client_submission_id": "answer-1",
                },
                {
                    "position": 2,
                    "practice_session_item_id": "item-2",
                    "selected_answer": "A",
                    "used_time": 20,
                    "client_submission_id": "answer-2",
                },
                {
                    "position": 3,
                    "practice_session_item_id": "item-3",
                    "selected_answer": "A",
                    "used_time": 30,
                    "client_submission_id": "answer-3",
                },
            ],
        )
        self.assertEqual(persisted_order, ["item-1", "item-2", "item-3"])
        for call in persist_mock.call_args_list:
            self.assertEqual(call.kwargs["comprehensive_session_id"], "session-1")
            self.assertEqual(call.kwargs["comprehensive_client_submission_id"], "round-submit-1")
            self.assertEqual(
                call.kwargs["comprehensive_manifest_hash"],
                begin_payload["p_manifest_hash"],
            )
        public_grade.assert_not_called()
        warm_cache.assert_not_called()
        self.assertEqual(
            reconcile.call_args.kwargs,
            {
                "user_id": "user-1",
                "exam_code": "Z001",
                "subject": "逻辑推理",
                "prefetched_session_items": fixed_items,
            },
        )
        self.assertEqual([entry["position"] for entry in result["results"]], [1, 2, 3])
        self.assertEqual(result["summary"]["correct_count"], 2)
        self.assertEqual(result["summary"]["wrong_count"], 1)
        self.assertEqual(result["summary"]["used_time"], 60)

    def test_submit_uses_one_atomic_batch_persistence_rpc_when_deployed(self):
        fixed_items = [item(1), item(2)]
        payload = submission_payload([2, 1], skipped={2})
        client = RpcClient(
            {
                "begin_adaptive_comprehensive_submission": {
                    "session_id": "session-1",
                    "phase": "LOCKED",
                    "idempotent": False,
                    "status": "ACTIVE",
                },
                "persist_adaptive_comprehensive_answers_batch": {
                    "session_id": "session-1",
                    "phase": "LOCKED",
                    "status": "ACTIVE",
                    "item_count": 2,
                    "items": [
                        {
                            "position": 1,
                            "practice_session_item_id": "item-1",
                            "status": "ANSWERED",
                        },
                        {
                            "position": 2,
                            "practice_session_item_id": "item-2",
                            "status": "SKIPPED",
                        },
                    ],
                    "idempotent": False,
                },
                "finalize_adaptive_comprehensive_submission": {
                    "session_id": "session-1",
                    "status": "COMPLETED",
                    "completion_state": completion_state(),
                },
            }
        )

        with (
            patch.object(adaptive_practice, "_load_session", return_value=session(count=2)),
            patch.object(adaptive_practice, "_load_session_items", return_value=fixed_items),
            patch.object(adaptive_practice, "persist_answer_submission") as persist_one,
            patch.object(adaptive_practice, "_record_comprehensive_skip") as skip_one,
            patch.object(
                adaptive_practice,
                "reconcile_pending_adaptive_updates",
                return_value=1,
            ) as reconcile,
        ):
            result = adaptive_practice.submit_comprehensive_session(
                client,
                user_id="user-1",
                session_id="session-1",
                payload=payload,
            )

        persist_one.assert_not_called()
        skip_one.assert_not_called()
        self.assertEqual(
            [name for name, _payload in client.calls],
            [
                "begin_adaptive_comprehensive_submission",
                "persist_adaptive_comprehensive_answers_batch",
                "finalize_adaptive_comprehensive_submission",
            ],
        )
        self.assertIs(reconcile.call_args.kwargs["prefetched_session_items"], fixed_items)
        self.assertEqual(result["summary"]["answered_count"], 1)
        self.assertEqual(result["summary"]["skipped_count"], 1)

    def test_batch_persistence_real_failure_never_downgrades_to_item_writes(self):
        payload = submission_payload([1])
        client = RpcClient(
            {
                "begin_adaptive_comprehensive_submission": {
                    "phase": "LOCKED",
                    "idempotent": False,
                },
                "persist_adaptive_comprehensive_answers_batch": RuntimeError(
                    "database transaction aborted"
                ),
            }
        )
        with (
            patch.object(adaptive_practice, "_load_session", return_value=session(count=1)),
            patch.object(adaptive_practice, "_load_session_items", return_value=[item(1)]),
            patch.object(adaptive_practice, "persist_answer_submission") as persist_one,
        ):
            with self.assertRaisesRegex(RuntimeError, "transaction aborted"):
                adaptive_practice.submit_comprehensive_session(
                    client,
                    user_id="user-1",
                    session_id="session-1",
                    payload=payload,
                )
        persist_one.assert_not_called()

    def test_batch_persistence_table_or_dependency_drift_never_uses_legacy_fallback(self):
        for error_message in (
            "PGRST205 Could not find the table in the schema cache",
            'relation "public.practice_session_items" does not exist',
            "function public.record_answer_submission(uuid) does not exist",
        ):
            with self.subTest(error_message=error_message):
                payload = submission_payload([1])
                client = RpcClient(
                    {
                        "begin_adaptive_comprehensive_submission": {
                            "phase": "LOCKED",
                            "idempotent": False,
                        },
                        "persist_adaptive_comprehensive_answers_batch": RuntimeError(
                            error_message
                        ),
                    }
                )
                with (
                    patch.object(
                        adaptive_practice,
                        "_load_session",
                        return_value=session(count=1),
                    ),
                    patch.object(
                        adaptive_practice,
                        "_load_session_items",
                        return_value=[item(1)],
                    ),
                    patch.object(
                        adaptive_practice,
                        "persist_answer_submission",
                    ) as persist_one,
                ):
                    with self.assertRaisesRegex(RuntimeError, re.escape(error_message)):
                        adaptive_practice.submit_comprehensive_session(
                            client,
                            user_id="user-1",
                            session_id="session-1",
                            payload=payload,
                        )
                persist_one.assert_not_called()

    def test_batch_persistence_malformed_count_returns_stable_503(self):
        client = RpcClient(
            {
                "persist_adaptive_comprehensive_answers_batch": {
                    "phase": "LOCKED",
                    "status": "ACTIVE",
                    "item_count": "one",
                    "items": [{}],
                }
            }
        )
        with self.assertRaises(HTTPException) as raised:
            adaptive_practice._persist_comprehensive_answers_batch(
                client,
                user_id="user-1",
                session_id="session-1",
                client_submission_id="round-submit-1",
                manifest_hash="a" * 64,
                expected_count=1,
            )
        self.assertEqual(raised.exception.status_code, 503)

    def test_malformed_batch_snapshot_falls_back_to_authoritative_reconciliation_reads(self):
        fixed_items = [item(1), item(2)]
        subject_row = {
            "user_id": "user-1",
            "stats_exam_code": "Z001",
            "subject": "逻辑推理",
            "theta": 0.1,
            "pending_conflict_count": 0,
        }

        def answered(position: int, *, adaptive_updated: object = False) -> dict:
            return {
                "position": position,
                "practice_session_item_id": f"item-{position}",
                "question_id": f"q-{position}",
                "selected_answer": "A",
                "status": "ANSWERED",
                "answer_id": f"answer-{position}",
                "stats_exam_code": "Z001",
                "is_correct": True,
                "is_first_attempt": True,
                "used_time": 20,
                "answer_created_at": f"2026-09-04T00:00:0{position}+00:00",
                "adaptive_updated": adaptive_updated,
            }

        valid_prefix = {
            "external_pending_count": 0,
            "subject_state": subject_row,
            "topic_states": [],
            "pending_conflict": None,
        }
        malformed_results = (
            {**valid_prefix, "external_pending_count": "0", "items": [answered(1), answered(2)]},
            {**valid_prefix, "items": [answered(1, adaptive_updated="false"), answered(2)]},
            {**valid_prefix, "items": [answered(1), answered(1)]},
            {**valid_prefix, "items": [{**answered(1), "position": "1"}, answered(2)]},
        )
        for batch_result in malformed_results:
            with self.subTest(batch_result=batch_result):
                self.assertIsNone(
                    adaptive_practice._comprehensive_batch_reconciliation_context(
                        batch_result,
                        user_id="user-1",
                        exam_code="Z001",
                        subject="逻辑推理",
                        session_id="session-1",
                        session_items=fixed_items,
                    )
                )

    def test_exact_manifest_retry_resumes_after_partial_answer_persistence(self):
        fixed_items = [item(1), item(2)]
        payload = submission_payload([2, 1])
        client = RpcClient(
            {
                "begin_adaptive_comprehensive_submission": [
                    {"phase": "LOCKED", "idempotent": False},
                    {"phase": "LOCKED", "idempotent": True},
                ],
                "finalize_adaptive_comprehensive_submission": {
                    "status": "COMPLETED",
                    "completion_state": completion_state(),
                },
                "persist_adaptive_comprehensive_answers_batch": [
                    RuntimeError("PGRST202 Could not find the function in the schema cache"),
                    RuntimeError("PGRST202 Could not find the function in the schema cache"),
                ],
            }
        )
        attempts: Counter[str] = Counter()

        def persist(**kwargs):
            item_id = kwargs["practice_session_item_id"]
            attempts[item_id] += 1
            if item_id == "item-2" and attempts[item_id] == 1:
                raise HTTPException(status_code=503, detail="response lost")
            return {
                "submission_id": kwargs["client_submission_id"],
                "is_correct": kwargs["is_correct"],
                "persisted": True,
                "idempotent": attempts[item_id] > 1,
            }

        with (
            patch.object(adaptive_practice, "_load_session", return_value=session(count=2)),
            patch.object(adaptive_practice, "_load_session_items", return_value=fixed_items),
            patch.object(adaptive_practice, "persist_answer_submission", side_effect=persist),
            patch.object(adaptive_practice, "reconcile_pending_adaptive_updates", return_value=2) as reconcile,
        ):
            with self.assertRaises(HTTPException):
                adaptive_practice.submit_comprehensive_session(
                    client,
                    user_id="user-1",
                    session_id="session-1",
                    payload=payload,
                )
            result = adaptive_practice.submit_comprehensive_session(
                client,
                user_id="user-1",
                session_id="session-1",
                payload=payload,
            )

        begin_calls = [call for call in client.calls if call[0] == "begin_adaptive_comprehensive_submission"]
        self.assertEqual(len(begin_calls), 2)
        self.assertEqual(begin_calls[0][1]["p_answers"], begin_calls[1][1]["p_answers"])
        self.assertEqual(begin_calls[0][1]["p_manifest_hash"], begin_calls[1][1]["p_manifest_hash"])
        self.assertEqual(attempts, Counter({"item-1": 2, "item-2": 2}))
        reconcile.assert_called_once()
        self.assertEqual(result["status"], "COMPLETED")

    def test_exact_manifest_retry_resumes_after_skip_response_loss(self):
        payload = submission_payload([1], skipped={1})
        client = RpcClient(
            {
                "begin_adaptive_comprehensive_submission": [
                    {"phase": "LOCKED", "idempotent": False},
                    {"phase": "LOCKED", "idempotent": True},
                ],
                "persist_adaptive_comprehensive_answers_batch": [
                    RuntimeError("PGRST202 Could not find the function in the schema cache"),
                    RuntimeError("PGRST202 Could not find the function in the schema cache"),
                ],
            }
        )
        with (
            patch.object(adaptive_practice, "_load_session", return_value=session(count=1)),
            patch.object(adaptive_practice, "_load_session_items", return_value=[item(1)]),
            patch.object(adaptive_practice, "persist_answer_submission") as persist,
            patch.object(
                adaptive_practice,
                "_record_comprehensive_skip",
                side_effect=[HTTPException(status_code=503, detail="response lost"), {"idempotent": True}],
            ) as record_skip,
            patch.object(adaptive_practice, "reconcile_pending_adaptive_updates", return_value=0),
            patch.object(
                adaptive_practice,
                "_finalize_comprehensive_submission",
                return_value={"status": "COMPLETED", "completion_state": completion_state()},
            ),
        ):
            with self.assertRaises(HTTPException):
                adaptive_practice.submit_comprehensive_session(
                    client,
                    user_id="user-1",
                    session_id="session-1",
                    payload=payload,
                )
            result = adaptive_practice.submit_comprehensive_session(
                client,
                user_id="user-1",
                session_id="session-1",
                payload=payload,
            )

        persist.assert_not_called()
        self.assertEqual(record_skip.call_count, 2)
        begin_calls = [call for call in client.calls if call[0] == "begin_adaptive_comprehensive_submission"]
        self.assertEqual(begin_calls[0][1]["p_manifest_hash"], begin_calls[1][1]["p_manifest_hash"])
        self.assertEqual(result["summary"]["skipped_count"], 1)
        self.assertEqual(result["summary"]["answered_count"], 0)

    def test_completed_fast_path_recovers_after_finalize_response_loss(self):
        payload = submission_payload([1])
        completed_state = completion_state()
        client = RpcClient(
            {
                "begin_adaptive_comprehensive_submission": [
                    {"phase": "LOCKED", "idempotent": False},
                    {
                        "phase": "COMPLETED",
                        "idempotent": True,
                        "status": "COMPLETED",
                        "completion_state": completed_state,
                    },
                ],
                "persist_adaptive_comprehensive_answers_batch": RuntimeError(
                    "PGRST202 Could not find the function in the schema cache"
                ),
            }
        )
        with (
            patch.object(adaptive_practice, "_load_session", return_value=session(count=1)),
            patch.object(adaptive_practice, "_load_session_items", return_value=[item(1)]),
            patch.object(
                adaptive_practice,
                "persist_answer_submission",
                return_value={"submission_id": "answer-1", "persisted": True},
            ) as persist,
            patch.object(adaptive_practice, "reconcile_pending_adaptive_updates", return_value=1) as reconcile,
            patch.object(
                adaptive_practice,
                "_finalize_comprehensive_submission",
                side_effect=RuntimeError("connection dropped after committed finalize"),
            ) as finalize,
        ):
            with self.assertRaises(RuntimeError):
                adaptive_practice.submit_comprehensive_session(
                    client,
                    user_id="user-1",
                    session_id="session-1",
                    payload=payload,
                )
            recovered = adaptive_practice.submit_comprehensive_session(
                client,
                user_id="user-1",
                session_id="session-1",
                payload=payload,
            )

        persist.assert_called_once()
        reconcile.assert_called_once()
        finalize.assert_called_once()
        self.assertTrue(recovered["idempotent"])
        self.assertEqual(recovered["state"], completed_state)
        self.assertEqual(recovered["results"][0]["correct_answer"], "A")

    def test_locked_manifest_rejects_abandon_and_cancel_completion(self):
        locked = {
            "phase": "LOCKED",
            "client_submission_id": "round-submit-1",
            "manifest_hash": "hash-1",
        }
        for reason in ("abandoned", "cancelled"):
            with self.subTest(reason=reason):
                with (
                    patch.object(
                        adaptive_practice,
                        "_load_session",
                        return_value=session(count=1, submission=locked),
                    ),
                    patch.object(adaptive_practice, "reconcile_pending_adaptive_updates") as reconcile,
                ):
                    with self.assertRaises(HTTPException) as raised:
                        adaptive_practice.complete_session(
                            object(),
                            user_id="user-1",
                            session_id="session-1",
                            reason=reason,
                        )
                self.assertEqual(raised.exception.status_code, 409)
                self.assertEqual(
                    raised.exception.detail["code"],
                    "ADAPTIVE_COMPREHENSIVE_SUBMISSION_IN_PROGRESS",
                )
                reconcile.assert_not_called()

    def test_completed_manifest_returns_original_completion_snapshot(self):
        state = completion_state()
        completed = {
            "phase": "COMPLETED",
            "client_submission_id": "round-submit-1",
            "manifest_hash": "hash-1",
            "completion_state": state,
        }
        with (
            patch.object(
                adaptive_practice,
                "_load_session",
                return_value=session(count=1, status="COMPLETED", submission=completed),
            ),
            patch.object(adaptive_practice, "reconcile_pending_adaptive_updates") as reconcile,
        ):
            result = adaptive_practice.complete_session(
                object(),
                user_id="user-1",
                session_id="session-1",
                reason="cancelled",
            )

        reconcile.assert_not_called()
        self.assertTrue(result["idempotent"])
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["state"], state)

    def test_submit_rejects_a_payload_that_does_not_cover_every_position(self):
        payload = submission_payload([1])
        with (
            patch.object(adaptive_practice, "_load_session", return_value=session(count=2)),
            patch.object(adaptive_practice, "_load_session_items", return_value=[item(1), item(2)]),
        ):
            with self.assertRaises(HTTPException) as raised:
                adaptive_practice.submit_comprehensive_session(
                    object(),
                    user_id="user-1",
                    session_id="session-1",
                    payload=payload,
                )
        self.assertEqual(raised.exception.status_code, 422)

    def test_comprehensive_reconciliation_reuses_one_scoped_state_snapshot(self):
        fixed_items = [item(position) for position in (1, 2, 3)]
        pending = []
        for position, fixed_item in enumerate(fixed_items, start=1):
            pending.append(
                {
                    "id": fixed_item["id"],
                    "session_id": "session-1",
                    "question_id": fixed_item["question_id"],
                    "position": position,
                    "answer_id": f"answer-{position}",
                    "answered_at": f"2026-09-04T00:00:0{position}+00:00",
                    "answer": {
                        "id": f"answer-{position}",
                        "stats_exam_code": "Z001",
                        "is_correct": True,
                        "is_first_attempt": True,
                        "used_time": 20,
                        "created_at": f"2026-09-04T00:00:0{position}+00:00",
                    },
                    "questions": fixed_item["questions"],
                }
            )

        initial_state = AbilityState(theta=0.1, state_version=4)
        initial_topics = {("模块一", "考点一"): AbilityState(theta=0.1, state_version=2)}
        applied_versions: list[int] = []

        def apply_with_context(_supabase, **kwargs):
            before = kwargs["_prefetched_subject_state"]
            applied_versions.append(before.state_version)
            after = AbilityState(
                theta=before.theta + 0.01,
                uncertainty=before.uncertainty,
                effective_evidence=before.effective_evidence + 0.9,
                reliable_first_attempt_count=before.reliable_first_attempt_count + 1,
                diagnostic_status=before.diagnostic_status,
                pending_conflict_count=before.pending_conflict_count,
                state_version=before.state_version + 1,
            )
            return {
                "adaptive_updated": True,
                "_planning_context": {
                    "cache_valid": True,
                    "subject_after": after,
                    "topic_state_map_after": kwargs["_prefetched_topic_state_map"],
                    "pending_conflict_after": None,
                },
            }

        with (
            patch.object(
                adaptive_practice,
                "_load_pending_adaptive_update_items",
                return_value=pending,
            ),
            patch.object(
                adaptive_practice,
                "load_subject_state",
                return_value=initial_state,
            ) as load_subject,
            patch.object(
                adaptive_practice,
                "load_topic_state_map",
                return_value=initial_topics,
            ) as load_topics,
            patch.object(
                adaptive_practice,
                "_pending_conflict",
                side_effect=AssertionError("zero pending conflicts must not be queried"),
            ),
            patch.object(
                adaptive_practice,
                "apply_adaptive_answer_update",
                side_effect=apply_with_context,
            ) as apply_update,
        ):
            applied = adaptive_practice.reconcile_pending_adaptive_updates(
                object(),
                user_id="user-1",
                exam_code="Z001",
                subject="逻辑推理",
                prefetched_session_items=fixed_items,
            )

        self.assertEqual(applied, 3)
        self.assertEqual(applied_versions, [4, 5, 6])
        self.assertEqual(load_subject.call_count, 1)
        self.assertEqual(load_topics.call_count, 1)
        self.assertEqual(apply_update.call_count, 3)
        self.assertTrue(
            all(
                call.kwargs["_prefetched_session_items"] is not None
                for call in apply_update.call_args_list
            )
        )

    def test_prefetched_apply_avoids_reloading_item_sheet_and_scope_state(self):
        fixed_item = item(1, answer_id="answer-1")
        fixed_item["answer"] = {
            "id": "answer-1",
            "stats_exam_code": "Z001",
            "is_correct": True,
            "is_first_attempt": True,
            "used_time": 20,
            "created_at": "2026-09-04T00:00:01+00:00",
        }
        fixed_item["answered_at"] = "2026-09-04T00:00:01+00:00"
        subject_state = AbilityState(theta=0.1, state_version=4)
        topic_state = AbilityState(theta=0.1, state_version=2)
        client = RpcClient(
            {
                "apply_adaptive_model_update": {
                    "adaptive_updated": True,
                    "idempotent": False,
                    "diagnostic_status": "PROBING",
                    "theta": 0.2,
                    "uncertainty": 1.5,
                    "effective_evidence": 0.9,
                    "pending_conflicts": 0,
                    "conflict_action": "none",
                    "conflict_id": None,
                }
            }
        )

        with (
            patch.object(
                adaptive_practice,
                "_query_one",
                side_effect=AssertionError("prefetched item must avoid item read"),
            ),
            patch.object(
                adaptive_practice,
                "_load_session_items",
                side_effect=AssertionError("prefetched sheet must avoid sheet read"),
            ),
            patch.object(
                adaptive_practice,
                "load_subject_state",
                side_effect=AssertionError("prefetched subject must avoid state read"),
            ),
            patch.object(
                adaptive_practice,
                "load_topic_state_map",
                side_effect=AssertionError("prefetched topics must avoid state read"),
            ),
            patch.object(adaptive_practice, "_detect_unhandled_inversion", return_value=None),
        ):
            result = adaptive_practice.apply_adaptive_answer_update(
                client,
                user_id="user-1",
                question=fixed_item["questions"],
                persisted={
                    "submission_id": "answer-1",
                    "stats_exam_code": "Z001",
                    "is_first_attempt": True,
                    "is_correct": True,
                    "created_at": "2026-09-04T00:00:01+00:00",
                },
                used_time=20,
                practice_session_item_id="item-1",
                _prefetched_item=fixed_item,
                _prefetched_session_items=[fixed_item],
                _prefetched_subject_state=subject_state,
                _prefetched_topic_state_map={("模块一", "考点一"): topic_state},
                _prefetched_pending_conflict=None,
                _include_planning_context=True,
            )

        self.assertTrue(result["adaptive_updated"])
        self.assertTrue(result["_planning_context"]["cache_valid"])
        self.assertEqual(result["_planning_context"]["subject_after"].state_version, 5)
        self.assertEqual([name for name, _payload in client.calls], ["apply_adaptive_model_update"])

    def test_thirty_item_normal_path_has_at_most_thirty_five_remote_calls(self):
        fixed_items = []
        pending_items = []
        for position in range(1, 31):
            fixed_item = item(position, answer_id=f"answer-{position}")
            answer = {
                "id": f"answer-{position}",
                "stats_exam_code": "Z001",
                "is_correct": True,
                "is_first_attempt": True,
                "used_time": 20,
                "created_at": f"2026-09-04T00:00:{position:02d}+00:00",
            }
            fixed_item["answer"] = answer
            fixed_item["answered_at"] = answer["created_at"]
            fixed_items.append(fixed_item)
            pending_items.append(
                {
                    "id": fixed_item["id"],
                    "session_id": "session-1",
                    "question_id": fixed_item["question_id"],
                    "position": position,
                    "answer_id": answer["id"],
                    "answered_at": answer["created_at"],
                    "answer": answer,
                    "questions": fixed_item["questions"],
                }
            )

        client = RpcClient(
            {
                "apply_adaptive_model_update": [
                    {
                        "adaptive_updated": True,
                        "idempotent": False,
                        "pending_conflicts": 0,
                        "conflict_action": "none",
                        "conflict_id": None,
                    }
                    for _ in range(30)
                ]
            }
        )
        with (
            patch.object(
                adaptive_practice,
                "_load_pending_adaptive_update_items",
                side_effect=AssertionError("batch snapshot must avoid pending reread"),
            ),
            patch.object(
                adaptive_practice,
                "load_subject_state",
                side_effect=AssertionError("batch snapshot must avoid subject reread"),
            ),
            patch.object(
                adaptive_practice,
                "load_topic_state_map",
                side_effect=AssertionError("batch snapshot must avoid topic reread"),
            ),
            patch.object(adaptive_practice, "_detect_unhandled_inversion", return_value=None),
        ):
            applied = adaptive_practice.reconcile_pending_adaptive_updates(
                client,
                user_id="user-1",
                exam_code="Z001",
                subject="逻辑推理",
                prefetched_session_items=fixed_items,
                prefetched_pending_items=pending_items,
                prefetched_subject_state=AbilityState(),
                prefetched_topic_state_map={
                    ("模块一", "考点一"): AbilityState()
                },
                prefetched_pending_conflict=None,
            )

        self.assertEqual(applied, 30)
        self.assertEqual(len(client.calls), 30)
        self.assertTrue(
            all(name == "apply_adaptive_model_update" for name, _payload in client.calls)
        )
        # Two initial reads + begin + atomic persistence + 30 ordered model
        # applies + finalize. History size cannot add another remote read.
        estimated_endpoint_calls = 2 + 1 + 1 + len(client.calls) + 1
        self.assertLessEqual(estimated_endpoint_calls, 35)


if __name__ == "__main__":
    unittest.main()
