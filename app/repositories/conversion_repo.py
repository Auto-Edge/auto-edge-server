"""
Conversion Repository Interface

Abstract interface for conversion job operations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.models.conversion import Conversion


class ConversionRepository(ABC):
    """Abstract interface for conversion operations."""

    @abstractmethod
    async def create(
        self,
        task_id: str,
        input_filename: Optional[str] = None,
        is_demo: bool = False,
    ) -> Conversion:
        """Create a new conversion job."""
        pass

    @abstractmethod
    async def get(self, conversion_id: str) -> Optional[Conversion]:
        """Get a conversion by ID."""
        pass

    @abstractmethod
    async def get_by_task_id(self, task_id: str) -> Optional[Conversion]:
        """Get a conversion by Celery task ID."""
        pass

    @abstractmethod
    async def list_recent(self, limit: int = 20) -> List[Conversion]:
        """List recent conversions."""
        pass

    @abstractmethod
    async def list_active(self) -> List[Conversion]:
        """List active (pending/processing) conversions."""
        pass

    @abstractmethod
    async def update_status(
        self,
        conversion_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Optional[Conversion]:
        """Update conversion status and result."""
        pass

    @abstractmethod
    async def link_to_model(
        self, conversion_id: str, model_id: str
    ) -> Optional[Conversion]:
        """Link a conversion to a registered model."""
        pass

    @abstractmethod
    async def delete(self, conversion_id: str) -> bool:
        """Delete a conversion."""
        pass
