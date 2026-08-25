from typing import Any, Literal

from pydantic import BaseModel, Field


class WalletTransactionItem(BaseModel):
    id: str
    transaction_no: str
    fund_mode: Literal["demo", "real"] = "real"
    type: str
    title: str
    description: str = ""
    amount: float | int
    status: str
    month_key: str
    created_at: str | None = None
    completed_at: str | None = None
    order_id: str | None = None
    counterparty: str | None = None
    mentor: str | None = None
    settlement_status: str | None = None
    available_at: str | None = None
    payment_method: str | None = None
    note: str | None = None
    icon_label: str = "账"
    icon_tone: str = "blue"
    metadata: dict[str, Any] = Field(default_factory=dict)


class WalletSummaryResponse(BaseModel):
    role: Literal["user", "mentor"]
    fund_mode: Literal["demo", "real"]
    currency: str = "CNY"
    balance: float | int = 0
    withdrawable_balance: float | int = 0
    pending_settlement: float | int = 0
    monthly_expense: float | int = 0
    monthly_refund: float | int = 0
    monthly_income: float | int = 0
    total_income: float | int = 0
    total_paid: float | int = 0
    withdrawal_enabled: bool = False
    payment_enabled: bool = False
    message: str
    transactions: list[WalletTransactionItem] = Field(default_factory=list)
