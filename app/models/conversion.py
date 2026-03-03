"""
Conversion ORM Model

Represents conversion jobs with persistence.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


class Conversion(Base):
    """
    Conversion job entry.

    Tracks model conversion jobs for persistence across page reloads.
    """

    __tablename__ = "conversions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    task_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending, processing, completed, failed

    # Input
    input_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_demo: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Output (populated on completion)
    output_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    original_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    optimized_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reduction: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    precision: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Error (if failed)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Link to registered model (optional)
    registered_model_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("models.id"), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Conversion(id={self.id}, task_id={self.task_id}, status={self.status})>"
