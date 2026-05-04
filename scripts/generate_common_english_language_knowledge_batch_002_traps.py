from __future__ import annotations

import json
import random
import re
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "common_english_language_knowledge_batch_002_traps.json"
REVIEW_PATH = PROJECT_ROOT / "data" / "common_english_language_knowledge_batch_002_traps_review.md"


def normalize_stem(value: str) -> str:
    return re.sub(r"\s+", "", value or "").strip().lower()


def load_existing_stems() -> set[str]:
    stems: set[str] = set()
    for path in (PROJECT_ROOT / "data").glob("*.json"):
        if path.resolve() == OUTPUT_PATH.resolve():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        questions = payload.get("questions") if isinstance(payload, dict) else payload
        if not isinstance(questions, list):
            continue
        for item in questions:
            if isinstance(item, dict) and isinstance(item.get("stem"), str):
                stems.add(normalize_stem(item["stem"]))
    return stems


def make_options(correct: str, distractors: list[str], rng: random.Random) -> tuple[dict[str, str], str]:
    values: list[str] = []
    for value in [correct, *distractors]:
        if value and value not in values:
            values.append(value)
    if len(values) != 4:
        raise ValueError(f"Expected 4 unique options, got {values}")
    rng.shuffle(values)
    labels = ["A", "B", "C", "D"]
    options = dict(zip(labels, values))
    answer = next(label for label, value in options.items() if value == correct)
    return options, answer


def build_question(spec: dict, rng: random.Random) -> dict:
    options, answer = make_options(spec["correct"], spec["distractors"], rng)
    trap_note = spec["trap"]
    explanation = (
        f"本题考查英语运用中的“{spec['submodule']}”。正确答案为 {answer}（{spec['correct']}）。"
        f"{spec['reason']}"
        f"本题陷阱：{trap_note}"
        "做这类题时，要同时检查语义、搭配、词性和句法位置，不能只凭中文大意选择。"
    )
    return {
        "exam_code": "COMMON",
        "subject": "英语运用",
        "module": "语言知识",
        "submodule": spec["submodule"],
        "question_type": "single_choice",
        "stem": spec["stem"],
        "option_a": options["A"],
        "option_b": options["B"],
        "option_c": options["C"],
        "option_d": options["D"],
        "answer": answer,
        "explanation": explanation,
        "difficulty": spec["difficulty"],
        "source_type": "ai_generated",
        "source_year": 2026,
        "passage_id": None,
    }


SPECS = [
    {
        "submodule": "词汇",
        "stem": "The policy was introduced to ______ the pressure on local hospitals.",
        "correct": "relieve",
        "distractors": ["release", "reveal", "revise"],
        "reason": "relieve pressure 表示“缓解压力”，符合医疗资源紧张的语境。",
        "trap": "release 也有“释放”的意思，但不能和 pressure 构成此处的常用搭配；reveal 是“揭示”，revise 是“修改”。",
        "difficulty": 3,
    },
    {
        "submodule": "词汇",
        "stem": "The survey results should be treated with ______ because the sample size is small.",
        "correct": "caution",
        "distractors": ["courage", "confidence", "curiosity"],
        "reason": "with caution 表示“谨慎地”，样本量小意味着结论不能轻易推广。",
        "trap": "confidence 与“相信结果”有关，但 small sample size 恰好提示不能过度自信。",
        "difficulty": 3,
    },
    {
        "submodule": "词汇",
        "stem": "The two accounts of the accident are not ______ with each other.",
        "correct": "consistent",
        "distractors": ["constant", "considerate", "conscious"],
        "reason": "be consistent with 表示“与……一致”，用于比较两种说法是否吻合。",
        "trap": "constant 形近且有“持续的”意思，但不能表达“说法一致”。",
        "difficulty": 3,
    },
    {
        "submodule": "词汇",
        "stem": "The professor asked the students to ______ between fact and opinion.",
        "correct": "distinguish",
        "distractors": ["distribute", "display", "describe"],
        "reason": "distinguish between A and B 是固定搭配，表示“区分 A 和 B”。",
        "trap": "describe 和 display 都能接名词，但不能与 between...and...构成该语义结构。",
        "difficulty": 3,
    },
    {
        "submodule": "词汇",
        "stem": "The new evidence may ______ the original conclusion.",
        "correct": "undermine",
        "distractors": ["undergo", "undertake", "underline"],
        "reason": "undermine 表示“削弱、动摇”，符合 evidence 对 conclusion 的影响。",
        "trap": "underline 是“强调”，看起来和 conclusion 可搭配，但语义方向相反。",
        "difficulty": 4,
    },
    {
        "submodule": "词汇",
        "stem": "The medicine should be taken ______ to the doctor's instructions.",
        "correct": "according",
        "distractors": ["accorded", "accounting", "regarding"],
        "reason": "according to 表示“按照、根据”，是固定搭配。",
        "trap": "regarding 表示“关于”，不能和 to 构成 according to 的含义；accounting 形近但词性不对。",
        "difficulty": 3,
    },
    {
        "submodule": "词汇",
        "stem": "The report failed to ______ the long-term effects of the reform.",
        "correct": "address",
        "distractors": ["deliver", "locate", "announce"],
        "reason": "address a problem/issue 表示“处理、论及某问题”，此处指报告没有论及长期影响。",
        "trap": "deliver a report 是“作报告”，但题干主语已是 report，不能表示“讨论影响”。",
        "difficulty": 4,
    },
    {
        "submodule": "词汇",
        "stem": "The device is small, but it is highly ______ in saving energy.",
        "correct": "effective",
        "distractors": ["efficient", "sufficient", "affective"],
        "reason": "be effective in doing sth. 表示“在某方面有效”，强调效果。",
        "trap": "efficient 也和效率有关，但常指“高效、不浪费”，此处固定结构 effective in 更自然。",
        "difficulty": 4,
    },
    {
        "submodule": "词汇",
        "stem": "Many students found the instructions ______ and asked for clarification.",
        "correct": "ambiguous",
        "distractors": ["ambitious", "obvious", "absolute"],
        "reason": "ambiguous 表示“含糊的、有歧义的”，所以学生需要 clarification。",
        "trap": "ambitious 形近但表示“有雄心的”，不能修饰 instructions 的清晰程度。",
        "difficulty": 3,
    },
    {
        "submodule": "词汇",
        "stem": "The city has made efforts to ______ old buildings rather than tear them down.",
        "correct": "preserve",
        "distractors": ["reserve", "deserve", "observe"],
        "reason": "preserve old buildings 表示“保护老建筑”。",
        "trap": "reserve 是“预留”，observe 是“观察/遵守”，都容易因形近被误选。",
        "difficulty": 3,
    },
    {
        "submodule": "词汇",
        "stem": "The speaker's remarks were ______ to the topic under discussion.",
        "correct": "relevant",
        "distractors": ["relative", "reluctant", "reliable"],
        "reason": "be relevant to 表示“与……相关”。",
        "trap": "relative 有“相对的/亲属”的意思，和 topic 不构成“相关”的标准搭配。",
        "difficulty": 3,
    },
    {
        "submodule": "词汇",
        "stem": "The new law will come into ______ next month.",
        "correct": "effect",
        "distractors": ["affect", "effort", "affair"],
        "reason": "come into effect 是固定搭配，表示“生效”。",
        "trap": "affect 是动词“影响”，和 effect 形近，是典型拼写词性陷阱。",
        "difficulty": 3,
    },
    {
        "submodule": "词汇",
        "stem": "The company decided to ______ its resources on developing one key product.",
        "correct": "concentrate",
        "distractors": ["construct", "conclude", "contribute"],
        "reason": "concentrate resources on sth. 表示“把资源集中在某事上”。",
        "trap": "contribute to 表示“有助于/贡献给”，介词和语义都不符合 resources on 的结构。",
        "difficulty": 3,
    },
    {
        "submodule": "词汇",
        "stem": "The manager tried to ______ a balance between speed and quality.",
        "correct": "strike",
        "distractors": ["hit", "beat", "touch"],
        "reason": "strike a balance 是固定搭配，表示“取得平衡”。",
        "trap": "hit/beat 都有“击打”的字面意思，但不能替代 strike a balance。",
        "difficulty": 4,
    },
    {
        "submodule": "词汇",
        "stem": "The scientist's findings were later ______ by another research team.",
        "correct": "confirmed",
        "distractors": ["conformed", "confined", "confused"],
        "reason": "confirm findings 表示“证实研究发现”。",
        "trap": "conform 常与 to 搭配，表示“符合”；confined 表示“限制”，都是形近陷阱。",
        "difficulty": 4,
    },
    {
        "submodule": "词汇",
        "stem": "The old bridge is no longer ______ for heavy traffic.",
        "correct": "suitable",
        "distractors": ["available", "capable", "possible"],
        "reason": "be suitable for 表示“适合……”，符合 heavy traffic 的语境。",
        "trap": "available 表示“可获得/有空”，capable 常用 be capable of doing，介词搭配不同。",
        "difficulty": 3,
    },
    {
        "submodule": "词汇",
        "stem": "The project was delayed ______ a shortage of skilled workers.",
        "correct": "owing to",
        "distractors": ["because", "thanks for", "instead of"],
        "reason": "owing to 后接名词短语，表示“由于”。",
        "trap": "because 后通常接从句；thanks for 表示“感谢”，不是原因状语。",
        "difficulty": 4,
    },
    {
        "submodule": "词汇",
        "stem": "The evidence is too weak to ______ such a serious claim.",
        "correct": "support",
        "distractors": ["supply", "suppose", "suspend"],
        "reason": "support a claim 表示“支持某一主张”。",
        "trap": "supply 是“供应”，suppose 是“假设”，形近但不与 claim 构成此语义搭配。",
        "difficulty": 3,
    },
    {
        "submodule": "词汇",
        "stem": "The local government has taken measures to ______ traffic congestion.",
        "correct": "ease",
        "distractors": ["cease", "seize", "raise"],
        "reason": "ease congestion 表示“缓解拥堵”。",
        "trap": "cease 表示“停止”，seize 表示“抓住”，都和 ease 形近但语义不合。",
        "difficulty": 3,
    },
    {
        "submodule": "词汇",
        "stem": "The applicant was rejected because he failed to meet the basic ______.",
        "correct": "requirements",
        "distractors": ["acquirements", "requests", "inquiries"],
        "reason": "meet the requirements 是固定搭配，表示“符合要求”。",
        "trap": "requests 是“请求”，不能表达录取或申请的资格条件。",
        "difficulty": 3,
    },
    {
        "submodule": "语法",
        "stem": "It is essential that every student ______ the safety rules.",
        "correct": "follow",
        "distractors": ["follows", "followed", "has followed"],
        "reason": "It is essential that... 后常用虚拟语气，即 should + 动词原形，should 可省略。",
        "trap": "every student 是单数，容易诱导选择 follows，但虚拟语气要求动词原形。",
        "difficulty": 4,
    },
    {
        "submodule": "语法",
        "stem": "By the time the lecture began, most students ______ their seats.",
        "correct": "had taken",
        "distractors": ["took", "have taken", "were taking"],
        "reason": "by the time + 过去时间，主句动作发生在其之前，常用过去完成时。",
        "trap": "took 只是一般过去，不能体现“讲座开始前已经坐好”的先后关系。",
        "difficulty": 4,
    },
    {
        "submodule": "语法",
        "stem": "The book, together with several notes, ______ on the desk.",
        "correct": "is",
        "distractors": ["are", "were", "have been"],
        "reason": "主语中心词是 The book，together with several notes 不影响谓语单复数。",
        "trap": "several notes 离谓语更近，容易误导选择 are。",
        "difficulty": 4,
    },
    {
        "submodule": "语法",
        "stem": "Hardly had he entered the room ______ the phone rang.",
        "correct": "when",
        "distractors": ["than", "then", "while"],
        "reason": "Hardly had...when... 是固定倒装句型，表示“一……就……”。",
        "trap": "no sooner...than... 才搭配 than，hardly 对应 when。",
        "difficulty": 5,
    },
    {
        "submodule": "语法",
        "stem": "No sooner had the meeting started ______ the lights went out.",
        "correct": "than",
        "distractors": ["when", "then", "while"],
        "reason": "No sooner had...than... 是固定结构。",
        "trap": "Hardly/Scarcely 才常与 when 搭配，不能把两个句型混用。",
        "difficulty": 5,
    },
    {
        "submodule": "语法",
        "stem": "The reason ______ he was late was that the bus broke down.",
        "correct": "why",
        "distractors": ["because", "which", "what"],
        "reason": "先行词为 reason，定语从句中缺原因状语，常用 why。",
        "trap": "后面已有 was that，引导表语从句，不能再用 because 造成结构重复。",
        "difficulty": 4,
    },
    {
        "submodule": "语法",
        "stem": "This is the most interesting article ______ I have read this month.",
        "correct": "that",
        "distractors": ["which", "what", "where"],
        "reason": "先行词被最高级修饰时，定语从句关系代词常用 that。",
        "trap": "which 在普通物的定语从句中可用，但最高级限定时 that 更符合考试规则。",
        "difficulty": 3,
    },
    {
        "submodule": "语法",
        "stem": "The problem is ______ we can finish the work before Friday.",
        "correct": "whether",
        "distractors": ["that", "what", "which"],
        "reason": "表语从句表达“是否能完成”，应用 whether。",
        "trap": "that 只引导陈述事实，不表达“是否”；what 在从句中要充当成分。",
        "difficulty": 3,
    },
    {
        "submodule": "语法",
        "stem": "The teacher asked us ______ so much noise in the library.",
        "correct": "not to make",
        "distractors": ["not make", "not making", "do not make"],
        "reason": "ask sb. not to do sth. 是固定结构。",
        "trap": "not make 看似简洁，但 ask 后的宾补应为 to do 的否定形式。",
        "difficulty": 3,
    },
    {
        "submodule": "语法",
        "stem": "______ in a hurry, he left his notebook at home.",
        "correct": "Being",
        "distractors": ["To be", "Been", "Be"],
        "reason": "现在分词短语 Being in a hurry 作原因状语。",
        "trap": "To be 表目的，不适合解释“因为匆忙”；Been 不能单独作状语开头。",
        "difficulty": 4,
    },
    {
        "submodule": "语法",
        "stem": "The experiment ______ last week will be repeated tomorrow.",
        "correct": "conducted",
        "distractors": ["conducting", "to conduct", "conducts"],
        "reason": "experiment 与 conduct 是被动关系，过去分词 conducted 作后置定语。",
        "trap": "conducting 表主动，容易被 last week 误导，但实验不能主动实施自己。",
        "difficulty": 4,
    },
    {
        "submodule": "语法",
        "stem": "She is one of the students who ______ selected for the exchange program.",
        "correct": "were",
        "distractors": ["was", "is", "has been"],
        "reason": "定语从句先行词是 students，who 指复数学生，所以谓语用 were。",
        "trap": "one 离 who 更近，容易误选 was；但真正被修饰的是 students。",
        "difficulty": 5,
    },
    {
        "submodule": "语法",
        "stem": "Only after the results were announced ______ the mistake.",
        "correct": "did they realize",
        "distractors": ["they realized", "had they realized", "they had realized"],
        "reason": "Only + 状语位于句首时，主句需部分倒装；一般过去时用 did they realize。",
        "trap": "they realized 语序自然但不符合 only 句首倒装规则。",
        "difficulty": 5,
    },
    {
        "submodule": "语法",
        "stem": "The more carefully you read the passage, ______ you will understand it.",
        "correct": "the better",
        "distractors": ["better", "the best", "best"],
        "reason": "the more..., the better... 是比较级对应结构。",
        "trap": "better 语义对但缺少第二个 the，结构不完整。",
        "difficulty": 3,
    },
    {
        "submodule": "语法",
        "stem": "I would rather you ______ the truth now.",
        "correct": "told",
        "distractors": ["tell", "will tell", "have told"],
        "reason": "would rather 后接从句表示现在或将来的愿望时，从句常用一般过去时。",
        "trap": "now 容易诱导选择 tell，但该句型需要虚拟语气。",
        "difficulty": 5,
    },
    {
        "submodule": "语法",
        "stem": "Not until he explained it again ______ the point.",
        "correct": "did I understand",
        "distractors": ["I understood", "had I understood", "I had understood"],
        "reason": "Not until 位于句首时，主句部分倒装；根据 explained 用一般过去时。",
        "trap": "I understood 是正常语序，但在 not until 句首结构中不成立。",
        "difficulty": 5,
    },
    {
        "submodule": "语法",
        "stem": "The house needs ______ before the rainy season.",
        "correct": "repairing",
        "distractors": ["repaired", "repair", "to repair"],
        "reason": "need doing 可表示被动意义，相当于 need to be repaired。",
        "trap": "to repair 是主动含义，主语 house 不能主动修理东西。",
        "difficulty": 4,
    },
    {
        "submodule": "语法",
        "stem": "There is little doubt ______ the plan will succeed if fully supported.",
        "correct": "that",
        "distractors": ["whether", "what", "which"],
        "reason": "There is little/no doubt that... 表示“几乎毫无疑问……”。",
        "trap": "doubt 在肯定句中有时接 whether，但 little doubt 表示基本确定，应用 that。",
        "difficulty": 4,
    },
    {
        "submodule": "语法",
        "stem": "He talked as if he ______ everything about the matter.",
        "correct": "knew",
        "distractors": ["knows", "has known", "will know"],
        "reason": "as if 表示与现在事实相反或不确定的假设时，从句常用一般过去时。",
        "trap": "knows 符合第三人称现在时，但破坏了 as if 的虚拟语气。",
        "difficulty": 4,
    },
    {
        "submodule": "语法",
        "stem": "The number of students applying for the program ______ increasing.",
        "correct": "is",
        "distractors": ["are", "have been", "were"],
        "reason": "the number of... 作主语时，谓语用单数。",
        "trap": "students 是复数，容易误导选择 are；但主语中心词是 number。",
        "difficulty": 3,
    },
    {
        "submodule": "语法",
        "stem": "A number of students ______ interested in the new course.",
        "correct": "are",
        "distractors": ["is", "was", "has been"],
        "reason": "a number of... 表示“许多……”，谓语用复数。",
        "trap": "和 the number of 正好相反，是常见主谓一致陷阱。",
        "difficulty": 3,
    },
    {
        "submodule": "语用",
        "stem": "— Would you mind opening the window? — ______",
        "correct": "Not at all.",
        "distractors": ["Yes, I would.", "Never mind.", "It doesn't matter."],
        "reason": "对 Would you mind...? 表示同意帮忙时，常用 Not at all，意思是“不介意”。",
        "trap": "Yes, I would 字面像肯定回答，但实际表示“我介意”，不符合帮忙语境。",
        "difficulty": 3,
    },
    {
        "submodule": "语用",
        "stem": "— I'm sorry I broke your cup. — ______",
        "correct": "Never mind.",
        "distractors": ["You're welcome.", "That's right.", "With pleasure."],
        "reason": "对道歉的回应可用 Never mind，表示“没关系”。",
        "trap": "You're welcome 用于回应感谢，不用于回应道歉。",
        "difficulty": 2,
    },
    {
        "submodule": "语用",
        "stem": "— Could you help me carry this box? — ______",
        "correct": "With pleasure.",
        "distractors": ["It doesn't matter.", "Never mind.", "You are welcome."],
        "reason": "With pleasure 表示“很乐意”，用于答应别人的请求。",
        "trap": "You are welcome 是回应感谢，不是答应帮忙。",
        "difficulty": 2,
    },
    {
        "submodule": "语用",
        "stem": "— Thank you for your advice. — ______",
        "correct": "You're welcome.",
        "distractors": ["Never mind.", "It depends.", "I agree."],
        "reason": "You're welcome 是回应感谢的常用表达。",
        "trap": "Never mind 用于回应道歉或安慰对方，不用于回应感谢。",
        "difficulty": 2,
    },
    {
        "submodule": "语用",
        "stem": "— Shall we postpone the meeting until Friday? — ______ We still need more data.",
        "correct": "That sounds reasonable.",
        "distractors": ["That's all right.", "It doesn't matter.", "Don't mention it."],
        "reason": "That sounds reasonable 表示赞同对方建议，并与后句理由呼应。",
        "trap": "That's all right 常用于回应道歉，不能自然承接 postpone the meeting 的建议。",
        "difficulty": 3,
    },
    {
        "submodule": "语用",
        "stem": "— I failed the interview again. — ______ You still have other chances.",
        "correct": "Don't lose heart.",
        "distractors": ["Take your time.", "Help yourself.", "Make yourself at home."],
        "reason": "Don't lose heart 表示“别灰心”，适合安慰失败的人。",
        "trap": "Take your time 是“不着急”，不是对失败的鼓励。",
        "difficulty": 3,
    },
]


EXTRA_SPECS = [
    {
        "submodule": "词汇",
        "stem": "The final decision will depend ______ how much evidence can be collected.",
        "correct": "on",
        "distractors": ["in", "at", "for"],
        "reason": "depend on 是固定搭配，表示“取决于”。",
        "trap": "中文常说“依赖于”，容易误以为 for/in 也能接原因，但 depend 固定接 on。",
        "difficulty": 2,
    },
    {
        "submodule": "词汇",
        "stem": "The school has adopted a new approach ______ language teaching.",
        "correct": "to",
        "distractors": ["of", "for", "with"],
        "reason": "approach to sth. 表示“……的方法/途径”。",
        "trap": "很多名词可接 of/for，但 approach 表示方法时常接 to。",
        "difficulty": 3,
    },
    {
        "submodule": "词汇",
        "stem": "The success of the plan depends largely on the ______ of all team members.",
        "correct": "cooperation",
        "distractors": ["operation", "corporation", "competition"],
        "reason": "cooperation 表示“合作”，符合团队成员共同参与的语境。",
        "trap": "operation 和 corporation 形近，但分别指“运作/手术”和“公司”。",
        "difficulty": 3,
    },
    {
        "submodule": "词汇",
        "stem": "The new system is intended to ______ students from making the same mistakes.",
        "correct": "prevent",
        "distractors": ["protect", "prohibit", "prepare"],
        "reason": "prevent sb. from doing sth. 表示“阻止某人做某事”。",
        "trap": "prohibit 也有“禁止”，但常见结构是 prohibit sb. from doing；本句 intended to 后 prevent 更自然。",
        "difficulty": 4,
    },
    {
        "submodule": "词汇",
        "stem": "The committee reached a ______ after three hours of discussion.",
        "correct": "consensus",
        "distractors": ["consent", "consequence", "confidence"],
        "reason": "reach a consensus 表示“达成共识”。",
        "trap": "consent 表示“同意/许可”，但 reach a consent 不是自然搭配。",
        "difficulty": 4,
    },
    {
        "submodule": "词汇",
        "stem": "The researcher tried to keep his personal opinions from ______ the results.",
        "correct": "influencing",
        "distractors": ["affecting to", "effecting", "infecting"],
        "reason": "keep...from doing sth. 后接动名词，influence the results 表示“影响结果”。",
        "trap": "affecting 语义接近，但 affecting to 结构错误；effect 作动词多表示“实现”。",
        "difficulty": 4,
    },
    {
        "submodule": "词汇",
        "stem": "The data are not enough to draw a ______ conclusion.",
        "correct": "definite",
        "distractors": ["defined", "defensive", "defeated"],
        "reason": "definite conclusion 表示“明确结论”。",
        "trap": "defined 表示“被定义的/轮廓清楚的”，不能自然修饰 conclusion 表示确定性。",
        "difficulty": 3,
    },
    {
        "submodule": "词汇",
        "stem": "The article gives a brief ______ of the causes of climate change.",
        "correct": "overview",
        "distractors": ["overlook", "overthrow", "overtime"],
        "reason": "overview 表示“概述、综述”，符合 brief 的提示。",
        "trap": "overlook 是动词“忽视/俯瞰”，和 overview 形近但词性和语义都不对。",
        "difficulty": 3,
    },
    {
        "submodule": "词汇",
        "stem": "The hospital is trying to ______ the quality of its emergency services.",
        "correct": "improve",
        "distractors": ["approve", "prove", "remove"],
        "reason": "improve the quality 表示“提高质量”。",
        "trap": "approve 表示“批准/赞成”，和 improve 形近，不能和 quality 构成该语义。",
        "difficulty": 2,
    },
    {
        "submodule": "词汇",
        "stem": "The theory is difficult to understand because it involves several ______ ideas.",
        "correct": "abstract",
        "distractors": ["absolute", "absent", "absurd"],
        "reason": "abstract ideas 表示“抽象概念”。",
        "trap": "absolute 表示“绝对的”，absurd 表示“荒谬的”，都可能被中文感觉误导。",
        "difficulty": 3,
    },
    {
        "submodule": "语法",
        "stem": "If I ______ enough time yesterday, I would have finished the report.",
        "correct": "had had",
        "distractors": ["have had", "had", "would have"],
        "reason": "与过去事实相反的虚拟条件句，if 从句用 had done。",
        "trap": "yesterday 容易诱导选择一般过去 had，但主句 would have finished 提示过去虚拟。",
        "difficulty": 5,
    },
    {
        "submodule": "语法",
        "stem": "If it ______ tomorrow, the outdoor activity will be canceled.",
        "correct": "rains",
        "distractors": ["will rain", "rained", "has rained"],
        "reason": "真实条件句中，if 从句用一般现在时表示将来。",
        "trap": "tomorrow 容易诱导 will rain，但条件状语从句不能用 will 表示一般将来。",
        "difficulty": 3,
    },
    {
        "submodule": "语法",
        "stem": "The girl ______ father is a doctor won the first prize.",
        "correct": "whose",
        "distractors": ["who", "whom", "which"],
        "reason": "空格后有名词 father，关系词需表示所属关系，应用 whose。",
        "trap": "who 指人但不能直接修饰 father；whom 作宾语，不表示所属。",
        "difficulty": 3,
    },
    {
        "submodule": "语法",
        "stem": "This is the factory ______ my father worked ten years ago.",
        "correct": "where",
        "distractors": ["which", "what", "that"],
        "reason": "先行词 factory 在从句中作地点状语，应用 where。",
        "trap": "which/that 指物，但从句 worked 后不缺宾语，缺地点状语。",
        "difficulty": 4,
    },
    {
        "submodule": "语法",
        "stem": "The question ______ we should invite to the meeting has not been settled.",
        "correct": "who",
        "distractors": ["that", "which", "whether"],
        "reason": "从句中 invite 缺宾语，且指人，应用 who/whom；选项中 who 最合适。",
        "trap": "whether 表示“是否”，但这里不是二选一，而是问“邀请谁”。",
        "difficulty": 4,
    },
    {
        "submodule": "语法",
        "stem": "______ is known to all, regular practice is important for language learning.",
        "correct": "As",
        "distractors": ["It", "That", "What"],
        "reason": "As is known to all 是固定非限制性定语从句结构。",
        "trap": "It is known to all that... 也正确，但本句后面已有逗号结构，不是 it...that 句型。",
        "difficulty": 5,
    },
    {
        "submodule": "语法",
        "stem": "It was not until midnight ______ he finished the assignment.",
        "correct": "that",
        "distractors": ["when", "before", "since"],
        "reason": "It was not until...that... 是强调句结构。",
        "trap": "not until 放句首才倒装；这里是 It was...that 强调句，不能用 when。",
        "difficulty": 5,
    },
    {
        "submodule": "语法",
        "stem": "The windows are dirty and need ______.",
        "correct": "cleaning",
        "distractors": ["to clean", "cleaned", "clean"],
        "reason": "need doing 表示被动含义，相当于 need to be cleaned。",
        "trap": "to clean 是主动意义，主语 windows 不能主动清洁。",
        "difficulty": 4,
    },
    {
        "submodule": "语法",
        "stem": "The boy was seen ______ into the building at about eight.",
        "correct": "to go",
        "distractors": ["go", "went", "going to"],
        "reason": "感官动词用于被动语态时，省略的 to 要还原，be seen to do。",
        "trap": "主动结构 see sb. do 中可省 to，但被动后不能省。",
        "difficulty": 5,
    },
    {
        "submodule": "语法",
        "stem": "I have never heard such an interesting story, ______?",
        "correct": "have I",
        "distractors": ["haven't I", "do I", "don't I"],
        "reason": "陈述部分含 never，是否定意义，反意疑问句用肯定形式 have I。",
        "trap": "看到 have 容易机械选择 haven't I，但 never 已经使前半句为否定。",
        "difficulty": 4,
    },
    {
        "submodule": "语法",
        "stem": "Each of the students ______ a copy of the reading material.",
        "correct": "has",
        "distractors": ["have", "are having", "were having"],
        "reason": "Each of... 作主语时谓语用单数。",
        "trap": "students 是复数，容易误导选择 have。",
        "difficulty": 3,
    },
    {
        "submodule": "语法",
        "stem": "The news ______ surprising to everyone in the office.",
        "correct": "was",
        "distractors": ["were", "are", "have been"],
        "reason": "news 是不可数名词，作主语时谓语用单数。",
        "trap": "news 以 s 结尾，容易被误判为复数。",
        "difficulty": 3,
    },
    {
        "submodule": "语法",
        "stem": "There ______ a book and two pens on the table.",
        "correct": "is",
        "distractors": ["are", "were", "have"],
        "reason": "there be 句型常遵循就近原则，be 动词与最近的 a book 保持一致。",
        "trap": "后面有 two pens，容易误选 are，但最近主语是单数 a book。",
        "difficulty": 4,
    },
    {
        "submodule": "语用",
        "stem": "— Would you like me to print the document for you? — ______",
        "correct": "That would be very kind of you.",
        "distractors": ["It doesn't matter.", "Never mind.", "I don't think so."],
        "reason": "对别人主动提供帮助，That would be very kind of you 表示礼貌接受。",
        "trap": "It doesn't matter 和 Never mind 常用于回应道歉，不适合接受帮助。",
        "difficulty": 3,
    },
    {
        "submodule": "语用",
        "stem": "— I wonder if I could leave a little earlier today. — ______",
        "correct": "That depends on how much work is left.",
        "distractors": ["You are welcome.", "Don't mention it.", "With pleasure."],
        "reason": "That depends... 表示要看情况，符合请假请求场景。",
        "trap": "With pleasure 用于答应帮忙，不用于回应离开请求。",
        "difficulty": 3,
    },
    {
        "submodule": "语用",
        "stem": "— I passed the exam! — ______",
        "correct": "Congratulations!",
        "distractors": ["Good luck!", "Never mind!", "Take care!"],
        "reason": "对别人已经取得的成功应表示祝贺。",
        "trap": "Good luck 用于事情发生前祝好运，不用于已经通过考试的场景。",
        "difficulty": 2,
    },
    {
        "submodule": "语用",
        "stem": "— I have a terrible headache. — ______",
        "correct": "You'd better see a doctor.",
        "distractors": ["Congratulations.", "It sounds delicious.", "Help yourself."],
        "reason": "对身体不适应给出建议或关心，You'd better see a doctor 合适。",
        "trap": "Help yourself 用于请人自取食物，不适用于身体不适。",
        "difficulty": 2,
    },
    {
        "submodule": "语用",
        "stem": "— May I use your dictionary for a moment? — ______",
        "correct": "Go ahead.",
        "distractors": ["No way to go.", "Go on foot.", "Go away."],
        "reason": "Go ahead 在口语中表示“可以，请用吧”。",
        "trap": "Go ahead 不是字面“向前走”，其余选项按字面理解会误导。",
        "difficulty": 3,
    },
    {
        "submodule": "语用",
        "stem": "— I'm afraid I can't attend your party tonight. — ______",
        "correct": "What a pity!",
        "distractors": ["That's very kind of you.", "You are welcome.", "With pleasure."],
        "reason": "对别人不能参加活动表示遗憾，可用 What a pity。",
        "trap": "With pleasure 是答应帮忙；You're welcome 是回应感谢，语境不合。",
        "difficulty": 3,
    },
]


def generate_questions() -> list[dict]:
    rng = random.Random(20260503)
    existing_stems = load_existing_stems()
    questions: list[dict] = []
    seen: set[str] = set()
    for spec in [*SPECS, *EXTRA_SPECS]:
        key = normalize_stem(spec["stem"])
        if key in existing_stems or key in seen:
            continue
        seen.add(key)
        questions.append(build_question(spec, rng))
    return questions


def write_review(questions: list[dict]) -> None:
    difficulty_counter = Counter(item["difficulty"] for item in questions)
    submodule_counter = Counter(item["submodule"] for item in questions)
    lines = [
        "# COMMON 英语运用 batch 002 陷阱选项质检",
        "",
        f"- 文件：`{OUTPUT_PATH.name}`",
        f"- 题量：{len(questions)}",
        "- 定位：语言知识专项，强化真实考试中的近义、形近、搭配、语法结构和语用陷阱。",
        "- 设计要求：每题 3 个错误选项都不能明显离谱，至少包含 1 个高迷惑干扰项。",
        "",
        "## 难度分布",
        "",
    ]
    for difficulty in sorted(difficulty_counter):
        lines.append(f"- difficulty {difficulty}: {difficulty_counter[difficulty]} 题")
    lines.extend(["", "## 子模块分布", ""])
    for submodule, count in submodule_counter.most_common():
        lines.append(f"- {submodule}: {count} 题")
    REVIEW_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    questions = generate_questions()
    if len(questions) < 50:
        raise ValueError(f"Generated too few questions: {len(questions)}")
    OUTPUT_PATH.write_text(json.dumps({"questions": questions}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_review(questions)
    print(f"Generated {len(questions)} questions")
    print(f"Wrote {OUTPUT_PATH}")
    print(f"Wrote {REVIEW_PATH}")


if __name__ == "__main__":
    main()
