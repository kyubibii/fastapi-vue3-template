from datetime import datetime
import json

from pydantic import BaseModel, Field, field_validator, model_validator

ALLOWED_SETTING_TYPES = {"string", "int", "bool", "json"}


def validate_setting_value(value: str | None, value_type: str) -> None:
    if value is None:
        return

    if value_type == "string":
        return
    if value_type == "int":
        int(value)
        return
    if value_type == "bool":
        normalized = value.strip().lower()
        if normalized not in {"true", "false", "1", "0", "yes", "no", "on", "off"}:
            raise ValueError("Invalid bool value")
        return
    if value_type == "json":
        json.loads(value)
        return
    raise ValueError(f"Unsupported value_type: {value_type}")


class SettingCreate(BaseModel):
    setting_name: str = Field(min_length=1, max_length=100)
    setting_value: str | None = Field(default=None, max_length=4000)
    setting_group: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    value_type: str = Field(default="string", max_length=20)
    is_sensitive: bool = False
    is_encrypted: bool = False
    is_readonly: bool = False

    @field_validator("value_type")
    @classmethod
    def check_value_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ALLOWED_SETTING_TYPES:
            raise ValueError("value_type must be one of: string,int,bool,json")
        return normalized

    @model_validator(mode="after")
    def check_value_matches_type(self) -> "SettingCreate":
        validate_setting_value(self.setting_value, self.value_type)
        return self


class SettingUpdate(BaseModel):
    setting_value: str | None = Field(default=None, max_length=4000)
    setting_group: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    value_type: str | None = Field(default=None, max_length=20)
    is_sensitive: bool | None = None
    is_encrypted: bool | None = None
    is_readonly: bool | None = None

    @field_validator("value_type")
    @classmethod
    def check_value_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in ALLOWED_SETTING_TYPES:
            raise ValueError("value_type must be one of: string,int,bool,json")
        return normalized


class SettingListFilter(BaseModel):
    setting_name: str | None = None
    setting_group: str | None = None
    is_sensitive: bool | None = None


class SettingPublic(BaseModel):
    id: int
    setting_name: str
    setting_value: str | None
    setting_group: str
    description: str | None
    value_type: str
    is_sensitive: bool
    is_encrypted: bool
    is_readonly: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class SettingsPublic(BaseModel):
    data: list[SettingPublic]
    count: int


class SettingGroupPublic(BaseModel):
    setting_group: str


class SettingGroupsPublic(BaseModel):
    data: list[SettingGroupPublic]