"""
System Settings API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import get_admin_user
from app.models.system_setting import SETTING_CATEGORIES
from app.services.settings_service import SettingsService, load_settings_cache
from app.schemas.settings import (
    SettingsResponse,
    SettingUpdate,
    SettingsBatchUpdate,
    SettingsResetRequest,
    CategoriesResponse,
    CategoryInfo,
    SettingCategory
)

router = APIRouter(prefix="/settings", tags=["System Settings"])


@router.get("", response_model=SettingsResponse)
async def get_all_settings(
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all system settings grouped by category (admin only)
    """
    service = SettingsService(db)
    settings = await service.get_all_settings()

    return SettingsResponse(
        categories={
            key: SettingCategory(**value)
            for key, value in settings.items()
        }
    )


@router.get("/categories", response_model=CategoriesResponse)
async def get_categories(
    current_user: dict = Depends(get_admin_user)
):
    """
    Get available setting categories (admin only)
    """
    categories = [
        CategoryInfo(
            key=key,
            name=info["name"],
            icon=info["icon"],
            order=info["order"]
        )
        for key, info in sorted(SETTING_CATEGORIES.items(), key=lambda x: x[1]["order"])
    ]
    return CategoriesResponse(categories=categories)


@router.get("/category/{category}")
async def get_settings_by_category(
    category: str,
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get settings for a specific category (admin only)
    """
    if category not in SETTING_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category '{category}' not found"
        )

    service = SettingsService(db)
    settings = await service.get_settings_by_category(category)

    return {
        "category": category,
        "name": SETTING_CATEGORIES[category]["name"],
        "settings": settings
    }


@router.get("/{key}")
async def get_setting(
    key: str,
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific setting value (admin only)
    """
    service = SettingsService(db)
    value = await service.get_setting(key)

    if value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found"
        )

    return {"key": key, "value": value}


@router.put("/{key}")
async def update_setting(
    key: str,
    data: SettingUpdate,
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a specific setting (admin only)
    """
    service = SettingsService(db)
    success = await service.set_setting(key, data.value, current_user["username"])

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found"
        )

    # Reload cache
    await load_settings_cache(db)

    return {"message": "Setting updated successfully", "key": key, "value": data.value}


@router.put("")
async def update_settings_batch(
    data: SettingsBatchUpdate,
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update multiple settings at once (admin only)
    """
    service = SettingsService(db)
    updated_count = await service.set_settings_batch(data.settings, current_user["username"])

    # Reload cache
    await load_settings_cache(db)

    return {
        "message": f"Updated {updated_count} settings",
        "updated_count": updated_count
    }


@router.post("/reset")
async def reset_settings(
    data: SettingsResetRequest,
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Reset settings to default values (admin only)
    """
    service = SettingsService(db)
    reset_count = await service.reset_to_defaults(data.category)

    # Reload cache
    await load_settings_cache(db)

    category_msg = f" in category '{data.category}'" if data.category else ""
    return {
        "message": f"Reset {reset_count} settings{category_msg} to defaults",
        "reset_count": reset_count
    }


@router.post("/initialize")
async def initialize_settings(
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Initialize default settings (admin only)
    """
    service = SettingsService(db)
    await service.initialize_defaults()

    # Reload cache
    await load_settings_cache(db)

    return {"message": "Settings initialized successfully"}
