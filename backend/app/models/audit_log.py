import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Text
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AuditLog(SQLModel, table=True):
    """
    Immutable record of every non-GET API call.

    Written by AuditLogMiddleware. Never updated or soft-deleted.
    Sensitive fields (passwords, tokens) are sanitized before storage.
    Large request/response bodies are truncated to 10 KB.
    """

    __tablename__ = "audit_log"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Who made the call
    user_id: uuid.UUID | None = Field(default=None, index=True)
    username: str | None = Field(default=None, max_length=50)

    # What was called
    http_method: str = Field(max_length=10)
    endpoint: str = Field(max_length=500)
    module: str | None = Field(default=None, max_length=100, index=True)
    # Human-readable label extracted from route tags, e.g. "Create Item"
    operation: str | None = Field(default=None, max_length=200)

    # Payload (sanitized + truncated)
    request_body: str | None = Field(default=None, sa_column=Column(Text))
    response_body: str | None = Field(default=None, sa_column=Column(Text))

    # Outcome
    status_code: int | None = Field(default=None)
    duration_ms: int | None = Field(default=None)
    error_message: str | None = Field(default=None, max_length=2000)

    # Client info
    ip_address: str | None = Field(default=None, max_length=45)
    user_agent: str | None = Field(default=None, max_length=500)

    # Freeform tags, comma-separated, e.g. "bulk_operation,csv_export"
    tags: str | None = Field(default=None, max_length=200)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), default=_utcnow, index=True, nullable=False)
    )
