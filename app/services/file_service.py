"""
File Service

Handles file validation, upload, and storage operations.
"""

import logging
from pathlib import Path
from typing import BinaryIO, List

from app.core.exceptions import FileNotFoundError, ValidationError
from app.repositories.base import ModelRepository

logger = logging.getLogger(__name__)


class FileService:
    """Service for file operations."""

    def __init__(
        self,
        repository: ModelRepository,
        allowed_extensions: List[str],
        max_file_size_mb: int = 500,
    ):
        """
        Initialize file service.

        Args:
            repository: Storage repository instance.
            allowed_extensions: List of allowed file extensions.
            max_file_size_mb: Maximum file size in MB.
        """
        self.repository = repository
        self.allowed_extensions = allowed_extensions
        self.max_file_size_mb = max_file_size_mb

    def validate_filename(self, filename: str) -> None:
        """
        Validate file extension.

        Args:
            filename: Name of the file to validate.

        Raises:
            ValidationError: If extension is not allowed.
        """
        if not filename:
            raise ValidationError(
                message="Filename is required",
                field="filename",
            )

        extension = Path(filename).suffix.lower()
        if extension not in self.allowed_extensions:
            raise ValidationError(
                message=f"Invalid file type. Allowed: {', '.join(self.allowed_extensions)}",
                field="filename",
                details={
                    "extension": extension,
                    "allowed": self.allowed_extensions,
                },
            )

    async def save_upload(self, filename: str, content: BinaryIO) -> Path:
        """
        Validate and save an uploaded file.

        Args:
            filename: Original filename.
            content: File content.

        Returns:
            Path to saved file.

        Raises:
            ValidationError: If validation fails.
            StorageError: If save fails.
        """
        self.validate_filename(filename)
        logger.info(f"Saving uploaded file: {filename}")
        return await self.repository.save(filename, content)

    async def get_model_path(self, filename: str) -> Path:
        """
        Get path to a stored model file.

        Args:
            filename: Name of the model file.

        Returns:
            Path to the file.

        Raises:
            FileNotFoundError: If file doesn't exist.
        """
        return await self.repository.get(filename)

    async def list_converted_models(self) -> List[str]:
        """
        List all converted CoreML models.

        Returns:
            List of model filenames.
        """
        return await self.repository.list_models(
            extensions=[".mlmodel", ".mlpackage"]
        )

    async def file_exists(self, filename: str) -> bool:
        """Check if a file exists in storage."""
        return await self.repository.exists(filename)
