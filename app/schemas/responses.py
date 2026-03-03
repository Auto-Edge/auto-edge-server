"""
Response Schemas

Pydantic models for API response validation and documentation.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(description="Service health status")
    service: str = Field(description="Service name")


class TaskResponse(BaseModel):
    """Response for task creation (upload/demo)."""

    task_id: str = Field(description="Celery task ID for tracking")
    message: str = Field(description="Human-readable status message")


class DemoResponse(BaseModel):
    """Response for demo conversion request."""

    task_id: str = Field(description="Celery task ID for tracking")
    message: str = Field(description="Human-readable status message")


class ConversionResult(BaseModel):
    """Conversion task result details."""

    status: str = Field(description="Conversion status: success or error")
    model_name: Optional[str] = Field(default=None, description="Name of the model")
    original_size: Optional[str] = Field(default=None, description="Original size in MB")
    optimized_size: Optional[str] = Field(default=None, description="Optimized size in MB")
    reduction: Optional[str] = Field(default=None, description="Size reduction percentage")
    output_file: Optional[str] = Field(default=None, description="Output filename")
    precision: Optional[str] = Field(default=None, description="Model precision")
    target: Optional[str] = Field(default=None, description="Target platform")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class ProgressInfo(BaseModel):
    """Task progress information."""

    stage: str = Field(description="Current processing stage")
    progress: int = Field(description="Progress percentage (0-100)")


class StatusResponse(BaseModel):
    """Response for task status check."""

    task_id: str = Field(description="Celery task ID")
    status: str = Field(description="User-friendly status string")
    result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Task result or progress info",
    )


class ModelsListResponse(BaseModel):
    """Response for listing available models."""

    models: List[str] = Field(description="List of available model filenames")


class ErrorDetail(BaseModel):
    """Error detail structure."""

    code: str = Field(description="Error code")
    message: str = Field(description="Error message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: ErrorDetail = Field(description="Error details")
