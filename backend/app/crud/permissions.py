import uuid
from fnmatch import fnmatch

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.rbac import (
    Permission,
    PermissionGroup,
    PermissionPage,
    Role,
    RolePermission,
    UserRole,
)
from app.schemas.rbac import (
    NavigationGroup,
    NavigationPage,
    NavigationPermission,
)


# ── Permission tree queries ────────────────────────────────────────────────────


async def get_all_groups(*, session: AsyncSession) -> list[PermissionGroup]:
    result = await session.execute(
        select(PermissionGroup).order_by(PermissionGroup.sort_order)
    )
    return list(result.scalars().all())


async def get_pages_by_group(
    *, session: AsyncSession, group_id: int
) -> list[PermissionPage]:
    result = await session.execute(
        select(PermissionPage)
        .where(PermissionPage.group_id == group_id, PermissionPage.is_active.is_(True))
        .order_by(PermissionPage.sort_order)
    )
    return list(result.scalars().all())


async def get_permissions_by_page(
    *, session: AsyncSession, page_id: int
) -> list[Permission]:
    result = await session.execute(
        select(Permission).where(Permission.page_id == page_id)
    )
    return list(result.scalars().all())


async def get_permission_by_full_code(
    *, session: AsyncSession, full_code: str
) -> Permission | None:
    result = await session.execute(
        select(Permission).where(Permission.full_code == full_code)
    )
    return result.scalar_one_or_none()


# ── User permission resolution ─────────────────────────────────────────────────


async def get_user_permission_codes(
    *, session: AsyncSession, user_id: uuid.UUID
) -> list[str]:
    """Return all permission full_codes accessible to a user via their roles."""
    role_result = await session.execute(
        select(UserRole.role_id).where(UserRole.user_id == user_id)
    )
    role_ids = list(role_result.scalars().all())
    if not role_ids:
        return []

    perm_result = await session.execute(
        select(RolePermission.permission_id).where(
            RolePermission.role_id.in_(role_ids)
        )
    )
    perm_ids = list(perm_result.scalars().all())
    if not perm_ids:
        return []

    code_result = await session.execute(
        select(Permission.full_code).where(Permission.id.in_(perm_ids))
    )
    return list(code_result.scalars().all())


async def get_user_role_ids(
    *, session: AsyncSession, user_id: uuid.UUID
) -> list[int]:
    result = await session.execute(
        select(UserRole.role_id).where(UserRole.user_id == user_id)
    )
    return list(result.scalars().all())


async def assign_user_roles(
    *, session: AsyncSession, user_id: uuid.UUID, role_ids: list[int]
) -> None:
    """Replace all roles for a user (full overwrite)."""
    existing = await session.execute(
        select(UserRole).where(UserRole.user_id == user_id)
    )
    for ur in existing.scalars().all():
        await session.delete(ur)
    for role_id in role_ids:
        session.add(UserRole(user_id=user_id, role_id=role_id))
    await session.commit()


# ── Permission check ───────────────────────────────────────────────────────────


def check_permission(required: str, user_codes: list[str]) -> bool:
    """
    Check if `required` permission is satisfied by any code in `user_codes`.

    Supports wildcard patterns using fnmatch:
      "*"                → all permissions
      "content.*"        → all content group permissions
      "content.items.*"  → all actions on items page
      "content.items.read" → exact match

    Examples:
      check_permission("content.items.read", ["content.*"])  → True
      check_permission("content.items.read", ["user_mgmt.*"]) → False
    """
    for code in user_codes:
        if code == "*" or code == required or fnmatch(required, code):
            return True
    return False


# ── Navigation builder ─────────────────────────────────────────────────────────


async def get_navigation_for_user(
    *,
    session: AsyncSession,
    user_id: uuid.UUID,
    is_superuser: bool,
) -> list[NavigationGroup]:
    """
    Build the permission-filtered navigation tree for a user.

    Superusers get all pages. Regular users get only pages where they have
    at least one permission. Used by GET /users/me/navigation.
    """
    if is_superuser:
        user_perm_codes: list[str] = ["*"]
    else:
        user_perm_codes = await get_user_permission_codes(
            session=session, user_id=user_id
        )

    groups = await get_all_groups(session=session)
    nav_groups: list[NavigationGroup] = []

    for group in groups:
        pages = await get_pages_by_group(session=session, group_id=group.id)  # type: ignore[arg-type]
        nav_pages: list[NavigationPage] = []

        for page in pages:
            perms = await get_permissions_by_page(session=session, page_id=page.id)  # type: ignore[arg-type]
            nav_perms: list[NavigationPermission] = []

            for perm in perms:
                if is_superuser or check_permission(perm.full_code, user_perm_codes):
                    nav_perms.append(
                        NavigationPermission(
                            id=perm.id,  # type: ignore[arg-type]
                            name=perm.name,
                            code=perm.code,
                            full_code=perm.full_code,
                        )
                    )

            if nav_perms:
                nav_pages.append(
                    NavigationPage(
                        id=page.id,  # type: ignore[arg-type]
                        name=page.name,
                        code=page.code,
                        page_url=page.page_url,
                        sort_order=page.sort_order,
                        permissions=nav_perms,
                    )
                )

        if nav_pages:
            nav_groups.append(
                NavigationGroup(
                    id=group.id,  # type: ignore[arg-type]
                    name=group.name,
                    code=group.code,
                    sort_order=group.sort_order,
                    pages=nav_pages,
                )
            )

    return nav_groups
