"""
AnalyticsEvent ORM Model

Represents analytics events from devices.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.model import ModelVersion


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


class AnalyticsEvent(Base):
    """
    Analytics event entry.

    Tracks inference events and performance metrics from devices.
    """

    __tablename__ = "analytics_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    device_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("devices.id"), nullable=True
    )
    model_version_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("model_versions.id"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    inference_latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memory_usage_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    device: Mapped[Optional["Device"]] = relationship(
        "Device", back_populates="analytics_events"
    )
    model_version: Mapped[Optional["ModelVersion"]] = relationship(
        "ModelVersion", back_populates="analytics_events"
    )

    def __repr__(self) -> str:
        return f"<AnalyticsEvent(id={self.id}, type={self.event_type})>"
