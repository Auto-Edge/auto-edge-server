"""
Registry Service

Business logic for model registry operations.
"""

import hashlib
import logging
from pathlib import Path
from typing import List, Optional

from app.models.model import Model, ModelVersion
from app.repositories.model_registry_repo import ModelRegistryRepository
from app.core.exceptions import ValidationError, FileNotFoundError as AppFileNotFoundError

logger = logging.getLogger(__name__)


class RegistryService:
    """Service for model registry operations."""

    def __init__(self, repository: ModelRegistryRepository, storage_path: Path):
        """
        Initialize registry service.

        Args:
            repository: Model registry repository.
            storage_path: Path to model storage directory.
        """
        self._repository = repository
        self._storage_path = storage_path

    async def create_model(
        self, name: str, description: Optional[str] = None
    ) -> Model:
        """
        Create a new model.

        Args:
            name: Model name.
            description: Optional description.

        Returns:
            Created model.

        Raises:
            ValidationError: If model with same name exists.
        """
        # Check if model with same name exists
        existing = await self._repository.get_model_by_name(name)
        if existing:
            raise ValidationError(
                message=f"Model with name '{name}' already exists",
                field="name",
            )

        return await self._repository.create_model(name, description)

    async def get_model(self, model_id: str) -> Optional[Model]:
        """Get a model by ID."""
        return await self._repository.get_model(model_id)

    async def list_models(self, active_only: bool = True) -> List[Model]:
        """List all models."""
        return await self._repository.list_models(active_only)

    async def update_model(
        self,
        model_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Model]:
        """Update a model."""
        if name:
            # Check for duplicate name
            existing = await self._repository.get_model_by_name(name)
            if existing and existing.id != model_id:
                raise ValidationError(
                    message=f"Model with name '{name}' already exists",
                    field="name",
                )

        return await self._repository.update_model(model_id, name, description)

    async def delete_model(self, model_id: str) -> bool:
        """Delete a model (soft delete)."""
        return await self._repository.delete_model(model_id)

    async def create_version(
        self,
        model_id: str,
        version: str,
        file_path: str,
        file_size_bytes: Optional[int] = None,
        file_hash: Optional[str] = None,
        precision: str = "FLOAT16",
    ) -> ModelVersion:
        """
        Create a new version for a model.

        Args:
            model_id: Model ID.
            version: Version string.
            file_path: Path to the model file.
            file_size_bytes: File size in bytes.
            file_hash: SHA256 hash of the file.
            precision: Model precision.

        Returns:
            Created version.

        Raises:
            ValidationError: If model doesn't exist or version already exists.
            FileNotFoundError: If file doesn't exist.
        """
        # Check if model exists
        model = await self._repository.get_model(model_id)
        if not model:
            raise ValidationError(
                message=f"Model '{model_id}' not found",
                field="model_id",
            )

        # Check if version already exists
        existing = await self._repository.get_version_by_number(model_id, version)
        if existing:
            raise ValidationError(
                message=f"Version '{version}' already exists for this model",
                field="version",
            )

        # Verify file exists
        full_path = self._storage_path / file_path
        if not full_path.exists():
            raise AppFileNotFoundError(
                message=f"File not found: {file_path}",
                filename=file_path,
            )

        # Calculate file size and hash if not provided
        if file_size_bytes is None:
            file_size_bytes = full_path.stat().st_size

        if file_hash is None:
            file_hash = self._calculate_file_hash(full_path)

        return await self._repository.create_version(
            model_id=model_id,
            version=version,
            file_path=file_path,
            file_size_bytes=file_size_bytes,
            file_hash=file_hash,
            precision=precision,
        )

    async def get_version(self, version_id: str) -> Optional[ModelVersion]:
        """Get a version by ID."""
        return await self._repository.get_version(version_id)

    async def get_version_by_number(
        self, model_id: str, version: str
    ) -> Optional[ModelVersion]:
        """Get a specific version of a model."""
        return await self._repository.get_version_by_number(model_id, version)

    async def list_versions(
        self, model_id: str, published_only: bool = False
    ) -> List[ModelVersion]:
        """List all versions of a model."""
        return await self._repository.list_versions(model_id, published_only)

    async def publish_version(
        self, model_id: str, version: str, publish: bool = True
    ) -> Optional[ModelVersion]:
        """
        Publish or unpublish a version.

        Args:
            model_id: Model ID.
            version: Version string.
            publish: Whether to publish (True) or unpublish (False).

        Returns:
            Updated version or None if not found.
        """
        version_obj = await self._repository.get_version_by_number(model_id, version)
        if not version_obj:
            return None

        if publish:
            return await self._repository.publish_version(version_obj.id)
        else:
            return await self._repository.unpublish_version(version_obj.id)

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
