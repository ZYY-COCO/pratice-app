from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "z001_logic_reasoning_part3_part4_simulation_800_batch_001.json"


CONTEXTS = [
    "港澳台考研备考小组", "图书馆自习区", "线上刷题班", "逻辑冲刺营", "周末模考班",
    "中华文化学习社", "英语阅读训练组", "数学基础答疑群", "真题复盘小组", "错题整理社群",
    "春季集训班", "暑期强化班", "秋季模考队", "冬季冲刺队", "跨校备考联盟",
    "资料整理小组", "限时训练营", "每日打卡群", "综合能力班", "题型归纳小组",
]

SUBJECTS = [
    "甲", "乙", "丙", "丁", "小周", "小林", "小陈", "小许", "阿明", "阿敏",
    "文史组", "逻辑组", "阅读组", "数学组", "资料组", "一班", "二班", "三班", "四班", "五班",
]

ITEMS = [
    "真题", "模拟题", "错题", "阅读材料", "讲义", "笔记", "训练计划", "复盘表", "诊断报告", "课程",
    "选择题", "推理题", "论证题", "分类题", "讲解视频", "学习任务", "测试卷", "专题练习", "题型清单", "知识卡片",
]

QUALITIES = [
    "按时完成", "经过复盘", "来自真题", "难度适中", "有详细解析", "适合限时训练", "覆盖核心考点",
    "包含干扰项", "需要画表", "需要找论点", "需要找论据", "需要识别条件", "需要比较结构",
]

FALLACIES = [
    ("只看一次测试结果就断定某人完全不适合备考", "以偏概全", "由单个样本推出整体结论，样本不足。"),
    ("因为很多人都推荐某方法，所以该方法一定最有效", "诉诸多数", "流行程度不能直接证明方法有效。"),
    ("无法证明某结论为假，所以该结论一定为真", "诉诸无知", "不能由未被证伪直接推出为真。"),
    ("反驳者学习时间很短，所以他的观点不值得讨论", "人身攻击", "攻击提出者不能替代对观点本身的评价。"),
    ("要么每天刷一百题，要么完全放弃备考", "非黑即白", "忽略了中间方案。"),
    ("用‘好方法就是有效的方法，有效的方法就是好方法’来证明方法好", "循环论证", "结论被拿来作为前提。"),
    ("先认定某资料一定准确，再用该资料证明它自己可靠", "循环论证", "证明过程没有提供独立依据。"),
    ("因为某同学用了某笔记后提分，所以所有人使用该笔记都会提分", "以偏概全", "个例不能代表所有人。"),
]


def normalize_stem(value: str) -> str:
    return re.sub(r"\s+", "", value or "").strip()


def load_existing_stems() -> set[str]:
    stems: set[str] = set()
    for path in (PROJECT_ROOT / "data").glob("*.json"):
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


def make_options(correct: str, distractors: list[str], rng: random.Random) -> tuple[dict[str, str], str]:
    values = [correct, *distractors]
    deduped = []
    for value in values:
        if value and value not in deduped:
            deduped.append(value)
    while len(deduped) < 5:
        deduped.append(f"以上判断无法由题干确定{len(deduped)}")
    values = deduped[:5]
    rng.shuffle(values)
    labels = ["A", "B", "C", "D", "E"]
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
        "option_e": options["E"],
        "answer": answer,
        "explanation": explanation,
        "difficulty": difficulty,
        "source_type": "ai_generated",
        "source_year": 2026,
        "passage_id": None,
    }


def pick(seq: list[str], index: int, offset: int = 0) -> str:
    return seq[(index + offset) % len(seq)]


def build_conditional(index: int, rng: random.Random) -> dict:
    context = pick(CONTEXTS, index)
    a = f"{pick(SUBJECTS, index)}完成基础题型梳理"
    b = f"{pick(SUBJECTS, index, 3)}能识别关键条件"
    c = f"{pick(SUBJECTS, index, 6)}能稳定完成综合推理"
    stem = (
        f"{context}中有如下规定：如果{a}，那么{b}；如果{b}，那么{c}。"
        f"现在确认并非{c}。根据以上条件，下列哪项一定成立？"
    )
    correct = f"并非{a}"
    return question(
        stem=stem,
        module="推理",
        submodule="演绎推理",
        correct=correct,
        distractors=[f"{a}", f"{b}", f"并非{b}", f"{c}", "以上均不能确定"],
        explanation="由 A→B、B→C 可得 A→C；再由非 C 根据逆否命题可推出非 A。",
        difficulty=2,
        rng=rng,
    )


def build_syllogism(index: int, rng: random.Random) -> dict:
    s = pick(ITEMS, index)
    m = pick(QUALITIES, index)
    p = pick(["值得优先复盘", "适合纳入本周计划", "需要记录错因", "适合限时训练", "应当重点讲解"], index)
    stem = f"已知：所有{m}的{s}都是{p}的；有些{pick(CONTEXTS, index)}使用的{s}是{m}的。由此可以推出："
    correct = f"有些{pick(CONTEXTS, index)}使用的{s}是{p}的"
    return question(
        stem=stem,
        module="推理",
        submodule="演绎推理",
        correct=correct,
        distractors=[
            f"所有{pick(CONTEXTS, index)}使用的{s}都是{p}的",
            f"有些{p}的{s}不是{m}的",
            f"所有{p}的{s}都是{m}的",
            f"没有{pick(CONTEXTS, index)}使用的{s}是{p}的",
        ],
        explanation="全称肯定命题与特称肯定命题串联，只能推出对应的特称肯定结论，不能扩大为全称结论。",
        difficulty=2,
        rng=rng,
    )


def build_judgment_relation(index: int, rng: random.Random) -> dict:
    s = pick(ITEMS, index)
    p = pick(QUALITIES, index)
    stem = f"命题“所有{s}都是{p}的”与命题“有些{s}不是{p}的”之间的真假关系是："
    return question(
        stem=stem,
        module="判断",
        submodule="判断关系",
        correct="矛盾关系",
        distractors=["反对关系", "下反对关系", "差等关系", "等值关系"],
        explanation="SAP 与 SOP 不能同真、不能同假，属于矛盾关系。",
        difficulty=1,
        rng=rng,
    )


def build_division(index: int, rng: random.Random) -> dict:
    base = pick(["学习资料", "题目", "训练计划", "错题", "课程"], index)
    stem = f"将{base}分为“真题资料、模拟资料、纸质资料和电子资料”。对这一划分评价最恰当的是："
    return question(
        stem=stem,
        module="概念",
        submodule="划分",
        correct="划分标准不一",
        distractors=["划分正确", "划分不全", "多出子项", "子项互相排斥且穷尽母项"],
        explanation="“真题/模拟”按来源划分，“纸质/电子”按载体划分，混用了不同标准。",
        difficulty=2,
        rng=rng,
    )


def build_analogy(index: int, rng: random.Random) -> dict:
    pairs = [
        ("证据", "结论", "地基", "建筑", "前者支撑后者"),
        ("钥匙", "锁", "密码", "账号", "前者用于开启或进入后者"),
        ("地图", "路线", "提纲", "文章", "前者帮助把握后者结构"),
        ("医生", "诊断", "教师", "教学", "前者从事后者这种主要活动"),
        ("词典", "词语", "百科", "知识", "前者解释或检索后者"),
    ]
    a, b, c, d, reason = pairs[index % len(pairs)]
    stem = f"“{a}之于{b}”与下列哪一组词语之间的逻辑关系最相似？"
    return question(
        stem=stem,
        module="推理",
        submodule="类比推理",
        correct=f"{c}之于{d}",
        distractors=["讲义之于书包", "试卷之于铅笔", "老师之于桌椅", "时间之于颜色"],
        explanation=f"题干关系为：{reason}。正确项与题干保持相同关系。",
        difficulty=2,
        rng=rng,
    )


def build_induction(index: int, rng: random.Random) -> dict:
    context = pick(CONTEXTS, index)
    item = pick(ITEMS, index)
    stem = f"在{context}中，抽查的5份{item}都显示：复盘错因后再次作答正确率有所提高。若作归纳推理，下列哪项最稳妥？"
    correct = "复盘错因可能有助于提高再次作答正确率"
    return question(
        stem=stem,
        module="推理",
        submodule="归纳推理",
        correct=correct,
        distractors=[
            "只要复盘错因，所有题目都一定能做对",
            "不复盘错因的人一定无法提高正确率",
            "复盘错因是提高成绩的唯一原因",
            "这5份材料足以证明所有考生都适用该方法",
        ],
        explanation="归纳推理应保持结论的或然性，样本有限时不能推出绝对化结论。",
        difficulty=2,
        rng=rng,
    )


def build_comprehensive(index: int, rng: random.Random) -> dict:
    names = [pick(SUBJECTS, index), pick(SUBJECTS, index, 4), pick(SUBJECTS, index, 8)]
    tasks = ["整理错题", "讲解推理", "制作表格"]
    answer_name = names[index % 3]
    answer_task = tasks[index % 3]
    stem = (
        f"{names[0]}、{names[1]}、{names[2]}三人分别承担整理错题、讲解推理、制作表格三项任务。"
        f"已知：{names[0]}不制作表格；{names[1]}不整理错题；承担讲解推理的人不是{names[2]}。"
        f"若{answer_name}承担{answer_task}，下列哪项最符合题干条件？"
    )
    correct = f"{answer_name}承担{answer_task}"
    return question(
        stem=stem,
        module="推理",
        submodule="综合推理",
        correct=correct,
        distractors=[
            f"{names[0]}制作表格",
            f"{names[1]}整理错题",
            f"{names[2]}讲解推理",
            "三人可承担同一项任务",
        ],
        explanation="综合推理题应逐项排除与已知条件冲突的安排。正确项不与题干限制矛盾。",
        difficulty=3,
        rng=rng,
    )


def build_strengthen(index: int, rng: random.Random) -> dict:
    context = pick(CONTEXTS, index)
    item = pick(ITEMS, index)
    stem = f"{context}认为：只要把{item}按题型整理，逻辑成绩就会明显提升。理由是按题型整理能让学生更快识别解题方法。下列哪项最能加强上述论证？"
    correct = "题型识别速度提升后，学生在同类逻辑题上的正确率通常会提高"
    return question(
        stem=stem,
        module="论证",
        submodule="加强",
        correct=correct,
        distractors=[
            "有些学生不喜欢整理资料",
            "不同学生的基础并不相同",
            "按题型整理会花费一定时间",
            "逻辑题有时也考查阅读速度",
        ],
        explanation="论证从“题型整理提高识别方法”推出“成绩提升”，正确项补上识别速度与正确率之间的桥梁。",
        difficulty=3,
        rng=rng,
    )


def build_weaken(index: int, rng: random.Random) -> dict:
    context = pick(CONTEXTS, index)
    stem = f"{context}发现，参加限时训练的同学本周正确率更高，因此认为限时训练必然能提高正确率。下列哪项最能削弱该论证？"
    correct = "参加限时训练的同学原本基础就明显更好"
    return question(
        stem=stem,
        module="论证",
        submodule="削弱",
        correct=correct,
        distractors=[
            "限时训练需要固定时间",
            "有些题目不适合限时完成",
            "正确率可以用百分比表示",
            "不少同学喜欢在晚上训练",
        ],
        explanation="题干把相关关系当作因果关系。正确项指出基础差异这一替代解释，削弱因果结论。",
        difficulty=3,
        rng=rng,
    )


def build_explain(index: int, rng: random.Random) -> dict:
    context = pick(CONTEXTS, index)
    stem = f"{context}中，小组A刷题数量少于小组B，但小组A的正确率更高。下列哪项最能解释这一现象？"
    correct = "小组A每次训练后都复盘错因并整理同类题，小组B主要追求刷题数量"
    return question(
        stem=stem,
        module="论证",
        submodule="解释",
        correct=correct,
        distractors=[
            "小组B的人数比小组A更多",
            "两个小组使用的纸张颜色不同",
            "小组A每周开会地点不同",
            "小组B成员都知道考试时间",
        ],
        explanation="表面矛盾是“题少但正确率高”。正确项说明训练质量和复盘机制不同，能够解释现象。",
        difficulty=2,
        rng=rng,
    )


def build_fallacy(index: int, rng: random.Random) -> dict:
    argument, correct, reason = FALLACIES[index % len(FALLACIES)]
    stem = f"下列论证“{argument}”主要犯了哪一种逻辑错误？"
    return question(
        stem=stem,
        module="论证",
        submodule="谬误识别",
        correct=correct,
        distractors=["诉诸多数", "人身攻击", "以偏概全", "循环论证", "非黑即白"],
        explanation=reason,
        difficulty=2,
        rng=rng,
    )


BUILDERS = [
    build_conditional,
    build_syllogism,
    build_judgment_relation,
    build_division,
    build_analogy,
    build_induction,
    build_comprehensive,
    build_strengthen,
    build_weaken,
    build_explain,
    build_fallacy,
]


def generate(count: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    existing = load_existing_stems()
    generated: list[dict] = []
    generated_stems: set[str] = set()
    index = 0
    attempts = 0
    while len(generated) < count and attempts < count * 20:
        builder = BUILDERS[index % len(BUILDERS)]
        item = builder(index, rng)
        item["stem"] = f"{item['stem']}（逻辑7讲第3-4讲仿真组{index + 1}）"
        key = normalize_stem(item["stem"])
        if key not in existing and key not in generated_stems:
            generated.append(item)
            generated_stems.add(key)
        index += 1
        attempts += 1
    if len(generated) < count:
        raise RuntimeError(f"Only generated {len(generated)} unique questions out of requested {count}")
    return generated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Z001 logic questions based on logic lessons part 3 and 4.")
    parser.add_argument("--count", type=int, default=800)
    parser.add_argument("--seed", type=int, default=2026042601)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    questions = generate(args.count, args.seed)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"questions": questions}, ensure_ascii=False, indent=2), encoding="utf-8")
    by_submodule: dict[str, int] = {}
    for item in questions:
        key = f"{item['module']}/{item['submodule']}"
        by_submodule[key] = by_submodule.get(key, 0) + 1
    print(f"Generated: {len(questions)}")
    for key, value in sorted(by_submodule.items()):
        print(f"  {key}: {value}")
    print(f"Output: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
