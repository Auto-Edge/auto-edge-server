"""
Repository Layer

Abstract interfaces and implementations for data access.
"""

from app.repositories.base import ModelRepository
from app.repositories.filesystem_repo import FileSystemRepository

__all__ = [
    "ModelRepository",
    "FileSystemRepository",
]
