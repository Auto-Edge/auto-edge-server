"""
Analytics Repository Interface

Abstract interface for analytics operations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any

from app.models.analytics import AnalyticsEvent


class AnalyticsRepository(ABC):
    """Abstract interface for analytics operations."""

    @abstractmethod
    async def create_event(
        self,
        event_type: str,
        device_id: Optional[str] = None,
        model_version_id: Optional[str] = None,
        inference_latency_ms: Optional[float] = None,
        memory_usage_bytes: Optional[int] = None,
    ) -> AnalyticsEvent:
        """Create a new analytics event."""
        pass

    @abstractmethod
    async def create_events_batch(
        self, events: List[Dict[str, Any]]
    ) -> List[AnalyticsEvent]:
        """Create multiple analytics events in a batch."""
        pass

    @abstractmethod
    async def get_events_for_model(
        self,
        model_id: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[AnalyticsEvent]:
        """Get analytics events for a model."""
        pass

    @abstractmethod
    async def get_events_for_device(
        self,
        device_id: str,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AnalyticsEvent]:
        """Get analytics events for a device."""
        pass

    @abstractmethod
    async def get_inference_stats(
        self,
        model_id: str,
        since: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get aggregated inference statistics for a model."""
        pass

    @abstractmethod
    async def get_event_counts_by_type(
        self,
        since: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """Get event counts grouped by type."""
        pass

    @abstractmethod
    async def get_total_inferences(
        self, since: Optional[datetime] = None
    ) -> int:
        """Get total number of inference events."""
        pass

    @abstractmethod
    async def get_device_type_distribution(self) -> Dict[str, int]:
        """Get distribution of device types."""
        pass
