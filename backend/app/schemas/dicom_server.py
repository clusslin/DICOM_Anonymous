"""
DICOM Server Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DicomServerBase(BaseModel):
    """Base DICOM server schema"""
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    ae_title: str = Field(..., max_length=16)
    host: str = Field(..., max_length=255)
    port: int = Field(default=104, ge=1, le=65535)
    local_ae_title: str = Field(default="DICOM_ANON", max_length=16)
    is_active: bool = True
    is_default: bool = False
    use_tls: bool = False
    supports_find: bool = True
    supports_move: bool = True
    supports_get: bool = False
    move_destination_ae: Optional[str] = Field(None, max_length=16)
    query_retrieve_level: str = Field(default="STUDY", pattern="^(PATIENT|STUDY|SERIES|IMAGE)$")


class DicomServerCreate(DicomServerBase):
    """Schema for creating a DICOM server"""
    pass


class DicomServerUpdate(BaseModel):
    """Schema for updating a DICOM server"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    ae_title: Optional[str] = Field(None, max_length=16)
    host: Optional[str] = Field(None, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)
    local_ae_title: Optional[str] = Field(None, max_length=16)
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    use_tls: Optional[bool] = None
    supports_find: Optional[bool] = None
    supports_move: Optional[bool] = None
    supports_get: Optional[bool] = None
    move_destination_ae: Optional[str] = Field(None, max_length=16)
    query_retrieve_level: Optional[str] = Field(None, pattern="^(PATIENT|STUDY|SERIES|IMAGE)$")


class DicomServerResponse(DicomServerBase):
    """Schema for DICOM server response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConnectionTestResult(BaseModel):
    """Schema for connection test result"""
    success: bool
    message: str
    status_code: Optional[int] = None
