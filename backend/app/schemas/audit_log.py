import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditLogPublic(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    username: str | None
    http_method: str
    endpoint: str
    operation: str | None
    status_code: int | None
    duration_ms: int | None
    ip_address: str | None
    error_message: str | None
    tags: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogsPublic(BaseModel):
    data: list[AuditLogPublic]
    count: int
