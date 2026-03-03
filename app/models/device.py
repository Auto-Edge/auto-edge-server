"""
Device ORM Model

Represents devices that connect to the OTA service.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


class Device(Base):
    """
    Device registry entry.

    Tracks devices that have registered with the OTA service.
    """

    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    device_identifier: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    device_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    os_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    analytics_events: Mapped[List["AnalyticsEvent"]] = relationship(
        "AnalyticsEvent", back_populates="device"
    )

    def __repr__(self) -> str:
        return f"<Device(id={self.id}, identifier={self.device_identifier})>"


# Import here to avoid circular imports
from app.models.analytics import AnalyticsEvent
