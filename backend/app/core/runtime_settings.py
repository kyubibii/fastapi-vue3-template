from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from sqlmodel import select

from app.core.config import settings
from app.core.db import async_session_maker
from app.models.setting import Setting
from app.schemas.setting import validate_setting_value

logger = logging.getLogger(__name__)


@dataclass
class _CacheItem:
    value: str | None
    expires_at: float


def _normalize_key(name: str) -> str:
    return name.strip().lower()


def _to_bool(value: str | bool | int | None, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


class RuntimeSettingsService:
    def __init__(self) -> None:
        self._cache: dict[str, _CacheItem] = {}

    def invalidate(self, setting_name: str) -> None:
        self._cache.pop(_normalize_key(setting_name), None)

    async def get_raw(self, setting_name: str, default: str | None = None) -> str | None:
        key = _normalize_key(setting_name)
        cached = self._cache.get(key)
        now = time.monotonic()
        if cached and cached.expires_at > now:
            return cached.value

        db_value = await self._get_db_value(key)
        if db_value is not None:
            self._cache[key] = _CacheItem(
                value=db_value,
                expires_at=now + settings.RUNTIME_SETTINGS_CACHE_TTL_SECONDS,
            )
            return db_value

        env_value = self._get_env_fallback(setting_name)
        final_value = env_value if env_value is not None else default
        self._cache[key] = _CacheItem(
            value=final_value,
            expires_at=now + settings.RUNTIME_SETTINGS_CACHE_TTL_SECONDS,
        )
        return final_value

    async def get_str(self, setting_name: str, default: str = "") -> str:
        value = await self.get_raw(setting_name, default)
        return default if value is None else value

    async def get_int(self, setting_name: str, default: int = 0) -> int:
        value = await self.get_raw(setting_name)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    async def get_bool(self, setting_name: str, default: bool = False) -> bool:
        value = await self.get_raw(setting_name)
        return _to_bool(value, default)

    async def get_json(self, setting_name: str, default: Any = None) -> Any:
        value = await self.get_raw(setting_name)
        if value is None:
            return default
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default

    async def _get_db_value(self, setting_name: str) -> str | None:
        async with async_session_maker() as session:
            result = await session.execute(
                select(Setting).where(
                    Setting.setting_name == setting_name,
                    Setting.is_deleted.is_(False),
                )
            )
            row = result.scalar_one_or_none()
            return row.setting_value if row else None

    def _get_env_fallback(self, setting_name: str) -> str | None:
        candidates = (setting_name, setting_name.upper())
        for candidate in candidates:
            if hasattr(settings, candidate):
                value = getattr(settings, candidate)
                if value is None:
                    continue
                if isinstance(value, str):
                    return value
                if isinstance(value, bool):
                    return "true" if value else "false"
                return str(value)
        return None


runtime_settings = RuntimeSettingsService()


async def bootstrap_settings_from_env() -> tuple[int, int]:
    if not settings.SETTINGS_BOOTSTRAP_ENABLED:
        return (0, 0)

    defaults = settings.SETTINGS_BOOTSTRAP_ITEMS
    if not defaults:
        return (0, 0)

    inserted = 0
    skipped = 0
    async with async_session_maker() as session:
        for raw_item in defaults:
            name = str(raw_item.get("setting_name", "")).strip().lower()
            group = str(raw_item.get("setting_group", "")).strip().lower()
            if not name or not group:
                logger.warning("Skip invalid bootstrap setting item: %s", raw_item)
                skipped += 1
                continue

            existing = (
                await session.execute(
                    select(Setting).where(Setting.setting_name == name)
                )
            ).scalar_one_or_none()
            if existing:
                skipped += 1
                continue

            value = raw_item.get("setting_value")
            value_str = None if value is None else str(value)
            value_type = str(raw_item.get("value_type", "string")).strip().lower()
            is_sensitive = _to_bool(raw_item.get("is_sensitive"), False)
            is_encrypted = _to_bool(raw_item.get("is_encrypted"), False)
            is_readonly = _to_bool(raw_item.get("is_readonly"), False)
            description = raw_item.get("description")

            try:
                validate_setting_value(value_str, value_type)
            except ValueError:
                logger.warning("Skip invalid bootstrap setting value: %s", raw_item)
                skipped += 1
                continue

            session.add(
                Setting(
                    setting_name=name,
                    setting_group=group,
                    setting_value=value_str,
                    description=None if description is None else str(description),
                    value_type=value_type,
                    is_sensitive=is_sensitive,
                    is_encrypted=is_encrypted,
                    is_readonly=is_readonly,
                )
            )
            inserted += 1

        if inserted:
            await session.commit()

    return (inserted, skipped)