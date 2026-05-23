from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import get_supabase_admin
from app.dependencies import get_current_user_id, require_admin_user
from app.schemas.official_messages import (
    OfficialMessageAdminListResponse,
    OfficialMessageItem,
    OfficialMessageListResponse,
    OfficialMessagePayload,
    OfficialMessageReadResponse,
)

router = APIRouter(prefix="/official-messages", tags=["official messages"])
admin_router = APIRouter(prefix="/admin/messages", tags=["admin"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _is_visible_message(row: dict, current: datetime) -> bool:
    if row.get("status") != "published":
        return False
    published_at = _parse_datetime(row.get("published_at"))
    expires_at = _parse_datetime(row.get("expires_at"))
    if published_at and published_at > current:
        return False
    if expires_at and expires_at <= current:
        return False
    return True


def _fetch_visible_messages(supabase) -> list[dict]:
    response = (
        supabase.table("official_messages")
        .select("*")
        .neq("status", "archived")
        .order("published_at", desc=True)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    current = _now()
    return [row for row in (response.data or []) if _is_visible_message(row, current)]


def _fetch_read_message_ids(supabase, user_id: str, message_ids: list[str]) -> set[str]:
    if not message_ids:
        return set()
    response = (
        supabase.table("user_official_message_reads")
        .select("message_id")
        .eq("user_id", user_id)
        .in_("message_id", message_ids)
        .execute()
    )
    return {str(row.get("message_id")) for row in (response.data or []) if row.get("message_id")}


def _message_item(row: dict, read_ids: set[str]) -> OfficialMessageItem:
    message_id = str(row.get("id"))
    return OfficialMessageItem(
        id=message_id,
        title=row.get("title") or "",
        content=row.get("content") or "",
        status=row.get("status") or "draft",
        published_at=row.get("published_at"),
        expires_at=row.get("expires_at"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        read=message_id in read_ids,
    )


@router.get("", response_model=OfficialMessageListResponse)
def list_official_messages(user_id: str = Depends(get_current_user_id)) -> OfficialMessageListResponse:
    supabase = get_supabase_admin()
    rows = _fetch_visible_messages(supabase)
    message_ids = [str(row.get("id")) for row in rows if row.get("id")]
    read_ids = _fetch_read_message_ids(supabase, user_id, message_ids)
    items = [_message_item(row, read_ids) for row in rows]
    unread_count = sum(1 for item in items if not item.read)
    return OfficialMessageListResponse(items=items, unread_count=unread_count)


@router.post("/{message_id}/read", response_model=OfficialMessageReadResponse)
def mark_official_message_read(
    message_id: str,
    user_id: str = Depends(get_current_user_id),
) -> OfficialMessageReadResponse:
    supabase = get_supabase_admin()
    message_response = supabase.table("official_messages").select("id").eq("id", message_id).limit(1).execute()
    if not message_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Official message not found")
    supabase.table("user_official_message_reads").upsert(
        {
            "user_id": user_id,
            "message_id": message_id,
            "read_at": _to_iso(_now()),
        },
        on_conflict="user_id,message_id",
    ).execute()
    return OfficialMessageReadResponse()


@admin_router.get("", response_model=OfficialMessageAdminListResponse)
def admin_list_official_messages(
    message_status: str | None = Query(default=None, alias="status", max_length=20),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_admin_user),
) -> OfficialMessageAdminListResponse:
    supabase = get_supabase_admin()
    query = supabase.table("official_messages").select("*", count="exact").order("created_at", desc=True)
    if message_status:
        query = query.eq("status", message_status)
    response = query.range(offset, offset + limit - 1).execute()
    return OfficialMessageAdminListResponse(items=response.data or [], count=int(response.count or 0))


@admin_router.post("", response_model=dict)
def admin_create_official_message(
    payload: OfficialMessagePayload,
    admin_profile: dict = Depends(require_admin_user),
) -> dict:
    supabase = get_supabase_admin()
    current = _now()
    row = {
        "title": payload.title.strip(),
        "content": payload.content.strip(),
        "status": payload.status,
        "expires_at": payload.expires_at,
        "published_at": _to_iso(current) if payload.status == "published" else None,
        "created_by": admin_profile.get("id"),
        "updated_by": admin_profile.get("id"),
        "updated_at": _to_iso(current),
    }
    response = supabase.table("official_messages").insert(row).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Official message create failed")
    return response.data[0]


@admin_router.patch("/{message_id}", response_model=dict)
def admin_update_official_message(
    message_id: str,
    payload: OfficialMessagePayload,
    admin_profile: dict = Depends(require_admin_user),
) -> dict:
    supabase = get_supabase_admin()
    current = _now()
    existing_response = supabase.table("official_messages").select("*").eq("id", message_id).limit(1).execute()
    if not existing_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Official message not found")
    existing = existing_response.data[0]
    update_data = {
        "title": payload.title.strip(),
        "content": payload.content.strip(),
        "status": payload.status,
        "expires_at": payload.expires_at,
        "updated_by": admin_profile.get("id"),
        "updated_at": _to_iso(current),
    }
    if payload.status == "published" and not existing.get("published_at"):
        update_data["published_at"] = _to_iso(current)
    response = supabase.table("official_messages").update(update_data).eq("id", message_id).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Official message update failed")
    return response.data[0]
