"""Pydantic：无时区 datetime 按 APP_TIMEZONE（默认主机本地）解释。"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BeforeValidator

from app.core.timezone import attach_local_tz_if_naive


def _coerce_naive_local(v: object) -> object:
    if isinstance(v, datetime):
        return attach_local_tz_if_naive(v)
    return v


AwareLocalDatetime = Annotated[datetime, BeforeValidator(_coerce_naive_local)]
