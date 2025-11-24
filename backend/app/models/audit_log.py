"""
Audit log model for tracking user activities
Records downloads, job creations, and other important actions
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class AuditLog(Base):
    """Audit log for tracking user activities"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Action type
    action = Column(String(50), nullable=False, index=True)
    # e.g., "job_created", "job_downloaded", "job_deleted", "login", "logout"

    # User information
    username = Column(String(50), nullable=True, index=True)
    client_ip = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)

    # Related entity
    entity_type = Column(String(50), nullable=True)  # e.g., "job", "server", "user"
    entity_id = Column(String(100), nullable=True)  # job_uuid or other ID

    # Details
    description = Column(Text, nullable=True)
    request_reason = Column(Text, nullable=True)  # 申請理由 (for jobs)

    # Additional data (JSON)
    extra_data = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


# Action constants
class AuditAction:
    """Audit action constants"""
    JOB_CREATED = "job_created"
    JOB_DOWNLOADED = "job_downloaded"
    JOB_DELETED = "job_deleted"
    JOB_CANCELLED = "job_cancelled"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    SETTINGS_CHANGED = "settings_changed"
    SERVER_CREATED = "server_created"
    SERVER_DELETED = "server_deleted"
    USER_CREATED = "user_created"
    USER_DELETED = "user_deleted"
