from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_PATH = PROJECT_ROOT / "data" / "common_english_language_knowledge_batch_001.json"
REVIEW_PATH = PROJECT_ROOT / "data" / "common_english_language_knowledge_batch_001_review.md"
SQL_PATH = PROJECT_ROOT / "database" / "update_common_english_explanations.sql"


ENGLISH_EXPLANATION_MAP = {
    "Verbs such as demand can take a subjunctive that-clause: should be finished, with should omitted.": (
        "demand 等表示要求、命令、建议的动词后接 that 从句时，常用虚拟语气，即 should + 动词原形，should 可以省略。"
    ),
    "differ in something means to be different with respect to a particular aspect.": (
        "differ in sth. 表示“在某方面不同”，强调差异体现在某一具体方面。"
    ),
    "raise funds is a fixed collocation meaning to collect money.": (
        "raise funds 是固定搭配，表示“筹集资金”。"
    ),
    "revise means to change or improve something after reconsideration; reverse means to turn something around.": (
        "revise 表示“修改、修订”，强调重新考虑后作出改进；reverse 表示“颠倒、反转”，语义不合。"
    ),
    "whether...or not is used to introduce two possibilities.": (
        "whether...or not 用来引出“是否”的两种可能，常用于宾语从句或主语从句。"
    ),
    "This is an emphatic cleft sentence: It was...that...": (
        "本句是强调句型 It is/was...that...，用来强调句中某一成分。"
    ),
    "in accordance with means according to rules or requirements.": (
        "in accordance with 表示“按照、依据”，常与 rules、requirements、regulations 等搭配。"
    ),
    "ambiguous means unclear or having more than one possible meaning.": (
        "ambiguous 表示“含糊的、有歧义的”，指表达不够明确或可能有多种理解。"
    ),
    "emphasis on is the standard collocation.": (
        "emphasis 常与介词 on 搭配，表示“对……的强调”。"
    ),
    "identify is the verb meaning to recognize or determine something.": (
        "identify 是动词，表示“识别、确认”，用于说明认出或确定某事物。"
    ),
    "implementation means carrying a plan or policy into effect.": (
        "implementation 表示“实施、执行”，指把计划或政策真正落实。"
    ),
    "definite means clear and certain, which fits a statement supported by evidence.": (
        "definite 表示“明确的、确定的”，适合描述有证据支持的说法。"
    ),
    "unreliable means not trustworthy; a small sample size can make results unreliable.": (
        "unreliable 表示“不可靠的”，样本量过小时，研究结果往往缺乏可靠性。"
    ),
    "need doing can mean need to be done when the subject receives the action.": (
        "need doing 可表示被动含义，相当于 need to be done，主语是动作的承受者。"
    ),
    "promote means to encourage or support the development of something.": (
        "promote 表示“促进、推动”，强调支持某事物的发展。"
    ),
    "be capable of doing something is a fixed structure.": (
        "be capable of doing sth. 是固定结构，表示“有能力做某事”。"
    ),
    "restore means to repair something and return it to its former condition.": (
        "restore 表示“修复、恢复”，指把事物恢复到原来的状态。"
    ),
    "cast doubt on means to make something seem uncertain.": (
        "cast doubt on 表示“使……受到怀疑”，即让某事显得不确定或不可信。"
    ),
}


SUBMODULE_INTRO = {
    "词汇": "本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。",
    "语法": "本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。",
    "语用": "本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。",
}


SUBMODULE_METHOD = {
    "词汇": "做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。",
    "语法": "排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。",
    "语用": "排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。",
}


def load_questions() -> list[dict]:
    payload = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    questions = payload.get("questions") if isinstance(payload, dict) else payload
    if not isinstance(questions, list):
        raise ValueError("Source JSON must contain a questions array")
    return questions


def answer_text(question: dict) -> str:
    key = f"option_{str(question['answer']).strip().lower()}"
    return str(question.get(key, "")).strip()


def option_summary(question: dict) -> str:
    answer = str(question["answer"]).strip().upper()
    parts: list[str] = []
    for label in ["A", "B", "C", "D"]:
        if label == answer:
            continue
        value = str(question.get(f"option_{label.lower()}", "")).strip()
        if value:
            parts.append(f"{label}. {value}")
    return "；".join(parts)


def normalize_base(explanation: object) -> str:
    text = str(explanation or "").strip()
    return ENGLISH_EXPLANATION_MAP.get(text, text)


def enhance_explanation(question: dict) -> str:
    submodule = str(question.get("submodule") or "").strip()
    answer = str(question.get("answer") or "").strip().upper()
    correct = answer_text(question)
    base = normalize_base(question.get("explanation"))
    others = option_summary(question)

    intro = SUBMODULE_INTRO.get(submodule, "本题考查英语语言知识，需要结合语境、结构和搭配综合判断。")
    method = SUBMODULE_METHOD.get(submodule, "排除选项时，要同时检查语义、语法和搭配是否成立。")

    if "______" in str(question.get("stem", "")):
        target = "空格处"
    else:
        target = "题干所问内容"

    return (
        f"{intro}正确答案为 {answer}（{correct}）。"
        f"{target}应选择该项，核心理由是：{base}"
        f"其余选项（{others}）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。"
        f"{method}"
    )


def sql_quote(value: object) -> str:
    return "'" + str(value or "").replace("'", "''") + "'"


def write_sql(questions: list[dict]) -> None:
    lines = [
        "-- Update detailed Chinese explanations for COMMON English language knowledge questions.",
        "-- Safe to run after the questions have already been imported.",
        "begin;",
        "",
    ]
    for question in questions:
        lines.extend(
            [
                "update public.questions",
                f"set explanation = {sql_quote(question['explanation'])}",
                "where exam_code = 'COMMON'",
                "  and subject = '英语运用'",
                "  and module = '语言知识'",
                f"  and stem = {sql_quote(question['stem'])};",
                "",
            ]
        )
    lines.extend(["commit;", ""])
    SQL_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_review(questions: list[dict]) -> None:
    by_submodule: dict[str, int] = {}
    lengths: list[int] = []
    for question in questions:
        by_submodule[question["submodule"]] = by_submodule.get(question["submodule"], 0) + 1
        lengths.append(len(question["explanation"]))

    lines = [
        "# COMMON 英语运用 语言知识 批次 001",
        "",
        "本批次参考英语（一）语言知识考纲、用户提供的回忆录题型，以及专四语法词汇教材的考点体系生成。",
        "本轮已将答案解析统一优化为中文长解析，重点补充考点判断、正确项依据、排除思路和做题方法。",
        "",
        f"- 总题数：{len(questions)}",
        "- exam_code：COMMON",
        "- subject：英语运用",
        "- module：语言知识",
        "- source_type：ai_generated",
        "- source_year：2026",
        f"- 平均解析长度：{round(sum(lengths) / len(lengths))} 字",
        f"- 最短解析长度：{min(lengths)} 字",
        "",
        "## 子模块分布",
    ]
    for name in ["词汇", "语法", "语用"]:
        lines.append(f"- {name}：{by_submodule.get(name, 0)} 题")
    lines.extend(
        [
            "",
            "## 解析优化口径",
            "- 词汇题：强调语境、词义辨析和固定搭配。",
            "- 语法题：强调句子结构、时态语态、从句和非谓语规则。",
            "- 语用题：强调交际场景、礼貌程度和语篇逻辑。",
        ]
    )
    REVIEW_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    questions = load_questions()
    for question in questions:
        question["explanation"] = enhance_explanation(question)

    SOURCE_PATH.write_text(json.dumps({"questions": questions}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_review(questions)
    write_sql(questions)

    lengths = [len(question["explanation"]) for question in questions]
    print(f"Enhanced questions: {len(questions)}")
    print(f"Average explanation length: {round(sum(lengths) / len(lengths))}")
    print(f"Shortest explanation length: {min(lengths)}")
    print(f"Wrote {SQL_PATH.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
