from pydantic import BaseModel, Field


class MembershipStatusResponse(BaseModel):
    user_id: str
    membership_status: str = "inactive"
    membership_plan: str | None = None
    membership_started_at: str | None = None
    membership_expires_at: str | None = None
    membership_updated_at: str | None = None
    membership_active: bool = False


class MembershipPlan(BaseModel):
    code: str
    name: str
    price_cents: int
    price_label: str
    duration_days: int
    description: str


class MembershipSubscriptionPageConfigPayload(BaseModel):
    title: str = Field(min_length=1, max_length=30)
    brand_name: str = Field(min_length=1, max_length=50)
    benefits: list[str] = Field(min_length=1, max_length=8)
    monthly_price_cents: int = Field(ge=1, le=1_000_000)
    quarterly_price_cents: int = Field(ge=1, le=1_000_000)
    plan_hint: str = Field(min_length=1, max_length=80)
    primary_button_text: str = Field(min_length=1, max_length=30)
    secondary_button_text: str = Field(min_length=1, max_length=30)
    description_text: str = Field(min_length=1, max_length=180)
    terms_text: str = Field(min_length=1, max_length=60)


class MembershipSubscriptionPageConfig(MembershipSubscriptionPageConfigPayload):
    updated_at: str | None = None


class CreateMembershipOrderRequest(BaseModel):
    plan_code: str


class MembershipOrderResponse(BaseModel):
    order_id: str
    provider: str
    provider_order_id: str
    plan_code: str
    amount_cents: int
    currency: str = "CNY"
    status: str
    checkout_url: str | None = None
    message: str


class PaymentWebhookRequest(BaseModel):
    provider: str
    provider_order_id: str
    status: str
    raw_payload: dict | None = None


class PaymentWebhookResponse(BaseModel):
    detail: str
    membership_active: bool = False
