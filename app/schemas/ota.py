"""
OTA Schemas

Pydantic models for OTA API requests and responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# Request schemas
class RegisterDeviceRequest(BaseModel):
    """Request to register a device."""

    device_identifier: str = Field(
        ..., min_length=1, max_length=255, description="Unique device identifier"
    )
    device_type: Optional[str] = Field(
        None, max_length=100, description="Device type (e.g., 'iPhone 15 Pro')"
    )
    os_version: Optional[str] = Field(
        None, max_length=50, description="OS version (e.g., 'iOS 17.2')"
    )


# Response schemas
class DeviceResponse(BaseModel):
    """Response for device registration."""

    id: str
    device_identifier: str
    device_type: Optional[str]
    os_version: Optional[str]
    last_seen_at: Optional[datetime]

    class Config:
        from_attributes = True


class UpdateCheckResponse(BaseModel):
    """Response for update check."""

    has_update: bool = Field(..., description="Whether an update is available")
    current_version: Optional[str] = Field(
        None, description="Current version on device (if provided)"
    )
    latest_version: Optional[str] = Field(
        None, description="Latest available version"
    )
    download_url: Optional[str] = Field(
        None, description="URL to download the update"
    )
    file_size_bytes: Optional[int] = Field(
        None, description="Size of the update file"
    )
    file_hash: Optional[str] = Field(
        None, description="SHA256 hash of the file for verification"
    )


class DownloadInfo(BaseModel):
    """Information about a download."""

    model_id: str
    version: str
    file_path: str
    file_size_bytes: Optional[int]
    file_hash: Optional[str]
    precision: str
