"""
Model Conversion Task

Celery task for converting PyTorch models to CoreML.
Includes retry logic and progress tracking.
"""

import logging
from typing import Any, Dict, Optional

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

from worker.celery_app import celery_app
from worker.config import config
from worker.converters.coreml_converter import CoreMLConverter
from worker.converters.pytorch_loader import PyTorchLoader

logger = logging.getLogger(__name__)


class ConversionTask(Task):
    """Custom task class with error handling."""

    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 300  # 5 minutes max
    retry_jitter = True
    max_retries = config.max_retries

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails after all retries."""
        logger.error(f"Task {task_id} failed permanently: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning(f"Task {task_id} retrying due to: {exc}")
        super().on_retry(exc, task_id, args, kwargs, einfo)


@celery_app.task(
    bind=True,
    base=ConversionTask,
    name="convert_model",
    acks_late=True,
    reject_on_worker_lost=True,
)
def convert_model(self, file_path: Optional[str]) -> Dict[str, Any]:
    """
    Convert a PyTorch model to CoreML.

    This task:
    1. Loads the PyTorch model (or uses MobileNetV2 fallback)
    2. Traces the model for conversion
    3. Converts to CoreML with FLOAT16 quantization
    4. Calculates size reduction metrics

    Args:
        file_path: Path to the PyTorch model file, or None for demo mode.

    Returns:
        Dictionary with conversion results and metrics.
    """
    task_id = self.request.id
    logger.info(f"Task {task_id}: Starting model conversion")

    loader = PyTorchLoader(config.shared_data_path)
    converter = CoreMLConverter(config.shared_data_path)

    try:
        # Stage 1: Load the model
        self.update_state(
            state="PROGRESS",
            meta={"stage": "Loading model", "progress": 10},
        )

        model, model_name, original_path = loader.load_model(file_path)
        original_size = loader.get_file_size_mb(original_path)
        logger.info(f"Task {task_id}: Original model size: {original_size} MB")

        # Stage 2: Trace the model
        self.update_state(
            state="PROGRESS",
            meta={"stage": "Tracing model", "progress": 30},
        )

        traced_model = loader.trace_model(model)
        logger.info(f"Task {task_id}: Model traced successfully")

        # Stage 3: Convert to CoreML
        self.update_state(
            state="PROGRESS",
            meta={"stage": "Converting to CoreML", "progress": 50},
        )

        output_path = converter.convert(traced_model, model_name)
        optimized_size = loader.get_file_size_mb(output_path)
        logger.info(f"Task {task_id}: Optimized model size: {optimized_size} MB")

        # Stage 4: Calculate metrics
        self.update_state(
            state="PROGRESS",
            meta={"stage": "Finalizing", "progress": 90},
        )

        if original_size > 0:
            reduction = round((1 - (optimized_size / original_size)) * 100, 1)
        else:
            reduction = 0.0

        result = {
            "status": "success",
            "model_name": model_name,
            "original_size": f"{original_size} MB",
            "optimized_size": f"{optimized_size} MB",
            "reduction": f"{reduction}%",
            "output_file": f"{model_name}.mlmodel",
            "precision": "FLOAT16",
            "target": "iOS12+",
        }

        logger.info(f"Task {task_id}: Conversion completed - {result}")
        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {task_id}: Soft time limit exceeded")
        return {
            "status": "error",
            "error": "Conversion timed out. The model may be too large.",
        }

    except Exception as e:
        logger.error(f"Task {task_id}: Conversion failed - {e}")

        # Let autoretry handle retryable errors
        if self.request.retries < self.max_retries:
            raise

        return {
            "status": "error",
            "error": str(e),
        }
