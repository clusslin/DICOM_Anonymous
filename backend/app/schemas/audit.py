"""
Audit log Pydantic schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AuditLogResponse(BaseModel):
    """Schema for audit log response"""
    id: int
    action: str
    username: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    description: Optional[str] = None
    request_reason: Optional[str] = None
    extra_data: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Schema for audit log list response"""
    total: int
    logs: List[AuditLogResponse]


class AuditLogFilter(BaseModel):
    """Schema for filtering audit logs"""
    action: Optional[str] = None
    username: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
