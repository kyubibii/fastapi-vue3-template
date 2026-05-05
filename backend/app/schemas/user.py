import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    nickname: str | None = None
    avatar_url: str | None = None
    email: str | None = None
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None
    email: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class UserUpdatePassword(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class UsersPublic(BaseModel):
    data: list[UserPublic]
    count: int
