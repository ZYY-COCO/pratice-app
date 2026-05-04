from __future__ import annotations

import json
import random
import re
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "common_english_language_knowledge_batch_005_matrix_traps.json"
REVIEW_PATH = PROJECT_ROOT / "data" / "common_english_language_knowledge_batch_005_matrix_traps_review.md"


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


SPECS: list[dict] = []


def add(
    submodule: str,
    stem: str,
    correct: str,
    distractors: list[str],
    reason: str,
    trap: str,
    difficulty: int,
    error_tag: str,
) -> None:
    SPECS.append(
        {
            "submodule": submodule,
            "stem": stem,
            "correct": correct,
            "distractors": distractors,
            "reason": reason,
            "trap": trap,
            "difficulty": difficulty,
            "error_tag": error_tag,
        }
    )


COLLOCATION_ITEMS = [
    ("The new students are not yet accustomed ______ taking notes in English.", "to", ["with", "for", "about"], "be accustomed to doing sth. 表示“习惯于做某事”。", "with 容易受 be familiar with 影响，但 accustomed 后接 to。", 3),
    ("This set of exercises is intended to help students adapt ______ exam-style questions.", "to", ["with", "for", "by"], "adapt to 表示“适应”。", "adapt with 是中式迁移，adapt 后常接 to 表示适应对象。", 3),
    ("The short passage appeals ______ students who prefer practical examples.", "to", ["for", "with", "on"], "appeal to 表示“吸引、对……有吸引力”。", "appeal for 表示“呼吁、请求”，与本句语义不同。", 3),
    ("The same rule can also apply ______ reading comprehension questions.", "to", ["for", "with", "on"], "apply to 表示“适用于”。", "apply for 表示“申请”，不是“适用”。", 3),
    ("Most teachers do not approve ______ guessing without checking the context.", "of", ["for", "to", "with"], "approve of 表示“赞成”。", "approve to 受 agree to 影响，是搭配误判。", 3),
    ("Students can benefit ______ reviewing their wrong answers regularly.", "from", ["of", "with", "for"], "benefit from 表示“从……中受益”。", "benefit for 常用于 benefit for sb. 的名词结构，不适合本句。", 3),
    ("The student was blamed ______ not reading the instructions carefully.", "for", ["of", "with", "to"], "blame sb. for doing sth. 表示“因……责备某人”。", "accuse sb. of doing sth. 与 blame sb. for doing sth. 容易混淆。", 4),
    ("We congratulated him ______ passing the examination on his first attempt.", "on", ["for", "with", "to"], "congratulate sb. on sth./doing sth. 表示“祝贺某人……”。", "for 可跟 praise/thank 搭配，但 congratulate 后常接 on。", 3),
    ("Many learners find it hard to cope ______ long sentences under time pressure.", "with", ["to", "for", "about"], "cope with 表示“应对、处理”。", "cope to 是把中文“应对到”直译造成的搭配错误。", 3),
    ("A clear conclusion must be based ______ evidence from the passage.", "on", ["in", "with", "for"], "be based on 表示“以……为基础”。", "based in 表示“总部位于”，与本句逻辑不符。", 3),
    ("This kind of mistake usually derives ______ a misunderstanding of the sentence structure.", "from", ["to", "with", "for"], "derive from 表示“源于”。", "derive to 不是表达来源的搭配。", 4),
    ("She devoted most of her weekend ______ reviewing vocabulary notes.", "to", ["for", "with", "on"], "devote...to doing sth. 表示“把……投入到做某事上”。", "to 后接动名词，这也是本题的非谓语陷阱。", 4),
    ("The candidate failed to escape ______ the trap hidden in the options.", "from", ["of", "with", "to"], "escape from 表示“逃脱、避开”。", "escape of 是常见介词误用。", 3),
    ("Students exchanged their answers ______ comments after class.", "for", ["with", "to", "by"], "exchange A for B 表示“用 A 换 B”。", "exchange with sb. 表示“与某人交换”，本句不是接交换对象。", 4),
    ("Good readers focus ______ the logical relationship between sentences.", "on", ["in", "to", "for"], "focus on 表示“集中于”。", "focus in 多用于摄影或具体聚焦，不适合抽象考点。", 3),
    ("He graduated ______ a local university before becoming an English teacher.", "from", ["in", "of", "by"], "graduate from 表示“毕业于”。", "graduate in 可表示专业领域，但后面是 university，应用 from。", 3),
    ("The speaker insisted ______ answering every question in complete sentences.", "on", ["to", "with", "for"], "insist on doing sth. 表示“坚持做某事”。", "insist to do 是常见误用。", 3),
    ("Noise from outside interfered ______ the students' listening practice.", "with", ["to", "for", "in"], "interfere with 表示“干扰”。", "interfere in 表示“干涉事务”，语义不同。", 4),
    ("All students are encouraged to participate ______ the weekly mock test.", "in", ["at", "on", "with"], "participate in 表示“参加”。", "participate at 受 be present at 影响，是搭配迁移。", 3),
    ("Some students prefer grammar drills ______ vocabulary memorization.", "to", ["than", "rather", "over"], "prefer A to B 表示“比起 B 更喜欢 A”。", "than 常用于 rather than 或 more...than，不用于 prefer A to B。", 4),
    ("The teacher prohibited students ______ using dictionaries during the quiz.", "from", ["to", "for", "with"], "prohibit sb. from doing sth. 表示“禁止某人做某事”。", "prohibit to do 是不定式误用。", 4),
    ("It took him several weeks to recover ______ the disappointment of failure.", "from", ["of", "with", "for"], "recover from 表示“从……中恢复”。", "recover of 不是标准搭配。", 3),
    ("Successful learners do not rely ______ luck when choosing answers.", "on", ["in", "with", "for"], "rely on 表示“依靠”。", "rely in 是介词误用。", 3),
    ("The example reminded me ______ a similar question in the previous test.", "of", ["about", "to", "with"], "remind sb. of sth. 表示“使某人想起某事”。", "remind sb. to do sth. 后接动作，本句后面是名词短语。", 4),
    ("Careless reading often results ______ avoidable mistakes.", "in", ["from", "with", "for"], "result in 表示“导致”。", "result from 表示“由……造成”，方向相反。", 4),
    ("His low score resulted ______ poor time management.", "from", ["in", "with", "to"], "result from 表示“由……造成”。", "result in 表示“导致”，与本句因果方向相反。", 4),
    ("The student searched ______ a clue in the last sentence.", "for", ["of", "with", "to"], "search for 表示“寻找”。", "search sb./place 表示搜查某人或某地，不等于 search for sth.。", 3),
    ("The professor specializes ______ modern English grammar.", "in", ["on", "at", "for"], "specialize in 表示“专门研究、专攻”。", "specialize on 是搭配误用。", 3),
    ("He succeeded ______ finding the hidden meaning of the sentence.", "in", ["to", "with", "for"], "succeed in doing sth. 表示“成功做某事”。", "succeed to 表示继承，语义不同。", 4),
    ("Many students suffer ______ test anxiety before important examinations.", "from", ["with", "of", "for"], "suffer from 表示“遭受某种问题或疾病”。", "suffer with 可表示同受痛苦，但考试搭配常考 suffer from。", 3),
    ("Good learners take advantage ______ every chance to review mistakes.", "of", ["for", "with", "to"], "take advantage of 表示“利用”。", "advantage over 表示优势，不符合本句结构。", 3),
    ("The school takes pride ______ its high pass rate.", "in", ["of", "for", "with"], "take pride in 表示“以……为荣”。", "pride of 可作名词短语，但 take pride 后接 in。", 3),
    ("The passage is short ______ examples, so readers must infer the meaning.", "of", ["for", "with", "to"], "be short of 表示“缺少”。", "short for 表示“是……的缩写”，语义不同。", 4),
    ("In this sentence, the second clause is equal ______ the first in importance.", "to", ["with", "as", "for"], "be equal to 表示“与……相等/相当”。", "equal with 不是本句标准搭配。", 3),
    ("This explanation is superior ______ the one given in the old textbook.", "to", ["than", "over", "with"], "be superior to 表示“优于”。", "superior 不与 than 搭配，这是比较结构陷阱。", 4),
    ("This method is suitable ______ students who need basic practice.", "for", ["to", "with", "about"], "be suitable for 表示“适合”。", "suitable to 偶见于特定语境，但考试常考 suitable for sb./sth.。", 3),
    ("The topic is closely related ______ the idea of lifelong learning.", "to", ["with", "for", "about"], "be related to 表示“与……有关”。", "related with 可见但不如 related to 标准，本句选 to。", 3),
    ("Students are responsible ______ checking their own answers before submission.", "for", ["to", "with", "of"], "be responsible for doing sth. 表示“负责做某事”。", "responsible to 表示“对某人负责”，后接对象不同。", 4),
    ("The article makes no reference ______ the author's personal experience.", "to", ["about", "for", "with"], "reference to 表示“提及、涉及”。", "about 可跟 information/about 搭配，但 reference 后常接 to。", 4),
    ("The teacher has a positive attitude ______ students' mistakes.", "toward", ["for", "with", "on"], "attitude toward/to 表示“对……的态度”。", "attitude for 不是表达态度对象的搭配。", 3),
]

for stem, correct, distractors, reason, trap, difficulty in COLLOCATION_ITEMS:
    add("词汇", stem, correct, distractors, reason, trap, difficulty, "搭配误判")


WORD_CHOICE_ITEMS = [
    ("The new review plan is ______ because it saves both time and energy.", "efficient", ["effective", "sufficient", "deficient"], "efficient 强调“效率高”。", "effective 强调“有效”，不一定省时省力。", 4),
    ("The medicine proved ______, and the patient's condition improved quickly.", "effective", ["efficient", "sufficient", "deficient"], "effective 表示“有效的”。", "efficient 指人或方法效率高，不能直接说明药物产生疗效。", 3),
    ("The museum displays many ______ works of Chinese poetry.", "classic", ["classical", "classmate", "classified"], "classic 表示“经典的”。", "classical 常指古典的、古典主义的，不等于“经典作品”语境。", 4),
    ("The teacher gave us a ______ answer and avoided unnecessary details.", "concise", ["precise", "complex", "conscious"], "concise 表示“简明的”。", "precise 表示“精确的”，不一定简短。", 4),
    ("The instructions must be ______ enough for beginners to follow.", "clear", ["clean", "clever", "close"], "clear 表示“清楚的”。", "clean 是“干净的”，受中文“清”字误导。", 2),
    ("His explanation was ______; it helped us understand the rule immediately.", "practical", ["practicable", "practiced", "practicing"], "practical 表示“实用的”。", "practicable 表示“可行的”，不等于“实用建议”。", 4),
    ("The plan is ______ only if every student follows it carefully.", "practicable", ["practical", "practiced", "practicing"], "practicable 表示“可实行的”。", "practical 更偏“实用的”，本句强调计划是否可执行。", 5),
    ("The word 'oral' in an oral test means ______.", "spoken", ["written", "ordinary", "official"], "oral 表示“口头的”。", "verbal 也可与语言有关，但 oral test 明确是口试。", 3),
    ("The event was a ______ moment in the history of the school.", "historic", ["historical", "hysterical", "history"], "historic 表示“有历史意义的”。", "historical 表示“与历史有关的”，不一定重要。", 4),
    ("The novel is set against a ______ background.", "historical", ["historic", "hysterical", "history"], "historical background 表示“历史背景”。", "historic 强调重大历史意义，不适合普通背景。", 4),
    ("A ______ person can understand how others feel.", "considerate", ["considerable", "considering", "considered"], "considerate 表示“体贴的”。", "considerable 表示“相当大的”，形近但意义不同。", 4),
    ("The project requires a ______ amount of money.", "considerable", ["considerate", "considered", "considering"], "considerable 表示“相当大的”。", "considerate 是“体贴的”，不能修饰 amount。", 4),
    ("The factory needs more ______ workers to improve production.", "industrious", ["industrial", "inductive", "indifferent"], "industrious 表示“勤奋的”。", "industrial 表示“工业的”，不能形容工人勤奋。", 4),
    ("The passage discusses the rapid growth of ______ production.", "industrial", ["industrious", "inductive", "individual"], "industrial production 表示“工业生产”。", "industrious 是勤奋的，常形容人。", 3),
    ("A ______ translation may miss the implied meaning of the sentence.", "literal", ["literary", "literate", "liberal"], "literal 表示“字面的”。", "literary 表示“文学的”，literate 表示“有读写能力的”。", 4),
    ("The article is written in a simple but ______ style.", "literary", ["literal", "literate", "liberal"], "literary style 表示“文学风格”。", "literal 是“字面的”，不修饰 style 表示文学风格。", 4),
    ("The handwriting is almost ______, so I cannot read the answer.", "illegible", ["eligible", "legible", "legal"], "illegible 表示“难以辨认的”。", "eligible 表示“有资格的”，形近但意义不同。", 4),
    ("Only students who meet the requirements are ______ for the scholarship.", "eligible", ["illegible", "legible", "legal"], "eligible 表示“有资格的”。", "legible/illegible 与字迹可读性有关。", 4),
    ("The danger is ______, so we must act at once.", "imminent", ["eminent", "immanent", "immediate"], "imminent 表示“即将发生的、迫近的”。", "eminent 表示“杰出的”，形近音近。", 5),
    ("The lecture was given by an ______ scholar in linguistics.", "eminent", ["imminent", "immanent", "immediate"], "eminent 表示“杰出的、著名的”。", "imminent 表示危险或事件迫近，不能形容学者。", 4),
    ("The author tries to ______ that the conclusion is not fully supported.", "imply", ["infer", "refer", "prefer"], "imply 表示“暗示”，主语通常是作者、话语或事实。", "infer 是读者“推断”，主语和动作方向不同。", 5),
    ("From the last paragraph, we may ______ that the writer disagrees.", "infer", ["imply", "refer", "prefer"], "infer 表示“推断”。", "imply 是文本或作者暗示，读者不能 imply 出结论。", 5),
    ("The new rule will ______ all students, not just the first-year students.", "affect", ["effect", "effort", "offer"], "affect 作动词表示“影响”。", "effect 作名词表示“效果”，作动词表示“实现”，不等于一般的“影响”。", 4),
    ("The new rule had a strong ______ on students' study habits.", "effect", ["affect", "effort", "offer"], "effect 作名词表示“影响、效果”。", "affect 通常作动词，不能直接被 a strong 修饰为名词。", 3),
    ("Please ______ that all answers are written clearly.", "ensure", ["assure", "insure", "sure"], "ensure 表示“确保”。", "assure 通常接人，表示向某人保证；insure 表示投保。", 4),
    ("The teacher tried to ______ the students that the test would be fair.", "assure", ["ensure", "insure", "sure"], "assure sb. that... 表示“向某人保证”。", "ensure 后通常不直接接人作宾语表达安慰保证。", 4),
    ("The school will ______ the laboratory equipment against damage.", "insure", ["ensure", "assure", "sure"], "insure 表示“给……投保”。", "ensure 是确保，assure 是保证某人，不表示投保。", 4),
    ("The scientist tried to ______ a new method for measuring progress.", "devise", ["device", "divide", "revise"], "devise 是动词，表示“设计、想出”。", "device 是名词“装置、设备”，词性不合。", 4),
    ("This small ______ can record students' speaking practice.", "device", ["devise", "divide", "revise"], "device 是名词，表示“设备”。", "devise 是动词，不能被 this small 直接修饰作名词。", 3),
    ("The college will hire more teaching ______ next year.", "personnel", ["personal", "personality", "person"], "personnel 表示“人员”。", "personal 是形容词“个人的”，不能表示人员群体。", 4),
    ("Please write your ______ information on the first page.", "personal", ["personnel", "personality", "person"], "personal information 表示“个人信息”。", "personnel information 是“人事信息”，语义范围不同。", 3),
    ("The final exam will ______ the oral test by two weeks.", "precede", ["proceed", "process", "produce"], "precede 表示“在……之前”。", "proceed 表示“继续进行”，不表示时间上先于。", 4),
    ("After a short break, the teacher asked us to ______ with the next exercise.", "proceed", ["precede", "process", "produce"], "proceed with 表示“继续进行”。", "precede 是“先于”，不能表达继续做练习。", 4),
    ("The two answers look similar, but they are ______ different.", "altogether", ["all together", "together all", "all"], "altogether 表示“完全地、总共”。", "all together 表示“全部在一起”，不是副词“完全地”。", 5),
    ("The students worked ______ to finish the project.", "all together", ["altogether", "together all", "all"], "all together 表示“大家一起”。", "altogether 表示“完全、总共”，不能表示共同完成。", 4),
    ("The writer failed to ______ enough evidence for his argument.", "cite", ["site", "sight", "sit"], "cite 表示“引用”。", "site 是地点，sight 是视力或景象，音近但词义不同。", 4),
    ("The new campus ______ is far from the city center.", "site", ["cite", "sight", "sit"], "site 表示“地点、场址”。", "cite 是引用，不能表示校园地点。", 3),
]

for stem, correct, distractors, reason, trap, difficulty in WORD_CHOICE_ITEMS:
    add("词汇", stem, correct, distractors, reason, trap, difficulty, "词义混淆")


GRAMMAR_ITEMS = [
    ("Neither the examples nor the rule ______ difficult to understand.", "is", ["are", "were", "be"], "neither...nor... 作主语时遵循就近原则，靠近谓语的是 the rule。", "只看 examples 会误选 are。", 4, "主谓一致"),
    ("Neither the rule nor the examples ______ difficult to understand.", "are", ["is", "was", "be"], "就近原则中靠近谓语的是 examples，谓语用复数。", "只记 neither 表否定而忽略就近原则会误选 is。", 4, "主谓一致"),
    ("Each of the explanations ______ a different point.", "covers", ["cover", "covering", "have covered"], "Each of + 复数名词作主语时谓语用单数。", "explanations 是复数，但真正主语是 Each。", 3, "主谓一致"),
    ("More than one student ______ made the same mistake.", "has", ["have", "are", "were"], "more than one + 单数名词作主语时谓语通常用单数。", "中文理解成“很多学生”会误选 have。", 4, "主谓一致"),
    ("Many a candidate ______ trapped by the similar-looking options.", "is", ["are", "were", "be"], "many a + 单数名词作主语，谓语用单数。", "many 容易让人误判为复数。", 5, "主谓一致"),
    ("What matters most ______ not the number of books but the quality of review.", "is", ["are", "were", "be"], "What 引导的主语从句整体作单数概念。", "books 是表语中的名词，不决定谓语。", 4, "主谓一致"),
    ("The teacher, together with several students, ______ preparing a new test.", "is", ["are", "were", "be"], "together with 插入成分不改变主语 teacher 的单数性质。", "看到 several students 就选 are 是典型近邻干扰。", 4, "主谓一致"),
    ("The number of wrong answers ______ been reduced after daily review.", "has", ["have", "are", "were"], "the number of 表示“……的数量”，作单数。", "wrong answers 是复数，但主语核心是 number。", 3, "主谓一致"),
    ("A number of wrong answers ______ been corrected by the students.", "have", ["has", "is", "was"], "a number of 表示“许多”，后接复数名词，谓语用复数。", "与 the number of 的谓语形式容易混淆。", 3, "主谓一致"),
    ("Reading long English sentences ______ patience and practice.", "requires", ["require", "requiring", "are requiring"], "动名词短语作主语时谓语通常用单数。", "sentences 是短语内部名词，不是句子主语。", 3, "主谓一致"),
    ("When I arrived, the students ______ the test for ten minutes.", "had been taking", ["have taken", "took", "are taking"], "过去某时之前已持续一段时间，用过去完成进行时。", "for ten minutes 是持续时间提示，不能只用一般过去时。", 5, "时态语态"),
    ("This is the first time that he ______ such a difficult grammar question.", "has met", ["met", "had met", "meets"], "This is the first time that... 从句常用现在完成时。", "first time 容易误用一般过去时，但结构要求完成时。", 4, "时态语态"),
    ("It was the first time that he ______ such a difficult grammar question.", "had met", ["has met", "met", "meets"], "It was the first time that... 从句常用过去完成时。", "was 把时间基点放到过去，因此用 had met。", 5, "时态语态"),
    ("The classroom ______ when the students came in.", "was being cleaned", ["cleaned", "has cleaned", "was cleaning"], "教室是被打扫，且动作正在进行，用过去进行时的被动语态。", "was cleaning 会让 classroom 主动打扫，逻辑不通。", 4, "时态语态"),
    ("The problem ______ by the end of yesterday's class.", "had been solved", ["has been solved", "was solving", "solved"], "by the end of yesterday's class 表示过去某时之前完成，用过去完成被动。", "has been solved 与过去时间基点不一致。", 5, "时态语态"),
    ("I ______ the rule several times, but I still made a mistake yesterday.", "had reviewed", ["have reviewed", "reviewed", "was reviewing"], "昨天犯错之前已经复习过，用过去完成时突出先后。", "have reviewed 与 yesterday 的过去叙事不协调。", 4, "时态语态"),
    ("The sentence ______ more clearly if the subject is placed at the beginning.", "will read", ["will be read", "reads", "is read"], "read 可作系动词/不及物，表示“读起来”。", "will be read 是被动“被阅读”，不表达“读起来更清楚”。", 5, "时态语态"),
    ("The new words ______ again and again until they are remembered.", "should be reviewed", ["should review", "review", "reviewing"], "words 是被复习的对象，用被动语态。", "should review 缺少执行者且让 words 主动复习，逻辑错误。", 3, "时态语态"),
    ("The teacher asked us to keep the windows ______ during the listening test.", "closed", ["closing", "to close", "close"], "keep + 宾语 + 过去分词，表示“使窗户保持关闭”。", "closing 表示正在关，close 可能是形容词但本结构更自然用 closed。", 4, "非谓语"),
    ("With so many questions ______, the students felt nervous.", "to answer", ["answered", "answering", "answer"], "with + 宾语 + to do 表示尚未完成的动作。", "answered 表示已经被回答，与 nervous 的原因不一致。", 5, "非谓语"),
    ("With all the questions ______, the students handed in their papers.", "answered", ["to answer", "answering", "answer"], "with + 宾语 + 过去分词表示动作已完成且被动。", "to answer 表示未答完，与 handed in 矛盾。", 5, "非谓语"),
    ("The easiest way ______ progress is to review mistakes.", "to make", ["making", "made", "make"], "名词 way 后常接不定式作后置定语。", "making progress 是固定搭配，但这里修饰 way，要用 to make。", 4, "非谓语"),
    ("He had difficulty ______ the difference between the two words.", "telling", ["to tell", "tell", "told"], "have difficulty doing sth. 表示“做某事有困难”。", "to tell 受 difficult to do 影响，是结构混淆。", 3, "非谓语"),
    ("The book is easy ______ but hard to master.", "to read", ["reading", "read", "to be read"], "形容词 easy 后接不定式，主动形式表被动意义。", "to be read 虽然被动，但本结构通常用主动不定式。", 4, "非谓语"),
    ("The question is worth ______ carefully.", "considering", ["to consider", "considered", "being considered"], "be worth doing 是固定结构。", "being considered 看似被动，但 worth 后常用主动形式。", 4, "非谓语"),
    ("The teacher had the students ______ the answer aloud.", "read", ["to read", "reading", "readed"], "have sb. do sth. 表示“让某人做某事”。", "to read 受 ask sb. to do 影响。", 3, "非谓语"),
    ("The teacher had the answer ______ aloud.", "read", ["to read", "reading", "readed"], "have sth. done 表示“让某事被做”，read 的过去分词仍为 read。", "to read 表主动目的，不符合 answer 被读出的结构。", 5, "非谓语"),
    ("I regret ______ you that your answer is wrong.", "to tell", ["telling", "tell", "told"], "regret to tell 表示“遗憾地告知”。", "regret doing 表示后悔做过某事，语义不同。", 4, "非谓语"),
    ("He regretted ______ the instructions too quickly.", "reading", ["to read", "read", "to have read"], "regret doing 表示“后悔做过某事”。", "regret to do 表示遗憾地将要做某事，不符合句意。", 4, "非谓语"),
    ("I remember ______ this rule in yesterday's class.", "learning", ["to learn", "learn", "to be learned"], "remember doing 表示“记得做过”。", "remember to do 表示记得要去做，语义不同。", 3, "非谓语"),
    ("Please remember ______ the answer sheet before you leave.", "to check", ["checking", "check", "checked"], "remember to do 表示“记得去做”。", "checking 表示记得做过，与 before you leave 的未完成动作不符。", 3, "非谓语"),
    ("The reason ______ he was late was not accepted.", "why", ["that", "which", "what"], "reason 在定语从句中作原因状语，用 why。", "that/which 常在从句中作主语或宾语，本句不缺宾语。", 4, "从句关系"),
    ("The reason ______ he gave was not accepted.", "that", ["why", "because", "what"], "reason 在从句中作 gave 的宾语，用 that/which 或省略。", "why 用于作原因状语，不用于 gave 的宾语位置。", 5, "从句关系"),
    ("I will never forget the day ______ I first took a mock test.", "when", ["which", "that", "what"], "day 在从句中作时间状语，用 when。", "which/that 作宾语或主语，本句 took 已有宾语 test。", 4, "从句关系"),
    ("I will never forget the day ______ we spent together reviewing grammar.", "that", ["when", "where", "what"], "day 在从句中作 spent 的宾语，用 that/which。", "when 是时间状语，但 spent 缺宾语。", 5, "从句关系"),
    ("The place ______ the students discussed the answers was quiet.", "where", ["which", "that", "what"], "place 在从句中作地点状语，用 where。", "discussed 后已有宾语 answers，不缺宾语。", 4, "从句关系"),
    ("The place ______ the students visited after the test was quiet.", "that", ["where", "when", "what"], "place 在从句中作 visited 的宾语，用 that/which。", "where 表地点状语，不可作 visited 的宾语。", 4, "从句关系"),
    ("The student ______ answer was selected gave a clear explanation.", "whose", ["who", "whom", "which"], "whose 表示所属关系，修饰 answer。", "who 不能直接修饰名词 answer。", 3, "从句关系"),
    ("______ he said at the meeting surprised everyone.", "What", ["That", "Which", "Where"], "What 引导主语从句，并在从句中作 said 的宾语。", "That 引导名词性从句时不作成分，不能作 said 的宾语。", 4, "从句关系"),
    ("I don't know ______ he will choose the difficult test or the easier one.", "whether", ["that", "what", "which"], "whether...or... 表示“是否……还是……”。", "that 不与 or 构成选择关系。", 3, "从句关系"),
    ("The fact ______ he finished the paper early surprised us.", "that", ["which", "what", "why"], "fact 后接同位语从句，用 that 说明事实内容。", "which 引导定语从句，不能说明 fact 的完整内容。", 4, "从句关系"),
    ("Only by reading the whole sentence ______ the correct answer.", "can you find", ["you can find", "you find", "can find you"], "Only + 状语置于句首，主句部分倒装。", "you can find 是正常语序，漏了倒装。", 4, "倒装强调"),
    ("Not only ______ the rule, but he also gave examples.", "did he explain", ["he explained", "he did explained", "explained he"], "Not only 置于句首时前一分句部分倒装。", "did explained 忽视助动词后用动词原形。", 5, "倒装强调"),
    ("Seldom ______ such a tricky question in a basic test.", "do we see", ["we see", "we saw", "see we"], "否定副词 Seldom 置于句首时部分倒装。", "we see 是正常语序，不能跟句首 Seldom。", 5, "倒装强调"),
    ("So carefully ______ that he found every hidden clue.", "did he read", ["he read", "he did read", "read he"], "So + 副词置于句首时，主句部分倒装。", "he read 漏掉倒装。", 5, "倒装强调"),
    ("It was the context ______ helped him choose the right answer.", "that", ["which", "where", "what"], "强调句结构为 It was...that...。", "which 易被看成定语从句，但本句是强调句。", 4, "倒装强调"),
    ("It is not the length of the passage but the logic ______ matters.", "that", ["what", "which", "where"], "强调句中被强调部分后用 that。", "what 不能接在 It is... 后构成强调句。", 5, "倒装强调"),
    ("Had he checked the options carefully, he ______ the trap.", "would have avoided", ["would avoid", "will avoid", "avoided"], "省略 if 的虚拟倒装：Had he checked = If he had checked。", "would avoid 不对应过去事实相反。", 5, "虚拟语气"),
    ("Were I in your position, I ______ the wrong questions first.", "would review", ["will review", "reviewed", "had reviewed"], "Were I... 表示与现在事实相反的虚拟条件。", "will review 是真实将来，不符合虚拟。", 5, "虚拟语气"),
    ("If the teacher were here, he ______ the rule more clearly.", "would explain", ["will explain", "explained", "had explained"], "与现在事实相反的虚拟条件句，主句用 would do。", "will explain 是真实条件的将来。", 4, "虚拟语气"),
    ("If she had not reviewed the notes, she ______ the answer.", "would not have found", ["would not find", "will not find", "had not found"], "与过去事实相反，主句用 would have done。", "would not find 是现在/将来的虚拟结果。", 5, "虚拟语气"),
    ("The teacher suggested that the answer ______ checked twice.", "be", ["is", "was", "will be"], "suggest 表建议时，从句用 should + 动词原形，should 可省略。", "is 是陈述语气，不符合建议类虚拟。", 5, "虚拟语气"),
    ("It is important that every student ______ the instructions carefully.", "read", ["reads", "reading", "will read"], "It is important that... 可用 should + 动词原形，should 省略后用 read。", "reads 受 every student 单数影响，但虚拟语气用原形。", 5, "虚拟语气"),
    ("I wish I ______ more time to review yesterday.", "had had", ["had", "have", "would have"], "wish 后表示与过去事实相反，用过去完成时。", "had 表示现在愿望，不符合 yesterday。", 5, "虚拟语气"),
    ("He talks as if he ______ all the answers.", "knew", ["knows", "has known", "will know"], "as if 表与事实不符的假设，可用过去式表示现在虚拟。", "knows 是真实陈述，削弱 as if 的虚拟意味。", 4, "虚拟语气"),
    ("______ the question is short, it may still contain a trap.", "Although", ["Because", "Since", "Unless"], "前后是让步关系：题短，但有陷阱。", "Because/Since 表原因，会让逻辑关系错误。", 3, "逻辑连接"),
    ("You will not improve ______ you review your mistakes regularly.", "unless", ["because", "although", "so that"], "unless 表示“除非”，符合“不复盘就不会提升”。", "because 表原因，不能表达条件限制。", 3, "逻辑连接"),
    ("The option looks correct; ______, it does not fit the context.", "however", ["therefore", "besides", "instead"], "前后是转折关系，用 however。", "therefore 表结果，会把逻辑方向弄反。", 3, "逻辑连接"),
    ("He reviewed the rule carefully; ______, he avoided the same mistake.", "therefore", ["however", "otherwise", "although"], "前后是因果关系，用 therefore。", "however 表转折，不符合“复习所以避免错误”。", 3, "逻辑连接"),
    ("The more examples you compare, ______ the rule becomes.", "the clearer", ["clearer", "the clear", "the clearly"], "the more..., the + 比较级... 是固定比较结构。", "clearer 少了第二个 the，结构不完整。", 4, "比较结构"),
    ("This question is ______ difficult for beginners to answer without help.", "too", ["so", "very", "enough"], "too...to... 表示“太……而不能……”。", "so 通常接 that 从句，不直接接 to answer。", 3, "比较结构"),
    ("The sentence is clear enough ______ understood by most students.", "to be", ["being", "be", "to"], "enough to be understood 表示“足够清楚而能被理解”。", "to 后缺 be 会导致被动结构不完整。", 4, "比较结构"),
]

for stem, correct, distractors, reason, trap, difficulty, error_tag in GRAMMAR_ITEMS:
    add("语法", stem, correct, distractors, reason, trap, difficulty, error_tag)


USAGE_ITEMS = [
    ("- Would you mind if I turned off the light? - ______ I am leaving now.", "Not at all.", ["Yes, please.", "Never mind.", "You are welcome."], "同意对方请求时，可用 Not at all，表示不介意。", "Yes, please 在 mind 问句中容易造成“介意”的理解。", 4),
    ("- I'm sorry I broke your pen. - ______ I have another one.", "Never mind.", ["With pleasure.", "Congratulations.", "Good luck."], "回应道歉时 Never mind 表示“没关系”。", "With pleasure 用于答应请求，不用于回应道歉。", 3),
    ("- Could you show me how to solve this problem? - ______", "With pleasure.", ["Never mind.", "It doesn't matter.", "No, thanks."], "With pleasure 表示乐意帮忙。", "It doesn't matter 回应道歉，不是答应帮助。", 2),
    ("- I finally passed the mock test. - ______", "Congratulations!", ["I'm sorry to hear that.", "Help yourself.", "Never mind."], "听到好消息，应表示祝贺。", "I'm sorry to hear that 用于坏消息。", 2),
    ("- I failed again. - ______ You still have time to improve.", "Don't lose heart.", ["Enjoy yourself.", "It depends.", "Good appetite."], "Don't lose heart 表示“别灰心”。", "Enjoy yourself 用于祝玩得开心，不用于安慰失败。", 3),
    ("- Thank you for explaining the rule. - ______", "You're welcome.", ["Never mind.", "No, thank you.", "I am sorry."], "You're welcome 用于回应感谢。", "Never mind 多回应道歉，不回应感谢。", 2),
    ("- Shall we start with vocabulary today? - ______", "Good idea.", ["You're welcome.", "It doesn't matter.", "No way to speak."], "对建议表示赞同可用 Good idea。", "You're welcome 是回应感谢。", 2),
    ("- May I borrow your grammar notebook? - ______", "Sure, here you are.", ["No, you may.", "Thank you.", "I don't borrow."], "对借物请求同意时，可说 Sure, here you are。", "No, you may 前后矛盾。", 3),
    ("- Could I speak to Miss Wang, please? - ______", "Hold on, please.", ["I am speaking.", "You are welcome.", "No speaking."], "电话用语中 Hold on, please 表示“请稍等”。", "You are welcome 不适用于电话转接。", 3),
    ("- Would you like another cup of tea? - ______", "No, thank you.", ["No, I wouldn't.", "Never mind.", "Don't mention it."], "礼貌拒绝饮品可用 No, thank you。", "No, I wouldn't 语气生硬且不自然。", 3),
    ("- I lost my answer sheet. - ______", "What a pity!", ["Congratulations!", "Good idea.", "Enjoy yourself."], "对坏消息表示遗憾可用 What a pity。", "Congratulations 与坏消息语境相反。", 2),
    ("- Could you repeat the last sentence? - ______", "Certainly.", ["It repeats.", "No sentence.", "You repeat me."], "Certainly 可表示答应对方请求。", "You repeat me 是中式表达，语义不合。", 3),
    ("- How about reviewing the wrong questions first? - ______", "Sounds good.", ["It hears good.", "Never mind.", "Help yourself."], "Sounds good 表示赞同建议。", "It hears good 把 sound 误作 hear，语用和语法都错。", 3),
    ("- Do you mind my opening the window? - ______ It's a little hot here.", "Of course not.", ["Yes, open it.", "No, you mind.", "It doesn't window."], "Of course not 表示“不介意”，允许对方开窗。", "Yes, open it 容易按中文理解，但 mind 问句中 yes 可能表示介意。", 4),
    ("- I have a headache and can't focus. - ______", "You'd better take a rest.", ["Congratulations.", "Help yourself.", "It doesn't matter."], "对身体不适应给建议或关心。", "It doesn't matter 回应道歉，不适合身体不适。", 3),
    ("- Excuse me, where is the reading room? - ______", "Go straight and turn right.", ["I am reading.", "No, thanks.", "You are welcome."], "问路时应给方向。", "You are welcome 回应感谢，不回答地点。", 3),
    ("- I am taking the entrance exam tomorrow. - ______", "Good luck!", ["Never mind.", "I'm sorry.", "Help yourself."], "考试前祝愿对方好运。", "Never mind 用于安慰小失误，不是祝福。", 2),
    ("- Could you lend me your dictionary? - ______ I need it now.", "Sorry, I can't.", ["With pleasure.", "Here you are.", "Congratulations."], "后句 I need it now 表示不能借，应礼貌拒绝。", "With pleasure/Here you are 表示同意，与后句矛盾。", 4),
    ("- I don't understand this sentence. - ______", "Let me explain it to you.", ["You are welcome.", "No, I don't.", "Good luck."], "对方不理解时，合适回应是提供解释。", "You are welcome 与感谢语境相关，不符合这里。", 3),
    ("- Please give my best wishes to your parents. - ______", "I will.", ["No, thanks.", "Yes, please.", "Never mind."], "I will 表示会转达祝福。", "Yes, please 用于接受提议，不表示转达。", 3),
    ("- Would you care for some fruit? - ______", "Yes, please.", ["I don't care.", "Never mind.", "Don't mention it."], "Would you care for...? 是礼貌邀请，接受可用 Yes, please。", "I don't care 语气不礼貌，也不是接受邀请。", 3),
    ("- Sorry, I can't finish the task on time. - ______", "Take it easy.", ["Congratulations.", "Enjoy it.", "You are welcome."], "Take it easy 可用于安慰对方不要太紧张。", "You are welcome 只回应感谢。", 3),
    ("- My phone is out of power. May I use yours? - ______", "Sure, go ahead.", ["No, go ahead.", "Yes, you can't.", "I am power."], "Sure, go ahead 表示允许对方使用。", "Yes, you can't 前后矛盾。", 3),
    ("- I think this answer is B. - ______ It should be C according to the context.", "I don't agree.", ["That's right.", "Exactly.", "Well done."], "后句指出应为 C，所以前句应表示不同意。", "That's right/Exactly 与后句矛盾。", 4),
    ("- Could you help me check this sentence? - ______ I am busy now.", "Sorry, I can't.", ["With pleasure.", "Certainly.", "No problem."], "后句 I am busy now 表示不能帮忙，应礼貌拒绝。", "With pleasure/Certainly/No problem 都表示同意。", 4),
    ("- The exam was harder than I expected. - ______", "So it was.", ["So was it.", "So it did.", "So did it."], "So it was 表示同意对方对同一事物的判断。", "So was it 是倒装结构，表示另一个对象也如此，不符合本句。", 5),
    ("- Tom passed the test. - ______", "So did Mary.", ["So Mary did.", "So was Mary.", "So Mary was."], "So did Mary 表示 Mary 也通过了。", "So Mary did 表示强调 Tom/Mary 确实做了，不表达“也”。", 5),
    ("- I haven't finished the exercise. - ______", "Neither have I.", ["So have I.", "Neither I have.", "So I have."], "否定情况的“我也没有”用 Neither/Nor + 助动词 + 主语。", "So have I 用于肯定的“我也一样”。", 5),
]

for stem, correct, distractors, reason, trap, difficulty in USAGE_ITEMS:
    add("语用", stem, correct, distractors, reason, trap, difficulty, "语境误判")


def build_question(spec: dict, rng: random.Random) -> dict:
    options, answer = make_options(spec["correct"], spec["distractors"], rng)
    explanation = (
        f"本题考查英语运用中的「{spec['submodule']}」。正确答案为 {answer}（{spec['correct']}）。"
        f"{spec['reason']} 本题陷阱：{spec['trap']} "
        f"错因提示：{spec['error_tag']}。"
        "做题时先判断句法位置和上下文逻辑，再检查固定搭配、词性和语气是否同时成立。"
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


def generate_questions() -> list[dict]:
    rng = random.Random(20260504)
    existing_stems = load_existing_stems()
    questions: list[dict] = []
    seen: set[str] = set()
    for spec in SPECS:
        key = normalize_stem(spec["stem"])
        if key in existing_stems or key in seen:
            continue
        seen.add(key)
        questions.append(build_question(spec, rng))
    return questions


def write_review(questions: list[dict]) -> None:
    difficulty_counter = Counter(item["difficulty"] for item in questions)
    submodule_counter = Counter(item["submodule"] for item in questions)
    tag_counter = Counter()
    for item in questions:
        match = re.search(r"错因提示：([^。]+)", item["explanation"])
        if match:
            tag_counter[match.group(1)] += 1
    lines = [
        "# COMMON 英语运用 batch 005 考点矩阵陷阱题质检",
        "",
        f"- 文件：`{OUTPUT_PATH.name}`",
        f"- 题量：{len(questions)}",
        "- 定位：按考点矩阵继续扩充语言知识，兼顾固定搭配、词义混淆、句法结构和交际语境。",
        "- 解析策略：每题写明正确理由、陷阱来源和错因提示，方便后续学习报告做薄弱点归因。",
        "",
        "## 子模块分布",
        "",
    ]
    for submodule, count in submodule_counter.most_common():
        lines.append(f"- {submodule}: {count} 题")
    lines.extend(["", "## 难度分布", ""])
    for difficulty in sorted(difficulty_counter):
        lines.append(f"- difficulty {difficulty}: {difficulty_counter[difficulty]} 题")
    lines.extend(["", "## 错因提示分布", ""])
    for tag, count in tag_counter.most_common():
        lines.append(f"- {tag}: {count} 题")
    REVIEW_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    questions = generate_questions()
    if len(questions) < 150:
        raise ValueError(f"Generated too few questions: {len(questions)}")
    OUTPUT_PATH.write_text(json.dumps({"questions": questions}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_review(questions)
    print(f"Generated {len(questions)} questions")
    print(f"Wrote {OUTPUT_PATH}")
    print(f"Wrote {REVIEW_PATH}")


if __name__ == "__main__":
    main()
