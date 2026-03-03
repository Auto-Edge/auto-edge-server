"""
SQLite Analytics Repository

SQLite implementation of the analytics repository.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, desc

from app.models.analytics import AnalyticsEvent
from app.models.model import ModelVersion
from app.models.device import Device
from app.repositories.analytics_repo import AnalyticsRepository
from app.repositories.sqlite.base import SQLiteRepositoryBase

logger = logging.getLogger(__name__)


class SQLiteAnalyticsRepository(SQLiteRepositoryBase, AnalyticsRepository):
    """SQLite implementation of analytics operations."""

    async def create_event(
        self,
        event_type: str,
        device_id: Optional[str] = None,
        model_version_id: Optional[str] = None,
        inference_latency_ms: Optional[float] = None,
        memory_usage_bytes: Optional[int] = None,
    ) -> AnalyticsEvent:
        """Create a new analytics event."""
        event = AnalyticsEvent(
            event_type=event_type,
            device_id=device_id,
            model_version_id=model_version_id,
            inference_latency_ms=inference_latency_ms,
            memory_usage_bytes=memory_usage_bytes,
        )
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        logger.debug(f"Created analytics event: {event_type}")
        return event

    async def create_events_batch(
        self, events: List[Dict[str, Any]]
    ) -> List[AnalyticsEvent]:
        """Create multiple analytics events in a batch."""
        created_events = []
        for event_data in events:
            event = AnalyticsEvent(
                event_type=event_data["event_type"],
                device_id=event_data.get("device_id"),
                model_version_id=event_data.get("model_version_id"),
                inference_latency_ms=event_data.get("inference_latency_ms"),
                memory_usage_bytes=event_data.get("memory_usage_bytes"),
            )
            self.session.add(event)
            created_events.append(event)

        await self.session.flush()
        for event in created_events:
            await self.session.refresh(event)

        logger.info(f"Created {len(created_events)} analytics events in batch")
        return created_events

    async def get_events_for_model(
        self,
        model_id: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[AnalyticsEvent]:
        """Get analytics events for a model."""
        # First get all version IDs for this model
        version_stmt = select(ModelVersion.id).where(ModelVersion.model_id == model_id)
        version_result = await self.session.execute(version_stmt)
        version_ids = [v[0] for v in version_result.all()]

        if not version_ids:
            return []

        # Then get events for those versions
        stmt = select(AnalyticsEvent).where(
            AnalyticsEvent.model_version_id.in_(version_ids)
        )

        if since:
            stmt = stmt.where(AnalyticsEvent.created_at >= since)
        if until:
            stmt = stmt.where(AnalyticsEvent.created_at <= until)

        stmt = stmt.order_by(desc(AnalyticsEvent.created_at)).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_events_for_device(
        self,
        device_id: str,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AnalyticsEvent]:
        """Get analytics events for a device."""
        stmt = select(AnalyticsEvent).where(AnalyticsEvent.device_id == device_id)

        if since:
            stmt = stmt.where(AnalyticsEvent.created_at >= since)

        stmt = stmt.order_by(desc(AnalyticsEvent.created_at)).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_inference_stats(
        self,
        model_id: str,
        since: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get aggregated inference statistics for a model."""
        # Get version IDs for this model
        version_stmt = select(ModelVersion.id).where(ModelVersion.model_id == model_id)
        version_result = await self.session.execute(version_stmt)
        version_ids = [v[0] for v in version_result.all()]

        if not version_ids:
            return {
                "total_inferences": 0,
                "avg_latency_ms": None,
                "min_latency_ms": None,
                "max_latency_ms": None,
                "p50_latency_ms": None,
                "p95_latency_ms": None,
                "avg_memory_bytes": None,
            }

        # Build query for inference events
        stmt = select(
            func.count(AnalyticsEvent.id).label("total"),
            func.avg(AnalyticsEvent.inference_latency_ms).label("avg_latency"),
            func.min(AnalyticsEvent.inference_latency_ms).label("min_latency"),
            func.max(AnalyticsEvent.inference_latency_ms).label("max_latency"),
            func.avg(AnalyticsEvent.memory_usage_bytes).label("avg_memory"),
        ).where(
            AnalyticsEvent.model_version_id.in_(version_ids),
            AnalyticsEvent.event_type == "inference",
        )

        if since:
            stmt = stmt.where(AnalyticsEvent.created_at >= since)

        result = await self.session.execute(stmt)
        row = result.one()

        return {
            "total_inferences": row.total or 0,
            "avg_latency_ms": float(row.avg_latency) if row.avg_latency else None,
            "min_latency_ms": float(row.min_latency) if row.min_latency else None,
            "max_latency_ms": float(row.max_latency) if row.max_latency else None,
            "avg_memory_bytes": int(row.avg_memory) if row.avg_memory else None,
        }

    async def get_event_counts_by_type(
        self,
        since: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """Get event counts grouped by type."""
        stmt = select(
            AnalyticsEvent.event_type,
            func.count(AnalyticsEvent.id).label("count"),
        ).group_by(AnalyticsEvent.event_type)

        if since:
            stmt = stmt.where(AnalyticsEvent.created_at >= since)

        result = await self.session.execute(stmt)
        return {row.event_type: row.count for row in result.all()}

    async def get_total_inferences(
        self, since: Optional[datetime] = None
    ) -> int:
        """Get total number of inference events."""
        stmt = select(func.count(AnalyticsEvent.id)).where(
            AnalyticsEvent.event_type == "inference"
        )

        if since:
            stmt = stmt.where(AnalyticsEvent.created_at >= since)

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_device_type_distribution(self) -> Dict[str, int]:
        """Get distribution of device types."""
        stmt = select(
            Device.device_type,
            func.count(Device.id).label("count"),
        ).group_by(Device.device_type)

        result = await self.session.execute(stmt)
        return {
            (row.device_type or "Unknown"): row.count
            for row in result.all()
        }
