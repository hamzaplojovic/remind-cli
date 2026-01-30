"""Backend configuration and environment settings."""

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Backend settings loaded from environment variables."""

    model_config = ConfigDict(
        env_file=".env",
        env_prefix="REMIND_",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from CLI config
    )

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-5-nano"

    # Database
    database_url: str = "sqlite:///./backend.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Rate limiting
    rate_limit_requests: int = 10
    rate_limit_window_seconds: int = 60

    # Paddle payment processing
    paddle_api_key: str | None = None
    paddle_webhook_secret: str | None = None

    # Paddle product ID mapping (from Paddle dashboard)
    paddle_product_indie: str | None = None
    paddle_product_pro: str | None = None
    paddle_product_team: str | None = None

    # Email configuration (for sending license tokens)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None


def get_settings() -> Settings:
    """Get global settings instance."""
    return Settings()
