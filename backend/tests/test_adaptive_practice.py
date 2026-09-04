from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import ANY, patch

from fastapi import HTTPException

from app.routes import adaptive_practice as adaptive_routes
from app.routes import answers as answer_routes
from app.routes import questions as question_routes
from app.schemas.adaptive_practice import CreateAdaptivePracticeSessionRequest
from app.schemas.answers import MarkUnfamiliarRequest, SubmitAnswerRequest
from app.services import adaptive_practice, answers as answer_service
from app.services.adaptive_engine import (
    AbilityState,
    DiagnosticStatus,
    Observation,
    TargetPlan,
    TargetZone,
)


class _Response:
    def __init__(self, data):
        self.data = data


class _RpcClient:
    def __init__(self, *, response=None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.rpc_name = None
        self.rpc_payload = None
        self.execute_count = 0

    def rpc(self, name, payload):
        self.rpc_name = name
        self.rpc_payload = payload
        return self

    def execute(self):
        self.execute_count += 1
        if self.error:
            raise self.error
        return _Response(self.response)


class _SequentialRpcClient:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def rpc(self, name, payload):
        self.calls.append((name, payload))
        return self

    def table(self, _name):
        return self

    def __getattr__(self, _name):
        return lambda *_args, **_kwargs: self

    def execute(self):
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return _Response(outcome)


class _InsertQuery:
    def __init__(self):
        self.payload = None

    def insert(self, payload):
        self.payload = dict(payload)
        return self

    def execute(self):
        return _Response([{**self.payload, "id": "inserted-item"}])


class _InsertClient:
    def __init__(self, *, errors=None, responses=None):
        self.query = _InsertQuery()
        self.rpc_name = None
        self.rpc_payload = None
        self.errors = list(errors or [])
        self.responses = list(responses or [])
        self.execute_count = 0

    def table(self, table_name):
        if table_name != "practice_session_items":
            raise AssertionError(f"unexpected table: {table_name}")
        return self.query

    def rpc(self, name, payload):
        if name != "claim_next_adaptive_practice_item":
            raise AssertionError(f"unexpected rpc: {name}")
        self.rpc_name = name
        self.rpc_payload = dict(payload)
        self.query.payload = {
            **dict(payload["p_item"]),
            "id": "inserted-item",
            "session_id": payload["p_session_id"],
            "question_id": payload["p_question_id"],
            "position": payload["p_position"],
            "item_status": "SELECTED",
        }
        return self

    def execute(self):
        self.execute_count += 1
        if self.errors:
            error = self.errors.pop(0)
            if error is not None:
                raise error
        if self.responses:
            response = self.responses.pop(0)
            if response is not None:
                return _Response(response)
        return _Response(dict(self.query.payload))


class _BootstrapQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.filters = {}
        self.insert_payload = None

    def select(self, _fields):
        return self

    def eq(self, field, value):
        self.filters[field] = value
        return self

    def in_(self, field, values):
        self.filters[field] = tuple(values)
        return self

    def or_(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def insert(self, payload):
        self.insert_payload = dict(payload)
        return self

    def execute(self):
        if self.insert_payload is not None:
            self.client.inserts.setdefault(self.table_name, []).append(self.insert_payload)
            if self.table_name == "user_subject_state":
                key = (
                    self.insert_payload["stats_exam_code"],
                    self.insert_payload["subject"],
                )
                self.client.subject_rows[key] = self.insert_payload
            return _Response([self.insert_payload])
        if self.table_name == "user_answers":
            self.client.history_filters.append(dict(self.filters))
            key = (self.filters.get("stats_exam_code"), self.filters.get("questions.subject"))
            return _Response(list(self.client.histories.get(key, [])))
        raise AssertionError(f"unexpected read table: {self.table_name}")


class _BootstrapClient:
    def __init__(self, histories):
        self.histories = histories
        self.history_filters = []
        self.inserts = {}
        self.subject_rows = {}

    def table(self, table_name):
        return _BootstrapQuery(self, table_name)


class _RecordingQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.operations = []

    def select(self, fields, **kwargs):
        self.operations.append(("select", fields, kwargs))
        return self

    def eq(self, field, value):
        self.operations.append(("eq", field, value))
        return self

    def in_(self, field, values):
        self.operations.append(("in", field, tuple(values)))
        return self

    def gte(self, field, value):
        self.operations.append(("gte", field, value))
        return self

    def or_(self, *args, **kwargs):
        self.operations.append(("or", args, kwargs))
        return self

    def order(self, field, **kwargs):
        self.operations.append(("order", field, kwargs))
        return self

    def range(self, start, end):
        self.operations.append(("range", start, end))
        return self

    def limit(self, value):
        self.operations.append(("limit", value))
        return self

    def execute(self):
        self.client.queries.append(self)
        rows = list(self.client.rows.get(self.table_name, []))
        ranges = [operation for operation in self.operations if operation[0] == "range"]
        if ranges:
            _, start, end = ranges[-1]
            rows = rows[start : end + 1]
        return _Response(rows)


class _RecordingClient:
    def __init__(self, rows=None):
        self.rows = rows or {}
        self.queries = []

    def table(self, table_name):
        return _RecordingQuery(self, table_name)


def _question(question_id: str, difficulty: int, module: str = "模块一", submodule: str = "考点一") -> dict:
    return {
        "id": question_id,
        "exam_code": "Z001",
        "subject": "逻辑推理",
        "module": module,
        "submodule": submodule,
        "question_type": "single_choice",
        "stem": f"题目 {question_id}",
        "option_a": "A",
        "option_b": "B",
        "option_c": "C",
        "option_d": "D",
        "answer": "A",
        "explanation": f"解析 {question_id}",
        "difficulty": difficulty,
        "source_type": "official",
        "source_year": 2026,
        "passage_id": None,
        "skill_tags": [],
        "solution_type": None,
        "estimated_time_sec": 60,
        "status": "active",
    }


class AdaptiveRouteAndAnswerTests(unittest.TestCase):
    def test_new_session_honors_disabled_rollout_flag(self):
        payload = CreateAdaptivePracticeSessionRequest(
            exam_code="Z001",
            subject="逻辑推理",
            practice_mode="special",
            scopes=[{"module": "模块一", "submodule": "考点一"}],
            client_session_id="first-create-id",
        )
        with (
            patch.object(adaptive_routes, "get_settings", return_value=SimpleNamespace(adaptive_practice_enabled=False)),
            patch.object(adaptive_routes, "create_adaptive_session") as create,
        ):
            with self.assertRaises(HTTPException) as raised:
                adaptive_routes.create_session(payload=payload, user_id="user-1")
        self.assertEqual(raised.exception.status_code, 503)
        create.assert_not_called()

    def test_disabled_rollout_still_routes_idempotent_create_retry(self):
        payload = CreateAdaptivePracticeSessionRequest(
            exam_code="Z001",
            subject="逻辑推理",
            practice_mode="special",
            scopes=[{"module": "模块一", "submodule": "考点一"}],
            client_session_id="client-session-1",
            resume_existing_session=True,
        )
        with (
            patch.object(
                adaptive_routes,
                "get_settings",
                return_value=SimpleNamespace(adaptive_practice_enabled=False),
            ),
            patch.object(adaptive_routes, "get_supabase_admin", return_value=object()),
            patch.object(
                adaptive_routes,
                "create_adaptive_session",
                side_effect=HTTPException(status_code=503, detail="not found"),
            ) as create,
        ):
            with self.assertRaises(HTTPException):
                adaptive_routes.create_session(payload=payload, user_id="user-1")
        self.assertFalse(create.call_args.kwargs["allow_new_session"])

    def test_closed_rollout_does_not_create_unknown_idempotency_key(self):
        payload = CreateAdaptivePracticeSessionRequest(
            exam_code="Z001",
            subject="逻辑推理",
            practice_mode="special",
            scopes=[{"module": "模块一", "submodule": "考点一"}],
            client_session_id="unknown-client-session",
            resume_existing_session=True,
        )
        client = _RecordingClient({"practice_sessions": []})
        with (
            patch.object(adaptive_practice, "reconcile_pending_adaptive_updates") as reconcile,
            patch.object(adaptive_practice, "bootstrap_subject_state_if_needed") as bootstrap,
        ):
            with self.assertRaises(HTTPException) as raised:
                adaptive_practice.create_adaptive_session(
                    client,
                    user_id="user-1",
                    payload=payload,
                    allow_new_session=False,
                )
        self.assertEqual(raised.exception.status_code, 503)
        reconcile.assert_not_called()
        bootstrap.assert_not_called()

    def test_closed_rollout_recovers_existing_idempotent_session(self):
        payload = CreateAdaptivePracticeSessionRequest(
            exam_code="Z001",
            subject="逻辑推理",
            practice_mode="special",
            scopes=[{"module": "模块一", "submodule": "考点一"}],
            question_count=10,
            client_session_id="known-client-session",
            resume_existing_session=True,
        )
        existing = {
            "id": "existing-session",
            "user_id": "user-1",
            "client_session_id": "known-client-session",
            "stats_exam_code": "Z001",
            "subject": "逻辑推理",
            "mode": "special",
            "scope_filter": [{"module": "模块一", "submodule": "考点一"}],
            "requested_question_count": 10,
            "user_preference": "standard",
            "status": "ACTIVE",
            "diagnostic_status": "STABLE",
            "strategy_config": {"accepted_challenge": False},
            "state_snapshot": {
                "diagnostic_status": "STABLE",
                "reliable_first_attempt_count": 8,
            },
        }
        client = _RecordingClient({"practice_sessions": [existing]})
        state = AbilityState(
            theta=0.2,
            uncertainty=0.5,
            effective_evidence=8.0,
            reliable_first_attempt_count=8,
            diagnostic_status=DiagnosticStatus.STABLE,
        )
        with (
            patch.object(
                adaptive_practice,
                "reconcile_pending_adaptive_updates",
                return_value=0,
            ),
            patch.object(
                adaptive_practice,
                "bootstrap_subject_state_if_needed",
                return_value=(state, {}),
            ),
            patch.object(
                adaptive_practice,
                "_select_and_insert_next",
                return_value=None,
            ) as select_next,
        ):
            result = adaptive_practice.create_adaptive_session(
                client,
                user_id="user-1",
                payload=payload,
                allow_new_session=False,
            )

        self.assertEqual(result["session"]["id"], "existing-session")
        select_next.assert_called_once()

    def test_closed_rollout_does_not_gate_existing_session_endpoints(self):
        operations = (
            (
                "get_next_adaptive_item",
                lambda: adaptive_routes.next_item("session-1", user_id="user-1"),
            ),
            (
                "record_item_event",
                lambda: adaptive_routes.item_event(
                    "session-1",
                    "item-1",
                    adaptive_routes.AdaptivePracticeItemEventRequest(
                        event_type="presented"
                    ),
                    user_id="user-1",
                ),
            ),
            (
                "complete_session",
                lambda: adaptive_routes.finish_session(
                    "session-1",
                    adaptive_routes.CompleteAdaptivePracticeSessionRequest(),
                    user_id="user-1",
                ),
            ),
            (
                "submit_comprehensive_session",
                lambda: adaptive_routes.submit_comprehensive(
                    "session-1",
                    adaptive_routes.SubmitAdaptiveComprehensiveSessionRequest(
                        client_submission_id="batch-1",
                        answers=[
                            {
                                "practice_session_item_id": "item-1",
                                "selected_answer": "A",
                                "used_time": 10,
                                "client_submission_id": "answer-1",
                            }
                        ],
                    ),
                    user_id="user-1",
                ),
            ),
        )
        for service_name, invoke in operations:
            with self.subTest(service_name=service_name):
                with (
                    patch.object(
                        adaptive_routes,
                        "get_settings",
                        side_effect=AssertionError(
                            "existing-session endpoint read rollout"
                        ),
                    ),
                    patch.object(
                        adaptive_routes,
                        "get_supabase_admin",
                        return_value=object(),
                    ),
                    patch.object(
                        adaptive_routes,
                        service_name,
                        side_effect=HTTPException(
                            status_code=418,
                            detail="reached service",
                        ),
                    ),
                ):
                    with self.assertRaises(HTTPException) as raised:
                        invoke()
                    self.assertEqual(raised.exception.status_code, 418)

    def test_answer_rpc_atomically_receives_session_item_id(self):
        client = _RpcClient(response={
            "submission_id": "answer-1",
            "stats_exam_code": "Z001",
            "persisted": True,
            "idempotent": False,
        })
        with patch.object(answer_service, "get_supabase_admin", return_value=client):
            answer_service.persist_answer_submission(
                user_id="user-1",
                question={
                    "id": "question-1",
                    "exam_code": "Z001",
                    "subject": "逻辑推理",
                    "module": "模块一",
                    "submodule": "考点一",
                },
                selected_answer="A",
                used_time=12,
                is_correct=True,
                client_submission_id="client-answer-1",
                practice_session_item_id="session-item-1",
            )
        self.assertEqual(client.rpc_payload["p_practice_session_item_id"], "session-item-1")

    def test_answer_scope_mismatch_maps_to_conflict(self):
        client = _RpcClient(error=RuntimeError("answer_submission_scope_mismatch"))
        with patch.object(answer_service, "get_supabase_admin", return_value=client):
            with self.assertRaises(HTTPException) as raised:
                answer_service.persist_answer_submission(
                    user_id="user-1",
                    question={
                        "id": "question-1",
                        "exam_code": "Z002",
                        "subject": "中华文化",
                        "module": "模块一",
                        "submodule": "考点一",
                    },
                    selected_answer="A",
                    used_time=12,
                    is_correct=True,
                    client_submission_id="client-answer-1",
                    practice_session_item_id="session-item-1",
                )
        self.assertEqual(raised.exception.status_code, 409)

    def test_durable_answer_survives_adaptive_update_failure(self):
        grade = {
            "question_id": "question-1",
            "exam_code": "Z001",
            "subject": "逻辑推理",
            "module": "模块一",
            "submodule": "考点一",
            "question_type": "single_choice",
            "difficulty": 2,
            "estimated_time_sec": 60,
            "source_type": "official",
            "selected_answer": "A",
            "correct_answer": "A",
            "is_correct": True,
            "explanation": "解析",
            "added_to_wrong_questions": False,
        }
        durable = {
            "submission_id": "answer-1",
            "stats_exam_code": "Z001",
            "persisted": True,
            "idempotent": False,
            "ability_accuracy": 100,
        }
        payload = SubmitAnswerRequest(
            question_id="question-1",
            client_submission_id="client-answer-1",
            practice_session_item_id="session-item-1",
            selected_answer="A",
            exam_code="Z001",
        )
        with (
            patch.object(answer_routes, "persist_answer_submission", return_value=durable),
            patch.object(answer_routes, "apply_adaptive_answer_update", side_effect=RuntimeError("temporary")),
        ):
            result = answer_routes._persist_graded_answer(
                result=grade,
                payload=payload,
                user_id="user-1",
                supabase=object(),
            )
        self.assertTrue(result["persisted"])
        self.assertFalse(result["adaptive"]["adaptive_updated"])
        self.assertTrue(result["adaptive"]["retryable"])

    def test_mark_unfamiliar_updates_the_linked_adaptive_item(self):
        grade = {
            "question_id": "question-1",
            "exam_code": "Z001",
            "subject": "逻辑推理",
            "module": "模块一",
            "submodule": "考点一",
            "question_type": "single_choice",
            "difficulty": 2,
            "estimated_time_sec": 60,
            "source_type": "official",
            "selected_answer": "B",
            "correct_answer": "A",
            "is_correct": False,
            "explanation": "解析",
            "added_to_wrong_questions": True,
        }
        payload = MarkUnfamiliarRequest(
            question_id="question-1",
            client_submission_id="client-unfamiliar-1",
            practice_session_item_id="session-item-1",
            used_time=9,
            exam_code="Z001",
        )
        durable = {
            **grade,
            "submission_id": "answer-1",
            "stats_exam_code": "Z001",
            "persisted": True,
            "idempotent": False,
            "adaptive": {"adaptive_updated": True},
        }
        with (
            patch.object(answer_routes, "get_supabase_admin", return_value=object()),
            patch.object(answer_routes, "mark_unfamiliar_answer", return_value=grade),
            patch.object(answer_routes, "_persist_graded_answer", return_value=durable) as persist,
        ):
            response = answer_routes.mark_unfamiliar(payload=payload, user_id="user-1")

        forwarded = persist.call_args.kwargs["payload"]
        self.assertEqual(forwarded.practice_session_item_id, "session-item-1")
        self.assertEqual(forwarded.selected_answer, "B")
        self.assertTrue(response.adaptive.adaptive_updated)

    def test_physical_cross_exam_question_is_rejected_before_grading(self):
        with self.assertRaises(HTTPException) as raised:
            answer_service.resolve_stats_exam_code(
                object(),
                "user-1",
                {"exam_code": "Z001", "subject": "中华文化"},
                "Z002",
            )
        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(
            answer_service.resolve_stats_exam_code(
                object(),
                "user-1",
                {"exam_code": "COMMON", "subject": "中华文化"},
                "Z002",
            ),
            "Z002",
        )


class AdaptiveSelectionTests(unittest.TestCase):
    def setUp(self):
        adaptive_practice._clear_candidate_caches()

    def _select(
        self,
        *,
        plan: TargetPlan,
        questions: list[dict],
        calibrations: dict[str, dict] | None = None,
        items=None,
        observations=None,
        pending=None,
        ever_answered=None,
        scope_filter=None,
        fallback_plan: TargetPlan | None = None,
        subject_state: AbilityState | None = None,
        client: _InsertClient | None = None,
        item_loads=None,
        trusted_current=True,
    ):
        client = client or _InsertClient()
        self.last_insert_client = client
        session = {
            "id": "session-1",
            "stats_exam_code": "Z001",
            "subject": "逻辑推理",
            "requested_question_count": 8,
            "user_preference": "standard",
            "strategy_config": {},
            "state_snapshot": {
                "diagnostic_status": "NEW",
                "reliable_first_attempt_count": 0,
            },
            "scope_filter": scope_filter or [],
        }

        def choose_plan(**kwargs):
            if fallback_plan is not None and kwargs.get("pending_verification") is False:
                return fallback_plan
            return plan

        selected_subject_state = subject_state or AbilityState(
            pending_conflict_count=1 if pending else 0
        )

        load_items_patch = (
            patch.object(
                adaptive_practice,
                "_load_session_items",
                side_effect=item_loads,
            )
            if item_loads is not None
            else patch.object(
                adaptive_practice,
                "_load_session_items",
                return_value=items or [],
            )
        )
        with (
            load_items_patch,
            patch.object(
                adaptive_practice,
                "load_subject_state",
                return_value=selected_subject_state,
            ),
            patch.object(adaptive_practice, "load_topic_state_map", return_value={}),
            patch.object(
                adaptive_practice,
                "_pending_conflict",
                return_value=pending,
            ) as pending_conflict_read,
            patch.object(adaptive_practice, "_observations_from_items", return_value=observations or []),
            patch.object(adaptive_practice, "plan_next_target", side_effect=choose_plan),
            patch.object(adaptive_practice, "_fetch_candidate_questions", return_value=questions),
            patch.object(adaptive_practice, "_load_calibration_map", return_value=calibrations or {}),
            patch.object(
                adaptive_practice,
                "_load_candidate_history_snapshot",
                return_value={
                    "recent_question_ids": set(),
                    "ever_answered_question_ids": set(ever_answered or []),
                    "due_review_values": {},
                },
            ),
            patch.object(
                adaptive_practice,
                "_selected_trusted_candidate_is_current",
                side_effect=(
                    trusted_current
                    if isinstance(trusted_current, list)
                    else None
                ),
                return_value=(
                    True if isinstance(trusted_current, list) else trusted_current
                ),
            ) as trusted_revalidation,
            patch.object(adaptive_practice, "warm_submission_questions"),
        ):
            result = adaptive_practice._select_and_insert_next(client, "user-1", session)
        self.last_trusted_revalidation = trusted_revalidation
        self.last_pending_conflict_read = pending_conflict_read
        return result, client.query.payload

    def test_selection_uses_atomic_claim_with_subject_state_version(self):
        self._select(
            plan=TargetPlan(2, TargetZone.MAIN, ("matched_training",)),
            questions=[_question("question-1", 2)],
            subject_state=AbilityState(theta=0.25, state_version=7),
        )
        self.assertEqual(
            self.last_insert_client.rpc_name,
            "claim_next_adaptive_practice_item",
        )
        self.assertEqual(
            self.last_insert_client.rpc_payload["p_expected_subject_state_version"],
            7,
        )
        self.assertEqual(
            self.last_insert_client.rpc_payload["p_question_id"],
            "question-1",
        )
        self.last_pending_conflict_read.assert_not_called()

    def test_claim_uses_authoritative_question_snapshot_for_display(self):
        stale_question = _question("question-1", 2)
        stale_question["stem"] = "缓存中的旧题面"
        stale_question["answer"] = "A"
        authoritative_question = {
            **stale_question,
            "stem": "数据库当前题面",
            "answer": "B",
            "explanation": "数据库当前解析",
        }
        client = _InsertClient(
            responses=[
                {
                    "id": "inserted-item",
                    "session_id": "session-1",
                    "question_id": "question-1",
                    "position": 1,
                    "item_status": "SELECTED",
                    "selection_reason": "matched_training",
                    "target_zone": "main",
                    "predicted_probability": 0.7,
                    "strategy_metadata": {"reason_codes": ["matched_training"]},
                    "is_diagnostic": False,
                    "is_challenge": False,
                    "question_snapshot": authoritative_question,
                }
            ]
        )

        result, _ = self._select(
            plan=TargetPlan(2, TargetZone.MAIN, ("matched_training",)),
            questions=[stale_question],
            client=client,
        )

        self.assertEqual(result["question"]["stem"], "数据库当前题面")
        self.assertIsNone(result["question"]["answer"])
        self.assertIsNone(result["question"]["explanation"])
        self.assertEqual(client.execute_count, 1)

    def test_atomic_claim_recomputes_once_after_state_conflict(self):
        client = _InsertClient(errors=[RuntimeError("adaptive_state_conflict")])
        result, _ = self._select(
            plan=TargetPlan(2, TargetZone.MAIN, ("matched_training",)),
            questions=[_question("question-1", 2)],
            client=client,
        )
        self.assertEqual(result["question"]["id"], "question-1")
        self.assertEqual(client.execute_count, 2)

    def test_atomic_claim_maps_repeated_state_conflict_to_retryable_409(self):
        client = _InsertClient(
            errors=[
                RuntimeError("adaptive_state_conflict"),
                RuntimeError("adaptive_state_conflict"),
            ]
        )
        with self.assertRaises(HTTPException) as raised:
            self._select(
                plan=TargetPlan(2, TargetZone.MAIN, ("matched_training",)),
                questions=[_question("question-1", 2)],
                client=client,
            )
        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(raised.exception.detail["code"], "ADAPTIVE_NEXT_STATE_CHANGED")
        self.assertTrue(raised.exception.detail["retryable"])

    def test_atomic_claim_maps_database_pending_barrier_to_existing_code(self):
        client = _InsertClient(errors=[RuntimeError("adaptive_update_pending")])
        with self.assertRaises(HTTPException) as raised:
            self._select(
                plan=TargetPlan(2, TargetZone.MAIN, ("matched_training",)),
                questions=[_question("question-1", 2)],
                client=client,
            )
        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(raised.exception.detail["code"], "ADAPTIVE_UPDATE_PENDING")

    def test_idempotent_claim_returns_persisted_winner_question(self):
        winner_question = _question("winner-question", 2)
        winner = {
            "id": "winner-item",
            "session_id": "session-1",
            "question_id": "winner-question",
            "position": 1,
            "item_status": "SELECTED",
            "selection_reason": "matched_training",
            "target_zone": "main",
            "strategy_metadata": {"reason_codes": ["matched_training"]},
            "is_diagnostic": False,
            "is_challenge": False,
            "questions": winner_question,
        }
        client = _InsertClient(
            responses=[
                {
                    **winner,
                    "questions": None,
                    "claimed": False,
                    "idempotent": True,
                }
            ]
        )
        result, _ = self._select(
            plan=TargetPlan(2, TargetZone.MAIN, ("matched_training",)),
            questions=[_question("losing-question", 2)],
            client=client,
            item_loads=[[], [winner]],
        )
        self.assertEqual(result["id"], "winner-item")
        self.assertEqual(result["question"]["id"], "winner-question")

    def test_untrusted_d1_to_d3_diagnostic_falls_back_to_ordinary_coverage(self):
        fallback_reason = "diagnostic_evidence_deferred_untrusted_pool"
        for difficulty in (1, 2, 3):
            with self.subTest(difficulty=difficulty):
                result, inserted = self._select(
                    plan=TargetPlan(
                        difficulty,
                        TargetZone.DIAGNOSTIC,
                        (f"diagnostic_d{difficulty}",),
                        True,
                        True,
                    ),
                    questions=[_question(f"ordinary-d{difficulty}", difficulty)],
                    calibrations={
                        f"ordinary-d{difficulty}": {
                            "quality_status": "APPROVED",
                            "quality_weight": 1.0,
                            "is_diagnostic_candidate": False,
                        }
                    },
                )

                self.assertEqual(result["question"]["id"], f"ordinary-d{difficulty}")
                self.assertEqual(inserted["target_zone"], TargetZone.COVERAGE.value)
                self.assertFalse(inserted["is_diagnostic"])
                self.assertFalse(inserted["is_challenge"])
                self.assertEqual(inserted["selection_reason"], fallback_reason)
                self.assertEqual(inserted["fallback_reason"], fallback_reason)
                self.assertIn("ability_match", inserted["score_components"])
                self.assertNotIn("information", inserted["score_components"])
                self.assertIn(
                    f"diagnostic_d{difficulty}",
                    inserted["strategy_metadata"]["reason_codes"],
                )
                self.last_trusted_revalidation.assert_not_called()

    def test_warmup_d4_never_falls_back_to_unreviewed_d4(self):
        result, inserted = self._select(
            plan=TargetPlan(4, TargetZone.DIAGNOSTIC, ("probe_upper_bound",), True, True),
            questions=[_question("ordinary-d4", 4), _question("fallback-d3", 3)],
        )
        self.assertEqual(result["question"]["id"], "fallback-d3")
        self.assertEqual(inserted["fallback_reason"], "d4_diagnostic_pool_unavailable_fallback_d3")

    def test_warmup_d5_pool_shortage_falls_back_to_approved_d4(self):
        result, inserted = self._select(
            plan=TargetPlan(5, TargetZone.CHALLENGE, ("bounded_challenge",), False, True),
            questions=[_question("ordinary-d5", 5), _question("approved-d4", 4)],
            calibrations={
                "approved-d4": {
                    "quality_status": "APPROVED",
                    "quality_weight": 1.0,
                    "is_diagnostic_candidate": True,
                }
            },
        )
        self.assertEqual(result["question"]["id"], "approved-d4")
        self.assertEqual(inserted["fallback_reason"], "d5_diagnostic_pool_unavailable_fallback_d4")

    def test_verification_selection_stays_on_pending_conflict_skill(self):
        pending = {
            "id": "conflict-1",
            "module": "模块一",
            "submodule": "考点一",
            "question_type": "single_choice",
            "verification_count": 0,
            "low_question_id": "old-low",
            "high_question_id": "old-high",
        }
        result, inserted = self._select(
            plan=TargetPlan(2, TargetZone.VERIFY, ("inversion_parallel_recheck",), True),
            questions=[
                _question("same-skill", 2, "模块一", "考点一"),
                _question("other-skill", 2, "模块二", "考点二"),
            ],
            calibrations={
                "same-skill": {
                    "quality_status": "APPROVED",
                    "quality_weight": 0.7,
                }
            },
            pending=pending,
        )
        self.assertEqual(result["question"]["id"], "same-skill")
        self.assertTrue(inserted["strategy_metadata"]["verification_skill_matched"])
        self.assertEqual(self.last_trusted_revalidation.call_count, 1)
        self.assertFalse(
            self.last_trusted_revalidation.call_args.kwargs[
                "require_diagnostic_candidate"
            ]
        )

    def test_verification_never_uses_seen_or_wrong_difficulty_item(self):
        pending = {
            "id": "conflict-1",
            "module": "模块一",
            "submodule": "考点一",
            "question_type": "single_choice",
            "verification_count": 0,
            "low_question_id": "old-low",
            "high_question_id": "old-high",
        }
        result, inserted = self._select(
            plan=TargetPlan(2, TargetZone.VERIFY, ("inversion_parallel_recheck",), True),
            fallback_plan=TargetPlan(1, TargetZone.MAIN, ("matched_training",)),
            questions=[
                _question("seen-exact", 2, "模块一", "考点一"),
                _question("fresh-wrong-level", 3, "模块一", "考点一"),
                _question("ordinary-fallback", 1, "模块二", "考点二"),
            ],
            pending=pending,
            ever_answered={"seen-exact"},
        )
        self.assertEqual(result["question"]["id"], "ordinary-fallback")
        self.assertEqual(inserted["target_zone"], TargetZone.MAIN.value)
        self.assertFalse(inserted["strategy_metadata"]["verification_skill_matched"])
        self.assertIn(
            "verification_deferred_pool_unavailable",
            inserted["strategy_metadata"]["reason_codes"],
        )

    def test_concurrent_verification_slot_claim_falls_back_to_ordinary_training(self):
        pending = {
            "id": "conflict-1",
            "module": "模块一",
            "submodule": "考点一",
            "question_type": "single_choice",
            "verification_count": 0,
            "low_question_id": "old-low",
            "high_question_id": "old-high",
        }
        client = _InsertClient(
            errors=[RuntimeError("adaptive_conflict_verification_slot_claimed")]
        )
        result, inserted = self._select(
            plan=TargetPlan(2, TargetZone.VERIFY, ("inversion_parallel_recheck",), True),
            fallback_plan=TargetPlan(1, TargetZone.MAIN, ("matched_training",)),
            questions=[
                _question("verification-d2", 2, "模块一", "考点一"),
                _question("ordinary-d1", 1, "模块二", "考点二"),
            ],
            calibrations={
                "verification-d2": {
                    "quality_status": "APPROVED",
                    "quality_weight": 0.7,
                }
            },
            pending=pending,
            client=client,
        )
        self.assertEqual(result["question"]["id"], "ordinary-d1")
        self.assertEqual(inserted["target_zone"], TargetZone.MAIN.value)
        self.assertIn(
            "verification_deferred_slot_claimed",
            inserted["strategy_metadata"]["reason_codes"],
        )
        self.assertEqual(client.execute_count, 2)

    def test_diagnostic_claim_revalidates_trusted_pool(self):
        result, inserted = self._select(
            plan=TargetPlan(2, TargetZone.DIAGNOSTIC, ("probe_boundary",), True),
            questions=[_question("diagnostic-d2", 2)],
            calibrations={
                "diagnostic-d2": {
                    "quality_status": "APPROVED",
                    "quality_weight": 0.7,
                    "is_diagnostic_candidate": True,
                }
            },
        )

        self.assertEqual(result["question"]["id"], "diagnostic-d2")
        self.assertTrue(inserted["is_diagnostic"])
        self.assertEqual(self.last_trusted_revalidation.call_count, 1)
        self.assertTrue(
            self.last_trusted_revalidation.call_args.kwargs[
                "require_diagnostic_candidate"
            ]
        )

    def test_atomic_trusted_claim_change_invalidates_cache_and_recomputes_once(self):
        client = _InsertClient(
            errors=[RuntimeError("adaptive_trusted_candidate_changed")]
        )
        result, _ = self._select(
            plan=TargetPlan(2, TargetZone.DIAGNOSTIC, ("probe_boundary",), True),
            questions=[_question("diagnostic-d2", 2)],
            calibrations={
                "diagnostic-d2": {
                    "quality_status": "APPROVED",
                    "quality_weight": 0.7,
                    "is_diagnostic_candidate": True,
                }
            },
            client=client,
        )

        self.assertEqual(result["question"]["id"], "diagnostic-d2")
        self.assertEqual(client.execute_count, 2)

    def test_atomic_main_candidate_change_invalidates_cache_and_recomputes_once(self):
        client = _InsertClient(errors=[RuntimeError("adaptive_candidate_changed")])
        result, _ = self._select(
            plan=TargetPlan(2, TargetZone.MAIN, ("matched_training",)),
            questions=[_question("ordinary-d2", 2)],
            client=client,
        )

        self.assertEqual(result["question"]["id"], "ordinary-d2")
        self.assertEqual(client.execute_count, 2)

    def test_repeated_atomic_main_candidate_change_returns_retryable_503(self):
        client = _InsertClient(
            errors=[
                RuntimeError("adaptive_candidate_changed"),
                RuntimeError("adaptive_candidate_changed"),
            ]
        )
        with self.assertRaises(HTTPException) as raised:
            self._select(
                plan=TargetPlan(2, TargetZone.MAIN, ("matched_training",)),
                questions=[_question("ordinary-d2", 2)],
                client=client,
            )

        self.assertEqual(client.execute_count, 2)
        self.assertEqual(raised.exception.status_code, 503)
        self.assertTrue(raised.exception.detail["retryable"])

    def test_repeated_atomic_trusted_claim_change_returns_retryable_503(self):
        client = _InsertClient(
            errors=[
                RuntimeError("adaptive_trusted_candidate_changed"),
                RuntimeError("adaptive_trusted_candidate_changed"),
            ]
        )
        with self.assertRaises(HTTPException) as raised:
            self._select(
                plan=TargetPlan(2, TargetZone.DIAGNOSTIC, ("probe_boundary",), True),
                questions=[_question("diagnostic-d2", 2)],
                calibrations={
                    "diagnostic-d2": {
                        "quality_status": "APPROVED",
                        "quality_weight": 0.7,
                        "is_diagnostic_candidate": True,
                    }
                },
                client=client,
            )

        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(
            raised.exception.detail["code"],
            "ADAPTIVE_TRUSTED_POOL_CHANGED",
        )
        self.assertTrue(raised.exception.detail["retryable"])

    def test_revoked_trusted_candidate_clears_cache_and_recomputes_once(self):
        result, _ = self._select(
            plan=TargetPlan(2, TargetZone.DIAGNOSTIC, ("probe_boundary",), True),
            questions=[_question("diagnostic-d2", 2)],
            calibrations={
                "diagnostic-d2": {
                    "quality_status": "APPROVED",
                    "quality_weight": 0.7,
                    "is_diagnostic_candidate": True,
                }
            },
            trusted_current=[False, True],
        )

        self.assertEqual(result["question"]["id"], "diagnostic-d2")
        self.assertEqual(self.last_trusted_revalidation.call_count, 2)
        self.assertEqual(self.last_insert_client.execute_count, 1)

    def test_repeated_trusted_pool_revocation_returns_retryable_503(self):
        with self.assertRaises(HTTPException) as raised:
            self._select(
                plan=TargetPlan(2, TargetZone.DIAGNOSTIC, ("probe_boundary",), True),
                questions=[_question("diagnostic-d2", 2)],
                calibrations={
                    "diagnostic-d2": {
                        "quality_status": "APPROVED",
                        "quality_weight": 0.7,
                        "is_diagnostic_candidate": True,
                    }
                },
                trusted_current=[False, False],
            )

        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(
            raised.exception.detail["code"],
            "ADAPTIVE_TRUSTED_POOL_CHANGED",
        )
        self.assertTrue(raised.exception.detail["retryable"])
        self.assertEqual(self.last_insert_client.execute_count, 0)

    def test_out_of_scope_conflict_is_deferred_without_verify_label(self):
        pending = {
            "id": "conflict-1",
            "module": "模块一",
            "submodule": "考点一",
            "question_type": "single_choice",
            "verification_count": 0,
        }
        result, inserted = self._select(
            plan=TargetPlan(2, TargetZone.VERIFY, ("inversion_parallel_recheck",), True),
            fallback_plan=TargetPlan(2, TargetZone.MAIN, ("matched_training",)),
            questions=[_question("in-scope", 2, "模块二", "考点二")],
            pending=pending,
            scope_filter=[{"module": "模块二", "submodule": "考点二"}],
        )
        self.assertEqual(result["question"]["id"], "in-scope")
        self.assertEqual(inserted["target_zone"], TargetZone.MAIN.value)
        self.assertIn(
            "verification_deferred_out_of_scope",
            inserted["strategy_metadata"]["reason_codes"],
        )

    def test_three_wrong_switches_topic_before_difficulty_fallback(self):
        observations = [
            Observation(f"wrong-{index}", 2, False, "模块一", "考点一", position=index)
            for index in range(1, 4)
        ]
        result, inserted = self._select(
            plan=TargetPlan(2, TargetZone.CONSOLIDATION, ("two_wrong_protection",)),
            questions=[
                _question("same-topic-exact", 2, "模块一", "考点一"),
                _question("other-topic-nearby", 3, "模块二", "考点二"),
            ],
            observations=observations,
        )
        self.assertEqual(result["question"]["id"], "other-topic-nearby")
        self.assertIn(
            "three_wrong_topic_switch",
            inserted["strategy_metadata"]["reason_codes"],
        )

    def test_positive_finish_reports_safe_pool_shortage_instead_of_falling_upward(self):
        with self.assertRaises(HTTPException) as raised:
            self._select(
                plan=TargetPlan(1, TargetZone.CONSOLIDATION, ("positive_finish",)),
                questions=[_question("only-hard", 4)],
            )
        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(
            raised.exception.detail["code"],
            "ADAPTIVE_SAFE_POOL_UNAVAILABLE",
        )

    def test_challenge_recovery_fallback_only_moves_to_an_easier_bucket(self):
        result, inserted = self._select(
            plan=TargetPlan(2, TargetZone.CONSOLIDATION, ("challenge_recovery",)),
            questions=[
                _question("easier", 1),
                _question("harder", 4),
            ],
        )
        self.assertEqual(result["question"]["id"], "easier")
        self.assertEqual(inserted["fallback_reason"], "difficulty_shortage")

    def test_answered_last_item_is_not_returned_again(self):
        answered_item = {
            "id": "item-1",
            "question_id": "question-1",
            "position": 1,
            "item_status": "ANSWERED",
            "answer_id": "answer-1",
            "questions": _question("question-1", 2),
        }
        with patch.object(adaptive_practice, "_load_session_items", return_value=[answered_item]):
            result = adaptive_practice._select_and_insert_next(
                object(),
                "user-1",
                {
                    "id": "session-1",
                    "stats_exam_code": "Z001",
                    "subject": "逻辑推理",
                    "requested_question_count": 1,
                },
            )
        self.assertIsNone(result)

    def test_expired_verification_item_remains_answerable_in_its_session(self):
        expired_item = {
            "id": "expired-verify-item",
            "session_id": "session-1",
            "question_id": "expired-verify-question",
            "position": 8,
            "item_status": "PRESENTED",
            "answer_id": None,
            "target_zone": "verify",
            "strategy_metadata": {"verification_slot_expired": True},
            "questions": _question("expired-verify-question", 2),
        }
        result, inserted = self._select(
            plan=TargetPlan(2, TargetZone.MAIN, ("matched_training",)),
            questions=[_question("replacement-question", 2)],
            items=[expired_item],
        )
        self.assertEqual(result["question"]["id"], "expired-verify-question")
        self.assertEqual(result["position"], 8)
        self.assertIsNone(inserted)


class AdaptiveEvidenceTests(unittest.TestCase):
    def test_explanation_viewed_after_answer_keeps_answer_evidence(self):
        answer = {"created_at": "2026-09-04T10:00:00+00:00"}
        viewed_after = {"explanation_viewed_at": "2026-09-04T10:00:01+00:00"}
        viewed_before = {"explanation_viewed_at": "2026-09-04T09:59:59+00:00"}
        self.assertFalse(adaptive_practice._answer_was_seen_before_submission(viewed_after, answer))
        self.assertTrue(adaptive_practice._answer_was_seen_before_submission(viewed_before, answer))

    def test_zero_evidence_weight_remains_zero(self):
        item = {
            "id": "item-1",
            "question_id": "question-1",
            "position": 1,
            "answer_id": "answer-1",
            "strategy_metadata": {"evidence_weight": 0.0},
            "questions": _question("question-1", 2),
        }
        with patch.object(
            adaptive_practice,
            "_answer_map",
            return_value={
                "answer-1": {
                    "id": "answer-1",
                    "is_correct": True,
                    "is_first_attempt": True,
                    "used_time": 20,
                    "created_at": "2026-09-01T00:00:00+00:00",
                }
            },
        ):
            observations = adaptive_practice._observations_from_items(object(), [item])
        self.assertEqual(observations[0].evidence_weight, 0.0)

    def test_embedded_session_answer_avoids_followup_answer_query(self):
        item = {
            "id": "item-1",
            "question_id": "question-1",
            "position": 1,
            "answer_id": "answer-1",
            "strategy_metadata": {"quality_weight": 1.0},
            "questions": _question("question-1", 2),
            "answer": {
                "id": "answer-1",
                "question_id": "question-1",
                "is_correct": True,
                "is_first_attempt": True,
                "used_time": 20,
                "created_at": "2026-09-01T00:00:00+00:00",
            },
        }
        with patch.object(
            adaptive_practice,
            "_answer_map",
            side_effect=AssertionError("embedded answer should avoid a second read"),
        ):
            observations = adaptive_practice._observations_from_items(
                object(), [item]
            )

        self.assertEqual(len(observations), 1)
        self.assertTrue(observations[0].is_correct)

    def test_closed_inversion_pair_is_not_reopened(self):
        observations = [
            Observation("low", 1, False, "模块一", "考点一", position=1),
            Observation("high", 3, True, "模块一", "考点一", position=2),
        ]
        with patch.object(adaptive_practice, "_conflict_pair_is_closed", return_value=True) as closed:
            inversion = adaptive_practice._detect_unhandled_inversion(
                object(),
                user_id="user-1",
                exam_code="Z001",
                subject="逻辑推理",
                observations=observations,
                pending_conflict=None,
            )
        self.assertIsNone(inversion)
        closed.assert_called_once_with(
            ANY,
            user_id="user-1",
            exam_code="Z001",
            subject="逻辑推理",
            low_question_id="low",
            high_question_id="high",
        )

    def test_legacy_bootstrap_isolated_by_actual_exam_code_and_subject(self):
        def history_rows(is_correct):
            return [
                {
                    "id": f"answer-{index}",
                    "is_correct": is_correct,
                    "used_time": 30,
                    "created_at": f"2026-08-{index + 1:02d}T00:00:00+00:00",
                    "questions": {
                        **_question(
                            f"question-{index}",
                            2,
                            "模块一" if index % 2 == 0 else "模块二",
                            "考点一" if index % 2 == 0 else "考点二",
                        ),
                        "subject": "中华文化",
                    },
                }
                for index in range(6)
            ]

        client = _BootstrapClient({
            ("Z001", "中华文化"): history_rows(True),
            ("Z002", "中华文化"): history_rows(False),
        })

        def load_subject_row(_client, _user_id, exam_code, subject):
            return client.subject_rows.get((exam_code, subject))

        with (
            patch.object(adaptive_practice, "_load_subject_state_row", side_effect=load_subject_row),
            patch.object(adaptive_practice, "_load_calibration_map", return_value={}),
        ):
            z001_state, z001_meta = adaptive_practice.bootstrap_subject_state_if_needed(
                client,
                user_id="user-1",
                exam_code="Z001",
                subject="中华文化",
            )
            z002_state, z002_meta = adaptive_practice.bootstrap_subject_state_if_needed(
                client,
                user_id="user-1",
                exam_code="Z002",
                subject="中华文化",
            )

        self.assertGreater(z001_state.theta, 0)
        self.assertLess(z002_state.theta, 0)
        self.assertEqual(z001_meta["bootstrap_count"], 6)
        self.assertEqual(z002_meta["bootstrap_count"], 6)
        self.assertEqual(
            {(filters["stats_exam_code"], filters["questions.subject"]) for filters in client.history_filters},
            {("Z001", "中华文化"), ("Z002", "中华文化")},
        )
        self.assertEqual(
            {filters["questions.exam_code"] for filters in client.history_filters},
            {("COMMON", "Z001"), ("COMMON", "Z002")},
        )

    def test_non_public_bootstrap_never_reads_common_questions(self):
        client = _BootstrapClient({("Z001", "逻辑推理"): []})
        with patch.object(adaptive_practice, "_load_subject_state_row", return_value=None):
            state, metadata = adaptive_practice.bootstrap_subject_state_if_needed(
                client,
                user_id="user-1",
                exam_code="Z001",
                subject="逻辑推理",
            )
        self.assertEqual(state, AbilityState())
        self.assertFalse(metadata["bootstrap_applied"])
        self.assertEqual(client.history_filters[0]["questions.exam_code"], "Z001")


class AdaptiveConflictConcurrencyTests(unittest.TestCase):
    def test_zero_conflict_counter_skips_conflict_table_read_on_answer_update(self):
        question = _question("ordinary-question", 2)
        item = {
            "id": "ordinary-item",
            "session_id": "session-1",
            "question_id": question["id"],
            "position": 1,
            "target_zone": "main",
            "answered_at": "2026-09-04T00:00:00+00:00",
            "strategy_metadata": {},
            "practice_sessions": {
                "user_id": "user-1",
                "stats_exam_code": "Z001",
                "subject": "逻辑推理",
            },
            "persisted_snapshot": {
                "question_id": question["id"],
                "question_snapshot": question,
            },
            "questions": {
                **question,
                "subject": "中华文化",
                "module": "被编辑模块",
                "difficulty": 5,
            },
        }
        client = _SequentialRpcClient(
            [{"adaptive_updated": True, "idempotent": False}]
        )
        with (
            patch.object(adaptive_practice, "_query_one", return_value=item),
            patch.object(adaptive_practice, "_calibration_for_question", return_value={}),
            patch.object(adaptive_practice, "_load_session_items", return_value=[item]),
            patch.object(adaptive_practice, "_observations_from_items", return_value=[]),
            patch.object(
                adaptive_practice,
                "load_subject_state",
                return_value=AbilityState(pending_conflict_count=0),
            ),
            patch.object(adaptive_practice, "load_topic_state_map", return_value={}),
            patch.object(adaptive_practice, "_pending_conflict") as pending_read,
            patch.object(adaptive_practice, "_detect_unhandled_inversion", return_value=None),
        ):
            result = adaptive_practice.apply_adaptive_answer_update(
                client,
                user_id="user-1",
                question=question,
                persisted={
                    "submission_id": "answer-1",
                    "stats_exam_code": "Z001",
                    "is_first_attempt": True,
                    "is_correct": True,
                    "created_at": "2026-09-04T00:00:00+00:00",
                },
                used_time=20,
                practice_session_item_id="ordinary-item",
            )

        self.assertTrue(result["adaptive_updated"])
        pending_read.assert_not_called()

    def test_answer_update_uses_frozen_item_difficulty_and_quality_metadata(self):
        frozen_question = _question("frozen-question", 2)
        item = {
            "id": "frozen-item",
            "session_id": "session-1",
            "question_id": frozen_question["id"],
            "position": 1,
            "target_zone": "main",
            "answered_at": "2026-09-04T00:00:00+00:00",
            "item_difficulty": 0.875,
            "strategy_metadata": {
                "quality_weight": 0.35,
                "question_valid": False,
            },
            "practice_sessions": {
                "user_id": "user-1",
                "stats_exam_code": "Z001",
                "subject": "逻辑推理",
            },
            "persisted_snapshot": {
                "question_id": frozen_question["id"],
                "question_snapshot": frozen_question,
            },
            # Deliberately disagree with the frozen snapshot. The joined live
            # question and current calibration are not ability-update inputs.
            "questions": {
                **frozen_question,
                "difficulty": 5,
            },
        }
        client = _SequentialRpcClient(
            [{"adaptive_updated": True, "idempotent": False}]
        )
        with (
            patch.object(adaptive_practice, "_query_one", return_value=item),
            patch.object(
                adaptive_practice,
                "_calibration_for_question",
                return_value={
                    "item_difficulty": -1.5,
                    "quality_weight": 1.0,
                    "quality_status": "APPROVED",
                },
            ) as live_calibration,
            patch.object(adaptive_practice, "_load_session_items", return_value=[item]),
            patch.object(adaptive_practice, "_observations_from_items", return_value=[]),
            patch.object(adaptive_practice, "load_subject_state", return_value=AbilityState()),
            patch.object(adaptive_practice, "load_topic_state_map", return_value={}),
            patch.object(adaptive_practice, "_pending_conflict") as pending_read,
            patch.object(adaptive_practice, "_detect_unhandled_inversion", return_value=None),
            patch.object(
                adaptive_practice,
                "compute_evidence_weight",
                wraps=adaptive_practice.compute_evidence_weight,
            ) as evidence_weight,
        ):
            result = adaptive_practice.apply_adaptive_answer_update(
                client,
                user_id="user-1",
                question={**frozen_question, "difficulty": 5},
                persisted={
                    "submission_id": "answer-1",
                    "stats_exam_code": "Z001",
                    "is_first_attempt": True,
                    "is_correct": True,
                    "created_at": "2026-09-04T00:00:00+00:00",
                },
                used_time=20,
                practice_session_item_id="frozen-item",
            )

        self.assertTrue(result["adaptive_updated"])
        live_calibration.assert_not_called()
        pending_read.assert_not_called()
        evidence_context = evidence_weight.call_args.args[0]
        self.assertEqual(evidence_context.quality_weight, 0.35)
        self.assertFalse(evidence_context.question_valid)
        update_payload = client.calls[0][1]["p_update"]
        self.assertEqual(update_payload["item_difficulty"], 0.875)
        self.assertFalse(update_payload["question_valid"])
        self.assertEqual(update_payload["evidence_weight"], 0.0)

    def test_update_retry_classifies_state_and_verification_snapshot_races(self):
        for marker in (
            "adaptive_state_conflict",
            "adaptive_conflict_verification_snapshot_mismatch",
            "adaptive_conflict_verification_difficulty_mismatch",
        ):
            with self.subTest(marker=marker):
                self.assertTrue(
                    adaptive_practice._is_retryable_adaptive_update_error(
                        RuntimeError(marker)
                    )
                )
        self.assertFalse(
            adaptive_practice._is_retryable_adaptive_update_error(
                RuntimeError("adaptive_scope_mismatch")
            )
        )

    def test_state_conflict_retry_reloads_verification_count_and_reclassifies_stale_d2(self):
        question = _question("verify-d2", 2)
        conflict_base = {
            "id": "conflict-1",
            "module": "模块一",
            "submodule": "考点一",
            "question_type": "single_choice",
            "low_question_id": "old-low",
            "high_question_id": "old-high",
        }
        item = {
            "id": "item-1",
            "session_id": "session-1",
            "question_id": "verify-d2",
            "position": 3,
            "target_zone": "verify",
            "answered_at": "2026-09-04T00:00:00+00:00",
            "strategy_metadata": {
                "verification_conflict_id": "conflict-1",
                "verification_expected_count": 0,
                "verification_expected_difficulty": 2,
            },
            "practice_sessions": {
                "user_id": "user-1",
                "stats_exam_code": "Z001",
                "subject": "逻辑推理",
            },
            "persisted_snapshot": {
                "question_id": question["id"],
                "question_snapshot": question,
            },
            "questions": question,
        }
        client = _SequentialRpcClient(
            [
                RuntimeError("adaptive_state_conflict"),
                {"adaptive_updated": True, "idempotent": False},
            ]
        )
        first_state = AbilityState(
            pending_conflict_count=1,
            state_version=0,
            diagnostic_status=DiagnosticStatus.VERIFYING,
        )
        winning_state = AbilityState(
            theta=0.1,
            pending_conflict_count=1,
            state_version=1,
            diagnostic_status=DiagnosticStatus.VERIFYING,
        )
        with (
            patch.object(adaptive_practice, "_query_one", return_value=item),
            patch.object(adaptive_practice, "_calibration_for_question", return_value={}),
            patch.object(adaptive_practice, "_load_session_items", return_value=[item]),
            patch.object(adaptive_practice, "_observations_from_items", return_value=[]),
            patch.object(
                adaptive_practice,
                "load_subject_state",
                side_effect=[first_state, winning_state],
            ),
            patch.object(
                adaptive_practice,
                "load_topic_state",
                side_effect=[
                    AbilityState(state_version=0),
                    AbilityState(theta=0.1, state_version=1),
                ],
            ),
            patch.object(
                adaptive_practice,
                "_pending_conflict",
                side_effect=[
                    {**conflict_base, "verification_count": 0},
                    {**conflict_base, "verification_count": 1},
                ],
            ),
            patch.object(adaptive_practice, "_detect_unhandled_inversion", return_value=None),
            patch.object(adaptive_practice, "load_topic_state_map", return_value={}),
        ):
            result = adaptive_practice.apply_adaptive_answer_update(
                client,
                user_id="user-1",
                question=question,
                persisted={
                    "submission_id": "answer-1",
                    "stats_exam_code": "Z001",
                    "is_first_attempt": True,
                    "is_correct": True,
                    "created_at": "2026-09-04T00:00:00+00:00",
                },
                used_time=20,
                practice_session_item_id="item-1",
            )

        self.assertTrue(result["adaptive_updated"])
        first_payload = client.calls[0][1]["p_update"]
        second_payload = client.calls[1][1]["p_update"]
        self.assertEqual(first_payload["update_reason"], "conflict_recheck")
        self.assertEqual(first_payload["conflict"]["action"], "verify")
        self.assertEqual(second_payload["update_reason"], "answer")
        self.assertEqual(second_payload["conflict"]["action"], "none")

    def test_expired_verification_answer_is_only_ordinary_ability_evidence(self):
        question = _question("late-verify-d2", 2)
        pending_conflict = {
            "id": "conflict-1",
            "module": "模块一",
            "submodule": "考点一",
            "question_type": "single_choice",
            "low_question_id": "old-low",
            "high_question_id": "old-high",
            "verification_count": 0,
        }
        item = {
            "id": "expired-item",
            "session_id": "old-session",
            "question_id": "late-verify-d2",
            "position": 3,
            "target_zone": "verify",
            "answered_at": "2026-09-04T00:20:00+00:00",
            "strategy_metadata": {
                "verification_conflict_id": "conflict-1",
                "verification_expected_count": 0,
                "verification_expected_difficulty": 2,
                "verification_slot_expired": True,
                "verification_slot_expired_at": "2026-09-04T00:15:00+00:00",
                "verification_slot_lease_seconds": 900,
            },
            "practice_sessions": {
                "user_id": "user-1",
                "stats_exam_code": "Z001",
                "subject": "逻辑推理",
            },
            "persisted_snapshot": {
                "question_id": question["id"],
                "question_snapshot": question,
            },
            "questions": question,
        }
        state = AbilityState(
            pending_conflict_count=1,
            diagnostic_status=DiagnosticStatus.VERIFYING,
        )
        client = _SequentialRpcClient(
            [{"adaptive_updated": True, "idempotent": False}]
        )
        with (
            patch.object(adaptive_practice, "_query_one", return_value=item),
            patch.object(adaptive_practice, "_calibration_for_question", return_value={}),
            patch.object(adaptive_practice, "_load_session_items", return_value=[item]),
            patch.object(adaptive_practice, "_observations_from_items", return_value=[]),
            patch.object(adaptive_practice, "load_subject_state", return_value=state),
            patch.object(
                adaptive_practice,
                "load_topic_state",
                return_value=AbilityState(),
            ) as legacy_topic_read,
            patch.object(adaptive_practice, "_pending_conflict", return_value=pending_conflict),
            patch.object(adaptive_practice, "_detect_unhandled_inversion", return_value=None),
            patch.object(
                adaptive_practice,
                "load_topic_state_map",
                return_value={},
            ) as topic_map_read,
        ):
            result = adaptive_practice.apply_adaptive_answer_update(
                client,
                user_id="user-1",
                question=question,
                persisted={
                    "submission_id": "late-answer",
                    "stats_exam_code": "Z001",
                    "is_first_attempt": True,
                    "is_correct": True,
                    "created_at": "2026-09-04T00:20:00+00:00",
                },
                used_time=20,
                practice_session_item_id="expired-item",
            )

        self.assertTrue(result["adaptive_updated"])
        legacy_topic_read.assert_not_called()
        topic_map_read.assert_called_once()
        update_payload = client.calls[0][1]["p_update"]
        self.assertEqual(update_payload["update_reason"], "answer")
        self.assertEqual(update_payload["conflict"]["action"], "none")
        self.assertGreater(
            update_payload["subject_after"]["theta"],
            update_payload["subject_before"]["theta"],
        )

    def test_verification_history_uses_database_consumption_result(self):
        client = _RecordingClient(
            {
                "adaptive_model_updates": [
                    {
                        "actual_correct": False,
                        "update_payload": {
                            "conflict": {"id": "conflict-1", "action": "resolve"},
                            "conflict_result": {
                                "id": "conflict-1",
                                "action": "resolve",
                            },
                        },
                    },
                    {
                        "actual_correct": True,
                        "update_payload": {
                            "conflict": {"id": "conflict-1", "action": "verify"},
                            "conflict_result": {"id": None, "action": "none"},
                        },
                    },
                    {
                        "actual_correct": True,
                        "update_payload": {
                            "conflict": {"id": "conflict-1", "action": "verify"},
                            "conflict_result": {
                                "id": "conflict-1",
                                "action": "verify",
                            },
                        },
                    },
                    {
                        "actual_correct": True,
                        "update_payload": {
                            "conflict_result": {
                                "id": "another-conflict",
                                "action": "verify",
                            },
                        },
                    },
                ]
            }
        )

        results = adaptive_practice._conflict_verification_results(
            client,
            user_id="user-1",
            exam_code="Z001",
            subject="逻辑推理",
            conflict_id="conflict-1",
        )

        self.assertEqual(results, [True, False])


class AdaptiveUpdateBarrierTests(unittest.TestCase):
    @staticmethod
    def _active_session() -> dict:
        return {
            "id": "session-1",
            "stats_exam_code": "Z001",
            "subject": "逻辑推理",
            "mode": "special",
            "requested_question_count": 8,
            "user_preference": "standard",
            "status": "ACTIVE",
            "diagnostic_status": "CALIBRATING",
            "strategy_version": "adaptive-delivery-v1",
            "model_version": "theta-shrinkage-v1",
        }

    def test_pending_item_loader_uses_database_antijoin_rpc(self):
        client = _RpcClient(
            response=[
                {
                    "practice_session_item_id": "item-1",
                    "session_id": "other-session",
                    "question_id": "question-1",
                    "item_position": 2,
                    "answer_id": "answer-1",
                    "answered_at": "2026-09-04T00:00:00+00:00",
                    "answer_stats_exam_code": "Z001",
                    "is_correct": True,
                    "is_first_attempt": True,
                    "used_time": 20,
                    "answer_created_at": "2026-09-04T00:00:00+00:00",
                    "question_exam_code": "Z001",
                    "question_subject": "逻辑推理",
                    "module": "模块一",
                    "submodule": "考点一",
                    "question_type": "single_choice",
                    "difficulty": 2,
                    "estimated_time_sec": 60,
                    "source_type": "official",
                }
            ]
        )
        items = adaptive_practice._load_pending_adaptive_update_items(
            client,
            user_id="user-1",
            exam_code="Z001",
            subject="逻辑推理",
        )
        self.assertEqual(client.rpc_name, "get_pending_adaptive_update_items")
        self.assertIsNone(client.rpc_payload["p_session_id"])
        self.assertEqual(items[0]["session_id"], "other-session")
        self.assertEqual(items[0]["answer"]["id"], "answer-1")
        self.assertEqual(items[0]["questions"]["id"], "question-1")

    def test_scope_wide_pending_items_have_stable_answer_session_position_order(self):
        def row(
            item_id: str,
            *,
            answered_at: str,
            session_id: str,
            position: int,
        ) -> dict:
            return {
                "practice_session_item_id": item_id,
                "session_id": session_id,
                "question_id": f"question-{item_id}",
                "item_position": position,
                "answer_id": f"answer-{item_id}",
                "answered_at": answered_at,
                "answer_stats_exam_code": "Z001",
                "is_correct": True,
                "is_first_attempt": True,
                "used_time": 20,
                "answer_created_at": answered_at,
                "question_exam_code": "Z001",
                "question_subject": "逻辑推理",
                "module": "模块一",
                "submodule": "考点一",
                "question_type": "single_choice",
                "difficulty": 2,
                "estimated_time_sec": 60,
                "source_type": "official",
            }

        client = _RpcClient(
            response=[
                row(
                    "latest",
                    answered_at="2026-09-04T00:02:00+00:00",
                    session_id="session-a",
                    position=1,
                ),
                row(
                    "same-time-session-b",
                    answered_at="2026-09-04T00:01:00+00:00",
                    session_id="session-b",
                    position=1,
                ),
                row(
                    "same-time-position-2",
                    answered_at="2026-09-04T00:01:00+00:00",
                    session_id="session-a",
                    position=2,
                ),
                row(
                    "same-time-position-1",
                    answered_at="2026-09-04T00:01:00+00:00",
                    session_id="session-a",
                    position=1,
                ),
            ]
        )

        items = adaptive_practice._load_pending_adaptive_update_items(
            client,
            user_id="user-1",
            exam_code="Z001",
            subject="逻辑推理",
        )

        self.assertEqual(
            [entry["id"] for entry in items],
            [
                "same-time-position-1",
                "same-time-position-2",
                "same-time-session-b",
                "latest",
            ],
        )

    def test_next_item_barrier_covers_every_session_in_the_ability_scope(self):
        session = self._active_session()
        loaded_state = AbilityState(theta=0.25, state_version=3)
        with (
            patch.object(adaptive_practice, "_load_session", return_value=session),
            patch.object(
                adaptive_practice,
                "reconcile_pending_adaptive_updates",
                return_value=0,
            ) as reconcile,
            patch.object(adaptive_practice, "load_subject_state", return_value=loaded_state),
            patch.object(
                adaptive_practice,
                "_select_and_insert_next",
                return_value=None,
            ) as select_next,
        ):
            adaptive_practice.get_next_adaptive_item(
                object(),
                user_id="user-1",
                session_id="session-1",
            )
        self.assertEqual(
            reconcile.call_args.kwargs,
            {
                "user_id": "user-1",
                "exam_code": "Z001",
                "subject": "逻辑推理",
            },
        )
        self.assertIs(
            select_next.call_args.kwargs["_subject_state"],
            loaded_state,
        )

    def test_complete_barrier_covers_every_session_in_the_ability_scope(self):
        session = self._active_session()
        client = _RpcClient(
            response={
                "session_id": "session-1",
                "status": "COMPLETED",
                "reason": "completed",
                "idempotent": False,
            }
        )
        with (
            patch.object(adaptive_practice, "_load_session", return_value=session),
            patch.object(
                adaptive_practice,
                "reconcile_pending_adaptive_updates",
                return_value=0,
            ) as reconcile,
            patch.object(adaptive_practice, "load_subject_state", return_value=AbilityState()),
        ):
            adaptive_practice.complete_session(
                client,
                user_id="user-1",
                session_id="session-1",
                reason="completed",
            )
        self.assertNotIn("session_id", reconcile.call_args.kwargs)
        self.assertEqual(reconcile.call_args.kwargs["exam_code"], "Z001")
        self.assertEqual(reconcile.call_args.kwargs["subject"], "逻辑推理")

    def test_barrier_compensates_missing_updates_in_answer_order(self):
        items = [
            {
                "id": "item-1",
                "answer_id": "answer-1",
                "answer": {
                    "id": "answer-1",
                    "stats_exam_code": "Z001",
                    "is_first_attempt": True,
                    "is_correct": True,
                    "used_time": 20,
                },
                "questions": _question("question-1", 2),
            },
            {
                "id": "item-2",
                "answer_id": "answer-2",
                "answer": {
                    "id": "answer-2",
                    "stats_exam_code": "Z001",
                    "is_first_attempt": True,
                    "is_correct": False,
                    "used_time": 30,
                },
                "questions": _question("question-2", 3),
            },
        ]
        with (
            patch.object(
                adaptive_practice,
                "_load_pending_adaptive_update_items",
                return_value=items,
            ),
            patch.object(
                adaptive_practice,
                "apply_adaptive_answer_update",
                return_value={"adaptive_updated": True},
            ) as apply_update,
        ):
            applied = adaptive_practice.reconcile_pending_adaptive_updates(
                object(),
                user_id="user-1",
                exam_code="Z001",
                subject="逻辑推理",
            )
        self.assertEqual(applied, 2)
        self.assertEqual(
            [entry.kwargs["practice_session_item_id"] for entry in apply_update.call_args_list],
            ["item-1", "item-2"],
        )

    def test_barrier_returns_stable_conflict_when_compensation_is_still_pending(self):
        item = {
            "id": "item-1",
            "answer_id": "answer-1",
            "answer": {
                "id": "answer-1",
                "stats_exam_code": "Z001",
                "is_first_attempt": True,
                "is_correct": True,
                "used_time": 20,
            },
            "questions": _question("question-1", 2),
        }
        with (
            patch.object(
                adaptive_practice,
                "_load_pending_adaptive_update_items",
                return_value=[item],
            ),
            patch.object(
                adaptive_practice,
                "apply_adaptive_answer_update",
                return_value={"adaptive_updated": False, "retryable": True},
            ),
        ):
            with self.assertRaises(HTTPException) as raised:
                adaptive_practice.reconcile_pending_adaptive_updates(
                    object(),
                    user_id="user-1",
                    exam_code="Z001",
                    subject="逻辑推理",
                )
        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(raised.exception.detail["code"], "ADAPTIVE_UPDATE_PENDING")

    def test_new_session_runs_update_barrier_before_legacy_bootstrap(self):
        payload = CreateAdaptivePracticeSessionRequest(
            exam_code="Z001",
            subject="逻辑推理",
            practice_mode="special",
            scopes=[{"module": "模块一", "submodule": "考点一"}],
        )
        events = []

        def barrier(*_args, **_kwargs):
            events.append("barrier")

        def bootstrap(*_args, **_kwargs):
            events.append("bootstrap")
            raise RuntimeError("stop after ordering assertion")

        with (
            patch.object(adaptive_practice, "reconcile_pending_adaptive_updates", side_effect=barrier),
            patch.object(adaptive_practice, "bootstrap_subject_state_if_needed", side_effect=bootstrap),
        ):
            with self.assertRaises(RuntimeError):
                adaptive_practice.create_adaptive_session(
                    object(),
                    user_id="user-1",
                    payload=payload,
                )
        self.assertEqual(events, ["barrier", "bootstrap"])


class AdaptiveCandidateReadOptimizationTests(unittest.TestCase):
    def setUp(self):
        adaptive_practice._clear_candidate_caches()

    def tearDown(self):
        adaptive_practice._clear_candidate_caches()

    @staticmethod
    def _session(*, exam_code="Z001", subject="逻辑推理", scopes=None):
        return {
            "stats_exam_code": exam_code,
            "subject": subject,
            "scope_filter": scopes or [{"module": "模块一", "submodule": "考点一"}],
        }

    def test_candidate_cache_normalizes_scope_and_returns_defensive_copies(self):
        question = _question("question-1", 2)
        client = _RecordingClient({"questions": [question]})
        first_session = self._session(
            scopes=[
                {"module": "模块二", "submodule": "考点二"},
                {"module": "模块一", "submodule": "考点一"},
            ]
        )
        equivalent_session = self._session(
            scopes=[
                {"module": "模块一", "submodule": "考点一"},
                {"module": "模块二", "submodule": "考点二"},
            ]
        )

        first = adaptive_practice._fetch_candidate_questions(client, first_session)
        initial_query_count = len(client.queries)
        selected_fields = [
            operation[1]
            for operation in client.queries[0].operations
            if operation[0] == "select"
        ][0]
        first[0]["stem"] = "被调用方修改"
        second = adaptive_practice._fetch_candidate_questions(client, equivalent_session)

        self.assertEqual(initial_query_count, 2)
        self.assertEqual(len(client.queries), initial_query_count)
        self.assertEqual(second[0]["stem"], question["stem"])
        self.assertIn("answer", selected_fields.split(","))
        self.assertIn("explanation", selected_fields.split(","))

    def test_session_item_join_warms_grading_fields_without_api_disclosure(self):
        question = _question("warm-grading-question", 2)
        edited_live_question = {
            **question,
            "stem": "领取后被编辑的题面",
            "answer": "B",
            "explanation": "领取后被编辑的解析",
        }
        item = {
            "id": "warm-grading-item",
            "session_id": "warm-grading-session",
            "question_id": question["id"],
            "position": 1,
            "item_status": "SELECTED",
            "selection_reason": "matched_training",
            "target_zone": "main",
            "strategy_metadata": {"reason_codes": ["matched_training"]},
            "is_diagnostic": False,
            "is_challenge": False,
            "answer_id": None,
            "persisted_snapshot": {
                "question_id": question["id"],
                "question_snapshot": question,
            },
            "questions": edited_live_question,
        }
        client = _RecordingClient({"practice_session_items": [item]})

        items = adaptive_practice._load_session_items(client, "warm-grading-session")
        selected_fields = [
            operation[1]
            for operation in client.queries[0].operations
            if operation[0] == "select"
        ][0]
        with (
            patch.object(adaptive_practice, "_load_session_items", return_value=items),
            patch.object(
                adaptive_practice,
                "warm_submission_questions",
                wraps=answer_service.warm_submission_questions,
            ) as warm,
        ):
            view = adaptive_practice._select_and_insert_next(
                object(),
                "user-1",
                {
                    "id": "warm-grading-session",
                    "requested_question_count": 10,
                },
        )

        self.assertIn("question_snapshot", selected_fields)
        self.assertIn("answer:user_answers", selected_fields)
        self.assertIn("practice_session_item_question_snapshots!inner", selected_fields)
        warmed_question = warm.call_args.args[0][0]
        self.assertEqual(warmed_question["answer"], "A")
        self.assertEqual(warmed_question["explanation"], "解析 warm-grading-question")
        self.assertEqual(
            warm.call_args.kwargs,
            {
                "practice_session_item_id": "warm-grading-item",
                "user_id": "user-1",
            },
        )
        self.assertIsNone(view["question"]["answer"])
        self.assertIsNone(view["question"]["explanation"])
        self.assertEqual(view["question"]["stem"], question["stem"])

        class _NoQuestionReadClient:
            def __init__(self):
                self.rpc_name = None

            def rpc(self, name, _payload):
                self.rpc_name = name
                return self

            def execute(self):
                if self.rpc_name != "assert_single_answer_feedback_allowed":
                    raise AssertionError(f"unexpected grading rpc: {self.rpc_name}")
                return _Response(True)

            def table(self, table_name):
                raise AssertionError(f"unexpected grading database read: {table_name}")

        no_read_client = _NoQuestionReadClient()
        cached = answer_service.get_submission_question_or_404(
            no_read_client,
            question["id"],
            practice_session_item_id=item["id"],
            user_id="user-1",
        )
        self.assertEqual(no_read_client.rpc_name, "assert_single_answer_feedback_allowed")
        self.assertEqual(cached["answer"], "A")
        self.assertEqual(cached["explanation"], "解析 warm-grading-question")

    def test_candidate_cache_isolated_by_exam_subject_and_scope(self):
        client = _RecordingClient({"questions": [_question("question-1", 2)]})
        sessions = [
            self._session(),
            self._session(exam_code="Z002", subject="数学基础"),
            self._session(scopes=[{"module": "模块二", "submodule": "考点二"}]),
        ]

        for session in sessions:
            adaptive_practice._fetch_candidate_questions(client, session)

        self.assertEqual(len(client.queries), 3)

    def test_candidate_cache_is_bounded_and_expires(self):
        self.assertEqual(adaptive_practice.CANDIDATE_CACHE_MAX_ENTRIES, 8)
        client = _RecordingClient({"questions": [_question("question-1", 2)]})
        first = self._session()
        second = self._session(scopes=[{"module": "模块二", "submodule": "考点二"}])
        with patch.object(adaptive_practice, "CANDIDATE_CACHE_MAX_ENTRIES", 1):
            adaptive_practice._fetch_candidate_questions(client, first)
            adaptive_practice._fetch_candidate_questions(client, second)
            adaptive_practice._fetch_candidate_questions(client, first)
        self.assertEqual(len(client.queries), 3)

        adaptive_practice._clear_candidate_caches()
        client.queries.clear()
        with patch.object(adaptive_practice, "CANDIDATE_CACHE_TTL_SECONDS", 0):
            adaptive_practice._fetch_candidate_questions(client, first)
            adaptive_practice._fetch_candidate_questions(client, first)
        self.assertEqual(len(client.queries), 2)

    def test_calibration_cache_reuses_scope_read_and_returns_defensive_copy(self):
        session = self._session()
        client = _RecordingClient(
            {
                "question_calibration": [
                    {
                        "question_id": "question-1",
                        "stats_exam_code": "Z001",
                        "quality_status": "APPROVED",
                        "quality_weight": 0.9,
                    }
                ]
            }
        )

        first = adaptive_practice._load_candidate_calibration_map(
            client,
            session,
            ["question-1"],
        )
        first["question-1"]["quality_weight"] = 0.1
        second = adaptive_practice._load_candidate_calibration_map(
            client,
            dict(session),
            ["question-1"],
        )

        self.assertEqual(len(client.queries), 1)
        self.assertEqual(second["question-1"]["quality_weight"], 0.9)

    def test_trusted_candidate_revalidation_enforces_current_review_contract(self):
        session = self._session()

        def row(**overrides):
            question = _question("question-1", 2)
            payload = {
                "question_id": "question-1",
                "stats_exam_code": "Z001",
                "quality_status": "APPROVED",
                "quality_weight": 0.7,
                "is_diagnostic_candidate": True,
                "questions": {**question, "status": "active"},
            }
            payload.update(overrides)
            return payload

        valid_client = _RecordingClient({"question_calibration": [row()]})
        self.assertTrue(
            adaptive_practice._selected_trusted_candidate_is_current(
                valid_client,
                session=session,
                question_id="question-1",
                expected_difficulty=2,
                require_diagnostic_candidate=True,
            )
        )

        verify_client = _RecordingClient(
            {
                "question_calibration": [
                    row(is_diagnostic_candidate=False)
                ]
            }
        )
        self.assertTrue(
            adaptive_practice._selected_trusted_candidate_is_current(
                verify_client,
                session=session,
                question_id="question-1",
                expected_difficulty=2,
                require_diagnostic_candidate=False,
            )
        )

        for revoked in (
            row(quality_status="FLAGGED"),
            row(quality_weight=0.69),
            row(is_diagnostic_candidate=False),
            row(questions={**_question("question-1", 2), "status": "inactive"}),
        ):
            revoked_client = _RecordingClient(
                {"question_calibration": [revoked]}
            )
            self.assertFalse(
                adaptive_practice._selected_trusted_candidate_is_current(
                    revoked_client,
                    session=session,
                    question_id="question-1",
                    expected_difficulty=2,
                    require_diagnostic_candidate=True,
                )
            )

    def test_global_seen_is_candidate_bounded_and_crosses_exam_scopes(self):
        client = _RecordingClient(
            {
                "user_question_progress": [
                    {
                        "question_id": "question-1",
                        "stats_exam_code": "Z001",
                    },
                    {
                        "question_id": "outside",
                        "stats_exam_code": "Z002",
                    },
                ]
            }
        )
        candidate_ids = ["question-1", *[f"candidate-{index}" for index in range(449)]]

        seen = adaptive_practice._load_ever_answered_question_ids(
            client,
            "user-1",
            "逻辑推理",
            candidate_ids,
        )

        self.assertEqual(seen, {"question-1"})
        self.assertEqual(len(client.queries), 3)
        for query in client.queries:
            operations = query.operations
            self.assertEqual(query.table_name, "user_question_progress")
            self.assertIn(("eq", "user_id", "user-1"), operations)
            self.assertIn(("eq", "questions.subject", "逻辑推理"), operations)
            self.assertFalse(
                any(operation[:2] == ("eq", "stats_exam_code") for operation in operations)
            )
            candidate_filter = next(operation for operation in operations if operation[0] == "in")
            self.assertLessEqual(
                len(candidate_filter[2]),
                adaptive_practice.HISTORY_LOOKUP_BATCH_SIZE,
            )
            self.assertFalse(any(operation[0] == "range" for operation in operations))

    def test_due_review_is_candidate_bounded_inside_exact_exam_subject_scope(self):
        client = _RecordingClient(
            {
                "user_question_progress": [
                    {
                        "question_id": "question-1",
                        "stats_exam_code": "Z002",
                        "correct_count": 0,
                        "last_is_correct": False,
                        "last_answered_at": "2026-09-01T00:00:00Z",
                    },
                    {
                        "question_id": "outside",
                        "stats_exam_code": "Z001",
                        "correct_count": 0,
                        "last_is_correct": False,
                        "last_answered_at": "2026-09-01T00:00:00Z",
                    },
                ]
            }
        )
        candidate_ids = ["question-1", *[f"candidate-{index}" for index in range(449)]]

        values = adaptive_practice._load_due_review_values(
            client,
            "user-1",
            "Z002",
            "英语运用",
            candidate_ids,
        )

        self.assertEqual(values, {"question-1": 1.0})
        self.assertEqual(len(client.queries), 3)
        for query in client.queries:
            operations = query.operations
            self.assertIn(("eq", "user_id", "user-1"), operations)
            self.assertIn(("eq", "stats_exam_code", "Z002"), operations)
            self.assertIn(("eq", "questions.subject", "英语运用"), operations)
            self.assertTrue(any(operation[0] == "in" for operation in operations))
            self.assertFalse(any(operation[0] == "range" for operation in operations))

    def test_candidate_history_hot_path_is_one_rpc_at_maximum_pool_size(self):
        client = _RpcClient(
            response={
                "recent_question_ids": ["recent-question"],
                "ever_answered_question_ids": ["candidate-1", "outside"],
                "progress_rows": [
                    {
                        "question_id": "candidate-1",
                        "stats_exam_code": "Z001",
                        "correct_count": 0,
                        "last_is_correct": False,
                        "last_answered_at": "2026-09-01T00:00:00Z",
                    },
                    {
                        "question_id": "candidate-2",
                        "stats_exam_code": "Z002",
                        "correct_count": 0,
                        "last_is_correct": False,
                        "last_answered_at": "2026-09-01T00:00:00Z",
                    },
                ],
            }
        )
        candidate_ids = [
            f"candidate-{index}" for index in range(adaptive_practice.MAX_CANDIDATE_ROWS)
        ]

        history = adaptive_practice._load_candidate_history_snapshot(
            client,
            user_id="user-1",
            exam_code="Z001",
            subject="逻辑推理",
            question_ids=candidate_ids,
            include_global_seen=True,
        )

        self.assertEqual(client.execute_count, 1)
        self.assertEqual(client.rpc_name, "get_adaptive_candidate_history_v1")
        self.assertEqual(client.rpc_payload["p_user_id"], "user-1")
        self.assertEqual(client.rpc_payload["p_stats_exam_code"], "Z001")
        self.assertEqual(client.rpc_payload["p_subject"], "逻辑推理")
        self.assertEqual(len(client.rpc_payload["p_question_ids"]), 3000)
        self.assertEqual(history["recent_question_ids"], {"recent-question"})
        self.assertEqual(history["ever_answered_question_ids"], {"candidate-1"})
        self.assertEqual(history["due_review_values"], {"candidate-1": 1.0})

    def test_candidate_history_missing_rpc_fallback_has_fixed_query_ceiling(self):
        historical_answers = [
            {"question_id": f"old-history-{index}"} for index in range(1500)
        ]
        client = _RecordingClient(
            {
                "user_answers": historical_answers,
                "user_question_progress": [],
            }
        )
        candidate_ids = [
            f"candidate-{index}" for index in range(adaptive_practice.MAX_CANDIDATE_ROWS)
        ]

        with patch.object(
            adaptive_practice,
            "_load_candidate_history_via_rpc",
            side_effect=RuntimeError(
                "PGRST202 Could not find the function in the schema cache"
            ),
        ):
            adaptive_practice._load_candidate_history_snapshot(
                client,
                user_id="user-1",
                exam_code="Z002",
                subject="数学基础",
                question_ids=candidate_ids,
                include_global_seen=True,
            )

        expected_progress_queries = (
            adaptive_practice.MAX_CANDIDATE_ROWS
            + adaptive_practice.HISTORY_LOOKUP_BATCH_SIZE
            - 1
        ) // adaptive_practice.HISTORY_LOOKUP_BATCH_SIZE
        self.assertEqual(len(client.queries), 1 + expected_progress_queries)
        self.assertEqual(client.queries[0].table_name, "user_answers")
        self.assertIn(
            ("limit", adaptive_practice.RECENT_QUESTION_LIMIT),
            client.queries[0].operations,
        )
        for query in client.queries[1:]:
            self.assertEqual(query.table_name, "user_question_progress")
            self.assertFalse(any(operation[0] == "range" for operation in query.operations))


class AdaptiveDiagnosticPoolTests(unittest.TestCase):
    def setUp(self):
        adaptive_practice._clear_candidate_caches()

    def test_d4_gate_pages_past_seen_candidates_and_uses_diagnostic_filters(self):
        def calibration(question_id: str) -> dict:
            question = _question(question_id, 4)
            return {
                "question_id": question_id,
                "stats_exam_code": "Z001",
                "quality_status": "APPROVED",
                "quality_weight": 1.0,
                "is_diagnostic_candidate": True,
                "diagnostic_priority": 100,
                "questions": question,
            }

        client = _RecordingClient(
            {
                "question_calibration": [
                    calibration("seen-1"),
                    calibration("seen-2"),
                    calibration("fresh-on-next-page"),
                ]
            }
        )
        session = {
            "stats_exam_code": "Z001",
            "subject": "逻辑推理",
            "scope_filter": [{"module": "模块一"}],
        }
        with (
            patch.object(adaptive_practice, "PAGE_SIZE", 2),
            patch.object(
                adaptive_practice,
                "_load_ever_answered_question_ids",
                side_effect=[{"seen-1", "seen-2"}, set()],
            ),
        ):
            found = adaptive_practice._find_fresh_approved_diagnostic_d4(
                client,
                user_id="user-1",
                session=session,
            )

        self.assertEqual(found[0]["id"], "fresh-on-next-page")
        self.assertEqual(len(client.queries), 2)
        operations = client.queries[0].operations
        selected_fields = next(
            operation[1] for operation in operations if operation[0] == "select"
        )
        self.assertIn(("eq", "quality_status", "APPROVED"), operations)
        self.assertIn(("eq", "is_diagnostic_candidate", True), operations)
        self.assertIn(("gte", "quality_weight", 0.7), operations)
        self.assertIn(("eq", "questions.difficulty", 4), operations)
        self.assertIn(("eq", "questions.status", "active"), operations)
        self.assertIn(("eq", "questions.exam_code", "Z001"), operations)
        self.assertIn("answer,explanation", selected_fields)

    def test_cold_start_gate_requires_fresh_approved_d4(self):
        session = {
            "stats_exam_code": "Z001",
            "subject": "逻辑推理",
            "scope_filter": [{"module": "模块一", "submodule": "考点一"}],
        }
        question = _question("diagnostic-d4", 4)
        calibration = {
            "diagnostic-d4": {
                "quality_status": "APPROVED",
                "quality_weight": 1.0,
                "is_diagnostic_candidate": True,
            }
        }
        with (
            patch.object(
                adaptive_practice,
                "_find_fresh_approved_diagnostic_d4",
                return_value=None,
            ),
            patch.object(adaptive_practice, "_fetch_candidate_questions", return_value=[question]),
            patch.object(adaptive_practice, "_load_calibration_map", return_value=calibration),
            patch.object(
                adaptive_practice,
                "_load_ever_answered_question_ids",
                return_value={"diagnostic-d4"},
            ),
        ):
            with self.assertRaises(HTTPException) as raised:
                adaptive_practice._prepare_initial_diagnostic_pool(
                    object(),
                    user_id="user-1",
                    session=session,
                )
        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(
            raised.exception.detail["code"],
            "ADAPTIVE_DIAGNOSTIC_POOL_UNAVAILABLE",
        )

    def test_cold_start_gate_reuses_validated_candidate_reads(self):
        session = {
            "stats_exam_code": "Z001",
            "subject": "逻辑推理",
            "scope_filter": [{"module": "模块一", "submodule": "考点一"}],
        }
        question = _question("diagnostic-d4", 4)
        calibration = {
            "diagnostic-d4": {
                "quality_status": "APPROVED",
                "quality_weight": 0.7,
                "is_diagnostic_candidate": True,
            }
        }
        with (
            patch.object(
                adaptive_practice,
                "_find_fresh_approved_diagnostic_d4",
                return_value=(question, calibration["diagnostic-d4"]),
            ),
            patch.object(adaptive_practice, "_fetch_candidate_questions", return_value=[question]),
            patch.object(adaptive_practice, "_load_calibration_map", return_value=calibration),
            patch.object(adaptive_practice, "_load_ever_answered_question_ids", return_value=set()),
        ):
            adaptive_practice._prepare_initial_diagnostic_pool(
                object(),
                user_id="user-1",
                session=session,
            )
        self.assertEqual(session["_prefetched_candidate_questions"], [question])
        self.assertEqual(session["_prefetched_calibrations"], calibration)

    def test_cold_start_gate_injects_d4_found_beyond_general_candidate_cap(self):
        session = {
            "stats_exam_code": "Z001",
            "subject": "逻辑推理",
            "scope_filter": [{"module": "模块一", "submodule": "考点一"}],
        }
        ordinary = _question("ordinary-d2", 2)
        diagnostic = _question("late-approved-d4", 4)
        diagnostic_calibration = {
            "question_id": "late-approved-d4",
            "quality_status": "APPROVED",
            "quality_weight": 1.0,
            "is_diagnostic_candidate": True,
        }
        with (
            patch.object(
                adaptive_practice,
                "_find_fresh_approved_diagnostic_d4",
                return_value=(diagnostic, diagnostic_calibration),
            ),
            patch.object(
                adaptive_practice,
                "_fetch_candidate_questions",
                return_value=[ordinary],
            ),
            patch.object(adaptive_practice, "_load_calibration_map", return_value={}),
            patch.object(adaptive_practice, "_load_ever_answered_question_ids", return_value=set()),
        ):
            adaptive_practice._prepare_initial_diagnostic_pool(
                object(),
                user_id="user-1",
                session=session,
            )

        self.assertEqual(
            [question["id"] for question in session["_prefetched_candidate_questions"]],
            ["ordinary-d2", "late-approved-d4"],
        )
        self.assertEqual(
            session["_prefetched_calibrations"]["late-approved-d4"],
            diagnostic_calibration,
        )

    def test_client_session_id_reuse_rejects_changed_scope_or_preferences(self):
        existing = {
            "stats_exam_code": "Z001",
            "subject": "逻辑推理",
            "mode": "special",
            "scope_filter": [{"module": "模块一", "submodule": "考点一"}],
            "requested_question_count": 8,
            "user_preference": "standard",
            "strategy_config": {"accepted_challenge": False},
            "state_snapshot": {
                "diagnostic_status": "NEW",
                "reliable_first_attempt_count": 0,
            },
        }
        changed = CreateAdaptivePracticeSessionRequest(
            exam_code="Z001",
            subject="逻辑推理",
            practice_mode="special",
            scopes=[{"module": "模块二", "submodule": "考点二"}],
            preference="challenge",
        )
        with self.assertRaises(HTTPException) as raised:
            adaptive_practice._assert_idempotent_session_matches(
                existing,
                payload=changed,
                exam_code="Z001",
                subject="逻辑推理",
            )
        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(raised.exception.detail["code"], "ADAPTIVE_SESSION_ID_CONFLICT")


class ScopedReadTests(unittest.TestCase):
    def test_answer_history_filters_exam_and_subject_before_pagination(self):
        client = _RecordingClient()
        result = answer_service.list_answer_history(
            client,
            "user-1",
            exam_code="Z002",
            subject="英语运用",
            limit=30,
            offset=0,
        )
        self.assertEqual(result, {"items": [], "count": 0})
        operations = client.queries[0].operations
        self.assertIn(("eq", "stats_exam_code", "Z002"), operations)
        self.assertIn(("eq", "questions.subject", "英语运用"), operations)
        range_index = next(index for index, operation in enumerate(operations) if operation[0] == "range")
        self.assertLess(operations.index(("eq", "stats_exam_code", "Z002")), range_index)
        self.assertLess(operations.index(("eq", "questions.subject", "英语运用")), range_index)

    def test_question_progress_reads_only_requested_exam_scope(self):
        client = _RecordingClient()
        rows = question_routes.fetch_user_question_progress_rows(client, "user-1", "Z002")
        self.assertEqual(rows, [])
        self.assertIn(
            ("eq", "stats_exam_code", "Z002"),
            client.queries[0].operations,
        )

    def test_omitted_exam_code_resolves_from_user_profile(self):
        client = _RecordingClient(rows={"users": [{"exam_target": "Z002"}]})
        self.assertEqual(answer_service.resolve_user_exam_code(client, "user-1", None), "Z002")
        self.assertIn(("eq", "id", "user-1"), client.queries[0].operations)


if __name__ == "__main__":
    unittest.main()
