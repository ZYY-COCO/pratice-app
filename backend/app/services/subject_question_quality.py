"""Deterministic quality gates for non-logic AI generated questions.

The model's metadata is treated as an auditable contract, not as proof.  Culture
and English candidates still need a blind second-model review in the online
route.  Math candidates additionally need a locally executable verification
spec that agrees with the declared answer.
"""

from __future__ import annotations

import ast
import math
import re
from collections.abc import Mapping

from app.services.culture_explanation_v3 import (
    CULTURE_V3_REQUIRED_FIELDS,
    culture_v3_display_budget,
    is_culture_v3_metadata,
    validate_culture_v3_contract,
)


CULTURE_SUBJECT = "中华文化"
ENGLISH_SUBJECT = "英语运用"
MATH_SUBJECT = "数学基础"
V2_SUBJECTS = {CULTURE_SUBJECT, ENGLISH_SUBJECT, MATH_SUBJECT}

OPTION_LABELS = ("A", "B", "C", "D")
OPTION_FIELDS = {
    "A": "option_a",
    "B": "option_b",
    "C": "option_c",
    "D": "option_d",
}

CULTURE_FORMS = {
    "direct_identification",
    "relationship_match",
    "negative_identification",
    "odd_one_out",
}
CULTURE_EXPLANATION_MAX_CHARS = 420
# V2 uses learner-facing labels that map directly to the product card.  The
# first tuple entry is always the preferred/new label; legacy labels remain
# accepted so existing questions can be read during the migration window.
CULTURE_EXPLANATION_LABELS = {
    "why": ("解题思路", "为什么"),
    "distractors": ("选项解析", "易混辨析", "选项辨析"),
    "knowledge": ("知识点", "关键知识"),
    "memory": ("记忆方法", "记忆提醒", "记忆提示", "做题提醒"),
}
CULTURE_EXPLANATION_LABEL_TO_KEY = {
    label: key for key, labels in CULTURE_EXPLANATION_LABELS.items() for label in labels
}
CULTURE_EXPLANATION_NEW_LABELS = {
    labels[0] for labels in CULTURE_EXPLANATION_LABELS.values()
}
CULTURE_EXPLANATION_BLOCK_LIMITS = {
    "why": (8, 140),
    "knowledge": (8, 120),
    "distractors": (0, 320),
    "memory": (6, 80),
}
CULTURE_MECHANICAL_PHRASES = (
    "题干对象",
    "核心对应",
    "实际对应",
    "该项对应",
    "可保留：",
    "题目给出的正确答案",
    "句中空缺应填",
)
CULTURE_REASONING_CONNECTOR_RE = re.compile(
    r"→|因为|由于|因此|所以|从而|说明|表明|体现|源于|属于|对应|提出|创作|主持|用于|形成|导致|先.+再"
)
ENGLISH_SKILLS = {
    "词汇": "vocabulary",
    "语法": "grammar",
    "语用": "pragmatics",
}
MATH_VERIFICATION_KINDS = {
    "numeric_expression",
    "derivative_value",
    "partial_derivative_value",
    "definite_integral",
    "limit_value",
    "antiderivative_choice",
    "expression_choice",
}
MATH_SUBMODULE_VERIFICATION_KINDS = {
    "极限": {"limit_value"},
    "连续": {"limit_value", "numeric_expression", "expression_choice"},
    "导数": {"derivative_value", "expression_choice"},
    "微分": {"derivative_value", "expression_choice"},
    "高阶导数": {"derivative_value", "expression_choice"},
    "洛必达法则": {"limit_value"},
    "单调性": {"numeric_expression", "expression_choice"},
    "极值与最值": {"numeric_expression", "expression_choice"},
    "凹凸性": {"expression_choice"},
    "拐点": {"numeric_expression", "expression_choice"},
    "渐近线": {"limit_value", "numeric_expression", "expression_choice"},
    "原函数": {"antiderivative_choice"},
    "定积分": {"definite_integral", "numeric_expression", "expression_choice"},
    "变限定积分": {"definite_integral", "derivative_value", "expression_choice"},
    "牛顿-莱布尼兹公式": {"definite_integral", "numeric_expression", "expression_choice"},
    "换元积分": {"definite_integral", "antiderivative_choice", "expression_choice"},
    "分部积分": {"definite_integral", "antiderivative_choice", "expression_choice"},
    "几何应用": {"definite_integral", "numeric_expression"},
    "物理应用": {"definite_integral", "numeric_expression"},
    "偏导数": {"partial_derivative_value", "expression_choice"},
    "全微分": {"partial_derivative_value", "expression_choice"},
    "二阶偏导": {"partial_derivative_value", "expression_choice"},
    "链导法则": {"derivative_value", "partial_derivative_value", "expression_choice"},
    "隐函数求导": {"derivative_value", "partial_derivative_value", "expression_choice"},
    "二元函数极值": {"numeric_expression", "partial_derivative_value", "expression_choice"},
}

META_PHRASES = (
    "题干若考察",
    "依据中华文化考纲",
    "知识点归类",
    "最准确的知识点归类",
    "下列归类最准确",
    "考查知识点",
    "考察知识点",
    "本题由ai",
    "ai生成",
    "生成题",
    "命题过程",
    "复盘报告",
    "学习报告",
    "测评记录",
    "讲义来源",
)
CULTURE_MEDIA_PHRASES = (
    "根据材料",
    "阅读材料",
    "如下图",
    "观察图片",
    "观看视频",
)
ENGLISH_OUT_OF_SCOPE_PHRASES = (
    "according to the passage",
    "read the passage",
    "write an essay",
    "translate the following",
    "reading comprehension",
    "cloze test",
)
MATH_BANNED_PATTERNS = (
    "线性代数",
    "矩阵",
    "行列式",
    "概率",
    "数理统计",
    "无穷级数",
    "幂级数",
    "常微分方程",
    "二重积分",
    "三重积分",
    "曲线积分",
    "曲面积分",
    "空间解析几何",
    "证明题",
    "请证明",
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _normalized(value: object) -> str:
    text = _text(value).lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[“”\"'`，。；：！？、,.!?;:]", "", text)
    return text


def _normalized_english(value: object) -> str:
    text = _text(value).lower().replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", text).strip()


def _has_chinese(value: object) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", _text(value)))


def _has_latin(value: object) -> bool:
    return bool(re.search(r"[A-Za-z]", _text(value)))


def _issue(code: str, severity: str, message: str, action: str = "reject") -> dict[str, str]:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "action": action,
    }


def _options(question: Mapping[str, object]) -> dict[str, str]:
    return {label: _text(question.get(field)) for label, field in OPTION_FIELDS.items()}


def _wrong_labels(answer: str) -> set[str]:
    return set(OPTION_LABELS) - {answer}


def _finalize(subject: str, issues: list[dict[str, str]], **extra: object) -> dict:
    blocking = [item for item in issues if item["severity"] in {"critical", "high"}]
    return {
        "subject": subject,
        "valid_for_generation": not blocking,
        "issues": issues,
        "blocking_codes": [item["code"] for item in blocking],
        **extra,
    }


def _common_issues(question: Mapping[str, object], expected_subject: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if _text(question.get("subject")) != expected_subject:
        issues.append(_issue("subject_mismatch", "critical", f"subject 必须为 {expected_subject}"))
    if _text(question.get("question_type")) != "single_choice":
        issues.append(_issue("invalid_question_type", "critical", "question_type 必须为 single_choice"))

    answer = _text(question.get("answer")).upper()
    if answer not in OPTION_LABELS:
        issues.append(_issue("invalid_answer", "critical", "answer 必须为 A、B、C、D 之一"))

    options = _options(question)
    if any(not value for value in options.values()):
        issues.append(_issue("blank_option", "critical", "A-D 四个选项都必须非空"))
    normalized_options = [_normalized(value) for value in options.values()]
    if all(normalized_options) and len(set(normalized_options)) != 4:
        issues.append(_issue("duplicate_options", "critical", "A-D 选项不得重复或仅有标点差异"))

    if not _text(question.get("stem")):
        issues.append(_issue("blank_stem", "critical", "题干不得为空"))
    if not _text(question.get("explanation")):
        issues.append(_issue("blank_explanation", "critical", "解析不得为空"))

    difficulty = question.get("difficulty")
    if not isinstance(difficulty, int) or isinstance(difficulty, bool) or not 1 <= difficulty <= 5:
        issues.append(_issue("invalid_difficulty", "critical", "difficulty 必须为 1-5 的整数"))
    return issues


def _metadata_issues(
    metadata: object,
    required_fields: set[str],
    metadata_name: str,
    require_v2_metadata: bool,
    expected_version: str = "2.0",
) -> tuple[dict, list[dict[str, str]]]:
    issues: list[dict[str, str]] = []
    if not isinstance(metadata, dict):
        if require_v2_metadata:
            issues.append(
                _issue(
                    f"missing_{metadata_name}_metadata",
                    "critical",
                    f"在线生成题必须提供完整 {metadata_name} 元数据",
                )
            )
        return {}, issues

    missing = sorted(field for field in required_fields if field not in metadata)
    if missing:
        issues.append(
            _issue(
                f"incomplete_{metadata_name}_metadata",
                "critical",
                f"{metadata_name} 缺少字段：{', '.join(missing)}",
            )
        )
    if _text(metadata.get("version")) != expected_version:
        issues.append(
            _issue(
                f"invalid_{metadata_name}_version",
                "critical",
                f"{metadata_name}.version 必须为 {expected_version}",
            )
        )
    return metadata, issues


def _distractor_issues(metadata: Mapping[str, object], answer: str, metadata_name: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    distractors = metadata.get("distractor_errors")
    if not isinstance(distractors, dict):
        return [_issue("missing_distractor_errors", "critical", f"{metadata_name} 必须逐项说明三个错项的错误机制")]

    expected = _wrong_labels(answer) if answer in OPTION_LABELS else set(OPTION_LABELS)
    missing = sorted(label for label in expected if len(_text(distractors.get(label))) < 4)
    if missing:
        issues.append(
            _issue(
                "incomplete_distractor_errors",
                "high",
                f"以下错项缺少具体错误机制：{', '.join(missing)}",
            )
        )
    if answer in distractors and _text(distractors.get(answer)):
        issues.append(_issue("answer_marked_as_distractor", "critical", "正确答案不得出现在 distractor_errors 中"))
    return issues


def _culture_explanation_blocks(explanation: str) -> dict[str, str]:
    """Read the learner-facing culture explanation contract.

    The labels are deliberately line-oriented so a renderer can keep each
    block separate. An inline fallback is accepted for model responses that
    escaped newlines differently, while the generated prompt still asks for
    literal line breaks.
    """

    text = _text(explanation).replace("\r\n", "\n").replace("\r", "\n")
    # Match the new labels first.  The expression is intentionally line
    # oriented so a sentence mentioning “知识点” is not mistaken for a
    # section header.  The inline fallback below keeps old imported rows
    # readable when a client flattened newlines.
    labels = sorted(CULTURE_EXPLANATION_LABEL_TO_KEY, key=len, reverse=True)
    label_pattern = "|".join(re.escape(label) for label in labels)
    marker_re = re.compile(rf"(?:^|\n)\s*({label_pattern})\s*[：:]\s*", re.MULTILINE)
    matches = list(marker_re.finditer(text))
    if not matches:
        marker_re = re.compile(rf"({label_pattern})\s*[：:]\s*")
        matches = list(marker_re.finditer(text))
    if not matches:
        return {}

    # Keep the preferred V2 block when a row contains both old and new labels;
    # otherwise fall back to the legacy block.  This makes upgrades idempotent
    # and avoids duplicating content in the first-screen card.
    candidates: dict[str, list[tuple[int, int, str]]] = {}
    for index, match in enumerate(matches):
        label = match.group(1)
        key = CULTURE_EXPLANATION_LABEL_TO_KEY[label]
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        value = text[start:end].strip()
        if value:
            priority = 2 if label in CULTURE_EXPLANATION_NEW_LABELS else 1
            candidates.setdefault(key, []).append((priority, index, value))
    blocks: dict[str, str] = {}
    for key, values in candidates.items():
        preferred = max(item[0] for item in values)
        selected = [item[2] for item in values if item[0] == preferred]
        blocks[key] = "\n".join(selected).strip()
    return blocks


def _display_marks_balanced(value: str) -> bool:
    return all(value.count(left) == value.count(right) for left, right in (("“", "”"), ("‘", "’"), ("《", "》"), ("（", "）")))


def _culture_explanation_issues(
    explanation: str,
    *,
    require_structured: bool,
    answer: str = "",
    answer_option: str = "",
    memory_optional: bool = False,
    max_chars: int | None = None,
) -> list[dict[str, str]]:
    """Enforce a short-first, expandable explanation without a giant block."""

    text = _text(explanation)
    blocks = _culture_explanation_blocks(text)
    uses_v2_why = bool(re.search(r"(?:^|\n)\s*解题思路\s*[：:]", text))
    uses_v2_distractors = bool(re.search(r"(?:^|\n)\s*选项解析\s*[：:]", text))
    required = ("why", "knowledge", "distractors") if memory_optional else ("why", "knowledge", "distractors", "memory")
    missing = [label for label in required if not blocks.get(label)]

    if missing:
        if require_structured:
            return [
                _issue(
                    "culture_explanation_structure_missing",
                    "high",
                    "中华文化解析必须分成解题思路、选项解析、知识点、记忆方法；"
                    f"缺少：{'、'.join(missing)}",
                )
            ]
        if len(text) > 50:
            return [_issue("culture_explanation_too_long", "high", "未采用结构化格式的中华文化解析不得超过 50 字符")]
        return []

    issues: list[dict[str, str]] = []
    for phrase in CULTURE_MECHANICAL_PHRASES:
        if phrase in text:
            issues.append(
                _issue(
                    "culture_explanation_mechanical_template",
                    "high",
                    f"解析含答案复述或审核模板词：{phrase}",
                )
            )
    if re.search(r"(?:\.\.\.|…)", text):
        issues.append(_issue("culture_explanation_truncated", "high", "解析不得用省略号截断事实或选项理由"))
    if re.search(r"(?m)^\s*[”’》）】]", text):
        issues.append(_issue("culture_explanation_broken_quote", "high", "解析区块存在无起始内容的右引号，疑似资料截断"))
    if re.search(r"[\u3400-\u9fff][ \t]+[\u3400-\u9fff]", text):
        issues.append(_issue("culture_explanation_ocr_spacing", "high", "解析含中文词语内部异常空格，疑似 OCR 串行污染"))
    explanation_max_chars = max_chars or CULTURE_EXPLANATION_MAX_CHARS
    if len(text) > explanation_max_chars:
        issues.append(
            _issue(
                "culture_explanation_too_long",
                "high",
                f"当前题型的结构化中华文化解析不得超过 {explanation_max_chars} 字符",
            )
        )

    for label, (minimum, maximum) in CULTURE_EXPLANATION_BLOCK_LIMITS.items():
        value = blocks.get(label, "")
        if label == "memory" and memory_optional and not value:
            continue
        if len(value) < minimum:
            issues.append(_issue("culture_explanation_block_too_short", "high", f"解析区块‘{label}’信息不足"))
        if len(value) > maximum:
            issues.append(_issue("culture_explanation_block_too_long", "high", f"解析区块‘{label}’过长，应保留最小判断依据"))

    if require_structured and uses_v2_why:
        reasoning_parts = [part.strip() for part in re.split(r"→(?=(?:因此|所以|故)?(?:应)?选\s*[A-D])", blocks.get("why", ""), maxsplit=1) if part.strip()]
        if len(reasoning_parts) == 2:
            clue_fact = reasoning_parts[0].split("→", 1)
            reasoning_parts = [*clue_fact, reasoning_parts[1]] if len(clue_fact) == 2 else reasoning_parts
        if len(reasoning_parts) < 3:
            issues.append(
                _issue(
                    "culture_explanation_reasoning_chain_incomplete",
                    "high",
                    "用户可见的解题思路必须完整保留‘题干线索→相关事实→答案结论’三段",
                )
            )
        conclusion = (
            reasoning_parts[-1]
            if len(reasoning_parts) >= 3
            else blocks.get("why", "").rsplit("→", 1)[-1].strip()
        )
        answer_key = _text(answer).upper()
        names_answer = bool(
            (answer_option and _normalized(answer_option) in _normalized(conclusion))
            or (
                answer_key
                and re.search(
                    rf"(?:选|选择|应选|答案(?:为|是)?)\s*{re.escape(answer_key)}(?=$|[→。；，,、:“”‘’（）()\s])",
                    conclusion,
                    re.I,
                )
            )
        )
        if answer_key and not names_answer:
            issues.append(
                _issue(
                    "culture_explanation_reasoning_missing_answer",
                    "high",
                    "用户可见的解题思路结论必须落到正确选项或答案字母",
                )
            )
        if answer:
            selection_mentions = re.findall(
                rf"(?:选|选择|应选)\s*{re.escape(_text(answer).upper())}(?=$|[→。；，,、:“”‘’（）()\s])",
                blocks.get("why", ""),
                re.I,
            )
            if len(selection_mentions) > 1:
                issues.append(
                    _issue(
                        "culture_explanation_repeated_answer_conclusion",
                        "high",
                        "解题思路重复出现同一选择结论，应只在最后一段落答案",
                    )
                )

    distractor_labels = set(
        re.findall(r"(?:^|\n|[。！？；;])\s*([ABCD])\s*[.．、:：]", blocks["distractors"], re.MULTILINE)
    )
    minimum_options = 4 if require_structured else 3
    if len(distractor_labels) < minimum_options:
        label_name = "选项解析" if require_structured else "易混辨析"
        issues.append(
            _issue(
                "culture_explanation_distractors_incomplete",
                "high",
                f"{label_name}至少要逐项列出{'四个' if require_structured else '三个'}选项的具体边界",
            )
        )
    # A structured block must not merely repeat the option letter.  Requiring
    # a short explanatory tail catches the old “A项正确/B项为干扰项” shell
    # while still allowing concise factual sentences.
    if require_structured:
        option_lines: dict[str, str] = {}
        for label in sorted(distractor_labels):
            line_match = re.search(
                rf"(?:^|\n|[。！？；;])\s*{label}\s*[.．、:：]\s*([^\n]+)",
                blocks["distractors"],
                re.MULTILINE,
            )
            line = _text(line_match.group(1) if line_match else "")
            option_lines[label] = line
            if len(line) < 6 or re.fullmatch(r"(?:正确|错误|干扰项|排除)[。！!，,；;：: ]*", line):
                issues.append(
                    _issue(
                        "culture_explanation_option_reason_weak",
                        "high",
                        f"选项解析 {label} 行必须包含具体判断依据",
                    )
                )
            if uses_v2_distractors:
                expected_marker = "✓" if label == _text(answer).upper() else "×"
                if not line.startswith(expected_marker):
                    issues.append(
                        _issue(
                            "culture_explanation_option_marker_mismatch",
                            "high",
                            f"选项解析 {label} 行应以 {expected_marker} 标明判断结果",
                        )
                    )
                if not re.search(r"[。！？!?]$", line):
                    issues.append(
                        _issue(
                            "culture_explanation_option_reason_unfinished",
                            "high",
                            f"选项解析 {label} 行必须以完整句结束，不得留下半截事实或名单",
                        )
                    )
                if not _display_marks_balanced(line):
                    issues.append(
                        _issue(
                            "culture_explanation_option_broken_marks",
                            "high",
                            f"选项解析 {label} 行的引号、书名号或括号未成对",
                        )
                    )
                tail = re.sub(r"[。！？!?]+$", "", line).rstrip()
                dangling_tail = bool(
                    re.search(r"(?:包括|分为|通常为|通常是|[、，,；;：:])$", tail)
                    or re.search(r"(?:^|[，,；;：:\s])(?:与|和|或|及|是|为)$", tail)
                    or re.search(r"(?:这是|属于|对应|关于).{0,30}的$", tail)
                )
                if dangling_tail:
                    issues.append(
                        _issue(
                            "culture_explanation_option_reason_fragment",
                            "high",
                            f"选项解析 {label} 行疑似在连接词或列举中途被截断",
                        )
                    )
        mechanical_reverse_lines = sum(
            bool(re.search(r"属于[“\"][^”\"]{1,36}[”\"]范围", line))
            for line in option_lines.values()
        )
        if mechanical_reverse_lines >= 2:
            issues.append(
                _issue(
                    "culture_explanation_repeated_reverse_template",
                    "high",
                    "多个选项重复使用‘属于某范围’模板，应直接说明该项为何正确或为何排除",
                )
            )
    return issues


def audit_culture_question(
    question: Mapping[str, object],
    *,
    metadata: object = None,
    require_v2_metadata: bool = False,
) -> dict:
    issues = _common_issues(question, CULTURE_SUBJECT)
    stem = _text(question.get("stem"))
    explanation = _text(question.get("explanation"))
    combined = f"{stem}\n{explanation}".lower()
    uses_v3_contract = is_culture_v3_metadata(metadata)

    for phrase in META_PHRASES:
        if phrase.lower() in combined:
            issues.append(_issue("culture_meta_language", "high", f"题面含命题过程或元话术：{phrase}"))
    for phrase in CULTURE_MEDIA_PHRASES:
        if phrase.lower() in combined:
            issues.append(_issue("culture_material_question", "high", f"当前在线题不得依赖材料、图片或视频：{phrase}"))
    if len(stem) > 220:
        issues.append(_issue("culture_stem_too_long", "high", "中华文化题干应简洁直接，不得超过 220 字符"))
    if not _has_chinese(explanation):
        issues.append(_issue("culture_explanation_not_chinese", "high", "中华文化解析必须使用中文"))
    if len(explanation) < 8:
        issues.append(_issue("culture_explanation_too_short", "high", "解析必须给出可核对的答案依据"))
    answer = _text(question.get("answer")).upper()
    answer_option = _options(question).get(answer, "")
    issues.extend(
        _culture_explanation_issues(
            explanation,
            require_structured=require_v2_metadata,
            answer=answer,
            answer_option=answer_option,
            memory_optional=uses_v3_contract,
            max_chars=(
                culture_v3_display_budget(question, metadata)
                if uses_v3_contract and isinstance(metadata, Mapping)
                else None
            ),
        )
    )

    if uses_v3_contract:
        metadata, metadata_issues = _metadata_issues(
            metadata,
            CULTURE_V3_REQUIRED_FIELDS,
            "culture_v3",
            require_v2_metadata,
            expected_version="3.0",
        )
        issues.extend(metadata_issues)
        if metadata:
            for contract_issue in validate_culture_v3_contract(question, metadata):
                issues.append(
                    _issue(
                        contract_issue["code"],
                        contract_issue.get("severity", "high"),
                        contract_issue["message"],
                    )
                )
        return _finalize(
            CULTURE_SUBJECT,
            issues,
            verification_level="v3_structured_teaching_plus_blind_answer_and_explanation_review",
        )

    metadata, metadata_issues = _metadata_issues(
        metadata,
        {
            "version",
            "question_form",
            "fact_anchor",
            "answer_basis",
            "evidence_excerpt",
            "reasoning_chain",
            "knowledge_extension",
            "memory_hook",
            "scope_level",
            "controversy_status",
            "distractor_errors",
            "verification_status",
            "difficulty_features",
        },
        "culture_v2",
        require_v2_metadata,
    )
    issues.extend(metadata_issues)
    if metadata:
        question_form = _text(metadata.get("question_form"))
        if question_form not in CULTURE_FORMS:
            issues.append(_issue("invalid_culture_question_form", "high", "question_form 不属于中华文化 V2 允许题型"))
        # “无一不是……”是双重否定的正向陈述，不能因为其中出现
        # “不是”就把整道题误判成逆向题。
        stem_for_direction = re.sub(r"无一不是|没有一个不是|莫不(?:是)?", "均是", stem)
        negative_stem = bool(
            re.search(
                r"不正确|不属于|不包括|并非|不是|错误(?:的是|项)?|有误(?:的是)?|不当(?:的是)?|"
                r"不同的是|不相同|不能说明|不应|不宜|需排除|排除对象|例外|不在(?:该|此|本|名单|范围)",
                stem_for_direction,
            )
        )
        negative_form = question_form in {"negative_identification", "odd_one_out"}
        if negative_stem != negative_form:
            issues.append(_issue("culture_question_form_mismatch", "high", "question_form 与题干正向或逆向设问不一致"))
        if _text(metadata.get("scope_level")) != "core":
            issues.append(_issue("culture_scope_not_core", "high", "只接收普通考试范围内的核心、稳定文化常识"))
        if _text(metadata.get("controversy_status")) != "stable":
            issues.append(_issue("culture_fact_not_stable", "high", "争议性或考据型事实不得进入在线训练题"))
        if _text(metadata.get("verification_status")) != "cross_checked":
            issues.append(_issue("culture_not_cross_checked", "high", "culture_v2.verification_status 必须为 cross_checked"))

        anchor = metadata.get("fact_anchor")
        if not isinstance(anchor, dict) or any(len(_text(anchor.get(key))) < 1 for key in ("subject", "relation", "object")):
            issues.append(_issue("invalid_culture_fact_anchor", "critical", "fact_anchor 必须明确对象、关系和值"))
            anchor_text = ""
        else:
            anchor_text = " ".join(_text(value) for value in anchor.values())

        answer_basis = _text(metadata.get("answer_basis"))
        evidence_excerpt = _text(metadata.get("evidence_excerpt"))
        reasoning_chain = _text(metadata.get("reasoning_chain"))
        knowledge_extension = _text(metadata.get("knowledge_extension"))
        memory_hook = _text(metadata.get("memory_hook"))
        if len(answer_basis) < 6:
            issues.append(_issue("weak_culture_answer_basis", "high", "answer_basis 必须解释答案对应关系"))
        if len(evidence_excerpt) < 8:
            issues.append(_issue("weak_culture_evidence", "high", "evidence_excerpt 必须包含可复核的事实陈述"))
        if len(reasoning_chain) < 12:
            issues.append(_issue("weak_culture_reasoning_chain", "high", "reasoning_chain 必须补出题干线索到答案之间的推理过程"))
        elif not CULTURE_REASONING_CONNECTOR_RE.search(reasoning_chain):
            issues.append(_issue("culture_reasoning_chain_missing_link", "high", "reasoning_chain 缺少明确的因果、归属或推导连接"))
        if "→" in reasoning_chain and len([part for part in reasoning_chain.split("→") if _text(part)]) < 3:
            issues.append(_issue("culture_reasoning_chain_too_shallow", "high", "箭头推理链至少应包含线索、事实和结论三段"))
        if len(knowledge_extension) < 8 or re.search(r"(?:因此|所以)?选\s*[A-D]", knowledge_extension, re.I):
            issues.append(_issue("weak_culture_knowledge_extension", "high", "knowledge_extension 应是独立复习事实，不得重复选答案过程"))
        normalized_knowledge = _normalized(knowledge_extension)
        normalized_reasoning = _normalized(reasoning_chain)
        if normalized_knowledge and (
            normalized_knowledge == normalized_reasoning
            or normalized_knowledge in normalized_reasoning
        ):
            issues.append(_issue("culture_knowledge_duplicates_reasoning", "high", "知识点与解题思路职责重复"))
        if len(memory_hook) < 6 or _normalized(memory_hook) in {
            _normalized("记住这组对应关系"),
            _normalized("把这组对应记住"),
        }:
            issues.append(_issue("weak_culture_memory_hook", "high", "memory_hook 必须提供可复用的关键词、对比或知识链"))

        for field_name, field_value in (
            ("answer_basis", answer_basis),
            ("evidence_excerpt", evidence_excerpt),
            ("reasoning_chain", reasoning_chain),
            ("knowledge_extension", knowledge_extension),
            ("memory_hook", memory_hook),
        ):
            if any(phrase in field_value for phrase in CULTURE_MECHANICAL_PHRASES):
                issues.append(
                    _issue(
                        "culture_metadata_mechanical_template",
                        "high",
                        f"culture_v2.{field_name} 含答案复述或审核模板词",
                    )
                )
            if re.search(r"(?:\.\.\.|…)", field_value):
                issues.append(_issue("culture_metadata_truncated", "high", f"culture_v2.{field_name} 疑似被截断"))
            if re.search(r"[\u3400-\u9fff][ \t]+[\u3400-\u9fff]", field_value):
                issues.append(_issue("culture_metadata_ocr_spacing", "high", f"culture_v2.{field_name} 含异常 OCR 空格"))
            if (
                field_name in {"answer_basis", "evidence_excerpt", "knowledge_extension"}
                and len(field_value) > 80
                and len(re.findall(r"[:：]", field_value)) >= 4
            ):
                issues.append(_issue("culture_metadata_dense_ocr_list", "high", f"culture_v2.{field_name} 疑似混入多条 OCR 列表"))

        answer = _text(question.get("answer")).upper()
        answer_option = _options(question).get(answer, "")
        if answer_option and _normalized(answer_option) not in _normalized(f"{anchor_text} {answer_basis}"):
            issues.append(_issue("culture_answer_not_anchored", "high", "正确选项必须在事实锚点或答案依据中被明确对应"))
        reasoning_names_answer = bool(
            answer_option
            and (
                _normalized(answer_option) in _normalized(reasoning_chain)
                or re.search(rf"(?:选|选择|应选|答案(?:为|是)?)\s*{re.escape(answer)}(?:\b|[。；，,])", reasoning_chain, re.I)
            )
        )
        if answer_option and not reasoning_names_answer:
            issues.append(_issue("culture_reasoning_missing_answer", "high", "reasoning_chain 必须明确落到正确选项原文"))
        issues.extend(_distractor_issues(metadata, answer, "culture_v2"))

        distractors = metadata.get("distractor_errors")
        if isinstance(distractors, dict):
            for label, value in distractors.items():
                reason = _text(value)
                if any(phrase in reason for phrase in CULTURE_MECHANICAL_PHRASES) or re.search(r"(?:\.\.\.|…)", reason):
                    issues.append(
                        _issue(
                            "culture_distractor_reason_mechanical",
                            "high",
                            f"错项 {label} 的说明含模板词或截断内容",
                        )
                    )

        features = metadata.get("difficulty_features")
        if not isinstance(features, list) or not any(_text(item) for item in features):
            issues.append(_issue("missing_culture_difficulty_features", "high", "difficulty_features 至少说明一个难度来源"))

    return _finalize(CULTURE_SUBJECT, issues, verification_level="metadata_consistency_plus_blind_review")


def audit_english_question(
    question: Mapping[str, object],
    *,
    metadata: object = None,
    require_v2_metadata: bool = False,
) -> dict:
    issues = _common_issues(question, ENGLISH_SUBJECT)
    stem = _text(question.get("stem"))
    explanation = _text(question.get("explanation"))
    options = _options(question)

    if _text(question.get("module")) != "语言知识":
        issues.append(_issue("english_module_out_of_scope", "critical", "英语在线出题只允许语言知识模块"))
    submodule = _text(question.get("submodule"))
    if submodule not in ENGLISH_SKILLS:
        issues.append(_issue("english_submodule_out_of_scope", "critical", "英语考点只允许词汇、语法、语用"))

    if stem.count("____") != 1:
        issues.append(_issue("english_blank_count", "critical", "英文题干必须且只能包含一个 ____"))
    if _has_chinese(stem) or not _has_latin(stem):
        issues.append(_issue("english_stem_not_english", "critical", "英语题干必须是英文句子"))
    if len(stem.split()) < 4 or len(stem.split()) > 45:
        issues.append(_issue("english_stem_length", "high", "英文题干应为 4-45 个词的自然考试句子"))
    if stem and not (re.search(r"[.!?\"']\s*$", stem) or stem.endswith("____")):
        issues.append(_issue("english_stem_not_sentence", "high", "英文题干必须是完整句子填空"))
    lower_stem = stem.lower()
    for phrase in ENGLISH_OUT_OF_SCOPE_PHRASES:
        if phrase in lower_stem:
            issues.append(_issue("english_out_of_scope_task", "critical", f"英语在线题不得混入阅读、写作、翻译或完形：{phrase}"))

    for label, option in options.items():
        if _has_chinese(option) or not _has_latin(option):
            issues.append(_issue("english_option_not_english", "critical", f"选项 {label} 必须为英文"))
        if re.match(r"^[A-D][.、:]\s*", option, flags=re.IGNORECASE):
            issues.append(_issue("english_option_has_label", "high", f"选项 {label} 不得重复携带选项字母"))
    if not _has_chinese(explanation):
        issues.append(_issue("english_explanation_not_chinese", "critical", "英语题解析必须使用中文"))
    if len(explanation) < 15:
        issues.append(_issue("english_explanation_too_short", "high", "英语解析必须说明正确依据和至少一个陷阱"))
    if len(explanation) > 260:
        issues.append(_issue("english_explanation_too_long", "high", "英语解析不应超过 260 字符"))

    metadata, metadata_issues = _metadata_issues(
        metadata,
        {
            "version",
            "skill",
            "completed_sentence",
            "answer_rationale",
            "distractor_errors",
            "verification_checks",
            "verification_status",
            "difficulty_features",
        },
        "english_v2",
        require_v2_metadata,
    )
    issues.extend(metadata_issues)
    if metadata:
        if submodule in ENGLISH_SKILLS and _text(metadata.get("skill")) != ENGLISH_SKILLS[submodule]:
            issues.append(_issue("english_skill_mismatch", "high", "english_v2.skill 与 submodule 不一致"))
        if _text(metadata.get("verification_status")) != "cross_checked":
            issues.append(_issue("english_not_cross_checked", "high", "english_v2.verification_status 必须为 cross_checked"))

        answer = _text(question.get("answer")).upper()
        correct_option = options.get(answer, "")
        expected_sentence = stem.replace("____", correct_option, 1)
        completed_sentence = _text(metadata.get("completed_sentence"))
        if _normalized_english(completed_sentence) != _normalized_english(expected_sentence):
            issues.append(_issue("english_completed_sentence_mismatch", "critical", "completed_sentence 必须等于题干填入正确选项后的完整句子"))
        if len(_text(metadata.get("answer_rationale"))) < 8:
            issues.append(_issue("weak_english_answer_rationale", "high", "answer_rationale 必须说明词义、搭配、语法或语境依据"))
        issues.extend(_distractor_issues(metadata, answer, "english_v2"))

        checks = metadata.get("verification_checks")
        required_checks = {"unique_answer", "grammar", "collocation", "context_natural"}
        if not isinstance(checks, dict) or any(checks.get(key) is not True for key in required_checks):
            issues.append(_issue("english_verification_checks_failed", "high", "唯一答案、语法、搭配和语境自然度四项检查必须全部为 true"))
        features = metadata.get("difficulty_features")
        if not isinstance(features, list) or not any(_text(item) for item in features):
            issues.append(_issue("missing_english_difficulty_features", "high", "difficulty_features 至少说明一个真实难点"))

    return _finalize(ENGLISH_SUBJECT, issues, verification_level="deterministic_form_plus_blind_review")


_ALLOWED_FUNCTIONS = {
    "abs": abs,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    "exp": math.exp,
    "log": math.log,
    "ln": math.log,
    "floor": math.floor,
    "ceil": math.ceil,
}
_ALLOWED_CONSTANTS = {"pi": math.pi, "e": math.e}
_ALLOWED_BINARY_OPS = {
    ast.Add: lambda left, right: left + right,
    ast.Sub: lambda left, right: left - right,
    ast.Mult: lambda left, right: left * right,
    ast.Div: lambda left, right: left / right,
    ast.Pow: lambda left, right: left**right,
}
_ALLOWED_UNARY_OPS = {
    ast.UAdd: lambda value: value,
    ast.USub: lambda value: -value,
}


def _eval_math_node(node: ast.AST, variables: Mapping[str, float]) -> float:
    if isinstance(node, ast.Expression):
        return _eval_math_node(node.body, variables)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id in variables:
            return float(variables[node.id])
        if node.id in _ALLOWED_CONSTANTS:
            return _ALLOWED_CONSTANTS[node.id]
        raise ValueError(f"unknown variable: {node.id}")
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINARY_OPS:
        left = _eval_math_node(node.left, variables)
        right = _eval_math_node(node.right, variables)
        if isinstance(node.op, ast.Pow) and abs(right) > 20:
            raise ValueError("power is too large")
        return float(_ALLOWED_BINARY_OPS[type(node.op)](left, right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY_OPS:
        return float(_ALLOWED_UNARY_OPS[type(node.op)](_eval_math_node(node.operand, variables)))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        function = _ALLOWED_FUNCTIONS.get(node.func.id)
        if not function or node.keywords or len(node.args) not in {1, 2}:
            raise ValueError("function call is not allowed")
        arguments = [_eval_math_node(item, variables) for item in node.args]
        return float(function(*arguments))
    raise ValueError(f"unsupported expression node: {type(node).__name__}")


def safe_evaluate_math_expression(expression: object, variables: Mapping[str, object] | None = None) -> float:
    raw = _text(expression).replace("^", "**").replace("π", "pi")
    if not raw or len(raw) > 320 or "__" in raw:
        raise ValueError("expression is empty or too long")
    parsed = ast.parse(raw, mode="eval")
    if sum(1 for _ in ast.walk(parsed)) > 120:
        raise ValueError("expression is too complex")
    numeric_variables = {str(key): float(value) for key, value in (variables or {}).items()}
    result = _eval_math_node(parsed, numeric_variables)
    if not math.isfinite(result):
        raise ValueError("expression result is not finite")
    return result


def _is_close(left: float, right: float, tolerance: float) -> bool:
    return math.isclose(left, right, rel_tol=max(tolerance, 1e-6), abs_tol=max(tolerance, 1e-7))


def _numeric_derivative(expression: str, variable: str, point: float, variables: dict[str, float], order: int) -> float:
    scale = 1 + abs(point)
    h = (1e-4 if order == 1 else 1e-3) * scale

    def value(offset: float) -> float:
        current = dict(variables)
        current[variable] = point + offset
        return safe_evaluate_math_expression(expression, current)

    if order == 1:
        central = (value(-2 * h) - 8 * value(-h) + 8 * value(h) - value(2 * h)) / (12 * h)
        left = (3 * value(0) - 4 * value(-h) + value(-2 * h)) / (2 * h)
        right = (-3 * value(0) + 4 * value(h) - value(2 * h)) / (2 * h)
        if not _is_close(left, right, 2e-3):
            raise ValueError("left and right sampled derivatives disagree")
        return central
    if order == 2:
        central = (-value(2 * h) + 16 * value(h) - 30 * value(0) + 16 * value(-h) - value(-2 * h)) / (12 * h * h)
        half_h = h / 2
        refined = (
            -value(2 * half_h)
            + 16 * value(half_h)
            - 30 * value(0)
            + 16 * value(-half_h)
            - value(-2 * half_h)
        ) / (12 * half_h * half_h)
        if not _is_close(central, refined, 3e-3):
            raise ValueError("sampled second derivative does not converge")
        return refined
    raise ValueError("only first and second derivatives are supported")


def _simpson_integral(expression: str, variable: str, lower: float, upper: float, variables: dict[str, float]) -> float:
    intervals = 600
    step = (upper - lower) / intervals
    total = 0.0
    for index in range(intervals + 1):
        current = dict(variables)
        current[variable] = lower + index * step
        value = safe_evaluate_math_expression(expression, current)
        weight = 1 if index in {0, intervals} else (4 if index % 2 else 2)
        total += weight * value
    return total * step / 3


def _limit_estimate(expression: str, variable: str, point: object, direction: str, variables: dict[str, float]) -> float:
    if _text(point).lower() in {"inf", "+inf", "infinity", "+infinity"}:
        samples = [1e3, 3e3, 1e4]
    elif _text(point).lower() in {"-inf", "-infinity"}:
        samples = [-1e3, -3e3, -1e4]
    else:
        center = float(point)
        scale = 1 + abs(center)
        offsets = [1e-3 * scale, 3e-4 * scale, 1e-4 * scale]
        if direction == "left":
            samples = [center - item for item in offsets]
        elif direction == "right":
            samples = [center + item for item in offsets]
        else:
            left_values = []
            right_values = []
            for item in offsets:
                left_context = dict(variables)
                right_context = dict(variables)
                left_context[variable] = center - item
                right_context[variable] = center + item
                left_values.append(safe_evaluate_math_expression(expression, left_context))
                right_values.append(safe_evaluate_math_expression(expression, right_context))
            if not _is_close(left_values[-1], right_values[-1], 5e-3):
                raise ValueError("left and right sampled limits disagree")
            return (left_values[-1] + right_values[-1]) / 2

    values = []
    for sample in samples:
        current = dict(variables)
        current[variable] = sample
        values.append(safe_evaluate_math_expression(expression, current))
    if not _is_close(values[-1], values[-2], 1e-2):
        raise ValueError("sampled limit does not converge")
    return values[-1]


def _verification_options(spec: Mapping[str, object], question_options: Mapping[str, str]) -> dict[str, dict]:
    raw_options = spec.get("options")
    if not isinstance(raw_options, dict) or set(raw_options) != set(OPTION_LABELS):
        raise ValueError("verification_spec.options must contain A-D")
    parsed: dict[str, dict] = {}
    for label in OPTION_LABELS:
        item = raw_options.get(label)
        if not isinstance(item, dict):
            raise ValueError(f"verification option {label} must be an object")
        if _normalized(item.get("source_text")) != _normalized(question_options[label]):
            raise ValueError(f"verification option {label} source_text does not match displayed option")
        parsed[label] = item
    return parsed


def verify_math_spec(spec: object, *, answer: str, options: Mapping[str, str]) -> dict:
    result = {"ok": False, "kind": None, "valid_labels": [], "computed": None, "errors": []}
    if not isinstance(spec, dict):
        result["errors"].append("verification_spec must be an object")
        return result

    kind = _text(spec.get("kind"))
    result["kind"] = kind
    if kind not in MATH_VERIFICATION_KINDS:
        result["errors"].append(f"unsupported verification kind: {kind or 'blank'}")
        return result

    try:
        parsed_options = _verification_options(spec, options)
        tolerance = float(spec.get("tolerance") or 1e-4)
        if tolerance <= 0 or tolerance > 0.05:
            raise ValueError("tolerance must be between 0 and 0.05")
        variables = {str(key): float(value) for key, value in (spec.get("variables") or {}).items()}
        expression = _text(spec.get("expression"))
        variable = _text(spec.get("variable")) or "x"

        if kind == "numeric_expression":
            computed = safe_evaluate_math_expression(expression, variables)
            valid_labels = [
                label
                for label, item in parsed_options.items()
                if _is_close(computed, safe_evaluate_math_expression(item.get("value")), tolerance)
            ]
        elif kind in {"derivative_value", "partial_derivative_value"}:
            point = float(spec.get("point"))
            order = int(spec.get("order") or 1)
            computed = _numeric_derivative(expression, variable, point, variables, order)
            valid_labels = [
                label
                for label, item in parsed_options.items()
                if _is_close(computed, safe_evaluate_math_expression(item.get("value")), max(tolerance, 2e-4))
            ]
        elif kind == "definite_integral":
            lower = float(spec.get("lower"))
            upper = float(spec.get("upper"))
            computed = _simpson_integral(expression, variable, lower, upper, variables)
            valid_labels = [
                label
                for label, item in parsed_options.items()
                if _is_close(computed, safe_evaluate_math_expression(item.get("value")), max(tolerance, 5e-4))
            ]
        elif kind == "limit_value":
            computed = _limit_estimate(expression, variable, spec.get("point"), _text(spec.get("direction")) or "both", variables)
            valid_labels = [
                label
                for label, item in parsed_options.items()
                if _is_close(computed, safe_evaluate_math_expression(item.get("value")), max(tolerance, 1e-3))
            ]
        elif kind == "antiderivative_choice":
            sample_points = spec.get("sample_points")
            if not isinstance(sample_points, list) or len(sample_points) < 3:
                raise ValueError("antiderivative_choice requires at least three sample_points")
            valid_labels = []
            for label, item in parsed_options.items():
                candidate = _text(item.get("expression"))
                matches = True
                for raw_point in sample_points:
                    point = float(raw_point)
                    expected_context = dict(variables)
                    expected_context[variable] = point
                    expected = safe_evaluate_math_expression(expression, expected_context)
                    actual = _numeric_derivative(candidate, variable, point, variables, 1)
                    if not _is_close(actual, expected, max(tolerance, 5e-4)):
                        matches = False
                        break
                if matches:
                    valid_labels.append(label)
            computed = {"sample_points": sample_points}
        else:  # expression_choice
            reference = _text(spec.get("reference_expression"))
            sample_assignments = spec.get("sample_assignments")
            if not isinstance(sample_assignments, list) or len(sample_assignments) < 3:
                raise ValueError("expression_choice requires at least three sample_assignments")
            valid_labels = []
            for label, item in parsed_options.items():
                candidate = _text(item.get("expression"))
                matches = True
                for assignment in sample_assignments:
                    if not isinstance(assignment, dict):
                        raise ValueError("sample_assignments entries must be objects")
                    context = {str(key): float(value) for key, value in assignment.items()}
                    expected = safe_evaluate_math_expression(reference, context)
                    actual = safe_evaluate_math_expression(candidate, context)
                    if not _is_close(actual, expected, tolerance):
                        matches = False
                        break
                if matches:
                    valid_labels.append(label)
            computed = {"sample_count": len(sample_assignments)}

        result["computed"] = computed
        result["valid_labels"] = valid_labels
        if valid_labels != [answer]:
            result["errors"].append(f"locally verified labels are {valid_labels}, declared answer is {answer}")
            return result
        result["ok"] = True
        return result
    except Exception as exc:
        result["errors"].append(str(exc))
        return result


def _has_latex(value: object) -> bool:
    text = _text(value)
    return bool(re.search(r"\\\(.+?\\\)|\$[^$]+\$", text, flags=re.DOTALL))


def audit_math_question(
    question: Mapping[str, object],
    *,
    metadata: object = None,
    require_v2_metadata: bool = False,
) -> dict:
    issues = _common_issues(question, MATH_SUBJECT)
    stem = _text(question.get("stem"))
    explanation = _text(question.get("explanation"))
    combined = f"{stem}\n{explanation}"

    if not _has_latex(stem):
        issues.append(_issue("math_stem_missing_latex", "critical", "数学题干中的数学表达式必须使用 LaTeX 包裹"))
    for pattern in MATH_BANNED_PATTERNS:
        if pattern in combined:
            issues.append(_issue("math_out_of_scope", "critical", f"数学题超出 Z002 允许范围：{pattern}"))
    for phrase in META_PHRASES:
        if phrase.lower() in combined.lower():
            issues.append(_issue("math_meta_language", "high", f"题面含命题过程或元话术：{phrase}"))
    if not _has_chinese(explanation):
        issues.append(_issue("math_explanation_not_chinese", "critical", "数学解析必须使用中文"))

    marker_groups = {
        "解题思路": ("解题思路", "思路"),
        "关键公式": ("关键公式", "公式"),
        "推导过程": ("推导过程", "计算过程", "推导"),
        "答案理由": ("答案理由", "因此答案", "答案"),
        "易错点": ("易错点", "易错提醒", "易错"),
    }
    for label, variants in marker_groups.items():
        if not any(item in explanation for item in variants):
            issues.append(_issue("math_explanation_incomplete", "high", f"数学解析缺少：{label}"))

    metadata, metadata_issues = _metadata_issues(
        metadata,
        {
            "version",
            "problem_family",
            "givens",
            "required",
            "solution_method",
            "source_expression",
            "verification_status",
            "verification_spec",
            "distractor_errors",
            "difficulty_features",
        },
        "math_v2",
        require_v2_metadata,
    )
    issues.extend(metadata_issues)
    verification = {"ok": False, "errors": ["math_v2 metadata missing"]}
    if metadata:
        if _text(metadata.get("verification_status")) != "locally_verified":
            issues.append(_issue("math_not_locally_verified", "critical", "math_v2.verification_status 必须为 locally_verified"))
        if not isinstance(metadata.get("givens"), list) or not any(_text(item) for item in metadata.get("givens") or []):
            issues.append(_issue("math_givens_missing", "high", "math_v2.givens 必须列出已知条件"))
        if len(_text(metadata.get("required"))) < 2 or len(_text(metadata.get("solution_method"))) < 2:
            issues.append(_issue("math_method_incomplete", "high", "math_v2 必须写清求解目标和方法"))
        source_expression = _text(metadata.get("source_expression"))
        if not source_expression or _normalized(source_expression) not in _normalized(stem):
            issues.append(_issue("math_source_expression_mismatch", "critical", "source_expression 必须逐字对应题干中的公式或条件片段"))

        answer = _text(question.get("answer")).upper()
        issues.extend(_distractor_issues(metadata, answer, "math_v2"))
        features = metadata.get("difficulty_features")
        if not isinstance(features, list) or not any(_text(item) for item in features):
            issues.append(_issue("missing_math_difficulty_features", "high", "difficulty_features 至少说明一个计算或辨析难点"))

        verification_spec = metadata.get("verification_spec")
        verification_kind = _text(verification_spec.get("kind")) if isinstance(verification_spec, dict) else ""
        submodule = _text(question.get("submodule"))
        allowed_kinds = MATH_SUBMODULE_VERIFICATION_KINDS.get(submodule)
        if allowed_kinds is not None and verification_kind not in allowed_kinds:
            issues.append(
                _issue(
                    "math_verification_kind_mismatch",
                    "critical",
                    f"{submodule} 不应使用 {verification_kind or '空'} 复算规格",
                )
            )
        verification = verify_math_spec(verification_spec, answer=answer, options=_options(question))
        if not verification.get("ok"):
            message = verification.get("errors", ["本地复算未通过"])[0]
            issues.append(_issue("math_local_verification_failed", "critical", f"数学本地复算失败：{message}"))

    return _finalize(MATH_SUBJECT, issues, verification_level="local_recalculation_plus_blind_review", local_verification=verification)


def metadata_key_for_subject(subject: str) -> str | None:
    return {
        CULTURE_SUBJECT: "culture_v3",
        ENGLISH_SUBJECT: "english_v2",
        MATH_SUBJECT: "math_v2",
    }.get(subject)


def audit_subject_question(
    question: Mapping[str, object],
    *,
    metadata: object = None,
    require_v2_metadata: bool = False,
) -> dict:
    subject = _text(question.get("subject"))
    if subject == CULTURE_SUBJECT:
        return audit_culture_question(question, metadata=metadata, require_v2_metadata=require_v2_metadata)
    if subject == ENGLISH_SUBJECT:
        return audit_english_question(question, metadata=metadata, require_v2_metadata=require_v2_metadata)
    if subject == MATH_SUBJECT:
        return audit_math_question(question, metadata=metadata, require_v2_metadata=require_v2_metadata)
    return _finalize(subject, [_issue("unsupported_quality_subject", "critical", f"未配置专项质量门：{subject}")])


def subject_v2_prompt_requirement(subject: str) -> str:
    if subject == CULTURE_SUBJECT:
        return (
            "\n中华文化解析 V3 专项要求：\n"
            "1. 只考普通考研范围内稳定、无争议的核心文化常识；题干短、直接，不出材料题、图片题或冷僻考据题。\n"
            "2. 先确定人物/时代/作品/制度/概念的事实锚点，再设计同朝代、同流派、同体裁或同门类干扰项。\n"
            "3. 只输出 culture_v3 教学契约，不要自行编写 explanation；后端会统一渲染现有解题思路、选项解析、知识点、记忆方法区块。\n"
            "4. question_form 只能为 direct_identification、relationship_match、negative_identification、odd_one_out；reasoning_mode 按事实关系选择 person_event_effect、person_school_claim、work_author_era、concept_definition、chronology、place_object_mapping、category_comparison、quote_meaning、institution_function、direct_fact。\n"
            "5. reasoning_steps 分别写 clue、bridge、conclusion：clue 只提取题干线索，bridge 补出中间文化事实，conclusion 才落到答案；禁止把题干和答案换个说法当作 bridge。\n"
            "6. option_analysis 必须覆盖 A-D。每项包含 verdict、fact、fit：fact 说明该项真实对应的知识，fit 说明为什么符合或为何与本题错配；不得只写‘符合题干’‘不符合共同限定’‘故不选’。\n"
            "7. knowledge_extension 只扩展独立考试知识，不写做题步骤，也不重复 bridge。memory_strategy 只能为 keyword、contrast、chain、none；没有真正有用的记忆抓手时用 none 且 memory_hook 留空。\n"
            "8. fact_anchor 和 evidence_excerpt 必须是可核对的具体事实；scope_level=core、controversy_status=stable、verification_status=cross_checked。内容优先级为准确、清楚、教学价值、简洁；不要出现来源、生成、AI、考纲归类或审核口吻。"
        )
    if subject == ENGLISH_SUBJECT:
        return (
            "\n英语运用 V2 专项要求：\n"
            "1. 只生成语言知识单选题：module 固定语言知识，submodule 只能是词汇、语法、语用；不得生成阅读、完形、翻译或作文。\n"
            "2. stem 必须是自然英文句子且只含一个 ____；A-D 都必须是英文，解析必须用中文。\n"
            "3. english_v2 必须提供 skill、completed_sentence、answer_rationale、distractor_errors、verification_checks、verification_status、difficulty_features。\n"
            "4. completed_sentence 必须等于把正确选项原样填入题干后的完整句子；verification_checks 的 unique_answer、grammar、collocation、context_natural 必须全部为 true。\n"
            "5. 三个错项要分别说明近义词、形近词、词性、搭配、时态语态、非谓语、从句或语域陷阱；不得用明显离谱选项。\n"
            "6. verification_status 固定 cross_checked，skill 按词汇/语法/语用分别写 vocabulary/grammar/pragmatics。"
        )
    if subject == MATH_SUBJECT:
        return (
            "\n数学基础 V2 专项要求：\n"
            "1. 只在 Z002 三个允许模块及当前考点内命题；禁止线代、概率、级数、微分方程、多重积分、空间解析几何、证明题和开放题。\n"
            "2. 所有公式使用 \\(...\\)；解析必须明确写出解题思路、关键公式、推导过程、答案理由、易错点。\n"
            "3. math_v2 必须提供 problem_family、givens、required、solution_method、source_expression、verification_status、verification_spec、distractor_errors、difficulty_features。\n"
            "4. verification_status 固定 locally_verified；source_expression 必须逐字出现在题干中。不得只声称已复算，必须给本地可执行 verification_spec。\n"
            "5. verification_spec.kind 只能是 numeric_expression、derivative_value、partial_derivative_value、definite_integral、limit_value、antiderivative_choice、expression_choice，并且必须与当前 submodule 的实际任务匹配。表达式用安全 ASCII 写法，如 x**2、sin(x)、log(x)。\n"
            "6. verification_spec.options 必须含 A-D，每项 source_text 与显示选项逐字一致；数值型填 value，表达式型填 expression。只有声明答案能通过复算。\n"
            "7. 三个错项逐项说明漏负号、漏系数、公式误用、上下限错误、链式法则错误等具体来源。"
        )
    return ""


def subject_v2_output_schema(subject: str) -> str | None:
    if subject == CULTURE_SUBJECT:
        return (
            '{"questions":[{"stem":"题干","option_a":"A选项","option_b":"B选项","option_c":"C选项",'
            '"option_d":"D选项","answer":"A","subject":"中华文化","module":"模块",'
            '"submodule":"考点","difficulty":2,"culture_v3":{"version":"3.0",'
            '"question_form":"direct_identification","reasoning_mode":"direct_fact",'
            '"fact_anchor":{"subject":"事实对象","relation":"对应关系","object":"A选项原文"},'
            '"reasoning_steps":{"clue":"题干中的关键线索","bridge":"能解释线索与答案关系的具体事实","conclusion":"因此选 A‘选项原文’"},'
            '"evidence_excerpt":"可核对的具体事实句","knowledge_extension":"与解题事实不同的独立复习知识",'
            '"memory_strategy":"none","memory_hook":"",'
            '"option_analysis":{'
            '"A":{"verdict":"correct","fact":"A项对应的真实知识","fit":"该事实直接回应题干线索"},'
            '"B":{"verdict":"incorrect","fact":"B项实际对应的真实知识","fit":"其对象或关系与题干不同"},'
            '"C":{"verdict":"incorrect","fact":"C项实际对应的真实知识","fit":"其对象或关系与题干不同"},'
            '"D":{"verdict":"incorrect","fact":"D项实际对应的真实知识","fit":"其对象或关系与题干不同"}},'
            '"scope_level":"core","controversy_status":"stable","verification_status":"cross_checked",'
            '"difficulty_features":["难度来源"]}}]}'
        )
    if subject == ENGLISH_SUBJECT:
        return (
            '{"questions":[{"stem":"English ____ sentence.","option_a":"A option","option_b":"B option",'
            '"option_c":"C option","option_d":"D option","answer":"A","explanation":"中文解析",'
            '"subject":"英语运用","module":"语言知识","submodule":"词汇或语法或语用","difficulty":2,'
            '"english_v2":{"version":"2.0","skill":"vocabulary或grammar或pragmatics",'
            '"completed_sentence":"填入A选项后的完整英文句子","answer_rationale":"答案依据",'
            '"distractor_errors":{"B":"具体陷阱","C":"具体陷阱","D":"具体陷阱"},'
            '"verification_checks":{"unique_answer":true,"grammar":true,"collocation":true,"context_natural":true},'
            '"verification_status":"cross_checked","difficulty_features":["难度来源"]}}]}'
        )
    if subject == MATH_SUBJECT:
        return (
            '{"questions":[{"stem":"含\\\\(...\\\\)的题干","option_a":"\\\\(1\\\\)","option_b":"\\\\(2\\\\)",'
            '"option_c":"\\\\(3\\\\)","option_d":"\\\\(4\\\\)","answer":"A",'
            '"explanation":"解题思路：...关键公式：...推导过程：...答案理由：...易错点：...",'
            '"subject":"数学基础","module":"允许模块","submodule":"允许考点","difficulty":2,'
            '"math_v2":{"version":"2.0","problem_family":"题型","givens":["已知"],"required":"求解目标",'
            '"solution_method":"方法","source_expression":"题干中逐字公式片段","verification_status":"locally_verified",'
            '"verification_spec":{"kind":"numeric_expression","expression":"1+0","variables":{},"tolerance":0.0001,'
            '"options":{"A":{"source_text":"\\\\(1\\\\)","value":"1"},"B":{"source_text":"\\\\(2\\\\)","value":"2"},'
            '"C":{"source_text":"\\\\(3\\\\)","value":"3"},"D":{"source_text":"\\\\(4\\\\)","value":"4"}}},'
            '"distractor_errors":{"B":"具体错因","C":"具体错因","D":"具体错因"},"difficulty_features":["难度来源"]}}]}'
        )
    return None
