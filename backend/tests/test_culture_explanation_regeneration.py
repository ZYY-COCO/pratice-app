from __future__ import annotations

import json
import unittest

from app.services.culture_explanation_regeneration import (
    build_culture_explanation_regeneration_messages,
    feedback_by_id_from_rejections,
    parse_culture_explanation_regeneration_response,
)


GOLDEN_ID = "2260c050-4624-4c78-a534-d3866060a742"
SECOND_ID = "second-fixed-question"
REPLACEMENT_ID = "model-replaced-question-id"
OLD_EXPLANATION = "OLD_EXPLANATION_MUST_NEVER_REACH_THE_MODEL"


def build_question(question_id: str = GOLDEN_ID) -> dict[str, object]:
    return {
        "id": question_id,
        "exam_code": "COMMON",
        "subject": "中华文化",
        "module": "中国哲学常识",
        "submodule": "儒家",
        "question_type": "single_choice",
        "stem": "古语云“博学之，审问之，慎思之，明辨之，笃行之”，此句出自哪里？",
        "option_a": "《大学》",
        "option_b": "《中庸》",
        "option_c": "《论语》",
        "option_d": "《荀子》",
        "answer": "B",
        "difficulty": 4,
        "explanation": OLD_EXPLANATION,
    }


def build_golden_metadata() -> dict[str, object]:
    return {
        "version": "3.0",
        "question_form": "relationship_match",
        "reasoning_mode": "work_author_era",
        "fact_anchor": {
            "subject": "博学之,审问之,慎思之,明辨之,笃行之",
            "relation": "作品或典籍对应",
            "object": "《中庸》",
        },
        "reasoning_steps": {
            "clue": "博学之，审问之，慎思之，明辨之，笃行之",
            "bridge": "‘博学之、审问之、慎思之、明辨之、笃行之’见于《礼记·中庸》，概括从广学到实践的学习次序",
            "conclusion": "因此选 B“《中庸》”",
        },
        "evidence_excerpt": (
            "“博学之，审问之，慎思之，明辨之，笃行之”是一个汉语词汇，"
            "意思是要博学多才，就要对学问详细地询问，彻底搞懂，要慎重地思考，"
            "要明白地辨别"
        ),
        "knowledge_extension": "《中庸》强调学习与实践相贯通，这五个环节依次是学习、求问、思考、辨析和力行",
        "memory_strategy": "contrast",
        "memory_hook": "《中庸》—五步学习；《大学》—三纲八目",
        "option_analysis": {
            "A": {
                "verdict": "incorrect",
                "fact": "《大学》以三纲领、八条目等内容著称",
                "fit": "不是这句五步学习法的出处",
            },
            "B": {
                "verdict": "correct",
                "fact": "‘博学之、审问之、慎思之、明辨之、笃行之’见于《礼记·中庸》，概括从广学到实践的学习次序",
                "fit": "事实直接回应题干线索",
            },
            "C": {
                "verdict": "incorrect",
                "fact": "《论语》记录孔子及弟子言行，但题干整句不出自《论语》",
                "fit": "对应“《论语》”，不是“博学之，审问之”",
            },
            "D": {
                "verdict": "incorrect",
                "fact": "《荀子》也重视学习与实践，但题干引文出自《中庸》",
                "fit": "对应“《荀子》”，不是“博学之，审问之”",
            },
        },
        "scope_level": "core",
        "controversy_status": "stable",
        "verification_status": "cross_checked",
        "difficulty_features": ["作品或典籍对应", "同域选项辨析"],
    }


def response_json(*updates: dict[str, object]) -> str:
    return json.dumps({"updates": list(updates)}, ensure_ascii=False)


class CultureExplanationRegenerationTests(unittest.TestCase):
    def test_prompt_excludes_old_explanation_and_declares_narrow_output_contract(self):
        messages = build_culture_explanation_regeneration_messages([build_question()])
        prompt = "\n".join(message["content"] for message in messages)

        self.assertNotIn(OLD_EXPLANATION, prompt)
        self.assertNotIn('"explanation"', prompt)
        self.assertIn("不得改题、改选项、改答案、改分类或改难度", messages[0]["content"])
        self.assertIn("update 对象只能包含 id 和 culture_v3", messages[0]["content"])
        self.assertIn("逆向题的 clue", prompt)
        self.assertIn("不得把错误选项本身当成证据", prompt)
        self.assertIn("v3_generation_hints", prompt)
        self.assertIn("expected_reasoning_mode", prompt)
        self.assertIn("memory_strategy_requirement", prompt)
        self.assertIn('"memory_strategy_requirement":"contrast"', prompt)
        self.assertIn("rendered_display_budget", prompt)
        self.assertIn("option_fact", prompt)
        self.assertIn("每个选项只写一个短事实和一个短边界", prompt)
        self.assertIn("至少两组同维度易混映射用 contrast", prompt)
        self.assertNotIn("默认不生成记忆方法", prompt)

    def test_prompt_keeps_option_scope_in_fit_and_distinguishes_chronology_stages(self):
        messages = build_culture_explanation_regeneration_messages([build_question()])
        prompt = "\n".join(message["content"] for message in messages)

        self.assertIn("不得擅自添加选项未表达的地域、时代、对象范围", prompt)
        self.assertIn("赵国策士议论时局", prompt)
        self.assertIn("其活动局限于赵国", prompt)
        self.assertIn("选项表述范围较窄，未覆盖诸国游说", prompt)
        self.assertIn("写在 fit", prompt)
        self.assertIn("区分源起、成熟、兴盛和延续", prompt)
        self.assertIn("主要关联时代", prompt)
        self.assertIn("不得因此武断写成在某代兴起", prompt)
        self.assertIn("宜兴紫砂在明代成熟并兴盛、清代延续发展", prompt)

    def test_valid_golden_response_is_rendered_and_accepted(self):
        question = build_question()
        parsed = parse_culture_explanation_regeneration_response(
            response_json({"id": GOLDEN_ID, "culture_v3": build_golden_metadata()}),
            {GOLDEN_ID: question},
        )

        self.assertEqual(parsed["rejected"], [])
        self.assertEqual(len(parsed["accepted"]), 1)
        accepted = parsed["accepted"][0]
        self.assertEqual(accepted["id"], GOLDEN_ID)
        self.assertTrue(accepted["audit"]["valid_for_generation"])
        self.assertNotEqual(accepted["question"]["explanation"], OLD_EXPLANATION)
        self.assertIn("解题思路：", accepted["question"]["explanation"])

    def test_response_attempting_to_rewrite_question_is_rejected(self):
        parsed = parse_culture_explanation_regeneration_response(
            response_json(
                {
                    "id": GOLDEN_ID,
                    "stem": "模型擅自改写的题干",
                    "culture_v3": build_golden_metadata(),
                }
            ),
            {GOLDEN_ID: build_question()},
        )

        self.assertEqual(parsed["accepted"], [])
        self.assertEqual(
            parsed["rejected"][0]["codes"],
            ["regeneration_attempted_question_mutation"],
        )
        self.assertIn("stem", parsed["rejected"][0]["reasons"][0])

    def test_response_root_rejects_extra_question_payloads(self):
        content = json.dumps(
            {
                "updates": [
                    {"id": GOLDEN_ID, "culture_v3": build_golden_metadata()}
                ],
                "questions": [{"stem": "模型擅自改题", "answer": "A"}],
            },
            ensure_ascii=False,
        )

        with self.assertRaisesRegex(ValueError, "root 只能包含 updates"):
            parse_culture_explanation_regeneration_response(
                content,
                {GOLDEN_ID: build_question()},
            )

    def test_nested_culture_contract_rejects_unknown_payload_fields(self):
        cases = []

        top_level = build_golden_metadata()
        top_level["questions"] = [{"stem": "rewrite", "answer": "A"}]
        cases.append((top_level, "culture_v3_unknown_fields"))

        reasoning = build_golden_metadata()
        reasoning["reasoning_steps"]["answer"] = "B"
        cases.append((reasoning, "culture_v3_reasoning_steps_unknown_fields"))

        extra_option = build_golden_metadata()
        extra_option["option_analysis"]["E"] = {
            "verdict": "incorrect",
            "fact": "额外字段不得进入固定契约",
            "fit": "不属于 A-D",
        }
        cases.append((extra_option, "culture_v3_option_analysis_unknown_labels"))

        for metadata, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                parsed = parse_culture_explanation_regeneration_response(
                    response_json({"id": GOLDEN_ID, "culture_v3": metadata}),
                    {GOLDEN_ID: build_question()},
                )
                self.assertEqual(parsed["accepted"], [])
                codes = {
                    code for item in parsed["rejected"] for code in item["codes"]
                }
                self.assertIn(expected_code, codes)

    def test_duplicate_and_missing_ids_are_both_rejected(self):
        parsed = parse_culture_explanation_regeneration_response(
            response_json(
                {"id": GOLDEN_ID, "culture_v3": build_golden_metadata()},
                {"id": GOLDEN_ID, "culture_v3": build_golden_metadata()},
            ),
            {
                GOLDEN_ID: build_question(),
                SECOND_ID: build_question(SECOND_ID),
            },
        )

        rejection_codes = {
            (item["id"], code)
            for item in parsed["rejected"]
            for code in item["codes"]
        }
        self.assertIn((GOLDEN_ID, "regeneration_duplicate_id"), rejection_codes)
        self.assertIn((SECOND_ID, "regeneration_missing_id"), rejection_codes)
        self.assertEqual(parsed["accepted"], [])
        self.assertEqual(parsed["response_count"], 2)
        self.assertEqual(parsed["expected_count"], 2)

    def test_replacement_id_is_unknown_and_original_id_remains_missing(self):
        parsed = parse_culture_explanation_regeneration_response(
            response_json(
                {"id": REPLACEMENT_ID, "culture_v3": build_golden_metadata()},
            ),
            {GOLDEN_ID: build_question()},
        )

        rejection_codes = {
            (item["id"], code)
            for item in parsed["rejected"]
            for code in item["codes"]
        }
        self.assertEqual(parsed["accepted"], [])
        self.assertIn((REPLACEMENT_ID, "regeneration_unknown_id"), rejection_codes)
        self.assertIn((GOLDEN_ID, "regeneration_missing_id"), rejection_codes)

    def test_retry_feedback_is_cleaned_filtered_and_bounded(self):
        long_reason = "  " + ("x" * 300) + "  "
        rejected = [
            {"id": GOLDEN_ID, "reasons": ["  缺少具体中间事实  ", "", long_reason]},
            {"id": GOLDEN_ID, "reasons": ["缺少具体中间事实", "第二轮新原因"]},
            {"id": SECOND_ID, "reasons": [f"原因 {index}" for index in range(12)]},
            {"id": "ignored-string", "reasons": "字符串不是原因列表"},
            {"id": "", "reasons": ["没有 id 应该被忽略"]},
        ]

        feedback = feedback_by_id_from_rejections(rejected)

        self.assertEqual(feedback[GOLDEN_ID][0], "缺少具体中间事实")
        self.assertEqual(len(feedback[GOLDEN_ID][1]), 240)
        self.assertEqual(feedback[GOLDEN_ID][2], "第二轮新原因")
        self.assertEqual(feedback[SECOND_ID], [f"原因 {index}" for index in range(10)])
        self.assertNotIn("ignored-string", feedback)
        self.assertNotIn("", feedback)


if __name__ == "__main__":
    unittest.main()
