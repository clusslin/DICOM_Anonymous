"""
Anonymization job model for tracking download and anonymization tasks
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class JobStatus(enum.Enum):
    """Job status enum"""
    PENDING = "pending"
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnonymizationJob(Base):
    """Anonymization job model"""
    __tablename__ = "anonymization_jobs"

    id = Column(Integer, primary_key=True, index=True)

    # Job identification
    job_uuid = Column(String(36), unique=True, index=True, nullable=False)

    # Source information
    server_id = Column(Integer, ForeignKey("dicom_servers.id"), nullable=False)
    patient_id = Column(String(64), nullable=True)
    patient_name = Column(String(64), nullable=True)
    study_instance_uid = Column(String(64), nullable=False)
    series_instance_uid = Column(String(64), nullable=True)  # If null, download entire study

    # Study information (cached from query)
    study_date = Column(String(10), nullable=True)
    study_description = Column(String(255), nullable=True)
    modality = Column(String(16), nullable=True)
    accession_number = Column(String(64), nullable=True)

    # Anonymization settings (JSON string)
    anonymization_options = Column(Text, nullable=True)

    # New patient info (after anonymization)
    new_patient_id = Column(String(64), nullable=True)
    new_patient_name = Column(String(64), nullable=True)

    # Job status
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False)
    progress = Column(Integer, default=0)  # 0-100
    total_instances = Column(Integer, default=0)
    processed_instances = Column(Integer, default=0)

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Output file path
    output_path = Column(String(500), nullable=True)
    output_filename = Column(String(255), nullable=True)

    # User who created the job
    created_by = Column(String(50), nullable=True)

    # Audit fields
    request_reason = Column(Text, nullable=True)  # 申請理由
    client_ip = Column(String(45), nullable=True)  # IPv4 or IPv6

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    server = relationship("DicomServer", backref="jobs")
