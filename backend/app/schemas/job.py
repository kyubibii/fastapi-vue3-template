from __future__ import annotations

import datetime

from pydantic import BaseModel


class JobPublic(BaseModel):
    id: str
    name: str
    description: str
    trigger_type: str
    trigger_description: str
    next_run_time: datetime.datetime | None
    is_paused: bool


class JobsPublic(BaseModel):
    data: list[JobPublic]


class JobTriggerResult(BaseModel):
    job_id: str
    message: str
    triggered_at: datetime.datetime
