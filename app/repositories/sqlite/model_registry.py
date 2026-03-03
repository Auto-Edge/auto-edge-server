"""
SQLite Model Registry Repository

SQLite implementation of the model registry repository.
"""

import logging
from typing import List, Optional

from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.models.model import Model, ModelVersion
from app.repositories.model_registry_repo import ModelRegistryRepository
from app.repositories.sqlite.base import SQLiteRepositoryBase

logger = logging.getLogger(__name__)


class SQLiteModelRegistryRepository(SQLiteRepositoryBase, ModelRegistryRepository):
    """SQLite implementation of model registry operations."""

    # Model operations
    async def create_model(self, name: str, description: Optional[str] = None) -> Model:
        """Create a new model entry."""
        model = Model(name=name, description=description)
        self.session.add(model)
        await self.session.flush()

        # Reload with relationships to avoid lazy loading issues
        stmt = (
            select(Model)
            .options(selectinload(Model.versions))
            .where(Model.id == model.id)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one()

        logger.info(f"Created model: {model.id} - {name}")
        return model

    async def get_model(self, model_id: str) -> Optional[Model]:
        """Get a model by ID."""
        stmt = (
            select(Model)
            .options(selectinload(Model.versions))
            .where(Model.id == model_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_model_by_name(self, name: str) -> Optional[Model]:
        """Get a model by name."""
        stmt = (
            select(Model)
            .options(selectinload(Model.versions))
            .where(Model.name == name)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_models(self, active_only: bool = True) -> List[Model]:
        """List all models."""
        stmt = select(Model).options(selectinload(Model.versions))
        if active_only:
            stmt = stmt.where(Model.is_active == True)
        stmt = stmt.order_by(desc(Model.created_at))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_model(
        self, model_id: str, name: Optional[str] = None, description: Optional[str] = None
    ) -> Optional[Model]:
        """Update a model."""
        model = await self.get_model(model_id)
        if not model:
            return None

        if name is not None:
            model.name = name
        if description is not None:
            model.description = description

        await self.session.flush()

        # Reload with relationships to avoid lazy loading issues
        stmt = (
            select(Model)
            .options(selectinload(Model.versions))
            .where(Model.id == model_id)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one()

        logger.info(f"Updated model: {model_id}")
        return model

    async def delete_model(self, model_id: str) -> bool:
        """Delete a model (soft delete by setting is_active=False)."""
        model = await self.get_model(model_id)
        if not model:
            return False

        model.is_active = False
        await self.session.flush()
        logger.info(f"Soft deleted model: {model_id}")
        return True

    # Version operations
    async def create_version(
        self,
        model_id: str,
        version: str,
        file_path: str,
        file_size_bytes: Optional[int] = None,
        file_hash: Optional[str] = None,
        precision: str = "FLOAT16",
    ) -> ModelVersion:
        """Create a new version for a model."""
        model_version = ModelVersion(
            model_id=model_id,
            version=version,
            file_path=file_path,
            file_size_bytes=file_size_bytes,
            file_hash=file_hash,
            precision=precision,
        )
        self.session.add(model_version)
        await self.session.flush()
        await self.session.refresh(model_version)
        logger.info(f"Created version {version} for model {model_id}")
        return model_version

    async def get_version(self, version_id: str) -> Optional[ModelVersion]:
        """Get a version by ID."""
        stmt = select(ModelVersion).where(ModelVersion.id == version_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_version_by_number(
        self, model_id: str, version: str
    ) -> Optional[ModelVersion]:
        """Get a specific version of a model."""
        stmt = select(ModelVersion).where(
            ModelVersion.model_id == model_id,
            ModelVersion.version == version,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_published_version(
        self, model_id: str
    ) -> Optional[ModelVersion]:
        """Get the latest published version of a model."""
        stmt = (
            select(ModelVersion)
            .where(
                ModelVersion.model_id == model_id,
                ModelVersion.is_published == True,
            )
            .order_by(desc(ModelVersion.created_at))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_versions(
        self, model_id: str, published_only: bool = False
    ) -> List[ModelVersion]:
        """List all versions of a model."""
        stmt = select(ModelVersion).where(ModelVersion.model_id == model_id)
        if published_only:
            stmt = stmt.where(ModelVersion.is_published == True)
        stmt = stmt.order_by(desc(ModelVersion.created_at))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def publish_version(self, version_id: str) -> Optional[ModelVersion]:
        """Publish a version."""
        version = await self.get_version(version_id)
        if not version:
            return None

        version.is_published = True
        await self.session.flush()
        await self.session.refresh(version)
        logger.info(f"Published version: {version_id}")
        return version

    async def unpublish_version(self, version_id: str) -> Optional[ModelVersion]:
        """Unpublish a version."""
        version = await self.get_version(version_id)
        if not version:
            return None

        version.is_published = False
        await self.session.flush()
        await self.session.refresh(version)
        logger.info(f"Unpublished version: {version_id}")
        return version

    async def increment_download_count(self, version_id: str) -> None:
        """Increment the download count for a version."""
        version = await self.get_version(version_id)
        if version:
            version.download_count += 1
            await self.session.flush()
