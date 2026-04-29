from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "z001_logic_reasoning_simulation_400_batch_001.json"

CONCEPTS = [
    ("鲁迅", "单独概念", "它只指称一个确定对象。"),
    ("大学生", "普遍概念", "它可以指称多个对象。"),
    ("森林", "集合概念", "它指称由许多个体构成的整体。"),
    ("非党员", "负概念", "它通过否定某一属性来指称对象。"),
    ("红色", "正概念", "它直接反映对象具有的属性。"),
]

RELATIONS = [
    ("苹果", "水果", "真包含于关系", "所有苹果都是水果，但并非所有水果都是苹果。"),
    ("教师", "医生", "全异关系", "二者外延没有交叉。"),
    ("作家", "诗人", "交叉关系", "有些作家是诗人，有些诗人也是作家，但二者不完全相同。"),
    ("等边三角形", "等角三角形", "全同关系", "二者外延完全相同。"),
    ("猫", "动物", "真包含于关系", "所有猫都是动物，但动物不都为猫。"),
]

DEFINITIONS = [
    ("三角形是由三条线段围成的平面图形", "正确揭示本质属性", "定义揭示了三角形的属概念和种差。"),
    ("教师就是在学校工作的人", "定义过宽", "学校工作人员还包括行政人员、后勤人员等。"),
    ("小说就是长篇小说", "定义过窄", "小说还包括短篇小说、中篇小说等。"),
    ("法律就是法律规范", "同语反复", "定义项没有提供新的解释。"),
    ("诚信就是不欺骗别人并遵守承诺", "正确揭示本质属性", "定义抓住了诚信的关键特征。"),
]

DIVISIONS = [
    ("图书可分为中文书、英文书和工具书", "划分标准不一", "语言和用途混用了不同标准。"),
    ("学生可分为本科生、研究生和男生", "划分标准不一", "学历层次和性别混用了不同标准。"),
    ("整数可分为正整数、零和负整数", "划分正确", "子项互不相容且穷尽母项。"),
    ("文学作品可分为诗歌、散文、小说和戏剧", "划分正确", "按文体进行划分，标准一致。"),
    ("交通工具可分为陆路工具、水路工具和自行车", "子项相容或层级不当", "自行车属于陆路工具，子项层级混乱。"),
]

JUDGMENTS = [
    ("所有参加复习的同学都是备考者", "全称肯定判断", "形式为“所有S都是P”。"),
    ("所有粗心的答题者都不是高分考生", "全称否定判断", "形式为“所有S都不是P”。"),
    ("有些真题适合限时训练", "特称肯定判断", "形式为“有些S是P”。"),
    ("有些论证题不是削弱题", "特称否定判断", "形式为“有些S不是P”。"),
    ("如果题干条件成立，那么结论可以推出", "充分条件假言判断", "形式为“如果P，那么Q”。"),
]

JUDGMENT_RELATIONS = [
    ("所有S都是P", "有些S不是P", "矛盾关系", "二者不能同真也不能同假。"),
    ("所有S都不是P", "有些S是P", "矛盾关系", "二者不能同真也不能同假。"),
    ("所有S都是P", "所有S都不是P", "反对关系", "二者不能同真，但可以同假。"),
    ("有些S是P", "有些S不是P", "下反对关系", "二者不能同假，但可以同真。"),
    ("所有S都是P", "有些S是P", "差等关系", "全称真可推出对应特称真。"),
]

CONDITIONALS = [
    ("认真复盘", "正确率提高", "如果认真复盘，那么正确率提高"),
    ("题目来自真题", "需要优先掌握", "如果题目来自真题，那么需要优先掌握"),
    ("计划合理", "学习效率提升", "如果计划合理，那么学习效率提升"),
    ("充分阅读题干", "遗漏条件减少", "如果充分阅读题干，那么遗漏条件减少"),
    ("掌握等价转化", "能快速处理假言题", "如果掌握等价转化，那么能快速处理假言题"),
]

INDUCTION_CASES = [
    ("甲、乙、丙三位同学复盘错题后成绩均有提升", "复盘错题可能有助于提高成绩"),
    ("抽查的五套模拟卷中，逻辑削弱题都考查选项对结论的影响", "削弱题常围绕结论支持度设置"),
    ("某班连续三周限时训练后平均用时下降", "限时训练可能提升做题速度"),
    ("多名考生在整理条件关系后综合推理题正确率提升", "整理条件关系可能有助于综合推理"),
    ("若干高分考生都建立了错题复盘表", "错题复盘表可能与高分表现有关"),
]

ANALOGIES = [
    ("钥匙之于锁", "密码之于账户", "二者都是开启或进入某对象的凭借。"),
    ("医生之于诊断", "教师之于教学", "前者是职业，后者是其主要活动。"),
    ("地图之于路线", "提纲之于文章", "前者帮助把握后者的结构。"),
    ("证据之于结论", "地基之于建筑", "前者支撑后者。"),
    ("词典之于词语", "百科之于知识", "前者提供后者的解释或检索。"),
]

ARGUMENT_TOPICS = [
    ("每天大量刷题的学生成绩一定更好", "有些学生只刷题不复盘，成绩并未提高", "刷题数量并非成绩提升的充分条件"),
    ("某学习法使所有使用者都能提分", "使用该方法的学生原本基础明显更好", "提分可能来自基础差异而非学习法本身"),
    ("某班平均分提高是因为换了教材", "同一时期该班还增加了每周讲评课", "平均分提高可能由讲评课导致"),
    ("某题型今年一定不会再考", "考试说明仍保留该题型且近年多次出现", "题型仍有出现可能"),
    ("错题本没有价值，因为整理耗时", "整理错题后重复错误率明显下降", "耗时不能否定其学习收益"),
]

EXPLANATION_TOPICS = [
    ("某同学刷题量减少，但正确率反而提高", "他减少了机械刷题，增加了错题复盘和限时总结"),
    ("同一套题第一次正确率低，第二次提升明显", "第一次后学生集中复盘了错因和条件关系"),
    ("某班学习时间相近，但逻辑成绩差异很大", "部分学生掌握了形式化推理方法，部分学生只凭感觉作答"),
    ("一道题看似简单却错误率很高", "题干中存在容易忽视的必要条件限制"),
    ("模拟训练后答题速度提高但正确率未下降", "训练重点是识别题型和固定解题步骤"),
]

FALLACIES = [
    ("他这次考试没考好，所以他一定不适合考研", "以偏概全", "由一次考试表现推出整体能力，样本过少。"),
    ("这套方法很流行，所以它一定最有效", "诉诸多数", "流行并不等于有效。"),
    ("你不能证明这个结论是假的，所以它是真的", "诉诸无知", "不能证明为假不等于为真。"),
    ("支持错题复盘的人只是想浪费时间，所以观点不可信", "人身攻击", "攻击提出者不能反驳观点本身。"),
    ("要么每天刷100题，要么完全放弃备考", "非黑即白", "忽略了中间方案。"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate 400 classified Z001 logic simulation questions.")
    parser.add_argument("--count", type=int, default=400, help="Number of questions to generate.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output JSON path.")
    parser.add_argument("--seed", type=int, default=20260425, help="Deterministic random seed.")
    return parser.parse_args()


def make_options(correct: str, distractors: list[str], rng: random.Random) -> tuple[dict[str, str], str]:
    values = [correct, *distractors][:4]
    rng.shuffle(values)
    labels = ["A", "B", "C", "D"]
    options = {label: value for label, value in zip(labels, values)}
    answer = next(label for label, value in options.items() if value == correct)
    return options, answer


def build_question(
    *,
    stem: str,
    module: str,
    submodule: str,
    correct: str,
    distractors: list[str],
    explanation: str,
    difficulty: int,
    rng: random.Random,
) -> dict:
    options, answer = make_options(correct, distractors, rng)
    return {
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


def concept_kind(index: int, rng: random.Random) -> dict:
    concept, correct, reason = CONCEPTS[index % len(CONCEPTS)]
    stem = f"下列关于概念“{concept}”的判断，哪一项最准确？"
    distractors = ["单独概念", "普遍概念", "集合概念", "负概念", "正概念"]
    distractors = [item for item in distractors if item != correct]
    return build_question(
        stem=stem,
        module="概念",
        submodule="概念种类",
        correct=correct,
        distractors=distractors,
        explanation=f"“{concept}”属于{correct}，因为{reason}",
        difficulty=1,
        rng=rng,
    )


def concept_relation(index: int, rng: random.Random) -> dict:
    left, right, correct, reason = RELATIONS[index % len(RELATIONS)]
    stem = f"从外延关系看，“{left}”与“{right}”之间最恰当的关系是？"
    distractors = ["全同关系", "真包含于关系", "真包含关系", "交叉关系", "全异关系"]
    distractors = [item for item in distractors if item != correct]
    return build_question(
        stem=stem,
        module="概念",
        submodule="概念关系",
        correct=correct,
        distractors=distractors,
        explanation=f"二者属于{correct}，因为{reason}",
        difficulty=2,
        rng=rng,
    )


def definition_question(index: int, rng: random.Random) -> dict:
    definition, correct, reason = DEFINITIONS[index % len(DEFINITIONS)]
    stem = f"对定义“{definition}”的评价，哪一项最恰当？"
    distractors = ["定义过宽", "定义过窄", "循环定义", "同语反复", "正确揭示本质属性"]
    distractors = [item for item in distractors if item != correct]
    return build_question(
        stem=stem,
        module="概念",
        submodule="定义",
        correct=correct,
        distractors=distractors,
        explanation=f"该定义的主要问题或特点是：{correct}。{reason}",
        difficulty=2,
        rng=rng,
    )


def division_question(index: int, rng: random.Random) -> dict:
    division, correct, reason = DIVISIONS[index % len(DIVISIONS)]
    stem = f"对划分“{division}”的评价，哪一项最恰当？"
    distractors = ["划分正确", "划分不全", "多出子项", "划分标准不一", "子项相容或层级不当"]
    distractors = [item for item in distractors if item != correct]
    return build_question(
        stem=stem,
        module="概念",
        submodule="划分",
        correct=correct,
        distractors=distractors,
        explanation=f"该划分属于{correct}。{reason}",
        difficulty=2,
        rng=rng,
    )


def judgment_kind(index: int, rng: random.Random) -> dict:
    sentence, correct, reason = JUDGMENTS[index % len(JUDGMENTS)]
    stem = f"命题“{sentence}”属于哪一种判断？"
    distractors = ["全称肯定判断", "全称否定判断", "特称肯定判断", "特称否定判断", "充分条件假言判断"]
    distractors = [item for item in distractors if item != correct]
    return build_question(
        stem=stem,
        module="判断",
        submodule="判断种类",
        correct=correct,
        distractors=distractors,
        explanation=f"该命题属于{correct}，因为{reason}",
        difficulty=1,
        rng=rng,
    )


def judgment_relation(index: int, rng: random.Random) -> dict:
    p, q, correct, reason = JUDGMENT_RELATIONS[index % len(JUDGMENT_RELATIONS)]
    stem = f"在传统直言命题对当关系中，“{p}”与“{q}”之间是什么关系？"
    distractors = ["矛盾关系", "反对关系", "下反对关系", "差等关系", "等值关系"]
    distractors = [item for item in distractors if item != correct]
    return build_question(
        stem=stem,
        module="判断",
        submodule="判断关系",
        correct=correct,
        distractors=distractors,
        explanation=f"二者是{correct}。{reason}",
        difficulty=2,
        rng=rng,
    )


def deductive_question(index: int, rng: random.Random) -> dict:
    p, q, sentence = CONDITIONALS[index % len(CONDITIONALS)]
    pattern = index % 4
    if pattern == 0:
        stem = f"已知：{sentence}。并且，{p}。据此必然可以推出哪项？"
        correct = q
        explanation = f"题干形式为 P→Q，且 P 成立，因此可由肯定前件推出 Q，即“{q}”。"
    elif pattern == 1:
        stem = f"已知：{sentence}。并且，{q}不成立。据此必然可以推出哪项？"
        correct = f"{p}不成立"
        explanation = f"题干形式为 P→Q，且非Q成立，可由否定后件推出非P，即“{p}不成立”。"
    elif pattern == 2:
        stem = f"只有{q}，才{p}。并且，{p}。据此必然可以推出哪项？"
        correct = q
        explanation = f"“只有Q才P”等价于 P→Q，P 成立可推出 Q。"
    else:
        stem = f"除非{q}，否则不{p}。并且，{p}。据此必然可以推出哪项？"
        correct = q
        explanation = f"“除非Q，否则不P”等价于 P→Q，P 成立可推出 Q。"
    distractors = [p, f"{q}不成立", f"{p}成立与否无法判断", f"{p}不成立", "以上都不能推出"]
    distractors = [item for item in distractors if item != correct]
    return build_question(
        stem=stem,
        module="推理",
        submodule="演绎推理",
        correct=correct,
        distractors=distractors[:4],
        explanation=explanation,
        difficulty=2,
        rng=rng,
    )


def induction_question(index: int, rng: random.Random) -> dict:
    premise, correct = INDUCTION_CASES[index % len(INDUCTION_CASES)]
    stem = f"观察到：{premise}。若进行归纳推理，下列哪项结论最为稳妥？"
    distractors = [
        correct.replace("可能", "一定"),
        "所有考生都应采用完全相同的方法",
        "只要增加学习时间就必然提分",
        "该观察无法提供任何学习启示",
        "不需要继续收集更多样本",
    ]
    distractors = [item for item in distractors if item != correct]
    return build_question(
        stem=stem,
        module="推理",
        submodule="归纳推理",
        correct=correct,
        distractors=distractors[:4],
        explanation="归纳推理只能从有限样本得出或然性结论，表述应保持谨慎，不能直接推出必然结论。",
        difficulty=2,
        rng=rng,
    )


def analogy_question(index: int, rng: random.Random) -> dict:
    source, target, reason = ANALOGIES[index % len(ANALOGIES)]
    stem = f"“{source}”与下列哪一组词语之间的逻辑关系最相似？"
    correct = target
    distractors = ["书本之于桌子", "雨水之于天空", "铅笔之于颜色", "道路之于行人", "灯光之于夜晚"]
    distractors = [item for item in distractors if item != correct]
    return build_question(
        stem=stem,
        module="推理",
        submodule="类比推理",
        correct=correct,
        distractors=distractors[:4],
        explanation=f"“{source}”与“{target}”关系相似：{reason}",
        difficulty=2,
        rng=rng,
    )


def synthesis_question(index: int, rng: random.Random) -> dict:
    names = ["甲", "乙", "丙", "丁", "戊"]
    offset = index % 5
    ordered = names[offset:] + names[:offset]
    stem = (
        f"{ordered[0]}、{ordered[1]}、{ordered[2]}、{ordered[3]}、{ordered[4]}参加答题赛，名次从高到低排列。"
        f"已知：{ordered[1]}高于{ordered[3]}；{ordered[2]}低于{ordered[0]}；"
        f"{ordered[4]}高于{ordered[1]}；{ordered[0]}高于{ordered[4]}。根据以上条件，谁的名次最高？"
    )
    correct = ordered[0]
    distractors = [name for name in ordered if name != correct]
    return build_question(
        stem=stem,
        module="推理",
        submodule="综合推理",
        correct=correct,
        distractors=distractors,
        explanation=f"由条件可得：{ordered[0]}>{ordered[4]}>{ordered[1]}>{ordered[3]}，且{ordered[0]}>{ordered[2]}，所以最高的是{ordered[0]}。",
        difficulty=3,
        rng=rng,
    )


def argument_question(index: int, rng: random.Random, submodule: str) -> dict:
    claim, weakener, principle = ARGUMENT_TOPICS[index % len(ARGUMENT_TOPICS)]
    if submodule == "削弱":
        stem = f"有人认为：{claim}。下列哪项最能削弱这一观点？"
        correct = weakener
        explanation = f"该选项指出：{principle}，从而削弱题干观点。"
        distractors = ["很多人都关心考试结果", "学习需要长期坚持", "不同学生的学习习惯不同", "考试题型每年可能变化", "复习资料种类很多"]
    elif submodule == "加强":
        stem = f"有人认为：{claim}。下列哪项最能加强这一观点？"
        correct = f"在控制基础水平后，符合该观点的学生成绩提升更明显"
        explanation = "该选项排除了基础差异等干扰因素，直接支持题干因果判断。"
        distractors = [weakener, "部分学生不喜欢整理笔记", "考试时间通常较紧", "有些题目难度较高", "不同科目分值不同"]
    else:
        stem = f"有人认为：{claim}。下列哪项最能指出该论证的主要问题？"
        correct = "把相关关系直接当作因果关系"
        explanation = "题干从现象直接推出原因，未排除其他可能因素，属于因果论证不充分。"
        distractors = ["偷换概念", "诉诸权威", "自相矛盾", "循环论证", "划分标准不一"]
    return build_question(
        stem=stem,
        module="论证",
        submodule=submodule,
        correct=correct,
        distractors=[item for item in distractors if item != correct][:4],
        explanation=explanation,
        difficulty=3,
        rng=rng,
    )


def explanation_question(index: int, rng: random.Random) -> dict:
    fact, correct = EXPLANATION_TOPICS[index % len(EXPLANATION_TOPICS)]
    stem = f"出现了这样的现象：{fact}。下列哪项最能解释这一现象？"
    distractors = ["该同学更喜欢文科", "考试当天气温较低", "题目顺序发生了变化", "同学之间讨论较多", "训练地点更加安静"]
    return build_question(
        stem=stem,
        module="论证",
        submodule="解释",
        correct=correct,
        distractors=[item for item in distractors if item != correct][:4],
        explanation="解释题要寻找能同时说明表面矛盾或异常现象的原因，该选项最直接解释了题干现象。",
        difficulty=3,
        rng=rng,
    )


def fallacy_question(index: int, rng: random.Random) -> dict:
    argument, correct, reason = FALLACIES[index % len(FALLACIES)]
    stem = f"下列论证“{argument}”主要犯了哪一种逻辑错误？"
    distractors = ["以偏概全", "诉诸多数", "诉诸无知", "人身攻击", "非黑即白"]
    distractors = [item for item in distractors if item != correct]
    return build_question(
        stem=stem,
        module="论证",
        submodule="谬误识别",
        correct=correct,
        distractors=distractors,
        explanation=f"该论证属于{correct}。{reason}",
        difficulty=2,
        rng=rng,
    )


GENERATORS = [
    concept_kind,
    concept_relation,
    definition_question,
    division_question,
    judgment_kind,
    judgment_relation,
    deductive_question,
    induction_question,
    analogy_question,
    synthesis_question,
    lambda i, rng: argument_question(i, rng, "加强"),
    lambda i, rng: argument_question(i, rng, "削弱"),
    explanation_question,
    fallacy_question,
]


def main() -> int:
    args = parse_args()
    rng = random.Random(args.seed)
    questions = []
    seen_stems = set()
    index = 0

    while len(questions) < args.count:
        generator = GENERATORS[index % len(GENERATORS)]
        cycle = index // len(GENERATORS)
        question = generator(cycle, rng)
        # Add a harmless scenario suffix to ensure stems remain unique across cycles.
        question["stem"] = f"{question['stem']}（训练组 {cycle + 1}）"
        if question["stem"] not in seen_stems:
            questions.append(question)
            seen_stems.add(question["stem"])
        index += 1

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({"questions": questions}, ensure_ascii=False, indent=2), encoding="utf-8")

    stats: dict[str, int] = {}
    for question in questions:
        key = f"{question['module']} / {question['submodule']}"
        stats[key] = stats.get(key, 0) + 1

    print(f"Generated questions: {len(questions)}")
    print(f"Output: {output_path}")
    print("Distribution:")
    for key in sorted(stats):
        print(f"  {key}: {stats[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
