"""Configuration management for Mirrarr."""

from functools import lru_cache
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

    # App settings
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
