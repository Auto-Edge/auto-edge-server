"""
Router Aggregator

Combines all API routers into a single router.
"""

from fastapi import APIRouter

from app.api.v1 import conversion, health, models, registry, ota, analytics

api_router = APIRouter()

# Include all v1 routers
api_router.include_router(
    health.router,
    tags=["Health"],
)

api_router.include_router(
    conversion.router,
    tags=["Conversion"],
)

api_router.include_router(
    models.router,
    tags=["Models"],
)

api_router.include_router(
    registry.router,
    tags=["Registry"],
)

api_router.include_router(
    ota.router,
    tags=["OTA"],
)

api_router.include_router(
    analytics.router,
    tags=["Analytics"],
)
