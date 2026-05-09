"""应用时区与 datetime 规范化。

- 持久化层约定：业务写入使用 UTC（见各模块 ``utcnow()``）；MySQL 驱动读出的 naive 值按 **UTC** 补上时区信息。
- ``APP_TIMEZONE``：解析 **接口传入的 naive datetime**（无时区字符串）时使用的 IANA 名称；留空则使用 **运行主机本地时区**
  （``datetime.now().astimezone().tzinfo``）。
"""

from __future__ import annotations

from datetime import UTC, datetime
from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.config import settings


@lru_cache
def _cached_zone_from_name(name: str):
    return ZoneInfo(name)


def get_app_timezone():
    """解释 API 侧 naive datetime 时使用的 tzinfo（默认 OS 本地）。"""
    raw = (settings.APP_TIMEZONE or "").strip()
    if raw:
        try:
            return _cached_zone_from_name(raw)
        except ZoneInfoNotFoundError:
            pass
    local = datetime.now().astimezone().tzinfo
    return local if local is not None else UTC


def utc_from_db_naive(dt: datetime | None) -> datetime | None:
    """将 ORM 读出的 naive 时刻视为 UTC，转为 aware。"""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt
    return dt.replace(tzinfo=UTC)


def attach_local_tz_if_naive(dt: datetime) -> datetime:
    """接口 body 中的 naive datetime 视为 APP_TIMEZONE（或 OS 本地）墙钟时间。"""
    if dt.tzinfo is not None:
        return dt
    return dt.replace(tzinfo=get_app_timezone())
