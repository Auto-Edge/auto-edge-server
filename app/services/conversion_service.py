"""
Conversion Service

Orchestrates model conversion tasks and status tracking.
"""

import logging
from typing import Any, Dict, Optional

from celery.result import AsyncResult

logger = logging.getLogger(__name__)


class ConversionService:
    """Service for managing model conversion tasks."""

    # Map Celery states to user-friendly statuses
    STATUS_MAP = {
        "PENDING": "Pending",
        "STARTED": "Processing",
        "PROGRESS": "Processing",
        "SUCCESS": "Completed",
        "FAILURE": "Failed",
        "REVOKED": "Cancelled",
    }

    def __init__(self, celery_app):
        """
        Initialize conversion service.

        Args:
            celery_app: Celery application instance.
        """
        self.celery_app = celery_app

    def start_conversion(self, file_path: Optional[str] = None) -> str:
        """
        Start a model conversion task.

        Args:
            file_path: Path to the model file, or None for demo mode.

        Returns:
            Task ID for tracking.
        """
        from worker.tasks.conversion_task import convert_model

        task = convert_model.delay(file_path)
        logger.info(f"Conversion task started: {task.id}")
        return task.id

    def start_demo_conversion(self) -> str:
        """
        Start a demo conversion using MobileNetV2.

        Returns:
            Task ID for tracking.
        """
        logger.info("Demo conversion requested - using MobileNetV2")
        return self.start_conversion(file_path=None)

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a conversion task.

        Args:
            task_id: The Celery task ID.

        Returns:
            Dictionary with task_id, status, and result.
        """
        logger.info(f"Status check for task: {task_id}")

        task_result = AsyncResult(task_id, app=self.celery_app)
        status = self.STATUS_MAP.get(task_result.state, task_result.state)

        response = {
            "task_id": task_id,
            "status": status,
            "result": None,
        }

        if task_result.state == "SUCCESS":
            response["result"] = task_result.result
        elif task_result.state == "FAILURE":
            response["result"] = {"error": str(task_result.result)}
        elif task_result.state == "PROGRESS":
            response["result"] = task_result.info

        logger.info(f"Task {task_id} status: {status}")
        return response
