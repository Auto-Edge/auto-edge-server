"""
Analytics API Endpoints

Analytics endpoints for ingesting events and retrieving metrics.
"""

from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    get_db_session,
    get_analytics_repo,
    get_device_repo,
    get_model_registry_repo,
)
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    BatchEventsRequest,
    BatchEventsResponse,
    EventResponse,
    ModelMetricsResponse,
    DashboardSummaryResponse,
)

router = APIRouter(prefix="/api/v1/analytics")


async def get_analytics_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AnalyticsService:
    """Get analytics service dependency."""
    analytics_repo = await get_analytics_repo(session)
    device_repo = await get_device_repo(session)
    model_repo = await get_model_registry_repo(session)

    return AnalyticsService(
        analytics_repo=analytics_repo,
        device_repo=device_repo,
        model_repo=model_repo,
    )


@router.post(
    "/events",
    response_model=BatchEventsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest analytics events",
)
async def ingest_events(
    request: BatchEventsRequest,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
):
    """
    Ingest a batch of analytics events.

    Events can include:
    - **inference**: Model inference event with latency and memory usage
    - **download**: Model download event
    - **error**: Error event

    Returns the ingested events with assigned IDs.
    """
    events = await service.ingest_events(request.events)
    return BatchEventsResponse(
        ingested_count=len(events),
        events=[EventResponse.model_validate(e) for e in events],
    )


@router.get(
    "/models/{model_id}/metrics",
    response_model=ModelMetricsResponse,
    summary="Get model metrics",
)
async def get_model_metrics(
    model_id: str,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    since: Optional[datetime] = Query(
        None, description="Start time for metrics (ISO format)"
    ),
):
    """
    Get analytics metrics for a specific model.

    Returns:
    - Inference statistics (count, latency, memory)
    - Total downloads
    - Active devices using the model
    - Published versions count
    """
    return await service.get_model_metrics(model_id, since)


@router.get(
    "/dashboard",
    response_model=DashboardSummaryResponse,
    summary="Get dashboard summary",
)
async def get_dashboard_summary(
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
):
    """
    Get summary statistics for the analytics dashboard.

    Returns:
    - Total models, versions, and devices
    - Active devices in last 24 hours
    - Total inferences and downloads
    - Event counts by type
    - Device type distribution
    """
    return await service.get_dashboard_summary()
