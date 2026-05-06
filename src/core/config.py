from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Shifrator VPN Bot"
    debug: bool = False

    bot_token: SecretStr | None = None
    webhook_base_url: str | None = None
    telegram_webhook_secret: str = "change-me"

    xray_gateway: str = "fake"
    xray_api_address: str = "127.0.0.1:10085"
    xray_default_inbound_tag: str = "vless-reality"

    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "shifrator"
    postgres_user: str = "shifrator"
    postgres_password: str = "shifrator"
    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return self.database_url

        return (
            "postgresql+asyncpg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def telegram_webhook_path(self) -> str:
        return f"/webhooks/telegram/{self.telegram_webhook_secret}"

    @property
    def telegram_webhook_url(self) -> str | None:
        if not self.webhook_base_url:
            return None
        return f"{self.webhook_base_url.rstrip('/')}{self.telegram_webhook_path}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
