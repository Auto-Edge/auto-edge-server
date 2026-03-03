"""
Worker Tasks

Celery task definitions.
"""

from worker.tasks.conversion_task import convert_model

__all__ = ["convert_model"]
