"""Configuration management for Remind."""

import os
from pathlib import Path
from typing import Optional

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from remind.models import Config as ConfigModel


class Settings(BaseSettings):
    """Application settings loaded from environment and config file."""

    timezone: str = "UTC"
    scheduler_interval_minutes: int = 1
    notifications_enabled: bool = True
    notification_sound_enabled: bool = True
    ai_rephrasing_enabled: bool = True
    openai_api_key: Optional[str] = None
    nudge_intervals_minutes: str = "5,15,60"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="REMIND_",
    )


def get_app_dir() -> Path:
    """Get the application directory, creating it if necessary."""
    app_dir = Path.home() / ".remind"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_db_path() -> Path:
    """Get the database path."""
    return get_app_dir() / "reminders.db"


def get_license_path() -> Path:
    """Get the license token file path."""
    return get_app_dir() / "license.json"


def get_config_path() -> Path:
    """Get the config file path."""
    return get_app_dir() / "config.toml"


def load_config() -> ConfigModel:
    """Load user configuration from config file and environment."""
    settings = Settings()

    # Try to load from TOML config file
    config_path = get_config_path()
    if config_path.exists():
        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib  # type: ignore

        try:
            with open(config_path, "rb") as f:
                data = tomllib.load(f)
                config_data = data.get("remind", {})
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            config_data = {}
    else:
        config_data = {}

    # Override with environment variables
    if settings.timezone != "UTC":
        config_data["timezone"] = settings.timezone
    if settings.scheduler_interval_minutes != 1:
        config_data["scheduler_interval_minutes"] = settings.scheduler_interval_minutes
    if not settings.notifications_enabled:
        config_data["notifications_enabled"] = False
    if not settings.notification_sound_enabled:
        config_data["notification_sound_enabled"] = False
    if not settings.ai_rephrasing_enabled:
        config_data["ai_rephrasing_enabled"] = False
    if settings.openai_api_key:
        config_data["openai_api_key"] = settings.openai_api_key

    # Parse nudge intervals
    if "nudge_intervals_minutes" not in config_data:
        nudge_str = settings.nudge_intervals_minutes
        config_data["nudge_intervals_minutes"] = [
            int(x.strip()) for x in nudge_str.split(",")
        ]

    try:
        return ConfigModel(**config_data)
    except ValidationError as e:
        print(f"Warning: Invalid config, using defaults: {e}")
        return ConfigModel()


def save_config(config: ConfigModel) -> None:
    """Save configuration to TOML file."""
    config_path = get_config_path()
    try:
        import tomllib
        import toml  # type: ignore
    except ModuleNotFoundError:
        try:
            import tomli as tomllib  # type: ignore
            import tomli_w as toml  # type: ignore
        except ModuleNotFoundError:
            print("Warning: toml libraries not available, skipping config save")
            return

    data = {"remind": config.model_dump()}
    with open(config_path, "w") as f:
        toml.dump(data, f)
