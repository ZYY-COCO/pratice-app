from __future__ import annotations

import json
import random
import re
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "common_english_language_knowledge_batch_004_traps_extra.json"
REVIEW_PATH = PROJECT_ROOT / "data" / "common_english_language_knowledge_batch_004_traps_extra_review.md"


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
        }
    )


add("词汇", "Many candidates find it difficult to distinguish facts ______ opinions in a passage.", "from", ["with", "between", "among"], "distinguish A from B 表示“把 A 与 B 区分开”。", "between 容易被中文“在两者之间区分”误导，但本句结构是 distinguish facts from opinions。", 3)
add("词汇", "The committee finally arrived ______ a decision after three hours of discussion.", "at", ["to", "on", "with"], "arrive at a decision 是固定搭配，表示“作出决定”。", "arrive to 常受 arrive to a place 的误类推影响，但英语中通常说 arrive at/in a place。", 3)
add("词汇", "The new policy is intended to protect students ______ misleading information.", "from", ["of", "against", "for"], "protect sb. from sth. 表示“保护某人免受某事影响”。", "against 也可与 protect 搭配，但本句更自然的是 protect students from misleading information，强调免受伤害。", 3)
add("词汇", "The result of the experiment was consistent ______ the original hypothesis.", "with", ["to", "for", "about"], "be consistent with 表示“与……一致”。", "to 常由 similar to 迁移而来，是搭配陷阱。", 3)
add("词汇", "Applicants should be familiar ______ the basic rules before taking the test.", "with", ["to", "for", "about"], "be familiar with sth. 表示“熟悉某事”。", "familiar to 表示“为某人所熟悉”，主语和宾语方向不同。", 3)
add("词汇", "The teacher laid special emphasis ______ the importance of reviewing mistakes.", "on", ["in", "for", "to"], "emphasis on 是固定搭配，表示“对……的强调”。", "to 容易受 attach importance to 影响，但 emphasis 后接 on。", 3)
add("词汇", "The report provides students ______ practical advice on time management.", "with", ["for", "to", "by"], "provide sb. with sth. 表示“给某人提供某物”。", "provide sth. for sb. 也成立，但本句 students 在 provide 后面，所以用 with。", 3)
add("词汇", "The problem can be traced ______ a lack of regular practice.", "to", ["from", "with", "for"], "trace sth. to 表示“把某事追溯到……原因”。", "from 可表示来源，但 trace the problem from... 不是本句所需结构。", 4)
add("词汇", "His success was largely due ______ careful planning rather than luck.", "to", ["for", "with", "by"], "due to 表示“由于”。", "due for 表示“预定应发生”，如 be due for a check-up，语义不同。", 3)
add("词汇", "The two versions differ greatly ______ style and level of difficulty.", "in", ["from", "with", "to"], "differ in 表示“在某方面不同”。", "differ from 表示“与……不同”，后面通常接比较对象，不接 style 这类方面。", 3)
add("词汇", "The course is aimed ______ students who need a quick review of grammar.", "at", ["to", "for", "on"], "be aimed at 表示“面向、针对”。", "aim to do 是动词结构，不能直接说 be aimed to students。", 3)
add("词汇", "The plan calls ______ more practice rather than more explanation.", "for", ["on", "up", "off"], "call for 表示“需要、要求”。", "call on 表示“拜访、号召”，与本句“需要练习”不符。", 3)
add("词汇", "The school will take measures to prevent such mistakes ______ happening again.", "from", ["to", "for", "with"], "prevent sth. from doing 表示“阻止某事发生”。", "prevent to do 是常见误用，不能作本句搭配。", 3)
add("词汇", "Students are encouraged to make use ______ every opportunity to speak English.", "of", ["for", "with", "to"], "make use of 是固定搭配，表示“利用”。", "use for 易被 use sth. for doing sth. 误导，但 make use 后必须接 of。", 2)
add("词汇", "The answer depends not on speed but ______ accuracy.", "on", ["in", "with", "for"], "depend on 表示“取决于”，not on... but on... 保持结构平行。", "but in 破坏平行结构，是常见的并列结构陷阱。", 3)
add("词汇", "The passage deals mainly ______ the relationship between memory and learning.", "with", ["about", "in", "for"], "deal with 表示“论述、处理”。", "about 可跟 talk/write 搭配，但 deal about 不自然。", 3)
add("词汇", "The writer objects ______ the idea that practice alone guarantees success.", "to", ["with", "against", "for"], "object to 表示“反对”。", "object against 可作动词短语但不适合本句标准搭配，考试中通常考 object to。", 4)
add("词汇", "The new exercise book is designed ______ beginners who lack a grammar foundation.", "for", ["to", "with", "by"], "be designed for 表示“为……设计”。", "be designed to 后面接动词原形，不能直接接 beginners。", 3)
add("词汇", "A good learner pays attention ______ both the answer and the reason behind it.", "to", ["on", "at", "for"], "pay attention to 是固定搭配。", "attention on 受 focus on 影响，是搭配迁移错误。", 2)
add("词汇", "The explanation should be brief but relevant ______ the question.", "to", ["with", "for", "about"], "be relevant to 表示“与……相关”。", "with 可表示伴随，但不能表达“相关于某问题”。", 3)
add("词汇", "The candidate was praised ______ his clear reasoning and careful expression.", "for", ["as", "with", "by"], "praise sb. for sth. 表示“因……表扬某人”。", "praised as 表示“被称赞为……”，后面通常接身份或评价名词。", 3)
add("词汇", "The teacher warned the class ______ copying examples without understanding them.", "against", ["from", "for", "of"], "warn sb. against doing sth. 表示“警告某人不要做某事”。", "warn sb. of/about sth. 表示提醒某事存在，不接 doing 表示禁止倾向。", 4)
add("词汇", "The applicant is capable ______ completing the task independently.", "of", ["for", "to", "with"], "be capable of doing sth. 表示“有能力做某事”。", "able to do 与 capable of doing 容易混淆，本句用 capable，所以接 of。", 3)
add("词汇", "The author refers ______ several studies to support his conclusion.", "to", ["with", "for", "about"], "refer to 表示“提到、参考”。", "refer with 不是标准搭配；support his conclusion 说明此处是引用研究。", 3)
add("词汇", "The word 'economic' in the passage is closest in meaning to ______.", "related to the economy", ["cheap to use", "saving money", "full of numbers"], "economic 表示“经济的、与经济有关的”。", "economical 才强调“节省的”，选项 cheap/saving money 是典型近形词陷阱。", 4)
add("词汇", "The word 'sensible' is closest in meaning to ______.", "reasonable", ["sensitive", "emotional", "visible"], "sensible 表示“明智的、合理的”。", "sensitive 表示“敏感的”，与 sensible 形近但意义不同。", 3)
add("词汇", "The word 'principal' in 'the principal reason' means ______.", "main", ["school head", "rule", "money"], "principal 作形容词时表示“主要的”。", "school head 是 principal 作名词时的含义，容易被词义迁移误导。", 4)
add("词汇", "If a statement is 'credible', it is ______.", "believable", ["easy to credit", "full of praise", "quick to complain"], "credible 表示“可信的”。", "credit 与 praise、贷款等含义有关，但 credible 在此处不是“值得表扬”。", 3)
add("词汇", "The verb 'raise' in 'raise a question' is closest in meaning to ______.", "bring up", ["rise", "arise", "arouse"], "raise a question 表示“提出问题”。", "rise/arise 是不及物动词，不能直接接 a question，是动词用法陷阱。", 4)
add("词汇", "The word 'considerate' is closest in meaning to ______.", "thoughtful of others", ["large in amount", "important", "carefully considered"], "considerate 表示“体贴的、为别人着想的”。", "considerable 表示“相当大的”，形近但意义不同。", 4)
add("词汇", "The word 'stationary' in 'a stationary object' means ______.", "not moving", ["writing paper", "temporary", "ordinary"], "stationary 表示“静止的”。", "stationery 表示“文具”，发音接近，是形近词陷阱。", 4)
add("词汇", "The word 'complement' in 'skills that complement each other' means ______.", "complete or improve", ["praise", "copy", "compete with"], "complement 表示“补充、使更完整”。", "compliment 表示“赞美”，和 complement 形近音近。", 4)
add("词汇", "The word 'adapt' is closest in meaning to ______.", "adjust", ["accept officially", "choose", "admire"], "adapt 表示“适应、调整”。", "adopt 表示“采纳、收养”，是高频形近词陷阱。", 3)
add("词汇", "The word 'infer' in a reading question means ______.", "draw a conclusion", ["suggest indirectly", "copy exactly", "explain fully"], "infer 表示“推断”。", "imply 是“暗示”，通常是作者或文本发出信息；读者是 infer。", 4)
add("词汇", "The word 'precede' is closest in meaning to ______.", "come before", ["continue", "go ahead with", "follow after"], "precede 表示“在……之前”。", "proceed 表示“继续进行”，形近但意义不同。", 4)
add("词汇", "The word 'ensure' is closest in meaning to ______.", "make certain", ["buy insurance for", "tell confidently", "permit"], "ensure 表示“确保”。", "insure 是“投保”，assure 是“向某人保证”，三者常被混淆。", 4)
add("词汇", "The word 'respective' in 'their respective tasks' means ______.", "separate and particular", ["respectful", "respectable", "similar"], "respective 表示“各自的”。", "respectful/respectable 都与尊重相关，但不是“各自的”。", 4)
add("词汇", "The word 'continuous' is closest in meaning to ______.", "without interruption", ["frequent but separate", "careful", "connected with time"], "continuous 表示“连续不断的”。", "continual 表示“反复发生的”，不一定没有中断。", 4)

add("语法", "By the time the lecture began, most students ______ their seats.", "had taken", ["took", "have taken", "were taking"], "By the time + 过去时间，主句表示更早完成的动作，用过去完成时。", "have taken 受中文“已经”影响，但时间基点是过去。", 3)
add("语法", "Neither the teacher nor the students ______ satisfied with the result.", "were", ["was", "is", "be"], "neither...nor... 作主语时遵循就近原则，students 是复数，所以用 were。", "was 容易只看 teacher，但谓语要靠近 students。", 4)
add("语法", "The number of students who choose this course ______ increasing.", "is", ["are", "were", "be"], "the number of... 作主语表示“……的数量”，谓语用单数。", "students 是复数名词，但真正主语是 number。", 3)
add("语法", "A number of useful examples ______ given in the last chapter.", "are", ["is", "was", "has"], "a number of 表示“许多”，后接复数名词，谓语用复数。", "the number of 和 a number of 的谓语形式正好相反。", 3)
add("语法", "The question is not as easy as it ______ at first sight.", "appears", ["is appeared", "appeared to", "appearing"], "appear 作系动词时不用被动，it appears 表示“它看起来”。", "is appeared 是把不及物/系动词误作被动。", 3)
add("语法", "Only after checking the answer ______ his mistake.", "did he realize", ["he realized", "he did realize", "realized he"], "Only + 状语置于句首时，主句要部分倒装。", "he realized 语序正常但漏了倒装，是考试常见陷阱。", 4)
add("语法", "Not until the final paragraph ______ the author's real attitude.", "did I understand", ["I understood", "I did understood", "understood I"], "Not until 置于句首时主句部分倒装，用 did + 动词原形。", "did understood 把助动词后动词原形规则忽略了。", 4)
add("语法", "No sooner had he finished the exercise ______ he found another mistake.", "than", ["when", "then", "that"], "no sooner...than... 是固定结构。", "hardly/scarcely 才常与 when 搭配，容易混淆。", 4)
add("语法", "Hardly had the test started ______ several students realized the questions were tricky.", "when", ["than", "that", "then"], "hardly...when... 表示“一……就……”。", "than 属于 no sooner...than... 的搭配。", 4)
add("语法", "It was because he reviewed his mistakes ______ he improved quickly.", "that", ["why", "which", "when"], "强调句结构为 It is/was + 被强调部分 + that...。", "because 已经在被强调部分中，后面不能再用 why。", 4)
add("语法", "The book is worth ______ carefully before the examination.", "reading", ["to read", "read", "being read"], "be worth doing 用主动形式表示被动意义。", "being read 看似被动，但 worth 后通常直接接动名词主动形式。", 3)
add("语法", "The teacher made the students ______ the sentence again.", "rewrite", ["to rewrite", "rewriting", "rewritten"], "make sb. do sth. 表示“让某人做某事”。", "to rewrite 受 ask sb. to do 影响，但 make 后省 to。", 3)
add("语法", "The students were made ______ the sentence again.", "to rewrite", ["rewrite", "rewriting", "rewritten"], "make 用于被动语态时，不定式符号 to 要还原。", "rewrite 是主动语态 make sb. do 的形式，不能用于被动。", 4)
add("语法", "I would rather you ______ the answer after thinking for yourself.", "checked", ["check", "will check", "to check"], "would rather + 从句表示现在或将来的愿望时，从句常用过去式。", "check 是原形，不能表达 would rather you... 的虚拟语气。", 5)
add("语法", "If I ______ more time, I would review all the wrong questions again.", "had", ["have", "will have", "had had"], "与现在事实相反的虚拟条件句从句用过去式。", "had had 表示与过去事实相反，不符合本句语境。", 4)
add("语法", "If he had followed the teacher's advice, he ______ fewer mistakes.", "would have made", ["would make", "will make", "made"], "与过去事实相反的虚拟条件句，主句用 would have done。", "would make 是对现在/将来的虚拟结果，不对应 had followed。", 5)
add("语法", "The suggestion that every student ______ a notebook for mistakes is practical.", "keep", ["keeps", "kept", "will keep"], "suggestion 后同位语从句表示建议时，用 should + 动词原形，should 可省略。", "keeps 受 every student 单数影响，但虚拟语气中用原形。", 5)
add("语法", "The reason ______ he gave for being late was not convincing.", "that", ["why", "because", "what"], "先行词 reason 在从句中作 gave 的宾语，用 that/which 或省略。", "why 用于 reason 在从句中作原因状语，如 the reason why he was late。", 4)
add("语法", "This is the factory ______ we visited last summer.", "that", ["where", "when", "why"], "factory 在定语从句中作 visited 的宾语，用 that/which。", "where 只有在从句中作地点状语时使用，如 where he works。", 3)
add("语法", "This is the factory ______ he worked for three years.", "where", ["that", "which", "what"], "factory 在从句中作地点状语，用 where。", "that/which 若作宾语可用，但 worked 后已有完整结构，不缺宾语。", 4)
add("语法", "He is the only student ______ answer was completely correct.", "whose", ["who", "whom", "which"], "whose 引导定语从句，表示所属关系。", "who 作主语，不能直接修饰 answer。", 3)
add("语法", "The more carefully you read the question, ______ mistakes you will make.", "the fewer", ["fewer", "the less", "less"], "the more..., the fewer... 是比较级平行结构；mistakes 可数，用 fewer。", "less 修饰不可数名词，不能修饰 mistakes。", 4)
add("语法", "So difficult ______ that few students got it right.", "was the question", ["the question was", "did the question", "the question did"], "So + 形容词置于句首时，主句部分倒装。", "the question was 是正常语序，放在 So difficult 后不符合倒装。", 4)
add("语法", "The passage is too difficult for beginners ______ without a dictionary.", "to understand", ["understanding", "understood", "understand"], "too...to do 表示“太……而不能……”。", "understanding 是动名词，不能接在 too difficult for beginners 后。", 3)
add("语法", "There is little doubt ______ regular review helps improve accuracy.", "that", ["whether", "which", "what"], "There is little/no doubt that... 表示“毫无疑问……”。", "whether 常用于 There is some doubt whether...，little doubt 后用 that。", 4)
add("语法", "It is necessary that every answer ______ checked before submission.", "be", ["is", "was", "will be"], "It is necessary that... 从句常用 should + 动词原形，should 可省略。", "is 符合陈述语气，但本结构要求虚拟语气。", 5)
add("语法", "The boy, together with his classmates, ______ preparing for the exam.", "is", ["are", "were", "be"], "主语后接 together with 短语时，谓语仍与前面的主语 the boy 一致。", "classmates 只是插入成分的一部分，不决定谓语。", 4)
add("语法", "Each of the answers ______ to be checked carefully.", "has", ["have", "are", "were"], "each of + 复数名词作主语时，谓语通常用单数。", "answers 是复数，但真正主语是 each。", 3)
add("语法", "What he needs most ______ not more books but better methods.", "is", ["are", "were", "be"], "What 引导的主语从句整体作单数概念，谓语用 is。", "books 是表语的一部分，不决定谓语。", 4)
add("语法", "The old method, if ______ properly, can still be useful.", "used", ["using", "use", "to use"], "if used properly 是 if it is used properly 的省略。", "using 会让 method 成为主动执行者，逻辑不通。", 4)
add("语法", "______ enough time, the students could finish the paper.", "Given", ["Giving", "To give", "Give"], "Given enough time 表示“如果给予足够时间”，过去分词表被动条件。", "Giving 会表示 students 主动给予时间，逻辑主语不一致。", 4)
add("语法", "The problem ______ at the meeting yesterday remains unsolved.", "discussed", ["discussing", "to discuss", "was discussed"], "discussed 作后置定语，表示“昨天会上被讨论的问题”。", "was discussed 会让句子出现两个谓语 remains 和 was discussed。", 4)
add("语法", "The man standing at the gate is the professor ______ lecture we attended.", "whose", ["whom", "which", "who"], "whose lecture 表示“他的讲座”。", "whom/who 指人，但不能直接修饰 lecture。", 3)
add("语法", "He spoke slowly so that every student ______ follow him.", "could", ["can", "may", "must"], "主句为过去时 spoke，目的状语从句常用 could。", "can 与过去时不协调；must 语气过强，不表示目的能力。", 3)
add("语法", "The task is more difficult than we ______ expected.", "had", ["have", "were", "are"], "expected 发生在发现任务困难之前，过去的过去可用 had expected。", "have expected 与过去语境不一致。", 4)
add("语法", "I still remember ______ to the library for the first time.", "being taken", ["taking", "to take", "to be taking"], "remember being taken 表示“记得曾被带去”。", "taking 表示自己带别人去，逻辑主语不一致。", 4)
add("语法", "The teacher asked us to avoid ______ the same mistake twice.", "making", ["to make", "made", "make"], "avoid 后接动名词。", "to make 受 want/plan to do 影响，是非谓语搭配陷阱。", 3)
add("语法", "He failed the test, ______ surprised everyone in the class.", "which", ["that", "what", "it"], "which 可引导非限制性定语从句，指代前面整件事。", "that 不能引导逗号后的非限制性定语从句。", 4)
add("语法", "______ the question was simple, many students chose the wrong answer.", "Although", ["Because", "Since", "As"], "前后构成让步关系：题目简单，但很多人选错。", "Because/Since/As 表原因，会让逻辑反向。", 3)
add("语法", "He did not know ______ answer to choose.", "which", ["what", "how", "where"], "which answer 表示“哪一个答案”。", "what answer 也可见于口语，但考试中针对限定选项更常用 which。", 3)
add("语法", "The students are used to ______ notes while listening.", "taking", ["take", "took", "to take"], "be used to doing 表示“习惯于做某事”。", "used to do 表示“过去常常”，与 be used to doing 不同。", 3)
add("语法", "The window needs ______ before the classroom is used again.", "cleaning", ["to clean", "clean", "being cleaned"], "need doing 可表示被动意义。", "to clean 表示主动去清洁，主语 window 不能主动执行。", 4)

add("语用", "- Could you help me carry these books? - ______", "With pleasure.", ["Never mind.", "It doesn't matter.", "Congratulations."], "With pleasure 用来答应别人请求，表示“乐意效劳”。", "Never mind/It doesn't matter 用于回应道歉，不用于答应帮忙。", 2)
add("语用", "- I'm sorry I kept you waiting. - ______", "It doesn't matter.", ["With pleasure.", "Good idea.", "Here you are."], "回应道歉可用 It doesn't matter。", "With pleasure 是答应请求，不是回应道歉。", 2)
add("语用", "- Thank you for your useful advice. - ______", "You're welcome.", ["Never mind.", "Good luck.", "No, thanks."], "You're welcome 用于回应感谢。", "Never mind 用于回应道歉或安慰，不用于感谢。", 2)
add("语用", "- I have passed the interview. - ______", "Congratulations!", ["I'm sorry to hear that.", "Never mind.", "Help yourself."], "听到对方通过面试，应表示祝贺。", "I'm sorry to hear that 用于坏消息，语境相反。", 2)
add("语用", "- Would you mind opening the window? - ______", "Not at all.", ["Yes, please.", "No, you can't.", "It is a window."], "Would you mind...? 同意对方请求时常说 Not at all。", "Yes, please 容易按中文“好的”误选，但在 mind 问句中不自然。", 3)
add("语用", "- Shall we review the wrong questions first? - ______", "Good idea.", ["No, I don't.", "You're welcome.", "I am fine."], "对建议表示赞同可用 Good idea。", "You're welcome 只能回应感谢。", 2)
add("语用", "- May I use your dictionary for a moment? - ______", "Sure, go ahead.", ["Yes, you may not.", "It depends yesterday.", "I disagree it."], "对许可请求的肯定回答可用 Sure, go ahead。", "may not 表示不允许，与肯定语境相反。", 3)
add("语用", "- I feel nervous before the exam. - ______", "Take it easy.", ["Help yourself.", "What a pity!", "Don't mention it."], "Take it easy 用于安慰紧张的人。", "What a pity 用于遗憾，不适合鼓励考前紧张。", 3)
add("语用", "- Could I speak to Mr. Brown, please? - ______", "Hold on, please.", ["I am Mr. Brown's book.", "No speaking.", "You are welcome."], "电话用语中 Hold on, please 表示“请稍等”。", "You are welcome 是回应感谢，不是电话转接语。", 3)
add("语用", "- Would you like some more tea? - ______", "No, thank you.", ["No, I wouldn't like.", "I don't like you.", "Never mind."], "礼貌拒绝饮品可用 No, thank you。", "No, I wouldn't like 语法和语气都不自然。", 3)
add("语用", "- I lost my notes on the way here. - ______", "What a pity!", ["Congratulations!", "Good idea.", "With pleasure."], "对坏消息表示遗憾可用 What a pity。", "Congratulations 用于好消息，语境相反。", 2)
add("语用", "- Do you mind if I sit here? - ______ It's free.", "Not at all.", ["Yes, please.", "No, you mind.", "I don't sit."], "Do you mind if...? 允许对方时说 Not at all/Of course not。", "Yes, please 在此容易造成“介意”的含义，不是理想回答。", 4)
add("语用", "- I failed the test again. - ______ You can do better next time.", "Don't lose heart.", ["Enjoy yourself.", "No problem.", "It tastes nice."], "Don't lose heart 用于鼓励失落的人。", "No problem 多用于回应请求或感谢，安慰力度和语境不合。", 3)
add("语用", "- I'm afraid I can't join your study group tonight. - ______", "That's all right.", ["I don't afraid.", "You must afraid.", "Here it is."], "对方无法参加时，That's all right 可表示理解。", "I don't afraid 是中式英语，语法错误。", 3)
add("语用", "- How about doing a short quiz before class? - ______", "Sounds good.", ["It hears good.", "I hear it.", "Never mind."], "Sounds good 表示赞同建议。", "It hears good 是把 sound 作普通动词误用。", 3)
add("语用", "- Excuse me, could you tell me where the library is? - ______", "Go straight and turn left.", ["You are library.", "Yes, I could not.", "Thank you."], "问路时应给出方向。", "Thank you 是提问者可能说的话，不是回答者的指路回答。", 3)
add("语用", "- I have to leave now. See you tomorrow. - ______", "See you.", ["I see it.", "See what?", "You see."], "告别回应可用 See you。", "I see it 是“我看见它”，不是告别语。", 2)
add("语用", "- Could you repeat the last sentence? - ______", "Certainly.", ["I repeat you.", "No sentence.", "Thanks a lot."], "Certainly 可礼貌答应重复。", "I repeat you 是直译错误，应为 repeat the sentence。", 3)


def build_question(spec: dict, rng: random.Random) -> dict:
    options, answer = make_options(spec["correct"], spec["distractors"], rng)
    explanation = (
        f"本题考查英语运用中的「{spec['submodule']}」。正确答案为 {answer}（{spec['correct']}）。"
        f"{spec['reason']} 本题陷阱：{spec['trap']} "
        "做题时要同时检查搭配、句法位置和语境逻辑，不能只凭中文大意选择。"
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
    rng = random.Random(20260505)
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
    lines = [
        "# COMMON 英语运用 batch 004 陷阱题补充质检",
        "",
        f"- 文件：`{OUTPUT_PATH.name}`",
        f"- 题量：{len(questions)}",
        "- 定位：补充语言知识中高频搭配、近形近义辨析、句法结构和交际用语。",
        "- 陷阱策略：每题至少设置一个看似合理但在搭配、语法或语境上不成立的强干扰项。",
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
    if len(questions) < 90:
        raise ValueError(f"Generated too few questions: {len(questions)}")
    OUTPUT_PATH.write_text(json.dumps({"questions": questions}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_review(questions)
    print(f"Generated {len(questions)} questions")
    print(f"Wrote {OUTPUT_PATH}")
    print(f"Wrote {REVIEW_PATH}")


if __name__ == "__main__":
    main()
