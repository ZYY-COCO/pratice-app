from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.answers import SubmitAnswerResponse
from app.schemas.questions import Question
from app.schemas.wrong_questions import (
    ReviewWrongQuestionRequest,
    WrongQuestionDetailResponse,
    WrongQuestionItem,
    WrongQuestionListResponse,
)
from app.services.answers import persist_answer_submission, submit_answer
from app.services.question_sources import exclude_ai_generated_questions, is_ai_generated_question
from app.utils.cursor_pagination import (
    build_keyset_filter,
    cursor_datetime,
    cursor_uuid,
    decode_page_cursor,
    encode_page_cursor,
)

router = APIRouter(prefix="/wrong-questions", tags=["错题本"])


@router.get("", response_model=WrongQuestionListResponse)
def list_wrong_questions(
    user_id: str = Depends(get_current_user_id),
    subject: str | None = None,
    module: str | None = None,
    submodule: str | None = None,
    limit: int = Query(default=30, ge=1, le=50),
    cursor: str | None = Query(default=None, max_length=2048),
) -> WrongQuestionListResponse:
    normalized_subject = str(subject or "").strip()
    normalized_module = str(module or "").strip()
    normalized_submodule = str(submodule or "").strip()
    cursor_context = {
        "subject": normalized_subject,
        "module": normalized_module,
        "submodule": normalized_submodule,
    }
    cursor_payload = decode_page_cursor(
        cursor,
        kind="wrong_questions",
        context=cursor_context,
    )

    supabase = get_supabase_admin()
    query = (
        supabase.table("wrong_questions")
        .select("id, question_id, wrong_count, last_wrong_at, questions!inner(*)")
        .eq("user_id", user_id)
    )
    if normalized_subject:
        query = query.eq("questions.subject", normalized_subject)
    if normalized_module:
        query = query.eq("questions.module", normalized_module)
    if normalized_submodule:
        query = query.eq("questions.submodule", normalized_submodule)
    query = exclude_ai_generated_questions(query, reference_table="questions")
    if cursor_payload:
        query = query.or_(build_keyset_filter([
            ("last_wrong_at", "desc", cursor_datetime(cursor_payload, "last_wrong_at")),
            ("id", "desc", cursor_uuid(cursor_payload, "id")),
        ]))
    response = (
        query
        .order("last_wrong_at", desc=True)
        .order("id", desc=True)
        .limit(limit + 1)
        .execute()
    )

    items: list[WrongQuestionItem] = []
    rows = list(response.data or [])
    has_more = len(rows) > limit
    page_rows = rows[:limit]
    for row in page_rows:
        question = row.get("questions")
        if is_ai_generated_question(question):
            continue
        if question:
            question = {**question, "answer": None, "explanation": None}
        items.append(
            WrongQuestionItem(
                id=row["id"],
                question_id=row["question_id"],
                wrong_count=row["wrong_count"],
                last_wrong_at=row["last_wrong_at"],
                question=Question(**question) if question else None,
            )
        )
    next_cursor = None
    if has_more and page_rows:
        anchor = page_rows[-1]
        next_cursor = encode_page_cursor("wrong_questions", {
            **cursor_context,
            "last_wrong_at": str(anchor.get("last_wrong_at") or ""),
            "id": str(anchor.get("id") or ""),
        })
    return WrongQuestionListResponse(
        items=items,
        count=len(items),
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.get("/{question_id}", response_model=WrongQuestionDetailResponse)
def get_wrong_question_detail(
    question_id: str,
    user_id: str = Depends(get_current_user_id),
) -> WrongQuestionDetailResponse:
    supabase = get_supabase_admin()
    wrong_response = (
        supabase.table("wrong_questions")
        .select("id, question_id, wrong_count, last_wrong_at, questions(*)")
        .eq("user_id", user_id)
        .eq("question_id", question_id)
        .limit(1)
        .execute()
    )
    if not wrong_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wrong question not found")

    row = wrong_response.data[0]
    if is_ai_generated_question(row.get("questions")):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wrong question not found")
    answer_response = (
        supabase.table("user_answers")
        .select("selected_answer")
        .eq("user_id", user_id)
        .eq("question_id", question_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    latest_selected_answer = answer_response.data[0]["selected_answer"] if answer_response.data else None

    return WrongQuestionDetailResponse(
        id=row["id"],
        question_id=row["question_id"],
        wrong_count=row["wrong_count"],
        last_wrong_at=row["last_wrong_at"],
        latest_selected_answer=latest_selected_answer,
        question=Question(**row["questions"]),
    )


@router.post("/review", response_model=SubmitAnswerResponse)
def review_wrong_question(
    payload: ReviewWrongQuestionRequest,
    user_id: str = Depends(get_current_user_id),
) -> SubmitAnswerResponse:
    supabase = get_supabase_admin()
    result = submit_answer(
        supabase=supabase,
        user_id=user_id,
        question_id=payload.question_id,
        selected_answer=payload.selected_answer,
        used_time=payload.used_time,
        requested_exam_code=payload.exam_code,
    )
    persisted = persist_answer_submission(
        user_id=user_id,
        question={
            "id": result["question_id"],
            "exam_code": result.get("exam_code"),
            "subject": result.get("subject"),
            "module": result.get("module"),
            "submodule": result.get("submodule"),
            "source_type": result.get("source_type"),
        },
        selected_answer=payload.selected_answer,
        used_time=payload.used_time,
        is_correct=result["is_correct"],
        client_submission_id=payload.client_submission_id,
    )
    result.update(persisted)
    result["ability_accuracy"] = persisted.get("ability_accuracy")
    return SubmitAnswerResponse(**result)
