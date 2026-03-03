"""
SQLite Conversion Repository

SQLite implementation of the conversion repository.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, desc, or_

from app.models.conversion import Conversion
from app.repositories.conversion_repo import ConversionRepository
from app.repositories.sqlite.base import SQLiteRepositoryBase

logger = logging.getLogger(__name__)


class SQLiteConversionRepository(SQLiteRepositoryBase, ConversionRepository):
    """SQLite implementation of conversion operations."""

    async def create(
        self,
        task_id: str,
        input_filename: Optional[str] = None,
        is_demo: bool = False,
    ) -> Conversion:
        """Create a new conversion job."""
        conversion = Conversion(
            task_id=task_id,
            input_filename=input_filename,
            is_demo=is_demo,
            status="pending",
        )
        self.session.add(conversion)
        await self.session.flush()
        await self.session.refresh(conversion)
        logger.info(f"Created conversion: {conversion.id} for task {task_id}")
        return conversion

    async def get(self, conversion_id: str) -> Optional[Conversion]:
        """Get a conversion by ID."""
        stmt = select(Conversion).where(Conversion.id == conversion_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_task_id(self, task_id: str) -> Optional[Conversion]:
        """Get a conversion by Celery task ID."""
        stmt = select(Conversion).where(Conversion.task_id == task_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_recent(self, limit: int = 20) -> List[Conversion]:
        """List recent conversions."""
        stmt = (
            select(Conversion)
            .order_by(desc(Conversion.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_active(self) -> List[Conversion]:
        """List active (pending/processing) conversions."""
        stmt = (
            select(Conversion)
            .where(or_(
                Conversion.status == "pending",
                Conversion.status == "processing",
            ))
            .order_by(desc(Conversion.created_at))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        conversion_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Optional[Conversion]:
        """Update conversion status and result."""
        conversion = await self.get(conversion_id)
        if not conversion:
            return None

        conversion.status = status

        if status in ("completed", "failed"):
            conversion.completed_at = datetime.utcnow()

        if result:
            conversion.output_file = result.get("output_file")
            conversion.model_name = result.get("model_name")
            conversion.original_size = result.get("original_size")
            conversion.optimized_size = result.get("optimized_size")
            conversion.reduction = result.get("reduction")
            conversion.precision = result.get("precision")

        if error:
            conversion.error_message = error

        await self.session.flush()
        await self.session.refresh(conversion)
        logger.info(f"Updated conversion {conversion_id} to status: {status}")
        return conversion

    async def link_to_model(
        self, conversion_id: str, model_id: str
    ) -> Optional[Conversion]:
        """Link a conversion to a registered model."""
        conversion = await self.get(conversion_id)
        if not conversion:
            return None

        conversion.registered_model_id = model_id
        await self.session.flush()
        await self.session.refresh(conversion)
        logger.info(f"Linked conversion {conversion_id} to model {model_id}")
        return conversion

    async def delete(self, conversion_id: str) -> bool:
        """Delete a conversion."""
        conversion = await self.get(conversion_id)
        if not conversion:
            return False

        await self.session.delete(conversion)
        await self.session.flush()
        logger.info(f"Deleted conversion: {conversion_id}")
        return True
