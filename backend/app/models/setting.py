from sqlmodel import Field

from app.models.base import AuditBase


class Setting(AuditBase, table=True):
    __tablename__ = "setting"

    id: int | None = Field(default=None, primary_key=True)
    setting_name: str = Field(min_length=1, max_length=100, unique=True, index=True)
    setting_value: str | None = Field(default=None, max_length=4000)
    setting_group: str = Field(min_length=1, max_length=50, index=True)
    description: str | None = Field(default=None, max_length=500)
    value_type: str = Field(default="string", max_length=20)
    is_sensitive: bool = Field(default=False)
    is_encrypted: bool = Field(default=False)
    is_readonly: bool = Field(default=False)