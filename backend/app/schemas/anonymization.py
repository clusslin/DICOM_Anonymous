"""
Anonymization Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TagAction(str, Enum):
    """Action to perform on a DICOM tag"""
    REMOVE = "remove"
    REPLACE = "replace"
    KEEP = "keep"
    HASH = "hash"


class TagConfig(BaseModel):
    """Configuration for a single DICOM tag"""
    action: TagAction
    value: Optional[str] = None
    description: Optional[str] = None


class AnonymizationOptions(BaseModel):
    """Schema for anonymization options"""
    # Standard options as booleans for simple UI
    remove_patient_name: bool = True
    remove_patient_id: bool = True
    remove_birth_date: bool = True
    remove_address: bool = True
    remove_phone: bool = True
    remove_institution: bool = True
    remove_physician: bool = True
    remove_private_tags: bool = True
    keep_study_date: bool = True
    keep_modality: bool = True
    keep_study_description: bool = True
    keep_series_description: bool = True
    hash_uids: bool = True
    hash_accession: bool = True

    # Custom tag configurations (advanced)
    custom_tags: Optional[Dict[str, TagConfig]] = None

    def to_tag_config(self) -> Dict[str, Dict[str, str]]:
        """Convert simple options to detailed tag configuration"""
        config = {}

        if self.remove_patient_name:
            config["PatientName"] = {"action": "replace"}
        if self.remove_patient_id:
            config["PatientID"] = {"action": "replace"}
        if self.remove_birth_date:
            config["PatientBirthDate"] = {"action": "remove"}
            config["PatientBirthTime"] = {"action": "remove"}
        if self.remove_address:
            config["PatientAddress"] = {"action": "remove"}
            config["InstitutionAddress"] = {"action": "remove"}
        if self.remove_phone:
            config["PatientTelephoneNumbers"] = {"action": "remove"}
        if self.remove_institution:
            config["InstitutionName"] = {"action": "remove"}
            config["InstitutionalDepartmentName"] = {"action": "remove"}
            config["StationName"] = {"action": "remove"}
        if self.remove_physician:
            config["ReferringPhysicianName"] = {"action": "remove"}
            config["PerformingPhysicianName"] = {"action": "remove"}
            config["OperatorsName"] = {"action": "remove"}
            config["NameOfPhysiciansReadingStudy"] = {"action": "remove"}
        if self.remove_private_tags:
            config["PrivateTags"] = {"action": "remove"}

        if self.keep_study_date:
            config["StudyDate"] = {"action": "keep"}
            config["StudyTime"] = {"action": "keep"}
        else:
            config["StudyDate"] = {"action": "remove"}
            config["StudyTime"] = {"action": "remove"}

        if self.keep_modality:
            config["Modality"] = {"action": "keep"}
        if self.keep_study_description:
            config["StudyDescription"] = {"action": "keep"}
        if self.keep_series_description:
            config["SeriesDescription"] = {"action": "keep"}

        if self.hash_uids:
            config["StudyInstanceUID"] = {"action": "hash"}
            config["SeriesInstanceUID"] = {"action": "hash"}
            config["SOPInstanceUID"] = {"action": "hash"}
        if self.hash_accession:
            config["AccessionNumber"] = {"action": "hash"}

        # Apply custom tag configurations
        if self.custom_tags:
            for tag_name, tag_config in self.custom_tags.items():
                config[tag_name] = {
                    "action": tag_config.action.value,
                    "value": tag_config.value
                }

        return config


class JobCreate(BaseModel):
    """Schema for creating a single anonymization job"""
    server_id: int
    study_instance_uid: str
    series_instance_uid: Optional[str] = None
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    study_date: Optional[str] = None
    study_description: Optional[str] = None
    modality: Optional[str] = None
    accession_number: Optional[str] = None
    anonymization_options: Optional[AnonymizationOptions] = None
    new_patient_id: Optional[str] = None
    new_patient_name: Optional[str] = None
    request_reason: Optional[str] = Field(None, description="申請理由")


class BatchJobItem(BaseModel):
    """Schema for a single item in a batch job"""
    study_instance_uid: str
    series_instance_uid: Optional[str] = None
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    study_date: Optional[str] = None
    study_description: Optional[str] = None
    modality: Optional[str] = None
    accession_number: Optional[str] = None


class BatchJobCreate(BaseModel):
    """Schema for creating multiple anonymization jobs"""
    server_id: int
    items: List[BatchJobItem]
    anonymization_options: Optional[AnonymizationOptions] = None
    new_patient_id: Optional[str] = None
    new_patient_name: Optional[str] = None
    request_reason: Optional[str] = Field(None, description="申請理由")


class JobStatus(str, Enum):
    """Job status enum for API"""
    PENDING = "pending"
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobResponse(BaseModel):
    """Schema for job response"""
    id: int
    job_uuid: str
    server_id: int
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    study_instance_uid: str
    series_instance_uid: Optional[str] = None
    study_date: Optional[str] = None
    study_description: Optional[str] = None
    modality: Optional[str] = None
    accession_number: Optional[str] = None
    new_patient_id: Optional[str] = None
    new_patient_name: Optional[str] = None
    status: JobStatus
    progress: int
    total_instances: int
    processed_instances: int
    error_message: Optional[str] = None
    output_filename: Optional[str] = None
    created_by: Optional[str] = None
    request_reason: Optional[str] = None
    client_ip: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobStatusUpdate(BaseModel):
    """Schema for job status update"""
    status: Optional[JobStatus] = None
    progress: Optional[int] = Field(None, ge=0, le=100)


class JobListResponse(BaseModel):
    """Schema for job list response"""
    total: int
    jobs: List[JobResponse]


class DefaultAnonymizationTagsResponse(BaseModel):
    """Schema for default anonymization tags response"""
    tags: Dict[str, Dict[str, str]]
