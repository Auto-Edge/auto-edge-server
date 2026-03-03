"""
FastAPI Exception Handlers

Centralized error handling for consistent API responses.
"""

import logging
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AutoEdgeException,
    ConversionError,
    FileNotFoundError,
    StorageError,
    ValidationError,
)

logger = logging.getLogger(__name__)


async def autoedge_exception_handler(
    request: Request,
    exc: AutoEdgeException,
) -> JSONResponse:
    """Handle all AutoEdge custom exceptions."""
    logger.warning(f"AutoEdge error: {exc.code} - {exc.message}")

    status_code = _get_status_code(exc)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


def _get_status_code(exc: AutoEdgeException) -> int:
    """Map exception types to HTTP status codes."""
    status_map = {
        ValidationError: 400,
        FileNotFoundError: 404,
        StorageError: 500,
        ConversionError: 500,
    }

    for exc_type, status_code in status_map.items():
        if isinstance(exc, exc_type):
            return status_code

    return 500


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(AutoEdgeException, autoedge_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
