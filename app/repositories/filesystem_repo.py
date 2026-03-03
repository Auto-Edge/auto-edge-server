"""
Filesystem Repository Implementation

Concrete implementation of ModelRepository using local filesystem.
"""

import logging
from pathlib import Path
from typing import BinaryIO, List, Optional

from app.core.exceptions import FileNotFoundError, StorageError, ValidationError
from app.repositories.base import ModelRepository

logger = logging.getLogger(__name__)


class FileSystemRepository(ModelRepository):
    """Filesystem-based model storage implementation."""

    def __init__(self, base_path: Path):
        """
        Initialize filesystem repository.

        Args:
            base_path: Base directory for file storage.
        """
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _validate_filename(self, filename: str) -> None:
        """Validate filename for security (prevent directory traversal)."""
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValidationError(
                message="Invalid filename",
                field="filename",
                details={"filename": filename},
            )

    def _get_full_path(self, filename: str) -> Path:
        """Get full path for a filename."""
        self._validate_filename(filename)
        return self.base_path / filename

    async def save(self, filename: str, content: BinaryIO) -> Path:
        """Save a model file to the filesystem."""
        try:
            file_path = self._get_full_path(filename)

            with open(file_path, "wb") as f:
                f.write(content.read())

            logger.info(f"File saved: {file_path}")
            return file_path

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to save file {filename}: {e}")
            raise StorageError(
                message="Failed to save file",
                path=filename,
                details={"error": str(e)},
            )

    async def get(self, filename: str) -> Path:
        """Get the path to a stored model file."""
        file_path = self._get_full_path(filename)

        if not file_path.exists():
            raise FileNotFoundError(filename=filename)

        return file_path

    async def exists(self, filename: str) -> bool:
        """Check if a model file exists."""
        try:
            file_path = self._get_full_path(filename)
            return file_path.exists()
        except ValidationError:
            return False

    async def delete(self, filename: str) -> bool:
        """Delete a model file from storage."""
        try:
            file_path = self._get_full_path(filename)

            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted: {file_path}")
                return True

            return False

        except ValidationError:
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {filename}: {e}")
            raise StorageError(
                message="Failed to delete file",
                path=filename,
                details={"error": str(e)},
            )

    async def list_models(self, extensions: Optional[List[str]] = None) -> List[str]:
        """List all model files in storage."""
        if extensions is None:
            extensions = [".mlmodel", ".mlpackage"]

        models = []
        for item in self.base_path.iterdir():
            if item.suffix in extensions:
                models.append(item.name)

        return sorted(models)

    def get_size_mb(self, filename: str) -> float:
        """Get the size of a file in megabytes."""
        try:
            file_path = self._get_full_path(filename)

            if not file_path.exists():
                return 0.0

            if file_path.is_file():
                size_bytes = file_path.stat().st_size
            elif file_path.is_dir():
                size_bytes = sum(
                    f.stat().st_size for f in file_path.rglob("*") if f.is_file()
                )
            else:
                return 0.0

            return round(size_bytes / (1024 * 1024), 2)

        except Exception:
            return 0.0

    def get_path_size_mb(self, path: Path) -> float:
        """Get the size of a path (file or directory) in megabytes."""
        try:
            if not path.exists():
                return 0.0

            if path.is_file():
                size_bytes = path.stat().st_size
            elif path.is_dir():
                size_bytes = sum(
                    f.stat().st_size for f in path.rglob("*") if f.is_file()
                )
            else:
                return 0.0

            return round(size_bytes / (1024 * 1024), 2)

        except Exception:
            return 0.0
