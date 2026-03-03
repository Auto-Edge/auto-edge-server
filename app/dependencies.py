"""
Dependency Injection

FastAPI dependency providers for services and repositories.
"""

from functools import lru_cache
from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.models.base import get_session_factory
from app.repositories.filesystem_repo import FileSystemRepository
from app.repositories.sqlite import (
    SQLiteModelRegistryRepository,
    SQLiteDeviceRepository,
    SQLiteAnalyticsRepository,
    SQLiteConversionRepository,
)
from app.services.conversion_service import ConversionService
from app.services.file_service import FileService


@lru_cache
def get_repository() -> FileSystemRepository:
    """Get cached repository instance."""
    settings = get_settings()
    return FileSystemRepository(base_path=settings.shared_data_path)


@lru_cache
def get_file_service() -> FileService:
    """Get cached file service instance."""
    settings = get_settings()
    return FileService(
        repository=get_repository(),
        allowed_extensions=settings.allowed_extensions,
        max_file_size_mb=settings.max_file_size_mb,
    )


@lru_cache
def get_conversion_service() -> ConversionService:
    """Get cached conversion service instance."""
    from worker.celery_app import celery_app

    return ConversionService(celery_app=celery_app)


def get_settings_dep() -> Settings:
    """Dependency for settings (non-cached for testing)."""
    return get_settings()


# Database session dependency
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session for request."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Repository dependencies that use the session
async def get_model_registry_repo(
    session: AsyncSession,
) -> SQLiteModelRegistryRepository:
    """Get model registry repository."""
    return SQLiteModelRegistryRepository(session)


async def get_device_repo(
    session: AsyncSession,
) -> SQLiteDeviceRepository:
    """Get device repository."""
    return SQLiteDeviceRepository(session)


async def get_analytics_repo(
    session: AsyncSession,
) -> SQLiteAnalyticsRepository:
    """Get analytics repository."""
    return SQLiteAnalyticsRepository(session)


async def get_conversion_repo(
    session: AsyncSession,
) -> SQLiteConversionRepository:
    """Get conversion repository."""
    return SQLiteConversionRepository(session)
