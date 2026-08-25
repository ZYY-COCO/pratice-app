from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config import get_settings
from app.db import get_supabase_admin
from app.dependencies import get_current_user_id
from app.schemas.wallet import WalletSummaryResponse, WalletTransactionItem
from app.services.supabase_resilience import call_supabase, is_missing_supabase_relation_error


router = APIRouter(prefix="/wallet", tags=["钱包"])


def _allowed_fund_mode(requested_mode: str | None) -> str:
    if requested_mode == "demo" and get_settings().mentor_consultation_demo_payment_enabled:
        return "demo"
    return "real"


def _money(cents: object) -> float:
    return round(int(cents or 0) / 100, 2)


def _month_key(value: object) -> str:
    text = str(value or "")
    return text[:7] if len(text) >= 7 else datetime.now(timezone.utc).strftime("%Y-%m")


def _activity_to_item(row: dict) -> WalletTransactionItem:
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    public_metadata = {
        key: metadata.get(key)
        for key in (
            "order_no",
            "consultation_type",
            "mentor_display_name",
            "mentor_school",
            "mentor_major",
        )
        if metadata.get(key) not in (None, "")
    }
    business_type = str(row.get("business_type") or "wallet")
    labels = {
        "consultation_payment": ("咨询支付", "咨", "blue"),
        "consultation_refund": ("咨询订单退款", "退", "mint"),
        "consultation_income_pending": ("咨询收入", "入", "mint"),
        "consultation_income_settled": ("待结算转入余额", "结", "cyan"),
        "consultation_income_reversed": ("咨询退款扣回", "调", "warm"),
    }
    title, icon_label, icon_tone = labels.get(business_type, ("钱包账单", "账", "blue"))
    if business_type == "consultation_income_reversed" and row.get("wallet_role") == "user":
        title, icon_label, icon_tone = "咨询订单退款", "退", "mint"
    if business_type == "consultation_payment" and metadata.get("mentor_display_name"):
        title = f"{metadata['mentor_display_name']} · 咨询支付"
    status_label = "completed"
    settlement_status = None
    if business_type == "consultation_income_pending":
        status_label = "settling"
        settlement_status = "待结算"
    elif business_type == "consultation_income_settled":
        status_label = "withdrawable"
        settlement_status = "已结算，可提现"
    elif business_type in {"consultation_refund", "consultation_income_reversed"}:
        status_label = "refunded"
        settlement_status = "已退款"
    occurred_at = row.get("occurred_at") or row.get("created_at")
    return WalletTransactionItem(
        id=str(row.get("id") or ""),
        transaction_no=str(row.get("transaction_no") or ""),
        fund_mode="demo" if row.get("fund_mode") == "demo" else "real",
        type=business_type,
        title=title,
        description=str(row.get("description") or ""),
        amount=_money(row.get("display_amount_cents")),
        status=status_label,
        month_key=_month_key(occurred_at),
        created_at=occurred_at,
        completed_at=occurred_at,
        order_id=str(metadata.get("order_no") or metadata.get("order_id") or "") or None,
        counterparty="港研通咨询服务",
        mentor=str(metadata.get("mentor_display_name") or "") or None,
        settlement_status=settlement_status,
        payment_method=("本地 Demo（无真实资金）" if row.get("fund_mode") == "demo" else "支付渠道"),
        note="Demo 账本与真实资金完全隔离" if row.get("fund_mode") == "demo" else None,
        icon_label=icon_label,
        icon_tone=icon_tone,
        metadata=public_metadata,
    )


@router.get("", response_model=WalletSummaryResponse)
def get_wallet_summary(
    role: Literal["user", "mentor"] = Query(default="user"),
    mode: Literal["demo", "real"] | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    user_id: str = Depends(get_current_user_id),
) -> WalletSummaryResponse:
    fund_mode = _allowed_fund_mode(mode)
    settings = get_settings()
    supabase = get_supabase_admin()
    if role == "mentor":
        try:
            mentor_response = call_supabase(
                lambda: (
                    supabase.table("mentor_profiles")
                    .select("id")
                    .eq("owner_user_id", user_id)
                    .eq("verification_status", "verified")
                    .limit(1)
                    .execute()
                ),
                operation_name="wallet mentor ownership lookup",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="认证前辈钱包暂时不可用，请稍后重试",
            ) from exc
        if not mentor_response.data:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前账号尚未具备认证前辈钱包")

    try:
        balance_response = call_supabase(
            lambda: (
                supabase.table("wallet_user_balances")
                .select("account_type,balance_cents")
                .eq("user_id", user_id)
                .eq("wallet_role", role)
                .eq("fund_mode", fund_mode)
                .execute()
            ),
            operation_name="wallet balance lookup",
        )
        activity_response = call_supabase(
            lambda: (
                supabase.table("wallet_user_activity")
                .select("*")
                .eq("user_id", user_id)
                .eq("wallet_role", role)
                .eq("fund_mode", fund_mode)
                .order("occurred_at", desc=True)
                .limit(limit)
                .execute()
            ),
            operation_name="wallet activity lookup",
        )
        summary_response = call_supabase(
            lambda: (
                supabase.table("wallet_user_summaries")
                .select("monthly_expense_cents,monthly_refund_cents,monthly_income_cents,total_income_cents,total_paid_cents")
                .eq("user_id", user_id)
                .eq("wallet_role", role)
                .eq("fund_mode", fund_mode)
                .limit(1)
                .execute()
            ),
            operation_name="wallet aggregate summary lookup",
        )
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="钱包账本正在初始化，请先执行第二批数据库迁移",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="钱包账本暂时不可用，请稍后重试",
        ) from exc

    balances = {
        str(row.get("account_type") or ""): int(row.get("balance_cents") or 0)
        for row in (balance_response.data or [])
    }
    transactions = [_activity_to_item(row) for row in (activity_response.data or [])]
    summary = (summary_response.data or [{}])[0]
    real_payment_enabled = bool(
        settings.mentor_consultation_real_payment_enabled
        and settings.mentor_consultation_payment_provider != "unconfigured"
        and settings.mentor_consultation_payment_checkout_url
        and settings.payment_webhook_secret
    )
    if fund_mode == "demo":
        message = "当前展示本地 Demo 账本，所有金额均不计入真实余额。"
    elif real_payment_enabled:
        message = "当前展示真实账本，资金变化以支付渠道确认结果为准。"
    else:
        message = "微信支付商户资质审核中；当前仅展示真实账本已有记录，不开放充值或提现。"
    return WalletSummaryResponse(
        role=role,
        fund_mode=fund_mode,
        balance=_money(balances.get("user_wallet", 0)),
        withdrawable_balance=_money(balances.get("mentor_available", 0)),
        pending_settlement=_money(balances.get("mentor_pending", 0)),
        monthly_expense=_money(summary.get("monthly_expense_cents", 0)),
        monthly_refund=_money(summary.get("monthly_refund_cents", 0)),
        monthly_income=_money(summary.get("monthly_income_cents", 0)),
        total_income=_money(summary.get("total_income_cents", 0)),
        total_paid=_money(summary.get("total_paid_cents", 0)),
        withdrawal_enabled=bool(real_payment_enabled and settings.wallet_withdrawal_enabled),
        payment_enabled=real_payment_enabled,
        message=message,
        transactions=transactions,
    )


@router.get("/transactions/{transaction_id}", response_model=WalletTransactionItem)
def get_wallet_transaction(
    transaction_id: str,
    role: Literal["user", "mentor"] = Query(default="user"),
    mode: Literal["demo", "real"] | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
) -> WalletTransactionItem:
    fund_mode = _allowed_fund_mode(mode)
    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: (
                supabase.table("wallet_user_activity")
                .select("*")
                .eq("id", transaction_id)
                .eq("user_id", user_id)
                .eq("wallet_role", role)
                .eq("fund_mode", fund_mode)
                .limit(1)
                .execute()
            ),
            operation_name="wallet transaction detail lookup",
        )
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="钱包账本正在初始化，请先执行第二批数据库迁移",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="账单详情暂时不可用，请稍后重试",
        ) from exc
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账单不存在或无权查看")
    return _activity_to_item(response.data[0])
