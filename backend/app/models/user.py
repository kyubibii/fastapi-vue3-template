import uuid

from sqlmodel import Field

from app.models.base import AuditBase


class User(AuditBase, table=True):
    """
    Application user.

    Login is by username (not email). Email is optional.
    Roles are linked via UserRole (see rbac.py).
    """

    __tablename__ = "user"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=50)
    nickname: str | None = Field(default=None, max_length=100)
    avatar_url: str | None = Field(default=None, max_length=500)
    email: str | None = Field(default=None, max_length=255, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
