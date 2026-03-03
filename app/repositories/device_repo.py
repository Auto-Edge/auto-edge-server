"""
Device Repository Interface

Abstract interface for device operations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from app.models.device import Device


class DeviceRepository(ABC):
    """Abstract interface for device operations."""

    @abstractmethod
    async def register_device(
        self,
        device_identifier: str,
        device_type: Optional[str] = None,
        os_version: Optional[str] = None,
    ) -> Device:
        """Register a new device or update existing one."""
        pass

    @abstractmethod
    async def get_device(self, device_id: str) -> Optional[Device]:
        """Get a device by ID."""
        pass

    @abstractmethod
    async def get_device_by_identifier(self, device_identifier: str) -> Optional[Device]:
        """Get a device by its identifier."""
        pass

    @abstractmethod
    async def update_last_seen(self, device_id: str) -> None:
        """Update the last seen timestamp for a device."""
        pass

    @abstractmethod
    async def list_devices(self, limit: int = 100, offset: int = 0) -> List[Device]:
        """List all devices with pagination."""
        pass

    @abstractmethod
    async def get_device_count(self) -> int:
        """Get total number of registered devices."""
        pass

    @abstractmethod
    async def get_active_devices_since(self, since: datetime) -> int:
        """Get count of devices active since a given time."""
        pass
