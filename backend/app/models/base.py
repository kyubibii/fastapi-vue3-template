import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditBase(SQLModel):
    """
    Base mixin providing 6 audit fields for all business tables.

    Columns:
        created_at  — row insertion time (UTC, set once, never updated)
        created_by  — UUID of user who created the row; NULL for system/migration
        updated_at  — last modification time; NULL until first update
        updated_by  — UUID of user who last updated; NULL for automated jobs
        deleted_at  — soft-delete timestamp; NULL means the row is alive
        deleted_by  — UUID of user who deleted; NULL for automated purges

    Usage:
        All queries against soft-deleted models MUST filter:
            WHERE deleted_at IS NULL
    """

    created_at: datetime = Field(
        default_factory=utcnow,
        sa_type=DateTime(timezone=True),  # type: ignore[call-arg]
    )
    created_by: uuid.UUID | None = Field(default=None)

    updated_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore[call-arg]
    )
    updated_by: uuid.UUID | None = Field(default=None)

    deleted_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore[call-arg]
    )
    deleted_by: uuid.UUID | None = Field(default=None)
