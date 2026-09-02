from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from scripts import regenerate_common_culture_explanation_v3 as runner


def build_question(index: int, *, subject: str = runner.SUBJECT) -> dict[str, object]:
    return {
        "id": f"question-{index:02d}",
        "exam_code": "COMMON",
        "subject": subject,
        "module": "中国哲学常识",
        "submodule": "儒家",
        "question_type": "single_choice",
        "stem": f"固定题干 {index}",
        "option_a": f"选项 A{index}",
        "option_b": f"选项 B{index}",
        "option_c": f"选项 C{index}",
        "option_d": f"选项 D{index}",
        "answer": "A",
        "difficulty": 2,
        "source_type": "fixture",
        "source_year": None,
        "passage_id": None,
        "explanation": "旧解析不得进入候选更新",
        "status": "active",
        "review_status": "approved",
    }


def write_snapshot(path: Path, questions: list[dict[str, object]]) -> None:
    payload = {
        "snapshot_version": "test",
        "read_only_source": True,
        "database_writes": 0,
        "question_count": len(questions),
        "questions": questions,
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def accepted_result(rows, *, model: str = "fake-model") -> dict[str, object]:
    accepted = []
    for row in rows:
        rendered = dict(row)
        rendered["explanation"] = f"新解析 {row['id']}"
        accepted.append(
            {
                "id": row["id"],
                "question": rendered,
                "culture_v3": {"version": "3.0", "fixture_id": row["id"]},
                "audit": {
                    "valid_for_generation": True,
                    "blocking_codes": [],
                    "issues": [],
                },
            }
        )
    return {
        "accepted": accepted,
        "rejected": [],
        "expected_count": len(rows),
        "response_count": len(rows),
        "model": model,
    }


class SimulatedCrash(BaseException):
    pass


class CommonCultureExplanationV3RegenerationRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.snapshot = self.root / "snapshot.json"
        self.checkpoint = self.root / "checkpoint.json"
        self.output = self.root / "candidates.json"
        self.report = self.root / "review.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_pipeline(self, **kwargs):
        return asyncio.run(
            runner.run_regeneration(
                snapshot_path=self.snapshot,
                checkpoint_path=self.checkpoint,
                output_path=self.output,
                report_path=self.report,
                **kwargs,
            )
        )

    def test_default_service_boundary_uses_fixed_six_question_batches_and_narrow_updates(self):
        culture_questions = [build_question(index) for index in range(1, 9)]
        outside_subject = build_question(99, subject="英语运用")
        write_snapshot(self.snapshot, [*culture_questions, outside_subject])
        calls: list[tuple[list[str], dict[str, list[str]]]] = []

        async def fake_service(rows, *, feedback_by_id):
            calls.append(([str(row["id"]) for row in rows], dict(feedback_by_id)))
            return accepted_result(rows)

        with patch.object(
            runner,
            "regenerate_culture_explanation_batch",
            new=AsyncMock(side_effect=fake_service),
        ) as mocked_service:
            candidate, report = self.run_pipeline(limit=7, max_attempts=2)

        self.assertEqual([len(ids) for ids, _ in calls], [runner.BATCH_SIZE, 1])
        self.assertEqual(mocked_service.await_count, 2)
        self.assertNotIn(outside_subject["id"], {item for ids, _ in calls for item in ids})
        self.assertEqual(candidate["selected_count"], 7)
        self.assertEqual(candidate["accepted_count"], 7)
        self.assertEqual(candidate["rejected_count"], 0)
        self.assertIs(candidate["ready_for_publish"], False)
        self.assertEqual(candidate["database_writes"], 0)
        self.assertEqual(
            [update["id"] for update in candidate["updates"]],
            [question["id"] for question in culture_questions[:7]],
        )
        for update in candidate["updates"]:
            self.assertEqual(set(update), {"id", "culture_v3"})

        self.assertEqual(report["summary"]["batch_call_count"], 2)
        self.assertEqual(report["summary"]["accepted_count"], 7)
        self.assertIs(report["ready_for_publish"], False)
        self.assertEqual(report["database_writes"], 0)
        checkpoint = json.loads(self.checkpoint.read_text(encoding="utf-8"))
        self.assertEqual(checkpoint["run_status"], "completed")
        self.assertEqual(checkpoint["batch_size"], 6)
        for question, item in zip(culture_questions[:7], checkpoint["items"]):
            self.assertEqual(item["baseline_sha256"], runner.baseline_sha256(question))
            self.assertTrue(item["baseline_verified"])

    def test_static_rejection_feedback_is_replayed_and_each_question_has_own_attempt_count(self):
        questions = [build_question(1), build_question(2)]
        write_snapshot(self.snapshot, questions)
        seen_feedback: list[dict[str, list[str]]] = []
        call_number = 0

        async def retrying_service(rows, *, feedback_by_id):
            nonlocal call_number
            call_number += 1
            seen_feedback.append(dict(feedback_by_id))
            if call_number == 1:
                accepted = accepted_result([rows[1]])["accepted"]
                return {
                    "accepted": accepted,
                    "rejected": [
                        {
                            "id": rows[0]["id"],
                            "codes": ["culture_v3_bridge_is_answer_echo"],
                            "reasons": ["bridge 只是答案复述，请补出具体中间事实"],
                        }
                    ],
                    "model": "fake-model",
                }
            self.assertEqual([row["id"] for row in rows], [questions[0]["id"]])
            self.assertIn(questions[0]["id"], feedback_by_id)
            self.assertIn("具体中间事实", feedback_by_id[questions[0]["id"]][0])
            return accepted_result(rows)

        candidate, report = self.run_pipeline(
            max_attempts=3,
            batch_generator=retrying_service,
        )

        self.assertEqual(call_number, 2)
        self.assertEqual(seen_feedback[0], {})
        self.assertEqual(candidate["accepted_count"], 2)
        by_id = {item["id"]: item for item in report["items"]}
        self.assertEqual(by_id[questions[0]["id"]]["attempts"], 2)
        self.assertEqual(by_id[questions[1]["id"]]["attempts"], 1)
        self.assertEqual(by_id[questions[0]["id"]]["failure_count"], 1)
        self.assertEqual(report["summary"]["retried_question_count"], 1)
        self.assertEqual(report["summary"]["feedback_replayed_count"], 1)

    def test_retry_ceiling_exhausts_question_without_database_or_publish_readiness(self):
        question = build_question(1)
        write_snapshot(self.snapshot, [question])
        call_count = 0

        async def always_rejected(rows, *, feedback_by_id):
            nonlocal call_count
            call_count += 1
            return {
                "accepted": [],
                "rejected": [
                    {
                        "id": rows[0]["id"],
                        "codes": ["culture_v3_static_gate"],
                        "reasons": [f"第 {call_count} 次仍未通过"],
                        "culture_v3": {"version": "3.0", "attempt": call_count},
                    }
                ],
                "model": "fake-model",
            }

        candidate, report = self.run_pipeline(
            max_attempts=2,
            batch_generator=always_rejected,
        )

        self.assertEqual(call_count, 2)
        self.assertEqual(candidate["updates"], [])
        self.assertEqual(candidate["accepted_count"], 0)
        self.assertEqual(candidate["rejected_count"], 1)
        self.assertIs(candidate["ready_for_publish"], False)
        self.assertEqual(candidate["database_writes"], 0)
        self.assertEqual(report["items"][0]["state"], "exhausted")
        self.assertEqual(report["items"][0]["attempts"], 2)
        self.assertEqual(report["items"][0]["failure_count"], 2)
        self.assertEqual(
            report["items"][0]["last_rejected_culture_v3"],
            {"version": "3.0", "attempt": 2},
        )
        self.assertEqual(report["summary"]["feedback_replayed_count"], 1)
        self.assertEqual(report["summary"]["feedback_replayed_question_count"], 1)

    def test_non_static_failure_without_candidate_preserves_saved_static_candidate(self):
        saved_metadata = {"version": "3.0", "saved": "static-candidate"}
        cases = (
            ("regeneration_batch_call_failed", "batch_call_failed"),
            ("regeneration_batch_result_invalid", "generation_contract_failed"),
            ("regeneration_interrupted_attempt", "interrupted_attempt"),
        )

        for code, expected_category in cases:
            with self.subTest(code=code):
                item = {
                    "id": "question-01",
                    "state": "pending",
                    "attempts": 3,
                    "feedback": [],
                    "failures": [],
                    "culture_v3": None,
                    "audit": None,
                    "in_flight": {"call_index": 3, "attempt": 3},
                    "last_rejected_culture_v3": dict(saved_metadata),
                }

                runner._apply_failure(
                    item,
                    {
                        "id": item["id"],
                        "codes": [code],
                        "reasons": ["本次失败没有返回新候选"],
                    },
                    max_attempts=3,
                )

                self.assertEqual(item["state"], "exhausted")
                self.assertEqual(item["terminal_category"], expected_category)
                self.assertEqual(item["last_failure_category"], expected_category)
                self.assertEqual(item["last_rejected_culture_v3"], saved_metadata)
                self.assertEqual(item["failures"][-1]["codes"], [code])

    def test_reaudit_saved_static_rejection_promotes_without_model_call_or_new_attempt(self):
        question = build_question(1)
        write_snapshot(self.snapshot, [question])
        saved_metadata = {"version": "3.0", "saved": "candidate"}

        async def rejected_once(rows, *, feedback_by_id):
            return {
                "accepted": [],
                "rejected": [
                    {
                        "id": rows[0]["id"],
                        "codes": ["culture_v3_bridge_is_answer_echo"],
                        "reasons": ["旧静态门拒收"],
                        "culture_v3": saved_metadata,
                    }
                ],
                "model": "fake-model",
            }

        candidate, report = self.run_pipeline(
            max_attempts=1,
            batch_generator=rejected_once,
        )
        self.assertEqual(candidate["accepted_count"], 0)
        self.assertEqual(report["items"][0]["failure_count"], 1)

        def passing_reaudit(content, questions_by_id):
            payload = json.loads(content)
            update = payload["updates"][0]
            row = dict(questions_by_id[question["id"]])
            row["explanation"] = "由当前静态门重新渲染的解析"
            return {
                "accepted": [
                    {
                        "id": question["id"],
                        "question": row,
                        "culture_v3": update["culture_v3"],
                        "audit": {
                            "valid_for_generation": True,
                            "blocking_codes": [],
                            "issues": [],
                        },
                    }
                ],
                "rejected": [],
            }

        generator = AsyncMock(side_effect=AssertionError("reaudit must not call provider"))
        with patch.object(
            runner,
            "parse_culture_explanation_regeneration_response",
            side_effect=passing_reaudit,
        ):
            candidate, report = self.run_pipeline(
                resume=True,
                reaudit_rejected=True,
                batch_generator=generator,
            )

        generator.assert_not_awaited()
        self.assertEqual(candidate["accepted_count"], 1)
        self.assertEqual(candidate["rejected_count"], 0)
        self.assertEqual(candidate["updates"][0]["culture_v3"], saved_metadata)
        item = report["items"][0]
        self.assertEqual(item["attempts"], 1)
        self.assertEqual(item["failure_count"], 1)
        self.assertEqual(item["accepted_via"], "saved_candidate_static_reaudit")
        self.assertEqual(report["summary"]["batch_call_count"], 1)
        self.assertEqual(report["summary"]["static_reaudit_event_count"], 1)
        self.assertEqual(report["summary"]["static_reaudit_passed_count"], 1)
        checkpoint = json.loads(self.checkpoint.read_text(encoding="utf-8"))
        self.assertEqual(checkpoint["items"][0]["state"], "accepted")
        self.assertEqual(checkpoint["static_reaudit_events"][0]["result"], "passed")

    def test_reaudit_rejected_requires_resume_before_checkpoint_creation(self):
        write_snapshot(self.snapshot, [build_question(1)])
        generator = AsyncMock()

        with self.assertRaisesRegex(ValueError, "requires --resume"):
            self.run_pipeline(
                reaudit_rejected=True,
                batch_generator=generator,
            )

        generator.assert_not_awaited()
        self.assertFalse(self.checkpoint.exists())

    def test_reaudit_all_demotes_stale_accepted_candidate_without_model_call(self):
        question = build_question(1)
        write_snapshot(self.snapshot, [question])
        candidate, report = self.run_pipeline(
            max_attempts=1,
            batch_generator=AsyncMock(return_value=accepted_result([question])),
        )
        self.assertEqual(candidate["accepted_count"], 1)
        self.assertEqual(report["items"][0]["failure_count"], 0)

        def rejecting_reaudit(content, questions_by_id):
            update = json.loads(content)["updates"][0]
            return {
                "accepted": [],
                "rejected": [
                    {
                        "id": update["id"],
                        "codes": ["culture_v3_option_fact_adds_unsupported_limit"],
                        "reasons": ["错项 fact 擅自增加选项未表达的范围限制"],
                        "culture_v3": update["culture_v3"],
                    }
                ],
            }

        generator = AsyncMock(side_effect=AssertionError("reaudit-all must not call provider"))
        with patch.object(
            runner,
            "parse_culture_explanation_regeneration_response",
            side_effect=rejecting_reaudit,
        ):
            candidate, report = self.run_pipeline(
                resume=True,
                reaudit_all=True,
                batch_generator=generator,
            )

        generator.assert_not_awaited()
        self.assertEqual(candidate["accepted_count"], 0)
        self.assertEqual(candidate["rejected_count"], 1)
        item = report["items"][0]
        self.assertEqual(item["state"], "exhausted")
        self.assertEqual(item["attempts"], 1)
        self.assertEqual(item["failure_count"], 0)
        self.assertEqual(item["terminal_category"], "static_gate_failed")
        self.assertEqual(
            item["last_rejected_culture_v3"],
            {"version": "3.0", "fixture_id": question["id"]},
        )
        self.assertEqual(report["summary"]["batch_call_count"], 1)
        self.assertEqual(report["summary"]["static_reaudit_demoted_count"], 1)

    def test_memory_gate_migration_requeues_only_new_gate_failure_with_one_local_grant(self):
        question = build_question(1)
        write_snapshot(self.snapshot, [question])
        self.run_pipeline(
            max_attempts=1,
            batch_generator=AsyncMock(side_effect=lambda rows, **_: accepted_result(rows)),
        )

        def memory_only_reaudit(content, questions_by_id):
            update = json.loads(content)["updates"][0]
            return {
                "accepted": [],
                "rejected": [
                    {
                        "id": question["id"],
                        "codes": [runner.MEMORY_GATE_REQUIRED_CODE],
                        "reasons": ["本题存在明确的同维度对比记忆价值，不能省略记忆方法"],
                        "culture_v3": update["culture_v3"],
                    }
                ],
            }

        generator = AsyncMock(side_effect=AssertionError("migration must not call provider"))
        with patch.object(
            runner,
            "parse_culture_explanation_regeneration_response",
            side_effect=memory_only_reaudit,
        ):
            candidate, report = self.run_pipeline(
                resume=True,
                migrate_memory_gate=True,
                batch_generator=generator,
            )

        generator.assert_not_awaited()
        self.assertEqual(candidate["accepted_count"], 0)
        self.assertEqual(candidate["rejected_count"], 0)
        self.assertFalse(candidate["complete"])
        item = report["items"][0]
        self.assertEqual(item["state"], "pending")
        self.assertEqual(item["attempts"], 1)
        self.assertEqual(item["failure_count"], 0)
        self.assertEqual(item["migration_extra_attempts_granted"], 1)
        self.assertTrue(item["memory_gate_migration_pending"])
        self.assertEqual(report["summary"]["memory_gate_migration_requeued_count"], 1)
        self.assertEqual(
            report["summary"]["memory_gate_migration_extra_attempt_granted_count"],
            1,
        )

        candidate, report = self.run_pipeline(
            resume=True,
            batch_generator=AsyncMock(side_effect=lambda rows, **_: accepted_result(rows)),
        )
        self.assertEqual(candidate["accepted_count"], 1)
        self.assertEqual(report["items"][0]["attempts"], 2)
        self.assertEqual(report["items"][0]["failure_count"], 0)
        self.assertFalse(report["items"][0]["memory_gate_migration_pending"])

    def test_returned_question_mutation_is_rejected_by_immutable_field_lock(self):
        question = build_question(1)
        write_snapshot(self.snapshot, [question])

        async def mutating_service(rows, *, feedback_by_id):
            result = accepted_result(rows)
            result["accepted"][0]["question"]["stem"] = "模型改写后的题干"
            return result

        candidate, report = self.run_pipeline(
            max_attempts=1,
            batch_generator=mutating_service,
        )

        self.assertEqual(candidate["updates"], [])
        failure = report["items"][0]["failures"][0]
        self.assertIn("regeneration_immutable_field_changed", failure["codes"])
        self.assertIn("stem", failure["reasons"][0])
        self.assertEqual(report["baseline_lock"]["immutable_field_failure_count"], 1)

    def test_resume_uses_pre_call_atomic_attempt_checkpoint_without_restarting(self):
        question = build_question(1)
        write_snapshot(self.snapshot, [question])

        async def crashing_service(rows, *, feedback_by_id):
            raise SimulatedCrash("process stopped after attempt was reserved")

        with self.assertRaises(SimulatedCrash):
            self.run_pipeline(
                max_attempts=3,
                batch_generator=crashing_service,
            )

        checkpoint = json.loads(self.checkpoint.read_text(encoding="utf-8"))
        self.assertEqual(checkpoint["items"][0]["attempts"], 1)
        self.assertEqual(checkpoint["items"][0]["state"], "pending")
        self.assertFalse(self.output.exists())
        self.assertFalse(self.report.exists())

        async def succeeding_service(rows, *, feedback_by_id):
            return accepted_result(rows)

        candidate, report = self.run_pipeline(
            resume=True,
            batch_generator=succeeding_service,
        )

        self.assertEqual(candidate["accepted_count"], 1)
        self.assertEqual(report["items"][0]["attempts"], 2)
        self.assertEqual(report["summary"]["batch_call_count"], 2)

    def test_resume_refuses_changed_snapshot_before_calling_generator(self):
        question = build_question(1)
        write_snapshot(self.snapshot, [question])

        async def crashing_service(rows, *, feedback_by_id):
            raise SimulatedCrash()

        with self.assertRaises(SimulatedCrash):
            self.run_pipeline(max_attempts=3, batch_generator=crashing_service)

        changed = dict(question)
        changed["stem"] = "快照已变化"
        write_snapshot(self.snapshot, [changed])
        generator = AsyncMock(return_value=accepted_result([changed]))
        with self.assertRaisesRegex(RuntimeError, "raw-file SHA-256 changed"):
            self.run_pipeline(resume=True, batch_generator=generator)
        generator.assert_not_awaited()

    def test_concurrent_resume_is_rejected_while_first_run_owns_checkpoint(self):
        question = build_question(1)
        write_snapshot(self.snapshot, [question])

        async def scenario():
            started = asyncio.Event()
            release = asyncio.Event()

            async def slow_service(rows, *, feedback_by_id):
                started.set()
                await release.wait()
                return accepted_result(rows)

            async def should_not_run(rows, *, feedback_by_id):
                self.fail("contending resume reached the batch generator")

            first = asyncio.create_task(
                runner.run_regeneration(
                    snapshot_path=self.snapshot,
                    checkpoint_path=self.checkpoint,
                    output_path=self.output,
                    report_path=self.report,
                    max_attempts=1,
                    batch_generator=slow_service,
                )
            )
            await started.wait()
            with self.assertRaisesRegex(RuntimeError, "owns checkpoint lock"):
                await runner.run_regeneration(
                    snapshot_path=self.snapshot,
                    checkpoint_path=self.checkpoint,
                    output_path=self.output,
                    report_path=self.report,
                    resume=True,
                    batch_generator=should_not_run,
                )
            release.set()
            return await first

        candidate, report = asyncio.run(scenario())
        self.assertEqual(candidate["accepted_count"], 1)
        self.assertEqual(candidate["rejected_count"], 0)
        self.assertEqual(report["summary"]["batch_call_count"], 1)

    def test_static_gate_requires_literal_true_and_empty_blockers(self):
        question = build_question(1)
        write_snapshot(self.snapshot, [question])

        async def contradictory_audit(rows, *, feedback_by_id):
            result = accepted_result(rows)
            result["accepted"][0]["audit"] = {
                "valid_for_generation": "false",
                "blocking_codes": ["culture_v3_fact_not_stable"],
                "issues": [
                    {
                        "code": "culture_v3_fact_not_stable",
                        "severity": "critical",
                    }
                ],
            }
            return result

        candidate, report = self.run_pipeline(
            max_attempts=1,
            batch_generator=contradictory_audit,
        )

        self.assertEqual(candidate["updates"], [])
        failure = report["items"][0]["failures"][0]
        self.assertIn("regeneration_static_gate_not_passed", failure["codes"])
        self.assertEqual(report["items"][0]["static_gate"], "failed")

    def test_call_failure_is_not_misreported_as_static_gate_failure_or_feedback_replay(self):
        question = build_question(1)
        write_snapshot(self.snapshot, [question])

        async def unavailable_service(rows, *, feedback_by_id):
            raise TimeoutError("fixture timeout")

        candidate, report = self.run_pipeline(
            max_attempts=1,
            batch_generator=unavailable_service,
        )

        self.assertEqual(candidate["review_gates"]["static_gate"]["failed_count"], 0)
        self.assertEqual(candidate["review_gates"]["static_gate"]["not_reached_count"], 1)
        self.assertEqual(report["items"][0]["static_gate"], "not_reached")
        self.assertEqual(report["items"][0]["terminal_category"], "batch_call_failed")
        self.assertEqual(report["summary"]["feedback_replayed_count"], 0)
        self.assertEqual(
            report["summary"]["terminal_category_counts"],
            {"batch_call_failed": 1},
        )

    def test_provider_failure_pauses_run_without_spending_later_batches_or_replaying_error(self):
        questions = [build_question(index) for index in range(1, 8)]
        write_snapshot(self.snapshot, questions)
        call_count = 0

        async def unavailable_service(rows, *, feedback_by_id):
            nonlocal call_count
            call_count += 1
            self.assertEqual(feedback_by_id, {})
            raise TimeoutError("provider temporarily unavailable")

        candidate, report = self.run_pipeline(
            max_attempts=3,
            provider="codex-cli",
            batch_generator=unavailable_service,
        )

        self.assertEqual(call_count, 1)
        self.assertFalse(candidate["complete"])
        self.assertEqual(candidate["accepted_count"], 0)
        self.assertEqual(candidate["rejected_count"], 0)
        self.assertEqual(report["summary"]["pending_count"], 7)
        self.assertEqual(report["summary"]["feedback_replayed_count"], 0)
        by_id = {item["id"]: item for item in report["items"]}
        for question in questions[:6]:
            self.assertEqual(by_id[question["id"]]["attempts"], 1)
            self.assertEqual(by_id[question["id"]]["retry_feedback"], [])
        self.assertEqual(by_id[questions[6]["id"]]["attempts"], 0)
        checkpoint = json.loads(self.checkpoint.read_text(encoding="utf-8"))
        self.assertEqual(checkpoint["run_status"], "paused_provider_error")
        self.assertEqual(checkpoint["provider"], "codex-cli")

    def test_codex_output_contract_error_retries_without_replaying_adapter_error(self):
        question = build_question(1)
        write_snapshot(self.snapshot, [question])
        call_count = 0

        async def flaky_output(rows, *, feedback_by_id):
            nonlocal call_count
            call_count += 1
            self.assertEqual(feedback_by_id, {})
            if call_count == 1:
                raise runner.CodexCLIOutputError("invalid structured output")
            return accepted_result(rows, model="codex-cli")

        candidate, report = self.run_pipeline(
            max_attempts=2,
            provider="codex-cli",
            batch_generator=flaky_output,
        )

        self.assertEqual(call_count, 2)
        self.assertEqual(candidate["accepted_count"], 1)
        self.assertEqual(report["items"][0]["attempts"], 2)
        self.assertEqual(report["items"][0]["retry_feedback"], [])
        self.assertEqual(report["summary"]["feedback_replayed_count"], 0)

    def test_resume_rejects_provider_change_before_calling_generator(self):
        question = build_question(1)
        write_snapshot(self.snapshot, [question])

        async def crashing_service(rows, *, feedback_by_id):
            raise SimulatedCrash("leave provider-locked checkpoint")

        with self.assertRaises(SimulatedCrash):
            self.run_pipeline(
                max_attempts=3,
                provider="codex-cli",
                batch_generator=crashing_service,
            )

        checkpoint = json.loads(self.checkpoint.read_text(encoding="utf-8"))
        self.assertEqual(checkpoint["provider"], "codex-cli")
        generator = AsyncMock()
        with self.assertRaisesRegex(RuntimeError, "does not match checkpoint provider"):
            self.run_pipeline(
                resume=True,
                provider="deepseek",
                batch_generator=generator,
            )
        generator.assert_not_awaited()

    def test_resume_rejects_changed_candidate_or_report_paths(self):
        question = build_question(1)
        write_snapshot(self.snapshot, [question])

        async def crashing_service(rows, *, feedback_by_id):
            raise SimulatedCrash("leave artifact-locked checkpoint")

        with self.assertRaises(SimulatedCrash):
            self.run_pipeline(max_attempts=3, batch_generator=crashing_service)

        generator = AsyncMock()
        with self.assertRaisesRegex(RuntimeError, "artifact paths do not match"):
            asyncio.run(
                runner.run_regeneration(
                    snapshot_path=self.snapshot,
                    checkpoint_path=self.checkpoint,
                    output_path=self.root / "different-candidates.json",
                    report_path=self.report,
                    resume=True,
                    batch_generator=generator,
                )
            )
        generator.assert_not_awaited()

    def test_limited_cli_selection_requires_three_independent_artifact_paths(self):
        with self.assertRaisesRegex(ValueError, "independent artifact paths"):
            runner._validate_limited_run_artifacts(
                requested_ids=None,
                limit=6,
                checkpoint_path=runner.CHECKPOINT_PATH,
                output_path=runner.CANDIDATE_PATH,
                report_path=runner.REVIEW_REPORT_PATH,
            )

        runner._validate_limited_run_artifacts(
            requested_ids=["fixed-id"],
            limit=None,
            checkpoint_path=self.checkpoint,
            output_path=self.output,
            report_path=self.report,
        )

    def test_protocol_failure_is_reported_as_contract_failure_before_static_gate(self):
        question = build_question(1)
        write_snapshot(self.snapshot, [question])

        async def malformed_service(rows, *, feedback_by_id):
            return {"accepted": "not-an-array", "rejected": []}

        candidate, report = self.run_pipeline(
            max_attempts=1,
            batch_generator=malformed_service,
        )

        self.assertEqual(candidate["review_gates"]["static_gate"]["failed_count"], 0)
        self.assertEqual(candidate["review_gates"]["static_gate"]["not_reached_count"], 1)
        item = report["items"][0]
        self.assertEqual(item["static_gate"], "not_reached")
        self.assertEqual(item["terminal_category"], "generation_contract_failed")
        self.assertIn("regeneration_batch_result_invalid", item["failures"][0]["codes"])

    def test_final_in_flight_attempt_is_audited_as_interrupted_on_resume(self):
        question = build_question(1)
        write_snapshot(self.snapshot, [question])

        async def crashing_service(rows, *, feedback_by_id):
            raise SimulatedCrash("hard stop on final attempt")

        with self.assertRaises(SimulatedCrash):
            self.run_pipeline(
                max_attempts=1,
                batch_generator=crashing_service,
            )

        generator = AsyncMock(return_value=accepted_result([question]))
        candidate, report = self.run_pipeline(
            resume=True,
            batch_generator=generator,
        )

        generator.assert_not_awaited()
        self.assertEqual(candidate["accepted_count"], 0)
        self.assertEqual(candidate["rejected_count"], 1)
        self.assertEqual(candidate["review_gates"]["static_gate"]["not_reached_count"], 1)
        item = report["items"][0]
        self.assertEqual(item["terminal_category"], "interrupted_attempt")
        self.assertIn("regeneration_interrupted_attempt", item["failures"][0]["codes"])
        self.assertEqual(report["summary"]["recovered_interrupted_attempt_count"], 1)
        self.assertEqual(report["summary"]["feedback_replayed_count"], 0)
        checkpoint = json.loads(self.checkpoint.read_text(encoding="utf-8"))
        self.assertEqual(checkpoint["batch_events"][0]["status"], "interrupted")

    def test_reaudit_all_promotes_saved_static_candidate_after_final_interruption(self):
        question = build_question(1)
        write_snapshot(self.snapshot, [question])
        call_count = 0

        async def reject_twice_then_crash(rows, *, feedback_by_id):
            nonlocal call_count
            call_count += 1
            if call_count == 3:
                raise SimulatedCrash("hard stop after two saved static candidates")
            return {
                "accepted": [],
                "rejected": [
                    {
                        "id": rows[0]["id"],
                        "codes": ["culture_v3_bridge_is_answer_echo"],
                        "reasons": [f"第 {call_count} 次静态门拒收"],
                        "culture_v3": {
                            "version": "3.0",
                            "saved_attempt": call_count,
                        },
                    }
                ],
                "model": "fake-model",
            }

        with self.assertRaises(SimulatedCrash):
            self.run_pipeline(
                max_attempts=3,
                batch_generator=reject_twice_then_crash,
            )

        saved_metadata = {"version": "3.0", "saved_attempt": 2}

        def passing_reaudit(content, questions_by_id):
            update = json.loads(content)["updates"][0]
            row = dict(questions_by_id[question["id"]])
            row["explanation"] = "中断前保存的候选已通过当前静态门"
            return {
                "accepted": [
                    {
                        "id": question["id"],
                        "question": row,
                        "culture_v3": update["culture_v3"],
                        "audit": {
                            "valid_for_generation": True,
                            "blocking_codes": [],
                            "issues": [],
                        },
                    }
                ],
                "rejected": [],
            }

        generator = AsyncMock(side_effect=AssertionError("reaudit-all must not call provider"))
        with patch.object(
            runner,
            "parse_culture_explanation_regeneration_response",
            side_effect=passing_reaudit,
        ):
            candidate, report = self.run_pipeline(
                resume=True,
                reaudit_all=True,
                batch_generator=generator,
            )

        generator.assert_not_awaited()
        self.assertEqual(candidate["accepted_count"], 1)
        self.assertEqual(candidate["rejected_count"], 0)
        self.assertEqual(candidate["updates"][0]["culture_v3"], saved_metadata)
        item = report["items"][0]
        self.assertEqual(item["state"], "accepted")
        self.assertEqual(item["attempts"], 3)
        self.assertEqual(item["failure_count"], 3)
        self.assertIn("regeneration_interrupted_attempt", item["failures"][-1]["codes"])
        self.assertIsNone(item["terminal_category"])
        self.assertEqual(item["accepted_via"], "saved_candidate_static_reaudit")
        self.assertEqual(report["summary"]["batch_call_count"], 3)
        self.assertEqual(report["summary"]["recovered_interrupted_attempt_count"], 1)
        self.assertEqual(report["summary"]["static_reaudit_passed_count"], 1)

        checkpoint = json.loads(self.checkpoint.read_text(encoding="utf-8"))
        self.assertEqual(checkpoint["batch_events"][-1]["status"], "interrupted")
        event = checkpoint["static_reaudit_events"][-1]
        self.assertEqual(event["previous_terminal_category"], "interrupted_attempt")
        self.assertEqual(event["result"], "passed")

    def test_atomic_write_preserves_previous_file_when_replace_fails(self):
        target = self.root / "atomic.json"
        target.write_text('{"old": true}\n', encoding="utf-8")

        with patch.object(runner.os, "replace", side_effect=OSError("replace failed")):
            with self.assertRaisesRegex(OSError, "replace failed"):
                runner.atomic_write_json(target, {"new": True})

        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"old": True})
        self.assertEqual(list(self.root.glob(f".{target.name}.*.tmp")), [])

    def test_explicit_ids_reject_question_outside_culture_subject(self):
        culture = build_question(1)
        english = build_question(2, subject="英语运用")
        write_snapshot(self.snapshot, [culture, english])

        with self.assertRaisesRegex(ValueError, "outside subject=中华文化"):
            self.run_pipeline(
                requested_ids=[str(english["id"])],
                batch_generator=AsyncMock(),
            )
        self.assertFalse(self.checkpoint.exists())


if __name__ == "__main__":
    unittest.main()
