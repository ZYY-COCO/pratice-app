from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.questions import Passage, Question, QuestionListResponse

router = APIRouter(tags=["题目"])

PUBLIC_SUBJECTS = {"中华文化", "英语运用"}
VERSION_EXAM_CODES = {"Z001", "Z002"}


def get_question_exam_codes(exam_code: str | None, subject: str | None) -> list[str]:
    """公共科目使用 COMMON 题库，同时兼容旧的版本专属题。"""
    if not exam_code:
        return []
    if exam_code == "COMMON":
        return ["COMMON"]
    if subject in PUBLIC_SUBJECTS and exam_code in VERSION_EXAM_CODES:
        return ["COMMON", exam_code]
    return [exam_code]


def hide_answer(row: dict, include_answer: bool = False) -> dict:
    if include_answer:
        return row
    return {**row, "answer": None, "explanation": None}


@router.get("/questions", response_model=QuestionListResponse)
def list_questions(
    _: str = Depends(get_current_user_id),
    exam_code: str | None = Query(default=None, pattern="^(Z001|Z002|COMMON)$"),
    subject: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    randomize: bool = Query(default=False),
) -> QuestionListResponse:
    supabase = get_supabase_admin()
    query = supabase.table("questions").select("*")
    exam_codes = get_question_exam_codes(exam_code, subject)
    if len(exam_codes) > 1:
        query = query.in_("exam_code", exam_codes)
    elif len(exam_codes) == 1:
        query = query.eq("exam_code", exam_codes[0])
    if subject:
        query = query.eq("subject", subject)
    if randomize:
        query = query.order("created_at", desc=False)

    response = query.limit(1000 if randomize else limit).execute()
    rows = response.data
    if randomize:
        import random

        rows = random.sample(rows, min(limit, len(rows)))
    items = [Question(**hide_answer(row)) for row in rows]
    return QuestionListResponse(items=items, count=len(items))


@router.get("/questions/by-module", response_model=QuestionListResponse)
def list_questions_by_module(
    _: str = Depends(get_current_user_id),
    exam_code: str = Query(pattern="^(Z001|Z002|COMMON)$"),
    subject: str = Query(min_length=1),
    module: str = Query(min_length=1),
    submodule: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=50),
) -> QuestionListResponse:
    supabase = get_supabase_admin()
    query = supabase.table("questions").select("*")
    exam_codes = get_question_exam_codes(exam_code, subject)
    if len(exam_codes) > 1:
        query = query.in_("exam_code", exam_codes)
    else:
        query = query.eq("exam_code", exam_codes[0])
    response = query.eq("subject", subject).eq("module", module).eq("submodule", submodule).limit(limit).execute()
    items = [Question(**hide_answer(row)) for row in response.data]
    return QuestionListResponse(items=items, count=len(items))


@router.get("/passages/{passage_id}", response_model=Passage)
def get_passage(passage_id: str, _: str = Depends(get_current_user_id)) -> Passage:
    supabase = get_supabase_admin()
    response = supabase.table("passages").select("*").eq("id", passage_id).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passage not found")
    return Passage(**response.data[0])
