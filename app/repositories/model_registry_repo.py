"""
Model Registry Repository Interface

Abstract interface for model registry operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.models.model import Model, ModelVersion


class ModelRegistryRepository(ABC):
    """Abstract interface for model registry operations."""

    # Model operations
    @abstractmethod
    async def create_model(self, name: str, description: Optional[str] = None) -> Model:
        """Create a new model entry."""
        pass

    @abstractmethod
    async def get_model(self, model_id: str) -> Optional[Model]:
        """Get a model by ID."""
        pass

    @abstractmethod
    async def get_model_by_name(self, name: str) -> Optional[Model]:
        """Get a model by name."""
        pass

    @abstractmethod
    async def list_models(self, active_only: bool = True) -> List[Model]:
        """List all models."""
        pass

    @abstractmethod
    async def update_model(
        self, model_id: str, name: Optional[str] = None, description: Optional[str] = None
    ) -> Optional[Model]:
        """Update a model."""
        pass

    @abstractmethod
    async def delete_model(self, model_id: str) -> bool:
        """Delete a model (soft delete by setting is_active=False)."""
        pass

    # Version operations
    @abstractmethod
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
        pass

    @abstractmethod
    async def get_version(self, version_id: str) -> Optional[ModelVersion]:
        """Get a version by ID."""
        pass

    @abstractmethod
    async def get_version_by_number(
        self, model_id: str, version: str
    ) -> Optional[ModelVersion]:
        """Get a specific version of a model."""
        pass

    @abstractmethod
    async def get_latest_published_version(
        self, model_id: str
    ) -> Optional[ModelVersion]:
        """Get the latest published version of a model."""
        pass

    @abstractmethod
    async def list_versions(
        self, model_id: str, published_only: bool = False
    ) -> List[ModelVersion]:
        """List all versions of a model."""
        pass

    @abstractmethod
    async def publish_version(self, version_id: str) -> Optional[ModelVersion]:
        """Publish a version."""
        pass

    @abstractmethod
    async def unpublish_version(self, version_id: str) -> Optional[ModelVersion]:
        """Unpublish a version."""
        pass

    @abstractmethod
    async def increment_download_count(self, version_id: str) -> None:
        """Increment the download count for a version."""
        pass
