import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

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


def _persist_graded_answer(
    *,
    result: dict,
    payload: SubmitAnswerRequest,
    user_id: str,
    supabase=None,
) -> dict:
    question = {
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
    persisted = persist_answer_submission(
        user_id=user_id,
        question=question,
        selected_answer=payload.selected_answer,
        used_time=payload.used_time,
        is_correct=result["is_correct"],
        client_submission_id=payload.client_submission_id,
        practice_session_item_id=payload.practice_session_item_id,
    )
    response = {**result, **persisted}
    response["ability_accuracy"] = persisted.get("ability_accuracy")
    if payload.practice_session_item_id:
        try:
            response["adaptive"] = apply_adaptive_answer_update(
                supabase or get_supabase_admin(),
                user_id=user_id,
                question=question,
                persisted={
                    **persisted,
                    "is_correct": persisted.get("is_correct", result["is_correct"]),
                },
                used_time=payload.used_time,
                practice_session_item_id=payload.practice_session_item_id,
            )
        except HTTPException as exc:
            logger.warning(
                "Adaptive answer link rejected after durable answer "
                "(question_id=%s status_code=%s)",
                result["question_id"],
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
                result["question_id"],
                type(exc).__name__,
            )
            response["adaptive"] = {
                "adaptive_updated": False,
                "retryable": True,
                "error": "adaptive_state_update_pending",
            }
    return response


def _responsive_grade_headers(result: dict) -> dict[str, str]:
    """Configure streaming without exposing feedback before the durable write.

    Mobile clients that cannot wait for the streamed body use the idempotent
    ``/grade`` fallback, which now persists through the same atomic path.
    """

    del result
    return {
        "Cache-Control": "no-store",
        "X-Accel-Buffering": "no",
    }


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
    user_id: str = Depends(get_current_user_id),
) -> StreamingResponse:
    """Flush transport setup, then return feedback after durable submission.

    A one-byte whitespace chunk starts the response without any grading data.
    The final JSON body contains feedback only after persistence succeeds;
    clients needing faster feedback use the idempotent ``/grade`` path.
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

    def stream_response():
        yield b" "
        response = dict(result)
        try:
            response = _persist_graded_answer(
                result=result,
                payload=payload,
                user_id=user_id,
                supabase=supabase,
            )
        except HTTPException as exc:
            response.update(
                {
                    "correct_answer": "",
                    "is_correct": None,
                    "explanation": "",
                    "added_to_wrong_questions": None,
                    "persisted": False,
                    "persistence_error": str(exc.detail),
                    "persistence_retryable": exc.status_code in {
                        status.HTTP_408_REQUEST_TIMEOUT,
                        status.HTTP_429_TOO_MANY_REQUESTS,
                        status.HTTP_500_INTERNAL_SERVER_ERROR,
                        status.HTTP_502_BAD_GATEWAY,
                        status.HTTP_503_SERVICE_UNAVAILABLE,
                        status.HTTP_504_GATEWAY_TIMEOUT,
                    },
                }
            )
        except Exception as exc:
            logger.warning(
                "Responsive answer persistence failed (question_id=%s error_type=%s)",
                payload.question_id,
                type(exc).__name__,
            )
            response.update(
                {
                    "correct_answer": "",
                    "is_correct": None,
                    "explanation": "",
                    "added_to_wrong_questions": None,
                    "persisted": False,
                    "persistence_error": "作答记录暂时无法保存，请稍后重试",
                    "persistence_retryable": True,
                }
            )

        body = SubmitAnswerResponse(**response).model_dump(mode="json")
        yield json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    return StreamingResponse(
        stream_response(),
        media_type="application/json",
        headers=_responsive_grade_headers(result),
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
