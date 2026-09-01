from __future__ import annotations

import json
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from app.routes.ai import (
    _build_deepseek_messages,
    _canonicalize_generation_target,
    _fallback_target_for_subject,
    _generate_unique_question_rows,
    _safe_question_candidate,
)
from app.schemas.ai import AiTrainingTarget
from app.services.question_generation_review import (
    build_culture_explanation_review_messages,
    build_quality_review_messages,
    parse_culture_explanation_reviews,
    parse_quality_reviews,
    review_generated_question_rows,
)
from tests.test_subject_question_quality import (
    build_culture_metadata,
    build_culture_question,
    build_culture_v3_question,
    build_culture_v3_metadata,
    build_english_metadata,
    build_english_question,
    build_math_metadata,
    build_math_question,
)


def build_target(question: dict, *, question_count: int = 5) -> AiTrainingTarget:
    return AiTrainingTarget(
        subject=question["subject"],
        module=question["module"],
        submodule=question["submodule"],
        difficulty="标准提升",
        question_count=question_count,
        basis="专项训练",
    )


class AiSubjectGenerationV2Tests(unittest.TestCase):
    def test_z002_no_history_falls_back_to_math_not_logic(self):
        fallback = _fallback_target_for_subject(None, "Z002")
        self.assertEqual(fallback["subject"], "数学基础")

    def test_generation_target_rejects_invalid_manual_classification(self):
        target = AiTrainingTarget(
            subject="英语运用",
            module="阅读理解",
            submodule="阅读主旨题",
            difficulty="标准提升",
            question_count=5,
            basis="手动选择",
        )
        with self.assertRaises(HTTPException) as context:
            _canonicalize_generation_target(target, "Z001")
        self.assertEqual(context.exception.status_code, 422)

    def test_culture_candidate_prefers_culture_v3_and_keeps_v2_compatibility(self):
        question = build_culture_question()
        raw = {**question, "explanation": "", "culture_v3": build_culture_v3_metadata()}
        row, reasons = _safe_question_candidate(raw, build_target(question), "Z001")
        self.assertIsNotNone(row, reasons)
        self.assertEqual(row["exam_code"], "COMMON")
        self.assertIn("解题思路：", row["explanation"])

        raw = {**question, "culture_v2": build_culture_metadata()}
        row, reasons = _safe_question_candidate(raw, build_target(question), "Z001")
        self.assertIsNotNone(row, reasons)

        raw.pop("culture_v2")
        row, reasons = _safe_question_candidate(raw, build_target(question), "Z001")
        self.assertIsNone(row)
        self.assertTrue(any("culture_v3" in reason for reason in reasons))

    def test_english_candidate_is_forced_to_language_target_and_common_storage_code(self):
        question = build_english_question()
        raw = {**question, "english_v2": build_english_metadata()}
        row, reasons = _safe_question_candidate(raw, build_target(question), "Z002")
        self.assertIsNotNone(row, reasons)
        self.assertEqual(row["exam_code"], "COMMON")
        self.assertIsNone(row["passage_id"])

        raw["submodule"] = "语法"
        row, reasons = _safe_question_candidate(raw, build_target(question), "Z002")
        self.assertIsNone(row)
        self.assertTrue(any("偏离目标" in reason for reason in reasons))

    def test_math_candidate_requires_successful_local_recalculation(self):
        question = build_math_question()
        raw = {**question, "math_v2": build_math_metadata()}
        row, reasons = _safe_question_candidate(raw, build_target(question), "Z002")
        self.assertIsNotNone(row, reasons)
        self.assertEqual(row["exam_code"], "Z002")

        raw["math_v2"]["verification_spec"]["expression"] = "2**3"
        row, reasons = _safe_question_candidate(raw, build_target(question), "Z002")
        self.assertIsNone(row)
        self.assertTrue(any("本地复算失败" in reason for reason in reasons))

    def test_each_subject_prompt_contains_its_own_v2_contract_and_retry_feedback(self):
        cases = [
            (build_culture_question(), "culture_v3", "fact_anchor"),
            (build_english_question(), "english_v2", "completed_sentence"),
            (build_math_question(), "math_v2", "verification_spec"),
        ]
        for question, metadata_key, contract_key in cases:
            with self.subTest(subject=question["subject"]):
                messages = _build_deepseek_messages(
                    build_target(question),
                    [],
                    request_count=5,
                    quality_feedback=["上一轮答案不唯一"],
                )
                content = "\n".join(message["content"] for message in messages)
                self.assertIn(metadata_key, content)
                self.assertIn(contract_key, content)
                self.assertIn("上一轮答案不唯一", content)
                if question["subject"] == "中华文化":
                    self.assertIn("reasoning_steps", content)
                    self.assertIn("option_analysis", content)
                    self.assertIn("knowledge_extension", content)
                    self.assertIn("memory_hook", content)


class BlindQuestionReviewTests(unittest.TestCase):
    def test_review_prompt_does_not_expose_declared_answer_or_explanation(self):
        row = build_english_question()
        row["explanation"] = "SECRET_EXPLANATION"
        messages = build_quality_review_messages([row], "英语运用")
        content = "\n".join(message["content"] for message in messages)
        self.assertNotIn("SECRET_EXPLANATION", content)
        candidate_payload = content.split("候选题：", 1)[1]
        self.assertNotIn('"answer"', candidate_payload)

    def test_blind_review_accepts_only_matching_independent_answer(self):
        row = build_english_question()
        accepted, feedback, _ = parse_quality_reviews(
            json.dumps(
                {
                    "reviews": [
                        {
                            "index": 1,
                            "accept": True,
                            "independent_answer": "A",
                            "issues": [],
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            [row],
        )
        self.assertEqual(accepted, [row])
        self.assertEqual(feedback, [])

        accepted, feedback, _ = parse_quality_reviews(
            '{"reviews":[{"index":1,"accept":true,"independent_answer":"B","issues":[]}]}',
            [row],
        )
        self.assertEqual(accepted, [])
        self.assertTrue(any("不一致" in item for item in feedback))

    def test_culture_explanation_review_checks_teaching_quality_after_answer_review(self):
        row = build_culture_v3_question()
        messages = build_culture_explanation_review_messages([row])
        content = "\n".join(message["content"] for message in messages)
        candidate = json.loads(content.split("候选解析：", 1)[1])[0]
        self.assertEqual(candidate["explanation"], row["explanation"])
        self.assertIn('"answer":"A"', content)
        self.assertIn("中间文化事实", content)
        self.assertIn("记忆方法允许省略", content)

    def test_culture_explanation_review_rejection_returns_specific_feedback(self):
        row = build_culture_v3_question()
        accepted, feedback, _ = parse_culture_explanation_reviews(
            '{"reviews":[{"index":1,"accept":false,"issues":["B项只写不符合题干，没有真实知识"]}]}',
            [row],
        )
        self.assertEqual(accepted, [])
        self.assertTrue(any("没有真实知识" in item for item in feedback))


class CultureTwoStageReviewTests(unittest.IsolatedAsyncioTestCase):
    async def test_culture_requires_blind_answer_and_explanation_review(self):
        row = build_culture_v3_question()
        responses = [
            {"reply": '{"reviews":[{"index":1,"accept":true,"independent_answer":"A","issues":[]}]}', "model": "reviewer"},
            {"reply": '{"reviews":[{"index":1,"accept":true,"issues":[]}]}', "model": "reviewer"},
        ]
        with patch(
            "app.services.question_generation_review.call_deepseek_chat",
            new=AsyncMock(side_effect=responses),
        ) as mocked_review:
            accepted, feedback, payload = await review_generated_question_rows([row], "中华文化")
        self.assertEqual(accepted, [row])
        self.assertEqual(feedback, [])
        self.assertEqual(mocked_review.await_count, 2)
        self.assertIn("answer_review", payload["chunks"][0])
        self.assertIn("explanation_review", payload["chunks"][0])


class SubjectGenerationRetryTests(unittest.IsolatedAsyncioTestCase):
    async def test_blind_review_rejection_is_fed_into_next_generation_attempt(self):
        question = build_english_question()
        raw = {**question, "english_v2": build_english_metadata()}
        response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({"questions": [raw]}, ensure_ascii=False),
                    }
                }
            ]
        }
        target = build_target(question, question_count=1)

        review_calls = 0

        async def fake_review(rows: list[dict], _: str):
            nonlocal review_calls
            review_calls += 1
            if review_calls == 1:
                return [], ["二次复核答案不一致"], {"round": 1}
            return rows, [], {"round": 2}

        with (
            patch("app.routes.ai._existing_ai_fingerprints", return_value=(set(), [])),
            patch("app.routes.ai._call_deepseek", new=AsyncMock(side_effect=[response, response])) as mocked_call,
            patch("app.routes.ai.review_generated_question_rows", side_effect=fake_review),
        ):
            rows, raw_response = await _generate_unique_question_rows(None, target, "Z001", [])

        self.assertEqual(len(rows), 1)
        self.assertEqual(review_calls, 2)
        second_feedback = mocked_call.await_args_list[1].kwargs["quality_feedback"]
        self.assertIn("二次复核答案不一致", second_feedback)
        self.assertEqual(len(raw_response["generation_attempts"]), 2)
        self.assertEqual(len(raw_response["independent_review_attempts"]), 2)


if __name__ == "__main__":
    unittest.main()
