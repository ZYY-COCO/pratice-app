import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.answers import (
    AbilityAccuracyResponse,
    AnswerHistoryResponse,
    GradeAnswerResponse,
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
    resolve_user_exam_code,
    submit_answer,
)
from app.services.adaptive_practice import apply_adaptive_answer_update

router = APIRouter(prefix="/answers", tags=["作答"])
logger = logging.getLogger(__name__)

RESPONSIVE_GRADE_HEADER_NAMES = (
    "X-GYT-Grading-Ready",
    "X-GYT-Question-Id",
    "X-GYT-Correct-Answer",
    "X-GYT-Is-Correct",
    "X-GYT-Added-To-Wrong-Questions",
)


def _submission_question(result: dict) -> dict:
    return {
        "id": result["question_id"],
        "exam_code": result.get("exam_code"),
        "subject": result.get("subject"),
        "module": result.get("module"),
        "submodule": result.get("submodule"),
        "source_type": result.get("source_type"),
        "question_type": result.get("question_type"),
        "difficulty": result.get("difficulty"),
        "estimated_time_sec": result.get("estimated_time_sec"),
    }


def _persist_graded_answer_core(
    *,
    result: dict,
    payload: SubmitAnswerRequest,
    user_id: str,
    require_atomic_persistence: bool = False,
) -> tuple[dict, dict, dict]:
    """Persist the minimum authoritative answer state before grade disclosure."""

    question = _submission_question(result)
    persisted = persist_answer_submission(
        user_id=user_id,
        question=question,
        selected_answer=payload.selected_answer,
        used_time=payload.used_time,
        is_correct=result["is_correct"],
        client_submission_id=payload.client_submission_id,
        practice_session_item_id=payload.practice_session_item_id,
        allow_compatibility_fallback=not require_atomic_persistence,
    )
    if persisted.get("persisted") is not True:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="作答记录暂时无法保存，请稍后重试",
        )
    response = {**result, **persisted}
    response["ability_accuracy"] = persisted.get("ability_accuracy")
    return response, question, persisted


def _apply_adaptive_update_to_answer(
    *,
    response: dict,
    question: dict,
    persisted: dict,
    payload: SubmitAnswerRequest,
    user_id: str,
    supabase=None,
) -> dict:
    if payload.practice_session_item_id:
        try:
            response["adaptive"] = apply_adaptive_answer_update(
                supabase or get_supabase_admin(),
                user_id=user_id,
                question=question,
                persisted={
                    **persisted,
                    "is_correct": persisted.get("is_correct", response["is_correct"]),
                },
                used_time=payload.used_time,
                practice_session_item_id=payload.practice_session_item_id,
            )
        except HTTPException as exc:
            logger.warning(
                "Adaptive answer link rejected after durable answer "
                "(question_id=%s status_code=%s)",
                response["question_id"],
                exc.status_code,
            )
            response["adaptive"] = {
                "adaptive_updated": False,
                "retryable": exc.status_code >= 500,
                "error": "adaptive_item_invalid" if exc.status_code < 500 else "adaptive_state_update_pending",
            }
        except Exception as exc:
            logger.warning(
                "Adaptive answer update unavailable after durable answer "
                "(question_id=%s error_type=%s)",
                response["question_id"],
                type(exc).__name__,
            )
            response["adaptive"] = {
                "adaptive_updated": False,
                "retryable": True,
                "error": "adaptive_state_update_pending",
            }
    return response


def _persist_graded_answer(
    *,
    result: dict,
    payload: SubmitAnswerRequest,
    user_id: str,
    supabase=None,
) -> dict:
    response, question, persisted = _persist_graded_answer_core(
        result=result,
        payload=payload,
        user_id=user_id,
    )
    return _apply_adaptive_update_to_answer(
        response=response,
        question=question,
        persisted=persisted,
        payload=payload,
        user_id=user_id,
        supabase=supabase,
    )


def _responsive_grade_headers(result: dict) -> dict[str, str]:
    """Expose grading metadata for instant feedback.

    The payload can be handled entirely from the short headers even when runtime
    cannot keep a long-lived stream open.
    """

    if result.get("persisted") is not True:
        raise RuntimeError("responsive grade headers require a durable answer")
    return {
        "Cache-Control": "no-store",
        "X-Accel-Buffering": "no",
        "X-GYT-Grading-Ready": "1",
        "X-GYT-Question-Id": str(result["question_id"]),
        "X-GYT-Correct-Answer": str(result["correct_answer"]),
        "X-GYT-Is-Correct": "1" if result["is_correct"] else "0",
        "X-GYT-Added-To-Wrong-Questions": (
            "1" if result["added_to_wrong_questions"] else "0"
        ),
    }


def _adaptive_update_pending(
    *,
    payload: SubmitAnswerRequest,
    persisted: dict,
) -> dict:
    return {
        "adaptive_updated": False,
        "retryable": True,
        "error": "adaptive_state_update_pending",
        "answer_id": persisted.get("submission_id"),
        "practice_session_item_id": payload.practice_session_item_id,
    }


def _apply_adaptive_update_in_background(
    *,
    response: dict,
    question: dict,
    persisted: dict,
    payload: SubmitAnswerRequest,
    user_id: str,
) -> None:
    """Best-effort fast follow; the client queue remains the durable retry owner."""

    completed = _apply_adaptive_update_to_answer(
        response=dict(response),
        question=dict(question),
        persisted=dict(persisted),
        payload=payload,
        user_id=user_id,
    )
    adaptive = completed.get("adaptive") or {}
    if adaptive.get("adaptive_updated") is True:
        logger.info(
            "Responsive adaptive update completed in background (question_id=%s)",
            response["question_id"],
        )
        return
    logger.warning(
        "Responsive adaptive update remains pending after background attempt "
        "(question_id=%s retryable=%s error=%s)",
        response["question_id"],
        adaptive.get("retryable"),
        adaptive.get("error"),
    )


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
    exam_code: str | None = Query(default=None, pattern="^(Z001|Z002)$"),
    subject: str | None = None,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> AnswerHistoryResponse:
    supabase = get_supabase_admin()
    resolved_exam_code = resolve_user_exam_code(supabase, user_id, exam_code)
    result = list_answer_history(
        supabase=supabase,
        user_id=user_id,
        status_filter=status_filter,
        exam_code=resolved_exam_code,
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
        practice_session_item_id=payload.practice_session_item_id,
    )
    response = _persist_graded_answer(result=result, payload=payload, user_id=user_id, supabase=supabase)
    return SubmitAnswerResponse(**response)


@router.post("/grade", response_model=GradeAnswerResponse)
def grade(
    payload: SubmitAnswerRequest,
    user_id: str = Depends(get_current_user_id),
) -> GradeAnswerResponse:
    """Return feedback only after the same durable submission used by ``/submit``.

    Mobile runtimes use this endpoint when streamed response headers are not
    observable.  Reusing the atomic persistence path keeps that fallback from
    becoming an answer oracle: a disclosed answer is always tied to the exact
    submitted choice, and concurrent retries converge through the existing
    ``client_submission_id`` idempotency key.
    """

    supabase = get_supabase_admin()
    result = submit_answer(
        supabase=supabase,
        user_id=user_id,
        question_id=payload.question_id,
        selected_answer=payload.selected_answer,
        used_time=payload.used_time,
        requested_exam_code=payload.exam_code,
        include_ability_accuracy=False,
        practice_session_item_id=payload.practice_session_item_id,
    )
    response = _persist_graded_answer(
        result=result,
        payload=payload,
        user_id=user_id,
        supabase=supabase,
    )
    return GradeAnswerResponse(**response)


@router.post("/submit-responsive", response_model=SubmitAnswerResponse)
def submit_responsive(
    payload: SubmitAnswerRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
) -> JSONResponse:
    """Persist the authoritative answer, then return grading immediately.

    The atomic persistence RPC is also the final comprehensive-practice embargo
    gate. Adaptive model work is a best-effort fast follow; the client keeps the
    same idempotency key queued until that second phase settles.
    """

    supabase = get_supabase_admin()
    result = submit_answer(
        supabase=supabase,
        user_id=user_id,
        question_id=payload.question_id,
        selected_answer=payload.selected_answer,
        used_time=payload.used_time,
        requested_exam_code=payload.exam_code,
        include_ability_accuracy=False,
        practice_session_item_id=payload.practice_session_item_id,
        precheck_feedback_embargo=False,
    )
    response, question, persisted = _persist_graded_answer_core(
        result=result,
        payload=payload,
        user_id=user_id,
        require_atomic_persistence=True,
    )
    if payload.practice_session_item_id:
        response["adaptive"] = _adaptive_update_pending(
            payload=payload,
            persisted=persisted,
        )
        background_tasks.add_task(
            _apply_adaptive_update_in_background,
            response=dict(response),
            question=dict(question),
            persisted=dict(persisted),
            payload=payload.model_copy(deep=True),
            user_id=user_id,
        )
    return JSONResponse(
        status_code=200,
        content=SubmitAnswerResponse(**response).model_dump(mode="json"),
        headers=_responsive_grade_headers(response),
        background=background_tasks,
    )


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
        practice_session_item_id=payload.practice_session_item_id,
    )
    submission_payload = SubmitAnswerRequest(
        question_id=payload.question_id,
        client_submission_id=payload.client_submission_id,
        practice_session_item_id=payload.practice_session_item_id,
        selected_answer=result["selected_answer"],
        used_time=payload.used_time,
        exam_code=payload.exam_code,
    )
    response = _persist_graded_answer(
        result=result,
        payload=submission_payload,
        user_id=user_id,
        supabase=supabase,
    )
    return SubmitAnswerResponse(**response)
