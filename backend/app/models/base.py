import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


class AuditBase(SQLModel):
    """
    Base mixin providing 7 audit fields for all business tables.

    Columns:
        created_at  — row insertion time (UTC, set once, never updated)
        created_by  — UUID of user who created the row; NULL for system/migration
        updated_at  — last modification time; NULL until first update
        updated_by  — UUID of user who last updated; NULL for automated jobs
        is_deleted  — indexed soft-delete marker; FALSE means the row is alive
        deleted_at  — soft-delete timestamp; NULL means the row is alive
        deleted_by  — UUID of user who deleted; NULL for automated purges

    Usage:
        All queries against soft-deleted models MUST filter:
            WHERE is_deleted = FALSE
    """

    created_at: datetime = Field(  # type: ignore[call-overload]
        default_factory=utcnow,
        sa_type=DateTime(timezone=True),
    )
    created_by: uuid.UUID | None = Field(default=None)

    updated_at: datetime | None = Field(  # type: ignore[call-overload]
        default=None,
        sa_type=DateTime(timezone=True),
    )
    updated_by: uuid.UUID | None = Field(default=None)

    is_deleted: bool = Field(default=False, index=True)

    deleted_at: datetime | None = Field(  # type: ignore[call-overload]
        default=None,
        sa_type=DateTime(timezone=True),
    )
    deleted_by: uuid.UUID | None = Field(default=None)
