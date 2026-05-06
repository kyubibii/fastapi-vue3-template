"""
Seed the database with:
  1. Initial superuser
  2. Default permission tree  (groups → pages → permissions)
  3. Builtin 'admin' role with all permissions
  4. Assign admin role to superuser
"""

import asyncio
import logging

from sqlmodel import select

from app.core.config import settings
from app.core.db import async_session_maker
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

# ── Permission tree definition ─────────────────────────────────────────────────
#
# Format:
#   (group_name, group_code, sort_order, [
#       (page_name, page_code, page_url, sort_order, [extra_action_codes]),
#       ...
#   ])
#
# Each page automatically gets 4 builtin actions: read/create/update/delete.
# Extra actions (e.g. "export") are appended as non-builtin.
_PERM_TREE = [
    (
        "内容管理", "content", 10,
        [
            ("物品管理", "items", "/items", 10, ["export"]),
        ],
    ),
    (
        "用户管理", "user_mgmt", 20,
        [
            ("用户列表", "users", "/users", 10, []),
        ],
    ),
    (
        "系统管理", "system", 30,
        [
            ("操作日志", "audit_logs", "/audit-logs", 10, []),
            ("角色权限", "roles", "/roles", 20, []),
            ("配置项管理", "settings", "/settings", 30, []),
            ("定时任务", "jobs", "/jobs", 40, ["trigger", "manage"]),
        ],
    ),
]

_BUILTIN_ACTIONS: list[tuple[str, str, bool]] = [
    ("读取", "read", True),
    ("创建", "create", True),
    ("更新", "update", True),
    ("删除", "delete", True),
]


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
        all_permission_ids: list[int] = []

        for group_name, group_code, group_sort, pages in _PERM_TREE:
            # Upsert group
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

            for page_name, page_code, page_url, page_sort, extra_actions in pages:
                # Upsert page
                page = (
                    await session.execute(
                        select(PermissionPage).where(
                            PermissionPage.code == page_code,
                            PermissionPage.group_id == group.id,
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
                elif page.page_url != page_url:
                    page.page_url = page_url
                    session.add(page)
                    await session.commit()
                    await session.refresh(page)
                    logger.info(
                        "Updated page_url for permission page: %s.%s -> %s",
                        group_code,
                        page_code,
                        page_url,
                    )

                # Builtin CRUD actions
                for action_name, action_code, is_builtin in _BUILTIN_ACTIONS:
                    full_code = f"{group_code}.{page_code}.{action_code}"
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

                    all_permission_ids.append(perm.id)  # type: ignore[arg-type]

                # Extra non-builtin actions
                for extra_code in extra_actions:
                    full_code = f"{group_code}.{page_code}.{extra_code}"
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

                    all_permission_ids.append(perm.id)  # type: ignore[arg-type]

        logger.info("Permission tree seeded (%d permissions).", len(all_permission_ids))

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

        # Assign all permissions to admin role (idempotent)
        for perm_id in all_permission_ids:
            exists = (
                await session.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == admin_role.id,
                        RolePermission.permission_id == perm_id,
                    )
                )
            ).scalar_one_or_none()
            if not exists:
                session.add(
                    RolePermission(role_id=admin_role.id, permission_id=perm_id)
                )

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
