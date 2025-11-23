"""
DICOM Query Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class PatientQuery(BaseModel):
    """Schema for patient query parameters"""
    patient_name: Optional[str] = Field(None, description="Patient name (supports wildcards *)")
    patient_id: Optional[str] = Field(None, description="Patient ID")
    birth_date: Optional[str] = Field(None, description="Birth date (YYYYMMDD)")


class StudyQuery(BaseModel):
    """Schema for study query parameters"""
    patient_name: Optional[str] = Field(None, description="Patient name (supports wildcards *)")
    patient_id: Optional[str] = Field(None, description="Patient ID")
    study_date: Optional[str] = Field(None, description="Study date (YYYYMMDD)")
    study_date_from: Optional[str] = Field(None, description="Study date range start (YYYYMMDD)")
    study_date_to: Optional[str] = Field(None, description="Study date range end (YYYYMMDD)")
    modality: Optional[str] = Field(None, description="Modality (CT, MR, CR, etc.)")
    accession_number: Optional[str] = Field(None, description="Accession number")
    study_description: Optional[str] = Field(None, description="Study description")


class PatientResult(BaseModel):
    """Schema for patient query result"""
    PatientName: str
    PatientID: str
    PatientBirthDate: str
    PatientSex: str
    NumberOfPatientRelatedStudies: str


class StudyResult(BaseModel):
    """Schema for study query result"""
    PatientName: str
    PatientID: str
    PatientBirthDate: str
    PatientSex: str
    StudyInstanceUID: str
    StudyDate: str
    StudyTime: str
    StudyDescription: str
    AccessionNumber: str
    StudyID: str
    ModalitiesInStudy: str
    NumberOfStudyRelatedSeries: str
    NumberOfStudyRelatedInstances: str


class SeriesResult(BaseModel):
    """Schema for series query result"""
    SeriesInstanceUID: str
    SeriesNumber: str
    SeriesDescription: str
    SeriesDate: str
    SeriesTime: str
    Modality: str
    BodyPartExamined: str
    NumberOfSeriesRelatedInstances: str
    ProtocolName: str


class StudyWithSeriesResult(StudyResult):
    """Schema for study with series information"""
    series: List[SeriesResult] = []


class QueryResponse(BaseModel):
    """Schema for query response"""
    success: bool
    count: int
    results: List[dict]
    message: Optional[str] = None
