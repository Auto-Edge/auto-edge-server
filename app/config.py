"""
Application Configuration

Pydantic Settings for environment-based configuration with validation.
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "AutoEdge API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # Storage
    shared_data_path: Path = Path("./shared_data")

    # Database
    database_url: str = "sqlite+aiosqlite:///./shared_data/autoedge.db"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # File validation
    allowed_extensions: List[str] = [".pt", ".pth"]
    max_file_size_mb: int = 500

    def ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.shared_data_path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.ensure_directories()
    return settings
