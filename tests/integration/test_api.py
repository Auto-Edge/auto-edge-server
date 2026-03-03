"""
Integration Tests for API Endpoints
"""

import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for health endpoint."""

    def test_health_check(self, client: TestClient):
        """Test health check returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "autoedge-backend"


class TestUploadEndpoint:
    """Tests for upload endpoint."""

    def test_upload_valid_file(self, client: TestClient, test_conversion_service):
        """Test uploading a valid .pt file."""
        # Mock the conversion service
        test_conversion_service.start_conversion = MagicMock(return_value="test-task-id")

        files = {"file": ("model.pt", io.BytesIO(b"test model"), "application/octet-stream")}
        response = client.post("/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert "model.pt" in data["message"]

    def test_upload_invalid_extension(self, client: TestClient):
        """Test uploading a file with invalid extension."""
        files = {"file": ("model.txt", io.BytesIO(b"test"), "text/plain")}
        response = client.post("/upload", files=files)

        assert response.status_code == 400


class TestDemoEndpoint:
    """Tests for demo endpoint."""

    def test_demo_conversion(self, client: TestClient, test_conversion_service):
        """Test starting a demo conversion."""
        test_conversion_service.start_demo_conversion = MagicMock(return_value="demo-task-id")

        response = client.post("/demo")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "demo-task-id"
        assert "MobileNetV2" in data["message"]


class TestStatusEndpoint:
    """Tests for status endpoint."""

    def test_get_status_pending(self, client: TestClient, test_conversion_service):
        """Test getting status for a pending task."""
        test_conversion_service.get_task_status = MagicMock(
            return_value={
                "task_id": "test-123",
                "status": "Pending",
                "result": None,
            }
        )

        response = client.get("/status/test-123")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Pending"
        assert data["task_id"] == "test-123"

    def test_get_status_completed(self, client: TestClient, test_conversion_service):
        """Test getting status for a completed task."""
        test_conversion_service.get_task_status = MagicMock(
            return_value={
                "task_id": "test-123",
                "status": "Completed",
                "result": {
                    "status": "success",
                    "model_name": "test_model",
                    "reduction": "45.2%",
                },
            }
        )

        response = client.get("/status/test-123")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Completed"
        assert data["result"]["status"] == "success"


class TestModelsEndpoint:
    """Tests for models endpoint."""

    def test_list_models_empty(self, client: TestClient):
        """Test listing models when none exist."""
        response = client.get("/models")

        assert response.status_code == 200
        data = response.json()
        assert data["models"] == []

    def test_list_models_with_files(self, client: TestClient, temp_dir):
        """Test listing models when files exist."""
        # Create test model files
        (temp_dir / "model1.mlmodel").write_text("test")
        (temp_dir / "model2.mlmodel").write_text("test")

        response = client.get("/models")

        assert response.status_code == 200
        data = response.json()
        assert len(data["models"]) == 2


class TestDownloadEndpoint:
    """Tests for download endpoint."""

    def test_download_existing_file(self, client: TestClient, temp_dir):
        """Test downloading an existing file."""
        # Create test file
        test_file = temp_dir / "model.mlmodel"
        test_file.write_bytes(b"test model content")

        response = client.get("/download/model.mlmodel")

        assert response.status_code == 200
        assert response.content == b"test model content"

    def test_download_nonexistent_file(self, client: TestClient):
        """Test downloading a non-existent file."""
        response = client.get("/download/nonexistent.mlmodel")

        assert response.status_code == 404
