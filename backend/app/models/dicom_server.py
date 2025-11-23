"""
DICOM Server configuration model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class DicomServer(Base):
    """DICOM Server configuration model"""
    __tablename__ = "dicom_servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)

    # DICOM connection settings
    ae_title = Column(String(16), nullable=False)  # AE Title (max 16 chars per DICOM standard)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False, default=104)

    # Our local AE title for connection
    local_ae_title = Column(String(16), nullable=False, default="DICOM_ANON")

    # Connection options
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    # TLS settings (optional)
    use_tls = Column(Boolean, default=False)

    # Supported operations
    supports_find = Column(Boolean, default=True)
    supports_move = Column(Boolean, default=True)
    supports_get = Column(Boolean, default=False)

    # Move destination (if using C-MOVE)
    move_destination_ae = Column(String(16), nullable=True)

    # Query/Retrieve level support
    query_retrieve_level = Column(String(20), default="STUDY")  # PATIENT, STUDY, SERIES, IMAGE

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
