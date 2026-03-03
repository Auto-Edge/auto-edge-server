"""
OTA Service

Business logic for over-the-air model delivery.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

from app.models.device import Device
from app.models.model import ModelVersion
from app.repositories.device_repo import DeviceRepository
from app.repositories.model_registry_repo import ModelRegistryRepository
from app.schemas.ota import UpdateCheckResponse, DownloadInfo
from app.core.exceptions import FileNotFoundError as AppFileNotFoundError

logger = logging.getLogger(__name__)


class OTAService:
    """Service for OTA model delivery operations."""

    def __init__(
        self,
        device_repo: DeviceRepository,
        model_repo: ModelRegistryRepository,
        storage_path: Path,
        base_url: str = "",
    ):
        """
        Initialize OTA service.

        Args:
            device_repo: Device repository.
            model_repo: Model registry repository.
            storage_path: Path to model storage directory.
            base_url: Base URL for download links.
        """
        self._device_repo = device_repo
        self._model_repo = model_repo
        self._storage_path = storage_path
        self._base_url = base_url

    async def register_device(
        self,
        device_identifier: str,
        device_type: Optional[str] = None,
        os_version: Optional[str] = None,
    ) -> Device:
        """
        Register a device or update existing device info.

        Args:
            device_identifier: Unique device identifier.
            device_type: Device type string.
            os_version: OS version string.

        Returns:
            Device object.
        """
        return await self._device_repo.register_device(
            device_identifier=device_identifier,
            device_type=device_type,
            os_version=os_version,
        )

    async def check_for_update(
        self,
        model_id: str,
        current_version: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> UpdateCheckResponse:
        """
        Check if an update is available for a model.

        Args:
            model_id: Model ID or name to check.
            current_version: Current version on device (optional).
            device_id: Device ID for tracking (optional).

        Returns:
            UpdateCheckResponse with update info.
        """
        # Update device last seen if provided
        if device_id:
            await self._device_repo.update_last_seen(device_id)

        # Resolve model_id (could be name or UUID)
        resolved_model_id = await self._resolve_model_id(model_id)
        if not resolved_model_id:
            return UpdateCheckResponse(
                has_update=False,
                current_version=current_version,
                latest_version=None,
                download_url=None,
            )

        # Get latest published version
        latest = await self._model_repo.get_latest_published_version(resolved_model_id)

        if not latest:
            return UpdateCheckResponse(
                has_update=False,
                current_version=current_version,
                latest_version=None,
                download_url=None,
            )

        # Check if update is needed
        has_update = current_version is None or current_version != latest.version

        download_url = None
        if has_update:
            download_url = f"{self._base_url}/api/v1/ota/download/{model_id}/{latest.version}"

        return UpdateCheckResponse(
            has_update=has_update,
            current_version=current_version,
            latest_version=latest.version,
            download_url=download_url,
            file_size_bytes=latest.file_size_bytes,
            file_hash=latest.file_hash,
        )

    async def get_download_info(
        self,
        model_id: str,
        version: Optional[str] = None,
    ) -> Tuple[DownloadInfo, Path]:
        """
        Get download information for a model version.

        Args:
            model_id: Model ID or name.
            version: Version string (None for latest).

        Returns:
            Tuple of (DownloadInfo, file_path).

        Raises:
            FileNotFoundError: If version or file not found.
        """
        # Resolve model_id (could be name or UUID)
        resolved_model_id = await self._resolve_model_id(model_id)
        if not resolved_model_id:
            raise AppFileNotFoundError(
                message=f"Model '{model_id}' not found",
                filename=model_id,
            )

        # Get version
        if version is None or version.lower() == "latest":
            model_version = await self._model_repo.get_latest_published_version(resolved_model_id)
            if not model_version:
                raise AppFileNotFoundError(
                    message=f"No published version found for model '{model_id}'",
                    filename=model_id,
                )
        else:
            model_version = await self._model_repo.get_version_by_number(resolved_model_id, version)
            if not model_version:
                raise AppFileNotFoundError(
                    message=f"Version '{version}' not found for model '{model_id}'",
                    filename=f"{model_id}/{version}",
                )

        # Verify file exists
        file_path = self._storage_path / model_version.file_path
        if not file_path.exists():
            raise AppFileNotFoundError(
                message=f"Model file not found: {model_version.file_path}",
                filename=model_version.file_path,
            )

        # Increment download count
        await self._model_repo.increment_download_count(model_version.id)

        download_info = DownloadInfo(
            model_id=model_id,
            version=model_version.version,
            file_path=model_version.file_path,
            file_size_bytes=model_version.file_size_bytes,
            file_hash=model_version.file_hash,
            precision=model_version.precision,
        )

        return download_info, file_path

    async def get_device_by_identifier(self, device_identifier: str) -> Optional[Device]:
        """Get device by its identifier."""
        return await self._device_repo.get_device_by_identifier(device_identifier)

    async def _resolve_model_id(self, model_id_or_name: str) -> Optional[str]:
        """
        Resolve a model ID or name to the actual model UUID.

        Args:
            model_id_or_name: Either a UUID or model name.

        Returns:
            The model UUID if found, None otherwise.
        """
        # First try to get by ID (UUID)
        model = await self._model_repo.get_model(model_id_or_name)
        if model:
            return model.id

        # If not found, try to get by name
        model = await self._model_repo.get_model_by_name(model_id_or_name)
        if model:
            return model.id

        return None
