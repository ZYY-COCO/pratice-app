from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.db import get_supabase_admin
from app.dependencies import get_current_user_id, get_optional_current_user_id
from app.schemas.community import (
    CommunityCommentItem,
    CommunityCommentPreview,
    CommunityCreateCommentRequest,
    CommunityCreateCommentResponse,
    CommunityImageUploadResponse,
    CommunityCreatePostRequest,
    CommunityLikeResponse,
    CommunityPostDetailResponse,
    CommunityPostItem,
    CommunityPostListResponse,
    CommunityPostStats,
    CommunityViewRequest,
    CommunityViewResponse,
)
from app.services.supabase_resilience import call_supabase


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/circle/community", tags=["考研圈"])
COMMUNITY_MEDIA_BUCKET = "circle-community-media"
MAX_COMMUNITY_IMAGE_BYTES = 8 * 1024 * 1024
COMMUNITY_IMAGE_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
COMMUNITY_POST_TYPES = {"chat", "experience"}
COMMUNITY_POST_TYPE_MARKER_KEY = "_circle_post_type"
_community_post_type_column_available: bool | None = None


def _relative_time(value: str | None) -> str:
    if not value:
        return "刚刚"

    try:
        current = datetime.now(timezone.utc)
        created_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        seconds = max(0, int((current - created_at.astimezone(timezone.utc)).total_seconds()))
    except (TypeError, ValueError):
        return "刚刚"

    if seconds < 60:
        return "刚刚"
    if seconds < 3600:
        return f"{seconds // 60} 分钟前"
    if seconds < 86400:
        return f"{seconds // 3600} 小时前"
    if seconds < 604800:
        return f"{seconds // 86400} 天前"
    return created_at.strftime("%Y-%m-%d")


def _first_character(value: str | None, fallback: str = "研") -> str:
    text = str(value or "").strip()
    return text[:1] if text else fallback


def _community_post_type(row: dict) -> str:
    """Read the durable column when available, with a legacy JSON marker fallback."""
    media = row.get("media")
    if isinstance(media, list):
        for item in media:
            if not isinstance(item, dict):
                continue
            marker = str(item.get(COMMUNITY_POST_TYPE_MARKER_KEY) or "")
            if marker in COMMUNITY_POST_TYPES:
                return marker

    post_type = str(row.get("post_type") or "")
    return post_type if post_type in COMMUNITY_POST_TYPES else "chat"


def _normalise_media(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [
        item
        for item in value
        if isinstance(item, dict) and COMMUNITY_POST_TYPE_MARKER_KEY not in item
    ][:9]


def _is_missing_post_type_column_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "post_type" in message and ("does not exist" in message or "42703" in message)


def _create_legacy_post_media(media: list[dict], post_type: str) -> list[dict]:
    return [*media, {COMMUNITY_POST_TYPE_MARKER_KEY: post_type}]


def _detect_community_image_content_type(data: bytes) -> tuple[str, str] | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", "jpg"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp", "webp"
    return None


def _ensure_community_media_bucket(storage) -> None:
    try:
        storage.get_bucket(COMMUNITY_MEDIA_BUCKET)
        return
    except Exception:
        pass

    try:
        storage.create_bucket(
            COMMUNITY_MEDIA_BUCKET,
            options={
                "public": True,
                "file_size_limit": MAX_COMMUNITY_IMAGE_BYTES,
                "allowed_mime_types": list(COMMUNITY_IMAGE_CONTENT_TYPES),
            },
        )
    except Exception:
        # Another request may have created the bucket at the same time.
        storage.get_bucket(COMMUNITY_MEDIA_BUCKET)


def _fetch_liked_post_ids(supabase, user_id: str | None, post_ids: list[str]) -> set[str]:
    if not user_id or not post_ids:
        return set()

    response = call_supabase(
        lambda: (
            supabase.table("circle_community_likes")
            .select("post_id")
            .eq("user_id", user_id)
            .in_("post_id", post_ids)
            .execute()
        ),
        operation_name="circle community like status lookup",
    )
    return {str(row.get("post_id")) for row in (response.data or []) if row.get("post_id")}


def _fetch_comment_previews(supabase, post_ids: list[str]) -> dict[str, list[CommunityCommentPreview]]:
    if not post_ids:
        return {}

    response = call_supabase(
        lambda: (
            supabase.table("circle_community_comments")
            .select("post_id,author_name,content,created_at")
            .in_("post_id", post_ids)
            .order("created_at", desc=True)
            .execute()
        ),
        operation_name="circle community comment preview lookup",
    )
    previews: dict[str, list[CommunityCommentPreview]] = {}
    for row in response.data or []:
        post_id = str(row.get("post_id") or "")
        if not post_id:
            continue
        post_previews = previews.setdefault(post_id, [])
        if len(post_previews) >= 3:
            continue
        post_previews.append(CommunityCommentPreview(
            author=str(row.get("author_name") or "研友"),
            text=str(row.get("content") or ""),
        ))
    return previews


def _post_item(
    row: dict,
    liked_post_ids: set[str],
    previews: dict[str, list[CommunityCommentPreview]],
) -> CommunityPostItem:
    post_id = str(row.get("id"))
    content = str(row.get("content") or "")
    comment_previews = previews.get(post_id, [])
    return CommunityPostItem(
        id=post_id,
        post_type=_community_post_type(row),
        category=str(row.get("category") or "备考日常"),
        author=str(row.get("author_name") or "研友"),
        avatar=_first_character(row.get("author_avatar") or row.get("author_name")),
        publish_time=_relative_time(row.get("created_at")),
        tone=str(row.get("author_tone") or "blue"),
        title=str(row.get("title") or ""),
        summary=content,
        content=content,
        media=_normalise_media(row.get("media")),
        comment_preview=comment_previews[0] if comment_previews else None,
        comment_previews=comment_previews,
        stats=CommunityPostStats(
            likes=int(row.get("like_count") or 0),
            comments=int(row.get("comment_count") or 0),
            views=int(row.get("view_count") or 0),
        ),
        liked=post_id in liked_post_ids,
    )


def _comment_item(row: dict, current_user_id: str | None) -> CommunityCommentItem:
    return CommunityCommentItem(
        id=str(row.get("id")),
        author=str(row.get("author_name") or "研友"),
        avatar=_first_character(row.get("author_avatar") or row.get("author_name")),
        content=str(row.get("content") or ""),
        created_at=row.get("created_at"),
        is_mine=bool(current_user_id and str(row.get("author_id") or "") == current_user_id),
    )


def _get_post_row(supabase, post_id: str) -> dict:
    response = call_supabase(
        lambda: (
            supabase.table("circle_community_posts")
            .select("*")
            .eq("id", post_id)
            .eq("is_published", True)
            .limit(1)
            .execute()
        ),
        operation_name="circle community post lookup",
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circle post not found")
    return response.data[0]


def _current_author(supabase, user_id: str) -> tuple[str, str]:
    response = call_supabase(
        lambda: (
            supabase.table("users")
            .select("nickname,email")
            .eq("id", user_id)
            .limit(1)
            .execute()
        ),
        operation_name="circle community author lookup",
    )
    profile = response.data[0] if response.data else {}
    nickname = str(profile.get("nickname") or "").strip()
    email = str(profile.get("email") or "").strip()
    name = nickname or (email.split("@", 1)[0] if "@" in email else "") or "研友"
    return name, _first_character(name)


def _raise_community_service_error(exc: Exception) -> None:
    logger.warning("Circle community service error (error_type=%s)", type(exc).__name__)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="考研圈服务暂时不可用，请稍后重试",
    ) from exc


@router.get("/posts", response_model=CommunityPostListResponse)
def list_community_posts(
    post_type: Literal["chat", "experience"] = Query(default="chat"),
    category: str | None = Query(default=None, max_length=24),
    limit: int = Query(default=50, ge=1, le=100),
    user_id: str | None = Depends(get_optional_current_user_id),
) -> CommunityPostListResponse:
    supabase = get_supabase_admin()
    try:
        query = (
            supabase.table("circle_community_posts")
            .select("*", count="exact")
            .eq("is_published", True)
            .order("created_at", desc=True)
            .limit(100)
        )
        if category and category != "全部":
            query = query.eq("category", category)

        response = call_supabase(query.execute, operation_name="circle community post list")
        rows = [
            row
            for row in (response.data or [])
            if _community_post_type(row) == post_type
        ][:limit]
        post_ids = [str(row.get("id")) for row in rows if row.get("id")]
        liked_post_ids = _fetch_liked_post_ids(supabase, user_id, post_ids)
        previews = _fetch_comment_previews(supabase, post_ids)
        return CommunityPostListResponse(
            items=[_post_item(row, liked_post_ids, previews) for row in rows],
            count=len(rows),
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_service_error(exc)


@router.get("/posts/{post_id}", response_model=CommunityPostDetailResponse)
def get_community_post(
    post_id: str,
    user_id: str | None = Depends(get_optional_current_user_id),
) -> CommunityPostDetailResponse:
    supabase = get_supabase_admin()
    try:
        row = _get_post_row(supabase, post_id)
        liked_post_ids = _fetch_liked_post_ids(supabase, user_id, [post_id])
        previews = _fetch_comment_previews(supabase, [post_id])
        comments_response = call_supabase(
            lambda: (
                supabase.table("circle_community_comments")
                .select("*")
                .eq("post_id", post_id)
                .order("created_at", desc=False)
                .limit(200)
                .execute()
            ),
            operation_name="circle community comment list",
        )
        return CommunityPostDetailResponse(
            post=_post_item(row, liked_post_ids, previews),
            comments=[_comment_item(item, user_id) for item in (comments_response.data or [])],
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_service_error(exc)


@router.post("/images", response_model=CommunityImageUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_community_image(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
) -> CommunityImageUploadResponse:
    data = await file.read(MAX_COMMUNITY_IMAGE_BYTES + 1)
    await file.close()

    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image file is empty")
    if len(data) > MAX_COMMUNITY_IMAGE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Each image must be 8 MB or smaller")

    detected = _detect_community_image_content_type(data)
    if not detected:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Images must be PNG, JPEG, or WebP files",
        )

    content_type, extension = detected
    storage_path = f"{user_id}/{uuid4().hex}.{extension}"
    supabase = get_supabase_admin()

    try:
        _ensure_community_media_bucket(supabase.storage)
        bucket = supabase.storage.from_(COMMUNITY_MEDIA_BUCKET)
        bucket.upload(
            storage_path,
            data,
            file_options={
                "content-type": content_type,
                "cache-control": "31536000",
                "upsert": "false",
            },
        )
        return CommunityImageUploadResponse(url=bucket.get_public_url(storage_path))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Circle community image upload failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image upload failed, please try again",
        ) from exc


@router.post("/posts", response_model=CommunityPostItem, status_code=status.HTTP_201_CREATED)
def create_community_post(
    payload: CommunityCreatePostRequest,
    user_id: str = Depends(get_current_user_id),
) -> CommunityPostItem:
    global _community_post_type_column_available

    supabase = get_supabase_admin()
    try:
        author_name, author_avatar = _current_author(supabase, user_id)
        media = [item.model_dump(by_alias=True) for item in payload.media[:9]]
        post_data = {
            "author_id": user_id,
            "author_name": author_name,
            "author_avatar": author_avatar,
            "author_tone": "blue",
            "category": payload.category.strip(),
            "title": payload.title.strip(),
            "content": payload.content.strip(),
            "media": media,
        }

        if _community_post_type_column_available is not False:
            try:
                response = call_supabase(
                    lambda: supabase.table("circle_community_posts").insert(
                        {**post_data, "post_type": payload.post_type}
                    ).execute(),
                    operation_name="circle community post create",
                )
                _community_post_type_column_available = True
            except Exception as exc:
                if not _is_missing_post_type_column_error(exc):
                    raise
                _community_post_type_column_available = False

        if _community_post_type_column_available is False:
            response = call_supabase(
                lambda: supabase.table("circle_community_posts").insert(
                    {
                        **post_data,
                        "media": _create_legacy_post_media(media, payload.post_type),
                    }
                ).execute(),
                operation_name="circle community legacy post create",
            )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Circle post create failed")
        return _post_item(response.data[0], set(), {})
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_service_error(exc)


@router.post("/posts/{post_id}/like", response_model=CommunityLikeResponse)
def toggle_community_like(
    post_id: str,
    user_id: str = Depends(get_current_user_id),
) -> CommunityLikeResponse:
    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: supabase.rpc(
                "circle_community_toggle_like",
                {"p_post_id": post_id, "p_user_id": user_id},
            ).execute(),
            operation_name="circle community like toggle",
        )
        row = (response.data or [None])[0]
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circle post not found")
        return CommunityLikeResponse(
            post_id=post_id,
            is_liked=bool(row.get("is_liked")),
            like_count=int(row.get("like_count") or 0),
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_service_error(exc)


@router.post(
    "/posts/{post_id}/comments",
    response_model=CommunityCreateCommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_community_comment(
    post_id: str,
    payload: CommunityCreateCommentRequest,
    user_id: str = Depends(get_current_user_id),
) -> CommunityCreateCommentResponse:
    supabase = get_supabase_admin()
    try:
        _get_post_row(supabase, post_id)
        author_name, author_avatar = _current_author(supabase, user_id)
        comment_response = call_supabase(
            lambda: supabase.table("circle_community_comments").insert(
                {
                    "post_id": post_id,
                    "author_id": user_id,
                    "author_name": author_name,
                    "author_avatar": author_avatar,
                    "content": payload.content.strip(),
                }
            ).execute(),
            operation_name="circle community comment create",
        )
        if not comment_response.data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Circle comment create failed")

        updated_post = _get_post_row(supabase, post_id)
        return CommunityCreateCommentResponse(
            comment=_comment_item(comment_response.data[0], user_id),
            comment_count=int(updated_post.get("comment_count") or 0),
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_service_error(exc)


@router.post("/posts/{post_id}/view", response_model=CommunityViewResponse)
def register_community_view(
    post_id: str,
    payload: CommunityViewRequest,
    user_id: str | None = Depends(get_optional_current_user_id),
) -> CommunityViewResponse:
    anonymous_id: str | None = None
    if not user_id:
        try:
            anonymous_id = str(UUID(str(payload.anonymous_id or "")))
        except (TypeError, ValueError):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid anonymous viewer")

    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: supabase.rpc(
                "circle_community_register_view",
                {
                    "p_post_id": post_id,
                    "p_user_id": user_id,
                    "p_anonymous_id": anonymous_id,
                },
            ).execute(),
            operation_name="circle community effective view registration",
        )
        row = (response.data or [None])[0]
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circle post not found")
        return CommunityViewResponse(
            post_id=post_id,
            counted=bool(row.get("counted")),
            view_count=int(row.get("view_count") or 0),
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_service_error(exc)
