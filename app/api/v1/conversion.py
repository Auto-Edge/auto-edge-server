"""
Conversion Endpoints

Handles model upload, demo conversion, and status tracking with persistence.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    get_conversion_service,
    get_file_service,
    get_db_session,
    get_conversion_repo,
)
from app.schemas.responses import StatusResponse, TaskResponse
from app.schemas.conversion import (
    ConversionResponse,
    ConversionListResponse,
    StartConversionResponse,
)
from app.services.conversion_service import ConversionService
from app.services.file_service import FileService
from app.repositories.sqlite import SQLiteConversionRepository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=StartConversionResponse)
async def upload_model(
    file: Annotated[UploadFile, File(...)],
    file_service: Annotated[FileService, Depends(get_file_service)],
    conversion_service: Annotated[ConversionService, Depends(get_conversion_service)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StartConversionResponse:
    """
    Upload a PyTorch model file and trigger conversion.

    Args:
        file: The uploaded .pt or .pth model file.

    Returns:
        StartConversionResponse with conversion_id and task_id for tracking.
    """
    filename = file.filename or "uploaded_model.pt"
    logger.info(f"Received file upload: {filename}")

    # Validate and save file
    file_path = await file_service.save_upload(filename, file.file)

    # Start conversion task
    task_id = conversion_service.start_conversion(str(file_path))
    logger.info(f"Conversion task triggered: {task_id}")

    # Persist conversion job
    repo = await get_conversion_repo(session)
    conversion = await repo.create(
        task_id=task_id,
        input_filename=filename,
        is_demo=False,
    )

    return StartConversionResponse(
        conversion_id=conversion.id,
        task_id=task_id,
        message=f"File '{filename}' uploaded. Conversion started.",
    )


@router.post("/demo", response_model=StartConversionResponse)
async def demo_conversion(
    conversion_service: Annotated[ConversionService, Depends(get_conversion_service)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StartConversionResponse:
    """
    Trigger a demo conversion using MobileNetV2.

    This endpoint demonstrates the pipeline without requiring a file upload.
    Uses pretrained MobileNetV2 as the source model.

    Returns:
        StartConversionResponse with conversion_id and task_id for tracking.
    """
    task_id = conversion_service.start_demo_conversion()
    logger.info(f"Demo conversion task triggered: {task_id}")

    # Persist conversion job
    repo = await get_conversion_repo(session)
    conversion = await repo.create(
        task_id=task_id,
        input_filename="MobileNetV2 (demo)",
        is_demo=True,
    )

    return StartConversionResponse(
        conversion_id=conversion.id,
        task_id=task_id,
        message="Demo conversion started with MobileNetV2 (pretrained).",
    )


@router.get("/status/{task_id}", response_model=StatusResponse)
async def get_task_status(
    task_id: str,
    conversion_service: Annotated[ConversionService, Depends(get_conversion_service)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StatusResponse:
    """
    Get the status of a conversion task.

    Args:
        task_id: The Celery task ID.

    Returns:
        StatusResponse with current status and result if completed.
    """
    result = conversion_service.get_task_status(task_id)

    # Update persisted conversion status
    repo = await get_conversion_repo(session)
    conversion = await repo.get_by_task_id(task_id)

    if conversion:
        new_status = _map_status(result["status"])
        if conversion.status != new_status:
            await repo.update_status(
                conversion.id,
                new_status,
                result=result.get("result") if result["status"] == "Completed" else None,
                error=result.get("result", {}).get("error") if result["status"] == "Failed" else None,
            )

    return StatusResponse(
        task_id=result["task_id"],
        status=result["status"],
        result=result["result"],
    )


@router.get("/conversions", response_model=ConversionListResponse)
async def list_conversions(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = 20,
) -> ConversionListResponse:
    """
    List recent conversion jobs.

    Returns persisted conversion jobs for resuming after page reload.
    """
    repo = await get_conversion_repo(session)
    conversions = await repo.list_recent(limit)

    return ConversionListResponse(
        conversions=[ConversionResponse.model_validate(c) for c in conversions],
        total=len(conversions),
    )


@router.get("/conversions/active", response_model=ConversionListResponse)
async def list_active_conversions(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ConversionListResponse:
    """
    List active (pending/processing) conversion jobs.

    Returns only jobs that are still running.
    """
    repo = await get_conversion_repo(session)
    conversions = await repo.list_active()

    return ConversionListResponse(
        conversions=[ConversionResponse.model_validate(c) for c in conversions],
        total=len(conversions),
    )


@router.get("/conversions/{conversion_id}", response_model=ConversionResponse)
async def get_conversion(
    conversion_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ConversionResponse:
    """
    Get a specific conversion by ID.
    """
    repo = await get_conversion_repo(session)
    conversion = await repo.get(conversion_id)

    if not conversion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Conversion '{conversion_id}' not found"},
        )

    return ConversionResponse.model_validate(conversion)


@router.delete("/conversions/{conversion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversion(
    conversion_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Delete a conversion job.
    """
    repo = await get_conversion_repo(session)
    deleted = await repo.delete(conversion_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Conversion '{conversion_id}' not found"},
        )


@router.post("/conversions/{conversion_id}/link/{model_id}")
async def link_conversion_to_model(
    conversion_id: str,
    model_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ConversionResponse:
    """
    Link a conversion to a registered model.
    """
    repo = await get_conversion_repo(session)
    conversion = await repo.link_to_model(conversion_id, model_id)

    if not conversion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Conversion '{conversion_id}' not found"},
        )

    return ConversionResponse.model_validate(conversion)


def _map_status(celery_status: str) -> str:
    """Map Celery status to our status."""
    status_map = {
        "Pending": "pending",
        "Processing": "processing",
        "Completed": "completed",
        "Failed": "failed",
    }
    return status_map.get(celery_status, "pending")
