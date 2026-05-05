import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Permission Tree ────────────────────────────────────────────────────────────
#   PermissionGroup  →  PermissionPage  →  Permission
#   "content"           "items"             "content.items.read"
# ─────────────────────────────────────────────────────────────────────────────


class PermissionGroup(SQLModel, table=True):
    """Top-level grouping of pages, e.g. '内容管理', '用户管理'."""

    __tablename__ = "permission_group"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    code: str = Field(max_length=50, unique=True, index=True)
    description: str | None = Field(default=None, max_length=500)
    sort_order: int = Field(default=0)


class PermissionPage(SQLModel, table=True):
    """A page/resource within a group, e.g. '物品列表' under '内容管理'."""

    __tablename__ = "permission_page"

    id: int | None = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="permission_group.id")
    name: str = Field(max_length=100)
    # Short code used to build full_code, e.g. "items"
    code: str = Field(max_length=50, index=True)
    # Frontend route path, e.g. "/items". Used to build the sidebar nav.
    page_url: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    sort_order: int = Field(default=0)
    is_active: bool = Field(default=True)


class Permission(SQLModel, table=True):
    """
    Leaf-level permission node.

    full_code format: "{group_code}.{page_code}.{action}"
    Examples: "content.items.read", "user_mgmt.users.create"

    Builtin permissions (is_builtin=True) are auto-created when a page is added
    and cannot be deleted.
    """

    __tablename__ = "permission"

    id: int | None = Field(default=None, primary_key=True)
    page_id: int = Field(foreign_key="permission_page.id")
    name: str = Field(max_length=100)
    # Action code, e.g. "read", "create", "update", "delete", "export"
    code: str = Field(max_length=50)
    # Globally unique dotted code, e.g. "content.items.read"
    full_code: str = Field(max_length=150, unique=True, index=True)
    is_builtin: bool = Field(default=False)
    description: str | None = Field(default=None, max_length=500)


# ── Role ───────────────────────────────────────────────────────────────────────


class Role(SQLModel, table=True):
    """Named collection of permissions assigned to users."""

    __tablename__ = "role"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    code: str = Field(max_length=50, unique=True, index=True)
    description: str | None = Field(default=None, max_length=500)
    # Builtin roles (e.g. "admin") cannot be deleted
    is_builtin: bool = Field(default=False)


# ── Many-to-many link tables ───────────────────────────────────────────────────


class RolePermission(SQLModel, table=True):
    """Role ←many-to-many→ Permission"""

    __tablename__ = "role_permission"

    role_id: int = Field(foreign_key="role.id", primary_key=True)
    permission_id: int = Field(foreign_key="permission.id", primary_key=True)


class UserRole(SQLModel, table=True):
    """User ←many-to-many→ Role"""

    __tablename__ = "user_role"

    user_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True)
    role_id: int = Field(foreign_key="role.id", primary_key=True)
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),  # type: ignore[call-arg]
    )
