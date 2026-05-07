import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.constants import GenderEnum
from app.schemas.rbac import RoleOptionPublic


class UserBase(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    nickname: str | None = None
    avatar_url: str | None = None
    email: str | None = None
    is_active: bool = True
    is_superuser: bool = False
    gender: GenderEnum | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None
    email: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    gender: GenderEnum | None = None


class UserUpdatePassword(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class UserListFilter(BaseModel):
    username: str | None = None
    email: str | None = None
    is_active: bool | None = None
    role_ids: list[int] = []
    gender: GenderEnum | None = None


class UserSearchFilter(BaseModel):
    keyword: str | None = None
    exclude_role_id: int | None = None


class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime
    roles: list[RoleOptionPublic] = []

    model_config = {"from_attributes": True}


class UserSearchPublic(BaseModel):
    id: uuid.UUID
    username: str
    nickname: str | None
    email: str | None
    roles: list[RoleOptionPublic] = []

    model_config = {"from_attributes": True}


class UserSearchResults(BaseModel):
    data: list[UserSearchPublic]


class UsersPublic(BaseModel):
    data: list[UserPublic]
    count: int
