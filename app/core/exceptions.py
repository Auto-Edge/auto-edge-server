"""
Custom Exception Hierarchy

Domain-specific exceptions for AutoEdge application.
"""

from typing import Any, Dict, Optional


class AutoEdgeException(Exception):
    """Base exception for all AutoEdge errors."""

    def __init__(
        self,
        message: str,
        code: str = "AUTOEDGE_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AutoEdgeException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"field": field, **(details or {})},
        )
        self.field = field


class StorageError(AutoEdgeException):
    """Raised when file storage operations fail."""

    def __init__(
        self,
        message: str,
        path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="STORAGE_ERROR",
            details={"path": path, **(details or {})},
        )
        self.path = path


class FileNotFoundError(AutoEdgeException):
    """Raised when a requested file does not exist."""

    def __init__(
        self,
        filename: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message or f"File not found: {filename}",
            code="FILE_NOT_FOUND",
            details={"filename": filename, **(details or {})},
        )
        self.filename = filename


class ConversionError(AutoEdgeException):
    """Raised when model conversion fails."""

    def __init__(
        self,
        message: str,
        stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="CONVERSION_ERROR",
            details={"stage": stage, **(details or {})},
        )
        self.stage = stage


class TaskNotFoundError(AutoEdgeException):
    """Raised when a task ID is not found."""

    def __init__(
        self,
        task_id: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"Task not found: {task_id}",
            code="TASK_NOT_FOUND",
            details={"task_id": task_id, **(details or {})},
        )
        self.task_id = task_id
