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
