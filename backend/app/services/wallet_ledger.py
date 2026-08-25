from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config import get_settings
from app.db import get_supabase_admin
from app.services.supabase_resilience import call_supabase, is_missing_supabase_relation_error


logger = logging.getLogger(__name__)


def consultation_fund_mode(order: dict) -> str:
    mode = str(order.get("payment_mode") or "").strip().lower()
    if mode in {"demo", "real"}:
        return mode
    reference = str(order.get("payment_reference") or "").upper()
    return "demo" if reference.startswith(("DEMO-", "MOCK-")) else "real"


def _transaction_no(event_key: str) -> str:
    digest = hashlib.sha256(event_key.encode("utf-8")).hexdigest()[:24].upper()
    return f"WTX-{digest}"


def _mentor_details(supabase: Any, mentor_id: str) -> dict[str, Any]:
    if not mentor_id:
        return {}
    response = call_supabase(
        lambda: (
            supabase.table("mentor_profiles")
            .select("owner_user_id,display_name,school,major")
            .eq("id", mentor_id)
            .limit(1)
            .execute()
        ),
        operation_name="wallet mentor owner lookup",
    )
    return (response.data or [{}])[0]


def _base_metadata(supabase: Any, order: dict) -> dict[str, Any]:
    mentor = _mentor_details(supabase, str(order.get("mentor_id") or ""))
    return {
        "order_id": str(order.get("id") or ""),
        "order_no": str(order.get("order_no") or ""),
        "applicant_user_id": str(order.get("applicant_user_id") or ""),
        "mentor_id": str(order.get("mentor_id") or ""),
        "mentor_owner_user_id": str(mentor.get("owner_user_id") or ""),
        "mentor_display_name": str(mentor.get("display_name") or ""),
        "mentor_school": str(mentor.get("school") or ""),
        "mentor_major": str(mentor.get("major") or ""),
        "consultation_type": str(order.get("consultation_type") or "instant"),
    }


def _post_wallet_transaction(
    supabase: Any,
    *,
    event_key: str,
    business_type: str,
    order: dict,
    description: str,
    metadata: dict[str, Any],
    entries: list[dict[str, Any]],
    occurred_at: str | None = None,
) -> bool:
    amount_cents = max(0, int(order.get("price_cents") or 0))
    if not event_key or amount_cents <= 0:
        return False
    try:
        if _wallet_event_exists(supabase, event_key):
            return False
    except Exception:
        pass
    try:
        response = call_supabase(
            lambda: supabase.rpc(
                "post_wallet_transaction",
                {
                    "p_transaction_no": _transaction_no(event_key),
                    "p_event_key": event_key,
                    "p_business_type": business_type,
                    "p_business_id": str(order.get("id") or ""),
                    "p_fund_mode": consultation_fund_mode(order),
                    "p_gross_amount_cents": amount_cents,
                    "p_description": description,
                    "p_metadata": metadata,
                    "p_entries": entries,
                    "p_occurred_at": occurred_at or datetime.now(timezone.utc).isoformat(),
                },
            ).execute(),
            operation_name=f"wallet ledger post {business_type}",
        )
        return bool(response.data)
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            return False
        logger.warning(
            "Wallet ledger post deferred (business_type=%s order_id=%s error_type=%s)",
            business_type,
            str(order.get("id") or ""),
            type(exc).__name__,
        )
        return False


def record_consultation_payment(supabase: Any, order: dict) -> bool:
    if str(order.get("payment_status") or "") != "paid":
        return False
    mode = consultation_fund_mode(order)
    order_id = str(order.get("id") or "")
    amount_cents = max(0, int(order.get("price_cents") or 0))
    metadata = _base_metadata(supabase, order)
    metadata["payment_reference"] = str(order.get("payment_reference") or "")
    return _post_wallet_transaction(
        supabase,
        event_key=f"consultation-payment:{order_id}",
        business_type="consultation_payment",
        order=order,
        description="咨询订单支付确认",
        metadata=metadata,
        occurred_at=str(order.get("updated_at") or "") or None,
        entries=[
            {
                "account_code": f"platform:cash:{mode}",
                "owner_user_id": None,
                "account_type": "platform_cash",
                "balance_class": "asset",
                "direction": "debit",
                "amount_cents": amount_cents,
            },
            {
                "account_code": f"consultation:{order_id}:escrow:{mode}",
                "owner_user_id": None,
                "account_type": "consultation_escrow",
                "balance_class": "liability",
                "direction": "credit",
                "amount_cents": amount_cents,
            },
        ],
    )


def record_consultation_income_pending(supabase: Any, order: dict) -> bool:
    if str(order.get("order_status") or "") != "completed" or str(order.get("payment_status") or "") != "paid":
        return False
    metadata = _base_metadata(supabase, order)
    mentor_owner_user_id = str(metadata.get("mentor_owner_user_id") or "")
    if not mentor_owner_user_id:
        return False
    mode = consultation_fund_mode(order)
    order_id = str(order.get("id") or "")
    amount_cents = max(0, int(order.get("price_cents") or 0))
    return _post_wallet_transaction(
        supabase,
        event_key=f"consultation-income-pending:{order_id}",
        business_type="consultation_income_pending",
        order=order,
        description="咨询完成，收入进入待结算",
        metadata=metadata,
        occurred_at=str(order.get("ended_at") or order.get("updated_at") or "") or None,
        entries=[
            {
                "account_code": f"consultation:{order_id}:escrow:{mode}",
                "owner_user_id": None,
                "account_type": "consultation_escrow",
                "balance_class": "liability",
                "direction": "debit",
                "amount_cents": amount_cents,
            },
            {
                "account_code": f"user:{mentor_owner_user_id}:mentor-pending:{mode}",
                "owner_user_id": mentor_owner_user_id,
                "account_type": "mentor_pending",
                "balance_class": "liability",
                "direction": "credit",
                "amount_cents": amount_cents,
            },
        ],
    )


def record_consultation_income_settled(supabase: Any, order: dict) -> bool:
    metadata = _base_metadata(supabase, order)
    mentor_owner_user_id = str(metadata.get("mentor_owner_user_id") or "")
    if not mentor_owner_user_id:
        return False
    mode = consultation_fund_mode(order)
    order_id = str(order.get("id") or "")
    amount_cents = max(0, int(order.get("price_cents") or 0))
    return _post_wallet_transaction(
        supabase,
        event_key=f"consultation-income-settled:{order_id}",
        business_type="consultation_income_settled",
        order=order,
        description="咨询收入结算为可提现余额",
        metadata=metadata,
        entries=[
            {
                "account_code": f"user:{mentor_owner_user_id}:mentor-pending:{mode}",
                "owner_user_id": mentor_owner_user_id,
                "account_type": "mentor_pending",
                "balance_class": "liability",
                "direction": "debit",
                "amount_cents": amount_cents,
            },
            {
                "account_code": f"user:{mentor_owner_user_id}:mentor-available:{mode}",
                "owner_user_id": mentor_owner_user_id,
                "account_type": "mentor_available",
                "balance_class": "liability",
                "direction": "credit",
                "amount_cents": amount_cents,
            },
        ],
    )


def _wallet_event_exists(supabase: Any, event_key: str) -> bool:
    try:
        response = call_supabase(
            lambda: (
                supabase.table("wallet_transactions")
                .select("id")
                .eq("event_key", event_key)
                .limit(1)
                .execute()
            ),
            operation_name="wallet event lookup",
        )
        return bool(response.data)
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            return False
        raise


def record_consultation_refund(supabase: Any, order: dict) -> bool:
    if str(order.get("payment_status") or "") != "refunded":
        return False
    order_id = str(order.get("id") or "")
    metadata = _base_metadata(supabase, order)
    metadata["refund_reference"] = str(order.get("refund_reference") or "")
    mentor_owner_user_id = str(metadata.get("mentor_owner_user_id") or "")
    mode = consultation_fund_mode(order)
    amount_cents = max(0, int(order.get("refund_amount_cents") or order.get("price_cents") or 0))
    ledger_order = {**order, "price_cents": amount_cents}

    settled = _wallet_event_exists(supabase, f"consultation-income-settled:{order_id}")
    income_created = _wallet_event_exists(supabase, f"consultation-income-pending:{order_id}")
    if mentor_owner_user_id and (settled or income_created):
        source_type = "mentor_available" if settled else "mentor_pending"
        source_suffix = "mentor-available" if settled else "mentor-pending"
        debit_account = {
            "account_code": f"user:{mentor_owner_user_id}:{source_suffix}:{mode}",
            "owner_user_id": mentor_owner_user_id,
            "account_type": source_type,
            "balance_class": "liability",
            "direction": "debit",
            "amount_cents": amount_cents,
        }
    else:
        debit_account = {
            "account_code": f"consultation:{order_id}:escrow:{mode}",
            "owner_user_id": None,
            "account_type": "consultation_escrow",
            "balance_class": "liability",
            "direction": "debit",
            "amount_cents": amount_cents,
        }

    business_type = "consultation_income_reversed" if income_created else "consultation_refund"
    return _post_wallet_transaction(
        supabase,
        event_key=f"consultation-refund:{order_id}:{str(order.get('refund_reference') or 'confirmed')}",
        business_type=business_type,
        order=ledger_order,
        description="咨询订单退款确认",
        metadata=metadata,
        occurred_at=str(order.get("updated_at") or "") or None,
        entries=[
            debit_account,
            {
                "account_code": f"platform:cash:{mode}",
                "owner_user_id": None,
                "account_type": "platform_cash",
                "balance_class": "asset",
                "direction": "credit",
                "amount_cents": amount_cents,
            },
        ],
    )


def reconcile_consultation_wallet_ledger(*, limit: int = 200) -> int:
    """Idempotently rebuild missing ledger events from consultation source rows."""

    client = get_supabase_admin()
    batch_size = max(1, min(int(limit or 200), 500))
    changed = 0
    try:
        paid_response = call_supabase(
            lambda: (
                client.table("mentor_consultation_orders")
                .select("*")
                .eq("payment_status", "paid")
                .order("updated_at", desc=True)
                .limit(batch_size)
                .execute()
            ),
            operation_name="wallet paid order reconciliation list",
        )
        settlement_days = max(0, min(int(get_settings().wallet_settlement_days or 3), 30))
        settlement_cutoff = datetime.now(timezone.utc) - timedelta(days=settlement_days)
        for order in paid_response.data or []:
            changed += int(record_consultation_payment(client, order))
            if str(order.get("order_status") or "") != "completed":
                continue
            changed += int(record_consultation_income_pending(client, order))
            ended_at = _as_utc_datetime(order.get("ended_at"))
            if ended_at is not None and ended_at <= settlement_cutoff:
                changed += int(record_consultation_income_settled(client, order))

        refunded_response = call_supabase(
            lambda: (
                client.table("mentor_consultation_orders")
                .select("*")
                .eq("payment_status", "refunded")
                .order("updated_at", desc=True)
                .limit(batch_size)
                .execute()
            ),
            operation_name="wallet refunded order reconciliation list",
        )
        for order in refunded_response.data or []:
            changed += int(record_consultation_refund(client, order))
    except Exception as exc:
        if is_missing_supabase_relation_error(exc):
            return 0
        logger.warning("Wallet ledger reconciliation deferred (error_type=%s)", type(exc).__name__)
    return changed


def _as_utc_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
