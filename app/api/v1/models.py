"""
Models Endpoints

Handles model listing and download.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.dependencies import get_file_service
from app.schemas.responses import ModelsListResponse
from app.services.file_service import FileService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/download/{filename}")
async def download_model(
    filename: str,
    file_service: Annotated[FileService, Depends(get_file_service)],
) -> FileResponse:
    """
    Download a converted CoreML model.

    Args:
        filename: The name of the .mlmodel file.

    Returns:
        FileResponse for downloading the converted model.
    """
    logger.info(f"Download requested: {filename}")

    file_path = await file_service.get_model_path(filename)

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
    )


@router.get("/models", response_model=ModelsListResponse)
async def list_models(
    file_service: Annotated[FileService, Depends(get_file_service)],
) -> ModelsListResponse:
    """
    List all converted models available for download.

    Returns:
        ModelsListResponse with list of available model files.
    """
    models = await file_service.list_converted_models()
    return ModelsListResponse(models=models)
