from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    # Production must only trust the deployed H5 origins. Local development
    # can opt in explicitly through API_CORS_ORIGINS in its local .env file.
    api_cors_origins: str = "https://www.gangyantong.com,https://gangyantong.com"
    smtp_host: str | None = None
    smtp_port: int = 465
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str = "港澳台考研刷题"
    smtp_use_tls: bool = False
    payment_webhook_secret: str | None = None
    mentor_consultation_service_rules_version: str = "2026-08-23"
    mentor_consultation_demo_payment_enabled: bool = False
    mentor_consultation_payment_provider: str = "unconfigured"
    mentor_consultation_payment_checkout_url: str | None = None
    mentor_consultation_lifecycle_interval_seconds: int = 60
    mentor_consultation_report_first_response_hours: int = 48
    mentor_consultation_urgent_report_first_response_hours: int = 12
    mentor_consultation_report_appeal_first_response_hours: int = 48
    mentor_consultation_report_sla_warning_hours: int = 6
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_timeout_seconds: int = 60
    phone_auth_password_secret: str | None = None
    sms_provider: str = "disabled"
    sms_mock_return_code: bool = False
    tencent_sms_secret_id: str | None = None
    tencent_sms_secret_key: str | None = None
    tencent_sms_sdk_app_id: str | None = None
    tencent_sms_sign_name: str | None = None
    tencent_sms_template_id: str | None = None
    tencent_sms_template_params: str = "code"
    tencent_sms_region: str = "ap-guangzhou"
    tencent_sms_endpoint: str = "sms.tencentcloudapi.com"
    tencent_ocr_secret_id: str | None = None
    tencent_ocr_secret_key: str | None = None
    tencent_ocr_region: str = "ap-guangzhou"
    tencent_ocr_endpoint: str = "ocr.tencentcloudapi.com"
    tencent_ocr_timeout_seconds: int = 30
    wechat_oauth_app_id: str | None = None
    wechat_oauth_app_secret: str | None = None
    wechat_oauth_scope: str = "snsapi_userinfo"
    wechat_miniprogram_app_id: str | None = None
    wechat_miniprogram_app_secret: str | None = None
    wechat_auth_password_secret: str | None = None
    # Retained only so older server env files remain parseable. Administrator
    # access is derived from public.users.role, never from an email allowlist.
    admin_emails: str = ""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins(self) -> list[str]:
        if self.api_cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]

    @property
    def smtp_enabled(self) -> bool:
        return bool(
            self.smtp_host and self.smtp_username and self.smtp_password and self.smtp_from_email
        )

@lru_cache
def get_settings() -> Settings:
    return Settings()
