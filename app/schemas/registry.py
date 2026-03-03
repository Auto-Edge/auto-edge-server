"""
Registry Schemas

Pydantic models for model registry API requests and responses.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# Request schemas
class CreateModelRequest(BaseModel):
    """Request to create a new model."""

    name: str = Field(..., min_length=1, max_length=255, description="Model name")
    description: Optional[str] = Field(None, description="Model description")


class UpdateModelRequest(BaseModel):
    """Request to update a model."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="New model name")
    description: Optional[str] = Field(None, description="New model description")


class CreateVersionRequest(BaseModel):
    """Request to create a new version."""

    version: str = Field(..., min_length=1, max_length=50, description="Version string (e.g., '1.0.0')")
    file_path: str = Field(..., description="Path to the model file")
    file_size_bytes: Optional[int] = Field(None, ge=0, description="File size in bytes")
    file_hash: Optional[str] = Field(None, max_length=64, description="SHA256 hash of the file")
    precision: str = Field("FLOAT16", description="Model precision (FLOAT16, FLOAT32, INT8)")


class PublishVersionRequest(BaseModel):
    """Request to publish/unpublish a version."""

    is_published: bool = Field(..., description="Whether to publish the version")


# Response schemas
class ModelVersionResponse(BaseModel):
    """Response for a model version."""

    id: str
    model_id: str
    version: str
    file_path: str
    file_size_bytes: Optional[int]
    file_hash: Optional[str]
    precision: str
    created_at: datetime
    is_published: bool
    download_count: int

    class Config:
        from_attributes = True


class ModelResponse(BaseModel):
    """Response for a model."""

    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    is_active: bool
    versions: List[ModelVersionResponse] = []

    class Config:
        from_attributes = True


class ModelListResponse(BaseModel):
    """Response for listing models."""

    models: List[ModelResponse]
    total: int


class ModelSummaryResponse(BaseModel):
    """Summary response for a model (without versions)."""

    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    is_active: bool
    version_count: int
    latest_version: Optional[str]

    class Config:
        from_attributes = True
