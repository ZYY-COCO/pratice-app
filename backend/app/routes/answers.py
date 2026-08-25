from fastapi import APIRouter, Depends, Query

from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.answers import (
    AbilityAccuracyResponse,
    AnswerHistoryResponse,
    MarkUnfamiliarRequest,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    SubmitBatchAnswerRequest,
    SubmitBatchAnswerResponse,
)
from app.services.answers import (
    get_current_ability_stats,
    get_submission_question_or_404,
    list_answer_history,
    mark_unfamiliar_answer,
    persist_answer_submission,
    resolve_stats_exam_code,
    submit_answer,
)

router = APIRouter(prefix="/answers", tags=["作答"])


@router.get("/ability-accuracy", response_model=AbilityAccuracyResponse)
def ability_accuracy(
    question_id: str,
    exam_code: str | None = Query(default=None, pattern="^(Z001|Z002)$"),
    user_id: str = Depends(get_current_user_id),
) -> AbilityAccuracyResponse:
    supabase = get_supabase_admin()
    question = get_submission_question_or_404(supabase, question_id)
    stats_exam_code = resolve_stats_exam_code(supabase, user_id, question, exam_code)
    current_ability = get_current_ability_stats(
        supabase,
        user_id,
        {**question, "exam_code": stats_exam_code},
    )
    return AbilityAccuracyResponse(
        ability_accuracy=float(current_ability["accuracy"]) if current_ability else None,
    )


@router.get("/history", response_model=AnswerHistoryResponse)
def history(
    user_id: str = Depends(get_current_user_id),
    status_filter: str = Query(default="all", alias="status", pattern="^(all|correct|wrong)$"),
    subject: str | None = None,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> AnswerHistoryResponse:
    supabase = get_supabase_admin()
    result = list_answer_history(
        supabase=supabase,
        user_id=user_id,
        status_filter=status_filter,
        subject=subject,
        limit=limit,
        offset=offset,
    )
    return AnswerHistoryResponse(**result)


@router.post("/submit", response_model=SubmitAnswerResponse)
def submit(
    payload: SubmitAnswerRequest,
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
        include_ability_accuracy=False,
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


@router.post("/submit-batch", response_model=SubmitBatchAnswerResponse)
def submit_batch(
    payload: SubmitBatchAnswerRequest,
    user_id: str = Depends(get_current_user_id),
) -> SubmitBatchAnswerResponse:
    supabase = get_supabase_admin()
    items: list[SubmitAnswerResponse] = []

    for item in payload.answers:
        result = submit_answer(
            supabase=supabase,
            user_id=user_id,
            question_id=item.question_id,
            selected_answer=item.selected_answer,
            used_time=item.used_time,
            requested_exam_code=payload.exam_code,
            include_ability_accuracy=False,
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
            selected_answer=item.selected_answer,
            used_time=item.used_time,
            is_correct=result["is_correct"],
            client_submission_id=item.client_submission_id,
        )
        result.update(persisted)
        result["ability_accuracy"] = persisted.get("ability_accuracy")
        items.append(SubmitAnswerResponse(**result))

    return SubmitBatchAnswerResponse(items=items)


@router.post("/mark-unfamiliar", response_model=SubmitAnswerResponse)
def mark_unfamiliar(
    payload: MarkUnfamiliarRequest,
    user_id: str = Depends(get_current_user_id),
) -> SubmitAnswerResponse:
    supabase = get_supabase_admin()
    result = mark_unfamiliar_answer(
        supabase=supabase,
        user_id=user_id,
        question_id=payload.question_id,
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
        selected_answer=result["selected_answer"],
        used_time=payload.used_time,
        is_correct=False,
        client_submission_id=payload.client_submission_id,
    )
    result.update(persisted)
    result["ability_accuracy"] = persisted.get("ability_accuracy")
    return SubmitAnswerResponse(**result)
