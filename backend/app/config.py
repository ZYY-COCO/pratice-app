from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    api_cors_origins: str = "*"
    smtp_host: str | None = None
    smtp_port: int = 465
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str = "港澳台考研刷题"
    smtp_use_tls: bool = False
    payment_webhook_secret: str | None = None
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
    wechat_oauth_app_id: str | None = None
    wechat_oauth_app_secret: str | None = None
    wechat_oauth_scope: str = "snsapi_userinfo"
    wechat_auth_password_secret: str | None = None

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
