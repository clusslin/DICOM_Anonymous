"""
System Settings Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class SettingValue(BaseModel):
    """Single setting value"""
    key: str
    value: Any
    type: str
    description: Optional[str] = None
    is_secret: bool = False


class SettingCategory(BaseModel):
    """Settings category with settings list"""
    name: str
    icon: str
    order: int
    settings: List[SettingValue]


class SettingsResponse(BaseModel):
    """Response with all settings grouped by category"""
    categories: Dict[str, SettingCategory]


class SettingUpdate(BaseModel):
    """Update a single setting"""
    value: Any


class SettingsBatchUpdate(BaseModel):
    """Update multiple settings at once"""
    settings: Dict[str, Any] = Field(..., description="Key-value pairs of settings to update")


class SettingsResetRequest(BaseModel):
    """Request to reset settings"""
    category: Optional[str] = Field(None, description="Category to reset, or None for all")


class CategoryInfo(BaseModel):
    """Category information"""
    key: str
    name: str
    icon: str
    order: int


class CategoriesResponse(BaseModel):
    """Response with available categories"""
    categories: List[CategoryInfo]
