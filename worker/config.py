"""
Worker Configuration

Celery and conversion settings for the worker.
"""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WorkerConfig:
    """Worker configuration loaded from environment."""

    broker_url: str
    result_backend: str
    shared_data_path: Path
    task_timeout: int  # seconds
    max_retries: int
    retry_backoff: int  # seconds

    @classmethod
    def from_env(cls) -> "WorkerConfig":
        """Load configuration from environment variables."""
        return cls(
            broker_url=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
            result_backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
            shared_data_path=Path(os.getenv("SHARED_DATA_PATH", "./shared_data")),
            task_timeout=int(os.getenv("TASK_TIMEOUT", "600")),  # 10 minutes
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            retry_backoff=int(os.getenv("RETRY_BACKOFF", "60")),  # 1 minute
        )


# Global config instance
config = WorkerConfig.from_env()
