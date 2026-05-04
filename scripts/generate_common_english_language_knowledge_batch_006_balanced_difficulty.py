from __future__ import annotations

import json
import random
import re
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "common_english_language_knowledge_batch_006_balanced_difficulty.json"
REVIEW_PATH = PROJECT_ROOT / "data" / "common_english_language_knowledge_batch_006_balanced_difficulty_review.md"


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
    difficulty: int,
    submodule: str,
    stem: str,
    correct: str,
    distractors: list[str],
    reason: str,
    trap: str,
    error_tag: str,
) -> None:
    SPECS.append(
        {
            "difficulty": difficulty,
            "submodule": submodule,
            "stem": stem,
            "correct": correct,
            "distractors": distractors,
            "reason": reason,
            "trap": trap,
            "error_tag": error_tag,
        }
    )


for item in [
    ("词汇", "Please ______ your name at the top of the answer sheet.", "write", ["read", "listen", "speak"], "write one's name 表示“写下姓名”。", "read/listen/speak 都是常见动词，但不能和 name 构成本句动作。", "词义基础"),
    ("词汇", "The students are asked to ______ the text aloud.", "read", ["look", "see", "watch"], "read the text aloud 表示“大声朗读课文”。", "look/see/watch 都与“看”有关，但不能表示朗读文本。", "词义基础"),
    ("词汇", "The class will begin ______ nine o'clock.", "at", ["in", "on", "by"], "具体时刻前用 at。", "in 用于较长时间段，on 用于具体日期，容易混用。", "介词基础"),
    ("词汇", "The teacher is kind ______ all the students.", "to", ["for", "with", "at"], "be kind to sb. 表示“对某人友好”。", "kind of 表示“有点儿”，kind for 不是本句搭配。", "搭配基础"),
    ("词汇", "The answer is different ______ yours.", "from", ["with", "to", "for"], "be different from 是常用搭配。", "with/to 受中文“和……不同”影响，容易误选。", "搭配基础"),
    ("词汇", "We should listen ______ the teacher carefully.", "to", ["at", "for", "with"], "listen to 表示“听”。", "hear 不加 to，但 listen 后需要 to。", "搭配基础"),
    ("词汇", "The boy is good ______ English grammar.", "at", ["in", "on", "for"], "be good at 表示“擅长”。", "good for 表示“对……有好处”，语义不同。", "搭配基础"),
    ("词汇", "The book is useful ______ beginners.", "for", ["to", "with", "on"], "be useful for sb. 表示“对某人有用”。", "useful to 也可见，但本句表示对象适用性，用 for 最自然。", "搭配基础"),
    ("词汇", "The girl smiled ______ me when she entered the room.", "at", ["to", "for", "with"], "smile at sb. 表示“朝某人微笑”。", "to 容易受 say to sb. 影响。", "搭配基础"),
    ("词汇", "He arrived ______ school early this morning.", "at", ["to", "in", "on"], "arrive at + 小地点。", "arrive to 是常见误用。", "介词基础"),
    ("语法", "My brother ______ English every morning.", "studies", ["study", "studying", "studied"], "主语 My brother 为第三人称单数，一般现在时谓语加 -s。", "study 忘记三单变化，是基础语法陷阱。", "主谓一致"),
    ("语法", "There ______ two books on the desk.", "are", ["is", "was", "be"], "There be 句型中 be 与后面的复数名词 two books 一致。", "只看 there 容易误选单数。", "主谓一致"),
    ("语法", "She ______ to school by bus yesterday.", "went", ["go", "goes", "going"], "yesterday 提示一般过去时。", "goes 是一般现在时三单，不符合过去时间。", "时态基础"),
    ("语法", "They are interested in ______ English songs.", "singing", ["sing", "to sing", "sang"], "介词 in 后接动名词。", "to sing 受 want to do 影响，但介词后不用不定式。", "非谓语基础"),
    ("语法", "I have ______ finished my homework.", "already", ["yet", "still", "ever"], "肯定句中表示“已经”常用 already。", "yet 常用于否定句或疑问句。", "副词基础"),
    ("语法", "He is ______ honest student.", "an", ["a", "the", "/"], "honest 以元音音素开头，用 an。", "只看字母 h 容易误选 a。", "冠词基础"),
    ("语法", "This is the book ______ I bought yesterday.", "that", ["who", "where", "when"], "先行词 book 在从句中作 bought 的宾语，用 that/which。", "where/when 是状语关系词，不作宾语。", "从句基础"),
    ("语法", "I don't know ______ he lives.", "where", ["who", "what", "which"], "live 是不及物动词，后面需要地点状语。", "what 不能作 live 的地点状语。", "从句基础"),
    ("语用", "- Thank you very much. - ______", "You're welcome.", ["Good luck.", "Never mind.", "I'm sorry."], "回应感谢用 You're welcome。", "Never mind 多用于回应道歉。", "语境基础"),
    ("语用", "- I'm sorry I'm late. - ______", "That's all right.", ["Good idea.", "Here you are.", "Congratulations."], "回应道歉可用 That's all right。", "Good idea 用于回应建议。", "语境基础"),
    ("语用", "- Happy birthday! - ______", "Thank you.", ["The same to you.", "Good night.", "Never mind."], "别人祝生日快乐，应表示感谢。", "The same to you 常用于节日互祝，不适合生日祝福。", "语境基础"),
    ("语用", "- Can I help you? - ______", "Yes, please.", ["Yes, I can.", "No, I help.", "Good luck."], "服务场景中接受帮助用 Yes, please。", "Yes, I can 是回答能力问题，不回应服务提问。", "语境基础"),
    ("语用", "- Have a nice weekend! - ______", "Thanks. The same to you.", ["I'm sorry.", "No, I don't.", "Here it is."], "祝愿类表达可用 Thanks. The same to you. 回应。", "I'm sorry 与祝愿语境不符。", "语境基础"),
    ("语用", "- Would you like some water? - ______", "Yes, please.", ["I like water.", "Never mind.", "You are right."], "接受饮品邀请可用 Yes, please。", "I like water 只是陈述喜好，不是自然回应。", "语境基础"),
    ("语用", "- Good night, Mum. - ______", "Good night.", ["Good morning.", "Good idea.", "That's right."], "夜间告别用 Good night 回应。", "Good morning 时间语境相反。", "语境基础"),
]:
    add(1, *item)


for item in [
    ("词汇", "The meeting was put ______ because the speaker was ill.", "off", ["up", "out", "away"], "put off 表示“推迟”。", "put up 表示张贴或搭建，put out 表示扑灭，均不合语境。", "短语动词"),
    ("词汇", "Please look ______ the new words in a dictionary.", "up", ["at", "after", "over"], "look up 表示“查阅”。", "look at 是看，look after 是照顾，和查词典不同。", "短语动词"),
    ("词汇", "The old man lives ______, but he does not feel lonely.", "alone", ["lonely", "single", "only"], "alone 表示“独自地”。", "lonely 表示“孤独的”，是形容词，不修饰 lives。", "词义混淆"),
    ("词汇", "This question is ______ easy, but many students still make mistakes.", "rather", ["quiet", "quite", "quit"], "quite/rather 都可修饰形容词，但本句选 rather 表“相当”。", "quiet 与 quite 形近，quit 是动词“退出”。", "形近词"),
    ("词汇", "The teacher asked us to pay attention ______ the spelling of the word.", "to", ["on", "at", "for"], "pay attention to 是固定搭配。", "attention on 受 focus on 影响，是搭配迁移。", "搭配误判"),
    ("词汇", "The train is expected to arrive ______ ten minutes.", "in", ["after", "at", "by"], "in + 时间段可表示“多久以后”。", "after ten minutes 不如 in ten minutes 自然，at 接具体时刻。", "介词辨析"),
    ("词汇", "He borrowed a book ______ the school library.", "from", ["to", "with", "for"], "borrow sth. from... 表示“从……借来”。", "lend sth. to sb. 与 borrow from 方向相反。", "动词搭配"),
    ("词汇", "The teacher divided the class ______ four groups.", "into", ["in", "to", "with"], "divide...into... 表示“把……分成……”。", "to 受 translate into 等结构干扰。", "搭配误判"),
    ("词汇", "The boy spent two hours ______ the grammar exercises.", "on", ["in", "for", "with"], "spend time on sth. 表示“花时间在某事上”。", "spend time doing 也可用，但后面是名词 exercises，所以用 on。", "搭配误判"),
    ("词汇", "The new rule will come ______ effect next month.", "into", ["in", "to", "on"], "come into effect 表示“生效”。", "in effect 表示“实际上/有效”，结构不同。", "固定搭配"),
    ("语法", "The room needs ______ before the guests arrive.", "cleaning", ["to clean", "clean", "cleaned"], "need doing 可表示被动意义。", "to clean 会让 room 主动清洁，逻辑不通。", "非谓语"),
    ("语法", "He suggested that we ______ the answer again.", "check", ["checked", "checks", "will check"], "suggest 表建议时，从句用 should + 动词原形，should 可省略。", "checks 受 we 后谓语影响，但这里是虚拟语气。", "虚拟语气"),
    ("语法", "The woman ______ is speaking now is our English teacher.", "who", ["which", "where", "when"], "先行词 woman 指人，且在从句中作主语，用 who。", "which 指物，where/when 是状语关系词。", "从句关系"),
    ("语法", "This is the place ______ we had the meeting.", "where", ["which", "that", "what"], "place 在从句中作地点状语，用 where。", "had the meeting 结构完整，不缺宾语，不能用 which/that 作宾语。", "从句关系"),
    ("语法", "I prefer reading at home to ______ outside.", "playing", ["play", "to play", "played"], "prefer doing A to doing B 要保持结构平行。", "to play 受 prefer to do 干扰，但本句是 prefer A to B。", "平行结构"),
    ("语法", "He has lived here ______ 2020.", "since", ["for", "during", "in"], "since 后接时间点，for 后接时间段。", "2020 是时间点，不是时间段。", "时态标志"),
    ("语法", "We have studied English ______ three years.", "for", ["since", "during", "by"], "for 后接时间段。", "since 后接时间点，不能接 three years 表持续时长。", "时态标志"),
    ("语法", "The more you practice, ______ you will become.", "the better", ["better", "the best", "best"], "the more..., the better... 是固定比较结构。", "better 缺少第二个 the，结构不完整。", "比较结构"),
    ("语用", "- Could you pass me the salt? - ______", "Here you are.", ["Good luck.", "No, thanks.", "It doesn't matter."], "递东西给对方常用 Here you are。", "No, thanks 是拒绝别人提供物品，不是递物回应。", "语境误判"),
    ("语用", "- I have passed the driving test. - ______", "Congratulations!", ["Never mind.", "What a pity!", "Help yourself."], "听到好消息应祝贺。", "What a pity 用于坏消息，语境相反。", "语境误判"),
    ("语用", "- Would you mind my sitting here? - ______", "Of course not.", ["Yes, sit down.", "You are welcome.", "Good idea."], "mind 问句中同意对方可说 Of course not。", "Yes, sit down 在 mind 问句中容易产生“介意”的歧义。", "语境误判"),
    ("语用", "- I'm afraid I can't go with you. - ______", "That's OK.", ["Well done.", "Congratulations.", "Good morning."], "对方无法同行时，可用 That's OK 表示理解。", "Well done 是表扬，语境不合。", "语境误判"),
    ("语用", "- Shall we meet at the library? - ______", "Good idea.", ["You're welcome.", "I'm sorry to hear that.", "Never mind."], "对建议表示赞同可用 Good idea。", "You're welcome 回应感谢。", "语境误判"),
    ("语用", "- I feel a little nervous. - ______", "Take it easy.", ["Enjoy yourself.", "Help yourself.", "Don't mention it."], "Take it easy 用于安慰紧张的人。", "Don't mention it 回应感谢。", "语境误判"),
    ("语用", "- May I take this seat? - ______", "Yes, please.", ["No, thanks.", "You're welcome.", "It doesn't matter."], "对请求许可表示同意，可用 Yes, please。", "No, thanks 是拒绝别人提供物品。", "语境误判"),
]:
    add(2, *item)


for item in [
    ("词汇", "The article provides a useful ______ into how students learn vocabulary.", "insight", ["sight", "site", "signal"], "insight into 表示“对……的洞察”。", "sight/site 与 insight 形近音近，但语义完全不同。", "形近词"),
    ("词汇", "The new evidence is not ______ to the main argument.", "relevant", ["relative", "reliable", "reluctant"], "be relevant to 表示“与……相关”。", "relative 表示相对的或亲属，reliable 表示可靠的。", "词义混淆"),
    ("词汇", "The teacher's explanation helped ______ the difference between the two words.", "clarify", ["classify", "verify", "simplify"], "clarify 表示“阐明、讲清楚”。", "classify 是分类，verify 是核实，simplify 是简化。", "近义辨析"),
    ("词汇", "The question requires students to ______ information from the last paragraph.", "infer", ["imply", "refer", "prefer"], "infer 表示“推断”。", "imply 是作者或文本暗示，读者应 infer。", "词义方向"),
    ("词汇", "The teacher tried to ______ students that the test would not be too difficult.", "assure", ["ensure", "insure", "secure"], "assure sb. that... 表示“向某人保证”。", "ensure 是确保，insure 是投保。", "词义混淆"),
    ("词汇", "The new policy may ______ students' choices of courses.", "affect", ["effect", "effort", "offer"], "affect 作动词表示“影响”。", "effect 常作名词“效果”，不能直接作本句谓语。", "词性误判"),
    ("词汇", "A good answer should be both accurate and ______.", "concise", ["conscious", "complex", "considerate"], "concise 表示“简明的”。", "conscious 是有意识的，considerate 是体贴的。", "词义混淆"),
    ("词汇", "The result was ______ with what we had expected.", "consistent", ["constant", "convenient", "considerate"], "be consistent with 表示“与……一致”。", "constant 表示持续不变，convenient 表示方便的。", "形近词"),
    ("词汇", "The two methods are similar in purpose but different in ______.", "approach", ["access", "accent", "account"], "approach 表示“方法、途径”。", "access 是入口或使用权，account 是账户或解释。", "词义混淆"),
    ("词汇", "The word 'economical' is closest in meaning to ______.", "saving money", ["related to the economy", "full of numbers", "widely used"], "economical 表示“节约的、经济实惠的”。", "economic 才表示“经济的、与经济有关的”。", "形近词"),
    ("语法", "Only when the context is clear ______ the correct answer.", "can we choose", ["we can choose", "we choose", "can choose we"], "Only + 状语从句置于句首，主句部分倒装。", "we can choose 是正常语序，漏了倒装。", "倒装结构"),
    ("语法", "The book is worth ______ more than once.", "reading", ["to read", "being read", "read"], "be worth doing 用主动形式表被动意义。", "being read 看似被动，但 worth 后一般用主动动名词。", "非谓语"),
    ("语法", "I remember ______ this expression in a previous exercise.", "seeing", ["to see", "see", "seen"], "remember doing 表示“记得做过”。", "remember to do 表示记得要去做，语义不同。", "非谓语"),
    ("语法", "Please remember ______ your answers before you submit the paper.", "to check", ["checking", "checked", "check"], "remember to do 表示“记得去做”。", "checking 表示记得做过，不符合 submit 前的未完成动作。", "非谓语"),
    ("语法", "The reason ______ he gave was not convincing.", "that", ["why", "because", "what"], "reason 在从句中作 gave 的宾语，用 that/which 或省略。", "why 用于 reason 作原因状语的情况。", "从句关系"),
    ("语法", "The reason ______ he was absent remains unknown.", "why", ["that", "which", "what"], "reason 在从句中作原因状语，用 why。", "that/which 作宾语或主语，本句从句不缺宾语。", "从句关系"),
    ("语法", "It was in the last paragraph ______ the answer was hidden.", "that", ["where", "which", "what"], "强调句结构为 It was...that...。", "where 容易受 paragraph 地点含义影响，但本句是强调句。", "强调句"),
    ("语法", "He speaks English as if he ______ abroad for years.", "had lived", ["has lived", "lives", "will live"], "as if 表与事实相反或不确定时，可用虚拟语气；for years 指过去经历，用 had lived。", "has lived 是真实陈述，不符合 as if 的虚拟意味。", "虚拟语气"),
    ("语用", "- I don't think this answer is correct. - ______ The context supports another choice.", "I agree.", ["No problem.", "Congratulations.", "Help yourself."], "后句说明语境支持另一个选项，因此应同意前者的否定判断。", "No problem 是回应请求或感谢，不表达观点一致。", "语境逻辑"),
    ("语用", "- The test was easier than expected. - ______", "So it was.", ["So was it.", "So did it.", "So it did."], "So it was 表示同意对方对同一事物的判断。", "So was it 表示另一个对象也如此，不是本句所需。", "倒装语用"),
    ("语用", "- Jane didn't finish the paper. - ______", "Neither did I.", ["So did I.", "Neither I did.", "So I did."], "否定情况的“我也没有”用 Neither + 助动词 + 主语。", "So did I 用于肯定的“我也一样”。", "倒装语用"),
    ("语用", "- Could you help me with this sentence? - ______ I have to leave now.", "Sorry, I can't.", ["With pleasure.", "No problem.", "Certainly."], "后句说明马上离开，所以应礼貌拒绝。", "With pleasure/No problem/Certainly 都表示同意，和后句矛盾。", "语境逻辑"),
    ("语用", "- I got the lowest score in the group. - ______ You can improve by reviewing mistakes.", "Don't lose heart.", ["Good appetite.", "Enjoy yourself.", "You are welcome."], "对失落的人应鼓励。", "Enjoy yourself 用于祝玩得开心，语境不合。", "语境误判"),
    ("语用", "- Could you repeat the question? - ______", "Certainly.", ["It repeats.", "No question.", "You repeat me."], "Certainly 可表示答应请求。", "You repeat me 是直译错误。", "语境基础"),
    ("语用", "- What do you think of the new grammar book? - ______", "It is very helpful.", ["Yes, I do.", "No, I don't.", "At the bookstore."], "What do you think of...? 问评价，应回答看法。", "Yes/No 不能回答开放评价问题。", "问答匹配"),
]:
    add(3, *item)


for item in [
    ("词汇", "The scholar's argument is persuasive because it is supported by ______ evidence.", "substantial", ["subtle", "subjective", "suspicious"], "substantial evidence 表示“充分的证据”。", "subtle 是微妙的，subjective 是主观的，不能支撑 persuasive。", "词义混淆"),
    ("词汇", "The instructions are ______; students may easily misunderstand them.", "ambiguous", ["ambitious", "available", "accurate"], "ambiguous 表示“含糊的、有歧义的”。", "ambitious 是有雄心的，形近但语义不同。", "形近词"),
    ("词汇", "The two ideas are not contradictory; they are actually ______.", "complementary", ["complimentary", "compulsory", "complicated"], "complementary 表示“互补的”。", "complimentary 表示赞美的或免费的，形近音近。", "形近词"),
    ("词汇", "The passage is mainly concerned ______ the causes of test anxiety.", "with", ["about", "for", "to"], "be concerned with 表示“涉及、关于”。", "be concerned about 表示“担心”，语义不同。", "搭配误判"),
    ("词汇", "The report draws a clear distinction ______ ability and performance.", "between", ["among", "from", "with"], "distinction between A and B 表示“两者之间的区别”。", "distinguish A from B 与 distinction between 易混。", "搭配误判"),
    ("词汇", "The answer is acceptable only ______ certain conditions.", "under", ["below", "beneath", "within"], "under certain conditions 表示“在某些条件下”。", "within 表范围，但不搭配 conditions 表条件限制。", "介词辨析"),
    ("词汇", "The old method is no longer ______ to the needs of today's learners.", "adequate", ["accurate", "available", "accidental"], "adequate to/for 表示“足以满足”。", "accurate 是准确的，不能表达“足够满足需求”。", "词义混淆"),
    ("词汇", "His conclusion was based on a ______ interpretation of the data.", "biased", ["balanced", "beneficial", "brief"], "biased 表示“有偏见的”。", "balanced 与 biased 意义相反，容易因首字母相近误选。", "词义对立"),
    ("词汇", "The writer's tone is ______ rather than emotional.", "objective", ["objectionable", "obligatory", "ordinary"], "objective 表示“客观的”。", "objectionable 表示令人反感的，形近但意义不同。", "形近词"),
    ("词汇", "The survey results should be interpreted with ______.", "caution", ["courage", "custom", "capacity"], "with caution 表示“谨慎地”。", "courage 是勇气，capacity 是能力或容量，语义不合。", "固定搭配"),
    ("语法", "Had the students read the instructions carefully, they ______ fewer mistakes.", "would have made", ["would make", "will make", "made"], "省略 if 的过去虚拟条件句，主句用 would have done。", "would make 对应现在/将来虚拟，不符合 Had read。", "虚拟语气"),
    ("语法", "Were the rule simpler, more students ______ it correctly.", "would use", ["will use", "used", "had used"], "Were... 是与现在事实相反的虚拟倒装，主句用 would do。", "will use 是真实条件句的将来。", "虚拟倒装"),
    ("语法", "Not until he checked the context ______ the correct answer.", "did he find", ["he found", "he did found", "found he"], "Not until 置于句首，主句部分倒装。", "did found 忽视助动词后用动词原形。", "倒装结构"),
    ("语法", "No sooner had the test begun ______ several students noticed the trap.", "than", ["when", "then", "that"], "no sooner...than... 是固定倒装结构。", "hardly/scarcely 才常与 when 搭配。", "倒装结构"),
    ("语法", "Hardly had he opened the book ______ the teacher asked him to close it.", "when", ["than", "that", "then"], "hardly...when... 表示“一……就……”。", "than 属于 no sooner...than...。", "倒装结构"),
    ("语法", "The proposal that every student ______ a mistake notebook was accepted.", "keep", ["keeps", "kept", "will keep"], "proposal 后同位语从句表示建议时，用 should + 动词原形，should 可省略。", "keeps 受 every student 单数影响，但虚拟语气用原形。", "虚拟语气"),
    ("语法", "The question is not so simple as it first ______.", "appears", ["is appeared", "appeared to", "appearing"], "appear 作系动词时不用被动。", "is appeared 是把系动词误作被动。", "语态误判"),
    ("语法", "The sentence reads better if the adverb ______ at the end.", "is placed", ["places", "is placing", "placed"], "adverb 是被放置的对象，用被动语态。", "places 会让 adverb 主动放置，逻辑不通。", "语态误判"),
    ("语用", "- I suppose the answer is D. - ______ The phrase after the blank requires a gerund.", "I don't think so.", ["Exactly.", "That's right.", "Well done."], "后句指出结构要求动名词，说明不同意 D。", "Exactly/That's right 与后句纠错矛盾。", "语境逻辑"),
    ("语用", "- I have never seen such a difficult question. - ______", "Neither have I.", ["So have I.", "Neither I have.", "So I have."], "否定陈述的“我也没有”用 Neither + 助动词 + 主语。", "So have I 用于肯定附和。", "倒装语用"),
    ("语用", "- He can explain the rule clearly. - ______", "So can I.", ["So I can.", "Neither can I.", "So do I."], "So can I 表示“我也能”。", "So I can 表示强调自己确实能，不表示“也”。", "倒装语用"),
    ("语用", "- I am afraid the plan won't work. - ______ We need a better one.", "I share your concern.", ["Enjoy yourself.", "Here you are.", "Don't mention it."], "后句表明同样担心，应说 I share your concern。", "Don't mention it 回应感谢，不表达担忧一致。", "语境判断"),
    ("语用", "- Would you mind if I corrected your answer? - ______ I need to know my mistake.", "Not at all.", ["Yes, don't.", "No, you mind.", "It doesn't matter."], "允许对方纠正可用 Not at all。", "It doesn't matter 回应道歉，不能直接表示允许纠正。", "语境判断"),
    ("语用", "- The sentence seems correct to me. - ______ There is a subject-verb agreement error.", "Look more carefully.", ["Congratulations.", "Never mind.", "Good appetite."], "后句指出语法错误，应提醒对方再仔细看。", "Never mind 用于安慰或回应道歉，不适合纠错。", "语境逻辑"),
    ("语用", "- Could I hand in the paper after class? - ______ The deadline is fixed.", "I'm afraid not.", ["With pleasure.", "Good luck.", "Help yourself."], "后句说明截止时间固定，应礼貌拒绝。", "With pleasure 表示同意帮忙，和后句矛盾。", "语境逻辑"),
]:
    add(4, *item)


for item in [
    ("词汇", "The evidence is ______ at best, so the conclusion should not be accepted too quickly.", "tentative", ["tempting", "temporary", "tremendous"], "tentative 表示“暂定的、试探性的、不确定的”。", "tempting 是诱人的，temporary 是临时的，不能准确描述证据强度。", "词义精辨"),
    ("词汇", "The two theories are not mutually ______; both may explain part of the phenomenon.", "exclusive", ["inclusive", "conclusive", "excessive"], "mutually exclusive 表示“相互排斥的”。", "inclusive 是包容的，conclusive 是决定性的，形近但搭配不同。", "固定搭配"),
    ("词汇", "The author's argument rests on a rather ______ assumption.", "questionable", ["questioning", "questioned", "questionary"], "questionable 表示“可疑的、有问题的”。", "questioned 是被质疑过的，questionary 不是常用形容词。", "词性误判"),
    ("词汇", "The policy was criticized for being ______ with earlier promises.", "inconsistent", ["constant", "consisting", "considerate"], "be inconsistent with 表示“与……不一致”。", "consisting 常与 of 搭配，不能作本句表语形容词。", "形近词"),
    ("词汇", "The speaker tried to ______ the objection by giving a concrete example.", "counter", ["count", "encounter", "account"], "counter 作动词可表示“反驳、抵消”。", "encounter 是遇到，account for 是解释，不能直接表示反驳 objection。", "词义精辨"),
    ("词汇", "The answer is grammatically possible but ______ inappropriate in this context.", "pragmatically", ["practically", "programmatically", "grammatically"], "pragmatically 表示“从语用角度看”。", "practically 表示实际上，grammatically 与前文重复且不表达语境得体性。", "语用词汇"),
    ("词汇", "The phrase is ______ used in formal writing, so it sounds odd in a casual dialogue.", "predominantly", ["previously", "precisely", "presently"], "predominantly 表示“主要地、大多”。", "previously 是以前，presently 是目前或不久，语义不合。", "副词辨析"),
    ("词汇", "The distinction is ______ but important for choosing the correct option.", "subtle", ["substantial", "sudden", "suitable"], "subtle 表示“微妙的、不易察觉的”。", "substantial 是大量的、实质性的，与 distinction 的细微性不符。", "词义精辨"),
    ("词汇", "The rule has several ______, which makes it difficult for beginners.", "exceptions", ["expectations", "experiments", "expressions"], "exception 表示“例外”。", "expectation 表示期望，形近但意义不同。", "形近词"),
    ("词汇", "The explanation is clear, but its application is ______ by several conditions.", "constrained", ["constructed", "concentrated", "concluded"], "constrained by 表示“受……限制”。", "constructed 是建造，concentrated 是集中，不能表达限制。", "词义精辨"),
    ("语法", "Had it not been for his careful review, he ______ the same mistake again.", "would have made", ["would make", "will make", "had made"], "Had it not been for... 是 If it had not been for... 的倒装，主句用 would have done。", "would make 不对应过去虚拟。", "虚拟倒装"),
    ("语法", "Should you encounter a similar structure, you ______ the verb form first.", "should check", ["checked", "had checked", "checking"], "Should you... 可表示 If you should...，主句用 should/imperative 等。", "checked 是过去式，不能作此条件结构的主句谓语。", "虚拟倒装"),
    ("语法", "It is high time that students ______ more attention to collocations.", "paid", ["pay", "will pay", "have paid"], "It is high time that... 后常用过去式表示“早该……”。", "pay 是原形，不能体现该结构的虚拟意味。", "虚拟语气"),
    ("语法", "But for the hint in the last sentence, I ______ the answer.", "would not have found", ["will not find", "would not find", "had not found"], "But for 表示“要不是”，本句指过去情况，主句用 would have done。", "would not find 是现在/将来虚拟结果。", "虚拟语气"),
    ("语法", "The answer depends on ______ the word is used as a noun or a verb.", "whether", ["that", "which", "what"], "whether...or... 表示“是……还是……”。", "that 不能与 or 构成选择关系。", "名词性从句"),
    ("语法", "What matters is not ______ the word means in isolation but how it functions in context.", "what", ["that", "which", "where"], "what 引导名词性从句，并在从句中作 means 的宾语。", "that 不作成分，不能作 means 的宾语。", "名词性从句"),
    ("语法", "The sentence, if ______ literally, may lead to a wrong answer.", "translated", ["translating", "to translate", "translate"], "if translated literally 是 if it is translated literally 的省略。", "translating 会让 sentence 主动翻译，逻辑不通。", "省略结构"),
    ("语法", "The more abstract the option is, ______ it is to be wrong in a detail question.", "the more likely", ["more likely", "the likely", "likely"], "the more..., the more... 比较结构要求两边都有 the。", "more likely 缺少第二个 the，结构不完整。", "比较结构"),
    ("语用", "- I assume either A or B is correct. - ______ The blank requires a preposition, not a conjunction.", "Neither is correct.", ["Either is correct.", "Both are correct.", "So do I."], "后句指出两项词性都不合，所以应说 neither。", "Either/Both 与后句否定判断矛盾。", "语境逻辑"),
    ("语用", "- The phrase sounds natural to me. - ______ It is acceptable in speech but too informal here.", "Not exactly.", ["Exactly.", "Of course.", "Congratulations."], "后句表示部分否定和修正，Not exactly 最合适。", "Exactly 表示完全同意，和后句限定冲突。", "语气判断"),
    ("语用", "- I suppose the author's tone is neutral. - ______ The words 'unfortunately' and 'wasteful' show criticism.", "I wouldn't say so.", ["I couldn't agree more.", "That's exactly right.", "Help yourself."], "后句指出带批评意味，因此不同意“neutral”。", "I couldn't agree more 表示完全同意，与后句矛盾。", "语境逻辑"),
    ("语用", "- Can I replace 'although' with 'because' here? - ______ The two clauses show contrast.", "No, that would change the logic.", ["Yes, they are the same.", "With pleasure.", "It tastes good."], "although 表让步，because 表原因，替换会改变逻辑。", "Yes, they are the same 忽视连接词逻辑差异。", "逻辑连接"),
    ("语用", "- The option is grammatically correct. - ______ It still doesn't match the writer's attitude.", "That may be true, but", ["Therefore", "In other words", "As a result"], "前后是让步转折：语法正确但语境不合。", "Therefore/As a result 表结果，会误导逻辑关系。", "语篇衔接"),
    ("语用", "- I chose the longest option because it looked formal. - ______", "Length alone is not a reliable clue.", ["The longest option is always right.", "Formal words are never used.", "You need no context."], "选项长短不能决定答案，必须看语境和结构。", "always/never/no context 都是绝对化表达，明显不严谨。", "应试策略"),
    ("语用", "- Could 'since' mean both time and reason? - ______", "Yes, the context decides its meaning.", ["No, it only means time.", "No, it only means reason.", "It means place."], "since 可表示时间或原因，需由语境判断。", "only time/only reason 是过度绝对化。", "语境判断"),
]:
    add(5, *item)


def build_question(spec: dict, rng: random.Random) -> dict:
    options, answer = make_options(spec["correct"], spec["distractors"], rng)
    explanation = (
        f"本题考查英语运用中的「{spec['submodule']}」。正确答案为 {answer}（{spec['correct']}）。"
        f"{spec['reason']} 本题陷阱：{spec['trap']} "
        f"错因提示：{spec['error_tag']}。"
        "做这类题时，先判断题干结构和上下文关系，再检查选项的搭配、词性、语气和逻辑是否同时成立。"
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
    rng = random.Random(20260506)
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
        "# COMMON 英语运用 batch 006 难度均衡题质检",
        "",
        f"- 文件：`{OUTPUT_PATH.name}`",
        f"- 题量：{len(questions)}",
        "- 定位：按 1-5 难度均衡补充英语运用语言知识题，适合后续模拟测试和分层训练抽题。",
        "- 解析策略：延续“正确理由 + 本题陷阱 + 错因提示”的讲题式解析。",
        "",
        "## 难度分布",
        "",
    ]
    for difficulty in sorted(difficulty_counter):
        lines.append(f"- difficulty {difficulty}: {difficulty_counter[difficulty]} 题")
    lines.extend(["", "## 子模块分布", ""])
    for submodule, count in submodule_counter.most_common():
        lines.append(f"- {submodule}: {count} 题")
    lines.extend(["", "## 错因提示分布", ""])
    for tag, count in tag_counter.most_common():
        lines.append(f"- {tag}: {count} 题")
    REVIEW_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    questions = generate_questions()
    if len(questions) < 110:
        raise ValueError(f"Generated too few questions: {len(questions)}")
    OUTPUT_PATH.write_text(json.dumps({"questions": questions}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_review(questions)
    print(f"Generated {len(questions)} questions")
    print(f"Wrote {OUTPUT_PATH}")
    print(f"Wrote {REVIEW_PATH}")


if __name__ == "__main__":
    main()
