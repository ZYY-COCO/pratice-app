from __future__ import annotations

from copy import deepcopy
import unittest

from app.services.culture_explanation_v3 import (
    infer_culture_reasoning_mode,
    render_culture_explanation_v3,
)
from app.services.subject_question_quality import (
    audit_culture_question,
    audit_english_question,
    audit_math_question,
    verify_math_spec,
)


def build_culture_question() -> dict:
    return {
        "exam_code": "COMMON",
        "subject": "中华文化",
        "module": "中国哲学常识",
        "submodule": "后代学派流变",
        "question_type": "single_choice",
        "stem": "“致良知”这一命题通常与下列哪位思想家相关？",
        "option_a": "王阳明",
        "option_b": "朱熹",
        "option_c": "韩非",
        "option_d": "墨子",
        "answer": "A",
        "explanation": (
            "解题思路：致良知→王阳明把它作为心学核心命题→因此选 A“王阳明”。\n"
            "选项解析：\n"
            "A. ✓ 王阳明提出致良知。\n"
            "B. × 朱熹代表程朱理学，不是致良知的提出者。\n"
            "C. × 韩非代表法家思想，与心学命题不同。\n"
            "D. × 墨子代表墨家思想，与心学命题不同。\n"
            "知识点：王阳明心学以致良知、知行合一为核心。\n"
            "记忆方法：王阳明抓“致良知”，朱熹抓“格物致知”。"
        ),
        "difficulty": 2,
    }


def build_culture_metadata() -> dict:
    return {
        "version": "2.0",
        "question_form": "direct_identification",
        "fact_anchor": {
            "subject": "致良知",
            "relation": "思想命题提出者",
            "object": "王阳明",
            "era": "明代",
        },
        "answer_basis": "“致良知”是王阳明心学的核心命题。",
        "evidence_excerpt": "王阳明主张致良知，强调知行合一。",
        "reasoning_chain": "致良知→王阳明把它作为心学核心命题→因此选择王阳明",
        "knowledge_extension": "王阳明心学还强调知行合一，朱熹理学则强调格物致知。",
        "memory_hook": "王阳明记“致良知、知行合一”；朱熹记“格物致知”。",
        "scope_level": "core",
        "controversy_status": "stable",
        "distractor_errors": {
            "B": "朱熹是理学代表，核心命题并非致良知",
            "C": "韩非是法家代表人物",
            "D": "墨子是墨家代表人物",
        },
        "verification_status": "cross_checked",
        "difficulty_features": ["理学与心学人物混淆"],
    }


def build_culture_v3_metadata() -> dict:
    return {
        "version": "3.0",
        "question_form": "direct_identification",
        "reasoning_mode": "person_school_claim",
        "fact_anchor": {
            "subject": "致良知",
            "relation": "思想命题提出者",
            "object": "王阳明",
        },
        "reasoning_steps": {
            "clue": "“致良知”",
            "bridge": "王阳明把“致良知”作为心学核心命题",
            "conclusion": "因此选 A“王阳明”",
        },
        "evidence_excerpt": "王阳明主张致良知，并强调知行合一。",
        "knowledge_extension": "王阳明是明代心学代表，陆九渊则是南宋心学代表。",
        "memory_strategy": "contrast",
        "memory_hook": "王阳明记“致良知”，朱熹记“格物致知”。",
        "option_analysis": {
            "A": {
                "verdict": "correct",
                "fact": "王阳明以“致良知”为心学核心命题",
                "fit": "这一主张直接回应题干线索",
            },
            "B": {
                "verdict": "incorrect",
                "fact": "朱熹是程朱理学集大成者，强调格物致知",
                "fit": "人物和思想命题与题干不同",
            },
            "C": {
                "verdict": "incorrect",
                "fact": "韩非是法家代表，强调法、术、势",
                "fit": "所属学派与心学题干不同",
            },
            "D": {
                "verdict": "incorrect",
                "fact": "墨子是墨家代表，主张兼爱、非攻",
                "fit": "所属学派与心学题干不同",
            },
        },
        "scope_level": "core",
        "controversy_status": "stable",
        "verification_status": "cross_checked",
        "difficulty_features": ["理学、心学与诸子学派人物混淆"],
    }


def build_culture_v3_question() -> dict:
    question = build_culture_question()
    metadata = build_culture_v3_metadata()
    question["explanation"] = render_culture_explanation_v3(question, metadata)
    return question


def build_english_question() -> dict:
    return {
        "exam_code": "COMMON",
        "subject": "英语运用",
        "module": "语言知识",
        "submodule": "词汇",
        "question_type": "single_choice",
        "stem": "Her explanation was fully ____ with the evidence presented.",
        "option_a": "consistent",
        "option_b": "resistant",
        "option_c": "persistent",
        "option_d": "assistant",
        "answer": "A",
        "explanation": "consistent with 表示“与……一致”；其余选项不能构成符合语境的搭配。",
        "difficulty": 3,
    }


def build_english_metadata() -> dict:
    return {
        "version": "2.0",
        "skill": "vocabulary",
        "completed_sentence": "Her explanation was fully consistent with the evidence presented.",
        "answer_rationale": "consistent with 是表示与证据一致的固定搭配。",
        "distractor_errors": {
            "B": "resistant 通常表示抵抗的，语义不符",
            "C": "persistent 表示持续的，不能表达一致关系",
            "D": "assistant 是名词或形容词，词义和搭配均不符",
        },
        "verification_checks": {
            "unique_answer": True,
            "grammar": True,
            "collocation": True,
            "context_natural": True,
        },
        "verification_status": "cross_checked",
        "difficulty_features": ["近形词与固定搭配混淆"],
    }


def build_math_question() -> dict:
    return {
        "exam_code": "Z002",
        "subject": "数学基础",
        "module": "一元函数微分学",
        "submodule": "导数",
        "question_type": "single_choice",
        "stem": "设 \\(f(x)=x^2\\)，则 \\(f'(2)\\) 的值为？",
        "option_a": "\\(4\\)",
        "option_b": "\\(2\\)",
        "option_c": "\\(8\\)",
        "option_d": "\\(0\\)",
        "answer": "A",
        "explanation": "解题思路：先求导再代入。关键公式：\\((x^2)'=2x\\)。推导过程：\\(f'(2)=4\\)。答案理由：结果为4。易错点：不要把函数值当导数值。",
        "difficulty": 1,
    }


def build_math_metadata() -> dict:
    return {
        "version": "2.0",
        "problem_family": "导数值计算",
        "givens": ["函数为x的平方"],
        "required": "计算函数在2处的导数值",
        "solution_method": "先求导函数再代入自变量",
        "source_expression": "\\(f(x)=x^2\\)",
        "verification_status": "locally_verified",
        "verification_spec": {
            "kind": "derivative_value",
            "expression": "x**2",
            "variable": "x",
            "point": 2,
            "order": 1,
            "tolerance": 0.0001,
            "options": {
                "A": {"source_text": "\\(4\\)", "value": "4"},
                "B": {"source_text": "\\(2\\)", "value": "2"},
                "C": {"source_text": "\\(8\\)", "value": "8"},
                "D": {"source_text": "\\(0\\)", "value": "0"},
            },
        },
        "distractor_errors": {
            "B": "把导数值误写成自变量",
            "C": "多乘了一个自变量",
            "D": "误认为平方函数在该点导数为零",
        },
        "difficulty_features": ["求导后代入"],
    }


class CultureQuestionQualityTests(unittest.TestCase):
    def test_complete_culture_v2_candidate_passes_static_gate(self):
        result = audit_culture_question(
            build_culture_question(),
            metadata=build_culture_metadata(),
            require_v2_metadata=True,
        )
        self.assertTrue(result["valid_for_generation"], result["issues"])

    def test_complete_culture_v3_candidate_passes_and_uses_canonical_renderer(self):
        question = build_culture_v3_question()
        metadata = build_culture_v3_metadata()
        result = audit_culture_question(question, metadata=metadata, require_v2_metadata=True)
        self.assertTrue(result["valid_for_generation"], result["issues"])
        self.assertIn("解题思路：", question["explanation"])
        self.assertIn("A. ✓", question["explanation"])

    def test_culture_v3_allows_omitting_a_low_value_memory_block(self):
        question = build_culture_question()
        question.update(
            {
                "module": "中国古代科技常识",
                "submodule": "科技发明",
                "stem": "独轮车主要属于哪一方面的成就？",
                "option_a": "茶学",
                "option_b": "建筑技术",
                "option_c": "运输工具",
                "option_d": "农学",
                "answer": "C",
                "difficulty": 3,
            }
        )
        metadata = {
            "version": "3.0",
            "question_form": "direct_identification",
            "reasoning_mode": "direct_fact",
            "fact_anchor": {
                "subject": "独轮车",
                "relation": "成就所属领域",
                "object": "运输工具",
            },
            "reasoning_steps": {
                "clue": "独轮车用途",
                "bridge": "独轮车以单轮承载车架和货物，借人力推行完成搬运，功能属于陆路运输。",
                "conclusion": "因此选 C“运输工具”",
            },
            "evidence_excerpt": "独轮车是以一个车轮负重、由人推行的运输工具。",
            "knowledge_extension": "独轮车的窄车身便于在狭窄道路通行。",
            "memory_strategy": "none",
            "memory_hook": "",
            "option_analysis": {
                "A": {
                    "verdict": "incorrect",
                    "fact": "茶学涵盖茶树栽培、制茶与饮用",
                    "fit": "领域不同，并非茶事研究",
                },
                "B": {
                    "verdict": "incorrect",
                    "fact": "建筑技术关注结构营造与施工方法",
                    "fit": "用途不同，并非建筑营造",
                },
                "C": {
                    "verdict": "correct",
                    "fact": "运输工具承担人员或货物的位移",
                    "fit": "直接对应搬运功能",
                },
                "D": {
                    "verdict": "incorrect",
                    "fact": "农学研究作物栽培与农业生产",
                    "fit": "虽可农用但不属于农学成就",
                },
            },
            "scope_level": "core",
            "controversy_status": "stable",
            "verification_status": "cross_checked",
            "difficulty_features": ["需按器物功能而非使用场景归类"],
        }
        question["explanation"] = render_culture_explanation_v3(question, metadata)
        result = audit_culture_question(question, metadata=metadata, require_v2_metadata=True)
        self.assertTrue(result["valid_for_generation"], result["issues"])
        self.assertNotIn("记忆方法：", question["explanation"])

    def test_culture_v3_rejects_answer_echo_as_the_middle_reasoning_step(self):
        metadata = build_culture_v3_metadata()
        metadata["reasoning_steps"]["bridge"] = "致良知对应王阳明"
        question = build_culture_question()
        question["explanation"] = render_culture_explanation_v3(question, metadata)
        result = audit_culture_question(question, metadata=metadata, require_v2_metadata=True)
        self.assertIn("culture_v3_bridge_is_answer_echo", result["blocking_codes"])

    def test_culture_v3_rejects_generic_option_copy_and_procedural_knowledge(self):
        metadata = build_culture_v3_metadata()
        metadata["option_analysis"]["B"] = {
            "verdict": "incorrect",
            "fact": "该项不符合题干共同限定",
            "fit": "故不选",
        }
        metadata["knowledge_extension"] = "做题时可按人物和流派建立对应，再排除干扰项。"
        question = build_culture_question()
        question["explanation"] = render_culture_explanation_v3(question, metadata)
        result = audit_culture_question(question, metadata=metadata, require_v2_metadata=True)
        self.assertIn("culture_v3_option_fact_weak", result["blocking_codes"])
        self.assertIn("culture_v3_option_fit_weak", result["blocking_codes"])
        self.assertIn("culture_v3_knowledge_role_mismatch", result["blocking_codes"])

    def test_culture_v3_rejects_a_second_freehand_display_explanation(self):
        metadata = build_culture_v3_metadata()
        question = build_culture_v3_question()
        question["explanation"] = question["explanation"].replace("明代心学代表", "心学代表人物")
        result = audit_culture_question(question, metadata=metadata, require_v2_metadata=True)
        self.assertIn("culture_v3_explanation_not_canonical", result["blocking_codes"])

    def test_culture_v3_routes_common_question_families(self):
        cases = {
            "下列事件按时间先后排序正确的是：": "chronology",
            "岳麓书院位于今天哪座城市？": "place_object_mapping",
            "“格物致知”的含义是：": "concept_definition",
            "下列哪句诗表达送别之情？": "quote_meaning",
            "下列人物中不属于法家的是：": "category_comparison",
            "科举制度的主要作用是：": "institution_function",
            "《红楼梦》前八十回作者是：": "work_author_era",
            "玄奘取经产生的直接影响是：": "person_event_effect",
            "“致良知”是哪位思想家的命题？": "person_school_claim",
        }
        for stem, expected in cases.items():
            with self.subTest(stem=stem):
                self.assertEqual(infer_culture_reasoning_mode({"stem": stem}), expected)

    def test_culture_v3_rejects_a_mismatched_reasoning_route(self):
        metadata = build_culture_v3_metadata()
        metadata["reasoning_mode"] = "chronology"
        question = build_culture_question()
        question["explanation"] = render_culture_explanation_v3(question, metadata)
        result = audit_culture_question(question, metadata=metadata, require_v2_metadata=True)
        self.assertIn("culture_v3_reasoning_mode_mismatch", result["blocking_codes"])

    def test_culture_meta_language_and_missing_distractor_are_blocked(self):
        question = build_culture_question()
        question["stem"] = "依据中华文化考纲，‘致良知’对应哪位思想家？"
        metadata = build_culture_metadata()
        metadata["distractor_errors"].pop("B")
        result = audit_culture_question(question, metadata=metadata, require_v2_metadata=True)
        self.assertFalse(result["valid_for_generation"])
        self.assertIn("culture_meta_language", result["blocking_codes"])
        self.assertIn("incomplete_distractor_errors", result["blocking_codes"])

    def test_culture_v2_explanation_requires_short_first_blocks(self):
        question = build_culture_question()
        question["explanation"] = "王阳明心学以“致良知”为核心命题，因此选A。"
        result = audit_culture_question(
            question,
            metadata=build_culture_metadata(),
            require_v2_metadata=True,
        )
        self.assertFalse(result["valid_for_generation"])
        self.assertIn("culture_explanation_structure_missing", result["blocking_codes"])

    def test_culture_v2_requires_teaching_metadata_fields(self):
        metadata = build_culture_metadata()
        metadata.pop("reasoning_chain")
        result = audit_culture_question(
            build_culture_question(),
            metadata=metadata,
            require_v2_metadata=True,
        )
        self.assertFalse(result["valid_for_generation"])
        self.assertIn("incomplete_culture_v2_metadata", result["blocking_codes"])

    def test_answer_restatement_and_truncated_copy_are_blocked(self):
        question = build_culture_question()
        question["explanation"] = question["explanation"].replace(
            "致良知→王阳明把它作为心学核心命题→因此选 A“王阳明”。",
            "题干对象“致良知”→核心对应是“王阳明”→因此选 A…",
        )
        metadata = build_culture_metadata()
        metadata["reasoning_chain"] = "题干对象致良知的核心对应是王阳明…"
        result = audit_culture_question(question, metadata=metadata, require_v2_metadata=True)
        self.assertIn("culture_explanation_mechanical_template", result["blocking_codes"])
        self.assertIn("culture_explanation_truncated", result["blocking_codes"])
        self.assertIn("culture_metadata_mechanical_template", result["blocking_codes"])

    def test_knowledge_extension_must_not_repeat_reasoning_fact(self):
        metadata = build_culture_metadata()
        metadata["knowledge_extension"] = "王阳明把它作为心学核心命题"
        result = audit_culture_question(
            build_culture_question(),
            metadata=metadata,
            require_v2_metadata=True,
        )
        self.assertIn("culture_knowledge_duplicates_reasoning", result["blocking_codes"])

    def test_double_negative_statement_does_not_flip_question_direction(self):
        question = build_culture_question()
        question["stem"] = "传统文化长期积淀形成，我国传统节日无一不是从历史中发展而来。下列描述正确的是："
        result = audit_culture_question(
            question,
            metadata=build_culture_metadata(),
            require_v2_metadata=True,
        )
        self.assertNotIn("culture_question_form_mismatch", result["blocking_codes"])

    def test_visible_reasoning_chain_must_keep_clue_fact_and_conclusion(self):
        question = build_culture_question()
        question["explanation"] = question["explanation"].replace(
            "致良知→王阳明把它作为心学核心命题→因此选 A“王阳明”。",
            "致良知→王阳明心学。",
        )
        result = audit_culture_question(question, metadata=build_culture_metadata(), require_v2_metadata=True)
        self.assertIn("culture_explanation_reasoning_chain_incomplete", result["blocking_codes"])

    def test_visible_reasoning_conclusion_must_name_the_answer_once(self):
        question = build_culture_question()
        question["explanation"] = question["explanation"].replace(
            "致良知→王阳明把它作为心学核心命题→因此选 A“王阳明”。",
            "致良知→王阳明把它作为心学核心命题→由此完成判断。",
        )
        result = audit_culture_question(question, metadata=build_culture_metadata(), require_v2_metadata=True)
        self.assertIn("culture_explanation_reasoning_missing_answer", result["blocking_codes"])

        question = build_culture_question()
        question["explanation"] = question["explanation"].replace(
            "致良知→王阳明把它作为心学核心命题→因此选 A“王阳明”。",
            "致良知→王阳明把它作为心学核心命题，选 A→因此选 A“王阳明”。",
        )
        result = audit_culture_question(question, metadata=build_culture_metadata(), require_v2_metadata=True)
        self.assertIn("culture_explanation_repeated_answer_conclusion", result["blocking_codes"])

    def test_visible_option_reason_must_be_a_complete_balanced_sentence(self):
        question = build_culture_question()
        question["explanation"] = question["explanation"].replace(
            "B. × 朱熹代表程朱理学，不是致良知的提出者。",
            "B. × “朱熹代表程朱理学",
        )
        result = audit_culture_question(question, metadata=build_culture_metadata(), require_v2_metadata=True)
        self.assertIn("culture_explanation_option_reason_unfinished", result["blocking_codes"])
        self.assertIn("culture_explanation_option_broken_marks", result["blocking_codes"])

    def test_ocr_spacing_and_dense_source_lists_are_blocked(self):
        question = build_culture_question()
        question["explanation"] = question["explanation"].replace("王阳明把它", "王 阳明把它")
        metadata = build_culture_metadata()
        metadata["evidence_excerpt"] = (
            "选官制度沿革资料：秦朝：按军功授爵；汉代：实行察举征辟；"
            "魏晋南北朝：实行九品中正；隋唐：发展科举；宋元：继续调整；"
            "明代：另有变化；清代：继续沿用相关制度并形成新的制度特点。"
        )
        result = audit_culture_question(question, metadata=metadata, require_v2_metadata=True)
        self.assertIn("culture_explanation_ocr_spacing", result["blocking_codes"])
        self.assertIn("culture_metadata_dense_ocr_list", result["blocking_codes"])

    def test_legacy_culture_labels_remain_compatible(self):
        question = build_culture_question()
        question["explanation"] = (
            "为什么：题干关键词“致良知”与王阳明对应。\n"
            "关键知识：王阳明心学以致良知、知行合一为核心。\n"
            "易混辨析：\n"
            "A. 王阳明提出致良知。\n"
            "B. 朱熹代表程朱理学。\n"
            "C. 韩非代表法家思想。\n"
            "D. 墨子代表墨家思想。\n"
            "记忆提醒：王阳明抓“致良知”。"
        )
        result = audit_culture_question(
            question,
            metadata=build_culture_metadata(),
            require_v2_metadata=True,
        )
        self.assertTrue(result["valid_for_generation"], result["issues"])

    def test_reverse_question_aliases_are_checked(self):
        question = build_culture_question()
        question["stem"] = "下列说法中，不包括王阳明心学核心命题的是："
        question["answer"] = "D"
        question["explanation"] = (
            "解题思路：题干要求找例外→墨子属于墨家而非王阳明心学→因此选 D“墨子”。\n"
            "选项解析：\n"
            "A. × 王阳明提出致良知，属于心学内容，故不选。\n"
            "B. × 朱熹代表程朱理学，此项不是题干所找例外。\n"
            "C. × 韩非代表法家思想，此项不是题干所找例外。\n"
            "D. ✓ 墨子属于墨家，并非王阳明心学命题。\n"
            "知识点：王阳明心学以致良知和知行合一为核心，墨子则属于墨家。\n"
            "记忆方法：心学记王阳明，墨家记墨子；先分学派再找例外。"
        )
        metadata = build_culture_metadata()
        metadata["question_form"] = "negative_identification"
        metadata["fact_anchor"]["object"] = "墨子"
        metadata["answer_basis"] = "正确选项“墨子”不包括在王阳明心学核心命题中。"
        metadata["evidence_excerpt"] = "墨子属于墨家，并非王阳明心学命题。"
        metadata["reasoning_chain"] = "题干要求找例外→墨子属于墨家而非王阳明心学→因此选择墨子"
        metadata["knowledge_extension"] = "王阳明心学以致良知和知行合一为核心，墨子则属于墨家。"
        metadata["memory_hook"] = "心学记王阳明，墨家记墨子；先分学派再找例外。"
        metadata["distractor_errors"] = {"A": "王阳明属于心学", "B": "朱熹属于理学", "C": "韩非属于法家"}
        result = audit_culture_question(
            question,
            metadata=metadata,
            require_v2_metadata=True,
        )
        self.assertTrue(result["valid_for_generation"], result["issues"])


class EnglishQuestionQualityTests(unittest.TestCase):
    def test_complete_english_v2_candidate_passes_static_gate(self):
        result = audit_english_question(
            build_english_question(),
            metadata=build_english_metadata(),
            require_v2_metadata=True,
        )
        self.assertTrue(result["valid_for_generation"], result["issues"])

    def test_completed_sentence_mismatch_is_blocked(self):
        metadata = build_english_metadata()
        metadata["completed_sentence"] = "Her explanation was fully resistant with the evidence presented."
        result = audit_english_question(
            build_english_question(),
            metadata=metadata,
            require_v2_metadata=True,
        )
        self.assertFalse(result["valid_for_generation"])
        self.assertIn("english_completed_sentence_mismatch", result["blocking_codes"])

    def test_reading_task_is_blocked(self):
        question = build_english_question()
        question["stem"] = "According to the passage, the author ____ the proposal."
        metadata = build_english_metadata()
        metadata["completed_sentence"] = "According to the passage, the author consistent the proposal."
        result = audit_english_question(question, metadata=metadata, require_v2_metadata=True)
        self.assertIn("english_out_of_scope_task", result["blocking_codes"])


class MathQuestionQualityTests(unittest.TestCase):
    def test_complete_math_v2_candidate_is_locally_recalculated(self):
        result = audit_math_question(
            build_math_question(),
            metadata=build_math_metadata(),
            require_v2_metadata=True,
        )
        self.assertTrue(result["valid_for_generation"], result["issues"])
        self.assertTrue(result["local_verification"]["ok"])
        self.assertEqual(result["local_verification"]["valid_labels"], ["A"])

    def test_declared_math_answer_disagreeing_with_recalculation_is_blocked(self):
        question = build_math_question()
        question["answer"] = "B"
        metadata = build_math_metadata()
        metadata["distractor_errors"] = {
            "A": "正确计算结果被误列为错项",
            "C": "多乘了一个自变量",
            "D": "误认为平方函数在该点导数为零",
        }
        result = audit_math_question(question, metadata=metadata, require_v2_metadata=True)
        self.assertFalse(result["valid_for_generation"])
        self.assertIn("math_local_verification_failed", result["blocking_codes"])

    def test_derivative_spec_is_computed_without_external_dependency(self):
        options = {"A": "\\(4\\)", "B": "\\(2\\)", "C": "\\(8\\)", "D": "\\(0\\)"}
        spec = {
            "kind": "derivative_value",
            "expression": "x**2",
            "variable": "x",
            "point": 2,
            "order": 1,
            "options": {
                "A": {"source_text": "\\(4\\)", "value": "4"},
                "B": {"source_text": "\\(2\\)", "value": "2"},
                "C": {"source_text": "\\(8\\)", "value": "8"},
                "D": {"source_text": "\\(0\\)", "value": "0"},
            },
        }
        result = verify_math_spec(spec, answer="A", options=options)
        self.assertTrue(result["ok"], result["errors"])

    def test_nondifferentiable_point_is_not_mistaken_for_zero_derivative(self):
        options = {"A": "\\(0\\)", "B": "\\(1\\)", "C": "\\(-1\\)", "D": "不存在"}
        spec = {
            "kind": "derivative_value",
            "expression": "abs(x)",
            "variable": "x",
            "point": 0,
            "options": {
                "A": {"source_text": "\\(0\\)", "value": "0"},
                "B": {"source_text": "\\(1\\)", "value": "1"},
                "C": {"source_text": "\\(-1\\)", "value": "-1"},
                "D": {"source_text": "不存在", "value": "999"},
            },
        }
        result = verify_math_spec(spec, answer="A", options=options)
        self.assertFalse(result["ok"])
        self.assertTrue(any("derivatives disagree" in item for item in result["errors"]))

    def test_out_of_scope_math_topic_is_blocked(self):
        question = deepcopy(build_math_question())
        question["stem"] = "设矩阵 \\(A\\) 为二阶矩阵，求其行列式。"
        result = audit_math_question(
            question,
            metadata=build_math_metadata(),
            require_v2_metadata=True,
        )
        self.assertIn("math_out_of_scope", result["blocking_codes"])

    def test_verification_kind_must_match_math_submodule(self):
        metadata = build_math_metadata()
        metadata["verification_spec"] = {
            "kind": "numeric_expression",
            "expression": "4",
            "options": {
                "A": {"source_text": "\\(4\\)", "value": "4"},
                "B": {"source_text": "\\(2\\)", "value": "2"},
                "C": {"source_text": "\\(8\\)", "value": "8"},
                "D": {"source_text": "\\(0\\)", "value": "0"},
            },
        }
        result = audit_math_question(
            build_math_question(),
            metadata=metadata,
            require_v2_metadata=True,
        )
        self.assertIn("math_verification_kind_mismatch", result["blocking_codes"])


if __name__ == "__main__":
    unittest.main()
