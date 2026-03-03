"""
Health Check Endpoint

Provides service health status.
"""

from fastapi import APIRouter

from app.schemas.responses import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns service health status for load balancers and monitoring.
    """
    return HealthResponse(
        status="healthy",
        service="autoedge-backend",
    )
