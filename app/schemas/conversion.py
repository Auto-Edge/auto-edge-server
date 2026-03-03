"""
Conversion Schemas

Pydantic models for conversion API requests and responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ConversionResponse(BaseModel):
    """Response for a conversion job."""

    id: str
    task_id: str
    status: str
    input_filename: Optional[str]
    is_demo: bool

    # Result fields (populated on completion)
    output_file: Optional[str]
    model_name: Optional[str]
    original_size: Optional[str]
    optimized_size: Optional[str]
    reduction: Optional[str]
    precision: Optional[str]

    # Error
    error_message: Optional[str]

    # Timestamps
    created_at: datetime
    completed_at: Optional[datetime]

    # Linked model
    registered_model_id: Optional[str]

    class Config:
        from_attributes = True


class ConversionListResponse(BaseModel):
    """Response for listing conversions."""

    conversions: list[ConversionResponse]
    total: int


class StartConversionResponse(BaseModel):
    """Response for starting a conversion."""

    conversion_id: str
    task_id: str
    message: str
