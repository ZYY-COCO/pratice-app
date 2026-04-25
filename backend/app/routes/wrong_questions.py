from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

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

router = APIRouter(prefix="/wrong-questions", tags=["错题本"])


@router.get("", response_model=WrongQuestionListResponse)
def list_wrong_questions(
    user_id: str = Depends(get_current_user_id),
    subject: str | None = None,
    module: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
) -> WrongQuestionListResponse:
    supabase = get_supabase_admin()
    response = (
        supabase.table("wrong_questions")
        .select("id, question_id, wrong_count, last_wrong_at, questions(*)")
        .eq("user_id", user_id)
        .order("last_wrong_at", desc=True)
        .limit(limit)
        .execute()
    )

    items: list[WrongQuestionItem] = []
    for row in response.data:
        question = row.get("questions")
        if subject and question and question.get("subject") != subject:
            continue
        if module and question and question.get("module") != module:
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
    return WrongQuestionListResponse(items=items, count=len(items))


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
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
) -> SubmitAnswerResponse:
    supabase = get_supabase_admin()
    result = submit_answer(
        supabase=supabase,
        user_id=user_id,
        question_id=payload.question_id,
        selected_answer=payload.selected_answer,
        used_time=payload.used_time,
    )
    background_tasks.add_task(
        persist_answer_submission,
        user_id=user_id,
        question={
            "id": result["question_id"],
            "exam_code": result.get("exam_code"),
            "subject": result.get("subject"),
            "module": result.get("module"),
            "submodule": result.get("submodule"),
        },
        selected_answer=payload.selected_answer,
        used_time=payload.used_time,
        is_correct=result["is_correct"],
    )
    return SubmitAnswerResponse(**result)
