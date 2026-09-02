"""Explanation-only regeneration for existing Chinese-culture questions.

The online question generator creates a complete question.  Existing-bank
repair has a narrower trust boundary: the stem, options, declared answer and
classification are immutable, and the model may only return the structured
``culture_v3`` teaching contract.  This module owns that boundary so batch
scripts do not silently accept question rewrites while improving explanations.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence

from app.services.ai_client import call_deepseek_chat
from app.services.culture_explanation_v3 import (
    culture_memory_strategy_requirement,
    infer_culture_reasoning_mode,
    render_culture_explanation_v3,
)
from app.services.subject_question_quality import audit_culture_question


MAX_REGENERATION_BATCH_SIZE = 6
OPTION_FIELDS = ("option_a", "option_b", "option_c", "option_d")
IMMUTABLE_MODEL_FIELDS = {
    "module",
    "submodule",
    "stem",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "answer",
    "difficulty",
}


def _text(value: object, max_length: int = 4000) -> str:
    return str(value or "").strip()[:max_length]


def _extract_json_object(content: str) -> dict:
    text = _text(content, 200_000)
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("regeneration response does not contain a JSON object")
    payload = json.loads(text[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("regeneration response root must be an object")
    return payload


def _candidate_payload(row: Mapping[str, object]) -> dict[str, object]:
    stem = _text(row.get("stem"), 2000)
    negative = bool(
        re.search(
            r"不正确|不属于|不包括|并非|错误|有误|不当|不同的是|不相同|例外|无关",
            stem,
        )
    )
    if negative:
        expected_form = "odd_one_out" if re.search(r"不同|不相同", stem) else "negative_identification"
        display_budget = 395 if expected_form == "negative_identification" else 410
    else:
        expected_form = (
            "relationship_match"
            if re.search(r"关系|关联|对应|共同|相同|最密切|分别是|搭配", stem)
            else "direct_identification"
        )
        display_budget = 350 if expected_form == "relationship_match" else 330
    expected_reasoning_mode = infer_culture_reasoning_mode(row)
    required_memory_strategy = culture_memory_strategy_requirement(
        row,
        {"reasoning_mode": expected_reasoning_mode},
    )
    return {
        "id": _text(row.get("id"), 80),
        "module": _text(row.get("module"), 80),
        "submodule": _text(row.get("submodule"), 80),
        "stem": stem,
        "option_a": _text(row.get("option_a"), 800),
        "option_b": _text(row.get("option_b"), 800),
        "option_c": _text(row.get("option_c"), 800),
        "option_d": _text(row.get("option_d"), 800),
        "answer": _text(row.get("answer"), 8).upper(),
        "difficulty": row.get("difficulty"),
        "v3_generation_hints": {
            "expected_question_form": expected_form,
            "expected_reasoning_mode": expected_reasoning_mode,
            "memory_strategy_requirement": required_memory_strategy or "optional",
            "rendered_display_budget": display_budget,
            "field_budgets": {
                "clue": "3-14字",
                "bridge": "18-42字；人物事件题可到48字",
                "conclusion": "6-24字",
                "evidence_excerpt": "12-45字",
                "knowledge_extension": "10-28字",
                "option_fact": "7-22字",
                "option_fit": "5-14字",
                "memory_hook": "required 时8-28字；optional 且无增量价值时留空",
            },
        },
    }


def build_culture_explanation_regeneration_messages(
    rows: Sequence[Mapping[str, object]],
    *,
    feedback_by_id: Mapping[str, Sequence[str]] | None = None,
) -> list[dict[str, str]]:
    """Build an explanation-only prompt for a small immutable batch."""

    if not rows:
        raise ValueError("at least one culture question is required")
    if len(rows) > MAX_REGENERATION_BATCH_SIZE:
        raise ValueError(f"one regeneration batch may contain at most {MAX_REGENERATION_BATCH_SIZE} questions")

    candidates = [_candidate_payload(row) for row in rows]
    if any(not item["id"] for item in candidates):
        raise ValueError("every culture question must have an id")
    if len({str(item["id"]) for item in candidates}) != len(candidates):
        raise ValueError("culture question ids must be unique within a batch")

    candidate_ids = {str(item["id"]) for item in candidates}
    feedback_payload: dict[str, list[str]] = {}
    for question_id, messages in (feedback_by_id or {}).items():
        cleaned_id = _text(question_id, 80)
        if not cleaned_id or cleaned_id not in candidate_ids:
            continue
        cleaned = [_text(message, 240) for message in messages if _text(message, 240)]
        if cleaned:
            feedback_payload[cleaned_id] = cleaned[:10]

    output_schema = {
        "updates": [
            {
                "id": "必须原样返回输入 id",
                "culture_v3": {
                    "version": "3.0",
                    "question_form": "direct_identification",
                    "reasoning_mode": "direct_fact",
                    "fact_anchor": {
                        "subject": "题干事实对象",
                        "relation": "设问关系",
                        "object": "正确选项原文",
                    },
                    "reasoning_steps": {
                        "clue": "题干关键线索",
                        "bridge": "补足线索和答案之间的具体文化事实",
                        "conclusion": "因此选 A“正确选项原文”",
                    },
                    "evidence_excerpt": "可单独核对的完整事实句",
                    "knowledge_extension": "围绕本题扩展、但不重复 bridge 的复习事实",
                    "memory_strategy": "keyword、contrast、chain 或 none",
                    "memory_hook": "有增量价值的短记忆抓手；none 时为空字符串",
                    "option_analysis": {
                        "A": {"verdict": "correct", "fact": "包含 A 项对象的事实", "fit": "具体符合或错配边界"},
                        "B": {"verdict": "incorrect", "fact": "包含 B 项对象的事实", "fit": "具体符合或错配边界"},
                        "C": {"verdict": "incorrect", "fact": "包含 C 项对象的事实", "fit": "具体符合或错配边界"},
                        "D": {"verdict": "incorrect", "fact": "包含 D 项对象的事实", "fit": "具体符合或错配边界"},
                    },
                    "scope_level": "core",
                    "controversy_status": "stable",
                    "verification_status": "cross_checked",
                    "difficulty_features": ["本题真正的辨析难点"],
                },
            }
        ]
    }

    return [
        {
            "role": "system",
            "content": (
                "你是港澳台考研中华文化题目的解析老师。本任务只重写现有题的教学解析，"
                "不得改题、改选项、改答案、改分类或改难度。只输出合法 JSON，不要输出 Markdown、"
                "代码块、前言或总结。每个输入 id 必须恰好返回一次，update 对象只能包含 id 和 culture_v3。"
                "宁可让事实不足的候选在后续质量门被拒收，也不要用套话、常识猜测或答案复述补齐。"
            ),
        },
        {
            "role": "user",
            "content": (
                "为以下固定题目重新生成 culture_v3 教学解析。\n"
                "生成规则：\n"
                "1. reasoning_steps 必须按‘题干线索→具体中间事实→答案结论’组织。bridge 要解释为什么，"
                "禁止只写‘X 对应 Y’‘典型特征是’‘创作时期是’或把答案换一种说法。\n"
                "2. 人物事件影响题必须写出至少两个有先后或因果关系的实际动作；年代、地点、作品、"
                "概念和制度题必须写清对应关系成立的具体依据。\n"
                "3. bridge、evidence_excerpt 和知识点都要点名对象，不能以‘他’‘该书’‘这句诗’开头；"
                "不得保留资料问句、OCR 粘连、截断句、审核话术或未经核实的最高级表述。\n"
                "4. 逆向题的 clue 必须保留‘不正确/不属于/不同项/例外’等方向词；evidence_excerpt "
                "必须同时支撑 bridge、点名被纠正选项的核心对象，并明确写出‘不在/不属于/并非/而非/不同’等纠偏边界，"
                "不得把错误选项本身当成证据。\n"
                "5. option_analysis 覆盖 A-D。每个 fact 必须出现本选项对象，并说明它真实对应的知识；"
                "fit 再指出与题干的具体符合或错配维度。三个错项不得复制同一种句式。\n"
                "6. knowledge_extension 只扩展一个独立、可复习的事实，不复制 bridge 或任一选项事实。"
                "记忆方法先做价值判定：固定日期或短触发词用 keyword；至少两组同维度易混映射用 contrast；"
                "至少三个真实先后、措施或因果节点用 chain；没有增量价值才用 none 且 memory_hook 为空。"
                "禁止牵强谐音、硬凑首字、复述答案或引入未核准事实。\n"
                "7. 内容优先级：准确、清楚、教学价值、简洁。scope_level=core，controversy_status=stable，"
                "verification_status=cross_checked。答案字母只能在 conclusion 和 verdict 中出现。\n"
                "8. 每题必须遵守 v3_generation_hints 中的 expected_question_form、expected_reasoning_mode、"
                "memory_strategy_requirement、rendered_display_budget 和字段字数。memory_strategy_requirement"
                "为 keyword/contrast/chain 时必须使用该策略并填写 memory_hook；为 optional 时仍须独立判断，"
                "有真实增量价值才生成，否则使用 none。总长度按后端渲染后的完整解析计算。\n"
                "9. 每个选项只写一个短事实和一个短边界。正确项 fit 必须用‘直接说明/正是/符合/对应’等词"
                "点明与题干的具体关系；错项 fit 必须用‘人物不同/时代不同/领域不同/并非/不属于’等词"
                "点明具体错配维度，不能只写‘不符’。\n"
                "10. bridge 只写一个完整的中间事实链，题干对象应在句首附近；人物事件题写出两个实际动作，"
                "年代题同时写时间值和出现、形成、生活、成书等时间事件词。避免把多个资料句无标点粘连。\n"
                "11. knowledge_extension 用一句短事实围绕题干对象或正确知识扩展，不另起无关人物，"
                "也不重复 bridge、答案对应或任一选项 fact。\n"
                "12. fact_anchor.subject 必须直接摘取题干中最短且可识别的对象词，优先 2-8 字，"
                "例如‘先考’‘夹纻’‘宜兴紫砂’；不要自行扩写成抽象长句。bridge 和 evidence_excerpt "
                "必须原样点名这个 subject，knowledge_extension 也必须出现 subject 或正确选项对象，"
                "再补一个新的事实，确保三个字段都可被独立锚定。\n"
                "13. 工艺领域题要写‘材料/步骤→形成何种器物部件→所属技术’，例如夹纻以麻布裱贴成胎，"
                "属于漆器胎体制作技术；时代复合项要把两个时期及其发展阶段写全，例如‘宜兴紫砂在明代"
                "成熟并兴盛、清代延续发展’才能推出‘明清’，不得只写‘主要关联明清’。称谓题要分清"
                "追称亡亲与称呼在世亲属。\n"
                "14. 错项 fact 只能陈述选项文字实际表达对象本身的可核对事实，不得擅自添加选项未表达的"
                "地域、时代、对象范围、唯一性或活动边界。例如‘赵国策士议论时局’不得改写成‘其活动局限于"
                "赵国’；如果它相较题干只覆盖局部，应把‘选项表述范围较窄，未覆盖诸国游说’写在 fit，"
                "不能把用于排除的范围推断伪装成 fact 中的史实。\n"
                "15. 时代题必须区分源起、成熟、兴盛和延续，并严格跟随题干所问阶段。题干问‘主要关联时代’"
                "时，应说明最具代表性的成熟或兴盛阶段；对象即使可能存在早期源流，也不得因此武断写成在某代"
                "兴起。宜兴紫砂优先表述为‘明代成熟并兴盛、清代延续发展’，不要把早期源流、成熟定型与后续"
                "发展混写成同一个时间结论。\n"
                f"上一轮静态门拒收反馈：{json.dumps(feedback_payload, ensure_ascii=False, separators=(',', ':'))}\n"
                f"固定题目：{json.dumps(candidates, ensure_ascii=False, separators=(',', ':'))}\n"
                f"固定输出结构：{json.dumps(output_schema, ensure_ascii=False, separators=(',', ':'))}"
            ),
        },
    ]


def parse_culture_explanation_regeneration_response(
    content: str,
    questions_by_id: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    """Parse, render and statically audit a model regeneration response."""

    payload = _extract_json_object(content)
    extra_root_fields = sorted(set(payload) - {"updates"})
    if extra_root_fields:
        raise ValueError(
            "regeneration response root 只能包含 updates，出现额外字段："
            + "、".join(extra_root_fields)
        )
    raw_updates = payload.get("updates")
    if not isinstance(raw_updates, list):
        raise ValueError("regeneration response is missing updates array")

    normalized_questions_by_id: dict[str, Mapping[str, object]] = {}
    for raw_id, question in questions_by_id.items():
        normalized_id = _text(raw_id, 80)
        if not normalized_id:
            raise ValueError("questions_by_id contains an empty id")
        if normalized_id in normalized_questions_by_id:
            raise ValueError("questions_by_id contains ids that collide after normalization")
        normalized_questions_by_id[normalized_id] = question
    expected_ids = set(normalized_questions_by_id)
    accepted: list[dict[str, object]] = []
    rejected: list[dict[str, object]] = []
    seen: set[str] = set()
    response_id_counts = Counter(
        _text(raw.get("id"), 80)
        for raw in raw_updates
        if isinstance(raw, Mapping) and _text(raw.get("id"), 80) in expected_ids
    )
    duplicate_ids = {question_id for question_id, count in response_id_counts.items() if count > 1}

    for position, raw in enumerate(raw_updates, start=1):
        if not isinstance(raw, Mapping):
            rejected.append(
                {
                    "id": "",
                    "position": position,
                    "codes": ["regeneration_update_not_object"],
                    "reasons": ["update 必须是 JSON 对象"],
                }
            )
            continue

        question_id = _text(raw.get("id"), 80)
        if not question_id or question_id not in expected_ids:
            rejected.append(
                {
                    "id": question_id,
                    "position": position,
                    "codes": ["regeneration_unknown_id"],
                    "reasons": ["update id 不在本批固定题目中"],
                }
            )
            continue
        if question_id in duplicate_ids:
            if question_id not in seen:
                rejected.append(
                    {
                        "id": question_id,
                        "position": position,
                        "codes": ["regeneration_duplicate_id"],
                        "reasons": ["同一 id 在响应中重复出现，所有重复版本均已拒收"],
                    }
                )
            seen.add(question_id)
            continue
        if question_id in seen:
            rejected.append(
                {
                    "id": question_id,
                    "position": position,
                    "codes": ["regeneration_duplicate_id"],
                    "reasons": ["同一 id 在响应中重复出现"],
                }
            )
            continue
        seen.add(question_id)

        extra_fields = sorted(set(raw) - {"id", "culture_v3"})
        if extra_fields or IMMUTABLE_MODEL_FIELDS & set(raw):
            rejected.append(
                {
                    "id": question_id,
                    "position": position,
                    "codes": ["regeneration_attempted_question_mutation"],
                    "reasons": [f"update 只能包含 id 和 culture_v3，出现额外字段：{'、'.join(extra_fields)}"],
                }
            )
            continue

        metadata = raw.get("culture_v3")
        if not isinstance(metadata, Mapping):
            rejected.append(
                {
                    "id": question_id,
                    "position": position,
                    "codes": ["regeneration_missing_culture_v3"],
                    "reasons": ["update 缺少 culture_v3 对象"],
                }
            )
            continue

        question = dict(normalized_questions_by_id[question_id])
        try:
            question["explanation"] = render_culture_explanation_v3(question, metadata)
        except ValueError as exc:
            rejected.append(
                {
                    "id": question_id,
                    "position": position,
                    "codes": ["regeneration_render_failed"],
                    "reasons": [str(exc)],
                    "culture_v3": dict(metadata),
                }
            )
            continue

        audit = audit_culture_question(question, metadata=metadata, require_v2_metadata=True)
        blocking_issues = [
            issue
            for issue in audit.get("issues", [])
            if issue.get("severity") in {"critical", "high"}
        ]
        if blocking_issues or not audit.get("valid_for_generation"):
            rejected.append(
                {
                    "id": question_id,
                    "position": position,
                    "codes": [str(issue.get("code") or "culture_v3_static_gate") for issue in blocking_issues],
                    "reasons": [str(issue.get("message") or "静态质量门未通过") for issue in blocking_issues],
                    "audit": audit,
                    "culture_v3": dict(metadata),
                }
            )
            continue

        accepted.append(
            {
                "id": question_id,
                "question": question,
                "culture_v3": dict(metadata),
                "audit": audit,
            }
        )

    for question_id in sorted(expected_ids - seen):
        rejected.append(
            {
                "id": question_id,
                "position": None,
                "codes": ["regeneration_missing_id"],
                "reasons": ["模型没有返回该固定题目的解析"],
            }
        )

    return {
        "accepted": accepted,
        "rejected": rejected,
        "response_count": len(raw_updates),
        "expected_count": len(expected_ids),
        "raw": payload,
    }


def feedback_by_id_from_rejections(rejected: Sequence[Mapping[str, object]]) -> dict[str, list[str]]:
    """Convert deterministic gate failures into compact retry feedback."""

    feedback: dict[str, list[str]] = {}
    for item in rejected:
        question_id = _text(item.get("id"), 80)
        reasons = item.get("reasons")
        if not question_id or not isinstance(reasons, Sequence) or isinstance(reasons, (str, bytes)):
            continue
        cleaned = [_text(reason, 240) for reason in reasons if _text(reason, 240)]
        if cleaned:
            bucket = feedback.setdefault(question_id, [])
            for reason in cleaned:
                if reason not in bucket:
                    bucket.append(reason)
                if len(bucket) >= 10:
                    break
    return feedback


async def regenerate_culture_explanation_batch(
    rows: Sequence[Mapping[str, object]],
    *,
    feedback_by_id: Mapping[str, Sequence[str]] | None = None,
) -> dict[str, object]:
    """Call the configured model once, then apply the deterministic V3 gate."""

    result = await call_deepseek_chat(
        build_culture_explanation_regeneration_messages(rows, feedback_by_id=feedback_by_id),
        temperature=0.2,
        max_tokens=max(2400, min(9000, len(rows) * 1450)),
        timeout_seconds=120,
    )
    questions_by_id = {_text(row.get("id"), 80): row for row in rows}
    parsed = parse_culture_explanation_regeneration_response(result["reply"], questions_by_id)
    parsed["model"] = result.get("model")
    return parsed
