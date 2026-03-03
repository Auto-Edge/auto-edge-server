"""
Analytics Service

Business logic for analytics operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from app.models.analytics import AnalyticsEvent
from app.repositories.analytics_repo import AnalyticsRepository
from app.repositories.device_repo import DeviceRepository
from app.repositories.model_registry_repo import ModelRegistryRepository
from app.schemas.analytics import (
    AnalyticsEventRequest,
    InferenceStats,
    ModelMetricsResponse,
    DashboardSummaryResponse,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics operations."""

    def __init__(
        self,
        analytics_repo: AnalyticsRepository,
        device_repo: DeviceRepository,
        model_repo: ModelRegistryRepository,
    ):
        """
        Initialize analytics service.

        Args:
            analytics_repo: Analytics repository.
            device_repo: Device repository.
            model_repo: Model registry repository.
        """
        self._analytics_repo = analytics_repo
        self._device_repo = device_repo
        self._model_repo = model_repo

    async def ingest_events(
        self,
        events: List[AnalyticsEventRequest],
    ) -> List[AnalyticsEvent]:
        """
        Ingest a batch of analytics events.

        Args:
            events: List of events to ingest.

        Returns:
            List of created events.
        """
        # Resolve device and model version IDs
        event_dicts = []
        for event in events:
            event_dict: Dict[str, Any] = {
                "event_type": event.event_type,
                "inference_latency_ms": event.inference_latency_ms,
                "memory_usage_bytes": event.memory_usage_bytes,
            }

            # Resolve device ID
            if event.device_identifier:
                device = await self._device_repo.get_device_by_identifier(
                    event.device_identifier
                )
                if device:
                    event_dict["device_id"] = device.id

            # Resolve model version ID
            if event.model_id and event.model_version:
                version = await self._model_repo.get_version_by_number(
                    event.model_id, event.model_version
                )
                if version:
                    event_dict["model_version_id"] = version.id

            event_dicts.append(event_dict)

        return await self._analytics_repo.create_events_batch(event_dicts)

    async def get_model_metrics(
        self,
        model_id: str,
        since: Optional[datetime] = None,
    ) -> ModelMetricsResponse:
        """
        Get metrics for a specific model.

        Args:
            model_id: Model ID.
            since: Optional start time for metrics.

        Returns:
            Model metrics response.
        """
        # Get inference stats
        stats = await self._analytics_repo.get_inference_stats(model_id, since)

        # Get model versions for download count
        versions = await self._model_repo.list_versions(model_id)
        total_downloads = sum(v.download_count for v in versions)
        versions_published = sum(1 for v in versions if v.is_published)

        # Get active devices (approximate from analytics)
        events = await self._analytics_repo.get_events_for_model(
            model_id,
            since=since or datetime.utcnow() - timedelta(days=30),
        )
        unique_devices = len(set(e.device_id for e in events if e.device_id))

        return ModelMetricsResponse(
            model_id=model_id,
            inference_stats=InferenceStats(
                total_inferences=stats["total_inferences"],
                avg_latency_ms=stats.get("avg_latency_ms"),
                min_latency_ms=stats.get("min_latency_ms"),
                max_latency_ms=stats.get("max_latency_ms"),
                avg_memory_bytes=stats.get("avg_memory_bytes"),
            ),
            total_downloads=total_downloads,
            active_devices=unique_devices,
            versions_published=versions_published,
        )

    async def get_dashboard_summary(self) -> DashboardSummaryResponse:
        """
        Get dashboard summary statistics.

        Returns:
            Dashboard summary response.
        """
        # Get model stats
        models = await self._model_repo.list_models(active_only=True)
        total_models = len(models)

        # Count versions and downloads
        total_versions = 0
        total_downloads = 0
        for model in models:
            versions = await self._model_repo.list_versions(model.id)
            total_versions += len(versions)
            total_downloads += sum(v.download_count for v in versions)

        # Get device stats
        total_devices = await self._device_repo.get_device_count()
        active_devices_24h = await self._device_repo.get_active_devices_since(
            datetime.utcnow() - timedelta(hours=24)
        )

        # Get analytics stats
        total_inferences = await self._analytics_repo.get_total_inferences()
        event_counts = await self._analytics_repo.get_event_counts_by_type()
        device_distribution = await self._analytics_repo.get_device_type_distribution()

        return DashboardSummaryResponse(
            total_models=total_models,
            total_versions=total_versions,
            total_devices=total_devices,
            active_devices_24h=active_devices_24h,
            total_inferences=total_inferences,
            total_downloads=total_downloads,
            event_counts_by_type=event_counts,
            device_type_distribution=device_distribution,
        )
