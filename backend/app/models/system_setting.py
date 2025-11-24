"""
System Settings model for storing configurable parameters
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func

from app.core.database import Base


class SystemSetting(Base):
    """System settings stored in database"""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=True)
    value_type = Column(String(20), nullable=False, default="string")  # string, int, bool, json
    category = Column(String(50), nullable=False, default="general")
    description = Column(String(500), nullable=True)
    is_secret = Column(Boolean, default=False)  # Hide value in responses
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


# Default system settings with their categories and descriptions
DEFAULT_SYSTEM_SETTINGS = {
    # DICOM Settings
    "dicom.local_ae_title": {
        "value": "DICOM_ANON",
        "type": "string",
        "category": "dicom",
        "description": "本地 AE Title（用於 DICOM 通訊）"
    },
    "dicom.listen_port": {
        "value": "11112",
        "type": "int",
        "category": "dicom",
        "description": "DICOM 監聽端口（用於 C-MOVE 接收）"
    },
    "dicom.connection_timeout": {
        "value": "30",
        "type": "int",
        "category": "dicom",
        "description": "DICOM 連線超時時間（秒）"
    },
    "dicom.download_timeout": {
        "value": "300",
        "type": "int",
        "category": "dicom",
        "description": "影像下載超時時間（秒）"
    },

    # Job Settings
    "job.max_concurrent_downloads": {
        "value": "3",
        "type": "int",
        "category": "job",
        "description": "最大同時下載任務數"
    },
    "job.auto_delete_completed_days": {
        "value": "7",
        "type": "int",
        "category": "job",
        "description": "自動刪除已完成任務的天數（0 表示不自動刪除）"
    },
    "job.auto_delete_files": {
        "value": "true",
        "type": "bool",
        "category": "job",
        "description": "刪除任務時是否同時刪除檔案"
    },

    # Anonymization Settings
    "anonymization.default_patient_name": {
        "value": "ANONYMOUS",
        "type": "string",
        "category": "anonymization",
        "description": "預設匿名化病人姓名"
    },
    "anonymization.default_patient_id_prefix": {
        "value": "ANON",
        "type": "string",
        "category": "anonymization",
        "description": "預設匿名化病人 ID 前綴"
    },
    "anonymization.decompress_images": {
        "value": "true",
        "type": "bool",
        "category": "anonymization",
        "description": "是否將壓縮影像解壓縮為非壓縮格式"
    },
    "anonymization.remove_private_tags": {
        "value": "true",
        "type": "bool",
        "category": "anonymization",
        "description": "預設是否移除私有標籤"
    },
    "anonymization.hash_uids": {
        "value": "true",
        "type": "bool",
        "category": "anonymization",
        "description": "預設是否雜湊 UID"
    },
    "anonymization.keep_study_date": {
        "value": "true",
        "type": "bool",
        "category": "anonymization",
        "description": "預設是否保留檢查日期"
    },
    "anonymization.keep_study_description": {
        "value": "true",
        "type": "bool",
        "category": "anonymization",
        "description": "預設是否保留檢查描述"
    },
    "anonymization.keep_series_description": {
        "value": "true",
        "type": "bool",
        "category": "anonymization",
        "description": "預設是否保留系列描述"
    },
    "anonymization.keep_modality": {
        "value": "true",
        "type": "bool",
        "category": "anonymization",
        "description": "預設是否保留檢查類型"
    },

    # Storage Settings
    "storage.temp_directory": {
        "value": "./temp_dicom",
        "type": "string",
        "category": "storage",
        "description": "暫存目錄路徑"
    },
    "storage.output_directory": {
        "value": "./output_dicom",
        "type": "string",
        "category": "storage",
        "description": "輸出目錄路徑"
    },
    "storage.max_storage_gb": {
        "value": "100",
        "type": "int",
        "category": "storage",
        "description": "最大儲存空間限制（GB，0 表示無限制）"
    },

    # Security Settings
    "security.session_timeout_minutes": {
        "value": "1440",
        "type": "int",
        "category": "security",
        "description": "登入 Session 有效時間（分鐘）"
    },
    "security.max_login_attempts": {
        "value": "5",
        "type": "int",
        "category": "security",
        "description": "最大登入嘗試次數（0 表示無限制）"
    },
    "security.lockout_duration_minutes": {
        "value": "15",
        "type": "int",
        "category": "security",
        "description": "帳號鎖定時間（分鐘）"
    },

    # UI Settings
    "ui.default_page_size": {
        "value": "20",
        "type": "int",
        "category": "ui",
        "description": "預設每頁顯示筆數"
    },
    "ui.auto_refresh_interval": {
        "value": "5",
        "type": "int",
        "category": "ui",
        "description": "任務列表自動刷新間隔（秒）"
    },
    "ui.date_format": {
        "value": "YYYY-MM-DD",
        "type": "string",
        "category": "ui",
        "description": "日期顯示格式"
    },
    "ui.datetime_format": {
        "value": "YYYY-MM-DD HH:mm:ss",
        "type": "string",
        "category": "ui",
        "description": "日期時間顯示格式"
    },
}


# Setting categories with display names
SETTING_CATEGORIES = {
    "dicom": {"name": "DICOM 設定", "icon": "Connection", "order": 1},
    "job": {"name": "任務設定", "icon": "List", "order": 2},
    "anonymization": {"name": "匿名化設定", "icon": "Hide", "order": 3},
    "storage": {"name": "儲存設定", "icon": "FolderOpened", "order": 4},
    "security": {"name": "安全設定", "icon": "Lock", "order": 5},
    "ui": {"name": "介面設定", "icon": "Monitor", "order": 6},
}
