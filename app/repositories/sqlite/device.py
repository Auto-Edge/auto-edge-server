"""
SQLite Device Repository

SQLite implementation of the device repository.
"""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, func

from app.models.device import Device
from app.repositories.device_repo import DeviceRepository
from app.repositories.sqlite.base import SQLiteRepositoryBase

logger = logging.getLogger(__name__)


class SQLiteDeviceRepository(SQLiteRepositoryBase, DeviceRepository):
    """SQLite implementation of device operations."""

    async def register_device(
        self,
        device_identifier: str,
        device_type: Optional[str] = None,
        os_version: Optional[str] = None,
    ) -> Device:
        """Register a new device or update existing one."""
        # Check if device already exists
        existing = await self.get_device_by_identifier(device_identifier)
        if existing:
            # Update existing device
            existing.device_type = device_type or existing.device_type
            existing.os_version = os_version or existing.os_version
            existing.last_seen_at = datetime.utcnow()
            await self.session.flush()
            await self.session.refresh(existing)
            logger.info(f"Updated existing device: {device_identifier}")
            return existing

        # Create new device
        device = Device(
            device_identifier=device_identifier,
            device_type=device_type,
            os_version=os_version,
            last_seen_at=datetime.utcnow(),
        )
        self.session.add(device)
        await self.session.flush()
        await self.session.refresh(device)
        logger.info(f"Registered new device: {device_identifier}")
        return device

    async def get_device(self, device_id: str) -> Optional[Device]:
        """Get a device by ID."""
        stmt = select(Device).where(Device.id == device_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_device_by_identifier(self, device_identifier: str) -> Optional[Device]:
        """Get a device by its identifier."""
        stmt = select(Device).where(Device.device_identifier == device_identifier)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_last_seen(self, device_id: str) -> None:
        """Update the last seen timestamp for a device."""
        device = await self.get_device(device_id)
        if device:
            device.last_seen_at = datetime.utcnow()
            await self.session.flush()

    async def list_devices(self, limit: int = 100, offset: int = 0) -> List[Device]:
        """List all devices with pagination."""
        stmt = (
            select(Device)
            .order_by(Device.last_seen_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_device_count(self) -> int:
        """Get total number of registered devices."""
        stmt = select(func.count(Device.id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_active_devices_since(self, since: datetime) -> int:
        """Get count of devices active since a given time."""
        stmt = select(func.count(Device.id)).where(Device.last_seen_at >= since)
        result = await self.session.execute(stmt)
        return result.scalar() or 0
