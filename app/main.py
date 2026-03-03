"""
AutoEdge Application Factory

Creates and configures the FastAPI application.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import get_settings
from app.core.error_handlers import register_exception_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Initialize database tables
    from app.models.base import init_db
    await init_db()
    logger.info("Database initialized")

    yield
    logger.info("Shutting down application")


def create_app() -> FastAPI:
    """
    Application factory for creating FastAPI instance.

    Returns:
        Configured FastAPI application.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="MLOps pipeline for PyTorch to CoreML conversion",
        version=settings.app_version,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Include API router
    app.include_router(api_router)

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(app, host=settings.host, port=settings.port)
