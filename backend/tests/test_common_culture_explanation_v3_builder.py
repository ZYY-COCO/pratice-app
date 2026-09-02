from __future__ import annotations

import unittest

from app.services.culture_explanation_v3 import (
    _ACTION_PREDICATE_RE,
    _INCOMPLETE_CLAUSE_END_RE,
    _OCR_SOURCE_SEAM_RE,
    _SOURCE_FRAGMENT_RE,
    _UNSAFE_KNOWLEDGE_RE,
    _UNSAFE_OPTION_FACT_RE,
    _WRONG_FIT_CONNECTOR_RE,
    _knowledge_is_grounded,
    _school_bridge_has_substantive_claim,
    _short_chronology_fit_has_date_fact,
    culture_bridge_is_grounded,
    culture_bridge_has_time_link,
    culture_memory_strategy_requirement,
    infer_culture_reasoning_mode,
    render_culture_explanation_v3,
    validate_culture_v3_contract,
)
from scripts.build_common_culture_explanation_v3 import (
    bridge_has_topic_answer_link,
    bridge_is_answer_echo,
    enumeration_incomplete,
    question_form as infer_question_form,
    sanitize_fact,
    semantic_flags,
)


def build_question(stem: str = "玄奘取经产生的直接影响是：") -> dict:
    return {
        "exam_code": "COMMON",
        "subject": "中华文化",
        "module": "中国历史学常识",
        "submodule": "中外文化交流",
        "question_type": "single_choice",
        "stem": stem,
        "option_a": "促进佛典翻译",
        "option_b": "推动远洋航海",
        "option_c": "建立早期道教组织",
        "option_d": "形成程朱理学",
        "answer": "A",
        "difficulty": 2,
    }


def build_metadata(bridge: str) -> dict:
    return {
        "version": "3.0",
        "question_form": "direct_identification",
        "reasoning_mode": "person_event_effect",
        "fact_anchor": {
            "subject": "玄奘取经",
            "relation": "直接影响",
            "object": "促进佛典翻译",
        },
        "reasoning_steps": {
            "clue": "玄奘取经",
            "bridge": bridge,
            "conclusion": "因此选 A“促进佛典翻译”",
        },
        "evidence_excerpt": "玄奘从印度带回大量佛经，回国后主持译经。",
        "knowledge_extension": "玄奘是唐代高僧，其译经活动促进了佛教经典在中国传播。",
        "memory_strategy": "contrast",
        "memory_hook": "玄奘—西行取经；鉴真—东渡传法。",
        "option_analysis": {
            "A": {
                "verdict": "correct",
                "fact": "玄奘带回大量佛经并在长安主持译经",
                "fit": "这一事迹直接推动佛典翻译",
            },
            "B": {
                "verdict": "incorrect",
                "fact": "指南针的应用推动了远洋航海",
                "fit": "对应技术传播，不是玄奘的取经活动",
            },
            "C": {
                "verdict": "incorrect",
                "fact": "五斗米道属于中国早期道教组织",
                "fit": "所属宗教传统与玄奘不同",
            },
            "D": {
                "verdict": "incorrect",
                "fact": "程朱理学形成于宋代儒学发展过程",
                "fit": "时代与思想领域均和玄奘取经不同",
            },
        },
        "scope_level": "core",
        "controversy_status": "stable",
        "verification_status": "cross_checked",
        "difficulty_features": ["佛教人物事迹辨析"],
    }


class CommonCultureExplanationV3BuilderTests(unittest.TestCase):
    def test_memory_value_gate_routes_high_confidence_cases_without_forcing_simple_facts(self):
        fixtures = (
            (
                {
                    "stem": "下列著作中，出自明代徐光启之手的是哪一项？",
                    "option_a": "《齐民要术》",
                    "option_b": "《天工开物》",
                    "option_c": "《农政全书》",
                    "option_d": "《梦溪笔谈》",
                    "answer": "C",
                },
                "contrast",
            ),
            (
                {
                    "stem": "扁鹊见蔡桓公有疾，这一事件体现了扁鹊哪个看诊手段？",
                    "option_a": "望",
                    "option_b": "闻",
                    "option_c": "问",
                    "option_d": "切",
                    "answer": "A",
                },
                "contrast",
            ),
            (
                {
                    "stem": "下列关于‘昆山腔改革’的表述，正确的是：",
                    "option_a": "唐代宫廷大曲代表",
                    "option_b": "魏良辅革新昆曲声腔",
                    "option_c": "孙过庭书论代表",
                    "option_d": "徐渭大写意花鸟代表",
                    "answer": "B",
                },
                "chain",
            ),
            (
                {
                    "stem": "重阳佳节是在农历几月几？",
                    "option_a": "五月初五",
                    "option_b": "七月十五",
                    "option_c": "八月十五",
                    "option_d": "九月初九",
                    "answer": "D",
                },
                "keyword",
            ),
            (
                {
                    "stem": "墨经力学通常归属于下列哪一学派或思想传统？",
                    "option_a": "阴阳家",
                    "option_b": "墨家",
                    "option_c": "玄学",
                    "option_d": "名家",
                    "answer": "B",
                },
                None,
            ),
            (
                {
                    "stem": "独轮车主要属于哪一方面的成就？",
                    "option_a": "茶学",
                    "option_b": "建筑技术",
                    "option_c": "运输工具",
                    "option_d": "农学",
                    "answer": "C",
                },
                None,
            ),
        )
        for question, expected in fixtures:
            with self.subTest(stem=question["stem"]):
                metadata = {"reasoning_mode": infer_culture_reasoning_mode(question)}
                self.assertEqual(
                    culture_memory_strategy_requirement(question, metadata),
                    expected,
                )

    def test_high_value_question_cannot_silently_drop_memory_card(self):
        question = build_question()
        metadata = build_metadata("玄奘西行带回大量佛经，回国后主持译经")
        metadata["memory_strategy"] = "none"
        metadata["memory_hook"] = ""
        question["explanation"] = render_culture_explanation_v3(question, metadata)

        codes = {issue["code"] for issue in validate_culture_v3_contract(question, metadata)}

        self.assertIn("culture_v3_memory_strategy_required", codes)

    def test_normal_culture_grammar_is_not_treated_as_ocr_or_procedure(self):
        normal_facts = (
            "《史记》以人物纪传为主体，贯通多个时代",
            "元杂剧《窦娥冤》的作者是关汉卿",
            "“考”“妣”分别是古代对父亲、母亲的称谓",
            "皎然是唐代诗僧，其《诗式》分门讨论诗歌创作与品评标准",
            "《千字文》正文为一千个不重复汉字",
            "《汉书·艺文志》把纵横家列为诸子十家之一",
        )
        for fact in normal_facts:
            with self.subTest(fact=fact):
                self.assertIsNone(_OCR_SOURCE_SEAM_RE.search(fact))
        self.assertIsNotNone(
            _OCR_SOURCE_SEAM_RE.search("孙思邈被称为“药王”扁鹊是战国时期医学家")
        )
        self.assertIsNotNone(
            _OCR_SOURCE_SEAM_RE.search("孙思邈被称为“药王”把扁鹊称为战国名医")
        )

        self.assertIsNone(_UNSAFE_KNOWLEDGE_RE.search("先考用于称已故父亲"))
        self.assertIsNone(_UNSAFE_KNOWLEDGE_RE.search("《资治通鉴》按年代先后编排史事"))
        self.assertIsNotNone(_UNSAFE_KNOWLEDGE_RE.search("先圈关键词，再排除错项"))

        self.assertIsNone(_INCOMPLETE_CLAUSE_END_RE.search("道家重视道、自然与清静无为"))
        self.assertIsNotNone(_INCOMPLETE_CLAUSE_END_RE.search("这部作品的代表作为"))

        self.assertIsNone(_UNSAFE_OPTION_FACT_RE.search("道家强调道法自然和无为"))
        self.assertIsNotNone(_UNSAFE_OPTION_FACT_RE.search("这项并非题干所述思想"))
        self.assertIsNone(_SOURCE_FRAGMENT_RE.search("杜牧是晚唐诗人，与李商隐并称小李杜"))
        self.assertIsNone(_SOURCE_FRAGMENT_RE.search("乃粒篇叙述稻、麦等粮食作物的生产"))
        self.assertIsNotNone(_SOURCE_FRAGMENT_RE.search("（1）杜牧是晚唐诗人"))

    def test_reasoning_router_prefers_question_semantics_over_incidental_words(self):
        self.assertEqual(
            infer_culture_reasoning_mode(
                {"stem": "三省六部制长期影响中央行政体制，其中六部不包括哪一项？"}
            ),
            "category_comparison",
        )
        self.assertEqual(
            infer_culture_reasoning_mode(
                {"stem": "哪一项最符合东晋田园诗代表人物，作品有《归园田居》？"}
            ),
            "work_author_era",
        )
        self.assertEqual(
            infer_culture_reasoning_mode(
                {"stem": "我国最早的纪传体通史是："}
            ),
            "direct_fact",
        )
        self.assertEqual(
            infer_culture_reasoning_mode(
                {"stem": "下列典籍按成书先后排序，正确的是："}
            ),
            "chronology",
        )
        for stem in (
            "下列制度中出现最早的是：",
            "下列四部典籍中成书最早的是：",
            "以下哪一项建立时间最早？",
            "下列人物中生活年代最早的是：",
            "下列人物中生活时代最晚的是：",
            "杜甫生活于哪个朝代？",
        ):
            with self.subTest(stem=stem):
                self.assertEqual(
                    infer_culture_reasoning_mode({"stem": stem}),
                    "chronology",
                )
        self.assertEqual(
            infer_culture_reasoning_mode({"stem": "成语‘胸有成竹’最早出自哪部典籍？"}),
            "work_author_era",
        )
        self.assertEqual(
            infer_culture_reasoning_mode({"stem": "我国现存最早的农书是："}),
            "direct_fact",
        )
        self.assertEqual(
            infer_culture_reasoning_mode(
                {"stem": "下列主张中，与战国游说之风关系最密切的是："}
            ),
            "direct_fact",
        )

    def test_router_uses_the_question_target_instead_of_background_keywords(self):
        background_place_stems = (
            "醉翁亭位于滁州，其建造者是谁？",
            "河姆渡遗址位于长江流域，其代表性建筑形式是：",
            "半坡遗址位于黄河流域，其主要种植的作物是：",
            "北京人遗址位于周口店，其生产生活特征是：",
        )
        for stem in background_place_stems:
            with self.subTest(stem=stem):
                self.assertNotEqual(
                    infer_culture_reasoning_mode({"stem": stem}),
                    "place_object_mapping",
                )

        self.assertEqual(
            infer_culture_reasoning_mode({"stem": "岳麓书院位于哪座城市？"}),
            "place_object_mapping",
        )

        school_stems = (
            "鉴真东渡所传播的思想属于哪一思想传统？",
            "吴起变法体现了哪一学派的主张？",
            "玄奘取经与哪一思想传统关系最密切？",
        )
        for stem in school_stems:
            with self.subTest(stem=stem):
                self.assertEqual(
                    infer_culture_reasoning_mode({"stem": stem}),
                    "person_school_claim",
                )

        self.assertEqual(
            infer_culture_reasoning_mode({"stem": "昆山腔改革主要发生在哪一时代？"}),
            "chronology",
        )
        for stem in (
            "‘昆山腔改革’主要对应的时代是：",
            "“永嘉玄言诗”主要关联的时代为：",
        ):
            with self.subTest(stem=stem):
                self.assertEqual(
                    infer_culture_reasoning_mode({"stem": stem}),
                    "chronology",
                )
        for stem in (
            "鉴真东渡对中日文化交流的主要影响是：",
            "吴起变法的主要贡献是：",
            "玄奘取经的主要影响是：",
        ):
            with self.subTest(stem=stem):
                self.assertEqual(
                    infer_culture_reasoning_mode({"stem": stem}),
                    "person_event_effect",
                )

    def test_contextual_unrelated_question_is_inverse_without_splitting_guiwu(self):
        negative_stem = "下列著作中，与韩非子无关的是："
        positive_stem = "下列命题中，与玄学贵无关系最密切的是："

        self.assertEqual(
            infer_question_form(negative_stem, "direct_identification"),
            "negative_identification",
        )
        self.assertEqual(
            infer_question_form(positive_stem, "relationship_match"),
            "relationship_match",
        )
        self.assertEqual(
            infer_culture_reasoning_mode(
                {
                    "stem": "韩非子是法家思想的代表人物，下列著作中，与韩非子无关的是："
                }
            ),
            "work_author_era",
        )

        negative_question = build_question(negative_stem)
        negative_metadata = build_metadata("《韩非子》是法家著作，《道德经》与韩非子无关")
        negative_metadata["question_form"] = "negative_identification"
        negative_metadata["reasoning_steps"]["clue"] = "找出与韩非子无关的著作"
        negative_codes = {
            issue["code"]
            for issue in validate_culture_v3_contract(negative_question, negative_metadata)
        }
        self.assertNotIn("culture_v3_question_form_mismatch", negative_codes)
        self.assertNotIn("culture_v3_inverse_clue_lacks_direction", negative_codes)

        positive_question = build_question(positive_stem)
        positive_metadata = build_metadata("玄学贵无思想重视“无”作为万物根本的意义")
        positive_metadata["question_form"] = "relationship_match"
        positive_codes = {
            issue["code"]
            for issue in validate_culture_v3_contract(positive_question, positive_metadata)
        }
        self.assertNotIn("culture_v3_question_form_mismatch", positive_codes)

    def test_sanitize_fact_removes_source_label_and_review_prefix(self):
        raw = "【解析】核对“明代吴门四家”的范围；徐渭是明代文学家、书画家"
        self.assertEqual(sanitize_fact(raw), "徐渭是明代文学家、书画家")

    def test_four_great_inventions_is_not_treated_as_an_action(self):
        bridge = "四大发明通常指造纸术、印刷术、火药和指南针"
        self.assertTrue(
            bridge_is_answer_echo(
                bridge,
                "中国古代四大发明中",
                "印刷术",
                "person_event_effect",
            )
        )

    def test_event_effect_requires_an_actual_causal_chain(self):
        self.assertTrue(
            bridge_is_answer_echo(
                "玄奘取经的重要特点是促进佛典翻译",
                "玄奘取经",
                "促进佛典翻译",
                "person_event_effect",
            )
        )

    def test_shang_yang_bridge_has_multiple_actions_without_answer_echo(self):
        bridge = "法家人物商鞅奖励耕战、推行县制并统一度量衡，增强秦国国力"
        self.assertGreaterEqual(len(_ACTION_PREDICATE_RE.findall(bridge)), 2)

        question = build_question(
            "在战国时期以变法著称、与秦国富强关系密切的法家人物是："
        )
        question.update(
            {
                "option_a": "商鞅",
                "option_b": "孟子",
                "option_c": "庄子",
                "option_d": "董仲舒",
                "answer": "A",
            }
        )
        metadata = build_metadata(bridge)
        metadata["question_form"] = "relationship_match"
        metadata["fact_anchor"] = {
            "subject": "法家人物",
            "relation": "以变法促进秦国富强",
            "object": "商鞅",
        }
        metadata["reasoning_steps"] = {
            "clue": "战国变法、强秦",
            "bridge": bridge,
            "conclusion": "因此选 A“商鞅”",
        }

        codes = {
            issue["code"] for issue in validate_culture_v3_contract(question, metadata)
        }

        self.assertNotIn("culture_v3_bridge_is_answer_echo", codes)

    def test_school_claim_bridge_rejects_subject_answer_plus_filler(self):
        question = build_question("玄奘的相关思想主张是：")
        metadata = build_metadata("玄奘取经和促进佛典翻译都是重要的中华文化常识")
        metadata["reasoning_mode"] = "person_school_claim"

        codes = {issue["code"] for issue in validate_culture_v3_contract(question, metadata)}

        self.assertIn("culture_v3_bridge_is_answer_echo", codes)

    def test_school_context_claim_and_knowledge_require_concrete_facts(self):
        accepted_bridges = (
            ("墨经力学见于墨家经典《墨经》，其中以力、重、平衡等概念讨论机械现象", "墨经力学", "墨家"),
            ("合同异说以惠施为代表，围绕事物同异关系辨析名实，属于先秦名家论题", "合同异说", "名家"),
            ("蔡泽先陈说祸福劝范雎退位，后经举荐继任秦相，体现纵横家游说取仕", "蔡泽代范雎", "纵横家"),
        )
        for bridge, subject, answer in accepted_bridges:
            with self.subTest(bridge=bridge):
                self.assertTrue(
                    _school_bridge_has_substantive_claim(bridge, subject, answer)
                )

        self.assertFalse(
            _school_bridge_has_substantive_claim(
                "墨经力学与墨家都是传统文化概念，讨论对象很多且历史悠久",
                "墨经力学",
                "墨家",
            )
        )

        for knowledge, answer in (
            ("墨家还重视几何、光学与逻辑知识", "墨家"),
            ("《汉书·艺文志》把纵横家列为诸子十家之一", "纵横家"),
        ):
            with self.subTest(knowledge=knowledge):
                self.assertTrue(
                    _knowledge_is_grounded(
                        knowledge,
                        "本题对象",
                        answer,
                        allow_generic_answer=True,
                    )
                )

        for knowledge in (
            "法家与墨家都是先秦重要学派，二者影响都很深远",
            "墨家是中国古代重要学派之一",
        ):
            with self.subTest(knowledge=knowledge):
                self.assertFalse(
                    _knowledge_is_grounded(
                        knowledge,
                        "墨经力学",
                        "墨家",
                        allow_generic_answer=True,
                    )
                )

    def test_bare_feature_or_period_mapping_is_not_a_reasoning_bridge(self):
        question = build_question()
        for bridge in (
            "玄奘取经的典型特征是促进佛典翻译",
            "玄奘取经这一观点是促进佛典翻译",
        ):
            with self.subTest(bridge=bridge):
                metadata = build_metadata(bridge)
                question["explanation"] = render_culture_explanation_v3(question, metadata)
                codes = {issue["code"] for issue in validate_culture_v3_contract(question, metadata)}
                self.assertTrue(
                    {"culture_v3_bridge_is_answer_echo", "culture_v3_bridge_uses_bare_mapping"} & codes
                )

    def test_dangling_reference_and_ocr_pronoun_seam_are_rejected(self):
        question = build_question()
        cases = (
            "他是唐代高僧，回国后主持译经并促进佛典翻译",
            "玄奘研究佛教思想他回国后主持译经并促进佛典翻译",
            "这句诗出自玄奘，后来促进佛典翻译",
        )
        for bridge in cases:
            with self.subTest(bridge=bridge):
                metadata = build_metadata(bridge)
                question["explanation"] = render_culture_explanation_v3(question, metadata)
                codes = {issue["code"] for issue in validate_culture_v3_contract(question, metadata)}
                self.assertTrue(
                    {"culture_v3_bridge_dangling_reference", "culture_v3_bridge_source_merge"} & codes
                )
        self.assertFalse(
            bridge_is_answer_echo(
                "玄奘西行带回大量佛经，回国后主持译经并推动佛典传播",
                "玄奘取经",
                "促进佛典翻译",
                "person_event_effect",
            )
        )

    def test_semantic_gate_rejects_stable_mapping_positive_exclusion_and_ocr_merge(self):
        cases = {
            "“韩非子”与“《德立》”构成稳定对应": "bridge_contains_review_or_negative_boundary",
            "吴门四家指沈周、文徵明、唐寅、仇英，徐渭不在其中": "bridge_contains_review_or_negative_boundary",
            "孙思邈著有《千金方》，被称为“药王”扁鹊是战国时期医学家": "bridge_dense_source_merge",
        }
        question = build_question()
        for bridge, expected in cases.items():
            with self.subTest(bridge=bridge):
                metadata = build_metadata(bridge)
                flags = semantic_flags(question, metadata, [], [])
                self.assertIn(expected, flags)

    def test_unrelated_same_era_context_cannot_support_a_bare_mapping(self):
        bridge = "施耐庵的创作时期是元末明初；《白兔记》主要关联元末明初"
        self.assertFalse(
            bridge_has_topic_answer_link(
                bridge,
                "《白兔记》",
                "元末明初",
                "work_author_era",
            )
        )

    def test_grounding_distinguishes_book_titles_and_accepts_a_stable_short_name(self):
        self.assertTrue(
            culture_bridge_is_grounded(
                "四书由《大学》《中庸》《论语》《孟子》组成，《春秋》列入五经而不在四书之中",
                subject="四书",
                clue="四书中不包括的典籍",
                correct_option="《春秋》",
                question_form="negative_identification",
            )
        )
        self.assertFalse(
            culture_bridge_is_grounded(
                "《春秋》列入五经而不在四书之中",
                subject="四书",
                clue="四书中不包括的典籍",
                correct_option="春秋",
                question_form="negative_identification",
            )
        )

        self.assertTrue(
            culture_bridge_is_grounded(
                "苏州园林在有限空间中叠山理水、分隔借景，使景观层层展开而不一览无余",
                subject="苏州古典园林",
                clue="苏州古典园林的审美特征",
                correct_option="咫尺山林、曲折含蓄",
                question_form="direct_identification",
            )
        )
        self.assertFalse(
            culture_bridge_is_grounded(
                "北京皇家园林强调中轴规整与宏大秩序",
                subject="苏州古典园林",
                clue="苏州古典园林的审美特征",
                correct_option="咫尺山林、曲折含蓄",
                question_form="direct_identification",
            )
        )

    def test_semantic_gate_rejects_incomplete_bridge_and_review_knowledge(self):
        question = build_question()
        metadata = build_metadata("玄奘带回佛经，回国后的主要著作为")
        metadata["knowledge_extension"] = "其余项按人物时代辨析，属于常考关系"
        flags = semantic_flags(question, metadata, [], [])
        self.assertIn("bridge_incomplete_clause", flags)
        self.assertIn("knowledge_contains_review_language", flags)

    def test_truncated_quotation_or_title_is_rejected(self):
        question = build_question()
        for bridge in (
            "杜甫《登高》名句是无边落木萧萧下，不",
            "三公指丞相、太尉、御史大",
            "也称四大楷书",
            "郭守敬主持编制《授时历》，与现行公历基",
        ):
            with self.subTest(bridge=bridge):
                metadata = build_metadata(bridge)
                flags = semantic_flags(question, metadata, [], [])
                self.assertIn("bridge_incomplete_clause", flags)

    def test_template_bridge_and_relative_time_without_proof_are_rejected(self):
        question = build_question("华佗去世后，曹操还可找哪位名医？")
        metadata = build_metadata("张仲景是东汉医学家，著有《伤寒杂病论》")
        flags = semantic_flags(question, metadata, [], [])
        self.assertIn("bridge_lacks_relative_time_proof", flags)

        metadata = build_metadata("战国策士活动，这是陈轸游说的相关思想主张")
        flags = semantic_flags(build_question(), metadata, [], [])
        self.assertIn("bridge_contains_review_or_negative_boundary", flags)

        metadata = build_metadata("纵横家代表人物常考苏秦、张仪")
        flags = semantic_flags(build_question(), metadata, [], [])
        self.assertIn("bridge_contains_review_or_negative_boundary", flags)

    def test_truncated_knowledge_is_rejected(self):
        question = build_question()
        metadata = build_metadata("玄奘西行带回大量佛经，回国后主持译经")
        metadata["knowledge_extension"] = "三公指丞相、太尉、御史大"
        flags = semantic_flags(question, metadata, [], [])
        self.assertIn("knowledge_incomplete_clause", flags)

        metadata = build_metadata("玄奘西行带回大量佛经，回国后主持译经")
        metadata["knowledge_extension"] = "2).《周髀算经》讨论古代数学与天文问题"
        question["explanation"] = render_culture_explanation_v3(question, metadata)
        codes = {issue["code"] for issue in validate_culture_v3_contract(question, metadata)}
        self.assertIn("culture_v3_knowledge_role_mismatch", codes)

    def test_truncated_memory_mapping_is_rejected(self):
        question = build_question()
        metadata = build_metadata("玄奘西行带回大量佛经，回国后主持译经")
        metadata["memory_hook"] = "玄奘—西行取经；吴道子—人物"
        question["explanation"] = render_culture_explanation_v3(question, metadata)
        codes = {issue["code"] for issue in validate_culture_v3_contract(question, metadata)}
        self.assertIn("culture_v3_memory_hook_requires_review", codes)

    def test_empty_and_repeated_memory_hooks_remain_rejected(self):
        question = build_question()
        metadata = build_metadata("玄奘西行带回大量佛经，回国后主持译经")
        metadata["memory_hook"] = ""
        question["explanation"] = render_culture_explanation_v3(question, metadata)
        empty_codes = {
            issue["code"] for issue in validate_culture_v3_contract(question, metadata)
        }
        self.assertIn("weak_culture_v3_memory_hook", empty_codes)

        metadata = build_metadata("玄奘西行带回大量佛经，回国后主持译经")
        metadata["memory_hook"] = metadata["knowledge_extension"]
        question["explanation"] = render_culture_explanation_v3(question, metadata)
        repeated_codes = {
            issue["code"] for issue in validate_culture_v3_contract(question, metadata)
        }
        self.assertIn("culture_v3_memory_duplicates_knowledge", repeated_codes)

    def test_period_question_requires_a_real_time_link(self):
        question = build_question("宣夜说主要出现或成书于哪个时期？")
        question.update(
            {
                "option_a": "春秋",
                "option_b": "战国",
                "option_c": "古代",
                "option_d": "唐代",
                "answer": "C",
            }
        )
        metadata = build_metadata("宣夜说属于古代宇宙结构学说领域")
        metadata["reasoning_mode"] = "direct_fact"
        metadata["fact_anchor"] = {
            "subject": "宣夜说",
            "relation": "出现时期",
            "object": "古代",
        }
        metadata["reasoning_steps"]["clue"] = "宣夜说"
        metadata["reasoning_steps"]["conclusion"] = "因此选 C“古代”"
        flags = semantic_flags(question, metadata, [], [])
        self.assertIn("bridge_lacks_time_link", flags)

        question = build_question("杜甫生活于哪个朝代？")
        question.update(
            {
                "option_a": "唐代",
                "option_b": "宋代",
                "option_c": "元代",
                "option_d": "明代",
                "answer": "A",
            }
        )
        metadata = build_metadata("杜甫是著名诗人，其作品影响深远")
        metadata["reasoning_mode"] = "chronology"
        metadata["fact_anchor"] = {
            "subject": "杜甫",
            "relation": "生活朝代",
            "object": "唐代",
        }
        metadata["reasoning_steps"] = {
            "clue": "杜甫生活朝代",
            "bridge": "杜甫是著名诗人，其作品影响深远",
            "conclusion": "因此选 A“唐代”",
        }
        codes = {
            issue["code"] for issue in validate_culture_v3_contract(question, metadata)
        }
        self.assertIn("culture_v3_bridge_lacks_time_link", codes)

        metadata["reasoning_steps"]["bridge"] = "杜甫是唐代诗人，其诗歌反映唐代社会现实"
        codes = {
            issue["code"] for issue in validate_culture_v3_contract(question, metadata)
        }
        self.assertNotIn("culture_v3_bridge_lacks_time_link", codes)

        for misplaced_bridge in (
            "杜甫是宋代诗人，其作品反映唐代社会现实",
            "白居易是唐代诗人，杜甫作品影响深远",
        ):
            with self.subTest(misplaced_bridge=misplaced_bridge):
                metadata["reasoning_steps"]["bridge"] = misplaced_bridge
                codes = {
                    issue["code"]
                    for issue in validate_culture_v3_contract(question, metadata)
                }
                self.assertIn("culture_v3_bridge_lacks_time_link", codes)

        metadata["reasoning_steps"]["bridge"] = "李白是唐代诗人，其诗歌具有鲜明浪漫主义色彩"
        codes = {
            issue["code"] for issue in validate_culture_v3_contract(question, metadata)
        }
        self.assertIn("culture_v3_bridge_not_grounded", codes)

        self.assertFalse(
            culture_bridge_has_time_link(
                "杜甫在许多年间创作诗歌，影响深远",
                stem="杜甫生活于哪个朝代？",
                correct_option="唐代",
            )
        )
        self.assertFalse(
            culture_bridge_has_time_link(
                "杜甫在很多年间创作诗歌，影响深远",
                stem="杜甫生活于哪个朝代？",
                correct_option="唐代",
            )
        )
        self.assertFalse(
            culture_bridge_has_time_link(
                "杜甫是宋代诗人，其作品影响深远",
                stem="杜甫生活于哪个朝代？",
                correct_option="唐代",
            )
        )
        self.assertTrue(
            culture_bridge_has_time_link(
                "杜甫是唐代诗人，其作品反映唐代社会现实",
                stem="杜甫生活于哪个朝代？",
                correct_option="唐代",
            )
        )
        self.assertTrue(
            culture_bridge_has_time_link(
                "唐太宗在贞观年间推行一系列治理措施",
                stem="唐太宗的相关治理主要发生在哪一时期？",
                correct_option="贞观年间",
            )
        )
        self.assertFalse(
            culture_bridge_has_time_link(
                "甲制度建立于唐代，是四项中最早的一项",
                stem="下列四项制度按建立先后排序，正确的是：",
                correct_option="甲制度",
            )
        )
        self.assertTrue(
            culture_bridge_has_time_link(
                "甲制度建立于唐代，乙制度形成于宋代，因此甲早于乙",
                stem="下列四项制度按建立先后排序，正确的是：",
                correct_option="甲制度",
            )
        )

        self.assertFalse(
            culture_bridge_has_time_link(
                "杜甫是宋代诗人，其作品反映唐代社会现实",
                stem="杜甫生活于哪个朝代？",
                correct_option="唐代",
                subject="杜甫",
            )
        )
        self.assertFalse(
            culture_bridge_has_time_link(
                "白居易是唐代诗人，杜甫作品影响深远",
                stem="杜甫生活于哪个朝代？",
                correct_option="唐代",
                subject="杜甫",
            )
        )
        self.assertTrue(
            culture_bridge_has_time_link(
                "杜甫的诗歌以沉郁顿挫著称，生活于唐代",
                stem="杜甫生活于哪个朝代？",
                correct_option="唐代",
                subject="杜甫",
            )
        )
        self.assertTrue(
            culture_bridge_has_time_link(
                "宜兴紫砂在明代兴起，清代进一步发展并形成多样器型",
                stem="宜兴紫砂主要关联的时代是：",
                correct_option="明清",
                subject="宜兴紫砂",
            )
        )
        self.assertFalse(
            culture_bridge_has_time_link(
                "宜兴紫砂在明代兴起",
                stem="宜兴紫砂主要关联的时代是：",
                correct_option="明清",
                subject="宜兴紫砂",
            )
        )

        comparison_stem = "下列人物中生活年代最早的是："
        self.assertFalse(
            culture_bridge_has_time_link(
                "孔子生活于春秋时期，因此他的生活年代最早",
                stem=comparison_stem,
                correct_option="孔子",
                subject="孔子",
            )
        )
        self.assertFalse(
            culture_bridge_has_time_link(
                "孔子生活于春秋时期，孟子生活于战国时期",
                stem=comparison_stem,
                correct_option="孔子",
                subject="孔子",
            )
        )
        self.assertFalse(
            culture_bridge_has_time_link(
                "《春秋》列入五经，孟子生活于战国时期，因此《春秋》早于孟子",
                stem=comparison_stem,
                correct_option="孔子",
                subject="孔子",
            )
        )
        self.assertTrue(
            culture_bridge_has_time_link(
                "孔子生活于春秋时期，孟子生活于战国时期，因此孔子早于孟子",
                stem=comparison_stem,
                correct_option="孔子",
                subject="孔子",
            )
        )

    def test_time_binding_accepts_qualified_dates_continuations_and_period_families(self):
        accepted_cases = (
            (
                "靖难之役发生于明代1399至1402年，朱棣起兵并最终夺取帝位",
                "明代",
                "靖难之役",
            ),
            (
                "鲁迅生于1881年、卒于1936年，生活与主要文学创作均处于中国现代时期",
                "现代",
                "鲁迅",
            ),
            (
                "秦兵马俑营建于秦始皇统治时期，作为帝陵陪葬遗存形成于秦代",
                "秦代",
                "秦兵马俑",
            ),
            (
                "贾思勰农书《齐民要术》约在六世纪前期成书，主要属于北魏末期著述",
                "北魏",
                "贾思勰农书",
            ),
            (
                "《周髀算经》的主要内容在秦汉间形成，约于西汉时期成书",
                "秦汉时期",
                "《周髀算经》",
            ),
            (
                "火药配方在唐代已有记载，北宋1044年成书的《武经总要》载有多种配方",
                "唐宋",
                "火药配方",
            ),
            (
                "《三国演义》在元末明初成书，后来又经整理刊刻",
                "元末明初",
                "《三国演义》",
            ),
            ("材份制形成于北宋", "宋代", "材份制"),
            ("交子出现于宋代", "北宋", "交子"),
            ("文景之治形成于西汉前期", "汉代", "文景之治"),
            ("光武中兴发生于汉代", "东汉", "光武中兴"),
        )
        for bridge, answer, subject in accepted_cases:
            with self.subTest(bridge=bridge, answer=answer):
                self.assertTrue(
                    culture_bridge_has_time_link(
                        bridge,
                        stem=f"{subject}主要关联的时代是：",
                        correct_option=answer,
                        subject=subject,
                    )
                )

        rejected_cases = (
            ("杜甫是宋代诗人并生活于唐代", "唐代", "杜甫"),
            ("交子出现于南宋", "北宋", "交子"),
            ("文景之治形成于东汉", "西汉", "文景之治"),
            ("靖难之役发生于明代1402年并延续至清代", "明代", "靖难之役"),
        )
        for bridge, answer, subject in rejected_cases:
            with self.subTest(bridge=bridge, answer=answer):
                self.assertFalse(
                    culture_bridge_has_time_link(
                        bridge,
                        stem=f"{subject}主要关联的时代是：",
                        correct_option=answer,
                        subject=subject,
                    )
                )

        self.assertTrue(
            culture_bridge_has_time_link(
                "宜兴紫砂在明代成熟并兴盛，清代延续发展",
                stem="宜兴紫砂主要关联的时代是：",
                correct_option="明清",
                subject="宜兴紫砂",
            )
        )
        self.assertFalse(
            culture_bridge_has_time_link(
                "宜兴紫砂在明代1600年前后成熟并兴盛",
                stem="宜兴紫砂主要关联的时代是：",
                correct_option="明清",
                subject="宜兴紫砂",
            )
        )

    def test_time_binding_rejects_unbound_stages_and_one_subject_comparison(self):
        rejected_cases = (
            (
                "宜兴紫砂在明代兴起，清代科举制度继续发展",
                "宜兴紫砂主要关联的时代是：",
                "明清",
                "宜兴紫砂",
            ),
            (
                "交子出现于北宋，南宋时期纸币继续发展",
                "交子主要关联的时代是：",
                "北宋",
                "交子",
            ),
            (
                "孔子生于公元前551年，生活于春秋时期，因此孔子最早",
                "下列人物中谁生活年代最早？",
                "孔子",
                "孔子",
            ),
            (
                "鲁迅生于1881年，在现代文学研究中形成了重要议题",
                "鲁迅主要关联的时代是：",
                "现代",
                "鲁迅",
            ),
        )
        for bridge, stem, answer, subject in rejected_cases:
            with self.subTest(bridge=bridge):
                self.assertFalse(
                    culture_bridge_has_time_link(
                        bridge,
                        stem=stem,
                        correct_option=answer,
                        subject=subject,
                    )
                )

    def test_time_binding_supports_detail_answers_and_requires_complete_ranges(self):
        accepted_cases = (
            ("靖难之役发生于明代1402年并结束", "1402年", "靖难之役"),
            ("唐太宗在唐代贞观年间推行新政", "贞观年间", "唐太宗"),
            ("某著作在唐代9世纪成书", "9世纪", "某著作"),
            ("靖难之役发生于明代1399至1402年", "1399—1402年", "靖难之役"),
            (
                "《文献通考》由马端临编纂，于元代大德十一年成书",
                "元代",
                "《文献通考》",
            ),
        )
        for bridge, answer, subject in accepted_cases:
            with self.subTest(bridge=bridge):
                self.assertTrue(
                    culture_bridge_has_time_link(
                        bridge,
                        stem=f"{subject}主要关联的时代是：",
                        correct_option=answer,
                        subject=subject,
                    )
                )

        rejected_cases = (
            ("某学说形成于公元3世纪", "公元前3世纪", "某学说"),
            ("靖难之役终于1402年", "1399—1402年", "靖难之役"),
            ("某运动兴起于20世纪初", "19世纪末至20世纪初", "某运动"),
        )
        for bridge, answer, subject in rejected_cases:
            with self.subTest(bridge=bridge):
                self.assertFalse(
                    culture_bridge_has_time_link(
                        bridge,
                        stem=f"{subject}主要关联的时代是：",
                        correct_option=answer,
                        subject=subject,
                    )
                )

    def test_chronology_contract_blocks_overlapping_options_and_non_time_answers(self):
        overlap_question = build_question("指南鱼主要出现或记载于哪个时期？")
        overlap_question.update(
            {
                "option_a": "宋元",
                "option_b": "唐代",
                "option_c": "北宋",
                "option_d": "宋代",
                "answer": "D",
            }
        )
        overlap_metadata = build_metadata(
            "指南鱼的制法见于北宋成书的《武经总要》，按总体朝代归入宋代"
        )
        overlap_metadata["reasoning_mode"] = "chronology"
        overlap_metadata["fact_anchor"] = {
            "subject": "指南鱼",
            "relation": "出现时期",
            "object": "宋代",
        }
        overlap_metadata["reasoning_steps"] = {
            "clue": "指南鱼出现时期",
            "bridge": "指南鱼的制法见于北宋成书的《武经总要》，按总体朝代归入宋代",
            "conclusion": "因此选 D“宋代”",
        }
        overlap_codes = {
            issue["code"]
            for issue in validate_culture_v3_contract(
                overlap_question,
                overlap_metadata,
            )
        }
        self.assertIn("culture_v3_time_options_overlap", overlap_codes)

        non_time_question = build_question("咏史诗最早出现的历史时期是：")
        non_time_question.update(
            {
                "option_a": "东汉",
                "option_b": "魏晋",
                "option_c": "古典诗歌",
                "option_d": "唐代",
                "answer": "C",
            }
        )
        non_time_metadata = build_metadata(
            "咏史诗在东汉出现，魏晋走向成熟，属于中国古典诗歌的题材类型"
        )
        non_time_metadata["reasoning_mode"] = "chronology"
        non_time_metadata["fact_anchor"] = {
            "subject": "咏史诗",
            "relation": "历史时期",
            "object": "古典诗歌",
        }
        non_time_metadata["reasoning_steps"] = {
            "clue": "咏史诗出现时期",
            "bridge": "咏史诗在东汉出现，魏晋走向成熟，属于中国古典诗歌的题材类型",
            "conclusion": "因此选 C“古典诗歌”",
        }
        non_time_codes = {
            issue["code"]
            for issue in validate_culture_v3_contract(
                non_time_question,
                non_time_metadata,
            )
        }
        self.assertIn("culture_v3_chronology_answer_not_time", non_time_codes)

    def test_materially_invalid_checkpoint_cases_remain_blocked(self):
        for stem, subject, clue in (
            (
                "《伤寒杂病论》对中医学发展的重要影响是：",
                "《伤寒杂病论》",
                "作者与著作性质",
            ),
            (
                "《邓析子》通常归属哪个学派或思想传统？",
                "《邓析子》",
                "名实辨析与论辩",
            ),
        ):
            with self.subTest(subject=subject):
                question = build_question(stem)
                metadata = build_metadata("玄奘西行带回佛经，回国后主持译经")
                metadata["fact_anchor"]["subject"] = subject
                metadata["reasoning_steps"]["clue"] = clue
                codes = {
                    issue["code"]
                    for issue in validate_culture_v3_contract(question, metadata)
                }
                self.assertIn("culture_v3_clue_not_grounded", codes)

        broad_time_cases = (
            ("凭几", "凭几在先秦典籍记载中已经出现，并长期用于传统起居礼仪"),
            ("花甲", "花甲源自古代干支六十年循环，唐代诗文已有相关用例"),
            ("十二律", "十二律在先秦已出现，汉代以后持续发展，属于中国古代乐律体系"),
        )
        for subject, bridge in broad_time_cases:
            with self.subTest(subject=subject):
                question = build_question(f"{subject}主要出现于哪个历史时期？")
                question.update(
                    {
                        "option_a": "古代",
                        "option_b": "战国",
                        "option_c": "西汉",
                        "option_d": "现代",
                        "answer": "A",
                    }
                )
                metadata = build_metadata(bridge)
                metadata["reasoning_mode"] = "chronology"
                metadata["fact_anchor"] = {
                    "subject": subject,
                    "relation": "出现时期",
                    "object": "古代",
                }
                metadata["reasoning_steps"] = {
                    "clue": f"{subject}出现时期",
                    "bridge": bridge,
                    "conclusion": "因此选 A“古代”",
                }
                codes = {
                    issue["code"]
                    for issue in validate_culture_v3_contract(question, metadata)
                }
                self.assertIn("culture_v3_time_answer_too_broad", codes)

    def test_knowledge_cannot_repeat_a_short_answer_mapping(self):
        question = build_question("交子主要关联的历史时期是：")
        question.update(
            {
                "option_a": "唐代",
                "option_b": "南宋",
                "option_c": "元代",
                "option_d": "北宋",
                "answer": "D",
            }
        )
        metadata = build_metadata("交子是北宋四川地区出现的早期纸币")
        metadata["reasoning_mode"] = "direct_fact"
        metadata["fact_anchor"] = {
            "subject": "交子",
            "relation": "出现时期",
            "object": "北宋",
        }
        metadata["reasoning_steps"] = {
            "clue": "交子",
            "bridge": "交子是北宋四川地区出现的早期纸币",
            "conclusion": "因此选 D“北宋”",
        }
        metadata["knowledge_extension"] = "交子对应北宋时期"
        flags = semantic_flags(question, metadata, [], [])
        self.assertIn("knowledge_repeats_answer_mapping", flags)

    def test_option_fact_cannot_be_a_negative_restatement_or_lose_the_answer(self):
        question = build_question()
        metadata = build_metadata("玄奘西行带回大量佛经，回国后主持译经")
        metadata["option_analysis"]["B"]["fact"] = "指南针不符合“玄奘取经”的人物事迹"
        metadata["option_analysis"]["A"]["fact"] = "唐代高僧回国后主持译经"
        question["explanation"] = render_culture_explanation_v3(question, metadata)
        codes = {issue["code"] for issue in validate_culture_v3_contract(question, metadata)}
        self.assertIn("culture_v3_option_fact_weak", codes)
        self.assertIn("culture_v3_correct_option_fact_missing_answer", codes)

    def test_option_fact_cannot_invent_a_limit_missing_from_the_option(self):
        question = build_question()
        question["option_c"] = "赵国策士议论时局"
        metadata = build_metadata("玄奘西行带回大量佛经，回国后主持译经")
        metadata["option_analysis"]["C"] = {
            "verdict": "incorrect",
            "fact": "赵国策士议论时局限于赵国范围",
            "fit": "地域范围过窄，并非列国风气",
        }

        codes = {issue["code"] for issue in validate_culture_v3_contract(question, metadata)}

        self.assertIn("culture_v3_option_fact_adds_unsupported_limit", codes)

        metadata["option_analysis"]["C"] = {
            "verdict": "incorrect",
            "fact": "赵国策士议论时局是特定国家层面的活动描述",
            "fit": "选项表述范围较窄，不能概括列国策士往来的整体风气",
        }
        codes = {issue["code"] for issue in validate_culture_v3_contract(question, metadata)}

        self.assertNotIn("culture_v3_option_fact_adds_unsupported_limit", codes)

    def test_specific_time_mismatch_fits_have_concrete_connectors(self):
        question = build_question()
        for fit in (
            "把兴起提前到元代",
            "遗漏清代发展",
            "尚非配方成书时期",
            "结束在成图以前",
        ):
            with self.subTest(fit=fit):
                self.assertIsNotNone(_WRONG_FIT_CONNECTOR_RE.search(fit))
                metadata = build_metadata(
                    "玄奘西行带回大量佛经，回国后组织译场并主持翻译"
                )
                metadata["option_analysis"]["B"]["fit"] = fit

                codes = {
                    issue["code"]
                    for issue in validate_culture_v3_contract(question, metadata)
                }

                self.assertNotIn(
                    "culture_v3_wrong_option_mismatch_unclear",
                    codes,
                )

        self.assertTrue(
            _short_chronology_fit_has_date_fact(
                "南朝宋存在于420年至479年",
                "时代不同",
            )
        )
        self.assertFalse(
            _short_chronology_fit_has_date_fact(
                "南朝宋属于古代王朝",
                "时代不同",
            )
        )

        reform_bridge = "昆山腔改革中，魏良辅先规范吐字行腔，又吸收北曲演唱长处，从而形成水磨腔"
        self.assertGreaterEqual(len(_ACTION_PREDICATE_RE.findall(reform_bridge)), 2)

    def test_fact_anchor_object_must_equal_the_correct_option_not_wrap_it(self):
        question = build_question()
        metadata = build_metadata("玄奘西行带回大量佛经，回国后组织译场并主持翻译")
        metadata["fact_anchor"]["object"] = "并非促进佛典翻译"

        codes = {issue["code"] for issue in validate_culture_v3_contract(question, metadata)}

        self.assertIn("culture_v3_fact_anchor_answer_mismatch", codes)

    def test_every_option_fact_must_name_its_own_object(self):
        question = build_question()
        metadata = build_metadata("玄奘西行带回大量佛经，回国后主持译经")
        metadata["option_analysis"]["B"]["fact"] = "造纸术改进降低了书写材料成本"
        question["explanation"] = render_culture_explanation_v3(question, metadata)
        codes = {issue["code"] for issue in validate_culture_v3_contract(question, metadata)}
        self.assertIn("culture_v3_wrong_option_fact_missing_object", codes)

        metadata = build_metadata("玄奘西行带回大量佛经，回国后主持译经")
        metadata["option_analysis"]["B"]["fact"] = "是中国古代地理学名著"
        question["explanation"] = render_culture_explanation_v3(question, metadata)
        codes = {issue["code"] for issue in validate_culture_v3_contract(question, metadata)}
        self.assertIn("culture_v3_option_fact_weak", codes)

        metadata = build_metadata("玄奘西行带回大量佛经，回国后主持译经")
        metadata["option_analysis"]["B"]["fact"] = "天台宗归属天台宗"
        question["explanation"] = render_culture_explanation_v3(question, metadata)
        codes = {issue["code"] for issue in validate_culture_v3_contract(question, metadata)}
        self.assertIn("culture_v3_option_fact_weak", codes)

        metadata = build_metadata("玄奘西行带回大量佛经，回国后主持译经")
        metadata["option_analysis"]["B"]["fact"] = "指南针与远洋航海构成稳定对应"
        question["explanation"] = render_culture_explanation_v3(question, metadata)
        codes = {issue["code"] for issue in validate_culture_v3_contract(question, metadata)}
        self.assertIn("culture_v3_option_fact_weak", codes)

    def test_bridge_cannot_bury_the_topic_after_unrelated_facts(self):
        question = build_question()
        metadata = build_metadata(
            "鉴真东渡日本传播佛法，张骞出使西域沟通中外，玄奘取经促进佛典翻译"
        )
        question["explanation"] = render_culture_explanation_v3(question, metadata)
        codes = {issue["code"] for issue in validate_culture_v3_contract(question, metadata)}
        self.assertIn("culture_v3_bridge_topic_arrives_late", codes)

    def test_bridge_must_stay_grounded_in_question_fact(self):
        question = build_question("王阳明提出的核心主张是：")
        question.update(
            {
                "option_a": "兼爱非攻",
                "option_b": "知行合一",
                "option_c": "无为而治",
                "option_d": "法术势",
                "answer": "B",
            }
        )
        metadata = build_metadata("墨子主张兼爱非攻，强调普遍相爱并反对侵略战争")
        metadata["reasoning_mode"] = "person_school_claim"
        metadata["fact_anchor"] = {
            "subject": "王阳明",
            "relation": "核心主张",
            "object": "知行合一",
        }
        metadata["reasoning_steps"] = {
            "clue": "王阳明核心主张",
            "bridge": "墨子主张兼爱非攻，强调普遍相爱并反对侵略战争",
            "conclusion": "因此选 B“知行合一”",
        }
        codes = {
            issue["code"] for issue in validate_culture_v3_contract(question, metadata)
        }
        self.assertIn("culture_v3_bridge_not_grounded", codes)

        metadata["reasoning_steps"]["bridge"] = "墨子认为道德认识与道德实践应统一，并以此说明伦理修养"
        codes = {
            issue["code"] for issue in validate_culture_v3_contract(question, metadata)
        }
        self.assertIn("culture_v3_bridge_not_grounded", codes)

        metadata["reasoning_steps"]["bridge"] = "王阳明强调知与行不可割裂，主张在实践中落实良知"
        codes = {
            issue["code"] for issue in validate_culture_v3_contract(question, metadata)
        }
        self.assertNotIn("culture_v3_bridge_not_grounded", codes)

        xuanzang = build_metadata("鉴真东渡日本传播佛法，促进佛典翻译")
        codes = {
            issue["code"]
            for issue in validate_culture_v3_contract(build_question(), xuanzang)
        }
        self.assertIn("culture_v3_bridge_not_grounded", codes)

    def test_knowledge_must_extend_current_topic_and_not_copy_option_fact(self):
        question = build_question()
        metadata = build_metadata("玄奘西行带回大量佛经，回国后主持译经")
        metadata["knowledge_extension"] = "五斗米道属于中国早期道教组织"
        question["explanation"] = render_culture_explanation_v3(question, metadata)
        codes = {issue["code"] for issue in validate_culture_v3_contract(question, metadata)}
        self.assertIn("culture_v3_knowledge_not_grounded", codes)
        self.assertIn("culture_v3_knowledge_duplicates_option_fact", codes)

    def test_three_identical_wrong_fit_shells_are_rejected(self):
        question = build_question()
        metadata = build_metadata("玄奘西行带回大量佛经，回国后主持译经")
        metadata["option_analysis"]["B"]["fit"] = "它说明的是“指南针”，不是“玄奘”"
        metadata["option_analysis"]["C"]["fit"] = "它说明的是“五斗米道”，不是“玄奘”"
        metadata["option_analysis"]["D"]["fit"] = "它说明的是“程朱理学”，不是“玄奘”"
        question["explanation"] = render_culture_explanation_v3(question, metadata)
        codes = {issue["code"] for issue in validate_culture_v3_contract(question, metadata)}
        self.assertIn("culture_v3_option_fit_template_repeated", codes)

    def test_three_identical_generic_wrong_fits_are_rejected_even_when_facts_differ(self):
        metadata = build_metadata("玄奘西行带回大量佛经，回国后组织译场并主持翻译")
        for label in ("B", "C", "D"):
            metadata["option_analysis"][label]["fit"] = "与本题所问对象不符"

        codes = {
            issue["code"]
            for issue in validate_culture_v3_contract(build_question(), metadata)
        }

        self.assertIn("culture_v3_option_fit_weak", codes)
        self.assertIn("culture_v3_option_fit_repeated", codes)

    def test_evidence_must_be_grounded_and_difficulty_features_nonempty(self):
        metadata = build_metadata("玄奘西行带回大量佛经，回国后组织译场并主持翻译")
        metadata["evidence_excerpt"] = "都江堰由李冰父子主持修建，用于灌溉和分洪。"
        metadata["difficulty_features"] = []

        codes = {
            issue["code"]
            for issue in validate_culture_v3_contract(build_question(), metadata)
        }

        self.assertIn("culture_v3_evidence_not_grounded", codes)
        self.assertIn("invalid_culture_v3_difficulty_features", codes)

    def test_inverse_evidence_bridge_rescue_still_names_the_corrected_option_fact(self):
        question = {
            **build_question("以下四个选项中，哪一个关于“古琴”的描述不正确？"),
            "option_a": "以古代八音的观点来看，“琴”与“瑟”均属于丝音",
            "option_b": "阮籍以弹奏《广陵散》闻名",
            "option_c": "《高山流水》一曲以伯牙与子期的故事引出",
            "option_d": "“对牛弹琴”“焚琴煮鹤”都与琴有关",
            "answer": "B",
        }
        metadata = build_metadata("《广陵散》因嵇康临刑前弹奏的故事而著名，并非以阮籍演奏闻名")
        metadata.update(
            {
                "question_form": "negative_identification",
                "reasoning_mode": "category_comparison",
                "fact_anchor": {
                    "subject": "古琴文化常识",
                    "relation": "错误描述",
                    "object": "阮籍以弹奏《广陵散》闻名",
                },
                "reasoning_steps": {
                    "clue": "找出古琴描述中的错误项",
                    "bridge": "《广陵散》因嵇康临刑前弹奏的故事而著名，并非以阮籍演奏闻名",
                    "conclusion": "因此选 B“阮籍以弹奏《广陵散》闻名”",
                },
            }
        )

        accepted = "古琴曲《广陵散》因嵇康临刑前演奏而闻名，并非因阮籍演奏而闻名。"
        metadata["evidence_excerpt"] = accepted
        accepted_codes = {
            issue["code"] for issue in validate_culture_v3_contract(question, metadata)
        }
        self.assertNotIn("culture_v3_evidence_not_grounded", accepted_codes)
        self.assertNotIn("culture_v3_inverse_evidence_lacks_correction", accepted_codes)
        self.assertNotIn("culture_v3_inverse_clue_lacks_direction", accepted_codes)

        metadata["reasoning_steps"]["clue"] = "古琴文化常识"
        direction_codes = {
            issue["code"] for issue in validate_culture_v3_contract(question, metadata)
        }
        self.assertIn("culture_v3_inverse_clue_lacks_direction", direction_codes)
        metadata["reasoning_steps"]["clue"] = "找出古琴描述中的错误项"

        rejected = (
            "嵇康临刑前身着绿色衣服。",
            "嵇康临刑前曾长期居住在洛阳。",
            "苏轼临刑前弹奏古琴而著名。",
            "古琴文化常识涉及乐器和典故。",
            "古琴文化历史悠久，是中华传统文化的重要组成部分。",
            "中华文化常识内容丰富，具有悠久历史。",
        )
        for evidence in rejected:
            with self.subTest(evidence=evidence):
                metadata["evidence_excerpt"] = evidence
                codes = {
                    issue["code"]
                    for issue in validate_culture_v3_contract(question, metadata)
                }
                self.assertIn("culture_v3_evidence_not_grounded", codes)

        false_restated_as_evidence = (
            "阮籍以弹奏《广陵散》闻名。",
            "阮籍以弹奏《广陵散》闻名，是古琴史上的重要事实。",
            "阮籍弹奏《广陵散》的故事在古琴文化中影响深远。",
        )
        for evidence in false_restated_as_evidence:
            with self.subTest(evidence=evidence):
                metadata["evidence_excerpt"] = evidence
                codes = {
                    issue["code"]
                    for issue in validate_culture_v3_contract(question, metadata)
                }
                self.assertIn("culture_v3_inverse_evidence_lacks_correction", codes)

        false_double_corrections = (
            "阮籍以弹奏《广陵散》闻名，并不是错误说法。",
            "阮籍以弹奏《广陵散》闻名，并非不正确。",
            "阮籍以弹奏《广陵散》闻名，与错误描述不同。",
        )
        for evidence in false_double_corrections:
            with self.subTest(evidence=evidence):
                metadata["evidence_excerpt"] = evidence
                codes = {
                    issue["code"]
                    for issue in validate_culture_v3_contract(question, metadata)
                }
                self.assertIn("culture_v3_evidence_not_grounded", codes)
        metadata["evidence_excerpt"] = false_double_corrections[1]
        codes = {
            issue["code"] for issue in validate_culture_v3_contract(question, metadata)
        }
        self.assertIn("culture_v3_inverse_evidence_false_correction", codes)

        short_answer_question = {
            **build_question("下列典籍中，不属于“四书”的是："),
            "option_a": "大学",
            "option_b": "中庸",
            "option_c": "论语",
            "option_d": "春秋",
            "answer": "D",
        }
        metadata["fact_anchor"] = {
            "subject": "四书",
            "relation": "不包括",
            "object": "春秋",
        }
        metadata["reasoning_steps"] = {
            "clue": "找出不属于四书的典籍",
            "bridge": "四书包括《大学》《中庸》《论语》《孟子》，《春秋》属于五经",
            "conclusion": "因此选 D“春秋”",
        }
        metadata["evidence_excerpt"] = "《春秋》属于五经，不在四书之列。"
        short_answer_codes = {
            issue["code"]
            for issue in validate_culture_v3_contract(short_answer_question, metadata)
        }
        self.assertNotIn("culture_v3_evidence_not_grounded", short_answer_codes)

        six_ministries_question = {
            **build_question("三省六部制中，下列机构不属于六部的是："),
            "option_a": "吏部",
            "option_b": "户部",
            "option_c": "礼部",
            "option_d": "御史台",
            "answer": "D",
        }
        metadata["fact_anchor"] = {
            "subject": "六部",
            "relation": "非六部机构",
            "object": "御史台",
        }
        metadata["reasoning_steps"] = {
            "clue": "找出不属于六部的机构",
            "bridge": "六部是吏户礼兵刑工六部，御史台是监察机构，不列入六部",
            "conclusion": "因此选 D“御史台”",
        }
        metadata["evidence_excerpt"] = "御史台承担监察职能，不列入吏户礼兵刑工六部。"
        six_ministries_codes = {
            issue["code"]
            for issue in validate_culture_v3_contract(six_ministries_question, metadata)
        }
        self.assertNotIn(
            "culture_v3_inverse_evidence_lacks_correction",
            six_ministries_codes,
        )
        self.assertNotIn("culture_v3_evidence_not_grounded", six_ministries_codes)

        metadata["evidence_excerpt"] = "御史台并非未列入六部，它承担监察职能。"
        double_negative_codes = {
            issue["code"]
            for issue in validate_culture_v3_contract(six_ministries_question, metadata)
        }
        self.assertIn(
            "culture_v3_inverse_evidence_false_correction",
            double_negative_codes,
        )
        self.assertIn("culture_v3_evidence_not_grounded", double_negative_codes)

    def test_nested_teaching_text_fields_must_be_strings(self):
        metadata = build_metadata("玄奘西行带回大量佛经，回国后组织译场并主持翻译")
        metadata["reasoning_steps"]["clue"] = ["玄奘取经"]
        metadata["knowledge_extension"] = ["玄奘是唐代高僧"]
        metadata["option_analysis"]["B"]["fit"] = ["对象不同"]

        codes = {
            issue["code"]
            for issue in validate_culture_v3_contract(build_question(), metadata)
        }

        self.assertIn("culture_v3_non_string_field", codes)
        self.assertIn("culture_v3_reasoning_step_not_string", codes)
        self.assertIn("culture_v3_option_analysis_non_string", codes)

    def test_incomplete_numbered_knowledge_list_is_detected(self):
        self.assertTrue(enumeration_incomplete("中国三大国粹分别为京剧"))
        self.assertFalse(enumeration_incomplete("三种记忆对象分别为京剧、国画和中医"))

    def test_procedural_or_self_contradictory_knowledge_is_rejected(self):
        question = build_question()
        for knowledge in (
            "典籍文物需区分作者、时代、体例、载体和用途",
            "陆游是南宋爱国诗人，但该名句通常不归于陆游",
        ):
            with self.subTest(knowledge=knowledge):
                metadata = build_metadata("玄奘西行带回大量佛经，回国后主持译经")
                metadata["knowledge_extension"] = knowledge
                question["explanation"] = render_culture_explanation_v3(question, metadata)
                codes = {issue["code"] for issue in validate_culture_v3_contract(question, metadata)}
                self.assertTrue(
                    {"culture_v3_knowledge_role_mismatch", "culture_v3_knowledge_self_contradiction"} & codes
                )

    def test_central_contract_rejects_source_merge_and_procedural_knowledge(self):
        question = build_question()
        metadata = build_metadata(
            "孙思邈著有《千金方》，被称为“药王”扁鹊是战国时期医学家"
        )
        metadata["knowledge_extension"] = "人物关系常考，要区分后再按时代串联"
        question["explanation"] = render_culture_explanation_v3(question, metadata)
        codes = {issue["code"] for issue in validate_culture_v3_contract(question, metadata)}
        self.assertIn("culture_v3_bridge_source_merge", codes)
        self.assertIn("culture_v3_knowledge_role_mismatch", codes)


if __name__ == "__main__":
    unittest.main()
