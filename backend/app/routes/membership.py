from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.config import get_settings
from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.membership import (
    CreateMembershipOrderRequest,
    MembershipOrderResponse,
    MembershipPlan,
    MembershipStatusResponse,
    PaymentWebhookRequest,
    PaymentWebhookResponse,
)

router = APIRouter(prefix="/membership", tags=["会员"])

MEMBERSHIP_PLANS = {
    "pro_monthly": MembershipPlan(
        code="pro_monthly",
        name="月卡",
        price_cents=990,
        price_label="9.9元/月",
        duration_days=31,
        description="适合短期体验 Pro 会员能力",
    ),
    "pro_quarterly": MembershipPlan(
        code="pro_quarterly",
        name="季卡",
        price_cents=2490,
        price_label="24.9元/季",
        duration_days=93,
        description="适合一轮系统复习周期",
    ),
}


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


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


def _get_plan_or_raise(plan_code: str) -> MembershipPlan:
    plan = MEMBERSHIP_PLANS.get(plan_code)
    if not plan:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid membership plan")
    return plan


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _activate_membership(user_id: str, plan: MembershipPlan) -> None:
    supabase_admin = get_supabase_admin()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=plan.duration_days)
    supabase_admin.table("users").update(
        {
            "membership_status": "active",
            "membership_plan": plan.code,
            "membership_started_at": now.isoformat(),
            "membership_expires_at": expires_at.isoformat(),
            "membership_updated_at": now.isoformat(),
        }
    ).eq("id", user_id).execute()


@router.get("/plans", response_model=list[MembershipPlan])
def list_membership_plans() -> list[MembershipPlan]:
    return list(MEMBERSHIP_PLANS.values())


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
