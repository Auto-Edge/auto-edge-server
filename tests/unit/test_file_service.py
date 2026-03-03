"""
Unit Tests for FileService
"""

import io

import pytest

from app.core.exceptions import ValidationError
from app.services.file_service import FileService


class TestFileService:
    """Tests for FileService."""

    def test_validate_filename_valid_pt(self, test_file_service: FileService):
        """Test validation passes for .pt files."""
        test_file_service.validate_filename("model.pt")

    def test_validate_filename_valid_pth(self, test_file_service: FileService):
        """Test validation passes for .pth files."""
        test_file_service.validate_filename("model.pth")

    def test_validate_filename_invalid_extension(self, test_file_service: FileService):
        """Test validation fails for invalid extensions."""
        with pytest.raises(ValidationError) as exc_info:
            test_file_service.validate_filename("model.txt")

        assert exc_info.value.field == "filename"
        assert "Invalid file type" in exc_info.value.message

    def test_validate_filename_empty(self, test_file_service: FileService):
        """Test validation fails for empty filename."""
        with pytest.raises(ValidationError) as exc_info:
            test_file_service.validate_filename("")

        assert exc_info.value.field == "filename"

    @pytest.mark.asyncio
    async def test_save_upload_success(self, test_file_service: FileService):
        """Test successful file upload."""
        content = io.BytesIO(b"test model content")
        path = await test_file_service.save_upload("test.pt", content)

        assert path.exists()
        assert path.name == "test.pt"

    @pytest.mark.asyncio
    async def test_save_upload_invalid_extension(self, test_file_service: FileService):
        """Test file upload fails for invalid extension."""
        content = io.BytesIO(b"test content")

        with pytest.raises(ValidationError):
            await test_file_service.save_upload("test.txt", content)

    @pytest.mark.asyncio
    async def test_list_converted_models_empty(self, test_file_service: FileService):
        """Test listing models when none exist."""
        models = await test_file_service.list_converted_models()
        assert models == []
