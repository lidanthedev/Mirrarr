"""Configuration management for Mirrarr."""

from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # TMDB
    tmdb_api_key: str

    # Database
    database_url: str = "sqlite:///./mirrarr.db"

    # Redis (for Celery)
    redis_url: str = "redis://localhost:6379/0"

    # Provider settings
    provider_timeout: int = 60  # Timeout for provider searches in seconds
    preferred_provider: str | None = None  # Provider to prioritize in AUTO selection
    quality_limit: Literal["2160p", "1080p", "720p", "480p", "360p", "240p"] = "2160p"  # Maximum quality to consider in AUTO selection

    # Authentication (leave empty to disable)
    auth_username: str = ""
    auth_password: str = ""

    # App settings
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
