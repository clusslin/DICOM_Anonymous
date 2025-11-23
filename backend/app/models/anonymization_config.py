"""
Anonymization configuration model for storing tag handling rules
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func

from app.core.database import Base


class AnonymizationConfig(Base):
    """Anonymization configuration presets"""
    __tablename__ = "anonymization_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500), nullable=True)
    is_default = Column(Boolean, default=False)

    # Configuration JSON containing tag handling rules
    # Format: {"tag": {"action": "remove|replace|keep|hash", "value": "replacement_value"}}
    config_json = Column(Text, nullable=False)

    # Created by
    created_by = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Default anonymization tags based on DICOM PS3.15 Annex E
DEFAULT_ANONYMIZATION_TAGS = {
    # Patient Identification
    "PatientName": {"action": "replace", "description": "病人姓名"},
    "PatientID": {"action": "replace", "description": "病人ID"},
    "PatientBirthDate": {"action": "remove", "description": "出生日期"},
    "PatientBirthTime": {"action": "remove", "description": "出生時間"},
    "PatientSex": {"action": "keep", "description": "性別"},
    "PatientAge": {"action": "keep", "description": "年齡"},
    "PatientWeight": {"action": "keep", "description": "體重"},
    "PatientAddress": {"action": "remove", "description": "地址"},
    "PatientTelephoneNumbers": {"action": "remove", "description": "電話號碼"},

    # Patient Demographics
    "EthnicGroup": {"action": "remove", "description": "種族"},
    "Occupation": {"action": "remove", "description": "職業"},
    "AdditionalPatientHistory": {"action": "remove", "description": "額外病史"},

    # Institution Information
    "InstitutionName": {"action": "remove", "description": "機構名稱"},
    "InstitutionAddress": {"action": "remove", "description": "機構地址"},
    "InstitutionalDepartmentName": {"action": "remove", "description": "部門名稱"},
    "StationName": {"action": "remove", "description": "工作站名稱"},

    # Physician Information
    "ReferringPhysicianName": {"action": "remove", "description": "轉介醫師姓名"},
    "ReferringPhysicianAddress": {"action": "remove", "description": "轉介醫師地址"},
    "ReferringPhysicianTelephoneNumbers": {"action": "remove", "description": "轉介醫師電話"},
    "PerformingPhysicianName": {"action": "remove", "description": "執行醫師姓名"},
    "OperatorsName": {"action": "remove", "description": "操作員姓名"},
    "PhysiciansOfRecord": {"action": "remove", "description": "記錄醫師"},
    "NameOfPhysiciansReadingStudy": {"action": "remove", "description": "判讀醫師姓名"},

    # Study Information
    "StudyID": {"action": "hash", "description": "檢查ID"},
    "AccessionNumber": {"action": "hash", "description": "檢驗單號"},
    "StudyDescription": {"action": "keep", "description": "檢查描述"},
    "StudyDate": {"action": "keep", "description": "檢查日期"},
    "StudyTime": {"action": "keep", "description": "檢查時間"},

    # Series Information
    "SeriesDescription": {"action": "keep", "description": "系列描述"},
    "SeriesDate": {"action": "keep", "description": "系列日期"},
    "SeriesTime": {"action": "keep", "description": "系列時間"},
    "ProtocolName": {"action": "keep", "description": "協議名稱"},

    # UIDs (need special handling)
    "StudyInstanceUID": {"action": "hash", "description": "檢查實例UID"},
    "SeriesInstanceUID": {"action": "hash", "description": "系列實例UID"},
    "SOPInstanceUID": {"action": "hash", "description": "SOP實例UID"},
    "FrameOfReferenceUID": {"action": "hash", "description": "參考框架UID"},

    # Device Information
    "DeviceSerialNumber": {"action": "remove", "description": "設備序號"},
    "Manufacturer": {"action": "keep", "description": "製造商"},
    "ManufacturerModelName": {"action": "keep", "description": "設備型號"},

    # Other potentially identifying information
    "OtherPatientIDs": {"action": "remove", "description": "其他病人ID"},
    "OtherPatientNames": {"action": "remove", "description": "其他病人姓名"},
    "MedicalRecordLocator": {"action": "remove", "description": "病歷位置"},
    "RequestingPhysician": {"action": "remove", "description": "申請醫師"},
    "RequestingService": {"action": "remove", "description": "申請服務"},
    "CurrentPatientLocation": {"action": "remove", "description": "目前位置"},
    "PatientInstitutionResidence": {"action": "remove", "description": "病人機構住所"},

    # Private tags
    "PrivateTags": {"action": "remove", "description": "私有標籤"},
}
