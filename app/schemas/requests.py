"""
Request Schemas

Pydantic models for API request validation.
"""

from typing import Optional

from pydantic import BaseModel, Field


class UploadRequest(BaseModel):
    """Model for file upload metadata (file handled separately by FastAPI)."""

    filename: Optional[str] = Field(
        default=None,
        description="Original filename of the uploaded model",
    )


class ConversionRequest(BaseModel):
    """Model for conversion task parameters."""

    file_path: Optional[str] = Field(
        default=None,
        description="Path to the model file, or None for demo mode",
    )
