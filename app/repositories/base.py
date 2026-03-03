"""
Abstract Repository Interface

Defines the contract for model storage operations.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, List, Optional


class ModelRepository(ABC):
    """Abstract interface for model file storage operations."""

    @abstractmethod
    async def save(self, filename: str, content: BinaryIO) -> Path:
        """
        Save a model file to storage.

        Args:
            filename: Name for the saved file.
            content: File content as binary stream.

        Returns:
            Path to the saved file.

        Raises:
            StorageError: If save operation fails.
        """
        pass

    @abstractmethod
    async def get(self, filename: str) -> Path:
        """
        Get the path to a stored model file.

        Args:
            filename: Name of the file to retrieve.

        Returns:
            Path to the file.

        Raises:
            FileNotFoundError: If file does not exist.
        """
        pass

    @abstractmethod
    async def exists(self, filename: str) -> bool:
        """
        Check if a model file exists in storage.

        Args:
            filename: Name of the file to check.

        Returns:
            True if file exists, False otherwise.
        """
        pass

    @abstractmethod
    async def delete(self, filename: str) -> bool:
        """
        Delete a model file from storage.

        Args:
            filename: Name of the file to delete.

        Returns:
            True if deleted, False if not found.
        """
        pass

    @abstractmethod
    async def list_models(self, extensions: Optional[List[str]] = None) -> List[str]:
        """
        List all model files in storage.

        Args:
            extensions: Optional list of extensions to filter by.

        Returns:
            List of model filenames.
        """
        pass

    @abstractmethod
    def get_size_mb(self, filename: str) -> float:
        """
        Get the size of a file in megabytes.

        Args:
            filename: Name of the file.

        Returns:
            Size in MB, or 0.0 if not found.
        """
        pass
