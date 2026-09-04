from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status

from app.db import get_supabase_admin
from app.dependencies import get_current_user_id, get_optional_current_user_id
from app.schemas.community import (
    COMMUNITY_EXPERIENCE_CATEGORIES,
    COMMUNITY_EXPERIENCE_STAGES,
    CommunityCommentItem,
    CommunityCommentListResponse,
    CommunityCommentLikeResponse,
    CommunityCommentPreview,
    CommunityModerationAppealCreateRequest,
    CommunityModerationAppealItem,
    CommunityModerationStatusItem,
    CommunityModerationStatusListResponse,
    CommunityCreateCommentRequest,
    CommunityCreateCommentResponse,
    CommunityCreateReportRequest,
    CommunityDeleteCommentResponse,
    CommunityDeletePostsRequest,
    CommunityDeletePostsResponse,
    CommunityImageUploadResponse,
    CommunityLikeItem,
    CommunityLikeListResponse,
    CommunityCreatePostRequest,
    CommunityLikeResponse,
    CommunityLikedPostItem,
    CommunityLikedPostListResponse,
    CommunityExperienceReviewHistoryItem,
    CommunityOwnPostDetailResponse,
    CommunityPostDetailResponse,
    CommunityPostItem,
    CommunityPostListResponse,
    CommunityReportItem,
    CommunityReportListResponse,
    CommunityResubmitExperiencePostRequest,
    CommunityPostStats,
    CommunitySetLikeRequest,
    CommunityViewRequest,
    CommunityViewResponse,
)
from app.services.supabase_resilience import (
    call_supabase,
    is_missing_supabase_relation_error,
    is_transient_supabase_error,
)
from app.services.user_notifications import create_user_notification
from app.utils.cursor_pagination import (
    build_keyset_filter,
    cursor_datetime,
    cursor_integer,
    cursor_uuid,
    decode_page_cursor,
    encode_page_cursor,
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/circle/community", tags=["考研圈"])
COMMUNITY_MEDIA_BUCKET = "circle-community-media"
COMMUNITY_FEED_VIEW = "circle_community_feed_rows"
COMMUNITY_FEED_VIEW_FIELDS = (
    "id,author_id,author_name,author_avatar,author_tone,post_type,category,experience_stages,"
    "title,content,media,media_count,like_count,comment_count,view_count,is_published,is_featured,"
    "review_status,review_version,review_reason_code,review_note,reviewed_at,submitted_at,created_at"
)
COMMUNITY_FEED_TABLE_FIELDS = "*"
MAX_COMMUNITY_IMAGE_BYTES = 8 * 1024 * 1024
COMMUNITY_IMAGE_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
COMMUNITY_POST_TYPES = {"chat", "experience"}
COMMUNITY_POST_TYPE_MARKER_KEY = "_circle_post_type"
COMMUNITY_EXPERIENCE_STAGES_MARKER_KEY = "_circle_experience_stages"
COMMUNITY_AUTHOR_DELETED_MARKER_KEY = "_circle_author_deleted_at"
COMMUNITY_EXPERIENCE_REVIEW_COLUMNS = {
    "review_status",
    "review_version",
    "review_reason_code",
    "review_note",
    "reviewed_by",
    "reviewed_at",
    "submitted_at",
}
COMMUNITY_STAT_UPDATE_ATTEMPTS = 4
COMMUNITY_APPEAL_FIELDS = (
    "id,appellant_user_id,target_type,post_id,comment_id,content,status,moderation_action,"
    "admin_note,handled_by,handled_at,created_at,updated_at"
)
COMMUNITY_POST_REPORT_REASONS = {
    "虚假或误导信息",
    "广告或引流",
    "骚扰、辱骂或不当言行",
    "泄露隐私",
    "违规交易或收费",
    "其他问题",
}
COMMUNITY_COMMENT_REPORT_REASONS = {
    "骚扰、辱骂或不当言行",
    "广告或引流",
    "虚假或误导信息",
    "泄露隐私",
    "其他问题",
}
COMMUNITY_RETIRED_SEED_POST_IDS = frozenset(
    {
        "0b46a665-7b7d-4e0c-a62c-f42282f4e101",
        "2fd58d9c-7c70-4d90-9d88-3a261c4847af",
        "423377f8-7fcf-4ddb-a34d-6ea7e25504da",
        "f7cd37cc-bf32-4873-b954-ffa5522d6e0b",
        "7aa84b22-9b9d-4d28-9ef8-7a09d42b0101",
        "7aa84b22-9b9d-4d28-9ef8-7a09d42b0102",
        "7aa84b22-9b9d-4d28-9ef8-7a09d42b0103",
        "7aa84b22-9b9d-4d28-9ef8-7a09d42b0104",
        "7aa84b22-9b9d-4d28-9ef8-7a09d42b0105",
    }
)
_community_post_type_column_available: bool | None = None
_community_client_request_id_column_available: bool | None = None
_community_experience_stages_column_available: bool | None = None
_community_experience_review_columns_available: bool | None = None
_community_comment_visibility_column_available: bool | None = None
_community_feed_view_available: bool | None = None
_community_comment_preview_rpc_available: bool | None = None
_community_comment_create_rpc_available: bool | None = None
_community_comment_client_request_id_column_available: bool | None = None
_community_set_like_rpc_available: bool | None = None
_community_set_comment_like_rpc_available: bool | None = None
_community_author_deleted_column_available: bool | None = None
_community_admin_deleted_column_available: bool | None = None


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


def _community_explicit_experience_stages(row: dict) -> list[str]:
    if _community_post_type(row) != "experience":
        return []

    allowed_stages = COMMUNITY_EXPERIENCE_STAGES | {"申请制"}
    stored_stages = row.get("experience_stages")
    if isinstance(stored_stages, list):
        normalized_stages = list(dict.fromkeys(
            stage
            for stage in (str(value or "").strip() for value in stored_stages)
            if stage in allowed_stages
        ))
        if normalized_stages:
            return normalized_stages

    media = row.get("media")
    if isinstance(media, list):
        for item in media:
            if not isinstance(item, dict):
                continue
            marker = item.get(COMMUNITY_EXPERIENCE_STAGES_MARKER_KEY)
            if not isinstance(marker, list):
                continue
            return list(dict.fromkeys(
                stage
                for stage in (str(value or "").strip() for value in marker)
                if stage in allowed_stages
            ))

    return []


def _community_experience_category(row: dict) -> str:
    raw_category = str(row.get("category") or "").strip()
    if _community_post_type(row) != "experience":
        return raw_category
    if raw_category == "申请制" or "申请制" in _community_explicit_experience_stages(row):
        return "申请制"
    return raw_category


def _community_experience_stages(row: dict) -> list[str]:
    if _community_post_type(row) != "experience":
        return []

    normalized_stages = [
        stage
        for stage in _community_explicit_experience_stages(row)
        if stage in COMMUNITY_EXPERIENCE_STAGES
    ]
    if normalized_stages:
        return normalized_stages

    legacy_category = str(row.get("category") or "").strip()
    if legacy_category == "复试":
        return ["复试"]
    if legacy_category == "专业课":
        return ["初试"]
    return []


def _matches_community_experience_stage(row: dict, stage: str) -> bool:
    normalized_stage = str(stage or "").strip()
    return not normalized_stage or normalized_stage in _community_experience_stages(row)


def _normalize_community_experience_filters(
    post_type: str,
    category: str | None,
    experience_stage: str | None,
) -> tuple[str, str]:
    normalized_category = str(category or "").strip()
    if normalized_category == "全部":
        normalized_category = ""
    if post_type != "experience":
        return normalized_category, ""

    normalized_stage = str(experience_stage or "").strip()
    if normalized_stage == "申请制":
        # 兼容旧客户端：申请制曾作为 experience_stage 传入，现已归入考试类别。
        return "申请制", ""
    return normalized_category, normalized_stage


def _matches_community_search(row: dict, keyword: str) -> bool:
    normalized_keyword = str(keyword or "").strip().casefold()
    if not normalized_keyword:
        return True
    searchable = " ".join([
        str(row.get("author_name") or ""),
        str(row.get("category") or ""),
        str(row.get("title") or ""),
        str(row.get("content") or ""),
    ]).casefold()
    return normalized_keyword in searchable


def _community_review_status(row: dict) -> str:
    if _community_post_type(row) != "experience":
        return "approved"
    review_status = str(row.get("review_status") or "").strip().lower()
    if review_status in {"pending", "approved", "rejected"}:
        return review_status
    return "pending" if row.get("is_published") is False and not row.get("moderation_note") else "approved"


def _is_public_verified_experience_post(row: dict, verified_author_ids: set[str]) -> bool:
    return (
        _community_post_type(row) == "experience"
        and str(row.get("author_id") or "") in verified_author_ids
        and _community_experience_category(row) in COMMUNITY_EXPERIENCE_CATEGORIES
        and _community_review_status(row) == "approved"
    )


def _normalise_media(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [
        item
        for item in value
        if (
            isinstance(item, dict)
            and COMMUNITY_POST_TYPE_MARKER_KEY not in item
            and COMMUNITY_EXPERIENCE_STAGES_MARKER_KEY not in item
            and COMMUNITY_AUTHOR_DELETED_MARKER_KEY not in item
        )
    ][:9]


def _is_author_deleted_post(row: dict) -> bool:
    if row.get("author_deleted_at"):
        return True
    media = row.get("media")
    return isinstance(media, list) and any(
        isinstance(item, dict) and item.get(COMMUNITY_AUTHOR_DELETED_MARKER_KEY)
        for item in media
    )


def _is_admin_deleted_post(row: dict) -> bool:
    return bool(row.get("admin_deleted_at"))


def _legacy_author_delete_posts(
    supabase,
    *,
    post_ids: list[str],
    user_id: str,
    deleted_at: str,
) -> list[str]:
    """Rolling-schema fallback that hides posts without breaking governance foreign keys."""

    response = call_supabase(
        lambda: (
            supabase.table("circle_community_posts")
            .select("id,media")
            .in_("id", post_ids)
            .eq("author_id", user_id)
            .execute()
        ),
        operation_name="circle community legacy author delete lookup",
    )
    rows = [row for row in (response.data or []) if not _is_author_deleted_post(row)]
    deleted_post_ids: list[str] = []
    for row in rows:
        post_id = str(row.get("id") or "")
        if not post_id:
            continue
        media = [
            item
            for item in (row.get("media") or [])
            if isinstance(item, dict) and COMMUNITY_AUTHOR_DELETED_MARKER_KEY not in item
        ]
        media = [{COMMUNITY_AUTHOR_DELETED_MARKER_KEY: deleted_at}, *media]
        update_response = call_supabase(
            lambda post_id=post_id, media=media: (
                supabase.table("circle_community_posts")
                .update({
                    "media": media,
                    "is_published": False,
                    "is_featured": False,
                    "updated_at": deleted_at,
                })
                .eq("id", post_id)
                .eq("author_id", user_id)
                .execute()
            ),
            operation_name="circle community legacy author delete",
        )
        if update_response.data:
            deleted_post_ids.append(post_id)
    return deleted_post_ids


def _is_missing_post_type_column_error(exc: Exception) -> bool:
    return _is_missing_community_post_column_error(exc, "post_type")


def _is_missing_community_post_column_error(exc: Exception, column_name: str) -> bool:
    message = str(exc).lower()
    normalized_column = str(column_name or "").strip().lower()
    return bool(normalized_column) and normalized_column in message and any(
        marker in message
        for marker in ("does not exist", "could not find", "schema cache", "42703", "pgrst204")
    )


def _is_missing_comment_visibility_column_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "is_published" in message
        and ("circle_community_comments" in message or "42703" in message or "does not exist" in message)
    )


def _is_community_comment_rpc_compatibility_error(exc: Exception) -> bool:
    """Whether the atomic comment RPC is absent or has a known migration defect."""

    message = str(exc).lower()
    provider_code = str(getattr(exc, "code", "") or "").strip()
    return is_missing_supabase_relation_error(exc) or (
        (provider_code == "42702" or "42702" in message)
        and "ambiguous" in message
        and ("author_id" in message or "client_request_id" in message)
    )


def _create_legacy_post_media(media: list[dict], post_type: str) -> list[dict]:
    return [*media, {COMMUNITY_POST_TYPE_MARKER_KEY: post_type}]


def _create_post_media(
    media: list[dict],
    post_type: str,
    experience_stages: list[str],
    *,
    use_legacy_stage_marker: bool = False,
) -> list[dict]:
    if post_type != "experience" or not use_legacy_stage_marker:
        return media
    return [
        *media,
        {COMMUNITY_EXPERIENCE_STAGES_MARKER_KEY: experience_stages},
    ]


def _find_community_post_by_request_id(
    supabase,
    *,
    author_id: str,
    client_request_id: str,
) -> dict | None:
    response = call_supabase(
        lambda: (
            supabase.table("circle_community_posts")
            .select("*")
            .eq("author_id", author_id)
            .eq("client_request_id", client_request_id)
            .limit(1)
            .execute()
        ),
        operation_name="circle community post idempotency lookup",
    )
    return (response.data or [None])[0]


def _lookup_idempotent_community_post(
    supabase,
    *,
    author_id: str,
    client_request_id: str,
) -> dict | None:
    global _community_client_request_id_column_available

    if _community_client_request_id_column_available is False:
        return None
    try:
        existing = _find_community_post_by_request_id(
            supabase,
            author_id=author_id,
            client_request_id=client_request_id,
        )
    except Exception as exc:
        if not _is_missing_community_post_column_error(exc, "client_request_id"):
            raise
        _community_client_request_id_column_available = False
        return None
    _community_client_request_id_column_available = True
    return existing


def _insert_community_post_with_compatibility(
    supabase,
    *,
    post_data: dict,
    post_type: str,
    experience_stages: list[str],
    client_request_id: str,
) -> dict | None:
    """Insert against both migrated and transitional community post schemas."""

    global _community_client_request_id_column_available
    global _community_experience_stages_column_available
    global _community_experience_review_columns_available
    global _community_post_type_column_available

    base_post_data = {
        key: value
        for key, value in post_data.items()
        if key not in COMMUNITY_EXPERIENCE_REVIEW_COLUMNS
    }
    review_post_data = {
        key: value
        for key, value in post_data.items()
        if key in COMMUNITY_EXPERIENCE_REVIEW_COLUMNS
    }

    for _ in range(6):
        include_client_request_id = _community_client_request_id_column_available is not False
        include_experience_stages = _community_experience_stages_column_available is not False
        include_review_columns = (
            bool(review_post_data)
            and _community_experience_review_columns_available is not False
        )
        include_post_type = _community_post_type_column_available is not False

        insert_data = {
            **base_post_data,
            "media": _create_post_media(
                list(base_post_data.get("media") or []),
                post_type,
                experience_stages,
                use_legacy_stage_marker=not include_experience_stages,
            ),
        }
        if include_review_columns:
            insert_data.update(review_post_data)
        if include_client_request_id:
            insert_data["client_request_id"] = client_request_id
        if include_experience_stages:
            insert_data["experience_stages"] = experience_stages
        if include_post_type:
            insert_data["post_type"] = post_type
        else:
            insert_data["media"] = _create_legacy_post_media(insert_data["media"], post_type)

        try:
            response = call_supabase(
                lambda insert_data=insert_data: (
                    supabase.table("circle_community_posts").insert(insert_data).execute()
                ),
                operation_name="circle community post create",
            )
        except Exception as exc:
            if (
                include_client_request_id
                and _is_missing_community_post_column_error(exc, "client_request_id")
            ):
                _community_client_request_id_column_available = False
                continue
            if (
                include_experience_stages
                and _is_missing_community_post_column_error(exc, "experience_stages")
            ):
                _community_experience_stages_column_available = False
                continue
            if include_post_type and _is_missing_post_type_column_error(exc):
                _community_post_type_column_available = False
                continue
            if include_review_columns and any(
                _is_missing_community_post_column_error(exc, column_name)
                for column_name in COMMUNITY_EXPERIENCE_REVIEW_COLUMNS
            ):
                _community_experience_review_columns_available = False
                continue
            if _is_duplicate_community_interaction_error(exc) and include_client_request_id:
                existing = _find_community_post_by_request_id(
                    supabase,
                    author_id=str(post_data.get("author_id") or ""),
                    client_request_id=client_request_id,
                )
                if existing:
                    _community_client_request_id_column_available = True
                    return existing
            raise

        if include_client_request_id:
            _community_client_request_id_column_available = True
        if include_experience_stages:
            _community_experience_stages_column_available = True
        if include_post_type:
            _community_post_type_column_available = True
        if include_review_columns:
            _community_experience_review_columns_available = True
        return (response.data or [None])[0]

    raise RuntimeError("Community post schema compatibility retries exhausted")


def _detect_community_image_content_type(data: bytes) -> tuple[str, str] | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", "jpg"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp", "webp"
    return None


def _build_community_thumbnail(data: bytes) -> bytes | None:
    """Create a compact feed image while preserving the separately stored original."""

    try:
        from PIL import Image, ImageOps

        with Image.open(BytesIO(data)) as source:
            image = ImageOps.exif_transpose(source)
            image.thumbnail((720, 720), Image.Resampling.LANCZOS)
            if image.mode not in {"RGB", "RGBA"}:
                image = image.convert("RGBA" if "transparency" in image.info else "RGB")
            output = BytesIO()
            image.save(output, format="WEBP", quality=78, method=4)
            thumbnail = output.getvalue()
            return thumbnail if thumbnail else None
    except ImportError:
        logger.warning("Pillow is not installed; community thumbnail generation skipped")
    except Exception as exc:
        logger.warning("Community thumbnail generation skipped (error_type=%s)", type(exc).__name__)
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


def _fetch_liked_comment_ids(supabase, user_id: str | None, comment_ids: list[str]) -> set[str]:
    if not user_id or not comment_ids:
        return set()

    response = call_supabase(
        lambda: (
            supabase.table("circle_community_comment_likes")
            .select("comment_id")
            .eq("user_id", user_id)
            .in_("comment_id", comment_ids)
            .execute()
        ),
        operation_name="circle community comment like status lookup",
    )
    return {str(row.get("comment_id")) for row in (response.data or []) if row.get("comment_id")}


def _fetch_community_profiles(supabase, user_ids: list[str]) -> dict[str, dict]:
    unique_user_ids = list(dict.fromkeys(user_id for user_id in user_ids if user_id))
    if not unique_user_ids:
        return {}

    response = call_supabase(
        lambda: (
            supabase.table("users")
            .select("id,nickname,email,avatar_url")
            .in_("id", unique_user_ids)
            .execute()
        ),
        operation_name="circle community profile lookup",
    )
    return {
        str(profile.get("id")): profile
        for profile in (response.data or [])
        if profile.get("id")
    }


def _fetch_verified_mentor_owner_ids(supabase, user_ids: list[str]) -> set[str]:
    """Return account IDs that currently own a visible, verified mentor profile."""

    ids = list(dict.fromkeys(str(user_id) for user_id in user_ids if user_id))
    if not ids:
        return set()
    response = call_supabase(
        lambda: (
            supabase.table("mentor_profiles")
            .select("owner_user_id")
            .in_("owner_user_id", ids)
            .eq("verification_status", "verified")
            .eq("is_published", True)
            .execute()
        ),
        operation_name="circle community verified author lookup",
    )
    return {
        str(row.get("owner_user_id") or "")
        for row in (response.data or [])
        if row.get("owner_user_id")
    }


def _community_avatar_url(row: dict, profiles: dict[str, dict]) -> str | None:
    profile = profiles.get(str(row.get("author_id") or ""), {})
    avatar_url = str(profile.get("avatar_url") or "").strip()
    return avatar_url or None


def _community_author_display(row: dict, profiles: dict[str, dict]) -> tuple[str, str]:
    """Resolve public community identity from the account profile, never mentor review data."""

    profile = profiles.get(str(row.get("author_id") or ""), {})
    nickname = str(profile.get("nickname") or "").strip()
    email = str(profile.get("email") or "").strip()
    email_name = email.split("@", 1)[0] if "@" in email else ""
    account_name = nickname or email_name
    stored_name = str(row.get("author_name") or "").strip()
    author_name = account_name or ("研友" if _community_post_type(row) == "experience" else stored_name) or "研友"
    avatar_source = author_name if account_name else (row.get("author_avatar") or author_name)
    return author_name, _first_character(avatar_source)


def _fetch_comment_previews(supabase, post_ids: list[str]) -> dict[str, list[CommunityCommentPreview]]:
    global _community_comment_preview_rpc_available, _community_comment_visibility_column_available
    if not post_ids:
        return {}

    if _community_comment_preview_rpc_available is not False and hasattr(supabase, "rpc"):
        try:
            response = call_supabase(
                lambda: supabase.rpc(
                    "circle_community_comment_previews",
                    {
                        "p_post_ids": post_ids,
                        "p_limit_per_post": 3,
                    },
                ).execute(),
                operation_name="circle community bounded comment preview lookup",
            )
            _community_comment_preview_rpc_available = True
            previews: dict[str, list[CommunityCommentPreview]] = {}
            for row in response.data or []:
                post_id = str(row.get("post_id") or "")
                if not post_id:
                    continue
                previews.setdefault(post_id, []).append(CommunityCommentPreview(
                    id=str(row.get("id") or "") or None,
                    author=str(row.get("author_name") or "研友"),
                    text=str(row.get("content") or ""),
                ))
            return previews
        except Exception as exc:
            if not is_missing_supabase_relation_error(exc):
                raise
            _community_comment_preview_rpc_available = False
            logger.info("Bounded community comment preview RPC unavailable; using compatibility query")

    def fetch_preview_rows(include_visibility: bool):
        query = (
            supabase.table("circle_community_comments")
            .select("id,post_id,author_name,content,created_at")
            .in_("post_id", post_ids)
            .order("created_at", desc=True)
        )
        if include_visibility:
            query = query.eq("is_published", True)
        return call_supabase(
            query.execute,
            operation_name="circle community comment preview lookup",
        )

    if _community_comment_visibility_column_available is not False:
        try:
            response = fetch_preview_rows(True)
            _community_comment_visibility_column_available = True
        except Exception as exc:
            if not _is_missing_comment_visibility_column_error(exc):
                raise
            _community_comment_visibility_column_available = False
            response = fetch_preview_rows(False)
    else:
        response = fetch_preview_rows(False)
    previews: dict[str, list[CommunityCommentPreview]] = {}
    for row in response.data or []:
        post_id = str(row.get("post_id") or "")
        if not post_id:
            continue
        post_previews = previews.setdefault(post_id, [])
        if len(post_previews) >= 3:
            continue
        post_previews.append(CommunityCommentPreview(
            id=str(row.get("id") or "") or None,
            author=str(row.get("author_name") or "研友"),
            text=str(row.get("content") or ""),
        ))
    return previews


def _post_item(
    row: dict,
    liked_post_ids: set[str],
    previews: dict[str, list[CommunityCommentPreview]],
    profiles: dict[str, dict],
    verified_author_ids: set[str] | None = None,
    *,
    compact: bool = False,
    current_user_id: str | None = None,
) -> CommunityPostItem:
    post_id = str(row.get("id"))
    content = str(row.get("content") or "")
    normalized_media = _normalise_media(row.get("media"))
    media_count = max(0, int(row.get("media_count") or len(normalized_media)))
    if compact:
        content = content[:320]
        normalized_media = normalized_media[:2]
    comment_previews = previews.get(post_id, [])
    author_name, author_avatar = _community_author_display(row, profiles)
    return CommunityPostItem(
        id=post_id,
        post_type=_community_post_type(row),
        category=(
            _community_experience_category(row)
            if _community_post_type(row) == "experience"
            else str(row.get("category") or "备考日常")
        ),
        experience_stages=_community_experience_stages(row),
        author=author_name,
        avatar=author_avatar,
        avatar_url=_community_avatar_url(row, profiles),
        publish_time=_relative_time(row.get("created_at")),
        tone=str(row.get("author_tone") or "blue"),
        title=str(row.get("title") or ""),
        summary=content,
        content="" if compact else content,
        media=normalized_media,
        media_count=media_count,
        comment_preview=comment_previews[0] if comment_previews else None,
        comment_previews=comment_previews,
        stats=CommunityPostStats(
            likes=int(row.get("like_count") or 0),
            comments=int(row.get("comment_count") or 0),
            views=int(row.get("view_count") or 0),
        ),
        is_featured=bool(row.get("is_featured")),
        liked=post_id in liked_post_ids,
        is_mine=bool(current_user_id and str(row.get("author_id") or "") == current_user_id),
        author_verified=str(row.get("author_id") or "") in (verified_author_ids or set()),
        is_published=bool(row.get("is_published", True)),
        review_status=_community_review_status(row),
        review_version=max(0, int(row.get("review_version") or 0)),
        review_reason_code=str(row.get("review_reason_code") or "").strip() or None,
        review_note=str(row.get("review_note") or "").strip() or None,
        reviewed_at=row.get("reviewed_at"),
        submitted_at=row.get("submitted_at"),
    )


def _comment_item(
    row: dict,
    current_user_id: str | None,
    profiles: dict[str, dict],
    liked_comment_ids: set[str],
) -> CommunityCommentItem:
    comment_id = str(row.get("id"))
    return CommunityCommentItem(
        id=comment_id,
        author=str(row.get("author_name") or "研友"),
        avatar=_first_character(row.get("author_avatar") or row.get("author_name")),
        avatar_url=_community_avatar_url(row, profiles),
        content=str(row.get("content") or ""),
        created_at=row.get("created_at"),
        is_mine=bool(current_user_id and str(row.get("author_id") or "") == current_user_id),
        like_count=int(row.get("like_count") or 0),
        liked=comment_id in liked_comment_ids,
    )


def _fetch_community_comment_page(
    supabase,
    *,
    post_id: str,
    limit: int,
    cursor: str | None,
) -> tuple[list[dict], str | None, bool]:
    """Fetch one bounded page of comments, newest page first and chronological within the page."""

    global _community_comment_visibility_column_available
    cursor_context = {"post_id": post_id}
    cursor_payload = decode_page_cursor(
        cursor,
        kind="community_comments",
        context=cursor_context,
    )

    def fetch_rows(include_visibility: bool):
        query = (
            supabase.table("circle_community_comments")
            .select("*")
            .eq("post_id", post_id)
        )
        if include_visibility:
            query = query.eq("is_published", True)
        if cursor_payload:
            query = query.or_(build_keyset_filter([
                ("created_at", "desc", cursor_datetime(cursor_payload, "created_at")),
                ("id", "desc", cursor_uuid(cursor_payload, "id")),
            ]))
        return call_supabase(
            lambda: (
                query.order("created_at", desc=True)
                .order("id", desc=True)
                .limit(limit + 1)
                .execute()
            ),
            operation_name="circle community paged comment list",
        )

    if _community_comment_visibility_column_available is not False:
        try:
            response = fetch_rows(True)
            _community_comment_visibility_column_available = True
        except Exception as exc:
            if not _is_missing_comment_visibility_column_error(exc):
                raise
            _community_comment_visibility_column_available = False
            response = fetch_rows(False)
    else:
        response = fetch_rows(False)

    rows_desc = list(response.data or [])
    has_more = len(rows_desc) > limit
    page_desc = rows_desc[:limit]
    next_cursor = None
    if has_more and page_desc:
        oldest_row = page_desc[-1]
        next_cursor = encode_page_cursor("community_comments", {
            **cursor_context,
            "created_at": str(oldest_row.get("created_at") or ""),
            "id": str(oldest_row.get("id") or ""),
        })
    return list(reversed(page_desc)), next_cursor, has_more


def _serialize_community_comment_page(
    supabase,
    *,
    rows: list[dict],
    user_id: str | None,
) -> list[CommunityCommentItem]:
    comment_ids = [str(row.get("id") or "") for row in rows if row.get("id")]
    author_ids = [str(row.get("author_id") or "") for row in rows if row.get("author_id")]
    with ThreadPoolExecutor(max_workers=2) as executor:
        profiles_future = executor.submit(_fetch_community_profiles, supabase, author_ids)
        liked_ids_future = executor.submit(_fetch_liked_comment_ids, supabase, user_id, comment_ids)
        profiles = profiles_future.result()
        liked_comment_ids = liked_ids_future.result()
    return [
        _comment_item(row, user_id, profiles, liked_comment_ids)
        for row in rows
    ]


def _get_post_row(supabase, post_id: str) -> dict:
    if post_id in COMMUNITY_RETIRED_SEED_POST_IDS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circle post not found")

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
    if (
        not response.data
        or _is_author_deleted_post(response.data[0])
        or _is_admin_deleted_post(response.data[0])
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circle post not found")
    return response.data[0]


def _get_comment_row(supabase, post_id: str, comment_id: str, *, visible_only: bool = True) -> dict:
    global _community_comment_visibility_column_available

    def fetch_comment(include_visibility: bool):
        query = (
            supabase.table("circle_community_comments")
            .select("*")
            .eq("id", comment_id)
            .eq("post_id", post_id)
            .limit(1)
        )
        if include_visibility:
            query = query.eq("is_published", True)
        return call_supabase(
            query.execute,
            operation_name="circle community comment lookup",
        )

    should_filter_visibility = visible_only and _community_comment_visibility_column_available is not False
    if should_filter_visibility:
        try:
            response = fetch_comment(True)
            _community_comment_visibility_column_available = True
        except Exception as exc:
            if not _is_missing_comment_visibility_column_error(exc):
                raise
            _community_comment_visibility_column_available = False
            response = fetch_comment(False)
    else:
        response = fetch_comment(False)
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circle comment not found")
    return response.data[0]


def _is_duplicate_community_interaction_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "duplicate key" in message or "unique constraint" in message or "23505" in message


def _get_community_like(supabase, post_id: str, user_id: str) -> bool:
    response = call_supabase(
        lambda: (
            supabase.table("circle_community_likes")
            .select("id")
            .eq("post_id", post_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        ),
        operation_name="circle community like lookup",
    )
    return bool(response.data)


def _adjust_community_post_stat(supabase, post_id: str, field: Literal["like_count", "view_count"], delta: int) -> int:
    """Apply a counter change with a short optimistic retry for concurrent readers."""

    for _ in range(COMMUNITY_STAT_UPDATE_ATTEMPTS):
        post = _get_post_row(supabase, post_id)
        current_value = max(0, int(post.get(field) or 0))
        next_value = max(0, current_value + delta)
        if next_value == current_value:
            return current_value

        response = call_supabase(
            lambda: (
                supabase.table("circle_community_posts")
                .update(
                    {
                        field: next_value,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                .eq("id", post_id)
                .eq(field, current_value)
                .execute()
            ),
            operation_name=f"circle community {field} update",
        )
        if response.data:
            return int(response.data[0].get(field) or next_value)

    raise RuntimeError(f"Circle community {field} update conflict")


def _toggle_community_like_without_rpc(supabase, post_id: str, user_id: str) -> tuple[bool, int]:
    """Toggle a like without relying on the legacy database RPC implementation."""

    _get_post_row(supabase, post_id)
    if _get_community_like(supabase, post_id, user_id):
        call_supabase(
            lambda: (
                supabase.table("circle_community_likes")
                .delete()
                .eq("post_id", post_id)
                .eq("user_id", user_id)
                .execute()
            ),
            operation_name="circle community unlike",
        )
        if _get_community_like(supabase, post_id, user_id):
            return True, int(_get_post_row(supabase, post_id).get("like_count") or 0)
        return False, _adjust_community_post_stat(supabase, post_id, "like_count", -1)

    try:
        call_supabase(
            lambda: (
                supabase.table("circle_community_likes")
                .insert({"post_id": post_id, "user_id": user_id})
                .execute()
            ),
            operation_name="circle community like create",
        )
    except Exception as exc:
        if not _is_duplicate_community_interaction_error(exc):
            raise
        return True, int(_get_post_row(supabase, post_id).get("like_count") or 0)

    return True, _adjust_community_post_stat(supabase, post_id, "like_count", 1)


def _set_community_like(
    supabase,
    *,
    post_id: str,
    user_id: str,
    desired_liked: bool,
) -> tuple[bool, int, bool]:
    """Set an explicit post-like target, using the atomic SQL path when deployed."""

    global _community_set_like_rpc_available
    if _community_set_like_rpc_available is not False and hasattr(supabase, "rpc"):
        try:
            response = call_supabase(
                lambda: supabase.rpc(
                    "circle_community_set_like",
                    {
                        "p_post_id": post_id,
                        "p_user_id": user_id,
                        "p_is_liked": desired_liked,
                    },
                ).execute(),
                operation_name="circle community atomic like target",
            )
            row = (response.data or [None])[0]
            if not row:
                raise RuntimeError("Circle community like target returned no row")
            _community_set_like_rpc_available = True
            return (
                bool(row.get("is_liked")),
                max(0, int(row.get("like_count") or 0)),
                bool(row.get("changed")),
            )
        except Exception as exc:
            if not is_missing_supabase_relation_error(exc):
                raise
            _community_set_like_rpc_available = False
            logger.info("Atomic community like target RPC unavailable; using compatibility path")

    current_liked = _get_community_like(supabase, post_id, user_id)
    post = _get_post_row(supabase, post_id)
    if current_liked == desired_liked:
        return current_liked, max(0, int(post.get("like_count") or 0)), False
    is_liked, like_count = _toggle_community_like_without_rpc(supabase, post_id, user_id)
    return is_liked, like_count, is_liked != current_liked


def _get_community_comment_like(supabase, comment_id: str, user_id: str) -> bool:
    response = call_supabase(
        lambda: (
            supabase.table("circle_community_comment_likes")
            .select("id")
            .eq("comment_id", comment_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        ),
        operation_name="circle community comment like lookup",
    )
    return bool(response.data)


def _adjust_community_comment_like_count(
    supabase,
    post_id: str,
    comment_id: str,
    delta: int,
) -> int:
    """Apply a comment like counter change with a short optimistic retry."""

    for _ in range(COMMUNITY_STAT_UPDATE_ATTEMPTS):
        comment = _get_comment_row(supabase, post_id, comment_id)
        current_value = max(0, int(comment.get("like_count") or 0))
        next_value = max(0, current_value + delta)
        if next_value == current_value:
            return current_value

        response = call_supabase(
            lambda: (
                supabase.table("circle_community_comments")
                .update({"like_count": next_value})
                .eq("id", comment_id)
                .eq("like_count", current_value)
                .execute()
            ),
            operation_name="circle community comment like count update",
        )
        if response.data:
            return int(response.data[0].get("like_count") or next_value)

    raise RuntimeError("Circle community comment like count update conflict")


def _toggle_community_comment_like_without_rpc(
    supabase,
    post_id: str,
    comment_id: str,
    user_id: str,
) -> tuple[bool, int]:
    """Toggle one user's like on one comment without depending on database RPC."""

    _get_post_row(supabase, post_id)
    _get_comment_row(supabase, post_id, comment_id)
    if _get_community_comment_like(supabase, comment_id, user_id):
        call_supabase(
            lambda: (
                supabase.table("circle_community_comment_likes")
                .delete()
                .eq("comment_id", comment_id)
                .eq("user_id", user_id)
                .execute()
            ),
            operation_name="circle community comment unlike",
        )
        if _get_community_comment_like(supabase, comment_id, user_id):
            return True, int(_get_comment_row(supabase, post_id, comment_id).get("like_count") or 0)
        return False, _adjust_community_comment_like_count(supabase, post_id, comment_id, -1)

    try:
        call_supabase(
            lambda: (
                supabase.table("circle_community_comment_likes")
                .insert({"comment_id": comment_id, "user_id": user_id})
                .execute()
            ),
            operation_name="circle community comment like create",
        )
    except Exception as exc:
        if not _is_duplicate_community_interaction_error(exc):
            raise
        return True, int(_get_comment_row(supabase, post_id, comment_id).get("like_count") or 0)

    return True, _adjust_community_comment_like_count(supabase, post_id, comment_id, 1)


def _set_community_comment_like(
    supabase,
    *,
    post_id: str,
    comment_id: str,
    user_id: str,
    desired_liked: bool,
) -> tuple[bool, int, bool]:
    """Set an explicit comment-like target, using the atomic SQL path when deployed."""

    global _community_set_comment_like_rpc_available
    if _community_set_comment_like_rpc_available is not False and hasattr(supabase, "rpc"):
        try:
            response = call_supabase(
                lambda: supabase.rpc(
                    "circle_community_set_comment_like",
                    {
                        "p_post_id": post_id,
                        "p_comment_id": comment_id,
                        "p_user_id": user_id,
                        "p_is_liked": desired_liked,
                    },
                ).execute(),
                operation_name="circle community atomic comment like target",
            )
            row = (response.data or [None])[0]
            if not row:
                raise RuntimeError("Circle community comment like target returned no row")
            _community_set_comment_like_rpc_available = True
            return (
                bool(row.get("is_liked")),
                max(0, int(row.get("like_count") or 0)),
                bool(row.get("changed")),
            )
        except Exception as exc:
            if not is_missing_supabase_relation_error(exc):
                raise
            _community_set_comment_like_rpc_available = False
            logger.info("Atomic community comment-like target RPC unavailable; using compatibility path")

    current_liked = _get_community_comment_like(supabase, comment_id, user_id)
    comment = _get_comment_row(supabase, post_id, comment_id)
    if current_liked == desired_liked:
        return current_liked, max(0, int(comment.get("like_count") or 0)), False
    is_liked, like_count = _toggle_community_comment_like_without_rpc(
        supabase,
        post_id,
        comment_id,
        user_id,
    )
    return is_liked, like_count, is_liked != current_liked


def _find_community_view(supabase, post_id: str, user_id: str | None, anonymous_id: str | None) -> dict | None:
    query = (
        supabase.table("circle_community_views")
        .select("id,last_counted_at")
        .eq("post_id", post_id)
        .limit(1)
    )
    query = query.eq("user_id", user_id) if user_id else query.eq("anonymous_id", anonymous_id)
    response = call_supabase(query.execute, operation_name="circle community view lookup")
    return (response.data or [None])[0]


def _register_community_view_without_rpc(
    supabase,
    post_id: str,
    user_id: str | None,
    anonymous_id: str | None,
) -> tuple[bool, int]:
    """Count one view per viewer every 24 hours without the legacy database RPC."""

    _get_post_row(supabase, post_id)
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    cutoff_iso = (now - timedelta(hours=24)).isoformat()
    existing = _find_community_view(supabase, post_id, user_id, anonymous_id)

    if existing:
        update_query = (
            supabase.table("circle_community_views")
            .update({"last_counted_at": now_iso})
            .eq("id", existing["id"])
            .lte("last_counted_at", cutoff_iso)
        )
        updated = call_supabase(
            update_query.execute,
            operation_name="circle community view refresh",
        )
        if not updated.data:
            return False, int(_get_post_row(supabase, post_id).get("view_count") or 0)
        return True, _adjust_community_post_stat(supabase, post_id, "view_count", 1)

    view_data = {
        "post_id": post_id,
        "last_counted_at": now_iso,
        **({"user_id": user_id} if user_id else {"anonymous_id": anonymous_id}),
    }
    try:
        inserted = call_supabase(
            lambda: supabase.table("circle_community_views").insert(view_data).execute(),
            operation_name="circle community view create",
        )
    except Exception as exc:
        if not _is_duplicate_community_interaction_error(exc):
            raise
        return False, int(_get_post_row(supabase, post_id).get("view_count") or 0)

    try:
        return True, _adjust_community_post_stat(supabase, post_id, "view_count", 1)
    except Exception:
        inserted_id = (inserted.data or [{}])[0].get("id")
        if inserted_id:
            try:
                call_supabase(
                    lambda: supabase.table("circle_community_views").delete().eq("id", inserted_id).execute(),
                    operation_name="circle community view rollback",
                )
            except Exception:
                logger.exception("Circle community view rollback failed")
        raise


def _current_author(supabase, user_id: str) -> tuple[str, str, str | None]:
    response = call_supabase(
        lambda: (
            supabase.table("users")
            .select("nickname,email,avatar_url")
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
    avatar_url = str(profile.get("avatar_url") or "").strip() or None
    return name, _first_character(name), avatar_url


def _find_community_comment_by_request_id(
    supabase,
    *,
    author_id: str,
    client_request_id: str,
) -> dict | None:
    response = call_supabase(
        lambda: (
            supabase.table("circle_community_comments")
            .select("*")
            .eq("author_id", author_id)
            .eq("client_request_id", client_request_id)
            .limit(1)
            .execute()
        ),
        operation_name="circle community comment idempotency lookup",
    )
    return (response.data or [None])[0]


def _create_community_comment_record(
    supabase,
    *,
    post_id: str,
    user_id: str,
    payload: CommunityCreateCommentRequest,
) -> tuple[dict, int, bool, dict, str | None, str]:
    """Create or recover one comment and return everything needed for the response."""

    global _community_comment_client_request_id_column_available, _community_comment_create_rpc_available
    client_request_id = str(payload.client_request_id)
    content = payload.content.strip()

    if _community_comment_create_rpc_available is not False and hasattr(supabase, "rpc"):
        try:
            response = call_supabase(
                lambda: supabase.rpc(
                    "circle_community_create_comment",
                    {
                        "p_post_id": post_id,
                        "p_user_id": user_id,
                        "p_content": content,
                        "p_client_request_id": client_request_id,
                    },
                ).execute(),
                operation_name="circle community atomic comment create",
            )
            row = (response.data or [None])[0]
            if not row:
                raise RuntimeError("Circle community comment create RPC returned no row")
            _community_comment_create_rpc_available = True
            _community_comment_client_request_id_column_available = True
            comment = {
                "id": row.get("comment_id"),
                "post_id": row.get("post_id") or post_id,
                "author_id": row.get("author_id") or user_id,
                "author_name": row.get("author_name") or "研友",
                "author_avatar": row.get("author_avatar") or "研",
                "content": row.get("content") or content,
                "created_at": row.get("created_at"),
                "like_count": row.get("like_count") or 0,
            }
            post = {
                "id": row.get("post_id") or post_id,
                "author_id": row.get("post_author_id"),
                "title": row.get("post_title") or "",
                "post_type": row.get("post_type") or "chat",
                "is_published": True,
            }
            return (
                comment,
                max(0, int(row.get("comment_count") or 0)),
                bool(row.get("created")),
                post,
                str(row.get("author_avatar_url") or "").strip() or None,
                str(row.get("author_name") or "研友"),
            )
        except Exception as exc:
            if not _is_community_comment_rpc_compatibility_error(exc):
                raise
            _community_comment_create_rpc_available = False
            logger.warning(
                "Atomic community comment RPC unavailable or incompatible; using compatibility path "
                "(error_type=%s)",
                type(exc).__name__,
            )

    post = _get_post_row(supabase, post_id)
    author_name, author_avatar, author_avatar_url = _current_author(supabase, user_id)
    existing = None
    if _community_comment_client_request_id_column_available is not False:
        try:
            existing = _find_community_comment_by_request_id(
                supabase,
                author_id=user_id,
                client_request_id=client_request_id,
            )
            _community_comment_client_request_id_column_available = True
        except Exception as exc:
            if not _is_missing_community_post_column_error(exc, "client_request_id"):
                raise
            _community_comment_client_request_id_column_available = False

    created = False
    comment = existing
    if comment is None:
        insert_data = {
            "post_id": post_id,
            "author_id": user_id,
            "author_name": author_name,
            "author_avatar": author_avatar,
            "content": content,
        }
        if _community_comment_client_request_id_column_available is not False:
            insert_data["client_request_id"] = client_request_id
        try:
            comment_response = call_supabase(
                lambda: supabase.table("circle_community_comments").insert(insert_data).execute(),
                operation_name="circle community comment create",
            )
            comment = (comment_response.data or [None])[0]
            created = comment is not None
        except Exception as exc:
            if (
                "client_request_id" in insert_data
                and _is_missing_community_post_column_error(exc, "client_request_id")
            ):
                _community_comment_client_request_id_column_available = False
                insert_data.pop("client_request_id", None)
                comment_response = call_supabase(
                    lambda: supabase.table("circle_community_comments").insert(insert_data).execute(),
                    operation_name="circle community legacy comment create",
                )
                comment = (comment_response.data or [None])[0]
                created = comment is not None
            elif _is_duplicate_community_interaction_error(exc):
                comment = _find_community_comment_by_request_id(
                    supabase,
                    author_id=user_id,
                    client_request_id=client_request_id,
                )
            else:
                raise
    if not comment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Circle comment create failed")

    updated_post = _get_post_row(supabase, post_id)
    return (
        comment,
        max(0, int(updated_post.get("comment_count") or 0)),
        created,
        post,
        author_avatar_url,
        author_name,
    )


def _notify_community_post_interaction(
    supabase,
    *,
    post: dict,
    actor_user_id: str,
    interaction: str,
    related_id: str,
    comment_content: str = "",
    actor_name: str = "",
) -> None:
    """Write a recipient-scoped notice when someone interacts with another user's post."""

    recipient_user_id = str(post.get("author_id") or "").strip()
    post_id = str(post.get("id") or "").strip()
    if not recipient_user_id or not post_id or recipient_user_id == str(actor_user_id or ""):
        return

    normalized_actor_name = str(actor_name or "").strip()
    if not normalized_actor_name:
        normalized_actor_name, _, _ = _current_author(supabase, actor_user_id)
    post_title = str(post.get("title") or "").strip() or "你的研圈帖子"
    route_path = (
        "/pages/home/index?tab=circle&section=community"
        f"&communityTab={_community_post_type(post)}&postId={post_id}"
    )
    if interaction == "comment":
        title = "你的帖子收到了新评论"
        summary = f"{normalized_actor_name[:30]} 评论了“{post_title[:48]}”"
        content = comment_content.strip()[:180] or "对方在你的帖子下留下了一条评论。"
        notification_type = "community_post_comment"
    else:
        title = "你的帖子收到了新的赞"
        summary = f"{normalized_actor_name[:30]} 赞了“{post_title[:48]}”"
        content = "点击查看帖子详情和最新互动。"
        notification_type = "community_post_like"

    create_user_notification(
        supabase,
        recipient_user_id=recipient_user_id,
        category="community",
        notification_type=notification_type,
        title=title,
        summary=summary,
        content=content,
        related_type="community_post",
        related_id=related_id or post_id,
        route_path=route_path,
        delivery_payload={
            "surface": "community_post",
            "interaction": interaction,
            "post_id": post_id,
            "post_type": _community_post_type(post),
            "actor_user_id": str(actor_user_id or ""),
        },
    )


def _notify_community_post_interaction_background(
    *,
    post: dict,
    actor_user_id: str,
    interaction: str,
    related_id: str,
    comment_content: str = "",
    actor_name: str = "",
) -> None:
    """Finish non-critical interaction notification work after the API response."""

    try:
        _notify_community_post_interaction(
            get_supabase_admin(),
            post=post,
            actor_user_id=actor_user_id,
            interaction=interaction,
            related_id=related_id,
            comment_content=comment_content,
            actor_name=actor_name,
        )
    except Exception as exc:
        logger.warning(
            "Community interaction notification deferred (interaction=%s error_type=%s)",
            interaction,
            type(exc).__name__,
        )


def _current_verified_mentor_author(supabase, user_id: str) -> dict:
    """Verify experience-post eligibility without replacing the account's public identity."""

    response = call_supabase(
        lambda: (
            supabase.table("mentor_profiles")
            .select("id,display_name,avatar_label,avatar_tone,avatar_url")
            .eq("owner_user_id", user_id)
            .eq("verification_status", "verified")
            .eq("is_published", True)
            .limit(1)
            .execute()
        ),
        operation_name="circle experience author verification",
    )
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="经验贴仅限已完成认证并公开展示的前辈发布",
        )
    return response.data[0]


def _get_owned_post_row(supabase, post_id: str, user_id: str) -> dict:
    response = call_supabase(
        lambda: (
            supabase.table("circle_community_posts")
            .select("*")
            .eq("id", post_id)
            .eq("author_id", user_id)
            .limit(1)
            .execute()
        ),
        operation_name="circle community own post lookup",
    )
    row = (response.data or [None])[0]
    if not row or _is_author_deleted_post(row) or _is_admin_deleted_post(row):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在")
    return row


def _ensure_owned_post_editable(supabase, post_id: str) -> None:
    """Preserve moderation evidence once a post has entered platform handling."""

    report_response = call_supabase(
        lambda: (
            supabase.table("circle_community_reports")
            .select("id")
            .eq("post_id", post_id)
            .limit(1)
            .execute()
        ),
        operation_name="circle community own post edit report protection lookup",
    )
    appeal_response = call_supabase(
        lambda: (
            supabase.table("circle_community_appeals")
            .select("id")
            .eq("post_id", post_id)
            .limit(1)
            .execute()
        ),
        operation_name="circle community own post edit appeal protection lookup",
    )
    if report_response.data or appeal_response.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该帖子已进入平台处理流程，为保留处理记录暂不能编辑",
        )


def _fetch_experience_review_history(
    supabase,
    post_id: str,
) -> list[CommunityExperienceReviewHistoryItem]:
    response = call_supabase(
        lambda: (
            supabase.table("circle_community_post_review_history")
            .select(
                "id,submission_version,action,from_status,to_status,reason_code,"
                "review_note,created_at"
            )
            .eq("post_id", post_id)
            .order("created_at", desc=True)
            .limit(100)
            .execute()
        ),
        operation_name="circle community experience review history",
    )
    return [
        CommunityExperienceReviewHistoryItem(**row)
        for row in (response.data or [])
    ]


def _serialize_community_report(row: dict, posts: dict[str, dict], comments: dict[str, dict]) -> dict:
    target_type = str(row.get("target_type") or "post")
    post = posts.get(str(row.get("post_id") or ""), {})
    comment = comments.get(str(row.get("comment_id") or ""), {})
    if target_type == "comment":
        target_title = str(post.get("title") or "帖子评论")
        target_excerpt = str(comment.get("content") or "")[:160]
    else:
        target_title = str(post.get("title") or "研圈帖子")
        target_excerpt = str(post.get("content") or "")[:160]
    return {
        "id": str(row.get("id") or ""),
        "target_type": target_type,
        "post_id": str(row.get("post_id") or ""),
        "comment_id": str(row.get("comment_id") or "") or None,
        "reason": str(row.get("reason") or "其他问题"),
        "content": str(row.get("content") or ""),
        "status": str(row.get("status") or "pending"),
        "moderation_action": str(row.get("moderation_action") or "none"),
        "admin_note": row.get("admin_note") or None,
        "target_title": target_title,
        "target_excerpt": target_excerpt,
        "created_at": row.get("created_at") or None,
        "handled_at": row.get("handled_at") or None,
    }


def _fetch_community_report_targets(supabase, rows: list[dict]) -> tuple[dict[str, dict], dict[str, dict]]:
    post_ids = list(dict.fromkeys(str(row.get("post_id") or "") for row in rows if row.get("post_id")))
    comment_ids = list(dict.fromkeys(str(row.get("comment_id") or "") for row in rows if row.get("comment_id")))
    posts: dict[str, dict] = {}
    comments: dict[str, dict] = {}
    if post_ids:
        post_response = call_supabase(
            lambda: (
                supabase.table("circle_community_posts")
                .select("id,title,content")
                .in_("id", post_ids)
                .execute()
            ),
            operation_name="circle community report post target lookup",
        )
        posts = {
            str(row.get("id") or ""): row
            for row in (post_response.data or [])
            if row.get("id")
        }
    if comment_ids:
        comment_response = call_supabase(
            lambda: (
                supabase.table("circle_community_comments")
                .select("id,content")
                .in_("id", comment_ids)
                .execute()
            ),
            operation_name="circle community report comment target lookup",
        )
        comments = {
            str(row.get("id") or ""): row
            for row in (comment_response.data or [])
            if row.get("id")
        }
    return posts, comments


def _create_community_report(
    supabase,
    *,
    post_id: str,
    comment_id: str | None,
    payload: CommunityCreateReportRequest,
    user_id: str,
) -> CommunityReportItem:
    post = _get_post_row(supabase, post_id)
    target_type = "comment" if comment_id else "post"
    target = _get_comment_row(supabase, post_id, comment_id) if comment_id else post
    if str(target.get("author_id") or "") == user_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不能举报自己发布的内容")

    reason = str(payload.reason or "").strip()
    content = str(payload.content or "").strip()
    allowed_reasons = COMMUNITY_COMMENT_REPORT_REASONS if comment_id else COMMUNITY_POST_REPORT_REASONS
    if reason not in allowed_reasons:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="请选择有效的举报原因")
    if len(content) < 10:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="请至少填写 10 个字的举报说明")

    duplicate_query = (
        supabase.table("circle_community_reports")
        .select("id")
        .eq("reporter_user_id", user_id)
        .eq("target_type", target_type)
        .eq("post_id", post_id)
        .limit(1)
    )
    if comment_id:
        duplicate_query = duplicate_query.eq("comment_id", comment_id)
    else:
        duplicate_query = duplicate_query.is_("comment_id", "null")
    duplicate_response = call_supabase(
        duplicate_query.execute,
        operation_name="circle community report duplicate lookup",
    )
    if duplicate_response.data:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="你已举报过该内容，可在我的举报中查看处理进度")

    response = call_supabase(
        lambda: supabase.table("circle_community_reports").insert({
            "reporter_user_id": user_id,
            "target_type": target_type,
            "post_id": post_id,
            "comment_id": comment_id,
            "target_user_id": str(target.get("author_id") or "") or None,
            "reason": reason,
            "content": content,
        }).execute(),
        operation_name="circle community report create",
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="举报提交失败")
    report = response.data[0]
    return CommunityReportItem(**_serialize_community_report(
        report,
        {post_id: post},
        {str(comment_id): target} if comment_id else {},
    ))


def _serialize_community_appeal(row: dict) -> CommunityModerationAppealItem:
    return CommunityModerationAppealItem(
        id=str(row.get("id") or ""),
        target_type=str(row.get("target_type") or "post"),
        post_id=str(row.get("post_id") or ""),
        comment_id=str(row.get("comment_id") or "") or None,
        content=str(row.get("content") or ""),
        status=str(row.get("status") or "pending"),
        moderation_action=str(row.get("moderation_action") or "none"),
        admin_note=row.get("admin_note") or None,
        created_at=row.get("created_at") or None,
        handled_at=row.get("handled_at") or None,
    )


def _get_owned_moderation_target_or_404(
    supabase,
    *,
    target_type: str,
    target_id: str,
    user_id: str,
) -> tuple[dict, str, str | None]:
    if target_type == "post":
        response = call_supabase(
            lambda: (
                supabase.table("circle_community_posts")
                .select("*")
                .eq("id", target_id)
                .eq("author_id", user_id)
                .limit(1)
                .execute()
            ),
            operation_name="circle community owned post moderation lookup",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到可申诉的帖子")
        return response.data[0], str(target_id), None

    if target_type == "comment":
        response = call_supabase(
            lambda: (
                supabase.table("circle_community_comments")
                .select("*")
                .eq("id", target_id)
                .eq("author_id", user_id)
                .limit(1)
                .execute()
            ),
            operation_name="circle community owned comment moderation lookup",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到可申诉的评论")
        target = response.data[0]
        return target, str(target.get("post_id") or ""), str(target_id)

    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的内容类型")


def _fetch_my_community_content_status(
    supabase,
    user_id: str,
    *,
    limit: int,
) -> list[CommunityModerationStatusItem]:
    post_response = call_supabase(
        lambda: (
            supabase.table("circle_community_posts")
            .select("id,title,content,is_published,moderation_note,moderated_at,created_at")
            .eq("author_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        ),
        operation_name="circle community own moderation post list",
    )
    comment_response = call_supabase(
        lambda: (
            supabase.table("circle_community_comments")
            .select("id,post_id,content,is_published,moderation_note,moderated_at,created_at")
            .eq("author_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        ),
        operation_name="circle community own moderation comment list",
    )
    appeal_response = call_supabase(
        lambda: (
            supabase.table("circle_community_appeals")
            .select(COMMUNITY_APPEAL_FIELDS)
            .eq("appellant_user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit * 2)
            .execute()
        ),
        operation_name="circle community own appeal list",
    )

    appeals_by_target: dict[str, dict] = {}
    for appeal in appeal_response.data or []:
        target_type = str(appeal.get("target_type") or "post")
        target_id = str(appeal.get("comment_id") or "") if target_type == "comment" else str(appeal.get("post_id") or "")
        if target_id and f"{target_type}:{target_id}" not in appeals_by_target:
            appeals_by_target[f"{target_type}:{target_id}"] = appeal

    posts = {
        str(row.get("id") or ""): row
        for row in (post_response.data or [])
        if row.get("id")
    }
    comment_rows = comment_response.data or []
    # 评论作者并不一定是帖子作者；补齐父帖标题，才能让用户在处理记录里
    # 准确辨认被下架或申诉的那条评论属于哪篇帖子。
    parent_post_ids = list(dict.fromkeys(
        str(row.get("post_id") or "")
        for row in comment_rows
        if row.get("post_id") and str(row.get("post_id") or "") not in posts
    ))
    if parent_post_ids:
        parent_response = call_supabase(
            lambda: (
                supabase.table("circle_community_posts")
                .select("id,title")
                .in_("id", parent_post_ids)
                .execute()
            ),
            operation_name="circle community moderation parent post lookup",
        )
        posts.update({
            str(row.get("id") or ""): row
            for row in (parent_response.data or [])
            if row.get("id")
        })
    items: list[CommunityModerationStatusItem] = []
    for post_id, post in posts.items():
        appeal = appeals_by_target.get(f"post:{post_id}")
        if bool(post.get("is_published", True)) and not post.get("moderation_note") and not appeal:
            continue
        items.append(CommunityModerationStatusItem(
            target_type="post",
            target_id=post_id,
            post_id=post_id,
            title=str(post.get("title") or "研圈帖子"),
            excerpt=str(post.get("content") or "")[:240],
            is_published=bool(post.get("is_published")),
            moderation_note=post.get("moderation_note") or None,
            moderated_at=post.get("moderated_at") or None,
            appeal=_serialize_community_appeal(appeal) if appeal else None,
        ))

    for comment in comment_rows:
        comment_id = str(comment.get("id") or "")
        post_id = str(comment.get("post_id") or "")
        if not comment_id or not post_id:
            continue
        appeal = appeals_by_target.get(f"comment:{comment_id}")
        if bool(comment.get("is_published", True)) and not comment.get("moderation_note") and not appeal:
            continue
        post = posts.get(post_id, {})
        items.append(CommunityModerationStatusItem(
            target_type="comment",
            target_id=comment_id,
            post_id=post_id,
            comment_id=comment_id,
            title=str(post.get("title") or "研圈评论"),
            excerpt=str(comment.get("content") or "")[:240],
            is_published=bool(comment.get("is_published")),
            moderation_note=comment.get("moderation_note") or None,
            moderated_at=comment.get("moderated_at") or None,
            appeal=_serialize_community_appeal(appeal) if appeal else None,
        ))

    return sorted(
        items,
        key=lambda item: str(item.appeal.created_at if item.appeal else item.moderated_at or ""),
        reverse=True,
    )[:limit]


def _raise_community_service_error(exc: Exception) -> None:
    logger.warning("Circle community service error (error_type=%s)", type(exc).__name__)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="考研圈服务暂时不可用，请稍后重试",
    ) from exc


def _community_provider_error_metadata(exc: Exception) -> tuple[str | None, int | None]:
    provider_status: int | None = None
    for source in (exc, getattr(exc, "response", None)):
        if source is None:
            continue
        for attribute in ("status_code", "status"):
            try:
                candidate_status = int(getattr(source, attribute, None))
            except (TypeError, ValueError):
                continue
            if 100 <= candidate_status <= 599:
                provider_status = candidate_status
                break
        if provider_status is not None:
            break

    raw_code = getattr(exc, "code", None)
    if raw_code is None:
        raw_code = getattr(getattr(exc, "response", None), "code", None)
    provider_code = str(raw_code or "").strip()
    if not (
        1 <= len(provider_code) <= 32
        and all(character.isascii() and (character.isalnum() or character in "-_.") for character in provider_code)
    ):
        provider_code = ""
    if provider_status is None and provider_code.isdigit():
        numeric_code = int(provider_code)
        if 100 <= numeric_code <= 599:
            provider_status = numeric_code
    return provider_code or None, provider_status


def _raise_community_post_create_error(
    exc: Exception,
    *,
    payload: CommunityCreatePostRequest,
    stage: str,
) -> None:
    provider_code, provider_status = _community_provider_error_metadata(exc)
    logger.warning(
        "Circle community post create failed "
        "(stage=%s request_id=%s post_type=%s category=%s content_length=%s "
        "media_count=%s provider_code=%s provider_status=%s)",
        stage,
        str(payload.client_request_id),
        payload.post_type,
        payload.category,
        len(payload.content),
        len(payload.media),
        provider_code or "-",
        provider_status if provider_status is not None else "-",
    )
    detail = (
        "考研圈上游服务暂时不可用，请稍后重试"
        if is_transient_supabase_error(exc)
        else "帖子保存失败，请稍后重试"
    )
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=detail,
    ) from exc


@router.get("/posts", response_model=CommunityPostListResponse)
def list_community_posts(
    post_type: Literal["chat", "experience"] = Query(default="chat"),
    category: str | None = Query(default=None, max_length=24),
    experience_stage: Literal["申请制", "初试", "复试"] | None = Query(default=None),
    featured_only: bool = Query(default=False),
    sort_by: Literal["latest", "hot"] = Query(default="latest"),
    search: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=12, ge=1, le=30),
    cursor: str | None = Query(default=None, max_length=2048),
    user_id: str | None = Depends(get_optional_current_user_id),
) -> CommunityPostListResponse:
    global _community_feed_view_available, _community_post_type_column_available

    normalized_category, normalized_experience_stage = _normalize_community_experience_filters(
        post_type,
        category,
        experience_stage,
    )
    normalized_search = str(search or "").strip().replace("%", "").replace("_", "")
    cursor_context = {
        "post_type": post_type,
        "category": normalized_category,
        "experience_stage": normalized_experience_stage,
        "featured_only": featured_only,
        "sort_by": sort_by,
        "search": normalized_search,
    }
    initial_cursor = decode_page_cursor(
        cursor,
        kind="community_posts",
        context=cursor_context,
    )

    supabase = get_supabase_admin()
    try:
        def cursor_fields(payload: dict) -> list[tuple[str, Literal["asc", "desc"], str | int]]:
            fields: list[tuple[str, Literal["asc", "desc"], str | int]] = []
            if sort_by == "hot":
                fields.extend([
                    ("like_count", "desc", cursor_integer(payload, "like_count")),
                    ("comment_count", "desc", cursor_integer(payload, "comment_count")),
                    ("view_count", "desc", cursor_integer(payload, "view_count")),
                ])
            fields.extend([
                ("created_at", "desc", cursor_datetime(payload, "created_at")),
                ("id", "desc", cursor_uuid(payload, "id")),
            ])
            return fields

        def row_cursor_payload(row: dict) -> dict:
            payload = {
                **cursor_context,
                "created_at": str(row.get("created_at") or ""),
                "id": str(row.get("id") or ""),
            }
            if sort_by == "hot":
                payload.update({
                    "like_count": int(row.get("like_count") or 0),
                    "comment_count": int(row.get("comment_count") or 0),
                    "view_count": int(row.get("view_count") or 0),
                })
            return payload

        def build_post_list_query(
            include_post_type: bool,
            page_cursor: dict | None,
            query_limit: int,
            *,
            source_name: str,
            select_fields: str,
            search_in_database: bool,
        ):
            query = (
                supabase.table(source_name)
                .select(select_fields)
                .eq("is_published", True)
            )
            if include_post_type:
                query = query.eq("post_type", post_type)
            if featured_only:
                query = query.eq("is_featured", True)
            if normalized_category:
                query = query.eq("category", normalized_category)
            if normalized_search and search_in_database:
                query = query.ilike("search_text", f"%{normalized_search}%")
            if page_cursor:
                query = query.or_(build_keyset_filter(cursor_fields(page_cursor)))
            if sort_by == "hot":
                return (
                    query.order("like_count", desc=True)
                    .order("comment_count", desc=True)
                    .order("view_count", desc=True)
                    .order("created_at", desc=True)
                    .order("id", desc=True)
                    .limit(query_limit)
                )
            return (
                query.order("created_at", desc=True)
                .order("id", desc=True)
                .limit(query_limit)
            )

        # Some legacy rows are intentionally hidden, and experience posts also
        # require a verified author. Scan stable database pages until one visible
        # API page (plus one look-ahead item) has been assembled.
        query_limit = max(32, limit + 1 + len(COMMUNITY_RETIRED_SEED_POST_IDS))
        scan_cursor = initial_cursor
        visible_rows: list[dict] = []
        exhausted = False
        while len(visible_rows) <= limit and not exhausted:
            include_post_type = _community_post_type_column_available is not False
            use_feed_view = _community_feed_view_available is not False
            try:
                response = call_supabase(
                    lambda: build_post_list_query(
                        include_post_type,
                        scan_cursor,
                        query_limit,
                        source_name=COMMUNITY_FEED_VIEW if use_feed_view else "circle_community_posts",
                        select_fields=COMMUNITY_FEED_VIEW_FIELDS if use_feed_view else COMMUNITY_FEED_TABLE_FIELDS,
                        search_in_database=use_feed_view,
                    ).execute(),
                    operation_name="circle community post list",
                )
                if use_feed_view:
                    _community_feed_view_available = True
                if include_post_type:
                    _community_post_type_column_available = True
            except Exception as exc:
                if use_feed_view and is_missing_supabase_relation_error(exc):
                    _community_feed_view_available = False
                    logger.info("Compact community feed view unavailable; using compatibility table query")
                    continue
                if not include_post_type or not _is_missing_post_type_column_error(exc):
                    raise
                _community_post_type_column_available = False
                response = call_supabase(
                    lambda: build_post_list_query(
                        False,
                        scan_cursor,
                        query_limit,
                        source_name="circle_community_posts",
                        select_fields=COMMUNITY_FEED_TABLE_FIELDS,
                        search_in_database=False,
                    ).execute(),
                    operation_name="circle community post list legacy",
                )

            raw_rows = list(response.data or [])
            if not raw_rows:
                exhausted = True
                break
            exhausted = len(raw_rows) < query_limit
            scan_cursor = row_cursor_payload(raw_rows[-1])
            candidate_rows = [
                row
                for row in raw_rows
                if (_community_post_type_column_available is not False or _community_post_type(row) == post_type)
                and str(row.get("id") or "") not in COMMUNITY_RETIRED_SEED_POST_IDS
                and not _is_author_deleted_post(row)
                and not _is_admin_deleted_post(row)
                and (_community_feed_view_available is True or _matches_community_search(row, normalized_search))
            ]
            if post_type == "experience" and candidate_rows:
                verified_ids = _fetch_verified_mentor_owner_ids(
                    supabase,
                    [str(row.get("author_id") or "") for row in candidate_rows],
                )
                candidate_rows = [
                    row for row in candidate_rows
                    if _is_public_verified_experience_post(row, verified_ids)
                ]
                if normalized_experience_stage:
                    candidate_rows = [
                        row for row in candidate_rows
                        if _matches_community_experience_stage(row, normalized_experience_stage)
                    ]
            visible_rows.extend(candidate_rows)

        has_more = len(visible_rows) > limit
        rows = visible_rows[:limit]
        post_ids = [str(row.get("id")) for row in rows if row.get("id")]
        with ThreadPoolExecutor(max_workers=4) as executor:
            profiles_future = executor.submit(
                _fetch_community_profiles,
                supabase,
                [str(row.get("author_id") or "") for row in rows],
            )
            verified_authors_future = executor.submit(
                _fetch_verified_mentor_owner_ids,
                supabase,
                [str(row.get("author_id") or "") for row in rows],
            )
            liked_post_ids_future = executor.submit(_fetch_liked_post_ids, supabase, user_id, post_ids)
            previews_future = executor.submit(_fetch_comment_previews, supabase, post_ids)
            profiles = profiles_future.result()
            verified_author_ids = verified_authors_future.result()
            liked_post_ids = liked_post_ids_future.result()
            previews = previews_future.result()
        next_cursor = None
        if has_more and rows:
            next_cursor = encode_page_cursor("community_posts", row_cursor_payload(rows[-1]))
        return CommunityPostListResponse(
            items=[
                _post_item(
                    row,
                    liked_post_ids,
                    previews,
                    profiles,
                    verified_author_ids,
                    compact=True,
                    current_user_id=user_id,
                )
                for row in rows
            ],
            count=len(rows),
            next_cursor=next_cursor,
            has_more=has_more,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_service_error(exc)


@router.get("/liked-posts", response_model=CommunityLikedPostListResponse)
def list_liked_community_posts(
    limit: int = Query(default=30, ge=1, le=50),
    cursor: str | None = Query(default=None, max_length=2048),
    user_id: str = Depends(get_current_user_id),
) -> CommunityLikedPostListResponse:
    """Return the current user's visible likes, newest like first."""

    supabase = get_supabase_admin()
    try:
        cursor_payload = decode_page_cursor(cursor, kind="community_liked_posts")
        likes_query = (
            supabase.table("circle_community_likes")
            .select("post_id,created_at")
            .eq("user_id", user_id)
        )
        if cursor_payload:
            likes_query = likes_query.or_(build_keyset_filter([
                ("created_at", "desc", cursor_datetime(cursor_payload, "created_at")),
                ("post_id", "desc", cursor_uuid(cursor_payload, "post_id")),
            ]))
        likes_response = call_supabase(
            lambda: (
                likes_query
                .order("created_at", desc=True)
                .order("post_id", desc=True)
                .limit(limit + 1)
                .execute()
            ),
            operation_name="circle community liked post list",
        )
        like_rows = list(likes_response.data or [])
        has_more = len(like_rows) > limit
        page_like_rows = like_rows[:limit]
        liked_at_by_post_id = {
            str(row.get("post_id")): row.get("created_at")
            for row in page_like_rows
            if row.get("post_id")
        }
        ordered_post_ids = list(liked_at_by_post_id)
        if not ordered_post_ids:
            return CommunityLikedPostListResponse(has_more=has_more)

        posts_response = call_supabase(
            lambda: (
                supabase.table("circle_community_posts")
                .select("*")
                .in_("id", ordered_post_ids)
                .eq("is_published", True)
                .execute()
            ),
            operation_name="circle community liked post lookup",
        )
        rows_by_id = {
            str(row.get("id")): row
            for row in (posts_response.data or [])
            if row.get("id")
        }
        rows = [
            rows_by_id[post_id]
            for post_id in ordered_post_ids
            if post_id in rows_by_id
            and post_id not in COMMUNITY_RETIRED_SEED_POST_IDS
            and not _is_author_deleted_post(rows_by_id[post_id])
            and not _is_admin_deleted_post(rows_by_id[post_id])
        ]
        post_ids = [str(row.get("id")) for row in rows]

        with ThreadPoolExecutor(max_workers=3) as executor:
            profiles_future = executor.submit(
                _fetch_community_profiles,
                supabase,
                [str(row.get("author_id") or "") for row in rows],
            )
            verified_authors_future = executor.submit(
                _fetch_verified_mentor_owner_ids,
                supabase,
                [str(row.get("author_id") or "") for row in rows],
            )
            previews_future = executor.submit(_fetch_comment_previews, supabase, post_ids)
            profiles = profiles_future.result()
            verified_author_ids = verified_authors_future.result()
            previews = previews_future.result()

        rows = [
            row
            for row in rows
            if _community_post_type(row) != "experience"
            or _is_public_verified_experience_post(row, verified_author_ids)
        ]

        next_cursor = None
        if has_more and page_like_rows:
            anchor = page_like_rows[-1]
            next_cursor = encode_page_cursor("community_liked_posts", {
                "created_at": str(anchor.get("created_at") or ""),
                "post_id": str(anchor.get("post_id") or ""),
            })
        return CommunityLikedPostListResponse(
            items=[
                CommunityLikedPostItem(
                    **_post_item(
                        row,
                        set(post_ids),
                        previews,
                        profiles,
                        verified_author_ids,
                        current_user_id=user_id,
                    ).model_dump(),
                    liked_at=liked_at_by_post_id.get(str(row.get("id"))),
                )
                for row in rows
            ],
            count=len(rows),
            next_cursor=next_cursor,
            has_more=has_more,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_service_error(exc)


@router.get("/my-posts", response_model=CommunityPostListResponse)
def list_my_community_posts(
    post_type: Literal["all", "chat", "experience"] = Query(default="all"),
    sort_by: Literal["latest", "hot"] = Query(default="latest"),
    limit: int = Query(default=30, ge=1, le=50),
    cursor: str | None = Query(default=None, max_length=2048),
    user_id: str = Depends(get_current_user_id),
) -> CommunityPostListResponse:
    """Return all posts owned by the current user, including review states."""

    global _community_admin_deleted_column_available
    global _community_author_deleted_column_available, _community_post_type_column_available

    supabase = get_supabase_admin()
    try:
        cursor_context = {"post_type": post_type, "sort_by": sort_by}
        cursor_payload = decode_page_cursor(cursor, kind="community_my_posts", context=cursor_context)
        query_limit = max(limit + 1 + len(COMMUNITY_RETIRED_SEED_POST_IDS), 32)

        def build_my_post_query(
            include_post_type: bool,
            include_author_deleted: bool,
            include_admin_deleted: bool,
        ):
            query = (
                supabase.table("circle_community_posts")
                .select("*")
                .eq("author_id", user_id)
            )
            if include_author_deleted:
                query = query.is_("author_deleted_at", "null")
            if include_admin_deleted:
                query = query.is_("admin_deleted_at", "null")
            if include_post_type and post_type != "all":
                query = query.eq("post_type", post_type)
            if cursor_payload:
                keyset_fields = []
                if sort_by == "hot":
                    keyset_fields.extend([
                        ("like_count", "desc", cursor_integer(cursor_payload, "like_count")),
                        ("comment_count", "desc", cursor_integer(cursor_payload, "comment_count")),
                        ("view_count", "desc", cursor_integer(cursor_payload, "view_count")),
                    ])
                keyset_fields.extend([
                    ("created_at", "desc", cursor_datetime(cursor_payload, "created_at")),
                    ("id", "desc", cursor_uuid(cursor_payload, "id")),
                ])
                query = query.or_(build_keyset_filter(keyset_fields))
            if sort_by == "hot":
                return (
                    query.order("like_count", desc=True)
                    .order("comment_count", desc=True)
                    .order("view_count", desc=True)
                    .order("created_at", desc=True)
                    .order("id", desc=True)
                    .limit(query_limit)
                )
            return query.order("created_at", desc=True).order("id", desc=True).limit(query_limit)

        include_post_type = _community_post_type_column_available is not False
        include_author_deleted = _community_author_deleted_column_available is not False
        include_admin_deleted = _community_admin_deleted_column_available is not False
        while True:
            try:
                response = call_supabase(
                    lambda: build_my_post_query(
                        include_post_type,
                        include_author_deleted,
                        include_admin_deleted,
                    ).execute(),
                    operation_name="circle community own post list",
                )
                if include_post_type:
                    _community_post_type_column_available = True
                if include_author_deleted:
                    _community_author_deleted_column_available = True
                if include_admin_deleted:
                    _community_admin_deleted_column_available = True
                rows = response.data or []
                break
            except Exception as exc:
                if include_admin_deleted and _is_missing_community_post_column_error(exc, "admin_deleted_at"):
                    _community_admin_deleted_column_available = False
                    include_admin_deleted = False
                    continue
                if include_author_deleted and _is_missing_community_post_column_error(exc, "author_deleted_at"):
                    _community_author_deleted_column_available = False
                    include_author_deleted = False
                    continue
                if include_post_type and _is_missing_post_type_column_error(exc):
                    _community_post_type_column_available = False
                    include_post_type = False
                    continue
                raise

        candidate_rows = [
            row
            for row in rows
            if str(row.get("id") or "") not in COMMUNITY_RETIRED_SEED_POST_IDS
            and not _is_author_deleted_post(row)
            and not _is_admin_deleted_post(row)
            and (post_type == "all" or _community_post_type(row) == post_type)
        ]
        has_more = len(candidate_rows) > limit
        rows = candidate_rows[:limit]
        post_ids = [str(row.get("id")) for row in rows if row.get("id")]

        with ThreadPoolExecutor(max_workers=3) as executor:
            profiles_future = executor.submit(_fetch_community_profiles, supabase, [user_id])
            verified_authors_future = executor.submit(_fetch_verified_mentor_owner_ids, supabase, [user_id])
            liked_post_ids_future = executor.submit(_fetch_liked_post_ids, supabase, user_id, post_ids)
            previews_future = executor.submit(_fetch_comment_previews, supabase, post_ids)
            profiles = profiles_future.result()
            verified_author_ids = verified_authors_future.result()
            liked_post_ids = liked_post_ids_future.result()
            previews = previews_future.result()

        next_cursor = None
        if has_more and rows:
            anchor = rows[-1]
            cursor_data = {
                **cursor_context,
                "created_at": str(anchor.get("created_at") or ""),
                "id": str(anchor.get("id") or ""),
            }
            if sort_by == "hot":
                cursor_data.update({
                    "like_count": int(anchor.get("like_count") or 0),
                    "comment_count": int(anchor.get("comment_count") or 0),
                    "view_count": int(anchor.get("view_count") or 0),
                })
            next_cursor = encode_page_cursor("community_my_posts", cursor_data)
        return CommunityPostListResponse(
            items=[
                _post_item(
                    row,
                    liked_post_ids,
                    previews,
                    profiles,
                    verified_author_ids,
                    current_user_id=user_id,
                )
                for row in rows
            ],
            count=len(rows),
            next_cursor=next_cursor,
            has_more=has_more,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_service_error(exc)


@router.get("/my-posts/{post_id}", response_model=CommunityOwnPostDetailResponse)
def get_my_community_post(
    post_id: str,
    user_id: str = Depends(get_current_user_id),
) -> CommunityOwnPostDetailResponse:
    supabase = get_supabase_admin()
    try:
        row = _get_owned_post_row(supabase, post_id, user_id)
        profiles = _fetch_community_profiles(supabase, [user_id])
        verified_author_ids = _fetch_verified_mentor_owner_ids(supabase, [user_id])
        review_history = (
            _fetch_experience_review_history(supabase, post_id)
            if _community_post_type(row) == "experience"
            else []
        )
        return CommunityOwnPostDetailResponse(
            post=_post_item(
                row,
                set(),
                {},
                profiles,
                verified_author_ids,
                current_user_id=user_id,
            ),
            review_history=review_history,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_service_error(exc)


@router.patch("/my-posts/{post_id}", response_model=CommunityPostItem)
def update_my_community_post(
    post_id: str,
    payload: CommunityCreatePostRequest,
    user_id: str = Depends(get_current_user_id),
) -> CommunityPostItem:
    """Update an owned post; experience edits always return to platform review."""

    supabase = get_supabase_admin()
    try:
        current = _get_owned_post_row(supabase, post_id, user_id)
        _ensure_owned_post_editable(supabase, post_id)
        current_post_type = _community_post_type(current)
        if payload.post_type != current_post_type:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="帖子类型与原内容不一致")

        if current_post_type == "experience":
            _current_verified_mentor_author(supabase, user_id)

        update_data = {
            "category": payload.category.strip(),
            "experience_stages": payload.experience_stages if current_post_type == "experience" else [],
            "title": payload.title.strip(),
            "content": payload.content.strip(),
            "media": [item.model_dump(by_alias=True) for item in payload.media[:9]],
            "is_featured": False,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if current_post_type == "experience":
            update_data.update({
                "is_published": False,
                "review_status": "pending",
                "review_version": max(0, int(current.get("review_version") or 0)) + 1,
                "review_reason_code": None,
                "review_note": None,
                "reviewed_by": None,
                "reviewed_at": None,
                "submitted_at": datetime.now(timezone.utc).isoformat(),
            })

        response = call_supabase(
            lambda: (
                supabase.table("circle_community_posts")
                .update(update_data)
                .eq("id", post_id)
                .eq("author_id", user_id)
                .execute()
            ),
            operation_name="circle community own post update",
        )
        row = (response.data or [None])[0]
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在或已被删除")

        profiles = _fetch_community_profiles(supabase, [user_id])
        verified_author_ids = {user_id} if current_post_type == "experience" else set()
        return _post_item(
            row,
            set(),
            {},
            profiles,
            verified_author_ids,
            current_user_id=user_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(
            "Circle community own post update failed (post_id=%s error_type=%s)",
            post_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="帖子更新失败，请稍后重试",
        ) from exc


@router.patch("/my-posts/{post_id}/resubmit", response_model=CommunityPostItem)
def resubmit_my_community_experience_post(
    post_id: str,
    payload: CommunityResubmitExperiencePostRequest,
    user_id: str = Depends(get_current_user_id),
) -> CommunityPostItem:
    supabase = get_supabase_admin()
    try:
        current = _get_owned_post_row(supabase, post_id, user_id)
        if _community_post_type(current) != "experience":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="经验贴不存在")
        if _community_review_status(current) != "rejected":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="只有审核未通过的经验贴可以修改后重新提交",
            )
        _current_verified_mentor_author(supabase, user_id)
        media = [item.model_dump(by_alias=True) for item in payload.media[:9]]
        response = call_supabase(
            lambda: supabase.rpc(
                "resubmit_circle_community_experience_post",
                {
                    "p_post_id": post_id,
                    "p_author_id": user_id,
                    "p_category": payload.category,
                    "p_experience_stages": payload.experience_stages,
                    "p_title": payload.title,
                    "p_content": payload.content,
                    "p_media": media,
                },
            ).execute(),
            operation_name="circle community experience resubmit",
        )
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="经验贴审核状态已变化，请刷新后重试",
            )
        row = response.data[0]
        profiles = _fetch_community_profiles(supabase, [user_id])
        return _post_item(row, set(), {}, profiles, {user_id}, current_user_id=user_id)
    except HTTPException:
        raise
    except Exception as exc:
        message = str(exc)
        if "只有审核未通过" in message or "审核状态已变化" in message:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message) from exc
        if "经验贴不存在" in message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="经验贴不存在") from exc
        logger.warning(
            "Circle community experience resubmit failed (post_id=%s error_type=%s)",
            post_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="经验贴重新提交失败，请稍后重试",
        ) from exc


@router.delete("/my-posts", response_model=CommunityDeletePostsResponse)
def delete_my_community_posts(
    payload: CommunityDeletePostsRequest,
    user_id: str = Depends(get_current_user_id),
) -> CommunityDeletePostsResponse:
    """Hide author-deleted posts while retaining moderation and appeal evidence."""

    global _community_author_deleted_column_available

    post_ids = list(dict.fromkeys(str(post_id) for post_id in payload.post_ids))
    if not post_ids:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="请选择要删除的帖子")

    supabase = get_supabase_admin()
    try:
        deleted_at = datetime.now(timezone.utc).isoformat()
        response = call_supabase(
            lambda: (
                supabase.table("circle_community_posts")
                .update({
                    "author_deleted_at": deleted_at,
                    "is_published": False,
                    "is_featured": False,
                    "updated_at": deleted_at,
                })
                .in_("id", post_ids)
                .eq("author_id", user_id)
                .is_("author_deleted_at", "null")
                .execute()
            ),
            operation_name="circle community own post author delete",
        )
        _community_author_deleted_column_available = True
        deleted_post_ids = [
            str(row.get("id"))
            for row in (response.data or [])
            if row.get("id")
        ]
        return CommunityDeletePostsResponse(
            deleted_post_ids=deleted_post_ids,
            deleted_count=len(deleted_post_ids),
        )
    except HTTPException:
        raise
    except Exception as exc:
        if _is_missing_community_post_column_error(exc, "author_deleted_at"):
            _community_author_deleted_column_available = False
            deleted_post_ids = _legacy_author_delete_posts(
                supabase,
                post_ids=post_ids,
                user_id=user_id,
                deleted_at=deleted_at,
            )
            return CommunityDeletePostsResponse(
                deleted_post_ids=deleted_post_ids,
                deleted_count=len(deleted_post_ids),
            )
        _raise_community_service_error(exc)


@router.get("/my-reports", response_model=CommunityReportListResponse)
def list_my_community_reports(
    limit: int = Query(default=100, ge=1, le=200),
    user_id: str = Depends(get_current_user_id),
) -> CommunityReportListResponse:
    """Let reporters see the platform's current conclusion and next action."""

    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: (
                supabase.table("circle_community_reports")
                .select(
                    "id,target_type,post_id,comment_id,reason,content,status,moderation_action,"
                    "admin_note,created_at,handled_at"
                )
                .eq("reporter_user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            ),
            operation_name="circle community own report list",
        )
        rows = response.data or []
        posts, comments = _fetch_community_report_targets(supabase, rows)
        return CommunityReportListResponse(
            items=[CommunityReportItem(**_serialize_community_report(row, posts, comments)) for row in rows],
            count=len(rows),
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_service_error(exc)


@router.get("/my-content-status", response_model=CommunityModerationStatusListResponse)
def list_my_community_content_status(
    limit: int = Query(default=100, ge=1, le=200),
    user_id: str = Depends(get_current_user_id),
) -> CommunityModerationStatusListResponse:
    """Keep content authors informed when their own post or comment enters moderation."""

    supabase = get_supabase_admin()
    try:
        items = _fetch_my_community_content_status(supabase, user_id, limit=limit)
        return CommunityModerationStatusListResponse(items=items, count=len(items))
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_service_error(exc)


@router.post(
    "/moderation/{target_type}/{target_id}/appeals",
    response_model=CommunityModerationAppealItem,
    status_code=status.HTTP_201_CREATED,
)
def create_community_moderation_appeal(
    target_type: Literal["post", "comment"],
    target_id: str,
    payload: CommunityModerationAppealCreateRequest,
    user_id: str = Depends(get_current_user_id),
) -> CommunityModerationAppealItem:
    """Let the owner request a human review after their content is taken down."""

    supabase = get_supabase_admin()
    try:
        target, post_id, comment_id = _get_owned_moderation_target_or_404(
            supabase,
            target_type=target_type,
            target_id=target_id,
            user_id=user_id,
        )
        if bool(target.get("is_published")):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该内容当前正常展示，无需提交申诉")

        duplicate_query = (
            supabase.table("circle_community_appeals")
            .select("id")
            .eq("appellant_user_id", user_id)
            .eq("target_type", target_type)
            .eq("post_id", post_id)
            .limit(1)
        )
        if comment_id:
            duplicate_query = duplicate_query.eq("comment_id", comment_id)
        else:
            duplicate_query = duplicate_query.is_("comment_id", "null")
        duplicate_response = call_supabase(
            duplicate_query.execute,
            operation_name="circle community appeal duplicate lookup",
        )
        if duplicate_response.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该内容已提交过申诉，可在内容处理记录中查看进度")

        response = call_supabase(
            lambda: supabase.table("circle_community_appeals").insert({
                "appellant_user_id": user_id,
                "target_type": target_type,
                "post_id": post_id,
                "comment_id": comment_id,
                "content": str(payload.content or "").strip(),
            }).execute(),
            operation_name="circle community appeal create",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="申诉提交失败")
        return _serialize_community_appeal(response.data[0])
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_service_error(exc)


@router.get("/posts/{post_id}", response_model=CommunityPostDetailResponse)
def get_community_post(
    post_id: str,
    comments_limit: int = Query(default=20, ge=1, le=50),
    comments_cursor: str | None = Query(default=None, max_length=2048),
    user_id: str | None = Depends(get_optional_current_user_id),
) -> CommunityPostDetailResponse:
    supabase = get_supabase_admin()
    try:
        row = _get_post_row(supabase, post_id)
        comment_rows, comments_next_cursor, comments_has_more = _fetch_community_comment_page(
            supabase,
            post_id=post_id,
            limit=comments_limit,
            cursor=comments_cursor,
        )
        comment_ids = [str(item.get("id") or "") for item in comment_rows if item.get("id")]
        author_ids = [str(item.get("author_id") or "") for item in [row, *comment_rows] if item.get("author_id")]
        post_author_id = str(row.get("author_id") or "")
        with ThreadPoolExecutor(max_workers=4) as executor:
            liked_posts_future = executor.submit(_fetch_liked_post_ids, supabase, user_id, [post_id])
            liked_comments_future = executor.submit(_fetch_liked_comment_ids, supabase, user_id, comment_ids)
            profiles_future = executor.submit(_fetch_community_profiles, supabase, author_ids)
            verified_authors_future = executor.submit(
                _fetch_verified_mentor_owner_ids,
                supabase,
                [post_author_id] if post_author_id else [],
            )
            liked_post_ids = liked_posts_future.result()
            liked_comment_ids = liked_comments_future.result()
            profiles = profiles_future.result()
            verified_author_ids = verified_authors_future.result()
        if (
            _community_post_type(row) == "experience"
            and not _is_public_verified_experience_post(row, verified_author_ids)
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该经验贴当前未满足公开展示条件")
        previews = {
            post_id: [
                CommunityCommentPreview(
                    id=str(item.get("id") or "") or None,
                    author=str(item.get("author_name") or "研友"),
                    text=str(item.get("content") or ""),
                )
                for item in reversed(comment_rows[-3:])
            ]
        }
        return CommunityPostDetailResponse(
            post=_post_item(
                row,
                liked_post_ids,
                previews,
                profiles,
                verified_author_ids,
                current_user_id=user_id,
            ),
            comments=[
                _comment_item(item, user_id, profiles, liked_comment_ids)
                for item in comment_rows
            ],
            comments_next_cursor=comments_next_cursor,
            comments_has_more=comments_has_more,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_service_error(exc)


@router.get("/posts/{post_id}/comments", response_model=CommunityCommentListResponse)
def list_community_comments(
    post_id: str,
    limit: int = Query(default=20, ge=1, le=50),
    cursor: str | None = Query(default=None, max_length=2048),
    user_id: str | None = Depends(get_optional_current_user_id),
) -> CommunityCommentListResponse:
    supabase = get_supabase_admin()
    try:
        _get_post_row(supabase, post_id)
        rows, next_cursor, has_more = _fetch_community_comment_page(
            supabase,
            post_id=post_id,
            limit=limit,
            cursor=cursor,
        )
        items = _serialize_community_comment_page(supabase, rows=rows, user_id=user_id)
        return CommunityCommentListResponse(
            items=items,
            count=len(items),
            next_cursor=next_cursor,
            has_more=has_more,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_service_error(exc)


@router.post(
    "/posts/{post_id}/reports",
    response_model=CommunityReportItem,
    status_code=status.HTTP_201_CREATED,
)
def create_community_post_report(
    post_id: str,
    payload: CommunityCreateReportRequest,
    user_id: str = Depends(get_current_user_id),
) -> CommunityReportItem:
    supabase = get_supabase_admin()
    try:
        return _create_community_report(
            supabase,
            post_id=post_id,
            comment_id=None,
            payload=payload,
            user_id=user_id,
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
    image_key = uuid4().hex
    storage_path = f"{user_id}/{image_key}.{extension}"
    thumbnail_path = f"{user_id}/thumbs/{image_key}.webp"
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
        original_url = bucket.get_public_url(storage_path)
        thumbnail_url = original_url
        thumbnail = _build_community_thumbnail(data)
        if thumbnail:
            try:
                bucket.upload(
                    thumbnail_path,
                    thumbnail,
                    file_options={
                        "content-type": "image/webp",
                        "cache-control": "31536000",
                        "upsert": "false",
                    },
                )
                thumbnail_url = bucket.get_public_url(thumbnail_path)
            except Exception as exc:
                logger.warning(
                    "Circle community thumbnail upload skipped (error_type=%s)",
                    type(exc).__name__,
                )
        return CommunityImageUploadResponse(url=original_url, thumbnail_url=thumbnail_url)
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
    stage = "author_lookup"
    try:
        supabase = get_supabase_admin()
        author_name, author_avatar, author_avatar_url = _current_author(supabase, user_id)
        author_tone = "blue"
        author_verified = False
        if payload.post_type == "experience":
            stage = "mentor_verification"
            _current_verified_mentor_author(supabase, user_id)
            author_verified = True

        client_request_id = str(payload.client_request_id)
        stage = "idempotency_lookup"
        existing_post = _lookup_idempotent_community_post(
            supabase,
            author_id=user_id,
            client_request_id=client_request_id,
        )

        media = [item.model_dump(by_alias=True) for item in payload.media[:9]]
        post_data = {
            "author_id": user_id,
            "author_name": author_name,
            "author_avatar": author_avatar,
            "author_tone": author_tone,
            "category": payload.category.strip(),
            "title": payload.title.strip(),
            "content": payload.content.strip(),
            "media": media,
        }
        if payload.post_type == "experience":
            post_data.update({
                "is_published": False,
                "review_status": "pending",
                "review_version": 1,
                "review_reason_code": None,
                "review_note": None,
                "reviewed_by": None,
                "reviewed_at": None,
                "submitted_at": datetime.now(timezone.utc).isoformat(),
            })

        if existing_post is None:
            stage = "post_insert"
            post_row = _insert_community_post_with_compatibility(
                supabase,
                post_data=post_data,
                post_type=payload.post_type,
                experience_stages=payload.experience_stages,
                client_request_id=client_request_id,
            )
        else:
            post_row = existing_post

        stage = "response"
        if not post_row:
            raise RuntimeError("Community post insert returned no row")
        return _post_item(
            post_row,
            set(),
            {},
            {user_id: {"nickname": author_name, "avatar_url": author_avatar_url}},
            {user_id} if author_verified else set(),
            current_user_id=user_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_post_create_error(exc, payload=payload, stage=stage)


@router.post("/posts/{post_id}/like", response_model=CommunityLikeResponse)
def toggle_community_like(
    post_id: str,
    payload: CommunitySetLikeRequest,
    user_id: str = Depends(get_current_user_id),
    background_tasks: BackgroundTasks = None,
) -> CommunityLikeResponse:
    supabase = get_supabase_admin()
    try:
        post = _get_post_row(supabase, post_id)
        if payload.is_liked is None:
            is_liked, like_count = _toggle_community_like_without_rpc(supabase, post_id, user_id)
            changed = True
        else:
            is_liked, like_count, changed = _set_community_like(
                supabase,
                post_id=post_id,
                user_id=user_id,
                desired_liked=payload.is_liked,
            )
        if is_liked and changed:
            notification_kwargs = {
                "post": dict(post),
                "actor_user_id": user_id,
                "interaction": "like",
                "related_id": f"{post_id}:like:{user_id}",
            }
            if background_tasks is not None:
                background_tasks.add_task(_notify_community_post_interaction_background, **notification_kwargs)
            else:
                _notify_community_post_interaction(supabase, **notification_kwargs)
        return CommunityLikeResponse(
            post_id=post_id,
            is_liked=is_liked,
            like_count=like_count,
            changed=changed,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_service_error(exc)


@router.post(
    "/posts/{post_id}/comments/{comment_id}/like",
    response_model=CommunityCommentLikeResponse,
)
def toggle_community_comment_like(
    post_id: str,
    comment_id: str,
    payload: CommunitySetLikeRequest,
    user_id: str = Depends(get_current_user_id),
) -> CommunityCommentLikeResponse:
    supabase = get_supabase_admin()
    try:
        if payload.is_liked is None:
            is_liked, like_count = _toggle_community_comment_like_without_rpc(
                supabase,
                post_id,
                comment_id,
                user_id,
            )
            changed = True
        else:
            is_liked, like_count, changed = _set_community_comment_like(
                supabase,
                post_id=post_id,
                comment_id=comment_id,
                user_id=user_id,
                desired_liked=payload.is_liked,
            )
        return CommunityCommentLikeResponse(
            comment_id=comment_id,
            is_liked=is_liked,
            like_count=like_count,
            changed=changed,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_service_error(exc)


@router.get("/posts/{post_id}/likes", response_model=CommunityLikeListResponse)
def list_community_post_likes(
    post_id: str,
    limit: int = Query(default=100, ge=1, le=200),
) -> CommunityLikeListResponse:
    supabase = get_supabase_admin()
    try:
        _get_post_row(supabase, post_id)
        response = call_supabase(
            lambda: (
                supabase.table("circle_community_likes")
                .select("id,user_id,created_at", count="exact")
                .eq("post_id", post_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            ),
            operation_name="circle community like list",
        )
        rows = response.data or []
        profiles = _fetch_community_profiles(
            supabase,
            [str(row.get("user_id") or "") for row in rows],
        )
        items: list[CommunityLikeItem] = []
        for row in rows:
            profile = profiles.get(str(row.get("user_id") or ""), {})
            author = str(profile.get("nickname") or "").strip() or "研友"
            avatar_url = str(profile.get("avatar_url") or "").strip() or None
            items.append(
                CommunityLikeItem(
                    id=str(row.get("id") or row.get("user_id")),
                    author=author,
                    avatar=_first_character(author),
                    avatar_url=avatar_url,
                    liked_at=row.get("created_at"),
                )
            )
        return CommunityLikeListResponse(items=items, count=int(response.count or len(rows)))
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
    background_tasks: BackgroundTasks = None,
) -> CommunityCreateCommentResponse:
    supabase = get_supabase_admin()
    try:
        comment, comment_count, created, post, author_avatar_url, author_name = _create_community_comment_record(
            supabase,
            post_id=post_id,
            user_id=user_id,
            payload=payload,
        )
        if created:
            notification_kwargs = {
                "post": dict(post),
                "actor_user_id": user_id,
                "interaction": "comment",
                "related_id": str(comment.get("id") or post_id),
                "comment_content": str(comment.get("content") or payload.content or ""),
                "actor_name": author_name,
            }
            if background_tasks is not None:
                background_tasks.add_task(_notify_community_post_interaction_background, **notification_kwargs)
            else:
                _notify_community_post_interaction(supabase, **notification_kwargs)
        return CommunityCreateCommentResponse(
            comment=_comment_item(
                comment,
                user_id,
                {user_id: {"avatar_url": author_avatar_url}},
                set(),
            ),
            comment_count=comment_count,
            created=created,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_service_error(exc)


@router.delete(
    "/posts/{post_id}/comments/{comment_id}",
    response_model=CommunityDeleteCommentResponse,
)
def delete_community_comment(
    post_id: str,
    comment_id: str,
    user_id: str = Depends(get_current_user_id),
) -> CommunityDeleteCommentResponse:
    """Authors can retract an ordinary comment unless it is already evidence in a case."""

    supabase = get_supabase_admin()
    try:
        _get_post_row(supabase, post_id)
        comment = _get_comment_row(supabase, post_id, comment_id, visible_only=False)
        if str(comment.get("author_id") or "") != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能删除自己发布的评论")
        report_response = call_supabase(
            lambda: (
                supabase.table("circle_community_reports")
                .select("id")
                .eq("comment_id", comment_id)
                .limit(1)
                .execute()
            ),
            operation_name="circle community own comment report protection lookup",
        )
        if report_response.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该评论已进入平台处理记录，暂不能删除",
            )
        appeal_response = call_supabase(
            lambda: (
                supabase.table("circle_community_appeals")
                .select("id")
                .eq("comment_id", comment_id)
                .limit(1)
                .execute()
            ),
            operation_name="circle community own comment appeal protection lookup",
        )
        if appeal_response.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该评论已有内容申诉留档，为保留平台处理记录暂不能删除",
            )
        response = call_supabase(
            lambda: (
                supabase.table("circle_community_comments")
                .delete()
                .eq("id", comment_id)
                .eq("post_id", post_id)
                .eq("author_id", user_id)
                .execute()
            ),
            operation_name="circle community own comment delete",
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该评论")
        updated_post = _get_post_row(supabase, post_id)
        return CommunityDeleteCommentResponse(
            comment_id=comment_id,
            comment_count=int(updated_post.get("comment_count") or 0),
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_service_error(exc)


@router.post(
    "/posts/{post_id}/comments/{comment_id}/reports",
    response_model=CommunityReportItem,
    status_code=status.HTTP_201_CREATED,
)
def create_community_comment_report(
    post_id: str,
    comment_id: str,
    payload: CommunityCreateReportRequest,
    user_id: str = Depends(get_current_user_id),
) -> CommunityReportItem:
    supabase = get_supabase_admin()
    try:
        return _create_community_report(
            supabase,
            post_id=post_id,
            comment_id=comment_id,
            payload=payload,
            user_id=user_id,
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
        counted, view_count = _register_community_view_without_rpc(
            supabase,
            post_id,
            user_id,
            anonymous_id,
        )
        return CommunityViewResponse(
            post_id=post_id,
            counted=counted,
            view_count=view_count,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_community_service_error(exc)
