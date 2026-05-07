import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DictionaryTypeBase(BaseModel):
    type_code: str = Field(min_length=1, max_length=100)
    type_name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    sort_order: int = 0


class DictionaryTypeCreate(DictionaryTypeBase):
    pass


class DictionaryTypeUpdate(BaseModel):
    type_code: str | None = Field(default=None, min_length=1, max_length=100)
    type_name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    sort_order: int | None = None


class DictionaryTypeListFilter(BaseModel):
    type_code: str | None = None
    type_name: str | None = None


class DictionaryTypePublic(DictionaryTypeBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class DictionaryTypesPublic(BaseModel):
    data: list[DictionaryTypePublic]
    count: int


class DictionaryItemBase(BaseModel):
    item_code: str = Field(min_length=1, max_length=100)
    item_label: str = Field(min_length=1, max_length=200)
    item_value: str = Field(min_length=1, max_length=500)
    sort_order: int = 0
    enabled: bool = True


class DictionaryItemCreate(DictionaryItemBase):
    type_id: uuid.UUID


class DictionaryItemUpdate(BaseModel):
    type_id: uuid.UUID | None = None
    item_code: str | None = Field(default=None, min_length=1, max_length=100)
    item_label: str | None = Field(default=None, min_length=1, max_length=200)
    item_value: str | None = Field(default=None, min_length=1, max_length=500)
    sort_order: int | None = None
    enabled: bool | None = None


class DictionaryItemListFilter(BaseModel):
    type_id: uuid.UUID | None = None
    item_code: str | None = None
    item_label: str | None = None
    enabled: bool | None = None


class DictionaryItemPublic(DictionaryItemBase):
    id: uuid.UUID
    type_id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class DictionaryItemsPublic(BaseModel):
    data: list[DictionaryItemPublic]
    count: int


class DictionaryOptionItemPublic(BaseModel):
    code: str
    label: str
    value: str
    sort_order: int


class DictionaryOptionsPublic(BaseModel):
    type_code: str
    data: list[DictionaryOptionItemPublic]
