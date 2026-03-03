"""
Pytest Configuration and Fixtures

Shared test fixtures for AutoEdge tests.
"""

import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.dependencies import get_conversion_service, get_file_service, get_repository
from app.main import create_app
from app.repositories.filesystem_repo import FileSystemRepository
from app.services.conversion_service import ConversionService
from app.services.file_service import FileService


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_settings(temp_dir: Path) -> Settings:
    """Create test settings with temporary directory."""
    return Settings(
        shared_data_path=temp_dir,
        debug=True,
    )


@pytest.fixture
def test_repository(temp_dir: Path) -> FileSystemRepository:
    """Create a test repository."""
    return FileSystemRepository(base_path=temp_dir)


@pytest.fixture
def test_file_service(test_repository: FileSystemRepository) -> FileService:
    """Create a test file service."""
    return FileService(
        repository=test_repository,
        allowed_extensions=[".pt", ".pth"],
        max_file_size_mb=100,
    )


@pytest.fixture
def mock_celery_app() -> MagicMock:
    """Create a mock Celery app."""
    return MagicMock()


@pytest.fixture
def test_conversion_service(mock_celery_app: MagicMock) -> ConversionService:
    """Create a test conversion service with mocked Celery."""
    return ConversionService(celery_app=mock_celery_app)


@pytest.fixture
def client(
    test_settings: Settings,
    test_file_service: FileService,
    test_conversion_service: ConversionService,
    test_repository: FileSystemRepository,
) -> TestClient:
    """Create a test client with dependency overrides."""
    app = create_app()

    # Override dependencies
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_file_service] = lambda: test_file_service
    app.dependency_overrides[get_conversion_service] = lambda: test_conversion_service
    app.dependency_overrides[get_repository] = lambda: test_repository

    return TestClient(app)


@pytest.fixture
def sample_pt_file(temp_dir: Path) -> Path:
    """Create a sample .pt file for testing."""
    file_path = temp_dir / "test_model.pt"
    file_path.write_bytes(b"dummy pytorch model data")
    return file_path
