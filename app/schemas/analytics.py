"""
Analytics Schemas

Pydantic models for analytics API requests and responses.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


# Request schemas
class AnalyticsEventRequest(BaseModel):
    """Single analytics event."""

    event_type: str = Field(
        ..., min_length=1, max_length=50, description="Event type (e.g., 'inference', 'download', 'error')"
    )
    device_identifier: Optional[str] = Field(
        None, description="Device identifier"
    )
    model_id: Optional[str] = Field(
        None, description="Model ID"
    )
    model_version: Optional[str] = Field(
        None, description="Model version"
    )
    inference_latency_ms: Optional[float] = Field(
        None, ge=0, description="Inference latency in milliseconds"
    )
    memory_usage_bytes: Optional[int] = Field(
        None, ge=0, description="Memory usage in bytes"
    )


class BatchEventsRequest(BaseModel):
    """Request to ingest multiple analytics events."""

    events: List[AnalyticsEventRequest] = Field(
        ..., min_length=1, max_length=1000, description="List of events to ingest"
    )


# Response schemas
class EventResponse(BaseModel):
    """Response for a single event."""

    id: str
    event_type: str
    device_id: Optional[str]
    model_version_id: Optional[str]
    inference_latency_ms: Optional[float]
    memory_usage_bytes: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class BatchEventsResponse(BaseModel):
    """Response for batch event ingestion."""

    ingested_count: int
    events: List[EventResponse]


class InferenceStats(BaseModel):
    """Inference statistics for a model."""

    total_inferences: int
    avg_latency_ms: Optional[float]
    min_latency_ms: Optional[float]
    max_latency_ms: Optional[float]
    avg_memory_bytes: Optional[int]


class ModelMetricsResponse(BaseModel):
    """Response for model metrics."""

    model_id: str
    inference_stats: InferenceStats
    total_downloads: int
    active_devices: int
    versions_published: int


class DashboardSummaryResponse(BaseModel):
    """Response for dashboard summary."""

    total_models: int
    total_versions: int
    total_devices: int
    active_devices_24h: int
    total_inferences: int
    total_downloads: int
    event_counts_by_type: Dict[str, int]
    device_type_distribution: Dict[str, int]


class TimeSeriesDataPoint(BaseModel):
    """A single data point in a time series."""

    timestamp: datetime
    value: float


class TimeSeriesResponse(BaseModel):
    """Response for time series data."""

    metric: str
    data_points: List[TimeSeriesDataPoint]
