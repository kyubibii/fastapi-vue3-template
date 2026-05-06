"""
Seed the database with:
  1. Initial superuser
  2. Default permission tree  (groups → pages → permissions)
  3. Builtin 'admin' role with all permissions
  4. Assign admin role to superuser
"""

import asyncio
import logging

from sqlmodel import delete, select

from app.core.config import settings
from app.core.db import async_session_maker
from app.core.permission_tree import BUILTIN_ACTIONS, PERMISSION_TREE
from app.core.security import get_password_hash
from app.models.rbac import (
    Permission,
    PermissionGroup,
    PermissionPage,
    Role,
    RolePermission,
    UserRole,
)
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed() -> None:
    async with async_session_maker() as session:
        # ── 1. Superuser ───────────────────────────────────────────────────────
        existing_superuser = (
            await session.execute(
                select(User).where(User.username == settings.FIRST_SUPERUSER)
            )
        ).scalar_one_or_none()

        if existing_superuser:
            superuser = existing_superuser
            logger.info("Superuser already exists, skipping creation.")
        else:
            superuser = User(
                username=settings.FIRST_SUPERUSER,
                nickname="超级管理员",
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                is_active=True,
                is_superuser=True,
            )
            session.add(superuser)
            await session.commit()
            await session.refresh(superuser)
            logger.info("Superuser '%s' created.", settings.FIRST_SUPERUSER)

        # ── 2. Permission tree ─────────────────────────────────────────────────
        target_permission_codes: set[str] = set()

        for group_name, group_code, group_sort, pages in PERMISSION_TREE:
            # Upsert group by code
            group = (
                await session.execute(
                    select(PermissionGroup).where(PermissionGroup.code == group_code)
                )
            ).scalar_one_or_none()

            if not group:
                group = PermissionGroup(
                    name=group_name, code=group_code, sort_order=group_sort
                )
                session.add(group)
                await session.commit()
                await session.refresh(group)
                logger.info("Created permission group: %s", group_code)
            else:
                should_update_group = (
                    group.name != group_name or group.sort_order != group_sort
                )
                if should_update_group:
                    group.name = group_name
                    group.sort_order = group_sort
                    session.add(group)
                    await session.commit()
                    await session.refresh(group)
                    logger.info("Updated permission group metadata: %s", group_code)

            for page_name, page_code, page_url, page_sort, extra_actions in pages:
                # Upsert page by code
                page = (
                    await session.execute(
                        select(PermissionPage).where(
                            PermissionPage.code == page_code
                        )
                    )
                ).scalar_one_or_none()

                if not page:
                    page = PermissionPage(
                        group_id=group.id,
                        name=page_name,
                        code=page_code,
                        page_url=page_url,
                        sort_order=page_sort,
                    )
                    session.add(page)
                    await session.commit()
                    await session.refresh(page)
                    logger.info("Created permission page: %s.%s", group_code, page_code)
                else:
                    should_update_page = (
                        page.group_id != group.id
                        or page.name != page_name
                        or page.page_url != page_url
                        or page.sort_order != page_sort
                        or page.is_active is False
                    )
                    if should_update_page:
                        page.group_id = group.id  # type: ignore[assignment]
                        page.name = page_name
                        page.page_url = page_url
                        page.sort_order = page_sort
                        page.is_active = True
                        session.add(page)
                        await session.commit()
                        await session.refresh(page)
                        logger.info("Updated permission page metadata: %s.%s", group_code, page_code)

                # Builtin CRUD actions
                for action_name, action_code, is_builtin in BUILTIN_ACTIONS:
                    full_code = f"{group_code}.{page_code}.{action_code}"
                    target_permission_codes.add(full_code)
                    perm = (
                        await session.execute(
                            select(Permission).where(Permission.full_code == full_code)
                        )
                    ).scalar_one_or_none()

                    if not perm:
                        perm = Permission(
                            page_id=page.id,
                            name=f"{action_name}{page_name}",
                            code=action_code,
                            full_code=full_code,
                            is_builtin=is_builtin,
                        )
                        session.add(perm)
                        await session.commit()
                        await session.refresh(perm)
                    else:
                        should_update_perm = (
                            perm.page_id != page.id
                            or perm.name != f"{action_name}{page_name}"
                            or perm.code != action_code
                            or perm.is_builtin is not is_builtin
                        )
                        if should_update_perm:
                            perm.page_id = page.id  # type: ignore[assignment]
                            perm.name = f"{action_name}{page_name}"
                            perm.code = action_code
                            perm.is_builtin = is_builtin
                            session.add(perm)
                            await session.commit()
                            await session.refresh(perm)

                # Extra non-builtin actions
                for extra_code in extra_actions:
                    full_code = f"{group_code}.{page_code}.{extra_code}"
                    target_permission_codes.add(full_code)
                    perm = (
                        await session.execute(
                            select(Permission).where(Permission.full_code == full_code)
                        )
                    ).scalar_one_or_none()

                    if not perm:
                        perm = Permission(
                            page_id=page.id,
                            name=f"{extra_code}{page_name}",
                            code=extra_code,
                            full_code=full_code,
                            is_builtin=False,
                        )
                        session.add(perm)
                        await session.commit()
                        await session.refresh(perm)
                    else:
                        should_update_perm = (
                            perm.page_id != page.id
                            or perm.name != f"{extra_code}{page_name}"
                            or perm.code != extra_code
                            or perm.is_builtin is not False
                        )
                        if should_update_perm:
                            perm.page_id = page.id  # type: ignore[assignment]
                            perm.name = f"{extra_code}{page_name}"
                            perm.code = extra_code
                            perm.is_builtin = False
                            session.add(perm)
                            await session.commit()
                            await session.refresh(perm)

        db_perms = (await session.execute(select(Permission))).scalars().all()
        stale_permission_ids = [
            p.id for p in db_perms if p.full_code not in target_permission_codes and p.id is not None
        ]

        if stale_permission_ids:
            await session.execute(
                delete(RolePermission).where(RolePermission.permission_id.in_(stale_permission_ids))
            )
            await session.execute(
                delete(Permission).where(Permission.id.in_(stale_permission_ids))
            )
            await session.commit()
            logger.info("Deleted stale permissions: %d", len(stale_permission_ids))

        current_permission_ids = list(
            (await session.execute(select(Permission.id))).scalars().all()
        )
        logger.info("Permission tree synced (%d permissions).", len(current_permission_ids))

        # ── 3. Admin role ──────────────────────────────────────────────────────
        admin_role = (
            await session.execute(select(Role).where(Role.code == "admin"))
        ).scalar_one_or_none()

        if not admin_role:
            admin_role = Role(name="管理员", code="admin", is_builtin=True)
            session.add(admin_role)
            await session.commit()
            await session.refresh(admin_role)
            logger.info("Admin role created.")

        # Replace admin role permissions with current full permission set.
        await session.execute(
            delete(RolePermission).where(RolePermission.role_id == admin_role.id)
        )
        for perm_id in current_permission_ids:
            session.add(RolePermission(role_id=admin_role.id, permission_id=perm_id))

        await session.commit()
        logger.info("All permissions assigned to admin role.")

        # ── 4. Assign admin role to superuser ──────────────────────────────────
        user_role_exists = (
            await session.execute(
                select(UserRole).where(
                    UserRole.user_id == superuser.id,
                    UserRole.role_id == admin_role.id,
                )
            )
        ).scalar_one_or_none()

        if not user_role_exists:
            session.add(UserRole(user_id=superuser.id, role_id=admin_role.id))
            await session.commit()
            logger.info("Admin role assigned to superuser.")
        else:
            logger.info("Superuser already has admin role.")


def main() -> None:
    logger.info("Seeding initial data...")
    asyncio.run(seed())
    logger.info("Done.")


if __name__ == "__main__":
    main()
