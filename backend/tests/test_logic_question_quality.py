from __future__ import annotations

from copy import deepcopy
import unittest

from app.services.logic_question_quality import (
    audit_logic_question,
    context_coherence_issues,
    normalize_logic_classification,
    verify_formal_spec,
)
from app.services.question_file_recognition import _normalize_excel_question
from app.services.question_catalog import normalize_and_validate_question_classification


def build_logic_question() -> dict:
    return {
        "exam_code": "Z001",
        "subject": "逻辑推理",
        "module": "推理",
        "submodule": "演绎推理",
        "question_type": "single_choice",
        "stem": "已知：如果甲参加，则乙参加；甲参加。根据上述信息，以下哪项一定成立？",
        "option_a": "乙参加",
        "option_b": "乙不参加",
        "option_c": "甲不参加",
        "option_d": "甲参加且乙不参加",
        "answer": "A",
        "explanation": "由甲参加以及“如果甲参加，则乙参加”进行肯定前件推理，可确定乙参加。B、D都与该必然结论冲突，C与已知事实冲突。",
        "difficulty": 2,
    }


def build_formal_spec() -> dict:
    return {
        "task": "must_be_true",
        "domains": {
            "甲参加": [False, True],
            "乙参加": [False, True],
        },
        "constraints": [
            {
                "id": "c1",
                "source_text": "如果甲参加，则乙参加",
                "expr": {
                    "op": "implies",
                    "if": {"op": "eq", "var": "甲参加", "value": True},
                    "then": {"op": "eq", "var": "乙参加", "value": True},
                },
            },
            {
                "id": "c2",
                "source_text": "甲参加",
                "expr": {"op": "eq", "var": "甲参加", "value": True},
            },
        ],
        "options": {
            "A": {
                "source_text": "乙参加",
                "expr": {"op": "eq", "var": "乙参加", "value": True},
            },
            "B": {
                "source_text": "乙不参加",
                "expr": {"op": "eq", "var": "乙参加", "value": False},
            },
            "C": {
                "source_text": "甲不参加",
                "expr": {"op": "eq", "var": "甲参加", "value": False},
            },
            "D": {
                "source_text": "甲参加且乙不参加",
                "expr": {
                    "op": "and",
                    "args": [
                        {"op": "eq", "var": "甲参加", "value": True},
                        {"op": "eq", "var": "乙参加", "value": False},
                    ],
                },
            },
        },
    }


def build_logic_metadata() -> dict:
    return {
        "version": "2.0",
        "logic_model": "conditional",
        "question_task": "must_be_true",
        "premise_form": ["甲参加→乙参加", "甲参加"],
        "variables": ["甲参加", "乙参加"],
        "constraints": ["如果甲参加，则乙参加", "甲参加"],
        "distractor_types": {
            "B": "否定必然结论",
            "C": "直接否定已知事实",
            "D": "保留前件但否定后件",
        },
        "source_fragment_ids": [],
        "shared_stem_id": None,
        "verification_status": "solver_verified",
        "counterexamples": {
            "B": "满足条件的唯一赋值中乙参加",
            "C": "题干已明确甲参加",
            "D": "甲参加时乙必须参加",
        },
        "difficulty_features": ["单条条件链", "一次肯定前件推理"],
        "formal_spec": build_formal_spec(),
    }


class LogicTaxonomyTests(unittest.TestCase):
    def test_legacy_taxonomy_is_normalized_jointly(self):
        self.assertEqual(normalize_logic_classification("概念判断", "判断关系"), ("判断", "判断关系"))
        self.assertEqual(normalize_logic_classification("概念判断", "概念关系"), ("概念", "概念关系"))
        self.assertEqual(normalize_logic_classification("削弱加强", "质疑"), ("论证", "削弱"))
        self.assertEqual(normalize_logic_classification("推理规则", "综合"), ("推理", "综合推理"))

    def test_excel_recognition_emits_v2_taxonomy(self):
        normalized = _normalize_excel_question(
            {
                "exam_code": "Z001",
                "subject": "逻辑",
                "module": "概念判断",
                "submodule": "判断关系",
                "stem": "题干",
                "option_a": "A. 甲",
                "option_b": "B. 乙",
                "option_c": "C. 丙",
                "option_d": "D. 丁",
                "answer": "答案A",
                "explanation": "解析",
            }
        )
        self.assertEqual(normalized["module"], "判断")
        self.assertEqual(normalized["submodule"], "判断关系")

    def test_admin_write_classification_emits_v2_taxonomy(self):
        normalized = normalize_and_validate_question_classification(
            exam_code="Z001",
            subject="逻辑推理",
            module="概念判断",
            submodule="判断种类",
        )
        self.assertEqual(normalized["module"], "判断")
        self.assertEqual(normalized["submodule"], "判断种类")


class FormalSpecTests(unittest.TestCase):
    def test_unique_answer_is_proved_by_exhaustive_enumeration(self):
        question = build_logic_question()
        options = {label: question[f"option_{label.lower()}"] for label in "ABCD"}
        result = verify_formal_spec(
            build_formal_spec(),
            answer=question["answer"],
            stem=question["stem"],
            options=options,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["state_count"], 4)
        self.assertEqual(result["solution_count"], 1)
        self.assertEqual(result["valid_labels"], ["A"])

    def test_multiple_valid_options_are_rejected(self):
        spec = build_formal_spec()
        spec["options"]["D"]["expr"] = {"op": "eq", "var": "乙参加", "value": True}
        result = verify_formal_spec(spec, answer="A")
        self.assertFalse(result["ok"])
        self.assertIn("2 valid options", result["errors"][0])

    def test_could_be_true_wrong_option_gets_a_concrete_counterexample(self):
        spec = build_formal_spec()
        spec["task"] = "could_be_true"
        result = verify_formal_spec(spec, answer="A")
        self.assertTrue(result["ok"], result["errors"])
        self.assertIsInstance(result["counterexamples"].get("B"), dict)


class ContextCoherenceTests(unittest.TestCase):
    def test_cross_domain_workflow_is_blocked_when_requested(self):
        question = build_logic_question()
        question.update(
            {
                "stem": "海关检验部门审核货物时，条件涉及四件事：接诊完成、会诊完成、治疗完成、配药完成。",
                "module": "推理",
                "submodule": "演绎推理",
            }
        )
        issues = context_coherence_issues(question)
        self.assertIn("scenario_action_mismatch", [item["code"] for item in issues])

    def test_scene_name_is_not_misread_as_a_foreign_workflow_action(self):
        question = build_logic_question()
        question.update(
            {
                "stem": (
                    "在出版社编辑部的本次排程中，五项工作覆盖周一至周五。"
                    "涉及稿件初审、事实核对、图表校正、版式检查、付印确认。"
                ),
                "module": "推理",
                "submodule": "综合推理",
            }
        )
        issues = context_coherence_issues(question)
        self.assertNotIn("scenario_action_mismatch", [item["code"] for item in issues])

    def test_process_words_are_not_group_members(self):
        question = build_logic_question()
        question.update(
            {
                "stem": "某小组把4名成员分为2组。已知：接诊编入甲组；检查编入乙组。",
                "module": "推理",
                "submodule": "综合推理",
            }
        )
        issues = context_coherence_issues(question)
        self.assertIn("process_used_as_participant", [item["code"] for item in issues])


class LogicQualityGateTests(unittest.TestCase):
    def test_complete_solver_verified_candidate_passes(self):
        result = audit_logic_question(
            build_logic_question(),
            metadata=build_logic_metadata(),
            require_v2_metadata=True,
        )
        self.assertTrue(result["valid_for_generation"], result["issues"])
        self.assertEqual(result["decision"], "keep")
        self.assertTrue(result["formal_verification"]["ok"])

    def test_missing_v2_metadata_blocks_online_generation(self):
        result = audit_logic_question(build_logic_question(), require_v2_metadata=True)
        self.assertFalse(result["valid_for_generation"])
        self.assertIn("missing_logic_v2_metadata", result["blocking_codes"])

    def test_argument_submodule_and_task_must_match(self):
        question = build_logic_question()
        question.update(
            {
                "module": "论证",
                "submodule": "加强",
                "stem": "某调查认为延长开放时间能提升到馆率。以下哪项如果为真，最能削弱上述观点？",
                "option_a": "延长时段与原时段的到馆人数相同",
                "option_b": "新增时段仅转移了原时段访客，没有增加总到馆人数",
                "option_c": "部分访客喜欢晚间到馆",
                "option_d": "图书馆同时增加了新书",
                "answer": "B",
                "explanation": "B说明延长开放只是改变到馆时间，没有提升总到馆率，直接削弱因果结论。A力度不足，C反而提供支持，D没有解释到馆率变化。",
            }
        )
        metadata = build_logic_metadata()
        metadata.update(
            {
                "logic_model": "argument_causal",
                "question_task": "weaken",
                "verification_status": "rubric_verified",
                "formal_spec": None,
                "distractor_types": {"A": "力度不足", "C": "方向相反", "D": "无关"},
                "counterexamples": {"A": "未说明总量", "C": "支持新增需求", "D": "未连接结论"},
            }
        )
        result = audit_logic_question(question, metadata=metadata, require_v2_metadata=True)
        self.assertFalse(result["valid_for_generation"])
        self.assertIn("submodule_task_mismatch", result["blocking_codes"])

    def test_low_value_distractor_requires_rewrite(self):
        question = deepcopy(build_logic_question())
        question["option_b"] = "相关记录的表格颜色发生变化。"
        result = audit_logic_question(question)
        self.assertEqual(result["decision"], "rewrite")
        self.assertIn("low_value_distractor", [issue["code"] for issue in result["issues"]])

    def test_group_count_surface_wording_must_match_formal_expression(self):
        question = build_logic_question()
        question.update(
            {
                "module": "推理",
                "submodule": "综合推理",
                "stem": "甲、乙、丙、丁分组。已知甲编入红组。以下哪项一定成立？",
                "option_a": "编入红组的成员至少有2人",
                "option_b": "编入红组的成员至多有1人",
                "option_c": "乙编入蓝组",
                "option_d": "丙不编入红组",
                "answer": "A",
                "explanation": "形式化条件显示红组至少有2名成员，因此选A。",
            }
        )
        metadata = build_logic_metadata()
        metadata.update(
            {
                "logic_model": "grouping",
                "premise_form": ["甲编入红组"],
                "variables": ["甲", "乙", "丙", "丁"],
                "constraints": ["甲编入红组"],
                "formal_spec": {
                    "task": "must_be_true",
                    "domains": {name: ["红组", "蓝组"] for name in ["甲", "乙", "丙", "丁"]},
                    "constraints": [
                        {
                            "source_text": "甲编入红组",
                            "expr": {"op": "eq", "var": "甲", "value": "红组"},
                        }
                    ],
                    "options": {
                        "A": {
                            "source_text": "编入红组的成员至少有2人",
                            "expr": {
                                "op": "count",
                                "args": [
                                    {"op": "eq", "var": name, "value": "红组"}
                                    for name in ["甲", "乙", "丙", "丁"]
                                ],
                                "comparison": "le",
                                "value": 1,
                            },
                        },
                        "B": {"source_text": "编入红组的成员至多有1人", "expr": {"op": "truthy", "var": "甲"}},
                        "C": {"source_text": "乙编入蓝组", "expr": {"op": "truthy", "var": "甲"}},
                        "D": {"source_text": "丙不编入红组", "expr": {"op": "truthy", "var": "甲"}},
                    },
                },
                "question_task": "must_be_true",
                "verification_status": "solver_verified",
                "counterexamples": {"B": "x", "C": "x", "D": "x"},
                "distractor_types": {"B": "x", "C": "x", "D": "x"},
            }
        )
        result = audit_logic_question(question, metadata=metadata, require_v2_metadata=True)
        self.assertIn("count_option_surface_mismatch", [issue["code"] for issue in result["issues"]])

    def test_invalid_categorical_middle_term_leap_requires_manual_review(self):
        question = build_logic_question()
        question.update(
            {
                "stem": "所有优秀运动员都具备坚强意志。有些具备坚强意志的人不是职业运动员。由此可以推出：",
                "option_a": "有些优秀运动员不是职业运动员",
                "option_b": "有些职业运动员不具备坚强意志",
                "option_c": "所有职业运动员都是优秀运动员",
                "option_d": "有些具备坚强意志的人不是优秀运动员",
                "answer": "A",
                "explanation": "题干把优秀运动员包含于具备坚强意志者，又据此声称部分优秀运动员不是职业运动员。",
            }
        )
        result = audit_logic_question(question)
        self.assertEqual(result["decision"], "manual_review")
        self.assertIn(
            "categorical_invalid_negative_middle_term_leap",
            [issue["code"] for issue in result["issues"]],
        )


if __name__ == "__main__":
    unittest.main()
