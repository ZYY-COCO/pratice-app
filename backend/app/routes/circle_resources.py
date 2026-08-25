"""Public and question-portal APIs for recommended materials and courses."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import get_supabase_admin
from app.dependencies import require_question_admin_portal_user
from app.schemas.circle_resources import (
    CircleResourceAdminListResponse,
    CircleResourceDeleteResponse,
    CircleResourceItem,
    CircleResourceListResponse,
    CircleResourceUpsertRequest,
)
from app.services.supabase_resilience import call_supabase, is_missing_supabase_relation_error


router = APIRouter(prefix="/circle/resources", tags=["研圈资料"])
admin_router = APIRouter(prefix="/admin/question-portal/resources", tags=["题库管理后台"])
logger = logging.getLogger(__name__)

RESOURCE_TABLE = "circle_resource_items"
RESOURCE_FIELDS = (
    "id,resource_type,title,summary,subject,tags,cover_url,share_url,access_code,"
    "instructor_name,course_price,sort_order,status,published_at,created_at,updated_at"
)
RESOURCE_TYPES = {"material", "course"}
RESOURCE_STATUSES = {"draft", "published", "archived"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _normalized_tags(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    tags: list[str] = []
    for item in value:
        tag = str(item or "").strip()
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def _item_from_row(row: dict) -> CircleResourceItem:
    price = row.get("course_price")
    try:
        normalized_price = float(price) if price not in (None, "") else None
    except (TypeError, ValueError):
        normalized_price = None
    resource_type = str(row.get("resource_type") or "material")
    resource_status = str(row.get("status") or "draft")
    return CircleResourceItem(
        id=str(row.get("id") or ""),
        resource_type=resource_type if resource_type in RESOURCE_TYPES else "material",
        title=str(row.get("title") or ""),
        summary=str(row.get("summary") or ""),
        subject=str(row.get("subject") or ""),
        tags=_normalized_tags(row.get("tags")),
        cover_url=str(row.get("cover_url") or ""),
        share_url=str(row.get("share_url") or ""),
        access_code=str(row.get("access_code") or ""),
        instructor_name=str(row.get("instructor_name") or ""),
        course_price=normalized_price,
        sort_order=int(row.get("sort_order") or 0),
        status=resource_status if resource_status in RESOURCE_STATUSES else "draft",
        published_at=row.get("published_at"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def _raise_resource_data_error(exc: Exception) -> None:
    if is_missing_supabase_relation_error(exc):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="资料管理数据尚未初始化，请先执行 circle_resource_management.sql。",
        ) from exc
    logger.warning("Circle resource request failed (error_type=%s)", type(exc).__name__)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="资料管理服务暂时不可用，请稍后重试。",
    ) from exc


def _build_resource_row(payload: CircleResourceUpsertRequest, admin_profile: dict) -> dict:
    current = _now()
    row = payload.model_dump()
    row["tags"] = list(payload.tags)
    row["created_by"] = admin_profile.get("id")
    row["updated_by"] = admin_profile.get("id")
    row["updated_at"] = _to_iso(current)
    if payload.status == "published":
        row["published_at"] = _to_iso(current)
    else:
        row["published_at"] = None
    return row


def _record_admin_action(supabase, admin_profile: dict, action: str, item: CircleResourceItem) -> None:
    try:
        supabase.table("admin_action_logs").insert(
            {
                "admin_user_id": admin_profile.get("id"),
                "action": action,
                "target_type": "circle_resource_item",
                "target_id": item.id,
                "details": {"resource_type": item.resource_type, "title": item.title, "status": item.status},
            }
        ).execute()
    except Exception:
        # Audit history should not make a content update unavailable during a partial migration.
        return


def _safe_keyword(value: str | None) -> str:
    return re.sub(r"[,%()\\]", " ", str(value or "")).strip()


@router.get("", response_model=CircleResourceListResponse)
def list_public_circle_resources(
    resource_type: Literal["material", "course"] = Query(default="material"),
    limit: int = Query(default=100, ge=1, le=100),
) -> CircleResourceListResponse:
    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: (
                supabase.table(RESOURCE_TABLE)
                .select(RESOURCE_FIELDS)
                .eq("resource_type", resource_type)
                .eq("status", "published")
                .order("sort_order")
                .order("published_at", desc=True)
                .limit(limit)
                .execute()
            ),
            operation_name="public circle resource list",
        )
    except Exception as exc:
        _raise_resource_data_error(exc)
    items = [_item_from_row(row) for row in (response.data or [])]
    return CircleResourceListResponse(items=items, count=len(items))


@admin_router.get("", response_model=CircleResourceAdminListResponse)
def list_admin_circle_resources(
    resource_type: Literal["material", "course"] = Query(default="material"),
    item_status: Literal["all", "draft", "published", "archived"] = Query(default="all", alias="status"),
    keyword: str = Query(default="", max_length=100),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_question_admin_portal_user),
) -> CircleResourceAdminListResponse:
    supabase = get_supabase_admin()
    query = (
        supabase.table(RESOURCE_TABLE)
        .select(RESOURCE_FIELDS, count="exact")
        .eq("resource_type", resource_type)
        .order("sort_order")
        .order("updated_at", desc=True)
    )
    if item_status != "all":
        query = query.eq("status", item_status)
    normalized_keyword = _safe_keyword(keyword)
    if normalized_keyword:
        query = query.or_(
            f"title.ilike.%{normalized_keyword}%,summary.ilike.%{normalized_keyword}%,subject.ilike.%{normalized_keyword}%"
        )
    try:
        response = call_supabase(
            lambda: query.range(offset, offset + limit - 1).execute(),
            operation_name="admin circle resource list",
        )
    except Exception as exc:
        _raise_resource_data_error(exc)
    return CircleResourceAdminListResponse(
        items=[_item_from_row(row) for row in (response.data or [])],
        count=int(response.count or 0),
        limit=limit,
        offset=offset,
    )


@admin_router.post("", response_model=CircleResourceItem, status_code=status.HTTP_201_CREATED)
def create_admin_circle_resource(
    payload: CircleResourceUpsertRequest,
    admin_profile: dict = Depends(require_question_admin_portal_user),
) -> CircleResourceItem:
    supabase = get_supabase_admin()
    row = _build_resource_row(payload, admin_profile)
    try:
        response = call_supabase(
            lambda: supabase.table(RESOURCE_TABLE).insert(row).execute(),
            operation_name="create circle resource",
        )
    except Exception as exc:
        _raise_resource_data_error(exc)
    if not response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="资料保存失败，请稍后重试。")
    item = _item_from_row(response.data[0])
    _record_admin_action(supabase, admin_profile, "create_circle_resource", item)
    return item


@admin_router.patch("/{resource_id}", response_model=CircleResourceItem)
def update_admin_circle_resource(
    resource_id: str,
    payload: CircleResourceUpsertRequest,
    admin_profile: dict = Depends(require_question_admin_portal_user),
) -> CircleResourceItem:
    supabase = get_supabase_admin()
    try:
        existing_response = call_supabase(
            lambda: (
                supabase.table(RESOURCE_TABLE)
                .select("id,status,published_at")
                .eq("id", resource_id)
                .limit(1)
                .execute()
            ),
            operation_name="find circle resource",
        )
    except Exception as exc:
        _raise_resource_data_error(exc)
    if not existing_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资料不存在或已删除。")

    existing = existing_response.data[0]
    row = _build_resource_row(payload, admin_profile)
    row.pop("created_by", None)
    if payload.status == "published" and existing.get("status") == "published":
        row["published_at"] = existing.get("published_at") or _to_iso(_now())
    try:
        response = call_supabase(
            lambda: supabase.table(RESOURCE_TABLE).update(row).eq("id", resource_id).execute(),
            operation_name="update circle resource",
        )
    except Exception as exc:
        _raise_resource_data_error(exc)
    if not response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="资料更新失败，请稍后重试。")
    item = _item_from_row(response.data[0])
    _record_admin_action(supabase, admin_profile, "update_circle_resource", item)
    return item


@admin_router.delete("/{resource_id}", response_model=CircleResourceDeleteResponse)
def delete_admin_circle_resource(
    resource_id: str,
    admin_profile: dict = Depends(require_question_admin_portal_user),
) -> CircleResourceDeleteResponse:
    supabase = get_supabase_admin()
    try:
        existing_response = call_supabase(
            lambda: (
                supabase.table(RESOURCE_TABLE)
                .select(RESOURCE_FIELDS)
                .eq("id", resource_id)
                .limit(1)
                .execute()
            ),
            operation_name="find circle resource for deletion",
        )
    except Exception as exc:
        _raise_resource_data_error(exc)
    if not existing_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资料不存在或已删除。")
    item = _item_from_row(existing_response.data[0])
    try:
        call_supabase(
            lambda: supabase.table(RESOURCE_TABLE).delete().eq("id", resource_id).execute(),
            operation_name="delete circle resource",
        )
    except Exception as exc:
        _raise_resource_data_error(exc)
    _record_admin_action(supabase, admin_profile, "delete_circle_resource", item)
    return CircleResourceDeleteResponse(id=resource_id)
