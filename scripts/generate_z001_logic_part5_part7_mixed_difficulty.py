from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "z001_logic_reasoning_part5_part7_mixed_difficulty_batch_001.json"
DEFAULT_REVIEW = PROJECT_ROOT / "data" / "z001_logic_reasoning_part5_part7_mixed_difficulty_batch_001_review.md"


CONTEXTS = [
    "港澳台考研逻辑训练营",
    "真题复盘小组",
    "周末模考班",
    "限时刷题小组",
    "综合能力冲刺营",
    "资料整理小组",
    "错题归因小组",
    "线上答疑班",
    "题型归纳小组",
    "阅读论证训练组",
    "春季集训班",
    "暑期强化班",
    "秋季模考队",
    "冬季冲刺队",
    "每日打卡群",
    "跨校备考联盟",
    "逻辑专项班",
    "论证分析小组",
    "条件推理训练组",
    "综合推理训练组",
]

SUBJECTS = [
    "甲",
    "乙",
    "丙",
    "丁",
    "小周",
    "小林",
    "小陈",
    "小许",
    "阿明",
    "阿敏",
    "一班",
    "二班",
    "三班",
    "文史组",
    "逻辑组",
    "阅读组",
    "数学组",
    "资料组",
]

ITEMS = [
    "真题",
    "模拟题",
    "错题",
    "阅读材料",
    "讲义",
    "笔记",
    "训练计划",
    "复盘表",
    "诊断报告",
    "专项练习",
    "推理题",
    "论证题",
    "分类题",
    "知识卡片",
]

QUALITIES = [
    "按时完成",
    "经过复盘",
    "来自真题",
    "难度适中",
    "有详细解析",
    "适合限时训练",
    "覆盖核心考点",
    "包含干扰项",
    "需要画表",
    "需要找论点",
    "需要找论据",
    "需要识别条件",
]

CONCEPT_CASES = [
    ("“孔子”", "单独概念", "它只指称一个确定对象。"),
    ("“考生”", "普遍概念", "它可以指称多个同类对象。"),
    ("“班级”作为若干学生组成的整体", "集合概念", "它强调由若干个体组成的整体。"),
    ("“非专业课”", "负概念", "它通过否定某一属性来指称对象。"),
    ("“蓝色”", "正概念", "它直接反映对象具有的属性。"),
    ("“三角形”", "普遍概念", "它可以指称所有符合定义的平面图形。"),
    ("“这本教材”", "单独概念", "它指称一个确定对象。"),
    ("“题库”作为所有题目的整体", "集合概念", "它强调题目集合形成的整体。"),
]

RELATION_CASES = [
    ("儒家", "先秦学派", "真包含于关系", "所有儒家都属于先秦学派之一，但先秦学派不只包含儒家。"),
    ("诗人", "作家", "真包含于关系", "诗人通常属于作家范围，但作家不都只是诗人。"),
    ("教师", "医生", "全异关系", "二者外延没有必然交叉。"),
    ("等边三角形", "等角三角形", "全同关系", "在平面几何中二者外延相同。"),
    ("研究生", "党员", "交叉关系", "有些研究生是党员，有些党员是研究生，但二者不完全相同。"),
    ("错题", "已掌握题", "全异关系", "在同一统计口径下，错题与已掌握题被区分记录。"),
    ("阅读题", "英语题", "真包含于关系", "阅读题是英语题的一类，但英语题还包括其他题型。"),
    ("逻辑题", "综合能力题", "真包含于关系", "逻辑题属于综合能力考试中的题型之一。"),
]

DEFINITION_CASES = [
    ("三角形就是由三条线段围成的平面图形", "正确揭示本质属性", "指出了属概念和种差。"),
    ("教师就是在学校工作的人", "定义过宽", "学校工作人员还包括行政、后勤等人员。"),
    ("小说就是长篇小说", "定义过窄", "小说还包括短篇、中篇等类型。"),
    ("法律就是法律规范", "同语反复", "定义项没有提供新的解释。"),
    ("诚信就是不欺骗别人并遵守承诺", "正确揭示本质属性", "抓住了诚信的关键特征。"),
    ("逻辑题就是考逻辑的题", "同语反复", "定义项只是重复被定义项。"),
    ("节气就是夏至", "定义过窄", "二十四节气不止夏至一个。"),
    ("文学作品就是小说、诗歌、散文和戏剧等语言艺术作品", "正确揭示本质属性", "从语言艺术及主要类别说明了对象。"),
]

ARGUMENT_CASES = [
    {
        "type": "加强",
        "stem": "某训练营认为：只要坚持错题复盘，逻辑题正确率就会明显提高。以下哪项最能加强这一结论？",
        "correct": "对照组研究显示，复盘错题的学生在相同练习量下正确率提升更明显。",
        "distractors": [
            "错题复盘需要花费较多时间。",
            "有些学生不喜欢整理错题。",
            "该训练营同时开设英语阅读课程。",
            "逻辑题的题型数量较多。",
        ],
        "explanation": "对照组证据排除了单纯练习量等干扰，更直接支持错题复盘与正确率提升之间的联系。",
    },
    {
        "type": "削弱",
        "stem": "有人认为：某班逻辑成绩提高，是因为他们更换了新的教材。以下哪项最能削弱这一结论？",
        "correct": "更换教材的同时，该班每周增加了两次真题讲评课。",
        "distractors": [
            "新教材的封面设计更醒目。",
            "该班学生都参加过期中测验。",
            "旧教材也包含基础概念。",
            "逻辑成绩提高让学生更有信心。",
        ],
        "explanation": "新增讲评课提供了替代原因，使“成绩提高源于新教材”的因果解释变弱。",
    },
    {
        "type": "解释",
        "stem": "某同学刷题量减少后，逻辑正确率反而提高。以下哪项最能解释这一现象？",
        "correct": "他减少了机械刷题，增加了错因复盘和条件关系整理。",
        "distractors": [
            "他更换了手机壁纸。",
            "他每天学习时间完全没有变化。",
            "他不再学习英语。",
            "他把题目按年份重新命名。",
        ],
        "explanation": "减少数量但提高质量，可以解释刷题量下降而正确率上升的表面矛盾。",
    },
    {
        "type": "谬误识别",
        "stem": "某人说：这位同学一次模考没考好，所以他一定不适合备考。该论证最主要的问题是：",
        "correct": "以偏概全",
        "distractors": ["诉诸权威", "循环论证", "偷换概念", "诉诸多数"],
        "explanation": "由一次模考表现推出整体能力判断，样本过少，属于以偏概全。",
    },
    {
        "type": "加强",
        "stem": "某机构认为：限时训练能显著提升逻辑题解题速度。以下哪项最能加强这一判断？",
        "correct": "同一批学生在限时训练前后，题型难度相当而平均用时明显下降。",
        "distractors": [
            "限时训练的页面颜色更醒目。",
            "部分学生觉得训练过程紧张。",
            "逻辑题包含概念、判断、推理和论证。",
            "该机构还提供数学课程。",
        ],
        "explanation": "同一批学生前后对比且难度相当，能较好支持限时训练提升速度。",
    },
    {
        "type": "削弱",
        "stem": "有人说：只要做题数量足够多，逻辑成绩一定会提高。以下哪项最能削弱该观点？",
        "correct": "不少学生大量刷题但不复盘错因，重复错误并未减少。",
        "distractors": [
            "做题数量可以用表格记录。",
            "有些逻辑题题干较长。",
            "题库中包含不同年份的题。",
            "有些学生喜欢晚上学习。",
        ],
        "explanation": "大量刷题并不必然减少错误，说明做题数量不是成绩提高的充分条件。",
    },
    {
        "type": "解释",
        "stem": "同一套逻辑题，第一次测试正确率较低，第二次测试正确率明显提高。以下哪项最能解释这一现象？",
        "correct": "第一次测试后，学生集中复盘了题干条件和错误选项的设置方式。",
        "distractors": [
            "第二次测试的教室更安静。",
            "所有学生都换了同一种笔。",
            "第一次测试在上午进行。",
            "题目编号在第二次测试中被保留。",
        ],
        "explanation": "复盘后掌握条件关系和干扰项规律，能解释二测正确率提升。",
    },
    {
        "type": "谬误识别",
        "stem": "有人说：很多人都推荐这套资料，所以它一定最有效。该论证最主要的问题是：",
        "correct": "诉诸多数",
        "distractors": ["以偏概全", "因果倒置", "人身攻击", "偷换概念"],
        "explanation": "流行或被多数推荐并不能直接证明资料最有效，属于诉诸多数。",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Z001 logic reasoning questions from part 5-7 topic patterns.")
    parser.add_argument("--count", type=int, default=300, help="Number of questions to generate.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output JSON path.")
    parser.add_argument("--review", default=str(DEFAULT_REVIEW), help="Review markdown path.")
    parser.add_argument("--seed", type=int, default=20260428, help="Deterministic random seed.")
    return parser.parse_args()


def normalize_stem(value: str) -> str:
    return re.sub(r"\s+", "", value or "").strip()


def load_existing_stems() -> set[str]:
    stems: set[str] = set()
    for path in (PROJECT_ROOT / "data").glob("*.json"):
        if path.resolve() == DEFAULT_OUTPUT.resolve():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        questions = payload.get("questions") if isinstance(payload, dict) else payload
        if not isinstance(questions, list):
            continue
        for question in questions:
            if isinstance(question, dict) and question.get("stem"):
                stems.add(normalize_stem(str(question["stem"])))
    return stems


def pick(values: list[str], index: int, offset: int = 0) -> str:
    return values[(index + offset) % len(values)]


def make_options(correct: str, distractors: list[str], rng: random.Random, include_e: bool = False) -> tuple[dict[str, str], str]:
    values: list[str] = []
    for value in [correct, *distractors]:
        if value and value not in values:
            values.append(value)
    needed = 4
    fallback_index = 1
    while len(values) < needed:
        values.append(f"由题干无法推出的干扰项{fallback_index}")
        fallback_index += 1
    values = values[:needed]
    rng.shuffle(values)
    labels = ["A", "B", "C", "D"]
    options = {label: value for label, value in zip(labels, values)}
    answer = next(label for label, value in options.items() if value == correct)
    return options, answer


def question(
    *,
    stem: str,
    module: str,
    submodule: str,
    correct: str,
    distractors: list[str],
    explanation: str,
    difficulty: int,
    rng: random.Random,
    include_e: bool = False,
) -> dict:
    options, answer = make_options(correct, distractors, rng, include_e=include_e)
    payload = {
        "exam_code": "Z001",
        "subject": "逻辑推理",
        "module": module,
        "submodule": submodule,
        "question_type": "single_choice",
        "stem": stem,
        "option_a": options["A"],
        "option_b": options["B"],
        "option_c": options["C"],
        "option_d": options["D"],
        "answer": answer,
        "explanation": explanation,
        "difficulty": difficulty,
        "source_type": "ai_generated",
        "source_year": 2026,
        "passage_id": None,
    }
    return payload


def concept_kind(index: int, difficulty: int, rng: random.Random) -> dict:
    phrase, correct, reason = CONCEPT_CASES[index % len(CONCEPT_CASES)]
    return question(
        stem=f"下列关于概念{phrase}的判断，哪一项最准确？",
        module="概念",
        submodule="概念种类",
        correct=correct,
        distractors=["单独概念", "普遍概念", "集合概念", "负概念", "正概念"],
        explanation=f"{phrase}属于{correct}，因为{reason}",
        difficulty=difficulty,
        rng=rng,
    )


def concept_relation(index: int, difficulty: int, rng: random.Random) -> dict:
    left, right, correct, reason = RELATION_CASES[index % len(RELATION_CASES)]
    return question(
        stem=f"从外延关系看，“{left}”与“{right}”之间最恰当的关系是：",
        module="概念",
        submodule="概念关系",
        correct=correct,
        distractors=["全同关系", "真包含于关系", "真包含关系", "交叉关系", "全异关系"],
        explanation=f"二者属于{correct}，因为{reason}",
        difficulty=difficulty,
        rng=rng,
        include_e=difficulty >= 3,
    )


def definition_question(index: int, difficulty: int, rng: random.Random) -> dict:
    definition, correct, reason = DEFINITION_CASES[index % len(DEFINITION_CASES)]
    return question(
        stem=f"对定义“{definition}”的评价，哪一项最恰当？",
        module="概念",
        submodule="定义",
        correct=correct,
        distractors=["定义过宽", "定义过窄", "同语反复", "循环定义", "正确揭示本质属性"],
        explanation=f"该定义的主要特点是：{correct}。{reason}",
        difficulty=difficulty,
        rng=rng,
        include_e=difficulty >= 3,
    )


def division_question(index: int, difficulty: int, rng: random.Random) -> dict:
    base = pick(["学习资料", "训练任务", "逻辑题", "复盘记录", "课程资源"], index)
    stem = f"把{base}分为“真题类、模拟类、纸质类和电子类”。对这一划分评价最恰当的是："
    return question(
        stem=stem,
        module="概念",
        submodule="划分",
        correct="划分标准不一",
        distractors=["划分正确", "划分不全", "多出子项", "子项互不相容且穷尽母项"],
        explanation="“真题/模拟”按来源划分，“纸质/电子”按载体划分，混用了不同标准。",
        difficulty=difficulty,
        rng=rng,
    )


def judgment_kind(index: int, difficulty: int, rng: random.Random) -> dict:
    item = pick(ITEMS, index)
    quality = pick(QUALITIES, index)
    stem = f"命题“有些{item}不是{quality}的”属于哪一种性质判断？"
    return question(
        stem=stem,
        module="判断",
        submodule="判断种类",
        correct="特称否定判断",
        distractors=["全称肯定判断", "全称否定判断", "特称肯定判断", "必要条件假言判断"],
        explanation="“有些S不是P”的标准形式是特称否定判断。",
        difficulty=difficulty,
        rng=rng,
    )


def judgment_relation(index: int, difficulty: int, rng: random.Random) -> dict:
    item = pick(ITEMS, index)
    quality = pick(QUALITIES, index)
    return question(
        stem=f"命题“所有{item}都是{quality}的”与命题“有些{item}不是{quality}的”之间的真假关系是：",
        module="判断",
        submodule="判断关系",
        correct="矛盾关系",
        distractors=["反对关系", "下反对关系", "差等关系", "等值关系"],
        explanation="SAP 与 SOP 不能同真、不能同假，属于矛盾关系。",
        difficulty=difficulty,
        rng=rng,
        include_e=difficulty >= 3,
    )


def conditional_chain(index: int, difficulty: int, rng: random.Random) -> dict:
    context = pick(CONTEXTS, index)
    a = f"{pick(SUBJECTS, index)}完成条件关系整理"
    b = f"{pick(SUBJECTS, index, 3)}能识别充分条件"
    c = f"{pick(SUBJECTS, index, 6)}能稳定完成演绎推理"
    stem = f"{context}有如下规则：如果{a}，那么{b}；如果{b}，那么{c}。现在确认并非{c}。根据以上条件，可以推出："
    return question(
        stem=stem,
        module="推理",
        submodule="演绎推理",
        correct=f"并非{a}",
        distractors=[a, b, f"并非{b}", c, "以上均不能确定"],
        explanation="由A→B、B→C可得A→C；再由非C，根据逆否命题可推出非A。",
        difficulty=difficulty,
        rng=rng,
        include_e=difficulty >= 3,
    )


def necessary_condition(index: int, difficulty: int, rng: random.Random) -> dict:
    a = f"{pick(SUBJECTS, index)}掌握概念关系"
    b = f"{pick(SUBJECTS, index, 4)}能正确处理划分题"
    stem = f"只有{a}，才{b}。现已知{b}。由此一定可以推出："
    return question(
        stem=stem,
        module="推理",
        submodule="演绎推理",
        correct=a,
        distractors=[f"并非{a}", f"并非{b}", "二者都不能推出", f"{a}不是{b}的必要条件"],
        explanation="“只有A才B”等值于B→A；已知B成立，所以A一定成立。",
        difficulty=difficulty,
        rng=rng,
    )


def syllogism_question(index: int, difficulty: int, rng: random.Random) -> dict:
    s = pick(ITEMS, index)
    m = pick(QUALITIES, index)
    p = pick(["值得优先复盘", "适合纳入本周计划", "需要记录错因", "适合限时训练"], index)
    context = pick(CONTEXTS, index)
    stem = f"已知：所有{m}的{s}都是{p}的；有些{context}使用的{s}是{m}的。由此可以推出："
    return question(
        stem=stem,
        module="推理",
        submodule="演绎推理",
        correct=f"有些{context}使用的{s}是{p}的",
        distractors=[
            f"所有{context}使用的{s}都是{p}的",
            f"有些{p}的{s}不是{m}的",
            f"所有{p}的{s}都是{m}的",
            f"没有{context}使用的{s}是{p}的",
        ],
        explanation="全称肯定命题和特称肯定命题串联，只能推出对应的特称肯定结论，不能扩大为全称。",
        difficulty=difficulty,
        rng=rng,
    )


def induction_question(index: int, difficulty: int, rng: random.Random) -> dict:
    context = pick(CONTEXTS, index)
    item = pick(ITEMS, index)
    stem = f"{context}抽查了20份{item}，发现其中16份在复盘后同类错误减少。下列哪项结论最谨慎、最符合归纳推理要求？"
    return question(
        stem=stem,
        module="推理",
        submodule="归纳推理",
        correct="复盘可能有助于减少同类错误，但仍需更多样本验证",
        distractors=[
            "所有考生只要复盘就一定不再犯错",
            "复盘对任何题型都没有作用",
            "只要做题量足够大，就不需要复盘",
            "这20份样本足以证明全部考生都会提分",
        ],
        explanation="归纳结论应保持概率性和谨慎性，不能从有限样本推出绝对结论。",
        difficulty=difficulty,
        rng=rng,
    )


def analogy_question(index: int, difficulty: int, rng: random.Random) -> dict:
    pairs = [
        ("证据", "结论", "地基", "建筑", "前者支撑后者"),
        ("钥匙", "锁", "密码", "账户", "前者用于开启或进入后者"),
        ("地图", "路线", "提纲", "文章", "前者帮助把握后者结构"),
        ("医生", "诊断", "教师", "教学", "前者从事后者这种主要活动"),
        ("词典", "词语", "百科", "知识", "前者解释或检索后者"),
    ]
    a, b, c, d, reason = pairs[index % len(pairs)]
    return question(
        stem=f"“{a}之于{b}”与下列哪一组词语之间的逻辑关系最相似？",
        module="推理",
        submodule="类比推理",
        correct=f"{c}之于{d}",
        distractors=["讲义之于书包", "试卷之于铅笔", "老师之于桌椅", "时间之于颜色"],
        explanation=f"题干关系为：{reason}。正确项与题干保持相同关系。",
        difficulty=difficulty,
        rng=rng,
    )


def comprehensive_question(index: int, difficulty: int, rng: random.Random) -> dict:
    a = pick(SUBJECTS, index)
    b = pick(SUBJECTS, index, 1)
    c = pick(SUBJECTS, index, 2)
    d = pick(SUBJECTS, index, 3)
    context = pick(CONTEXTS, index)
    round_name = f"第{index % 9 + 1}轮"
    stem = (
        f"{context}{round_name}训练安排满足：如果{a}参加，则{b}参加；如果{b}参加，则{c}参加；"
        f"{a}和{d}至少有一人参加；已知{d}没有参加。根据以上条件，必然可以推出："
    )
    return question(
        stem=stem,
        module="推理",
        submodule="综合推理",
        correct=f"{c}参加",
        distractors=[f"{a}不参加", f"{b}不参加", f"{d}参加", "无法确定任何人是否参加"],
        explanation=f"由“{a}或{d}”且{d}不参加，可得{a}参加；再由{a}→{b}、{b}→{c}，推出{c}参加。",
        difficulty=difficulty,
        rng=rng,
    )


def argument_question(index: int, difficulty: int, rng: random.Random) -> dict:
    case = ARGUMENT_CASES[index % len(ARGUMENT_CASES)]
    context = pick(CONTEXTS, index)
    round_name = f"第{index % 11 + 1}次讨论中"
    module_map = {
        "加强": "加强",
        "削弱": "削弱",
        "解释": "解释",
        "谬误识别": "谬误识别",
    }
    return question(
        stem=f"{context}{round_name}，{case['stem']}",
        module="论证",
        submodule=module_map[case["type"]],
        correct=case["correct"],
        distractors=case["distractors"],
        explanation=case["explanation"],
        difficulty=difficulty,
        rng=rng,
        include_e=difficulty >= 4,
    )


def quantitative_flaw(index: int, difficulty: int, rng: random.Random) -> dict:
    context = pick(CONTEXTS, index)
    round_name = f"第{index % 10 + 1}次统计"
    stem = (
        f"{context}{round_name}发现：前10名考生中有8人每天做逻辑题，于是得出结论："
        "只要每天做逻辑题，就一定能进入前10名。该论证最主要的问题是："
    )
    return question(
        stem=stem,
        module="论证",
        submodule="谬误识别",
        correct="把相关关系误当作充分条件",
        distractors=["正确使用了必要条件推理", "证明了所有刷题者都会高分", "属于完全归纳推理", "排除了所有其他影响因素"],
        explanation="高分者中多数刷题，只能说明二者可能相关，不能推出刷题是进入前10名的充分条件。",
        difficulty=difficulty,
        rng=rng,
    )


def hidden_assumption(index: int, difficulty: int, rng: random.Random) -> dict:
    context = pick(CONTEXTS, index)
    round_name = f"第{index % 12 + 1}次产品复盘中"
    stem = f"{context}{round_name}认为：某APP新增错题本后，用户留存率上升，因此错题本功能导致留存率上升。以下哪项是该论证需要假设的？"
    return question(
        stem=stem,
        module="论证",
        submodule="加强",
        correct="同期没有其他足以显著提高留存率的新功能或活动",
        distractors=[
            "所有用户都喜欢蓝色界面",
            "错题本只能记录逻辑题",
            "留存率上升一定代表学习效果提高",
            "用户从不使用其他学习工具",
            "该APP不需要任何题库内容",
        ],
        explanation="若同期存在其他强影响因素，就不能把留存率上升归因于错题本。排除替代原因是该论证的重要假设。",
        difficulty=difficulty,
        rng=rng,
        include_e=True,
    )


BUILDERS_BY_DIFFICULTY = {
    1: [concept_kind, concept_relation, definition_question, division_question, judgment_kind, judgment_relation],
    2: [
        concept_relation,
        definition_question,
        division_question,
        judgment_relation,
        conditional_chain,
        necessary_condition,
        syllogism_question,
        analogy_question,
    ],
    3: [
        definition_question,
        division_question,
        conditional_chain,
        necessary_condition,
        syllogism_question,
        induction_question,
        analogy_question,
        argument_question,
    ],
    4: [
        concept_relation,
        definition_question,
        division_question,
        conditional_chain,
        induction_question,
        analogy_question,
        argument_question,
        comprehensive_question,
        hidden_assumption,
        quantitative_flaw,
    ],
    5: [
        conditional_chain,
        syllogism_question,
        induction_question,
        analogy_question,
        argument_question,
        comprehensive_question,
        hidden_assumption,
        quantitative_flaw,
    ],
}


def target_distribution(count: int) -> dict[int, int]:
    ratios = {1: 0.14, 2: 0.24, 3: 0.28, 4: 0.22, 5: 0.12}
    targets = {level: int(count * ratio) for level, ratio in ratios.items()}
    while sum(targets.values()) < count:
        targets[3] += 1
    while sum(targets.values()) > count:
        targets[3] -= 1
    return targets


def generate(count: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    existing_stems = load_existing_stems()
    seen = set(existing_stems)
    questions: list[dict] = []
    targets = target_distribution(count)

    for difficulty, target in targets.items():
        builders = BUILDERS_BY_DIFFICULTY[difficulty]
        local_count = 0
        attempt = 0
        while local_count < target:
            builder = builders[attempt % len(builders)]
            question_payload = builder(attempt + difficulty * 1000, difficulty, rng)
            key = normalize_stem(question_payload["stem"])
            if key not in seen:
                questions.append(question_payload)
                seen.add(key)
                local_count += 1
            attempt += 1
            if attempt > target * 30:
                raise RuntimeError(f"Unable to generate enough unique difficulty {difficulty} questions")

    rng.shuffle(questions)
    return questions


def write_review(questions: list[dict], review_path: Path) -> None:
    by_difficulty = Counter(question["difficulty"] for question in questions)
    by_module = Counter(question["module"] for question in questions)
    by_submodule = Counter(f"{question['module']} / {question['submodule']}" for question in questions)
    lines = [
        "# Z001 逻辑推理 7讲5-7 分难度题库批次 001",
        "",
        "本批次为基于逻辑推理资料题型结构与考试知识树生成的仿真训练题，避免直接复刻原材料题干。",
        "",
        f"- 总题数：{len(questions)}",
        "- exam_code：Z001",
        "- subject：逻辑推理",
        "- source_type：ai_generated",
        "- source_year：2026",
        "",
        "## 难度分布",
    ]
    for difficulty in sorted(by_difficulty):
        lines.append(f"- 难度 {difficulty}：{by_difficulty[difficulty]} 题")
    lines.extend(["", "## 一级模块分布"])
    for module, value in sorted(by_module.items()):
        lines.append(f"- {module}：{value} 题")
    lines.extend(["", "## 二级模块分布"])
    for submodule, value in sorted(by_submodule.items()):
        lines.append(f"- {submodule}：{value} 题")
    review_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_path = Path(args.output).resolve()
    review_path = Path(args.review).resolve()
    questions = generate(args.count, args.seed)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({"questions": questions}, ensure_ascii=False, indent=2), encoding="utf-8")
    write_review(questions, review_path)
    print(f"Generated {len(questions)} questions")
    print(f"Output: {output_path}")
    print(f"Review: {review_path}")
    print(f"Difficulty: {dict(sorted(Counter(q['difficulty'] for q in questions).items()))}")
    print(f"Modules: {dict(sorted(Counter(q['module'] for q in questions).items()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
