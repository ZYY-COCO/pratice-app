from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.favorites import (
    FavoriteQuestionItem,
    FavoriteQuestionListResponse,
    FavoriteStatusResponse,
    FavoriteToggleRequest,
    FavoriteToggleResponse,
)
from app.schemas.questions import Question

router = APIRouter(prefix="/favorites", tags=["收藏夹"])


@router.get("", response_model=FavoriteQuestionListResponse)
def list_favorites(
    user_id: str = Depends(get_current_user_id),
    subject: str | None = None,
    limit: int = Query(default=100, ge=1, le=200),
) -> FavoriteQuestionListResponse:
    supabase = get_supabase_admin()
    response = (
        supabase.table("favorite_questions")
        .select("id, question_id, created_at, questions(*)")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    items: list[FavoriteQuestionItem] = []
    for row in response.data or []:
        question = row.get("questions")
        if subject and question and question.get("subject") != subject:
            continue
        items.append(
            FavoriteQuestionItem(
                id=row["id"],
                question_id=row["question_id"],
                created_at=row["created_at"],
                question=Question(**question) if question else None,
            )
        )
    return FavoriteQuestionListResponse(items=items, count=len(items))


@router.get("/status", response_model=FavoriteStatusResponse)
def favorite_status(
    question_id: str,
    user_id: str = Depends(get_current_user_id),
) -> FavoriteStatusResponse:
    supabase = get_supabase_admin()
    response = (
        supabase.table("favorite_questions")
        .select("id")
        .eq("user_id", user_id)
        .eq("question_id", question_id)
        .limit(1)
        .execute()
    )
    return FavoriteStatusResponse(question_id=question_id, is_favorited=bool(response.data))


@router.post("/toggle", response_model=FavoriteToggleResponse)
def toggle_favorite(
    payload: FavoriteToggleRequest,
    user_id: str = Depends(get_current_user_id),
) -> FavoriteToggleResponse:
    supabase = get_supabase_admin()
    question_response = (
        supabase.table("questions").select("id").eq("id", payload.question_id).limit(1).execute()
    )
    if not question_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    existing_response = (
        supabase.table("favorite_questions")
        .select("id")
        .eq("user_id", user_id)
        .eq("question_id", payload.question_id)
        .limit(1)
        .execute()
    )

    if existing_response.data:
        favorite_id = existing_response.data[0]["id"]
        supabase.table("favorite_questions").delete().eq("id", favorite_id).execute()
        return FavoriteToggleResponse(question_id=payload.question_id, is_favorited=False)

    supabase.table("favorite_questions").insert(
        {"user_id": user_id, "question_id": payload.question_id}
    ).execute()
    return FavoriteToggleResponse(question_id=payload.question_id, is_favorited=True)
