"""
Audit logging service
Records user activities for compliance and tracking
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.models.audit_log import AuditLog, AuditAction

logger = logging.getLogger(__name__)


class AuditService:
    """Service for managing audit logs"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        action: str,
        username: str = None,
        client_ip: str = None,
        user_agent: str = None,
        entity_type: str = None,
        entity_id: str = None,
        description: str = None,
        request_reason: str = None,
        extra_data: Dict = None
    ) -> AuditLog:
        """Create an audit log entry"""
        log_entry = AuditLog(
            action=action,
            username=username,
            client_ip=client_ip,
            user_agent=user_agent,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            request_reason=request_reason,
            extra_data=json.dumps(extra_data) if extra_data else None
        )

        self.db.add(log_entry)
        await self.db.commit()
        await self.db.refresh(log_entry)

        logger.info(f"Audit: {action} by {username} from {client_ip} - {description}")
        return log_entry

    async def log_job_created(
        self,
        job_uuid: str,
        username: str,
        client_ip: str,
        request_reason: str,
        study_info: Dict = None,
        user_agent: str = None
    ) -> AuditLog:
        """Log job creation"""
        return await self.log(
            action=AuditAction.JOB_CREATED,
            username=username,
            client_ip=client_ip,
            user_agent=user_agent,
            entity_type="job",
            entity_id=job_uuid,
            description=f"建立匿名化任務",
            request_reason=request_reason,
            extra_data=study_info
        )

    async def log_job_downloaded(
        self,
        job_uuid: str,
        username: str,
        client_ip: str,
        filename: str = None,
        user_agent: str = None
    ) -> AuditLog:
        """Log job file download"""
        return await self.log(
            action=AuditAction.JOB_DOWNLOADED,
            username=username,
            client_ip=client_ip,
            user_agent=user_agent,
            entity_type="job",
            entity_id=job_uuid,
            description=f"下載匿名化檔案: {filename}",
            extra_data={"filename": filename}
        )

    async def get_logs(
        self,
        action: str = None,
        username: str = None,
        entity_type: str = None,
        entity_id: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Get audit logs with filtering"""
        query = select(AuditLog)

        conditions = []
        if action:
            conditions.append(AuditLog.action == action)
        if username:
            conditions.append(AuditLog.username == username)
        if entity_type:
            conditions.append(AuditLog.entity_type == entity_type)
        if entity_id:
            conditions.append(AuditLog.entity_id == entity_id)
        if start_date:
            conditions.append(AuditLog.created_at >= start_date)
        if end_date:
            conditions.append(AuditLog.created_at <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(AuditLog.created_at))
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_job_audit_trail(self, job_uuid: str) -> List[AuditLog]:
        """Get all audit logs for a specific job"""
        return await self.get_logs(entity_type="job", entity_id=job_uuid)

    async def get_user_activity(
        self,
        username: str,
        days: int = 30
    ) -> List[AuditLog]:
        """Get user activity for the past N days"""
        start_date = datetime.utcnow() - timedelta(days=days)
        return await self.get_logs(username=username, start_date=start_date)

    async def count_logs(
        self,
        action: str = None,
        username: str = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> int:
        """Count audit logs matching criteria"""
        from sqlalchemy import func

        query = select(func.count(AuditLog.id))

        conditions = []
        if action:
            conditions.append(AuditLog.action == action)
        if username:
            conditions.append(AuditLog.username == username)
        if start_date:
            conditions.append(AuditLog.created_at >= start_date)
        if end_date:
            conditions.append(AuditLog.created_at <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.db.execute(query)
        return result.scalar()
