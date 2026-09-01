"""Structured teaching contract for Chinese-culture explanations.

V3 separates factual planning from learner-facing rendering.  The model emits
one auditable contract and the backend renders the existing four product
blocks.  This prevents the display copy and the review metadata from drifting
apart, while keeping the current ExplanationPanel protocol unchanged.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping
from difflib import SequenceMatcher


OPTION_LABELS = ("A", "B", "C", "D")
OPTION_FIELDS = {
    "A": "option_a",
    "B": "option_b",
    "C": "option_c",
    "D": "option_d",
}

CULTURE_V3_FORMS = {
    "direct_identification",
    "relationship_match",
    "negative_identification",
    "odd_one_out",
}

# ``question_form`` describes the direction of the question.  ``reasoning_mode``
# describes the factual bridge the learner must build, so the prompt does not
# force a person, chronology and place question through the same wording shell.
CULTURE_V3_REASONING_MODES = {
    "person_event_effect",
    "person_school_claim",
    "work_author_era",
    "concept_definition",
    "chronology",
    "place_object_mapping",
    "category_comparison",
    "quote_meaning",
    "institution_function",
    "direct_fact",
}

CULTURE_V3_MEMORY_STRATEGIES = {"none", "keyword", "contrast", "chain"}

CULTURE_V3_REQUIRED_FIELDS = {
    "version",
    "question_form",
    "reasoning_mode",
    "fact_anchor",
    "reasoning_steps",
    "evidence_excerpt",
    "knowledge_extension",
    "memory_strategy",
    "memory_hook",
    "option_analysis",
    "scope_level",
    "controversy_status",
    "verification_status",
    "difficulty_features",
}

_SELECTION_RE = re.compile(r"(?:选|选择|应选|答案(?:为|是)?)\s*[A-D](?=$|[。；，,、:“”‘’（）()\s])", re.I)
_PROCEDURAL_KNOWLEDGE_RE = re.compile(
    r"做题时|答题时|先圈|先分|再看|可?按.{0,18}(?:辨析|判断|建立对应|区分|串联)|"
    r"建立对应|掌握题干|知识点定位|回到题干|排除干扰项|要区分|需区分|常考|"
    r"建立时间线|要按"
)
_GENERIC_FACT_RE = re.compile(
    r"^(?:该项|此项|这一项|这个选项|该说法|题干对象|正确选项|错误选项|干扰项)|"
    r"(?:不符合|符合)(?:题干|本题|要求|共同限定|所列范围)|"
    r"与(?:题干|本题).{0,12}不符|属于[“\"][^”\"]{1,36}[”\"]范围"
)
_GENERIC_FIT_RE = re.compile(
    r"^(?:符合|不符合)(?:题干|本题|要求|共同限定|所列范围)[，。；]?$|"
    r"^(?:故|所以|因此)?(?:不选|排除|应选此项)[，。；]?$"
)
_GENERIC_MEMORY_RE = re.compile(
    r"^(?:记住|牢记|注意|掌握)(?:这|该|本)?(?:组)?(?:对应)?关系[。！!]?$|"
    r"^(?:先看题干|认真审题|排除干扰项)[。！!]?$"
)
_ANSWER_ECHO_BRIDGE_RE = re.compile(
    r"(?:^[^，。；;]{1,36}(?:核心对应|思想对应|实际对应|对应(?:的是|为|：|:)?|即为)"
    r"[^，。；;]{1,36}$)|(?:^[^，。；;]{1,80}构成稳定(?:的)?.{0,12}对应$)"
)
_BARE_MAPPING_PHRASE_RE = re.compile(
    r"的典型(?:艺术)?特征是|的(?:创作|生活|出现|成书)时期是|"
    r"这一(?:观点|主张|思想|说法)(?:是|属于)|主要关联(?:的历史)?时期是"
)
_ACTION_PREDICATE_RE = re.compile(
    r"带回|主持|翻译|传播|推动|促进|出使|东渡|西行|求取|改革|变法|创立|"
    r"编纂|撰写|设置|(?<!四大)发明|修建|用于|负责|沟通|演示|测报|形成|开创|奠定"
)
_SOURCE_LABEL_RE = re.compile(r"【\s*解析\s*】")
_OCR_SOURCE_SEAM_RE = re.compile(
    r"[”》）][\u3400-\u9fff]{2,10}(?:是|为|指|属于|主张|著有|提出|采用|创作)|"
    r"被称为.{0,16}徐霞客一生|"
    r"(?:思想|理论|作品|著作|时期|时代|人物|内容|成就)(?:他|她|其)"
    r"(?:用|以|主张|提出|认为|强调|倡导|创作|著有|回国|主持|传播|推动|促进|改革)"
)
_LEADING_REFERENCE_RE = re.compile(
    r"^(?:他|她|其人|此人|该人物|该书|此书|这部(?:著作|作品|典籍)|它)"
    r"(?:是|为|在|曾|又|还|由|被|用|以|主张|提出|认为|强调|著有|创作)"
)
_INCOMPLETE_CLAUSE_END_RE = re.compile(
    r"(?:名句|著作|代表作|作品|内容|包括|分为|例如|如)?(?:是|为|有|与|和|或|及|包括|分为)[：:]?$|"
    r"(?:不|未|无|并|但|而|又|及|与|和|或|、|，|,|：|:)$|"
    r"御史大$|四大楷书$|与现行公历基$|(?:时代和)?内容范围$|"
    r"前四史.*(?:后汉|三国)$|"
    r"但[^，。；]{0,12}(?:才能|能力|身份|作品)$|"
    r"一部.{0,48}的文$|它使成都平原$"
)
_REVIEW_LANGUAGE_RE = re.compile(
    r"题干已给出|[ABCD]\s*(?:项)?|其余项|事实或类别关系不同|"
    r"属于这一思想传统|主要关联这一时期|高频对应关系"
)
_UNSAFE_OPTION_FACT_RE = re.compile(
    r"不符合[“\"']|不是[“\"']|不属于[“\"']|与题干|未满足题干|无直接对应|故不选"
)
_SELF_CONTRADICTION_RE = re.compile(
    r"([\u3400-\u9fff]{2,8}).{0,40}(?:不归于|不属于|不是)\1"
)
_UNSAFE_KNOWLEDGE_RE = re.compile(
    r"记忆对象|做题|答题|先|再|按.{0,12}(?:分类|区分|辨析|记忆|建立)|"
    r"要区分|需区分|易混|常考|建立时间线|典籍文物需"
)
_SOURCE_FRAGMENT_RE = re.compile(r"[（(]\d+[）)]|^(?:乃|且|而|但)(?=[\u3400-\u9fff])")
_KNOWLEDGE_FRAGMENT_RE = re.compile(r"^[\u3400-\u9fff]{4,14}(?:、[\u3400-\u9fff]{2,8})*为代表(?:$|[；;])")
_TAUTOLOGY_FACT_RE = re.compile(r"^(.{2,14})(?:归属|属于|指)\1$")
_TIME_QUESTION_RE = re.compile(r"时期|时代|朝代|年代|何时|何代|成书于|出现于|生活于|创作于")
_TIME_LINK_RE = re.compile(
    r"出现|成书|形成|始建|建于|创作|生活|活动|制定|编纂|编成|流行|兴盛|盛行|"
    r"始于|终于|时人|年间|时期|时代|朝代|(?:是|为).{0,12}(?:人|家|作品|著作|制度|器物)"
)
_RELATIVE_TIME_STEM_RE = re.compile(r"去世后|之后|以后|此前|之前|早于|晚于|同时代")
_RELATIVE_TIME_FACT_RE = re.compile(r"生于|卒于|去世|在世|生卒|早于|晚于|同时代|先于|后于")
_TEMPLATE_BRIDGE_RE = re.compile(r"这是.{0,30}的相关思想主张|代表性思想主张[—:：]")
_FACT_RISK_RE = re.compile(
    r"吴道子是中国山水画的祖师|韩非子等.{0,12}均被称为[“\"]?前期法家|"
    r"世界上最早的天文学著作|古代经验科学出现的标志|由班固于东汉中元元年|"
    r"苏轼也对柳永持贬斥态度|(?:世界|中国|我国)(?:上)?最(?:早|古老|大)|"
    r"《春秋》.{0,24}(?:三十五卷|十三经.{0,8}最长)|"
    r"经世致用一词由.{0,32}提出|(?:都江堰.{0,32}鳖灵|鳖灵.{0,32}都江堰)"
)
_WRONG_FIT_CONNECTOR_RE = re.compile(r"不|无关|并非|而非|属于|对应|混淆|时代|人物|作品|对象|少|多|早|晚|题干")
_RIGHT_FIT_CONNECTOR_RE = re.compile(r"直接|符合|对应|正是|因此|所以|说明|题干|关系最密切")
_GENERIC_ANSWER_RE = re.compile(
    r"^(?:古代|近代|现代|当代|先秦|春秋|战国|秦代|汉代|西汉|东汉|魏晋|南北朝|"
    r"隋代|唐代|宋代|北宋|南宋|元代|明代|清代|儒家|道家|墨家|法家|名家|"
    r"阴阳家|纵横家|杂家|佛教|道教|.+(?:时期|时代|朝代|领域|工程|技术|制度|"
    r"学派|文体|书体|乐器|著作|作品|人物|方法|用途))$"
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _normalized(value: object) -> str:
    return re.sub(r"[^0-9a-z\u3400-\u9fff]+", "", _text(value).lower())


def _display_normalized(value: object) -> str:
    return re.sub(r"[ \t]+", "", _text(value).replace("\r\n", "\n").replace("\r", "\n"))


def _similar(left: object, right: object) -> float:
    a = _normalized(left)
    b = _normalized(right)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _cjk_bigrams(value: object) -> set[str]:
    text = re.sub(r"[^\u3400-\u9fff]", "", _text(value))
    return {text[index : index + 2] for index in range(max(0, len(text) - 1))}


def _anchor_residual(value: object, subject: object, answer: object) -> str:
    text = _normalized(value)
    for removable in sorted({_normalized(subject), _normalized(answer)}, key=len, reverse=True):
        if removable:
            text = text.replace(removable, "")
    relations = (
        "的典型艺术特征是",
        "的典型特征是",
        "这一观点是",
        "这一主张是",
        "这一思想是",
        "这一说法是",
        "对应的是",
        "主要关联",
        "创作时期",
        "生活时期",
        "出现时期",
        "成书时期",
        "对应",
        "属于",
        "时期",
        "时代",
        "朝代",
        "学派",
        "观点",
        "主张",
        "思想",
        "特征",
        "典型",
        "指",
        "是",
        "为",
        "的",
    )
    for relation in sorted(relations, key=len, reverse=True):
        text = text.replace(_normalized(relation), "")
    return text


def _fact_names_option(fact: object, option: object) -> bool:
    fact_key = _normalized(fact)
    option_key = _normalized(option)
    if not fact_key or not option_key:
        return False
    if option_key in fact_key:
        return True
    option_bigrams = _cjk_bigrams(option)
    if len(option_bigrams) < 2:
        return False
    return len(option_bigrams & _cjk_bigrams(fact)) / len(option_bigrams) >= 0.45


def _knowledge_is_grounded(value: object, subject: object, answer: object) -> bool:
    knowledge_key = _normalized(value)
    subject_key = _normalized(subject)
    answer_key = _normalized(answer)
    if not knowledge_key:
        return False
    if subject_key and subject_key in knowledge_key:
        return True
    if subject_key and len(subject_key) <= 8:
        match = SequenceMatcher(None, subject_key, knowledge_key).find_longest_match(
            0,
            len(subject_key),
            0,
            len(knowledge_key),
        )
        if match.size >= 2:
            return True
    return bool(
        answer_key
        and not _GENERIC_ANSWER_RE.fullmatch(answer_key)
        and answer_key in knowledge_key
    )


def _fit_template_family(value: object) -> str:
    text = _text(value)
    if re.search(r"说明的是“[^”]+”，不是“[^”]+”", text):
        return "explains_not_topic"
    if re.search(r"这个时代对应.+，不是.+", text):
        return "era_corresponds_not_topic"
    if re.search(r"其.+与“[^”]+”不同", text):
        return "relation_differs"
    if re.search(r"对象或关系不同|对象不同，不是", text):
        return "generic_object_mismatch"
    return ""


def _enumeration_incomplete(value: object) -> bool:
    text = _text(value)
    match = re.search(r"([二三四五六七八九十两]|\d+)大.{0,12}?分别为(.+)$", text)
    if not match:
        return False
    counts = {"两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    expected = counts.get(match.group(1), int(match.group(1)) if match.group(1).isdigit() else 0)
    actual = len([item for item in re.split(r"[、，,；;和及]", match.group(2)) if _text(item)])
    return bool(expected and actual < expected)


def _sentence(value: object) -> str:
    text = _text(value).rstrip("。！？!?；; ")
    return f"{text}。" if text else ""


def _clause(value: object) -> str:
    return _text(value).rstrip("。！？!?；;，, ")


def _issue(code: str, message: str, severity: str = "high") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def is_culture_v3_metadata(metadata: object) -> bool:
    return isinstance(metadata, Mapping) and _text(metadata.get("version")).startswith("3.")


def infer_culture_reasoning_mode(question: Mapping[str, object]) -> str:
    """Route common culture questions to a fact-specific reasoning pattern."""

    stem = _text(question.get("stem"))
    if re.search(r"先后|顺序|排序|最早|最晚|早于|晚于|年代|时期排列|去世后|之后|以前|此前", stem):
        return "chronology"
    if re.search(r"位于|所在地|哪一地区|哪座城市|发源地|地理位置|今天的", stem):
        return "place_object_mapping"
    if re.search(r"含义|释义|解释|指的是|概念是|定义|何谓", stem):
        return "concept_definition"
    if re.search(r"诗句|哪句诗|名句|句意|意象|表达了|体现了|描写的是", stem):
        return "quote_meaning"
    if re.search(r"共同点|不同的是|不属于|哪一类|门类|分类|归类|哪一项不同", stem):
        return "category_comparison"
    if re.search(r"制度|选官|科举|职能|功能|作用|用途|用于", stem):
        return "institution_function"
    if re.search(r"作者|曲作者|创作者|撰写|著有|代表作|出自|典籍.*关系|作品.*关系", stem):
        return "work_author_era"
    if re.search(r"取经|东渡|出使|变法|改革|事迹|贡献|影响|推动|促进", stem):
        return "person_event_effect"
    if re.search(r"学派|思想传统|思想家|主张|命题|学说|流派|代表人物", stem):
        return "person_school_claim"
    return "direct_fact"


def culture_v3_display_budget(question: Mapping[str, object], metadata: Mapping[str, object]) -> int:
    """Return a form-aware upper bound instead of one fixed explanation size."""

    form = _text(metadata.get("question_form"))
    base = {
        "direct_identification": 340,
        "relationship_match": 360,
        "negative_identification": 405,
        "odd_one_out": 420,
    }.get(form, 360)
    try:
        difficulty = int(question.get("difficulty") or 3)
    except (TypeError, ValueError):
        difficulty = 3
    if difficulty >= 4:
        base += 10
    return min(base, 430)


def render_culture_explanation_v3(
    question: Mapping[str, object],
    metadata: Mapping[str, object],
) -> str:
    """Render the current ExplanationPanel labels from a V3 teaching contract."""

    steps = metadata.get("reasoning_steps")
    analyses = metadata.get("option_analysis")
    if not isinstance(steps, Mapping) or not isinstance(analyses, Mapping):
        raise ValueError("culture_v3 缺少 reasoning_steps 或 option_analysis")

    clue = _clause(steps.get("clue"))
    bridge = _clause(steps.get("bridge"))
    conclusion = _clause(steps.get("conclusion"))
    if not all((clue, bridge, conclusion)):
        raise ValueError("culture_v3.reasoning_steps 必须包含 clue、bridge、conclusion")

    answer = _text(question.get("answer")).upper()
    lines = ["解题思路：", f"{clue}→{bridge}→{_sentence(conclusion)}", "", "选项解析："]
    for label in OPTION_LABELS:
        item = analyses.get(label)
        if not isinstance(item, Mapping):
            raise ValueError(f"culture_v3.option_analysis 缺少 {label}")
        fact = _clause(item.get("fact"))
        fit = _clause(item.get("fit"))
        if not fact or not fit:
            raise ValueError(f"culture_v3.option_analysis.{label} 缺少 fact 或 fit")
        option = _text(question.get(OPTION_FIELDS[label]))
        option_prefix = f"{option}：" if option and len(option) <= 22 and _normalized(option) not in _normalized(fact) else ""
        mark = "✓" if label == answer else "×"
        lines.append(f"{label}. {mark} {_sentence(f'{option_prefix}{fact}；{fit}')}")

    lines.extend(["", "知识点：", _sentence(metadata.get("knowledge_extension"))])
    memory_hook = _text(metadata.get("memory_hook"))
    if memory_hook:
        lines.extend(["", "记忆方法：", _sentence(memory_hook)])
    return "\n".join(lines)


def validate_culture_v3_contract(
    question: Mapping[str, object],
    metadata: object,
) -> list[dict[str, str]]:
    """Validate teaching semantics that cannot be guaranteed by display labels."""

    if not isinstance(metadata, Mapping):
        return [_issue("missing_culture_v3_metadata", "中华文化 V3 必须提供 culture_v3 对象", "critical")]

    issues: list[dict[str, str]] = []
    missing = sorted(field for field in CULTURE_V3_REQUIRED_FIELDS if field not in metadata)
    if missing:
        issues.append(
            _issue(
                "incomplete_culture_v3_metadata",
                f"culture_v3 缺少字段：{'、'.join(missing)}",
                "critical",
            )
        )

    if _text(metadata.get("version")) != "3.0":
        issues.append(_issue("invalid_culture_v3_version", "culture_v3.version 必须为 3.0"))

    stem = _text(question.get("stem"))
    answer = _text(question.get("answer")).upper()
    options = {label: _text(question.get(field)) for label, field in OPTION_FIELDS.items()}
    correct_option = options.get(answer, "")

    question_form = _text(metadata.get("question_form"))
    if question_form not in CULTURE_V3_FORMS:
        issues.append(_issue("invalid_culture_v3_question_form", "culture_v3.question_form 不在允许范围内"))
    stem_for_direction = re.sub(
        r"无一不是|没有一个不是|莫不(?:是)?",
        "均是",
        _text(question.get("stem")),
    )
    negative_stem = bool(
        re.search(
            r"不正确|不属于|不包括|并非|不是|错误(?:的是|项)?|有误(?:的是)?|不当(?:的是)?|"
            r"不同的是|不相同|不能说明|不应|不宜|需排除|排除对象|例外|不在(?:该|此|本|名单|范围)",
            stem_for_direction,
        )
    )
    if negative_stem != (question_form in {"negative_identification", "odd_one_out"}):
        issues.append(_issue("culture_v3_question_form_mismatch", "question_form 与题干正向或逆向设问不一致"))
    reasoning_mode = _text(metadata.get("reasoning_mode"))
    if reasoning_mode not in CULTURE_V3_REASONING_MODES:
        issues.append(_issue("invalid_culture_v3_reasoning_mode", "culture_v3.reasoning_mode 不在允许范围内"))
    else:
        expected_mode = infer_culture_reasoning_mode(question)
        if expected_mode != "direct_fact" and reasoning_mode != expected_mode:
            issues.append(
                _issue(
                    "culture_v3_reasoning_mode_mismatch",
                    f"题干应使用 {expected_mode} 推理路径，而不是 {reasoning_mode}",
                )
            )

    if _text(metadata.get("scope_level")) != "core":
        issues.append(_issue("culture_v3_scope_not_core", "只接收核心、稳定的普通文化常识"))
    if _text(metadata.get("controversy_status")) != "stable":
        issues.append(_issue("culture_v3_fact_not_stable", "争议性或考据型事实应进入人工复核"))
    if _text(metadata.get("verification_status")) != "cross_checked":
        issues.append(_issue("culture_v3_not_cross_checked", "culture_v3.verification_status 必须为 cross_checked"))

    anchor = metadata.get("fact_anchor")
    if not isinstance(anchor, Mapping) or any(not _text(anchor.get(key)) for key in ("subject", "relation", "object")):
        issues.append(_issue("invalid_culture_v3_fact_anchor", "fact_anchor 必须明确对象、关系和值", "critical"))
    elif correct_option and not (
        _normalized(correct_option) in _normalized(anchor.get("object"))
        or _normalized(anchor.get("object")) in _normalized(correct_option)
    ):
        issues.append(_issue("culture_v3_fact_anchor_answer_mismatch", "fact_anchor.object 必须落到正确选项原文"))

    evidence = _text(metadata.get("evidence_excerpt"))
    if len(evidence) < 8 or _GENERIC_FACT_RE.search(evidence):
        issues.append(_issue("weak_culture_v3_evidence", "evidence_excerpt 必须是可核对的具体文化事实"))
    if (
        _LEADING_REFERENCE_RE.search(evidence)
        or _OCR_SOURCE_SEAM_RE.search(evidence)
        or _INCOMPLETE_CLAUSE_END_RE.search(evidence)
        or _FACT_RISK_RE.search(evidence)
        or re.search(r"(?:谁|哪位|哪个|什么|如何|多少).{0,18}[？?]", evidence)
    ):
        issues.append(_issue("culture_v3_evidence_requires_review", "evidence_excerpt 含指代不明、残句或需复核事实"))

    steps = metadata.get("reasoning_steps")
    if not isinstance(steps, Mapping):
        issues.append(_issue("invalid_culture_v3_reasoning_steps", "reasoning_steps 必须包含 clue、bridge、conclusion", "critical"))
        clue = bridge = conclusion = ""
    else:
        clue = _text(steps.get("clue"))
        bridge = _text(steps.get("bridge"))
        conclusion = _text(steps.get("conclusion"))
        event_bridge = bridge
        for removable in (
            _text(anchor.get("subject")) if isinstance(anchor, Mapping) else "",
            correct_option,
        ):
            if removable:
                event_bridge = event_bridge.replace(removable, "")
        if len(clue) < 3 or len(bridge) < 8 or len(conclusion) < 6:
            issues.append(_issue("culture_v3_reasoning_steps_too_shallow", "推理必须包含简短线索、具体中间事实和答案结论"))
        if stem and (_normalized(clue) == _normalized(stem) or _similar(clue, stem) >= 0.94):
            issues.append(_issue("culture_v3_clue_repeats_stem", "clue 应提取关键线索，不得整句复述题干"))
        if stem and clue and not (_cjk_bigrams(stem) & _cjk_bigrams(clue)):
            issues.append(_issue("culture_v3_clue_not_grounded", "clue 必须能在题干中找到依据"))
        if _SELECTION_RE.search(clue) or _SELECTION_RE.search(bridge):
            issues.append(_issue("culture_v3_answer_leaks_before_conclusion", "选择结论只能出现在 conclusion"))
        if (
            _GENERIC_FACT_RE.search(bridge)
            or _ANSWER_ECHO_BRIDGE_RE.fullmatch(bridge)
            or _TEMPLATE_BRIDGE_RE.search(bridge)
            or _normalized(bridge) in {_normalized(clue), _normalized(correct_option)}
            or (
                isinstance(anchor, Mapping)
                and len(_anchor_residual(bridge, anchor.get("subject"), anchor.get("object"))) < 8
            )
            or (reasoning_mode == "person_event_effect" and len(_ACTION_PREDICATE_RE.findall(event_bridge)) < 2)
        ):
            issues.append(_issue("culture_v3_bridge_is_answer_echo", "bridge 必须补出中间事实，不得只做答案对应"))
        if _BARE_MAPPING_PHRASE_RE.search(bridge):
            issues.append(_issue("culture_v3_bridge_uses_bare_mapping", "bridge 使用特征或时期套话改写答案，缺少中间事实"))
        if _LEADING_REFERENCE_RE.search(bridge):
            issues.append(_issue("culture_v3_bridge_dangling_reference", "bridge 以他、该书等无指代对象开头"))
        if _SOURCE_LABEL_RE.search(bridge):
            issues.append(_issue("culture_v3_bridge_contains_source_label", "bridge 不得保留资料解析标签"))
        if _OCR_SOURCE_SEAM_RE.search(bridge):
            issues.append(_issue("culture_v3_bridge_source_merge", "bridge 疑似拼接了两个未分隔的资料事实"))
        if re.search(r"(?:谁|哪位|哪个|什么|如何|多少).{0,14}[？?]", bridge):
            issues.append(_issue("culture_v3_bridge_is_source_question", "bridge 不得保留资料中的问句"))
        if _FACT_RISK_RE.search(bridge):
            issues.append(_issue("culture_v3_bridge_fact_requires_review", "bridge 含有需复核的争议或错配事实"))
        if _INCOMPLETE_CLAUSE_END_RE.search(bridge):
            issues.append(_issue("culture_v3_bridge_incomplete", "bridge 句尾残缺，缺少完整文化事实"))
        if _REVIEW_LANGUAGE_RE.search(bridge):
            issues.append(_issue("culture_v3_bridge_contains_review_language", "bridge 不得保留选项字母或审核模板语言"))
        if _PROCEDURAL_KNOWLEDGE_RE.search(bridge) or _UNSAFE_KNOWLEDGE_RE.search(bridge):
            issues.append(_issue("culture_v3_bridge_contains_procedure", "bridge 不得包含常考、辨析等做题提示"))
        if not negative_stem and re.search(
            r"核对|不是|不在|不属于|不归于|不符合|不正确|错误|有误|未满足题干",
            bridge,
        ):
            issues.append(
                _issue(
                    "culture_v3_positive_bridge_uses_exclusion",
                    "正向题 bridge 应直接证明答案，不得依赖排除型背景",
                )
            )
        if _TIME_QUESTION_RE.search(stem) and not _TIME_LINK_RE.search(bridge):
            issues.append(_issue("culture_v3_bridge_lacks_time_link", "时代题 bridge 必须说明出现、成书、生活或形成时间"))
        if _TIME_QUESTION_RE.search(stem) and _normalized(correct_option) == "古代":
            issues.append(_issue("culture_v3_time_answer_too_broad", "时代题答案仅写古代，时间边界过宽，应进入复核"))
        if _RELATIVE_TIME_STEM_RE.search(stem) and not _RELATIVE_TIME_FACT_RE.search(bridge):
            issues.append(_issue("culture_v3_bridge_lacks_relative_time_proof", "先后关系题必须给出生卒或前后关系证据"))
        if bridge and conclusion and _similar(bridge, conclusion) >= 0.88:
            issues.append(_issue("culture_v3_bridge_duplicates_conclusion", "中间事实与答案结论不得重复"))
        names_answer = bool(
            answer
            and (
                re.search(rf"(?:选|选择|应选)\s*{re.escape(answer)}(?=$|[。；，,、:“”‘’（）()\s])", conclusion, re.I)
                or (correct_option and _normalized(correct_option) in _normalized(conclusion))
            )
        )
        if not names_answer:
            issues.append(_issue("culture_v3_conclusion_missing_answer", "conclusion 必须落到正确选项或选项原文"))

    knowledge = _text(metadata.get("knowledge_extension"))
    if len(knowledge) < 10:
        issues.append(_issue("weak_culture_v3_knowledge", "knowledge_extension 必须提供独立、可复习的事实"))
    if (
        _SELECTION_RE.search(knowledge)
        or _PROCEDURAL_KNOWLEDGE_RE.search(knowledge)
        or _REVIEW_LANGUAGE_RE.search(knowledge)
        or _UNSAFE_KNOWLEDGE_RE.search(knowledge)
        or _SOURCE_FRAGMENT_RE.search(knowledge)
        or _KNOWLEDGE_FRAGMENT_RE.search(knowledge)
        or _FACT_RISK_RE.search(knowledge)
    ):
        issues.append(_issue("culture_v3_knowledge_role_mismatch", "知识点只能扩展文化事实，不得写选项结论或通用做题步骤"))
    if _SELF_CONTRADICTION_RE.search(knowledge):
        issues.append(_issue("culture_v3_knowledge_self_contradiction", "知识点内部出现同一对象的自相矛盾表述"))
    if _INCOMPLETE_CLAUSE_END_RE.search(knowledge):
        issues.append(_issue("culture_v3_knowledge_incomplete", "知识点句尾残缺，需补全事实"))
    if _LEADING_REFERENCE_RE.search(knowledge):
        issues.append(_issue("culture_v3_knowledge_dangling_reference", "知识点以无明确对象的代词开头"))
    if _OCR_SOURCE_SEAM_RE.search(knowledge):
        issues.append(_issue("culture_v3_knowledge_source_merge", "知识点疑似粘连了两个资料事实"))
    if re.search(r"(?:谁|哪位|哪个|什么|如何|多少).{0,18}[？?]", knowledge):
        issues.append(_issue("culture_v3_knowledge_is_source_question", "知识点不得保留资料问句"))
    if _enumeration_incomplete(knowledge):
        issues.append(_issue("culture_v3_knowledge_incomplete_enumeration", "知识点列举数量与内容不完整"))
    if knowledge and stem and _similar(knowledge, stem) >= 0.78:
        issues.append(_issue("culture_v3_knowledge_repeats_stem", "知识点不得改写题干或重复本题答案"))
    if isinstance(anchor, Mapping) and bridge and knowledge:
        anchor_subject = anchor.get("subject")
        anchor_answer = anchor.get("object")
        bridge_key = _normalized(bridge)
        knowledge_key = _normalized(knowledge)
        if (
            _normalized(anchor_subject)
            and _normalized(anchor_answer)
            and _normalized(anchor_subject) in bridge_key
            and _normalized(anchor_answer) in bridge_key
            and _normalized(anchor_subject) in knowledge_key
            and _normalized(anchor_answer) in knowledge_key
            and len(_anchor_residual(knowledge, anchor_subject, anchor_answer)) < 8
        ):
            issues.append(_issue("culture_v3_knowledge_repeats_answer_mapping", "知识点不得再次复述题目对象与答案的对应"))
        if not _knowledge_is_grounded(knowledge, anchor_subject, anchor_answer):
            issues.append(_issue("culture_v3_knowledge_not_grounded", "知识点必须围绕本题对象或正确知识继续扩展"))
    if knowledge and bridge and (
        _normalized(knowledge) in _normalized(bridge)
        or _normalized(bridge) in _normalized(knowledge)
        or _similar(knowledge, bridge) >= 0.82
    ):
        issues.append(_issue("culture_v3_knowledge_duplicates_reasoning", "知识点与中间推理事实重复，应补充独立考试知识"))

    memory_strategy = _text(metadata.get("memory_strategy"))
    memory_hook = _text(metadata.get("memory_hook"))
    if memory_strategy not in CULTURE_V3_MEMORY_STRATEGIES:
        issues.append(_issue("invalid_culture_v3_memory_strategy", "memory_strategy 只能为 none、keyword、contrast 或 chain"))
    elif memory_strategy == "none":
        if memory_hook:
            issues.append(_issue("culture_v3_memory_none_has_copy", "memory_strategy 为 none 时 memory_hook 应为空"))
    else:
        if len(memory_hook) < 8 or _GENERIC_MEMORY_RE.search(memory_hook):
            issues.append(_issue("weak_culture_v3_memory_hook", "记忆方法必须是可复用的关键词、对比组或知识链"))
        if memory_hook and knowledge and _similar(memory_hook, knowledge) >= 0.86:
            issues.append(_issue("culture_v3_memory_duplicates_knowledge", "记忆方法不得复述知识点"))

    analyses = metadata.get("option_analysis")
    if not isinstance(analyses, Mapping):
        issues.append(_issue("invalid_culture_v3_option_analysis", "option_analysis 必须逐项覆盖 A-D", "critical"))
    else:
        missing_options = [label for label in OPTION_LABELS if not isinstance(analyses.get(label), Mapping)]
        if missing_options:
            issues.append(_issue("incomplete_culture_v3_option_analysis", f"option_analysis 缺少：{'、'.join(missing_options)}", "critical"))
        rendered_reasons: list[str] = []
        option_facts: list[str] = []
        wrong_fit_families: list[str] = []
        for label in OPTION_LABELS:
            item = analyses.get(label)
            if not isinstance(item, Mapping):
                continue
            verdict = _text(item.get("verdict"))
            expected = "correct" if label == answer else "incorrect"
            if verdict != expected:
                issues.append(_issue("culture_v3_option_verdict_mismatch", f"option_analysis.{label}.verdict 应为 {expected}"))
            fact = _text(item.get("fact"))
            fit = _text(item.get("fit"))
            if (
                len(fact) < 7
                or _GENERIC_FACT_RE.search(fact)
                or _UNSAFE_OPTION_FACT_RE.search(fact)
                or _INCOMPLETE_CLAUSE_END_RE.search(fact)
                or _TAUTOLOGY_FACT_RE.fullmatch(fact)
                or _LEADING_REFERENCE_RE.search(fact)
                or _OCR_SOURCE_SEAM_RE.search(fact)
                or _FACT_RISK_RE.search(fact)
                or _REVIEW_LANGUAGE_RE.search(fact)
            ):
                issues.append(_issue("culture_v3_option_fact_weak", f"选项 {label} 必须说明具体知识事实"))
            if options.get(label) and _normalized(fact) == _normalized(options[label]):
                issues.append(_issue("culture_v3_option_fact_repeats_option", f"选项 {label} 的 fact 只是复述选项原文"))
            if options.get(label) and not _fact_names_option(fact, options[label]):
                code = (
                    "culture_v3_correct_option_fact_missing_answer"
                    if label == answer
                    else "culture_v3_wrong_option_fact_missing_object"
                )
                issues.append(_issue(code, f"选项 {label} 的事实没有保留该选项的知识对象"))
            if len(fit) < 5 or _GENERIC_FIT_RE.search(fit):
                issues.append(_issue("culture_v3_option_fit_weak", f"选项 {label} 必须说明该事实为何符合或不符合本题"))
            elif label == answer and not _RIGHT_FIT_CONNECTOR_RE.search(fit):
                issues.append(_issue("culture_v3_correct_option_fit_unclear", f"选项 {label} 未说明与题干的直接关系"))
            elif label != answer and not _WRONG_FIT_CONNECTOR_RE.search(fit):
                issues.append(_issue("culture_v3_wrong_option_mismatch_unclear", f"选项 {label} 未说明错配边界"))
            if len(fact) > 72 or len(fit) > 58:
                issues.append(_issue("culture_v3_option_analysis_too_long", f"选项 {label} 的辨析过长，应保留一个事实和一个错配边界"))
            rendered_reasons.append(f"{_normalized(fact)}|{_normalized(fit)}")
            option_facts.append(fact)
            if label != answer:
                family = _fit_template_family(fit)
                if family:
                    wrong_fit_families.append(family)
        if len(rendered_reasons) != len(set(rendered_reasons)):
            issues.append(_issue("culture_v3_option_analysis_repeated", "A-D 选项解析不得复制同一句模板"))
        if question_form not in {"negative_identification", "odd_one_out"} and any(
            count >= 3 for count in Counter(wrong_fit_families).values()
        ):
            issues.append(_issue("culture_v3_option_fit_template_repeated", "三个错项不得反复套用同一种判断句式"))
        if knowledge and any(
            len(_normalized(fact)) >= 7
            and (
                _normalized(fact) in _normalized(knowledge)
                or _normalized(knowledge) in _normalized(fact)
                or _similar(fact, knowledge) >= 0.86
            )
            for fact in option_facts
        ):
            issues.append(_issue("culture_v3_knowledge_duplicates_option_fact", "知识点不得复制选项解析中的事实"))

    try:
        rendered = render_culture_explanation_v3(question, metadata)
    except ValueError as exc:
        issues.append(_issue("culture_v3_render_failed", str(exc), "critical"))
    else:
        explanation = _text(question.get("explanation"))
        if explanation and _display_normalized(explanation) != _display_normalized(rendered):
            issues.append(_issue("culture_v3_explanation_not_canonical", "展示解析必须由 culture_v3 字段统一渲染，不得另写一套内容"))
        budget = culture_v3_display_budget(question, metadata)
        if len(rendered) > budget:
            issues.append(_issue("culture_v3_explanation_over_budget", f"当前题型解析为 {len(rendered)} 字符，超过动态上限 {budget}"))

    return issues
