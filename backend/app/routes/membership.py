import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.config import get_settings
from app.db import get_supabase_admin
from app.dependencies import get_current_user_id, require_question_admin_user
from app.schemas.membership import (
    CreateMembershipOrderRequest,
    MembershipOrderResponse,
    MembershipPlan,
    MembershipStatusResponse,
    MembershipSubscriptionPageConfig,
    MembershipSubscriptionPageConfigPayload,
    PaymentWebhookRequest,
    PaymentWebhookResponse,
)

router = APIRouter(prefix="/membership", tags=["会员"])
logger = logging.getLogger(__name__)

MEMBERSHIP_PAGE_SETTINGS_TABLE = "membership_page_settings"
MEMBERSHIP_PAGE_SETTINGS_ID = "default"
DEFAULT_SUBSCRIPTION_PAGE_CONFIG = {
    "title": "开通 PLUS",
    "brand_name": "HMTC 升学交流圈",
    "benefits": [
        "完整访问港澳台考研题库",
        "获得 AI 专项训练与学习建议",
        "查看学习报告与错题复盘",
        "优先体验后续 PLUS 学习权益",
    ],
    "monthly_price_cents": 8800,
    "quarterly_price_cents": 22800,
    "plan_hint": "选择适合你的学习计划",
    "primary_button_text": "订阅 PLUS",
    "secondary_button_text": "恢复购买",
    "description_text": "订阅服务开通后，将按所选套餐为你提供 PLUS 学习权益。",
    "terms_text": "服务条款 · 隐私政策",
    "updated_at": None,
}


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_text(value: object, fallback: str) -> str:
    normalized = str(value or "").strip()
    return normalized or fallback


def _clean_price(value: object, fallback: int) -> int:
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        return fallback
    return normalized if normalized > 0 else fallback


def _clean_benefits(value: object) -> list[str]:
    source = value
    if isinstance(source, str):
        try:
            source = json.loads(source)
        except json.JSONDecodeError:
            source = []
    if not isinstance(source, list):
        return list(DEFAULT_SUBSCRIPTION_PAGE_CONFIG["benefits"])
    normalized = [str(item or "").strip() for item in source]
    normalized = [item for item in normalized if item][:8]
    return normalized or list(DEFAULT_SUBSCRIPTION_PAGE_CONFIG["benefits"])


def _normalize_subscription_page_config(row: dict | None) -> dict:
    source = row or {}
    return {
        "title": _clean_text(source.get("title"), DEFAULT_SUBSCRIPTION_PAGE_CONFIG["title"]),
        "brand_name": _clean_text(source.get("brand_name"), DEFAULT_SUBSCRIPTION_PAGE_CONFIG["brand_name"]),
        "benefits": _clean_benefits(source.get("benefits")),
        "monthly_price_cents": _clean_price(
            source.get("monthly_price_cents"),
            DEFAULT_SUBSCRIPTION_PAGE_CONFIG["monthly_price_cents"],
        ),
        "quarterly_price_cents": _clean_price(
            source.get("quarterly_price_cents"),
            DEFAULT_SUBSCRIPTION_PAGE_CONFIG["quarterly_price_cents"],
        ),
        "plan_hint": _clean_text(source.get("plan_hint"), DEFAULT_SUBSCRIPTION_PAGE_CONFIG["plan_hint"]),
        "primary_button_text": _clean_text(
            source.get("primary_button_text"),
            DEFAULT_SUBSCRIPTION_PAGE_CONFIG["primary_button_text"],
        ),
        "secondary_button_text": _clean_text(
            source.get("secondary_button_text"),
            DEFAULT_SUBSCRIPTION_PAGE_CONFIG["secondary_button_text"],
        ),
        "description_text": _clean_text(
            source.get("description_text"),
            DEFAULT_SUBSCRIPTION_PAGE_CONFIG["description_text"],
        ),
        "terms_text": _clean_text(source.get("terms_text"), DEFAULT_SUBSCRIPTION_PAGE_CONFIG["terms_text"]),
        "updated_at": source.get("updated_at") or None,
    }


def _validate_subscription_page_config(payload: MembershipSubscriptionPageConfigPayload) -> dict:
    source = payload.model_dump()
    text_fields = (
        "title",
        "brand_name",
        "plan_hint",
        "primary_button_text",
        "secondary_button_text",
        "description_text",
        "terms_text",
    )
    for field in text_fields:
        source[field] = str(source.get(field) or "").strip()
        if not source[field]:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{field} cannot be empty")

    benefits = [str(item or "").strip() for item in source.get("benefits") or []]
    if not benefits or any(not item for item in benefits):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="benefits cannot be empty")
    if len(benefits) > 8:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="benefits exceeds the maximum")
    source["benefits"] = benefits
    return source


def _load_subscription_page_config(*, require_storage: bool = False) -> dict:
    try:
        response = (
            get_supabase_admin()
            .table(MEMBERSHIP_PAGE_SETTINGS_TABLE)
            .select("*")
            .eq("id", MEMBERSHIP_PAGE_SETTINGS_ID)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        # The user-side sheet remains usable before the incremental SQL is applied.
        logger.warning("Membership page config lookup fell back to defaults (error_type=%s)", type(exc).__name__)
        if require_storage:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="会员配置表暂未就绪，请先执行 database/membership_page_settings.sql",
            ) from exc
        return _normalize_subscription_page_config(None)
    return _normalize_subscription_page_config((response.data or [None])[0])


def _format_price_label(price_cents: int, suffix: str) -> str:
    amount = price_cents / 100
    if amount.is_integer():
        return f"{int(amount)}元{suffix}"
    return f"{amount:.2f}".rstrip("0").rstrip(".") + f"元{suffix}"


def _build_membership_plans(page_config: dict | None = None) -> dict[str, MembershipPlan]:
    config = page_config or _load_subscription_page_config()
    monthly_price_cents = _clean_price(
        config.get("monthly_price_cents"),
        DEFAULT_SUBSCRIPTION_PAGE_CONFIG["monthly_price_cents"],
    )
    quarterly_price_cents = _clean_price(
        config.get("quarterly_price_cents"),
        DEFAULT_SUBSCRIPTION_PAGE_CONFIG["quarterly_price_cents"],
    )
    return {
        "pro_monthly": MembershipPlan(
            code="pro_monthly",
            name="月卡",
            price_cents=monthly_price_cents,
            price_label=_format_price_label(monthly_price_cents, "/月"),
            duration_days=31,
            description="适合短期体验 PLUS 学习能力",
        ),
        "pro_quarterly": MembershipPlan(
            code="pro_quarterly",
            name="季卡",
            price_cents=quarterly_price_cents,
            price_label=_format_price_label(quarterly_price_cents, "/季"),
            duration_days=93,
            description="适合一轮系统复习周期",
        ),
    }


def _get_plan_or_raise(plan_code: str) -> MembershipPlan:
    plan = _build_membership_plans().get(plan_code)
    if not plan:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid membership plan")
    return plan


def _build_membership_status(profile: dict) -> MembershipStatusResponse:
    raw_status = str(profile.get("membership_status") or "inactive").lower()
    expires_at = _parse_datetime(profile.get("membership_expires_at"))
    is_expired = bool(expires_at and expires_at < datetime.now(timezone.utc))
    effective_status = "expired" if raw_status == "active" and is_expired else raw_status
    return MembershipStatusResponse(
        user_id=profile["id"],
        membership_status=effective_status,
        membership_plan=profile.get("membership_plan"),
        membership_started_at=profile.get("membership_started_at"),
        membership_expires_at=profile.get("membership_expires_at"),
        membership_updated_at=profile.get("membership_updated_at"),
        membership_active=effective_status == "active",
    )


def _resolve_membership_period(
    profile: dict | None,
    plan: MembershipPlan,
    *,
    now: datetime | None = None,
) -> tuple[datetime, datetime]:
    """Keep an active member's remaining time when they renew."""

    current_time = now or datetime.now(timezone.utc)
    source = profile or {}
    raw_status = str(source.get("membership_status") or "inactive").lower()
    current_expiry = _parse_datetime(source.get("membership_expires_at"))
    is_currently_active = (
        raw_status == "active"
        and current_expiry is not None
        and current_expiry > current_time
    )
    current_started_at = _parse_datetime(source.get("membership_started_at"))
    started_at = current_started_at if is_currently_active and current_started_at else current_time
    renewal_base = current_expiry if is_currently_active else current_time
    return started_at, renewal_base + timedelta(days=plan.duration_days)


def _activate_membership(user_id: str, plan: MembershipPlan) -> None:
    supabase_admin = get_supabase_admin()
    now = datetime.now(timezone.utc)
    profile_response = (
        supabase_admin.table("users")
        .select("membership_status,membership_started_at,membership_expires_at")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    profile = (profile_response.data or [{}])[0]
    started_at, expires_at = _resolve_membership_period(profile, plan, now=now)
    supabase_admin.table("users").update(
        {
            "membership_status": "active",
            "membership_plan": plan.code,
            "membership_started_at": started_at.isoformat(),
            "membership_expires_at": expires_at.isoformat(),
            "membership_updated_at": now.isoformat(),
        }
    ).eq("id", user_id).execute()


@router.get("/subscription-page-config", response_model=MembershipSubscriptionPageConfig)
def get_subscription_page_config() -> MembershipSubscriptionPageConfig:
    """Public config used by the user-side PLUS subscription sheet."""

    return MembershipSubscriptionPageConfig(**_load_subscription_page_config())


@router.get("/admin/subscription-page-config", response_model=MembershipSubscriptionPageConfig)
def get_admin_subscription_page_config(
    _: dict = Depends(require_question_admin_user),
) -> MembershipSubscriptionPageConfig:
    return MembershipSubscriptionPageConfig(**_load_subscription_page_config(require_storage=True))


@router.put("/admin/subscription-page-config", response_model=MembershipSubscriptionPageConfig)
def update_admin_subscription_page_config(
    payload: MembershipSubscriptionPageConfigPayload,
    admin_profile: dict = Depends(require_question_admin_user),
) -> MembershipSubscriptionPageConfig:
    data = _validate_subscription_page_config(payload)
    record = {
        "id": MEMBERSHIP_PAGE_SETTINGS_ID,
        **data,
        "updated_by": admin_profile.get("id"),
        "updated_at": _utc_now_iso(),
    }
    try:
        response = get_supabase_admin().table(MEMBERSHIP_PAGE_SETTINGS_TABLE).upsert(record).execute()
    except Exception as exc:
        logger.warning("Membership page config save failed (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="会员配置表暂未就绪，请先执行 database/membership_page_settings.sql",
        ) from exc
    saved = (response.data or [record])[0]
    return MembershipSubscriptionPageConfig(**_normalize_subscription_page_config(saved))


@router.get("/plans", response_model=list[MembershipPlan])
def list_membership_plans() -> list[MembershipPlan]:
    return list(_build_membership_plans().values())


@router.get("/status", response_model=MembershipStatusResponse)
def get_membership_status(user_id: str = Depends(get_current_user_id)) -> MembershipStatusResponse:
    supabase_admin = get_supabase_admin()
    response = supabase_admin.table("users").select("*").eq("id", user_id).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
    return _build_membership_status(response.data[0])


@router.post("/orders", response_model=MembershipOrderResponse)
def create_membership_order(
    payload: CreateMembershipOrderRequest,
    user_id: str = Depends(get_current_user_id),
) -> MembershipOrderResponse:
    plan = _get_plan_or_raise(payload.plan_code)
    supabase_admin = get_supabase_admin()
    order_id = str(uuid4())
    provider = "manual"
    provider_order_id = f"manual_{order_id}"
    order = {
        "id": order_id,
        "user_id": user_id,
        "provider": provider,
        "provider_order_id": provider_order_id,
        "plan_code": plan.code,
        "amount_cents": plan.price_cents,
        "currency": "CNY",
        "status": "pending",
        "created_at": _utc_now_iso(),
        "updated_at": _utc_now_iso(),
    }
    supabase_admin.table("membership_orders").insert(order).execute()
    return MembershipOrderResponse(
        order_id=order_id,
        provider=provider,
        provider_order_id=provider_order_id,
        plan_code=plan.code,
        amount_cents=plan.price_cents,
        currency="CNY",
        status="pending",
        checkout_url=None,
        message="订单已创建，等待接入正式支付渠道。",
    )


@router.post("/webhooks/manual", response_model=PaymentWebhookResponse)
def handle_manual_payment_webhook(
    payload: PaymentWebhookRequest,
    x_payment_webhook_secret: Annotated[str | None, Header()] = None,
) -> PaymentWebhookResponse:
    settings = get_settings()
    if not settings.payment_webhook_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Payment webhook is not configured")
    if x_payment_webhook_secret != settings.payment_webhook_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid payment webhook secret")

    next_status = payload.status.lower()
    if next_status not in {"paid", "failed", "cancelled", "refunded"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment status")

    supabase_admin = get_supabase_admin()
    order_response = (
        supabase_admin.table("membership_orders")
        .select("*")
        .eq("provider", payload.provider)
        .eq("provider_order_id", payload.provider_order_id)
        .limit(1)
        .execute()
    )
    if not order_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership order not found")

    order = order_response.data[0]
    update_data = {
        "status": next_status,
        "raw_payload": payload.raw_payload or {},
        "updated_at": _utc_now_iso(),
    }
    if next_status == "paid":
        update_data["paid_at"] = _utc_now_iso()
    supabase_admin.table("membership_orders").update(update_data).eq("id", order["id"]).execute()

    if next_status == "paid":
        plan = _get_plan_or_raise(order["plan_code"])
        _activate_membership(order["user_id"], plan)
        return PaymentWebhookResponse(detail="Membership activated", membership_active=True)
    return PaymentWebhookResponse(detail=f"Order status updated to {next_status}", membership_active=False)
