"""
Registry API Endpoints

Model registry endpoints for creating, listing, and managing models and versions.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dependencies import get_db_session, get_model_registry_repo
from app.repositories.sqlite import SQLiteModelRegistryRepository
from app.services.registry_service import RegistryService
from app.schemas.registry import (
    CreateModelRequest,
    UpdateModelRequest,
    CreateVersionRequest,
    PublishVersionRequest,
    ModelResponse,
    ModelListResponse,
    ModelVersionResponse,
)
from app.core.exceptions import ValidationError, FileNotFoundError

router = APIRouter(prefix="/api/v1/registry")


async def get_registry_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RegistryService:
    """Get registry service dependency."""
    repo = await get_model_registry_repo(session)
    settings = get_settings()
    return RegistryService(repo, settings.shared_data_path)


@router.post(
    "/models",
    response_model=ModelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new model",
)
async def create_model(
    request: CreateModelRequest,
    service: Annotated[RegistryService, Depends(get_registry_service)],
):
    """
    Create a new model in the registry.

    - **name**: Unique name for the model
    - **description**: Optional description
    """
    try:
        model = await service.create_model(request.name, request.description)
        return ModelResponse.model_validate(model)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": e.message, "field": e.field},
        )


@router.get(
    "/models",
    response_model=ModelListResponse,
    summary="List all models",
)
async def list_models(
    service: Annotated[RegistryService, Depends(get_registry_service)],
    active_only: bool = True,
):
    """
    List all models in the registry.

    - **active_only**: If true, only return active models (default: true)
    """
    models = await service.list_models(active_only)
    return ModelListResponse(
        models=[ModelResponse.model_validate(m) for m in models],
        total=len(models),
    )


@router.get(
    "/models/{model_id}",
    response_model=ModelResponse,
    summary="Get a model by ID",
)
async def get_model(
    model_id: str,
    service: Annotated[RegistryService, Depends(get_registry_service)],
):
    """
    Get a specific model by its ID.

    Returns the model with all its versions.
    """
    model = await service.get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Model '{model_id}' not found"},
        )
    return ModelResponse.model_validate(model)


@router.patch(
    "/models/{model_id}",
    response_model=ModelResponse,
    summary="Update a model",
)
async def update_model(
    model_id: str,
    request: UpdateModelRequest,
    service: Annotated[RegistryService, Depends(get_registry_service)],
):
    """
    Update a model's name or description.
    """
    try:
        model = await service.update_model(model_id, request.name, request.description)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": f"Model '{model_id}' not found"},
            )
        return ModelResponse.model_validate(model)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": e.message, "field": e.field},
        )


@router.delete(
    "/models/{model_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a model",
)
async def delete_model(
    model_id: str,
    service: Annotated[RegistryService, Depends(get_registry_service)],
):
    """
    Delete a model (soft delete).

    The model will be marked as inactive but not removed from the database.
    """
    deleted = await service.delete_model(model_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Model '{model_id}' not found"},
        )


@router.post(
    "/models/{model_id}/versions",
    response_model=ModelVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a version to a model",
)
async def create_version(
    model_id: str,
    request: CreateVersionRequest,
    service: Annotated[RegistryService, Depends(get_registry_service)],
):
    """
    Add a new version to a model.

    - **version**: Version string (e.g., '1.0.0')
    - **file_path**: Path to the converted model file (relative to storage)
    - **precision**: Model precision (FLOAT16, FLOAT32, INT8)
    """
    try:
        version = await service.create_version(
            model_id=model_id,
            version=request.version,
            file_path=request.file_path,
            file_size_bytes=request.file_size_bytes,
            file_hash=request.file_hash,
            precision=request.precision,
        )
        return ModelVersionResponse.model_validate(version)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": e.message, "field": e.field},
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": e.message, "filename": e.filename},
        )


@router.patch(
    "/models/{model_id}/versions/{version}",
    response_model=ModelVersionResponse,
    summary="Publish or unpublish a version",
)
async def publish_version(
    model_id: str,
    version: str,
    request: PublishVersionRequest,
    service: Annotated[RegistryService, Depends(get_registry_service)],
):
    """
    Publish or unpublish a model version.

    Published versions are available for OTA delivery to devices.
    """
    updated = await service.publish_version(model_id, version, request.is_published)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Version '{version}' not found for model '{model_id}'"},
        )
    return ModelVersionResponse.model_validate(updated)


@router.get(
    "/models/{model_id}/versions",
    response_model=list[ModelVersionResponse],
    summary="List versions of a model",
)
async def list_versions(
    model_id: str,
    service: Annotated[RegistryService, Depends(get_registry_service)],
    published_only: bool = False,
):
    """
    List all versions of a model.

    - **published_only**: If true, only return published versions
    """
    versions = await service.list_versions(model_id, published_only)
    return [ModelVersionResponse.model_validate(v) for v in versions]
