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
    submit_answer,
)

router = APIRouter(prefix="/answers", tags=["作答"])
logger = logging.getLogger(__name__)


def _persist_graded_answer(
    *,
    result: dict,
    payload: SubmitAnswerRequest,
    user_id: str,
) -> dict:
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
    response = {**result, **persisted}
    response["ability_accuracy"] = persisted.get("ability_accuracy")
    return response


def _responsive_grade_headers(result: dict) -> dict[str, str]:
    """Expose the already computed grade before the durable write finishes.

    The response body still completes only after the atomic database RPC. This
    lets mobile clients paint the answer state immediately without weakening
    the existing success-means-persisted contract.
    """

    return {
        "Cache-Control": "no-store",
        "X-Accel-Buffering": "no",
        "X-GYT-Grading-Ready": "1",
        "X-GYT-Question-Id": str(result["question_id"]),
        "X-GYT-Correct-Answer": str(result["correct_answer"]),
        "X-GYT-Is-Correct": "1" if result["is_correct"] else "0",
        "X-GYT-Added-To-Wrong-Questions": "1" if result["added_to_wrong_questions"] else "0",
        "Access-Control-Expose-Headers": (
            "X-GYT-Grading-Ready, X-GYT-Question-Id, X-GYT-Correct-Answer, "
            "X-GYT-Is-Correct, X-GYT-Added-To-Wrong-Questions"
        ),
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
    response = _persist_graded_answer(result=result, payload=payload, user_id=user_id)
    return SubmitAnswerResponse(**response)


@router.post("/grade", response_model=GradeAnswerResponse)
def grade(
    payload: SubmitAnswerRequest,
    user_id: str = Depends(get_current_user_id),
) -> GradeAnswerResponse:
    """Return the server-side grade without claiming that persistence finished.

    Mobile runtimes that cannot observe streamed response headers use this as a
    visual-feedback fallback while the separate durable submission continues.
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
    )
    return GradeAnswerResponse(**result)


@router.post("/submit-responsive", response_model=SubmitAnswerResponse)
def submit_responsive(
    payload: SubmitAnswerRequest,
    user_id: str = Depends(get_current_user_id),
) -> StreamingResponse:
    """Stream the grade first, then finish the same durable submission.

    A one-byte whitespace chunk flushes the headers immediately. The final body
    remains ordinary JSON, so clients without header streaming keep the legacy
    behavior and receive the complete response after persistence.
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
    )

    def stream_response():
        yield b" "
        response = dict(result)
        try:
            response = _persist_graded_answer(result=result, payload=payload, user_id=user_id)
        except HTTPException as exc:
            response.update(
                {
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
