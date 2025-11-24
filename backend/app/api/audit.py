"""
Audit Log API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogResponse, AuditLogListResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    action: Optional[str] = None,
    username: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    List audit logs (admin only)
    """
    audit_service = AuditService(db)

    logs = await audit_service.get_logs(
        action=action,
        username=username,
        entity_type=entity_type,
        entity_id=entity_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )

    # Get total count
    total = await audit_service.count_logs(
        action=action,
        username=username,
        start_date=start_date,
        end_date=end_date
    )

    return AuditLogListResponse(
        total=total,
        logs=logs
    )


@router.get("/job/{job_uuid}", response_model=list[AuditLogResponse])
async def get_job_audit_trail(
    job_uuid: str,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get audit trail for a specific job (admin only)
    """
    audit_service = AuditService(db)
    logs = await audit_service.get_job_audit_trail(job_uuid)
    return logs


@router.get("/user/{username}", response_model=list[AuditLogResponse])
async def get_user_activity(
    username: str,
    days: int = Query(default=30, le=365),
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user activity for the past N days (admin only)
    """
    audit_service = AuditService(db)
    logs = await audit_service.get_user_activity(username, days)
    return logs


@router.get("/actions", response_model=list[str])
async def get_audit_actions(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of distinct audit actions
    """
    result = await db.execute(
        select(AuditLog.action).distinct().order_by(AuditLog.action)
    )
    return [row[0] for row in result.fetchall()]
