"""
SQLite Repository Base

Base class for SQLite repository implementations.
"""

from sqlalchemy.ext.asyncio import AsyncSession


class SQLiteRepositoryBase:
    """Base class for SQLite repositories."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session.
        """
        self._session = session

    @property
    def session(self) -> AsyncSession:
        """Get the database session."""
        return self._session
