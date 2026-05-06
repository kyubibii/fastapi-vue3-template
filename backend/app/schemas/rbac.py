from pydantic import BaseModel, Field

# ── Permission Tree ────────────────────────────────────────────────────────────


class PermissionGroupCreate(BaseModel):
    name: str = Field(max_length=100)
    code: str = Field(max_length=50)
    description: str | None = None
    sort_order: int = 0


class PermissionPageCreate(BaseModel):
    group_id: int
    name: str = Field(max_length=100)
    code: str = Field(max_length=50)
    page_url: str | None = None
    description: str | None = None
    sort_order: int = 0


class PermissionPublic(BaseModel):
    id: int
    name: str
    code: str
    full_code: str
    is_builtin: bool

    model_config = {"from_attributes": True}


class PermissionPagePublic(BaseModel):
    id: int
    name: str
    code: str
    page_url: str | None
    sort_order: int
    permissions: list[PermissionPublic] = []

    model_config = {"from_attributes": True}


class PermissionGroupPublic(BaseModel):
    id: int
    name: str
    code: str
    sort_order: int
    pages: list[PermissionPagePublic] = []

    model_config = {"from_attributes": True}


class PermissionTreeResponse(BaseModel):
    groups: list[PermissionGroupPublic]


# ── Role ───────────────────────────────────────────────────────────────────────


class RoleCreate(BaseModel):
    name: str = Field(max_length=100)
    code: str = Field(max_length=50)
    description: str | None = None


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class RolePublic(BaseModel):
    id: int
    name: str
    code: str
    description: str | None
    is_builtin: bool

    model_config = {"from_attributes": True}


class RolesPublic(BaseModel):
    data: list[RolePublic]
    count: int


class RoleOptionPublic(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class AssignRolePermissions(BaseModel):
    """Replaces all current permissions on a role."""
    permission_ids: list[int]


class AssignUserRoles(BaseModel):
    """Replaces all current roles for a user."""
    role_ids: list[int]


class AssignRoleUsers(BaseModel):
    """Replaces all current users assigned to a role."""
    user_ids: list[str]


# ── Navigation (user-specific view of permission tree) ─────────────────────────


class NavigationPermission(BaseModel):
    id: int
    name: str
    code: str
    full_code: str


class NavigationPage(BaseModel):
    id: int
    name: str
    code: str
    page_url: str | None
    sort_order: int
    permissions: list[NavigationPermission]


class NavigationGroup(BaseModel):
    id: int
    name: str
    code: str
    sort_order: int
    pages: list[NavigationPage]


class NavigationResponse(BaseModel):
    groups: list[NavigationGroup]
