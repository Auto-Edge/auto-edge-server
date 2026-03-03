"""
Unit Tests for FileSystemRepository
"""

import io

import pytest

from app.core.exceptions import FileNotFoundError, ValidationError
from app.repositories.filesystem_repo import FileSystemRepository


class TestFileSystemRepository:
    """Tests for FileSystemRepository."""

    @pytest.mark.asyncio
    async def test_save_and_get(self, test_repository: FileSystemRepository):
        """Test saving and retrieving a file."""
        content = io.BytesIO(b"test content")
        saved_path = await test_repository.save("test.pt", content)

        assert saved_path.exists()

        retrieved_path = await test_repository.get("test.pt")
        assert retrieved_path == saved_path

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, test_repository: FileSystemRepository):
        """Test getting a non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            await test_repository.get("nonexistent.pt")

    @pytest.mark.asyncio
    async def test_exists_true(self, test_repository: FileSystemRepository):
        """Test exists returns True for existing file."""
        content = io.BytesIO(b"test content")
        await test_repository.save("test.pt", content)

        assert await test_repository.exists("test.pt")

    @pytest.mark.asyncio
    async def test_exists_false(self, test_repository: FileSystemRepository):
        """Test exists returns False for non-existent file."""
        assert not await test_repository.exists("nonexistent.pt")

    @pytest.mark.asyncio
    async def test_delete_existing(self, test_repository: FileSystemRepository):
        """Test deleting an existing file."""
        content = io.BytesIO(b"test content")
        await test_repository.save("test.pt", content)

        result = await test_repository.delete("test.pt")

        assert result is True
        assert not await test_repository.exists("test.pt")

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, test_repository: FileSystemRepository):
        """Test deleting a non-existent file returns False."""
        result = await test_repository.delete("nonexistent.pt")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_models(self, test_repository: FileSystemRepository, temp_dir):
        """Test listing models with correct extensions."""
        # Create test files
        (temp_dir / "model1.mlmodel").write_text("test")
        (temp_dir / "model2.mlmodel").write_text("test")
        (temp_dir / "other.pt").write_text("test")

        models = await test_repository.list_models()

        assert len(models) == 2
        assert "model1.mlmodel" in models
        assert "model2.mlmodel" in models

    @pytest.mark.asyncio
    async def test_directory_traversal_prevented(
        self, test_repository: FileSystemRepository
    ):
        """Test that directory traversal is prevented."""
        with pytest.raises(ValidationError):
            await test_repository.get("../etc/passwd")

    def test_get_size_mb(self, test_repository: FileSystemRepository, temp_dir):
        """Test file size calculation."""
        # Create a file with known size (1024 bytes = 0.00 MB rounded)
        test_file = temp_dir / "test.pt"
        test_file.write_bytes(b"x" * 1024 * 1024)  # 1 MB

        size = test_repository.get_size_mb("test.pt")
        assert size == 1.0
