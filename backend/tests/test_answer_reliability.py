from __future__ import annotations

import asyncio
import json
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.routes import admin, answers, questions, reports
from app.schemas.answers import SubmitAnswerRequest
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


class AnswerReliabilityTests(unittest.TestCase):
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

    def test_stats_exam_code_uses_requested_version_only_for_public_subjects(self):
        self.assertEqual(
            answer_service.resolve_stats_exam_code(
                object(),
                "user-1",
                {"exam_code": "Z001", "subject": "中华文化"},
                "Z002",
            ),
            "Z002",
        )
        self.assertEqual(
            answer_service.resolve_stats_exam_code(
                object(),
                "user-1",
                {"exam_code": "Z001", "subject": "逻辑推理"},
                "Z002",
            ),
            "Z001",
        )

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

    def test_responsive_submit_exposes_grade_before_starting_persistence(self):
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
            "is_first_attempt": True,
            "attempt_number": 1,
            "ability_accuracy": 100,
        }
        payload = SubmitAnswerRequest(
            question_id="question-1",
            client_submission_id="client-1",
            selected_answer="B",
            used_time=18,
            exam_code="Z001",
        )
        with (
            patch.object(answers, "get_supabase_admin", return_value=object()),
            patch.object(answers, "submit_answer", return_value=grade_result),
            patch.object(answers, "persist_answer_submission", return_value=durable_result) as persist,
        ):
            response = answers.submit_responsive(payload=payload, user_id="user-1")

            self.assertEqual(response.headers["x-gyt-grading-ready"], "1")
            self.assertEqual(response.headers["x-gyt-correct-answer"], "B")
            self.assertEqual(response.headers["x-gyt-is-correct"], "1")
            self.assertFalse(persist.called)

            async def consume_stream():
                iterator = response.body_iterator.__aiter__()
                first_chunk = await iterator.__anext__()
                self.assertEqual(first_chunk, b" ")
                self.assertFalse(persist.called)
                chunks = [first_chunk]
                async for chunk in iterator:
                    chunks.append(chunk)
                return b"".join(chunks)

            body = json.loads(asyncio.run(consume_stream()))

        persist.assert_called_once()
        self.assertTrue(body["persisted"])
        self.assertEqual(body["submission_id"], "submission-1")
        self.assertEqual(body["correct_answer"], "B")

    def test_grade_fallback_returns_feedback_without_starting_persistence(self):
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
            patch.object(answers, "persist_answer_submission") as persist,
        ):
            response = answers.grade(payload=payload, user_id="user-1")

        persist.assert_not_called()
        self.assertEqual(response.correct_answer, "B")
        self.assertFalse(response.is_correct)
        self.assertTrue(response.added_to_wrong_questions)

    def test_responsive_submit_keeps_grade_and_reports_retryable_persistence_failure(self):
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
            response = answers.submit_responsive(payload=payload, user_id="user-1")

            async def consume_stream():
                chunks = []
                async for chunk in response.body_iterator:
                    chunks.append(chunk)
                return b"".join(chunks)

            body = json.loads(asyncio.run(consume_stream()))

        self.assertEqual(response.headers["x-gyt-correct-answer"], "B")
        self.assertEqual(response.headers["x-gyt-is-correct"], "0")
        self.assertFalse(body["persisted"])
        self.assertTrue(body["persistence_retryable"])
        self.assertEqual(body["persistence_error"], "暂时不可用")

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
