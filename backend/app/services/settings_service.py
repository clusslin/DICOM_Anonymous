"""
System Settings Service
Handles reading and writing system settings from database
"""
import json
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.system_setting import SystemSetting, DEFAULT_SYSTEM_SETTINGS, SETTING_CATEGORIES

logger = logging.getLogger(__name__)


class SettingsService:
    """Service for managing system settings"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._cache: Dict[str, Any] = {}

    async def initialize_defaults(self) -> None:
        """Initialize default settings if they don't exist"""
        for key, config in DEFAULT_SYSTEM_SETTINGS.items():
            result = await self.db.execute(
                select(SystemSetting).where(SystemSetting.key == key)
            )
            existing = result.scalar_one_or_none()

            if not existing:
                setting = SystemSetting(
                    key=key,
                    value=config["value"],
                    value_type=config["type"],
                    category=config["category"],
                    description=config["description"]
                )
                self.db.add(setting)

        await self.db.commit()

    async def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a single setting value"""
        result = await self.db.execute(
            select(SystemSetting).where(SystemSetting.key == key)
        )
        setting = result.scalar_one_or_none()

        if not setting:
            # Return from defaults if not in database
            if key in DEFAULT_SYSTEM_SETTINGS:
                return self._convert_value(
                    DEFAULT_SYSTEM_SETTINGS[key]["value"],
                    DEFAULT_SYSTEM_SETTINGS[key]["type"]
                )
            return default

        return self._convert_value(setting.value, setting.value_type)

    async def get_settings_by_category(self, category: str) -> Dict[str, Any]:
        """Get all settings in a category"""
        result = await self.db.execute(
            select(SystemSetting).where(SystemSetting.category == category)
        )
        settings = result.scalars().all()

        return {
            s.key: {
                "value": self._convert_value(s.value, s.value_type),
                "type": s.value_type,
                "description": s.description,
                "is_secret": s.is_secret
            }
            for s in settings
        }

    async def get_all_settings(self) -> Dict[str, Dict[str, Any]]:
        """Get all settings grouped by category"""
        result = await self.db.execute(select(SystemSetting))
        settings = result.scalars().all()

        # Group by category
        grouped = {}
        for setting in settings:
            if setting.category not in grouped:
                grouped[setting.category] = {
                    "name": SETTING_CATEGORIES.get(setting.category, {}).get("name", setting.category),
                    "icon": SETTING_CATEGORIES.get(setting.category, {}).get("icon", "Setting"),
                    "order": SETTING_CATEGORIES.get(setting.category, {}).get("order", 99),
                    "settings": []
                }

            grouped[setting.category]["settings"].append({
                "key": setting.key,
                "value": "" if setting.is_secret else self._convert_value(setting.value, setting.value_type),
                "type": setting.value_type,
                "description": setting.description,
                "is_secret": setting.is_secret
            })

        # Sort categories by order
        return dict(sorted(grouped.items(), key=lambda x: x[1]["order"]))

    async def set_setting(self, key: str, value: Any, updated_by: str = None) -> bool:
        """Set a single setting value"""
        result = await self.db.execute(
            select(SystemSetting).where(SystemSetting.key == key)
        )
        setting = result.scalar_one_or_none()

        if not setting:
            # Create new setting if in defaults
            if key in DEFAULT_SYSTEM_SETTINGS:
                config = DEFAULT_SYSTEM_SETTINGS[key]
                setting = SystemSetting(
                    key=key,
                    value=self._to_string(value, config["type"]),
                    value_type=config["type"],
                    category=config["category"],
                    description=config["description"],
                    updated_by=updated_by
                )
                self.db.add(setting)
            else:
                return False
        else:
            setting.value = self._to_string(value, setting.value_type)
            setting.updated_by = updated_by

        await self.db.commit()
        return True

    async def set_settings_batch(self, settings: Dict[str, Any], updated_by: str = None) -> int:
        """Set multiple settings at once"""
        updated_count = 0
        for key, value in settings.items():
            if await self.set_setting(key, value, updated_by):
                updated_count += 1
        return updated_count

    async def reset_to_defaults(self, category: str = None) -> int:
        """Reset settings to default values"""
        reset_count = 0

        for key, config in DEFAULT_SYSTEM_SETTINGS.items():
            if category and config["category"] != category:
                continue

            result = await self.db.execute(
                select(SystemSetting).where(SystemSetting.key == key)
            )
            setting = result.scalar_one_or_none()

            if setting:
                setting.value = config["value"]
                reset_count += 1

        await self.db.commit()
        return reset_count

    def _convert_value(self, value: str, value_type: str) -> Any:
        """Convert string value to appropriate type"""
        if value is None:
            return None

        try:
            if value_type == "int":
                return int(value)
            elif value_type == "bool":
                return value.lower() in ("true", "1", "yes")
            elif value_type == "json":
                return json.loads(value)
            else:
                return value
        except (ValueError, json.JSONDecodeError):
            return value

    def _to_string(self, value: Any, value_type: str) -> str:
        """Convert value to string for storage"""
        if value_type == "bool":
            return "true" if value else "false"
        elif value_type == "json":
            return json.dumps(value)
        else:
            return str(value)


# Singleton-like access for getting settings without async context
_settings_cache: Dict[str, Any] = {}


async def load_settings_cache(db: AsyncSession) -> None:
    """Load all settings into cache"""
    global _settings_cache
    service = SettingsService(db)
    result = await db.execute(select(SystemSetting))
    settings = result.scalars().all()

    for setting in settings:
        _settings_cache[setting.key] = service._convert_value(setting.value, setting.value_type)

    # Add defaults for missing keys
    for key, config in DEFAULT_SYSTEM_SETTINGS.items():
        if key not in _settings_cache:
            _settings_cache[key] = service._convert_value(config["value"], config["type"])


def get_cached_setting(key: str, default: Any = None) -> Any:
    """Get setting from cache (sync)"""
    return _settings_cache.get(key, default)
