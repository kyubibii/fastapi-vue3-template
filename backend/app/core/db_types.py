"""SQLAlchemy 类型：MySQL 返回的 naive datetime 规范为 UTC-aware，与 JSON API 中带偏移序列化一致。"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator

from app.core.timezone import utc_from_db_naive


class UtcDateTime(TypeDecorator):
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        return utc_from_db_naive(value)

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
