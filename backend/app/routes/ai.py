import json
from datetime import datetime, timezone
from uuid import uuid4

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, status

from app.config import get_settings
from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.ai import (
    AiTrainingGenerateRequest,
    AiTrainingSessionResponse,
    AiTrainingTarget,
    ExplainWrongRequest,
    ExplainWrongResponse,
    SimilarQuestionRequest,
    SimilarQuestionResponse,
    WeaknessAnalysisResponse,
)
from app.services.answers import get_question_or_404
from app.services.reports import build_ability_item

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


def _compact_text(value: object, max_length: int = 2000) -> str:
    text = str(value or "").strip()
    return text[:max_length]


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
    answer = _compact_text(raw.get("answer"), 8).upper()
    if answer not in {"A", "B", "C", "D"}:
        return None

    row = {
        "exam_code": exam_code,
        "subject": _compact_text(raw.get("subject") or target.subject, 80),
        "module": _compact_text(raw.get("module") or target.module, 80),
        "submodule": _compact_text(raw.get("submodule") or target.submodule, 80),
        "question_type": "single_choice",
        "stem": _compact_text(raw.get("stem"), 2000),
        "option_a": _compact_text(raw.get("option_a"), 800),
        "option_b": _compact_text(raw.get("option_b"), 800),
        "option_c": _compact_text(raw.get("option_c"), 800),
        "option_d": _compact_text(raw.get("option_d"), 800),
        "answer": answer,
        "explanation": _compact_text(raw.get("explanation"), 2000),
        "difficulty": int(raw.get("difficulty") or DIFFICULTY_LEVELS[target.difficulty]),
        "source_type": "ai_deepseek",
        "source_year": None,
    }

    required_fields = ["subject", "module", "submodule", "stem", "option_a", "option_b", "option_c", "option_d", "explanation"]
    if any(not row[field] for field in required_fields):
        return None
    row["difficulty"] = min(5, max(1, row["difficulty"]))
    return row


def _hide_answer(question: dict) -> dict:
    return {**question, "answer": None, "explanation": None}


def _build_target(supabase, user_id: str, profile: dict, payload: AiTrainingGenerateRequest) -> AiTrainingTarget:
    question_count = _normalize_question_count(payload.question_count)
    difficulty = _normalize_difficulty(payload.difficulty)

    if not payload.smart_mode:
        return AiTrainingTarget(
            subject=payload.subject or FALLBACK_TARGET["subject"],
            module=payload.module or FALLBACK_TARGET["module"],
            submodule=payload.submodule or FALLBACK_TARGET["submodule"],
            difficulty=difficulty,
            question_count=question_count,
            basis="用户手动选择训练范围和题量。",
        )

    exam_code = payload.exam_code or profile.get("exam_target") or "Z001"
    response = (
        supabase.table("ability_stats")
        .select("*")
        .eq("user_id", user_id)
        .eq("exam_code", exam_code)
        .gt("total_count", 0)
        .order("accuracy")
        .order("total_count", desc=True)
        .limit(1)
        .execute()
    )
    if response.data:
        row = response.data[0]
        accuracy = float(row.get("accuracy") or 0)
        return AiTrainingTarget(
            subject=row.get("subject") or FALLBACK_TARGET["subject"],
            module=row.get("module") or FALLBACK_TARGET["module"],
            submodule=row.get("submodule") or FALLBACK_TARGET["submodule"],
            difficulty=difficulty,
            question_count=question_count,
            basis=f"当前 {row.get('submodule') or row.get('module')} 正确率约 {round(accuracy)}%，优先生成同类强化题。",
        )

    return AiTrainingTarget(
        subject=FALLBACK_TARGET["subject"],
        module=FALLBACK_TARGET["module"],
        submodule=FALLBACK_TARGET["submodule"],
        difficulty=difficulty,
        question_count=question_count,
        basis=FALLBACK_TARGET["basis"],
    )


def _build_context_snippets(supabase, user_id: str) -> list[str]:
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
        stem = _compact_text(question.get("stem"), 180)
        if stem:
            snippets.append(
                f"- {question.get('subject')} / {question.get('module')} / {question.get('submodule')}：{stem}"
            )
    return snippets


def _build_deepseek_messages(target: AiTrainingTarget, context_snippets: list[str]) -> list[dict]:
    context = "\n".join(context_snippets) if context_snippets else "暂无最近错题样例。"
    return [
        {
            "role": "system",
            "content": (
                "你是港澳台考研刷题 App 的命题老师。请只输出合法 JSON，不要输出 Markdown。"
                "题目必须为单选题，只有 A、B、C、D 四个选项，绝对不要生成 E 选项。"
                "题干、选项、解析必须准确、简洁，贴近港澳台考研初试刷题训练。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"请生成 {target.question_count} 道训练题。\n"
                f"科目：{target.subject}\n"
                f"模块：{target.module}\n"
                f"知识点：{target.submodule}\n"
                f"难度：{target.difficulty}\n"
                f"推荐依据：{target.basis}\n"
                f"最近错题参考：\n{context}\n\n"
                "输出 JSON 格式必须为："
                '{"questions":[{"stem":"题干","option_a":"A选项","option_b":"B选项",'
                '"option_c":"C选项","option_d":"D选项","answer":"A","explanation":"解析",'
                '"subject":"科目","module":"模块","submodule":"知识点","difficulty":2}]}'
            ),
        },
    ]


async def _call_deepseek(target: AiTrainingTarget, context_snippets: list[str]) -> dict:
    settings = get_settings()
    if not settings.deepseek_api_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="DeepSeek API Key 尚未配置")

    url = f"{settings.deepseek_base_url.rstrip('/')}/chat/completions"
    timeout = aiohttp.ClientTimeout(total=settings.deepseek_timeout_seconds)
    body = {
        "model": settings.deepseek_model,
        "messages": _build_deepseek_messages(target, context_snippets),
        "temperature": 0.35,
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


def _parse_generated_questions(raw_response: dict, target: AiTrainingTarget, exam_code: str) -> list[dict]:
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

    rows = []
    for raw in raw_items:
        if isinstance(raw, dict):
            row = _safe_question_row(raw, target, exam_code)
            if row:
                rows.append(row)

    if len(rows) < target.question_count:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="DeepSeek 返回的有效题目数量不足")
    return rows[: target.question_count]


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
def explain_wrong(payload: ExplainWrongRequest, _: str = Depends(get_current_user_id)) -> ExplainWrongResponse:
    supabase = get_supabase_admin()
    question = get_question_or_404(supabase, payload.question_id)

    return ExplainWrongResponse(
        why_wrong=f"你选择了 {payload.selected_answer}，建议先对照题干关键词与选项含义，排除不符合知识点的选项。",
        why_correct=f"正确答案是 {question['answer']}。标准解析：{question['explanation']}",
        knowledge_point=f"{question['subject']} / {question['module']} / {question['submodule']}",
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
        supabase.table("questions")
        .select("*")
        .eq("exam_code", question["exam_code"])
        .eq("subject", question["subject"])
        .eq("module", question["module"])
        .eq("submodule", question["submodule"])
        .neq("id", payload.question_id)
        .limit(payload.limit)
        .execute()
    )

    items = [_hide_answer(row) for row in response.data]
    return SimilarQuestionResponse(items=items)


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
    context_snippets = _build_context_snippets(supabase, user_id)

    try:
        raw_response = await _call_deepseek(target, context_snippets)
        question_rows = _parse_generated_questions(raw_response, target, exam_code)
        inserted = supabase.table("questions").insert(question_rows).execute()
        questions = inserted.data or []
        mapping_rows = [
            {"session_id": session_id, "question_id": question["id"], "position": index + 1}
            for index, question in enumerate(questions)
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
        items=[_hide_answer(question) for question in questions],
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
    questions = [_hide_answer(row["questions"]) for row in question_response.data or [] if row.get("questions")]
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
