from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.rbac import Role, RolePermission
from app.schemas.rbac import RoleCreate, RoleUpdate


async def get_roles(
    *, session: AsyncSession, skip: int = 0, limit: int = 100
) -> tuple[list[Role], int]:
    result = await session.execute(select(Role))
    all_roles = list(result.scalars().all())
    count = len(all_roles)
    result2 = await session.execute(select(Role).offset(skip).limit(limit))
    return list(result2.scalars().all()), count


async def get_role_by_id(*, session: AsyncSession, role_id: int) -> Role | None:
    return await session.get(Role, role_id)


async def get_role_by_code(*, session: AsyncSession, code: str) -> Role | None:
    result = await session.execute(select(Role).where(Role.code == code))
    return result.scalar_one_or_none()


async def create_role(*, session: AsyncSession, role_in: RoleCreate) -> Role:
    role = Role(
        name=role_in.name,
        code=role_in.code,
        description=role_in.description,
    )
    session.add(role)
    await session.commit()
    await session.refresh(role)
    return role


async def update_role(
    *, session: AsyncSession, db_role: Role, role_in: RoleUpdate
) -> Role:
    for key, value in role_in.model_dump(exclude_unset=True).items():
        setattr(db_role, key, value)
    session.add(db_role)
    await session.commit()
    await session.refresh(db_role)
    return db_role


async def delete_role(*, session: AsyncSession, db_role: Role) -> None:
    # Also clean up link table rows
    existing = await session.execute(
        select(RolePermission).where(RolePermission.role_id == db_role.id)
    )
    for rp in existing.scalars().all():
        await session.delete(rp)
    await session.delete(db_role)
    await session.commit()


async def assign_role_permissions(
    *, session: AsyncSession, role_id: int, permission_ids: list[int]
) -> None:
    """Replace all permissions on a role (full overwrite)."""
    existing = await session.execute(
        select(RolePermission).where(RolePermission.role_id == role_id)
    )
    for rp in existing.scalars().all():
        await session.delete(rp)
    for perm_id in permission_ids:
        session.add(RolePermission(role_id=role_id, permission_id=perm_id))
    await session.commit()


async def get_role_permission_ids(
    *, session: AsyncSession, role_id: int
) -> list[int]:
    result = await session.execute(
        select(RolePermission.permission_id).where(RolePermission.role_id == role_id)
    )
    return list(result.scalars().all())
