"""
Celery Application Configuration

Creates and configures the Celery application instance.
"""

from celery import Celery

from worker.config import config

# Create Celery app
celery_app = Celery(
    "autoedge",
    broker=config.broker_url,
    backend=config.result_backend,
)

# Configure Celery
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Time settings
    timezone="UTC",
    enable_utc=True,

    # Task settings
    task_track_started=True,
    task_acks_late=True,
    task_time_limit=config.task_timeout,
    task_soft_time_limit=config.task_timeout - 30,  # 30 seconds before hard limit

    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time

    # Retry settings (global defaults)
    task_default_retry_delay=config.retry_backoff,

    # Result settings
    result_expires=3600,  # 1 hour
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["worker.tasks"])
