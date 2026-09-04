"""Authenticated API surface for adaptive practice V1."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, TypeVar

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import get_settings
from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.adaptive_practice import (
    AdaptivePracticeItemEventRequest,
    AdaptivePracticeItemEventResponse,
    CompleteAdaptivePracticeSessionRequest,
    CompleteAdaptivePracticeSessionResponse,
    CreateAdaptivePracticeSessionRequest,
    CreateAdaptivePracticeSessionResponse,
    NextAdaptivePracticeItemResponse,
    SubmitAdaptiveComprehensiveSessionRequest,
    SubmitAdaptiveComprehensiveSessionResponse,
)
from app.services.adaptive_practice import (
    complete_session,
    create_adaptive_session,
    get_next_adaptive_item,
    record_item_event,
    submit_comprehensive_session,
)
from app.services.adaptive_rollout import evaluate_adaptive_rollout
from app.services.supabase_resilience import is_missing_supabase_relation_error


router = APIRouter(prefix="/adaptive-practice", tags=["个性化练习"])
Result = TypeVar("Result")
logger = logging.getLogger(__name__)


def _call_service(operation: Callable[[], Result]) -> Result:
    try:
        return operation()
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="个性化出题数据迁移尚未启用",
            ) from exc
        raise


@router.post("/sessions", response_model=CreateAdaptivePracticeSessionResponse)
def create_session(
    payload: CreateAdaptivePracticeSessionRequest,
    user_id: str = Depends(get_current_user_id),
) -> CreateAdaptivePracticeSessionResponse:
    decision = evaluate_adaptive_rollout(get_settings(), user_id)
    logger.info(
        "Adaptive practice rollout decision "
        "source=%s rollout_basis_points=%s bucket=%s",
        decision.decision_source,
        decision.rollout_basis_points,
        decision.bucket,
    )
    if not decision.allowed and not payload.resume_existing_session:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="个性化出题正在灰度开放",
        )
    supabase = get_supabase_admin()
    result = _call_service(
        lambda: create_adaptive_session(
            supabase,
            user_id=user_id,
            payload=payload,
            allow_new_session=decision.allowed,
        )
    )
    if not decision.allowed:
        logger.info(
            "Adaptive practice rollout recovery outcome=idempotent_resume "
            "original_source=%s",
            decision.decision_source,
        )
    return CreateAdaptivePracticeSessionResponse(**result)


@router.get("/sessions/{session_id}/next", response_model=NextAdaptivePracticeItemResponse)
def next_item(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
) -> NextAdaptivePracticeItemResponse:
    supabase = get_supabase_admin()
    result = _call_service(
        lambda: get_next_adaptive_item(supabase, user_id=user_id, session_id=session_id)
    )
    return NextAdaptivePracticeItemResponse(**result)


@router.post(
    "/sessions/{session_id}/items/{item_id}/events",
    response_model=AdaptivePracticeItemEventResponse,
)
def item_event(
    session_id: str,
    item_id: str,
    payload: AdaptivePracticeItemEventRequest,
    user_id: str = Depends(get_current_user_id),
) -> AdaptivePracticeItemEventResponse:
    supabase = get_supabase_admin()
    result = _call_service(
        lambda: record_item_event(
            supabase,
            user_id=user_id,
            session_id=session_id,
            item_id=item_id,
            event_type=payload.event_type,
        )
    )
    return AdaptivePracticeItemEventResponse(**result)


@router.post(
    "/sessions/{session_id}/complete",
    response_model=CompleteAdaptivePracticeSessionResponse,
)
def finish_session(
    session_id: str,
    payload: CompleteAdaptivePracticeSessionRequest,
    user_id: str = Depends(get_current_user_id),
) -> CompleteAdaptivePracticeSessionResponse:
    supabase = get_supabase_admin()
    result = _call_service(
        lambda: complete_session(
            supabase,
            user_id=user_id,
            session_id=session_id,
            reason=payload.reason,
        )
    )
    return CompleteAdaptivePracticeSessionResponse(**result)


@router.post(
    "/sessions/{session_id}/submit",
    response_model=SubmitAdaptiveComprehensiveSessionResponse,
)
def submit_comprehensive(
    session_id: str,
    payload: SubmitAdaptiveComprehensiveSessionRequest,
    user_id: str = Depends(get_current_user_id),
) -> SubmitAdaptiveComprehensiveSessionResponse:
    supabase = get_supabase_admin()
    result = _call_service(
        lambda: submit_comprehensive_session(
            supabase,
            user_id=user_id,
            session_id=session_id,
            payload=payload,
        )
    )
    return SubmitAdaptiveComprehensiveSessionResponse(**result)
