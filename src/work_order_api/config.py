from functools import lru_cache

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "Work Order Management API"
    environment: str = "development"
    
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()

settings = get_settings()
