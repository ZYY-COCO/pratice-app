import json
import re
from datetime import datetime, timezone
from uuid import uuid4

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, status

from app.config import get_settings
from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.ai import (
    AiTrainingGenerateRequest,
    AiTrainingRecommendationResponse,
    AiTrainingSessionResponse,
    AiTrainingSummaryResponse,
    AiTrainingTarget,
    ExplainWrongRequest,
    ExplainWrongResponse,
    QuestionChatRequest,
    QuestionChatResponse,
    SimilarQuestionRequest,
    SimilarQuestionResponse,
    WeaknessAnalysisResponse,
)
from app.services.answers import (
    get_question_or_404,
    has_answer_submission,
    require_answer_disclosure_allowed,
    warm_submission_questions,
)
from app.services.ai_client import call_deepseek_chat
from app.services.culture_explanation_v3 import render_culture_explanation_v3
from app.services.logic_question_quality import (
    LOGIC_SUBJECT,
    audit_logic_question,
    is_canonical_logic_classification,
    normalize_logic_classification,
)
from app.services.question_catalog import normalize_and_validate_question_classification
from app.services.question_generation_review import review_generated_question_rows
from app.services.question_sources import exclude_ai_generated_questions
from app.services.reports import build_ability_item
from app.services.subject_question_quality import (
    CULTURE_SUBJECT,
    ENGLISH_SUBJECT,
    MATH_SUBJECT,
    V2_SUBJECTS,
    audit_subject_question,
    metadata_key_for_subject,
    subject_v2_output_schema,
    subject_v2_prompt_requirement,
)

router = APIRouter(prefix="/ai", tags=["AI"])

DIFFICULTY_LEVELS = {
    "基础巩固": 1,
    "标准提升": 2,
    "强化突破": 3,
    "冲刺挑战": 4,
}

FALLBACK_TARGET = {
    "subject": "逻辑推理",
    "module": "判断",
    "submodule": "判断关系",
    "difficulty": "标准提升",
    "basis": "当前暂无足够作答记录，先从逻辑推理常见薄弱点开始训练。",
}

EXAM_SUBJECTS = {
    "Z001": {"中华文化", "英语运用", "逻辑推理"},
    "Z002": {"中华文化", "英语运用", "数学基础"},
}

SUBJECT_STORAGE_EXAM_CODES = {
    CULTURE_SUBJECT: "COMMON",
    ENGLISH_SUBJECT: "COMMON",
    LOGIC_SUBJECT: "Z001",
    MATH_SUBJECT: "Z002",
}

SUBJECT_ALIASES = {
    "高数": "数学基础",
}

SUBJECT_FALLBACK_TARGETS = {
    "中华文化": {
        "subject": "中华文化",
        "module": "中国文学常识",
        "submodule": "文体流变",
        "difficulty": "标准提升",
        "basis": "当前暂无足够作答记录，先从中华文化高频常识题开始训练。",
    },
    "英语运用": {
        "subject": "英语运用",
        "module": "语言知识",
        "submodule": "词汇",
        "difficulty": "标准提升",
        "basis": "当前暂无足够作答记录，先从英语运用基础语言知识开始训练。",
    },
    "逻辑推理": FALLBACK_TARGET,
    "数学基础": {
        "subject": "数学基础",
        "module": "一元函数微分学",
        "submodule": "极限",
        "difficulty": "标准提升",
        "basis": "当前暂无足够作答记录，先从数学基础题型开始训练。",
    },
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _is_membership_active(profile: dict) -> bool:
    if str(profile.get("membership_status") or "").lower() != "active":
        return False
    expires_at = _parse_datetime(profile.get("membership_expires_at"))
    return not expires_at or expires_at >= datetime.now(timezone.utc)


def _get_profile_or_404(supabase, user_id: str) -> dict:
    response = supabase.table("users").select("*").eq("id", user_id).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户资料不存在")
    return response.data[0]


def _normalize_question_count(value: int) -> int:
    snapped = round(value / 5) * 5
    return min(30, max(5, snapped))


def _normalize_difficulty(value: str | None) -> str:
    if value in DIFFICULTY_LEVELS:
        return value
    return FALLBACK_TARGET["difficulty"]


def _normalize_subject(value: str | None) -> str | None:
    subject = _compact_text(value, 40)
    if not subject:
        return None
    return SUBJECT_ALIASES.get(subject, subject)


def _normalize_subject_for_exam(value: str | None, exam_code: str) -> str | None:
    subject = _normalize_subject(value)
    if not subject:
        return None
    if subject in EXAM_SUBJECTS.get(exam_code, set()):
        return subject
    return None


def _fallback_target_for_subject(subject: str | None, exam_code: str | None = None) -> dict:
    normalized = _normalize_subject(subject)
    if not normalized and exam_code == "Z002":
        normalized = MATH_SUBJECT
    if not normalized and exam_code == "Z001":
        normalized = LOGIC_SUBJECT
    return SUBJECT_FALLBACK_TARGETS.get(normalized or "", FALLBACK_TARGET)


def _difficulty_from_accuracy(accuracy: float | None, wrong_count: int = 0) -> str:
    score = 0 if accuracy is None else float(accuracy)
    if wrong_count >= 5 or score < 45:
        return "基础巩固"
    if score < 65:
        return "标准提升"
    if score < 82:
        return "强化突破"
    return "冲刺挑战"


def _question_count_from_focus(total_count: int = 0, wrong_count: int = 0, accuracy: float | None = None) -> int:
    score = 0 if accuracy is None else float(accuracy)
    if wrong_count >= 15 or (total_count >= 50 and score < 75):
        return 20
    if wrong_count >= 8 or (total_count >= 20 and score < 60):
        return 15
    return 10


def _compact_text(value: object, max_length: int = 2000) -> str:
    text = str(value or "").strip()
    return text[:max_length]


def _question_fingerprint(stem: object) -> str:
    text = _compact_text(stem, 400)
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[^\w\u4e00-\u9fff]", "", text, flags=re.UNICODE)
    return text.lower()[:180]


def _extract_json_object(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("DeepSeek did not return a JSON object")
    return json.loads(text[start : end + 1])


def _safe_question_row(raw: dict, target: AiTrainingTarget, exam_code: str) -> dict | None:
    row, _ = _safe_question_candidate(raw, target, exam_code)
    return row


def _safe_question_candidate(
    raw: dict,
    target: AiTrainingTarget,
    exam_code: str,
) -> tuple[dict | None, list[str]]:
    rejection_reasons: list[str] = []
    answer = _compact_text(raw.get("answer"), 8).upper()
    if answer not in {"A", "B", "C", "D"}:
        return None, ["answer 必须为 A、B、C、D 之一"]

    subject = _compact_text(raw.get("subject") or target.subject, 80)
    module = _compact_text(raw.get("module") or target.module, 80)
    submodule = _compact_text(raw.get("submodule") or target.submodule, 80)
    if target.subject == LOGIC_SUBJECT:
        target_module, target_submodule = normalize_logic_classification(target.module, target.submodule)
        module, submodule = normalize_logic_classification(module, submodule)
    else:
        target_module, target_submodule = target.module, target.submodule

    if subject != target.subject:
        rejection_reasons.append(f"生成题 subject {subject} 偏离目标 {target.subject}")
    if (module, submodule) != (target_module, target_submodule):
        rejection_reasons.append(
            f"生成题分类 {module}/{submodule} 偏离目标 {target_module}/{target_submodule}"
        )
    subject = target.subject
    module = target_module
    submodule = target_submodule

    storage_exam_code = SUBJECT_STORAGE_EXAM_CODES.get(subject, exam_code)
    try:
        normalized_classification = normalize_and_validate_question_classification(
            exam_code=storage_exam_code,
            subject=subject,
            module=module,
            submodule=submodule,
        )
        module = normalized_classification["module"]
        submodule = normalized_classification["submodule"]
    except ValueError as exc:
        rejection_reasons.append(str(exc))

    try:
        difficulty = int(raw.get("difficulty") or DIFFICULTY_LEVELS[target.difficulty])
    except (TypeError, ValueError):
        return None, ["difficulty 必须为 1-5 的整数"]

    row = {
        "exam_code": storage_exam_code,
        "subject": subject,
        "module": module,
        "submodule": submodule,
        "question_type": "single_choice",
        "stem": _compact_text(raw.get("stem"), 2000),
        "option_a": _compact_text(raw.get("option_a"), 800),
        "option_b": _compact_text(raw.get("option_b"), 800),
        "option_c": _compact_text(raw.get("option_c"), 800),
        "option_d": _compact_text(raw.get("option_d"), 800),
        "answer": answer,
        "explanation": _compact_text(raw.get("explanation"), 2000),
        "difficulty": difficulty,
        "source_type": "ai_deepseek",
        "source_year": datetime.now(timezone.utc).year,
        "passage_id": None,
    }

    # Culture V3 has one source of truth: the model returns structured teaching
    # fields and the backend renders the existing ExplanationPanel labels.
    # Legacy culture_v2 candidates keep their supplied display copy during the
    # compatibility window.
    culture_v3 = raw.get("culture_v3") if target.subject == CULTURE_SUBJECT else None
    if isinstance(culture_v3, dict):
        try:
            row["explanation"] = render_culture_explanation_v3(row, culture_v3)
        except ValueError as exc:
            return None, [f"culture_v3 渲染失败：{exc}"]

    required_fields = ["subject", "module", "submodule", "stem", "option_a", "option_b", "option_c", "option_d", "explanation"]
    if any(not row[field] for field in required_fields):
        return None, ["题干、A-D 选项、解析和分类字段必须完整"]
    row["difficulty"] = min(5, max(1, row["difficulty"]))

    if target.subject == LOGIC_SUBJECT:
        quality = audit_logic_question(
            row,
            metadata=raw.get("logic_v2"),
            require_v2_metadata=True,
            require_context_coherence=True,
        )
        rejection_reasons.extend(issue["message"] for issue in quality["issues"] if issue["severity"] in {"critical", "high"})
        if rejection_reasons or not quality["valid_for_generation"]:
            return None, rejection_reasons[:8]
        row["module"] = quality["canonical_module"]
        row["submodule"] = quality["canonical_submodule"]
    elif target.subject in V2_SUBJECTS:
        metadata_key = metadata_key_for_subject(target.subject)
        subject_metadata = raw.get(metadata_key) if metadata_key else None
        if target.subject == CULTURE_SUBJECT and subject_metadata is None:
            subject_metadata = raw.get("culture_v2")
            if subject_metadata is None:
                return None, ["中华文化题必须提供 culture_v3 教学契约"]
        quality = audit_subject_question(
            row,
            metadata=subject_metadata,
            require_v2_metadata=True,
        )
        rejection_reasons.extend(
            issue["message"]
            for issue in quality["issues"]
            if issue["severity"] in {"critical", "high"}
        )
        if rejection_reasons or not quality["valid_for_generation"]:
            return None, rejection_reasons[:8]

    return row, []


def _hide_answer(question: dict) -> dict:
    return {**question, "answer": None, "explanation": None}


def _format_question_options(question: dict) -> str:
    return "\n".join(
        [
            f"A. {_compact_text(question.get('option_a'), 500)}",
            f"B. {_compact_text(question.get('option_b'), 500)}",
            f"C. {_compact_text(question.get('option_c'), 500)}",
            f"D. {_compact_text(question.get('option_d'), 500)}",
        ]
    )


def _build_question_chat_prompt(question: dict, payload: QuestionChatRequest) -> str:
    prompt_parts = [
        "你是港研通 App 的 AI 解题助教，请基于当前题目回答用户问题。",
        f"科目：{question.get('subject')}",
        f"模块：{question.get('module')} / {question.get('submodule')}",
        f"题干：{_compact_text(question.get('stem'), 1600)}",
        f"选项：\n{_format_question_options(question)}",
        f"用户问题：{_compact_text(payload.user_message, 1000)}",
    ]

    if payload.submitted:
        prompt_parts.extend(
            [
                f"用户选择：{_compact_text(payload.user_answer, 8) or '未提供'}",
                f"正确答案：{question.get('answer')}",
                f"题目解析：{_compact_text(question.get('explanation'), 1800)}",
            ]
        )
    else:
        prompt_parts.append("用户尚未提交答案，只能给思路、考点和排除方向，不能透露正确答案或原解析。")

    return "\n".join(prompt_parts)


def _build_question_chat_messages(question: dict, payload: QuestionChatRequest) -> list[dict[str, str]]:
    guardrail = (
        "用户尚未提交答案。禁止直接或变相透露正确答案、答案字母、原题解析。"
        "只能给解题思路、知识点提醒、审题方向和排除法角度。"
        if not payload.submitted
        else (
            "用户已经提交答案。可以解释正确答案、用户选择的可能错误原因、"
            "每个选项含义或差异，以及同类题判断方法。"
        )
    )

    return [
        {
            "role": "system",
            "content": (
                "你是“港研通 AI 助教”，服务港澳台考研 App 用户。"
                "请使用简体中文回答，表达清楚，适合大学生备考理解。"
                "回答要围绕当前题目，不要过度冗长，不要编造真题来源，"
                "不要使用 Markdown 标题、粗体、表格或代码块；分点请用普通的“1. 2. 3.”。"
                "数学公式必须使用标准 LaTeX 行内格式 \\(...\\)，例如 \\(\\lim_{x\\to\\infty} y\\)、\\(\\frac{a}{b}\\)。"
                "不要直接输出未包裹的 \\frac、\\lim、\\partial 等公式命令。"
                "不要承诺一定提分。"
            ),
        },
        {
            "role": "user",
            "content": f"{guardrail}\n\n{_build_question_chat_prompt(question, payload)}",
        },
    ]


def _build_question_chat_fallback_reply(question: dict, payload: QuestionChatRequest) -> str:
    knowledge_point = f"{question.get('subject') or '当前科目'} / {question.get('module') or '当前模块'} / {question.get('submodule') or '当前考点'}"
    user_message = _compact_text(payload.user_message, 80)

    if not payload.submitted:
        return (
            f"我先给你思路，不直接透露答案。\n"
            f"1. 先判断考点：这题属于 {knowledge_point}。\n"
            f"2. 根据题干关键词和选项类型，先回忆对应定义、公式或典型判断方法。\n"
            f"3. 如果是计算题，先写出核心公式，再代入化简；如果是常识或逻辑题，先排除与题干对象、时代、概念不匹配的选项。\n"
            f"4. 你的问题是“{user_message}”，建议先从题干中的限定词和选项差异入手。"
        )

    explanation = _compact_text(question.get("explanation"), 900) or "本题暂未提供详细解析。"
    selected = _compact_text(payload.user_answer, 8) or "未提供"
    return (
        f"这题可以这样看：\n"
        f"1. 考点：{knowledge_point}。\n"
        f"2. 你的选择：{selected}；正确答案：{question.get('answer') or '未标明'}。\n"
        f"3. 核心依据：{explanation}\n"
        f"4. 复盘建议：先把题干限定条件圈出来，再逐项核对选项与考点是否匹配；同类题不要只凭印象选，要看搭配、公式、时代或概念边界。"
    )


def _candidate_key(row: dict) -> tuple[str, str, str]:
    subject = str(row.get("subject") or FALLBACK_TARGET["subject"])
    module = str(row.get("module") or FALLBACK_TARGET["module"])
    submodule = str(row.get("submodule") or FALLBACK_TARGET["submodule"])
    if subject == LOGIC_SUBJECT:
        module, submodule = normalize_logic_classification(module, submodule)
    return subject, module, submodule


def _canonicalize_logic_target(target: AiTrainingTarget) -> AiTrainingTarget:
    if target.subject != LOGIC_SUBJECT:
        return target
    module, submodule = normalize_logic_classification(target.module, target.submodule)
    if not is_canonical_logic_classification(module, submodule):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"逻辑推理分类不在 V2 目录中：{target.module} / {target.submodule}",
        )
    return target.model_copy(update={"module": module, "submodule": submodule})


def _canonicalize_generation_target(target: AiTrainingTarget, exam_code: str) -> AiTrainingTarget:
    if target.subject not in EXAM_SUBJECTS.get(exam_code, set()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{exam_code} 不支持 AI 生成科目：{target.subject}",
        )

    normalized_target = _canonicalize_logic_target(target)
    storage_exam_code = SUBJECT_STORAGE_EXAM_CODES.get(normalized_target.subject, exam_code)
    try:
        classification = normalize_and_validate_question_classification(
            exam_code=storage_exam_code,
            subject=normalized_target.subject,
            module=normalized_target.module,
            submodule=normalized_target.submodule,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return normalized_target.model_copy(
        update={
            "module": classification["module"],
            "submodule": classification["submodule"],
        }
    )


def _build_smart_target(
    supabase,
    user_id: str,
    profile: dict,
    exam_code: str,
    preferred_question_count: int | None = None,
    subject_filter: str | None = None,
) -> tuple[AiTrainingTarget, dict]:
    candidates: dict[tuple[str, str, str], dict] = {}

    try:
        ability_query = (
            supabase.table("ability_stats")
            .select("*")
            .eq("user_id", user_id)
            .in_("exam_code", [exam_code, "COMMON"])
            .gt("total_count", 0)
        )
        if subject_filter:
            ability_query = ability_query.eq("subject", subject_filter)
        ability_response = ability_query.order("accuracy").order("total_count", desc=True).limit(20).execute()
    except Exception:
        ability_response = None

    for row in ability_response.data if ability_response else []:
        key = _candidate_key(row)
        total_count = int(row.get("total_count") or 0)
        correct_count = int(row.get("correct_count") or 0)
        accuracy = float(row.get("accuracy") or 0)
        candidates[key] = {
            "subject": key[0],
            "module": key[1],
            "submodule": key[2],
            "total_count": total_count,
            "correct_count": correct_count,
            "accuracy": accuracy,
            "wrong_count": max(0, total_count - correct_count),
            "score": (100 - accuracy) * 2 + min(total_count, 40),
            "source": "ability_stats",
        }

    try:
        wrong_response = (
            supabase.table("wrong_questions")
            .select("wrong_count, questions(exam_code, subject, module, submodule, stem)")
            .eq("user_id", user_id)
            .order("last_wrong_at", desc=True)
            .limit(40)
            .execute()
        )
    except Exception:
        wrong_response = None

    for row in wrong_response.data if wrong_response else []:
        question = row.get("questions") or {}
        if question.get("exam_code") not in {exam_code, "COMMON", None}:
            continue
        if subject_filter and question.get("subject") != subject_filter:
            continue
        key = _candidate_key(question)
        wrong_count = int(row.get("wrong_count") or 1)
        current = candidates.get(
            key,
            {
                "subject": key[0],
                "module": key[1],
                "submodule": key[2],
                "total_count": 0,
                "correct_count": 0,
                "accuracy": None,
                "wrong_count": 0,
                "score": 80,
                "source": "wrong_questions",
            },
        )
        current["wrong_count"] = int(current.get("wrong_count") or 0) + wrong_count
        current["score"] = float(current.get("score") or 0) + wrong_count * 16
        candidates[key] = current

    if not candidates:
        question_count = _normalize_question_count(preferred_question_count or 10)
        fallback = _fallback_target_for_subject(subject_filter, exam_code)
        target = AiTrainingTarget(
            subject=fallback["subject"],
            module=fallback["module"],
            submodule=fallback["submodule"],
            difficulty=fallback["difficulty"],
            question_count=question_count,
            basis=fallback["basis"],
        )
        return _canonicalize_generation_target(target, exam_code), {
            "source": "fallback",
            "reason": "no_answer_history",
            "subject_filter": subject_filter,
        }

    chosen = max(
        candidates.values(),
        key=lambda item: (
            float(item.get("score") or 0),
            int(item.get("wrong_count") or 0),
            -float(item.get("accuracy") if item.get("accuracy") is not None else 100),
        ),
    )
    accuracy = chosen.get("accuracy")
    wrong_count = int(chosen.get("wrong_count") or 0)
    total_count = int(chosen.get("total_count") or 0)
    question_count = _normalize_question_count(
        preferred_question_count or _question_count_from_focus(total_count, wrong_count, accuracy)
    )
    difficulty = _difficulty_from_accuracy(accuracy, wrong_count)

    if accuracy is None:
        basis = f"近期 {chosen['submodule']} 错题出现 {wrong_count} 次，优先做同类加练。"
    else:
        basis = (
            f"{chosen['submodule']} 已做 {total_count} 题，正确率约 {round(float(accuracy))}%，"
            f"累计错题 {wrong_count} 次，优先巩固同类题目。"
        )

    target = AiTrainingTarget(
        subject=chosen["subject"],
        module=chosen["module"],
        submodule=chosen["submodule"],
        difficulty=difficulty,
        question_count=question_count,
        basis=basis,
    )
    return _canonicalize_generation_target(target, exam_code), {
        "source": chosen.get("source"),
        "total_count": total_count,
        "correct_count": int(chosen.get("correct_count") or 0),
        "wrong_count": wrong_count,
        "accuracy": accuracy,
    }


def _build_target(supabase, user_id: str, profile: dict, payload: AiTrainingGenerateRequest) -> AiTrainingTarget:
    question_count = _normalize_question_count(payload.question_count)
    difficulty = _normalize_difficulty(payload.difficulty)
    exam_code = payload.exam_code or profile.get("exam_target") or "Z001"
    if exam_code not in EXAM_SUBJECTS:
        exam_code = "Z001"
    subject_filter = _normalize_subject_for_exam(payload.subject, exam_code)
    fallback = _fallback_target_for_subject(subject_filter, exam_code)

    if not payload.smart_mode:
        return _canonicalize_generation_target(
            AiTrainingTarget(
                subject=subject_filter or fallback["subject"],
                module=payload.module or fallback["module"],
                submodule=payload.submodule or fallback["submodule"],
                difficulty=difficulty,
                question_count=question_count,
                basis="用户手动选择训练范围和题量。",
            ),
            exam_code,
        )

    preferred_count = question_count if "question_count" in payload.model_fields_set else None
    target, _ = _build_smart_target(supabase, user_id, profile, exam_code, preferred_count, subject_filter)
    return _canonicalize_generation_target(target, exam_code)


def _build_context_snippets(
    supabase,
    user_id: str,
    exam_code: str | None = None,
    subject_filter: str | None = None,
) -> list[str]:
    try:
        response = (
            supabase.table("wrong_questions")
            .select("wrong_count, questions(stem, subject, module, submodule)")
            .eq("user_id", user_id)
            .order("last_wrong_at", desc=True)
            .limit(5)
            .execute()
        )
    except Exception:
        return []

    snippets: list[str] = []
    for row in response.data or []:
        question = row.get("questions") or {}
        if exam_code and question.get("exam_code") not in {exam_code, "COMMON", None}:
            continue
        if subject_filter and question.get("subject") != subject_filter:
            continue
        stem = _compact_text(question.get("stem"), 180)
        if stem:
            snippets.append(
                f"- {question.get('subject')} / {question.get('module')} / {question.get('submodule')}：{stem}"
            )
    return snippets


def _logic_v2_prompt_requirement(target: AiTrainingTarget) -> str:
    if target.subject != LOGIC_SUBJECT:
        return ""
    return (
        "\n逻辑推理 V2 专项要求：\n"
        "1. 先确定母题 logic_model 和设问 question_task，再写自然语言题目。"
        "不得用概念识记题冒充综合推理题。\n"
        "2. 可用 question_task 包括 must_be_true、could_be_true、cannot_be_true、"
        "must_be_false、could_be_false、strengthen、weaken、assumption、explain、"
        "parallel_reasoning、flaw。\n"
        "3. 每个错项都要在 distractor_types 中写明错误机制，并在 counterexamples 中"
        "给出反例或说明为什么不是最佳答案；不能只写‘错误项’。\n"
        "4. 条件、分配、排序、分组、排班、方阵、符号匹配等结构题必须提供 formal_spec，"
        "verification_status 固定为 solver_verified。formal_spec 使用有限域：domains 为变量到"
        "候选值数组；constraints 和 options 中每项都包含 source_text 与 expr；task 与"
        "question_task 一致。expr 支持 eq、neq、lt、le、gt、ge、in、not_in、and、or、not、"
        "implies、iff、xor、all_different、before、adjacent、count、truthy。变量引用写成"
        "{\"var\":\"变量名\"}。每条 constraint 的 source_text 必须逐字出现在题干中，"
        "每个 option 的 source_text 必须与对应选项一致。\n"
        "5. 加强、削弱、假设、解释、形式相似和谬误题的 formal_spec 填 null，"
        "verification_status 固定为 rubric_verified；premise_form 要写清结论、论据和缺口。\n"
        "6. 解析必须说明正确项的作用，并具体排除至少两个错项。不得出现批次、AI、生成、"
        "复盘报告、学习报告、测评记录或讲义来源等命题过程字样。\n"
        "7. 结构题的场景、对象和动作必须属于同一工作语境；分组题只能用甲乙丙丁等成员名，"
        "不能把流程动作当成员。涉及人数的‘至少/至多/恰有’表述必须与 formal_spec.count 的比较符一致。\n"
        "8. logic_v2 必须包含 version、logic_model、question_task、premise_form、variables、"
        "constraints、distractor_types、source_fragment_ids、shared_stem_id、verification_status、"
        "counterexamples、difficulty_features、formal_spec 全部字段。version 固定为 2.0。"
    )


def _logic_v2_output_schema() -> str:
    return (
        '{"questions":[{"stem":"题干","option_a":"A选项","option_b":"B选项",'
        '"option_c":"C选项","option_d":"D选项","answer":"A","explanation":"解析",'
        '"subject":"逻辑推理","module":"模块","submodule":"知识点","difficulty":2,'
        '"logic_v2":{"version":"2.0","logic_model":"母题英文标识",'
        '"question_task":"设问英文标识","premise_form":["标准逻辑形式"],'
        '"variables":["变量"],"constraints":["条件摘要"],'
        '"distractor_types":{"B":"错因","C":"错因","D":"错因"},'
        '"source_fragment_ids":[],"shared_stem_id":null,'
        '"verification_status":"solver_verified或rubric_verified",'
        '"counterexamples":{"B":"反例或排除理由","C":"反例或排除理由","D":"反例或排除理由"},'
        '"difficulty_features":["难度特征"],"formal_spec":null}}]}'
    )


def _build_deepseek_messages(
    target: AiTrainingTarget,
    context_snippets: list[str],
    request_count: int | None = None,
    exclude_stems: list[str] | None = None,
    quality_feedback: list[str] | None = None,
) -> list[dict]:
    context = "\n".join(context_snippets) if context_snippets else "暂无最近错题样例。"
    count = request_count or target.question_count
    exclude_text = "\n".join(f"- {item}" for item in (exclude_stems or []) if item)
    if not exclude_text:
        exclude_text = "无。"
    feedback_text = "\n".join(f"- {item}" for item in (quality_feedback or []) if item)
    if not feedback_text:
        feedback_text = "无。"
    logic_requirement = _logic_v2_prompt_requirement(target)
    subject_requirement = subject_v2_prompt_requirement(target.subject)
    quality_requirement = logic_requirement or subject_requirement
    output_schema = _logic_v2_output_schema() if target.subject == LOGIC_SUBJECT else subject_v2_output_schema(target.subject)
    if not output_schema:
        output_schema = (
            '{"questions":[{"stem":"题干","option_a":"A选项","option_b":"B选项",'
            '"option_c":"C选项","option_d":"D选项","answer":"A","explanation":"解析",'
            '"subject":"科目","module":"模块","submodule":"知识点","difficulty":2}]}'
        )
    return [
        {
            "role": "system",
            "content": (
                "你是港澳台考研刷题 App 的命题老师。请只输出合法 JSON，不要输出 Markdown。"
                "题目必须为单选题，只有 A、B、C、D 四个选项，绝对不要生成 E 选项。"
                "题干、选项、解析必须准确、简洁，贴近港澳台考研初试刷题训练。"
                "同一批题目之间不得重复题干、不得只替换少量词语、不得复用示例题。"
                "错误选项要有考试干扰性，避免一眼排除的无效选项。"
                f"{quality_requirement}"
            ),
        },
        {
            "role": "user",
            "content": (
                f"请生成 {count} 道训练题。\n"
                f"科目：{target.subject}\n"
                f"模块：{target.module}\n"
                f"知识点：{target.submodule}\n"
                f"难度：{target.difficulty}\n"
                f"推荐依据：{target.basis}\n"
                f"最近错题参考：\n{context}\n\n"
                f"以下题干近期已生成或本轮已采用，必须避开：\n{exclude_text}\n\n"
                f"上一轮质量门拒收原因，必须逐条修正：\n{feedback_text}\n\n"
                "输出 JSON 格式必须为："
                f"{output_schema}"
            ),
        },
    ]


async def _call_deepseek(
    target: AiTrainingTarget,
    context_snippets: list[str],
    request_count: int | None = None,
    exclude_stems: list[str] | None = None,
    quality_feedback: list[str] | None = None,
) -> dict:
    settings = get_settings()
    if not settings.deepseek_api_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="DeepSeek API Key 尚未配置")

    url = f"{settings.deepseek_base_url.rstrip('/')}/chat/completions"
    timeout = aiohttp.ClientTimeout(total=settings.deepseek_timeout_seconds)
    body = {
        "model": settings.deepseek_model,
        "messages": _build_deepseek_messages(
            target,
            context_snippets,
            request_count,
            exclude_stems,
            quality_feedback,
        ),
        "temperature": 0.55,
        "response_format": {"type": "json_object"},
    }

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            url,
            headers={
                "Authorization": f"Bearer {settings.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            json=body,
        ) as response:
            data = await response.json(content_type=None)
            if response.status >= 400:
                detail = data.get("error", {}).get("message") if isinstance(data, dict) else None
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=detail or "DeepSeek 生成失败，请稍后重试",
                )
            return data


def _parse_generated_question_candidates(
    raw_response: dict,
    target: AiTrainingTarget,
    exam_code: str,
) -> tuple[list[dict], list[str]]:
    choices = raw_response.get("choices") or []
    content = choices[0].get("message", {}).get("content") if choices else ""
    if not content:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="DeepSeek 未返回题目内容")

    try:
        parsed = _extract_json_object(content)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="DeepSeek 返回格式无法解析") from exc

    raw_items = parsed.get("questions") if isinstance(parsed, dict) else None
    if not isinstance(raw_items, list):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="DeepSeek 返回中缺少 questions 数组")

    rows: list[dict] = []
    rejection_reasons: list[str] = []
    for index, raw in enumerate(raw_items, start=1):
        if isinstance(raw, dict):
            row, reasons = _safe_question_candidate(raw, target, exam_code)
            if row:
                rows.append(row)
            else:
                rejection_reasons.extend(f"第 {index} 个候选：{reason}" for reason in reasons)
        else:
            rejection_reasons.append(f"第 {index} 个候选不是 JSON 对象")

    return rows, rejection_reasons[:20]


def _parse_generated_questions(
    raw_response: dict,
    target: AiTrainingTarget,
    exam_code: str,
    required_count: int | None = None,
) -> list[dict]:
    rows, rejection_reasons = _parse_generated_question_candidates(raw_response, target, exam_code)

    minimum = target.question_count if required_count is None else required_count
    if len(rows) < minimum:
        detail = "DeepSeek 返回的有效题目数量不足"
        if rejection_reasons:
            detail = f"{detail}：{rejection_reasons[0]}"
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)
    return rows[: target.question_count]


def _existing_ai_fingerprints(supabase, target: AiTrainingTarget) -> tuple[set[str], list[str]]:
    try:
        response = (
            supabase.table("questions")
            .select("stem")
            .eq("source_type", "ai_deepseek")
            .eq("subject", target.subject)
            .eq("module", target.module)
            .eq("submodule", target.submodule)
            .limit(120)
            .execute()
        )
    except Exception:
        return set(), []

    fingerprints: set[str] = set()
    stems: list[str] = []
    for row in response.data or []:
        stem = row.get("stem")
        fingerprint = _question_fingerprint(stem)
        if fingerprint:
            fingerprints.add(fingerprint)
            if len(stems) < 8:
                stems.append(_compact_text(stem, 120))
    return fingerprints, stems


async def _generate_unique_question_rows(
    supabase,
    target: AiTrainingTarget,
    exam_code: str,
    context_snippets: list[str],
) -> tuple[list[dict], dict]:
    seen, existing_stems = _existing_ai_fingerprints(supabase, target)
    rows: list[dict] = []
    raw_responses: list[dict] = []
    review_responses: list[dict] = []
    quality_feedback: list[str] = []
    attempts = 0

    while len(rows) < target.question_count and attempts < 4:
        remaining = target.question_count - len(rows)
        request_count = min(30, max(remaining + 2, target.question_count if attempts == 0 else remaining))
        exclude_stems = existing_stems + [_compact_text(item["stem"], 120) for item in rows[-8:]]
        raw_response = await _call_deepseek(
            target,
            context_snippets,
            request_count=request_count,
            exclude_stems=exclude_stems,
            quality_feedback=quality_feedback[-8:],
        )
        raw_responses.append(raw_response)
        parsed_rows, rejected = _parse_generated_question_candidates(raw_response, target, exam_code)
        quality_feedback.extend(rejected)
        parsed_rows, review_feedback, review_response = await review_generated_question_rows(
            parsed_rows,
            target.subject,
        )
        quality_feedback.extend(review_feedback)
        review_responses.append(review_response)

        added_this_round = 0
        for row in parsed_rows:
            fingerprint = _question_fingerprint(row.get("stem"))
            if not fingerprint or fingerprint in seen:
                if fingerprint in seen:
                    quality_feedback.append("候选题干与近期或本轮题目重复")
                continue
            seen.add(fingerprint)
            rows.append(row)
            added_this_round += 1
            if len(rows) >= target.question_count:
                break

        attempts += 1

    if len(rows) < target.question_count:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"DeepSeek 只生成了 {len(rows)} 道不重复有效题，请稍后重试",
        )

    raw_response = {
        "generation_attempts": raw_responses,
        "independent_review_attempts": review_responses,
    }
    return rows[: target.question_count], raw_response


def _create_training_session(supabase, user_id: str, exam_code: str, target: AiTrainingTarget, payload: AiTrainingGenerateRequest) -> str:
    session_id = str(uuid4())
    try:
        supabase.table("ai_training_sessions").insert(
            {
                "id": session_id,
                "user_id": user_id,
                "exam_code": exam_code,
                "subject": target.subject,
                "module": target.module,
                "submodule": target.submodule,
                "difficulty": target.difficulty,
                "question_count": target.question_count,
                "smart_mode": payload.smart_mode,
                "basis": target.basis,
                "status": "generating",
                "raw_request": payload.model_dump(),
                "created_at": _utc_now_iso(),
                "updated_at": _utc_now_iso(),
            }
        ).execute()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="请先在 Supabase 执行 database/ai_training.sql") from exc
    return session_id


def _mark_session_failed(supabase, session_id: str, detail: str) -> None:
    try:
        supabase.table("ai_training_sessions").update(
            {"status": "failed", "error_message": detail, "updated_at": _utc_now_iso()}
        ).eq("id", session_id).execute()
    except Exception:
        pass


@router.post("/explain-wrong", response_model=ExplainWrongResponse)
def explain_wrong(
    payload: ExplainWrongRequest,
    user_id: str = Depends(get_current_user_id),
) -> ExplainWrongResponse:
    supabase = get_supabase_admin()
    question = get_question_or_404(supabase, payload.question_id)
    require_answer_disclosure_allowed(supabase, user_id, payload.question_id)

    return ExplainWrongResponse(
        why_wrong=f"你选择了 {payload.selected_answer}，建议先对照题干关键词与选项含义，排除不符合知识点的选项。",
        why_correct=f"正确答案是 {question['answer']}。标准解析：{question['explanation']}",
        knowledge_point=f"{question['subject']} / {question['module']} / {question['submodule']}",
    )


@router.post("/question-chat", response_model=QuestionChatResponse)
async def question_chat(
    payload: QuestionChatRequest,
    user_id: str = Depends(get_current_user_id),
) -> QuestionChatResponse:
    supabase = get_supabase_admin()
    question = get_question_or_404(supabase, payload.question_id)
    answer_disclosure_allowed = has_answer_submission(supabase, user_id, payload.question_id)
    safe_payload = payload.model_copy(
        update={"submitted": bool(payload.submitted and answer_disclosure_allowed)}
    )
    safe_question = question if safe_payload.submitted else _hide_answer(question)
    try:
        result = await call_deepseek_chat(
            _build_question_chat_messages(safe_question, safe_payload),
            max_tokens=650,
            timeout_seconds=18,
        )
    except HTTPException:
        result = {
            "reply": _build_question_chat_fallback_reply(safe_question, safe_payload),
            "model": "local_fallback",
        }

    return QuestionChatResponse(
        reply=result["reply"],
        usage={
            "model": result["model"],
            "mode": "question_assistant",
        },
    )


@router.post("/weakness-analysis", response_model=WeaknessAnalysisResponse)
def weakness_analysis(user_id: str = Depends(get_current_user_id)) -> WeaknessAnalysisResponse:
    supabase = get_supabase_admin()
    response = (
        supabase.table("ability_stats")
        .select("*")
        .eq("user_id", user_id)
        .order("accuracy")
        .limit(3)
        .execute()
    )
    weak_items = [build_ability_item(row) for row in response.data]
    weak_modules = [f"{item['subject']} / {item['module']} / {item['submodule']}" for item in weak_items]

    return WeaknessAnalysisResponse(
        weak_modules=weak_modules,
        suggested_points=weak_modules,
        summary="第一版先使用规则分析：优先训练正确率最低的 2-3 个知识点，并结合错题解析复盘。",
    )


@router.post("/generate-similar-question", response_model=SimilarQuestionResponse)
def generate_similar_question(
    payload: SimilarQuestionRequest,
    _: str = Depends(get_current_user_id),
) -> SimilarQuestionResponse:
    supabase = get_supabase_admin()
    question = get_question_or_404(supabase, payload.question_id)
    response = (
        exclude_ai_generated_questions(supabase.table("questions").select("*"))
        .eq("exam_code", question["exam_code"])
        .eq("subject", question["subject"])
        .eq("module", question["module"])
        .eq("submodule", question["submodule"])
        .eq("status", "active")
        .neq("id", payload.question_id)
        .limit(payload.limit)
        .execute()
    )

    items = [_hide_answer(row) for row in response.data]
    return SimilarQuestionResponse(items=items)


@router.get("/training/recommendation", response_model=AiTrainingRecommendationResponse)
def get_training_recommendation(
    exam_code: str | None = None,
    subject: str | None = None,
    user_id: str = Depends(get_current_user_id),
) -> AiTrainingRecommendationResponse:
    supabase = get_supabase_admin()
    profile = _get_profile_or_404(supabase, user_id)
    if not _is_membership_active(profile):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="AI 专项出题当前仅对 Pro 会员开放")

    resolved_exam_code = exam_code or profile.get("exam_target") or "Z001"
    if resolved_exam_code not in {"Z001", "Z002"}:
        resolved_exam_code = "Z001"

    subject_filter = _normalize_subject_for_exam(subject, resolved_exam_code)
    target, metrics = _build_smart_target(supabase, user_id, profile, resolved_exam_code, subject_filter=subject_filter)
    return AiTrainingRecommendationResponse(exam_code=resolved_exam_code, target=target, metrics=metrics)


@router.post("/training/generate", response_model=AiTrainingSessionResponse)
async def generate_training(
    payload: AiTrainingGenerateRequest,
    user_id: str = Depends(get_current_user_id),
) -> AiTrainingSessionResponse:
    supabase = get_supabase_admin()
    profile = _get_profile_or_404(supabase, user_id)
    if not _is_membership_active(profile):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="AI 专项出题当前仅对 Pro 会员开放")

    exam_code = payload.exam_code or profile.get("exam_target") or "Z001"
    if exam_code not in {"Z001", "Z002"}:
        exam_code = "Z001"

    target = _build_target(supabase, user_id, profile, payload)
    if not get_settings().deepseek_api_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="DeepSeek API Key 尚未配置")
    session_id = _create_training_session(supabase, user_id, exam_code, target, payload)
    context_snippets = _build_context_snippets(supabase, user_id, exam_code, target.subject)

    try:
        question_rows, raw_response = await _generate_unique_question_rows(supabase, target, exam_code, context_snippets)
        inserted = supabase.table("questions").insert(question_rows).execute()
        questions = inserted.data or []
        if len(questions) < target.question_count:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI 题目写入数量不足，请稍后重试")
        warm_submission_questions(questions)
        mapping_rows = [
            {"session_id": session_id, "question_id": question["id"], "position": index + 1}
            for index, question in enumerate(questions[: target.question_count])
        ]
        supabase.table("ai_training_session_questions").insert(mapping_rows).execute()
        supabase.table("ai_training_sessions").update(
            {"status": "completed", "raw_response": raw_response, "updated_at": _utc_now_iso()}
        ).eq("id", session_id).execute()
    except HTTPException as exc:
        _mark_session_failed(supabase, session_id, str(exc.detail))
        raise
    except Exception as exc:
        _mark_session_failed(supabase, session_id, "AI 训练生成失败")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI 训练生成失败") from exc

    return AiTrainingSessionResponse(
        session_id=session_id,
        status="completed",
        exam_code=exam_code,
        target=target,
        items=[_hide_answer(question) for question in questions[: target.question_count]],
    )


@router.get("/training/sessions/{session_id}", response_model=AiTrainingSessionResponse)
def get_training_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
) -> AiTrainingSessionResponse:
    supabase = get_supabase_admin()
    session_response = (
        supabase.table("ai_training_sessions")
        .select("*")
        .eq("id", session_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if not session_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI 训练不存在")

    session = session_response.data[0]
    question_response = (
        supabase.table("ai_training_session_questions")
        .select("position, questions(*)")
        .eq("session_id", session_id)
        .order("position")
        .execute()
    )
    full_questions = [row["questions"] for row in question_response.data or [] if row.get("questions")]
    warm_submission_questions(full_questions)
    questions = [_hide_answer(question) for question in full_questions]
    target = AiTrainingTarget(
        subject=session["subject"],
        module=session["module"],
        submodule=session["submodule"],
        difficulty=session["difficulty"],
        question_count=int(session.get("question_count") or len(questions)),
        basis=session.get("basis") or "",
    )
    return AiTrainingSessionResponse(
        session_id=session["id"],
        status=session["status"],
        exam_code=session["exam_code"],
        target=target,
        items=questions,
    )


@router.get("/training/sessions/{session_id}/summary", response_model=AiTrainingSummaryResponse)
def get_training_summary(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
) -> AiTrainingSummaryResponse:
    supabase = get_supabase_admin()
    session_response = (
        supabase.table("ai_training_sessions")
        .select("*")
        .eq("id", session_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if not session_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI 训练不存在")

    question_response = (
        supabase.table("ai_training_session_questions")
        .select("position, questions(*)")
        .eq("session_id", session_id)
        .order("position")
        .execute()
    )
    questions = [row["questions"] for row in question_response.data or [] if row.get("questions")]
    question_ids = [item["id"] for item in questions]

    answer_map: dict[str, dict] = {}
    if question_ids:
        answer_response = (
            supabase.table("user_answers")
            .select("question_id, selected_answer, is_correct, used_time, created_at")
            .eq("user_id", user_id)
            .in_("question_id", question_ids)
            .order("created_at", desc=True)
            .execute()
        )
        for row in answer_response.data or []:
            question_id = row.get("question_id")
            if question_id and question_id not in answer_map:
                answer_map[question_id] = row

    items: list[dict] = []
    weak_points: list[str] = []
    for question in questions:
        answer = answer_map.get(question["id"])
        is_correct = bool(answer.get("is_correct")) if answer else False
        if answer and not is_correct:
            label = f"{question.get('module')} / {question.get('submodule')}"
            if label not in weak_points:
                weak_points.append(label)
        items.append(
            {
                "question_id": question["id"],
                "stem": question.get("stem"),
                "selected_answer": answer.get("selected_answer") if answer else None,
                "correct_answer": question.get("answer") if answer else None,
                "is_correct": is_correct if answer else None,
                "explanation": question.get("explanation") if answer else None,
                "subject": question.get("subject"),
                "module": question.get("module"),
                "submodule": question.get("submodule"),
            }
        )

    total_count = len(questions)
    answered_count = len(answer_map)
    correct_count = sum(1 for row in answer_map.values() if row.get("is_correct"))
    accuracy = round(correct_count / answered_count * 100, 2) if answered_count else 0.0
    session = session_response.data[0]
    focus = f"{session.get('subject')} / {session.get('module')} / {session.get('submodule')}"

    if answered_count < total_count:
        summary = f"本轮 AI 训练还未完整作答，目前已完成 {answered_count}/{total_count} 题。"
        next_step = "建议先完成剩余题目，再回到总结页查看完整诊断。"
    elif accuracy >= 80:
        summary = f"本轮围绕 {focus} 训练，正确率 {round(accuracy)}%，掌握度较好。"
        next_step = "下一轮可以提高难度，继续做强化突破或冲刺挑战题。"
    elif accuracy >= 60:
        summary = f"本轮围绕 {focus} 训练，正确率 {round(accuracy)}%，基础理解基本到位，但稳定性还可以继续提升。"
        next_step = "建议回看错题解析，再生成一组同知识点标准提升训练。"
    else:
        summary = f"本轮围绕 {focus} 训练，正确率 {round(accuracy)}%，说明该知识点仍是当前薄弱项。"
        next_step = "建议先看完每道题解析，再用基础巩固难度重新训练 10 题。"

    return AiTrainingSummaryResponse(
        session_id=session_id,
        total_count=total_count,
        answered_count=answered_count,
        correct_count=correct_count,
        accuracy=accuracy,
        summary=summary,
        next_step=next_step,
        weak_points=weak_points[:5],
        items=items,
    )
