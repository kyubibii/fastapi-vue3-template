import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RefreshToken(SQLModel, table=True):
    """
    Persisted refresh tokens for the dual-token auth scheme.

    Storage: only the SHA-256 hash of the raw token is stored (token_hash).
    The raw token travels only over HTTPS in an httpOnly cookie.

    Revocation: set revoked_at to invalidate early (e.g. on logout).
    Rotation: each /auth/refresh call revokes the old token and issues a new one.
    """

    __tablename__ = "refresh_token"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # SHA-256 hex digest of the raw opaque token
    token_hash: str = Field(unique=True, index=True, max_length=64)
    # Stored as a plain UUID; no FK constraint to simplify cascade logic
    user_id: uuid.UUID = Field(index=True)
    expires_at: datetime = Field(
        sa_type=DateTime(timezone=True),  # type: ignore[call-arg]
    )
    revoked_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore[call-arg]
    )
    # Optional: browser / device identifier for session listing
    device_info: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),  # type: ignore[call-arg]
    )
