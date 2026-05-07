import uuid

from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from app.models.base import AuditBase


class DictionaryType(AuditBase, table=True):
    __tablename__ = "dictionary_type"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    type_code: str = Field(min_length=1, max_length=100, unique=True, index=True)
    type_name: str = Field(min_length=1, max_length=100, index=True)
    description: str | None = Field(default=None, max_length=500)
    sort_order: int = Field(default=0, index=True)


class DictionaryItem(AuditBase, table=True):
    __tablename__ = "dictionary_item"
    __table_args__ = (
        UniqueConstraint("type_id", "item_code", name="uq_dictionary_item_type_code"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    type_id: uuid.UUID = Field(foreign_key="dictionary_type.id", index=True)
    item_code: str = Field(min_length=1, max_length=100, index=True)
    item_label: str = Field(min_length=1, max_length=200, index=True)
    item_value: str = Field(min_length=1, max_length=500)
    sort_order: int = Field(default=0, index=True)
    enabled: bool = Field(default=True, index=True)
