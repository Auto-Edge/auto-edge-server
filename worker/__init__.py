"""
Worker Package

Celery worker for PyTorch to CoreML model conversion.
"""

from worker.celery_app import celery_app

__all__ = ["celery_app"]
