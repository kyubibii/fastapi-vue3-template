import uuid

from sqlmodel import Field

from app.models.base import AuditBase


class Item(AuditBase, table=True):
    """
    Sample business entity demonstrating AuditBase + soft-delete + CSV export.

    Replace or extend this with your own domain models.
    The owner_id intentionally has no DB-level FK to avoid cascade complexity;
    referential integrity is enforced at the application layer.
    """

    __tablename__ = "item"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(min_length=1, max_length=255, index=True)
    description: str | None = Field(default=None, max_length=1000)
    # Soft reference to user.id — no hard FK constraint
    owner_id: uuid.UUID = Field(index=True)
