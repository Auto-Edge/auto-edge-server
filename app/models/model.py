"""
Model and ModelVersion ORM Models

Represents ML models and their versions in the registry.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


class Model(Base):
    """
    Model registry entry.

    Represents a registered ML model that can have multiple versions.
    """

    __tablename__ = "models"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    versions: Mapped[List["ModelVersion"]] = relationship(
        "ModelVersion", back_populates="model", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Model(id={self.id}, name={self.name})>"


class ModelVersion(Base):
    """
    Model version entry.

    Represents a specific version of a model with file metadata.
    """

    __tablename__ = "model_versions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    model_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("models.id"), nullable=False
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    precision: Mapped[str] = mapped_column(String(20), default="FLOAT16", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    model: Mapped["Model"] = relationship("Model", back_populates="versions")
    analytics_events: Mapped[List["AnalyticsEvent"]] = relationship(
        "AnalyticsEvent", back_populates="model_version"
    )

    # Unique constraint
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

    def __repr__(self) -> str:
        return f"<ModelVersion(id={self.id}, version={self.version})>"


# Import here to avoid circular imports
from app.models.analytics import AnalyticsEvent
