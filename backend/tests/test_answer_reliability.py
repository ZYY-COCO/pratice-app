from __future__ import annotations

import asyncio
import json
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import BackgroundTasks, HTTPException

from app.main import create_app
from app.routes import admin, answers, questions, reports
from app.schemas.answers import (
    MarkUnfamiliarRequest,
    SubmitAnswerRequest,
    SubmitBatchAnswerRequest,
)
from app.services import answers as answer_service


class _Response:
    def __init__(self, data):
        self.data = data


class _RpcClient:
    def __init__(self, *, response=None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.rpc_name = None
        self.rpc_payload = None

    def rpc(self, name, payload):
        self.rpc_name = name
        self.rpc_payload = payload
        return self

    def execute(self):
        if self.error:
            raise self.error
        return _Response(self.response)


class _OrderedRpcClient:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []
        self.pending_name = None

    def rpc(self, name, payload):
        self.pending_name = name
        self.calls.append((name, payload))
        return self

    def execute(self):
        if not self.outcomes:
            raise AssertionError(f"unexpected rpc: {self.pending_name}")
        expected_name, outcome = self.outcomes.pop(0)
        if self.pending_name != expected_name:
            raise AssertionError(
                f"expected rpc {expected_name}, received {self.pending_name}"
            )
        if isinstance(outcome, Exception):
            raise outcome
        return _Response(outcome)


class _ComprehensiveEmbargoClient:
    def __init__(self):
        self.calls = []

    def rpc(self, name, payload):
        self.calls.append((name, payload))
        return self

    def execute(self):
        raise RuntimeError("adaptive_comprehensive_batch_required")

    def table(self, table_name):
        raise AssertionError(
            f"the comprehensive embargo must run before reading {table_name}"
        )


class _DeleteQuery:
    def __init__(self):
        self.deleted_ids = []

    def delete(self):
        return self

    def in_(self, _field, values):
        self.deleted_ids.extend(values)
        return self

    def execute(self):
        return _Response([{"id": value} for value in self.deleted_ids])


class _DeleteClient:
    def __init__(self):
        self.query = _DeleteQuery()

    def table(self, table_name):
        if table_name != "questions":
            raise AssertionError(f"unexpected table: {table_name}")
        return self.query


class _WeeklyAnswerQuery:
    def __init__(self):
        self.operations = []

    def select(self, fields):
        self.operations.append(("select", fields))
        return self

    def gte(self, field, value):
        self.operations.append(("gte", field, value))
        return self

    def eq(self, field, value):
        self.operations.append(("eq", field, value))
        return self

    def range(self, start, end):
        self.operations.append(("range", start, end))
        return self

    def execute(self):
        return _Response([])


class _WeeklyAnswerClient:
    def __init__(self):
        self.query = _WeeklyAnswerQuery()

    def table(self, table_name):
        if table_name != "user_answers":
            raise AssertionError(f"unexpected table: {table_name}")
        return self.query


class AnswerReliabilityTests(unittest.TestCase):
    def test_cors_exposes_responsive_grade_headers(self):
        app = create_app()
        cors = next(
            middleware
            for middleware in app.user_middleware
            if middleware.cls.__name__ == "CORSMiddleware"
        )

        self.assertEqual(
            cors.kwargs["expose_headers"],
            list(answers.RESPONSIVE_GRADE_HEADER_NAMES),
        )

    def test_responsive_grade_headers_reject_non_durable_feedback(self):
        with self.assertRaises(RuntimeError):
            answers._responsive_grade_headers(
                {
                    "persisted": False,
                    "question_id": "question-1",
                    "correct_answer": "B",
                    "is_correct": True,
                    "added_to_wrong_questions": False,
                }
            )

    def test_adaptive_grading_snapshot_cache_is_user_scoped(self):
        question_id = "snapshot-question-user-scope"
        item_id = "snapshot-item-user-scope"
        user_one_snapshot = {
            "id": question_id,
            "exam_code": "Z001",
            "subject": "逻辑推理",
            "module": "演绎推理",
            "submodule": "充分条件",
            "question_type": "single_choice",
            "difficulty": 2,
            "estimated_time_sec": 60,
            "source_type": "official",
            "answer": "A",
            "explanation": "领取版本 A",
        }
        user_two_snapshot = {
            **user_one_snapshot,
            "answer": "B",
            "explanation": "另一个用户自己的领取版本 B",
        }
        answer_service.warm_submission_questions(
            [user_one_snapshot],
            practice_session_item_id=item_id,
            user_id="user-1",
        )

        cached_client = _OrderedRpcClient(
            [("assert_single_answer_feedback_allowed", True)]
        )
        cached = answer_service.get_submission_question_or_404(
            cached_client,
            question_id,
            practice_session_item_id=item_id,
            user_id="user-1",
        )
        self.assertEqual(cached["answer"], "A")
        self.assertEqual(
            [name for name, _payload in cached_client.calls],
            ["assert_single_answer_feedback_allowed"],
        )

        other_user_client = _OrderedRpcClient(
            [
                ("assert_single_answer_feedback_allowed", True),
                ("get_adaptive_question_snapshot", user_two_snapshot),
            ]
        )
        other_user = answer_service.get_submission_question_or_404(
            other_user_client,
            question_id,
            practice_session_item_id=item_id,
            user_id="user-2",
        )
        self.assertEqual(other_user_client.calls[-1][0], "get_adaptive_question_snapshot")
        self.assertEqual(other_user_client.calls[-1][1]["p_user_id"], "user-2")
        self.assertEqual(other_user["answer"], "B")

        with self.assertRaises(HTTPException) as missing_scope:
            answer_service.get_submission_question_or_404(
                object(),
                question_id,
                practice_session_item_id=item_id,
            )
        self.assertEqual(missing_scope.exception.status_code, 409)

    def test_adaptive_grading_snapshot_cache_miss_uses_private_rpc(self):
        question_id = "snapshot-question-cross-worker"
        item_id = "snapshot-item-cross-worker"
        snapshot = {
            "id": question_id,
            "exam_code": "COMMON",
            "subject": "中华文化",
            "module": "历史",
            "submodule": "制度",
            "question_type": "single_choice",
            "difficulty": 4,
            "estimated_time_sec": 75,
            "source_type": "official",
            "answer": "C",
            "explanation": "领取时解析",
        }
        client = _OrderedRpcClient(
            [
                ("assert_single_answer_feedback_allowed", True),
                ("get_adaptive_question_snapshot", snapshot),
            ]
        )

        result = answer_service.get_submission_question_or_404(
            client,
            question_id,
            practice_session_item_id=item_id,
            user_id="user-cross-worker",
        )

        self.assertEqual(client.calls[-1][0], "get_adaptive_question_snapshot")
        self.assertEqual(client.calls[-1][1]["p_practice_session_item_id"], item_id)
        self.assertEqual(result["answer"], "C")
        self.assertEqual(result["explanation"], "领取时解析")

    def test_public_single_answer_feedback_routes_enforce_embargo_before_warm_cache(self):
        question_id = "comprehensive-feedback-embargo-question"
        item_id = "comprehensive-feedback-embargo-item"
        snapshot = {
            "id": question_id,
            "exam_code": "Z001",
            "subject": "逻辑推理",
            "module": "演绎推理",
            "submodule": "充分条件",
            "question_type": "single_choice",
            "difficulty": 2,
            "estimated_time_sec": 60,
            "source_type": "official",
            "answer": "A",
            "explanation": "综合交卷前不可见",
        }
        answer_service.warm_submission_questions([snapshot])
        answer_service.warm_submission_questions(
            [snapshot],
            practice_session_item_id=item_id,
            user_id="user-1",
        )

        for routed_name in ("grade", "submit", "mark_unfamiliar"):
            for routed_item_id in (item_id, None):
                with self.subTest(route=routed_name, item_id=routed_item_id):
                    client = _ComprehensiveEmbargoClient()
                    if routed_name == "mark_unfamiliar":
                        payload = MarkUnfamiliarRequest(
                            question_id=question_id,
                            client_submission_id="mark-client-1",
                            practice_session_item_id=routed_item_id,
                            used_time=5,
                            exam_code="Z001",
                        )
                    else:
                        payload = SubmitAnswerRequest(
                            question_id=question_id,
                            client_submission_id="answer-client-1",
                            practice_session_item_id=routed_item_id,
                            selected_answer="A",
                            used_time=5,
                            exam_code="Z001",
                        )
                    with (
                        patch.object(answers, "get_supabase_admin", return_value=client),
                        patch.object(answers, "persist_answer_submission") as persist,
                    ):
                        with self.assertRaises(HTTPException) as raised:
                            getattr(answers, routed_name)(payload=payload, user_id="user-1")

                    self.assertEqual(raised.exception.status_code, 409)
                    self.assertEqual(
                        raised.exception.detail["code"],
                        "ADAPTIVE_COMPREHENSIVE_BATCH_REQUIRED",
                    )
                    persist.assert_not_called()
                    self.assertEqual(
                        [name for name, _payload in client.calls],
                        ["assert_single_answer_feedback_allowed"],
                    )
                    self.assertEqual(
                        client.calls[0][1]["p_practice_session_item_id"],
                        routed_item_id,
                    )

    def test_responsive_grading_hot_path_skips_independent_embargo_precheck(self):
        question_id = "responsive-hot-path-question"
        snapshot = {
            "id": question_id,
            "exam_code": "Z001",
            "subject": "逻辑推理",
            "module": "演绎推理",
            "submodule": "充分条件",
            "question_type": "single_choice",
            "difficulty": 2,
            "estimated_time_sec": 60,
            "source_type": "official",
            "answer": "B",
            "explanation": "热路径缓存解析",
        }
        answer_service.warm_submission_questions([snapshot])

        result = answer_service.submit_answer(
            object(),
            user_id="user-1",
            question_id=question_id,
            selected_answer="B",
            used_time=5,
            requested_exam_code="Z001",
            include_ability_accuracy=False,
            precheck_feedback_embargo=False,
        )

        self.assertTrue(result["is_correct"])
        self.assertEqual(result["correct_answer"], "B")

    def test_public_batch_submit_enforces_question_id_embargo_before_warm_cache(self):
        question_id = "comprehensive-batch-embargo-question"
        snapshot = {
            "id": question_id,
            "exam_code": "Z001",
            "subject": "逻辑推理",
            "module": "演绎推理",
            "submodule": "充分条件",
            "question_type": "single_choice",
            "difficulty": 2,
            "estimated_time_sec": 60,
            "source_type": "official",
            "answer": "A",
            "explanation": "综合交卷前不可见",
        }
        answer_service.warm_submission_questions([snapshot])
        client = _ComprehensiveEmbargoClient()
        payload = SubmitBatchAnswerRequest(
            exam_code="Z001",
            answers=[
                {
                    "question_id": question_id,
                    "client_submission_id": "batch-answer-1",
                    "selected_answer": "A",
                    "used_time": 5,
                }
            ],
        )
        with (
            patch.object(answers, "get_supabase_admin", return_value=client),
            patch.object(answers, "persist_answer_submission") as persist,
        ):
            with self.assertRaises(HTTPException) as raised:
                answers.submit_batch(payload=payload, user_id="user-1")

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(
            raised.exception.detail["code"],
            "ADAPTIVE_COMPREHENSIVE_BATCH_REQUIRED",
        )
        persist.assert_not_called()
        self.assertEqual(
            [name for name, _payload in client.calls],
            ["assert_single_answer_feedback_allowed"],
        )
        self.assertIsNone(client.calls[0][1]["p_practice_session_item_id"])

    def test_ordinary_cached_question_is_still_graded_after_embargo_check_allows_it(self):
        question_id = "ordinary-feedback-question"
        item_id = "ordinary-feedback-item"
        snapshot = {
            "id": question_id,
            "exam_code": "Z001",
            "subject": "逻辑推理",
            "module": "演绎推理",
            "submodule": "充分条件",
            "question_type": "single_choice",
            "difficulty": 2,
            "estimated_time_sec": 60,
            "source_type": "official",
            "answer": "C",
            "explanation": "普通题解析",
        }
        answer_service.warm_submission_questions([snapshot])
        answer_service.warm_submission_questions(
            [snapshot],
            practice_session_item_id=item_id,
            user_id="user-1",
        )

        for routed_item_id in (item_id, None):
            with self.subTest(item_id=routed_item_id):
                client = _OrderedRpcClient(
                    [("assert_single_answer_feedback_allowed", True)]
                )
                result = answer_service.submit_answer(
                    client,
                    user_id="user-1",
                    question_id=question_id,
                    selected_answer="C",
                    used_time=8,
                    requested_exam_code="Z001",
                    include_ability_accuracy=False,
                    practice_session_item_id=routed_item_id,
                )
                self.assertTrue(result["is_correct"])
                self.assertEqual(result["correct_answer"], "C")
                self.assertEqual(
                    [name for name, _payload in client.calls],
                    ["assert_single_answer_feedback_allowed"],
                )

    def test_atomic_submission_uses_database_rpc_and_returns_durable_result(self):
        client = _RpcClient(response={
            "submission_id": "submission-1",
            "client_submission_id": "client-1",
            "stats_exam_code": "Z001",
            "idempotent": False,
            "persisted": True,
            "is_first_attempt": True,
            "attempt_number": 1,
            "ability_accuracy": 100,
        })
        question = {
            "id": "question-1",
            "exam_code": "Z001",
            "subject": "逻辑推理",
            "module": "演绎推理",
            "submodule": "充分条件",
            "source_type": "official",
        }
        with patch.object(answer_service, "get_supabase_admin", return_value=client):
            result = answer_service.persist_answer_submission(
                user_id="user-1",
                question=question,
                selected_answer="B",
                used_time=18,
                is_correct=True,
                client_submission_id="client-1",
            )

        self.assertEqual(client.rpc_name, "record_answer_submission")
        self.assertEqual(client.rpc_payload["p_client_submission_id"], "client-1")
        self.assertEqual(client.rpc_payload["p_used_time"], 18)
        self.assertEqual(result["submission_id"], "submission-1")
        self.assertEqual(result["stats_exam_code"], "Z001")
        self.assertEqual(result["attempt_number"], 1)
        self.assertTrue(result["is_first_attempt"])

    def test_atomic_required_submission_rejects_missing_rpc_without_compatibility_write(self):
        client = _RpcClient(
            error=RuntimeError("PGRST202 Could not find the function in the schema cache")
        )
        with patch.object(answer_service, "get_supabase_admin", return_value=client):
            with self.assertRaises(HTTPException) as raised:
                answer_service.persist_answer_submission(
                    user_id="user-1",
                    question={
                        "id": "question-1",
                        "exam_code": "Z001",
                        "subject": "逻辑推理",
                        "module": "演绎推理",
                        "submodule": "充分条件",
                    },
                    selected_answer="B",
                    used_time=18,
                    is_correct=True,
                    client_submission_id="client-1",
                    allow_compatibility_fallback=False,
                )

        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(raised.exception.detail, "作答原子持久化服务暂时不可用")

    def test_stats_exam_code_accepts_common_but_rejects_physical_cross_version_question(self):
        self.assertEqual(
            answer_service.resolve_stats_exam_code(
                object(),
                "user-1",
                {"exam_code": "COMMON", "subject": "中华文化"},
                "Z002",
            ),
            "Z002",
        )
        with self.assertRaises(HTTPException) as malformed_common:
            answer_service.resolve_stats_exam_code(
                object(),
                "user-1",
                {"exam_code": "COMMON", "subject": "逻辑推理"},
                "Z001",
            )
        self.assertEqual(malformed_common.exception.status_code, 409)
        with self.assertRaises(HTTPException) as raised:
            answer_service.resolve_stats_exam_code(
                object(),
                "user-1",
                {"exam_code": "Z001", "subject": "中华文化"},
                "Z002",
            )
        self.assertEqual(raised.exception.status_code, 409)

    def test_atomic_submission_maps_reused_key_with_different_payload_to_409(self):
        client = _RpcClient(error=RuntimeError("answer_submission_conflict"))
        with patch.object(answer_service, "get_supabase_admin", return_value=client):
            with self.assertRaises(HTTPException) as raised:
                answer_service.persist_answer_submission(
                    user_id="user-1",
                    question={
                        "id": "question-1",
                        "exam_code": "Z001",
                        "subject": "逻辑推理",
                        "module": "演绎推理",
                        "submodule": "充分条件",
                    },
                    selected_answer="A",
                    used_time=3,
                    is_correct=False,
                    client_submission_id="client-1",
                )
        self.assertEqual(raised.exception.status_code, 409)

    def test_atomic_submission_maps_comprehensive_embargo_to_public_error(self):
        client = _RpcClient(error=RuntimeError("adaptive_comprehensive_batch_required"))
        with patch.object(answer_service, "get_supabase_admin", return_value=client):
            with self.assertRaises(HTTPException) as raised:
                answer_service.persist_answer_submission(
                    user_id="user-1",
                    question={
                        "id": "question-1",
                        "exam_code": "Z001",
                        "subject": "逻辑推理",
                        "module": "演绎推理",
                        "submodule": "充分条件",
                    },
                    selected_answer="A",
                    used_time=18,
                    is_correct=False,
                    client_submission_id="client-1",
                )

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(
            raised.exception.detail["code"],
            "ADAPTIVE_COMPREHENSIVE_BATCH_REQUIRED",
        )

    def test_submit_route_waits_for_persistence_and_exposes_submission_id(self):
        grade_result = {
            "question_id": "question-1",
            "exam_code": "Z001",
            "subject": "逻辑推理",
            "module": "演绎推理",
            "submodule": "充分条件",
            "source_type": "official",
            "selected_answer": "B",
            "correct_answer": "B",
            "is_correct": True,
            "explanation": "解析",
            "added_to_wrong_questions": False,
            "ability_accuracy": None,
        }
        durable_result = {
            "submission_id": "submission-1",
            "client_submission_id": "client-1",
            "stats_exam_code": "Z001",
            "idempotent": False,
            "persisted": True,
            "selected_answer": "B",
            "correct_answer": "C",
            "is_correct": False,
            "explanation": "数据库权威解析",
            "added_to_wrong_questions": True,
            "is_first_attempt": True,
            "attempt_number": 1,
            "ability_accuracy": 100,
        }
        with (
            patch.object(answers, "get_supabase_admin", return_value=object()),
            patch.object(answers, "submit_answer", return_value=grade_result),
            patch.object(answers, "persist_answer_submission", return_value=durable_result) as persist,
        ):
            response = answers.submit(
                payload=SubmitAnswerRequest(
                    question_id="question-1",
                    client_submission_id="client-1",
                    selected_answer="B",
                    used_time=18,
                    exam_code="Z001",
                ),
                user_id="user-1",
            )

        persist.assert_called_once()
        self.assertTrue(response.persisted)
        self.assertEqual(response.submission_id, "submission-1")
        self.assertEqual(response.stats_exam_code, "Z001")
        self.assertEqual(response.attempt_number, 1)
        self.assertEqual(response.ability_accuracy, 100)
        self.assertEqual(response.correct_answer, "C")
        self.assertFalse(response.is_correct)
        self.assertEqual(response.explanation, "数据库权威解析")

    def test_responsive_submit_persists_before_feedback_and_defers_adaptive_update(self):
        grade_result = {
            "question_id": "question-1",
            "exam_code": "Z001",
            "subject": "逻辑推理",
            "module": "演绎推理",
            "submodule": "充分条件",
            "source_type": "official",
            "selected_answer": "B",
            "correct_answer": "B",
            "is_correct": True,
            "explanation": "解析",
            "added_to_wrong_questions": False,
            "ability_accuracy": None,
        }
        payload = SubmitAnswerRequest(
            question_id="question-1",
            client_submission_id="client-1",
            practice_session_item_id="practice-item-1",
            selected_answer="B",
            used_time=18,
            exam_code="Z001",
        )
        durable_result = {
            "submission_id": "submission-1",
            "client_submission_id": "client-1",
            "stats_exam_code": "Z001",
            "idempotent": False,
            "persisted": True,
            "selected_answer": "B",
            "correct_answer": "C",
            "is_correct": False,
            "explanation": "数据库权威解析",
            "added_to_wrong_questions": True,
            "is_first_attempt": True,
            "attempt_number": 1,
            "ability_accuracy": 100,
        }
        background_tasks = BackgroundTasks()
        with (
            patch.object(answers, "get_supabase_admin", return_value=object()),
            patch.object(answers, "submit_answer", return_value=grade_result) as grade_answer,
            patch.object(
                answers,
                "persist_answer_submission",
                return_value=durable_result,
            ) as persist,
            patch.object(
                answers,
                "apply_adaptive_answer_update",
                return_value={"adaptive_updated": True, "idempotent": False},
            ) as adaptive_update,
        ):
            response = answers.submit_responsive(
                payload=payload,
                background_tasks=background_tasks,
                user_id="user-1",
            )

            self.assertEqual(response.headers["x-gyt-grading-ready"], "1")
            self.assertEqual(response.headers["x-gyt-question-id"], "question-1")
            self.assertEqual(response.headers["x-gyt-correct-answer"], "C")
            self.assertEqual(response.headers["x-gyt-is-correct"], "0")
            self.assertEqual(response.headers["x-gyt-added-to-wrong-questions"], "1")
            body = json.loads(response.body.decode("utf-8"))
            adaptive_update.assert_not_called()
            asyncio.run(response.background())

        persist.assert_called_once()
        self.assertFalse(persist.call_args.kwargs["allow_compatibility_fallback"])
        self.assertFalse(grade_answer.call_args.kwargs["precheck_feedback_embargo"])
        self.assertTrue(body["persisted"])
        self.assertFalse(body["persistence_retryable"])
        self.assertIsNone(body["persistence_error"])
        self.assertEqual(body["correct_answer"], "C")
        self.assertFalse(body["is_correct"])
        self.assertEqual(body["explanation"], "数据库权威解析")
        self.assertFalse(body["adaptive"]["adaptive_updated"])
        self.assertTrue(body["adaptive"]["retryable"])
        self.assertEqual(body["adaptive"]["error"], "adaptive_state_update_pending")
        adaptive_update.assert_called_once()

    def test_grade_fallback_persists_before_returning_feedback(self):
        grade_result = {
            "question_id": "question-1",
            "exam_code": "Z001",
            "subject": "逻辑推理",
            "module": "演绎推理",
            "submodule": "充分条件",
            "source_type": "official",
            "selected_answer": "A",
            "correct_answer": "B",
            "is_correct": False,
            "explanation": "解析",
            "added_to_wrong_questions": True,
            "ability_accuracy": None,
        }
        durable_result = {
            "submission_id": "submission-1",
            "client_submission_id": "client-1",
            "stats_exam_code": "Z001",
            "idempotent": False,
            "persisted": True,
            "selected_answer": "A",
            "correct_answer": "B",
            "is_correct": False,
            "explanation": "解析",
            "added_to_wrong_questions": True,
            "is_first_attempt": True,
            "attempt_number": 1,
            "ability_accuracy": 0,
        }
        payload = SubmitAnswerRequest(
            question_id="question-1",
            client_submission_id="client-1",
            practice_session_item_id="practice-item-1",
            selected_answer="A",
            used_time=18,
            exam_code="Z001",
        )
        with (
            patch.object(answers, "get_supabase_admin", return_value=object()),
            patch.object(answers, "submit_answer", return_value=grade_result) as grade_answer,
            patch.object(
                answers,
                "persist_answer_submission",
                return_value=durable_result,
            ) as persist,
            patch.object(
                answers,
                "apply_adaptive_answer_update",
                return_value={"adaptive_updated": True, "idempotent": False},
            ) as adaptive_update,
        ):
            response = answers.grade(payload=payload, user_id="user-1")

        persist.assert_called_once()
        self.assertEqual(persist.call_args.kwargs["client_submission_id"], "client-1")
        self.assertEqual(
            persist.call_args.kwargs["practice_session_item_id"],
            "practice-item-1",
        )
        adaptive_update.assert_called_once()
        self.assertEqual(
            grade_answer.call_args.kwargs["practice_session_item_id"],
            "practice-item-1",
        )
        self.assertEqual(response.correct_answer, "B")
        self.assertFalse(response.is_correct)
        self.assertTrue(response.added_to_wrong_questions)

    def test_grade_fallback_does_not_return_feedback_when_persistence_fails(self):
        grade_result = {
            "question_id": "question-1",
            "exam_code": "Z001",
            "subject": "逻辑推理",
            "module": "演绎推理",
            "submodule": "充分条件",
            "source_type": "official",
            "selected_answer": "A",
            "correct_answer": "B",
            "is_correct": False,
            "explanation": "解析",
            "added_to_wrong_questions": True,
            "ability_accuracy": None,
        }
        payload = SubmitAnswerRequest(
            question_id="question-1",
            client_submission_id="client-1",
            selected_answer="A",
            used_time=18,
            exam_code="Z001",
        )
        with (
            patch.object(answers, "get_supabase_admin", return_value=object()),
            patch.object(answers, "submit_answer", return_value=grade_result),
            patch.object(
                answers,
                "persist_answer_submission",
                side_effect=HTTPException(status_code=503, detail="暂时不可用"),
            ),
        ):
            with self.assertRaises(HTTPException) as raised:
                answers.grade(payload=payload, user_id="user-1")

        self.assertEqual(raised.exception.status_code, 503)

    def test_grade_fallback_preserves_legacy_request_without_idempotency_key(self):
        grade_result = {
            "question_id": "question-1",
            "exam_code": "Z001",
            "subject": "逻辑推理",
            "module": "演绎推理",
            "submodule": "充分条件",
            "source_type": "official",
            "selected_answer": "B",
            "correct_answer": "B",
            "is_correct": True,
            "explanation": "解析",
            "added_to_wrong_questions": False,
            "ability_accuracy": None,
        }
        payload = SubmitAnswerRequest(
            question_id="question-1",
            selected_answer="B",
            used_time=18,
            exam_code="Z001",
        )
        durable_result = {
            **grade_result,
            "submission_id": "submission-1",
            "client_submission_id": None,
            "stats_exam_code": "Z001",
            "idempotent": False,
            "persisted": True,
            "is_first_attempt": True,
            "attempt_number": 1,
            "ability_accuracy": 100,
        }
        with (
            patch.object(answers, "get_supabase_admin", return_value=object()),
            patch.object(answers, "submit_answer", return_value=grade_result),
            patch.object(
                answers,
                "persist_answer_submission",
                return_value=durable_result,
            ) as persist,
        ):
            response = answers.grade(payload=payload, user_id="user-1")

        persist.assert_called_once()
        self.assertIsNone(persist.call_args.kwargs["client_submission_id"])
        self.assertTrue(response.is_correct)
        self.assertEqual(response.correct_answer, "B")

    def test_grade_fallback_retry_reuses_idempotency_key(self):
        grade_result = {
            "question_id": "question-1",
            "exam_code": "Z001",
            "subject": "逻辑推理",
            "module": "演绎推理",
            "submodule": "充分条件",
            "source_type": "official",
            "selected_answer": "A",
            "correct_answer": "B",
            "is_correct": False,
            "explanation": "解析",
            "added_to_wrong_questions": True,
            "ability_accuracy": None,
        }
        payload = SubmitAnswerRequest(
            question_id="question-1",
            client_submission_id="stable-client-1",
            selected_answer="A",
            used_time=18,
            exam_code="Z001",
        )
        durable_base = {
            **grade_result,
            "submission_id": "submission-1",
            "client_submission_id": "stable-client-1",
            "stats_exam_code": "Z001",
            "persisted": True,
            "is_first_attempt": True,
            "attempt_number": 1,
            "ability_accuracy": 0,
        }
        with (
            patch.object(answers, "get_supabase_admin", return_value=object()),
            patch.object(answers, "submit_answer", return_value=grade_result),
            patch.object(
                answers,
                "persist_answer_submission",
                side_effect=[
                    {**durable_base, "idempotent": False},
                    {**durable_base, "idempotent": True},
                ],
            ) as persist,
        ):
            first = answers.grade(payload=payload, user_id="user-1")
            retry = answers.grade(payload=payload, user_id="user-1")

        self.assertEqual(persist.call_count, 2)
        self.assertTrue(
            all(
                call.kwargs["client_submission_id"] == "stable-client-1"
                for call in persist.call_args_list
            )
        )
        self.assertEqual(first.correct_answer, "B")
        self.assertEqual(retry.correct_answer, "B")
        self.assertFalse(first.is_correct)
        self.assertFalse(retry.is_correct)

    def test_responsive_submit_does_not_disclose_grade_when_core_persistence_fails(self):
        grade_result = {
            "question_id": "question-1",
            "exam_code": "Z001",
            "subject": "逻辑推理",
            "module": "演绎推理",
            "submodule": "充分条件",
            "source_type": "official",
            "selected_answer": "A",
            "correct_answer": "B",
            "is_correct": False,
            "explanation": "解析",
            "added_to_wrong_questions": True,
            "ability_accuracy": None,
        }
        payload = SubmitAnswerRequest(
            question_id="question-1",
            client_submission_id="client-1",
            selected_answer="A",
            used_time=18,
            exam_code="Z001",
        )
        background_tasks = BackgroundTasks()
        with (
            patch.object(answers, "get_supabase_admin", return_value=object()),
            patch.object(answers, "submit_answer", return_value=grade_result),
            patch.object(
                answers,
                "persist_answer_submission",
                side_effect=HTTPException(status_code=503, detail="暂时不可用"),
            ),
            patch.object(answers, "_responsive_grade_headers") as grade_headers,
        ):
            with self.assertRaises(HTTPException) as raised:
                answers.submit_responsive(
                    payload=payload,
                    background_tasks=background_tasks,
                    user_id="user-1",
                )

        self.assertEqual(raised.exception.status_code, 503)
        grade_headers.assert_not_called()
        self.assertEqual(background_tasks.tasks, [])

    def test_learning_progress_uses_first_attempt_correctness(self):
        active_questions = [{"id": "question-1"}]
        wrong_then_correct = [
            {"question_id": "question-1", "is_correct": False, "created_at": "2026-08-20T08:00:00+00:00"},
            {"question_id": "question-1", "is_correct": True, "created_at": "2026-08-21T08:00:00+00:00"},
        ]
        correct_then_wrong = [
            {"question_id": "question-1", "is_correct": True, "created_at": "2026-08-20T08:00:00+00:00"},
            {"question_id": "question-1", "is_correct": False, "created_at": "2026-08-21T08:00:00+00:00"},
        ]
        with patch.object(questions, "fetch_subject_question_rows", return_value=active_questions):
            with patch.object(questions, "fetch_user_answer_rows", return_value=wrong_then_correct):
                first_wrong = questions.build_progress_summary(object(), "user-1", "Z001", "中华文化")
            with patch.object(questions, "fetch_user_answer_rows", return_value=correct_then_wrong):
                first_correct = questions.build_progress_summary(object(), "user-1", "Z001", "中华文化")

        self.assertEqual(first_wrong["mastered_questions"], 0)
        self.assertEqual(first_correct["mastered_questions"], 1)

    def test_leaderboard_reuses_timezone_fallback(self):
        fixed_timezone = timezone(timedelta(hours=8))
        with (
            patch.object(reports, "APP_TIMEZONE", fixed_timezone),
            patch.object(reports, "ZoneInfo", side_effect=AssertionError("leaderboard must not construct ZoneInfo")),
            patch.object(reports, "get_supabase_admin", return_value=object()),
            patch.object(reports, "fetch_user_profiles", return_value=[{
                "id": "user-1",
                "email": "masked@example.com",
                "phone": None,
                "nickname": "测试用户",
                "avatar_url": None,
            }]),
            patch.object(reports, "fetch_ability_rows", return_value=[{
                "user_id": "user-1",
                "total_count": 4,
                "correct_count": 3,
            }]),
            patch.object(reports, "fetch_weekly_answer_rows", return_value=[]),
        ):
            response = reports.leaderboard(_user_id="user-1", exam_code="Z001", limit=50)

        self.assertEqual(response.items[0].total_answers, 4)
        self.assertEqual(response.items[0].accuracy, 75)

    def test_leaderboard_weekly_answers_are_isolated_by_actual_exam_scope(self):
        profile = {
            "id": "user-1",
            "email": "masked@example.com",
            "phone": None,
            "nickname": "测试用户",
            "avatar_url": None,
        }
        weekly_rows = [
            {
                "user_id": "user-1",
                "stats_exam_code": "Z001",
                "questions": {"exam_code": "COMMON", "subject": "英语运用"},
            },
            {
                "user_id": "user-1",
                "stats_exam_code": "Z002",
                "questions": {"exam_code": "COMMON", "subject": "英语运用"},
            },
            {
                "user_id": "user-1",
                "stats_exam_code": "Z001",
                "questions": {"exam_code": "Z002", "subject": "中华文化"},
            },
        ]
        with (
            patch.object(reports, "get_supabase_admin", return_value=object()),
            patch.object(reports, "fetch_user_profiles", return_value=[profile]),
            patch.object(reports, "fetch_ability_rows", return_value=[]),
            patch.object(reports, "fetch_weekly_answer_rows", return_value=weekly_rows),
        ):
            z001 = reports.leaderboard(_user_id="user-1", exam_code="Z001", limit=50)
            z002 = reports.leaderboard(_user_id="user-1", exam_code="Z002", limit=50)

        self.assertEqual(z001.items[0].weekly_answers, 1)
        self.assertEqual(z002.items[0].weekly_answers, 1)

    def test_weekly_answer_query_filters_stats_scope_before_pagination(self):
        client = _WeeklyAnswerClient()
        reports.fetch_weekly_answer_rows(
            client,
            datetime(2026, 9, 1, tzinfo=timezone.utc),
            "Z002",
        )

        operations = client.query.operations
        select_operation = next(item for item in operations if item[0] == "select")
        self.assertIn("stats_exam_code", select_operation[1])
        scope_filter = ("eq", "stats_exam_code", "Z002")
        self.assertIn(scope_filter, operations)
        self.assertLess(operations.index(scope_filter), next(i for i, item in enumerate(operations) if item[0] == "range"))

    def test_public_subject_does_not_make_another_versions_private_question_common(self):
        self.assertTrue(
            reports.belongs_to_exam(
                {"exam_code": "COMMON", "subject": "中华文化"},
                "Z001",
                stats_exam_code="Z001",
            )
        )
        self.assertFalse(
            reports.belongs_to_exam(
                {"exam_code": "Z002", "subject": "中华文化"},
                "Z001",
                stats_exam_code="Z001",
            )
        )
        self.assertFalse(
            reports.belongs_to_exam(
                {"exam_code": "COMMON", "subject": "中华文化"},
                "Z001",
                stats_exam_code="Z002",
            )
        )

    def test_question_delete_blocks_referenced_learning_data(self):
        with patch.object(admin, "_find_question_reference_ids", return_value={"question-1"}):
            with self.assertRaises(HTTPException) as raised:
                admin._delete_questions_by_ids(object(), ["question-1"])
        self.assertEqual(raised.exception.status_code, 409)

    def test_question_delete_still_allows_unreferenced_records(self):
        client = _DeleteClient()
        with patch.object(admin, "_find_question_reference_ids", return_value=set()):
            deleted = admin._delete_questions_by_ids(client, ["question-1", "question-2"])
        self.assertEqual(deleted, 2)


if __name__ == "__main__":
    unittest.main()
