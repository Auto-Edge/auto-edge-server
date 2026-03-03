"""
OTA API Endpoints

Over-the-air model delivery endpoints for device registration,
update checking, and model downloads.
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dependencies import get_db_session, get_model_registry_repo, get_device_repo
from app.services.ota_service import OTAService
from app.schemas.ota import (
    RegisterDeviceRequest,
    DeviceResponse,
    UpdateCheckResponse,
)
from app.core.exceptions import FileNotFoundError

router = APIRouter(prefix="/api/v1/ota")


async def get_ota_service(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OTAService:
    """Get OTA service dependency."""
    device_repo = await get_device_repo(session)
    model_repo = await get_model_registry_repo(session)
    settings = get_settings()

    # Build base URL from request
    base_url = str(request.base_url).rstrip("/")

    return OTAService(
        device_repo=device_repo,
        model_repo=model_repo,
        storage_path=settings.shared_data_path,
        base_url=base_url,
    )


@router.post(
    "/devices/register",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a device",
)
async def register_device(
    request: RegisterDeviceRequest,
    service: Annotated[OTAService, Depends(get_ota_service)],
):
    """
    Register a device for OTA updates.

    - **device_identifier**: Unique identifier for the device
    - **device_type**: Device type (e.g., 'iPhone 15 Pro')
    - **os_version**: OS version (e.g., 'iOS 17.2')

    Returns device info including assigned device ID.
    """
    device = await service.register_device(
        device_identifier=request.device_identifier,
        device_type=request.device_type,
        os_version=request.os_version,
    )
    return DeviceResponse.model_validate(device)


@router.get(
    "/check-update/{model_id}",
    response_model=UpdateCheckResponse,
    summary="Check for model updates",
)
async def check_update(
    model_id: str,
    service: Annotated[OTAService, Depends(get_ota_service)],
    current_version: Optional[str] = None,
    device_identifier: Optional[str] = None,
):
    """
    Check if an update is available for a model.

    - **model_id**: ID of the model to check
    - **current_version**: Current version on device (optional)
    - **device_identifier**: Device identifier for tracking (optional)

    Returns update availability and download URL if available.
    """
    device_id = None
    if device_identifier:
        device = await service.get_device_by_identifier(device_identifier)
        if device:
            device_id = device.id

    return await service.check_for_update(
        model_id=model_id,
        current_version=current_version,
        device_id=device_id,
    )


@router.get(
    "/download/{model_id}/{version}",
    summary="Download a model version",
)
async def download_model(
    model_id: str,
    version: str,
    service: Annotated[OTAService, Depends(get_ota_service)],
):
    """
    Download a specific version of a model.

    - **model_id**: ID of the model
    - **version**: Version to download (e.g., '1.0.0')

    Returns the model file as a binary download.
    """
    try:
        download_info, file_path = await service.get_download_info(model_id, version)

        return FileResponse(
            path=file_path,
            media_type="application/octet-stream",
            filename=f"{model_id}-{download_info.version}.mlpackage",
            headers={
                "X-Model-Version": download_info.version,
                "X-Model-Precision": download_info.precision,
                "X-File-Hash": download_info.file_hash or "",
            },
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": e.message, "filename": e.filename},
        )


@router.get(
    "/download/{model_id}/latest",
    summary="Download the latest model version",
)
async def download_latest_model(
    model_id: str,
    service: Annotated[OTAService, Depends(get_ota_service)],
):
    """
    Download the latest published version of a model.

    - **model_id**: ID of the model

    Returns the model file as a binary download.
    """
    try:
        download_info, file_path = await service.get_download_info(model_id, None)

        return FileResponse(
            path=file_path,
            media_type="application/octet-stream",
            filename=f"{model_id}-{download_info.version}.mlpackage",
            headers={
                "X-Model-Version": download_info.version,
                "X-Model-Precision": download_info.precision,
                "X-File-Hash": download_info.file_hash or "",
            },
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": e.message, "filename": e.filename},
        )
