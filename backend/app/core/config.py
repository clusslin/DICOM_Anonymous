"""
Application configuration settings
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "DICOM Anonymization Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./dicom_anon.db"

    # Security
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Default admin credentials (change in production)
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"

    # DICOM settings
    DICOM_AE_TITLE: str = "DICOM_ANON"
    DICOM_PORT: int = 11112
    DICOM_TEMP_DIR: str = "./temp_dicom"
    DICOM_OUTPUT_DIR: str = "./output_dicom"

    # Download settings
    MAX_CONCURRENT_DOWNLOADS: int = 3
    DOWNLOAD_TIMEOUT: int = 300  # seconds

    # Anonymization default settings
    DEFAULT_REPLACEMENT_NAME: str = "ANONYMOUS"
    DEFAULT_REPLACEMENT_ID: str = "000000"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Ensure directories exist
os.makedirs(settings.DICOM_TEMP_DIR, exist_ok=True)
os.makedirs(settings.DICOM_OUTPUT_DIR, exist_ok=True)
