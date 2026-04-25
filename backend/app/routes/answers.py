from fastapi import APIRouter, BackgroundTasks, Depends

from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.answers import SubmitAnswerRequest, SubmitAnswerResponse
from app.services.answers import persist_answer_submission, submit_answer

router = APIRouter(prefix="/answers", tags=["作答"])


@router.post("/submit", response_model=SubmitAnswerResponse)
def submit(
    payload: SubmitAnswerRequest,
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
