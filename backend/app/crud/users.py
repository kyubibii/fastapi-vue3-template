import uuid
from datetime import UTC, datetime
from typing import Any, cast

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlmodel import select

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDServiceBase
from app.models.rbac import Role, UserRole
from app.models.user import User
from app.schemas.rbac import RoleOptionPublic
from app.schemas.user import (
    UserCreate,
    UserListFilter,
    UserSearchFilter,
    UserUpdate,
)

# Argon2 hash of a random string — used to ensure constant-time response when
# a username doesn't exist, preventing user-enumeration via timing attacks.
_DUMMY_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4"
    "$dGVzdHNhbHRmb3J0aW1pbmc"
    "$MZKWkHHvtyCqVkSr9LB8VqFIRHJqY6lFKM9X6pOWxHI"
)


class UserCRUDService(
    CRUDServiceBase[User, UserCreate, UserUpdate, UserListFilter, uuid.UUID]
):
    model = User
    list_order_by = cast(Any, User.created_at).desc()
    export_order_by = cast(Any, User.created_at).asc()
    export_fields = [
        "id",
        "username",
        "nickname",
        "email",
        "is_active",
        "is_superuser",
        "created_at",
    ]
    export_filename = "users.csv"

    def apply_filters(self, query: Any, filters: UserListFilter | None) -> Any:
        if not filters:
            return query
        if filters.username:
            query = query.where(cast(Any, User.username).contains(filters.username))
        if filters.email:
            query = query.where(cast(Any, User.email).contains(filters.email))
        if filters.is_active is not None:
            query = query.where(User.is_active == filters.is_active)
        if filters.role_ids:
            role_user_ids = select(UserRole.user_id).where(
                cast(Any, UserRole.role_id).in_(filters.role_ids)
            )
            query = query.where(cast(Any, User.id).in_(role_user_ids))
        return query

    async def get_by_id(
        self, *, session: AsyncSession, obj_id: uuid.UUID
    ) -> User | None:
        user = await super().get_by_id(session=session, obj_id=obj_id)
        if not user:
            return None
        users = await _attach_roles_to_users(session=session, users=[user])
        return users[0]

    async def get_multi(
        self,
        *,
        session: AsyncSession,
        filters: UserListFilter | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[User], int]:
        users, count = await super().get_multi(
            session=session,
            filters=filters,
            skip=skip,
            limit=limit,
        )
        users = await _attach_roles_to_users(session=session, users=users)
        return users, count

    def build_create_data(
        self, obj_in: UserCreate, **extra_fields: object
    ) -> dict[str, object]:
        data = obj_in.model_dump(exclude={"password"})
        data["hashed_password"] = get_password_hash(obj_in.password)
        data.update(extra_fields)
        return data

    async def before_create(
        self,
        *,
        session: AsyncSession,
        obj_in: UserCreate,
        create_data: dict[str, object],
    ) -> None:
        existing = await get_user_by_username(session=session, username=obj_in.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{obj_in.username}' already taken",
            )


service = UserCRUDService()


async def _attach_roles_to_users(
    *, session: AsyncSession, users: list[User]
) -> list[User]:
    if not users:
        return users

    user_ids = [user.id for user in users]
    result = await session.execute(
        select(UserRole.user_id, Role.id, Role.name)
        .where(
            cast(Any, Role.id) == UserRole.role_id,
            cast(Any, UserRole.user_id).in_(user_ids),
        )
        .order_by(cast(Any, Role.name).asc())
    )
    role_map: dict[uuid.UUID, list[RoleOptionPublic]] = {user_id: [] for user_id in user_ids}
    for user_id, role_id, role_name in result.all():
        role_map[user_id].append(RoleOptionPublic(id=role_id, name=role_name))

    for user in users:
        object.__setattr__(user, "roles", role_map.get(user.id, []))
    return users


async def get_user_by_id(
    *, session: AsyncSession, user_id: uuid.UUID
) -> User | None:
    user = await service.get_by_id(session=session, obj_id=user_id)
    if not user:
        return None
    users = await _attach_roles_to_users(session=session, users=[user])
    return users[0]


async def get_user_by_username(
    *, session: AsyncSession, username: str
) -> User | None:
    result = await session.execute(
        select(User).where(
            User.username == username,
            cast(Any, User.is_deleted).is_(False),
        )
    )
    return result.scalar_one_or_none()


async def get_users(
    *,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    username: str | None = None,
    email: str | None = None,
    is_active: bool | None = None,
    role_ids: list[int] | None = None,
) -> tuple[list[User], int]:
    filters = UserListFilter(
        username=username,
        email=email,
        is_active=is_active,
        role_ids=role_ids or [],
    )
    users, count = await service.get_multi(
        session=session,
        filters=filters,
        skip=skip,
        limit=limit,
    )
    users = await _attach_roles_to_users(session=session, users=users)
    return users, count


async def create_user(
    *,
    session: AsyncSession,
    user_in: UserCreate,
    created_by: uuid.UUID | None = None,
) -> User:
    return await service.create(
        session=session,
        obj_in=user_in,
        created_by=created_by,
    )


async def update_user(
    *,
    session: AsyncSession,
    db_user: User,
    user_in: UserUpdate,
    updated_by: uuid.UUID | None = None,
) -> User:
    return await service.update(
        session=session,
        db_obj=db_user,
        obj_in=user_in,
        updated_by=updated_by,
    )


async def update_user_password(
    *,
    session: AsyncSession,
    db_user: User,
    new_password: str,
    updated_by: uuid.UUID | None = None,
) -> User:
    db_user.hashed_password = get_password_hash(new_password)
    db_user.updated_at = datetime.now(UTC)
    db_user.updated_by = updated_by
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def soft_delete_user(
    *,
    session: AsyncSession,
    db_user: User,
    deleted_by: uuid.UUID | None = None,
) -> User:
    deleted = await service.delete(
        session=session,
        db_obj=db_user,
        deleted_by=deleted_by,
    )
    if deleted is None:
        raise RuntimeError("User service unexpectedly performed a hard delete")
    return deleted


async def get_all_users_for_export(
    *,
    session: AsyncSession,
    username: str | None = None,
    email: str | None = None,
    is_active: bool | None = None,
    role_ids: list[int] | None = None,
) -> list[User]:
    filters = UserListFilter(
        username=username,
        email=email,
        is_active=is_active,
        role_ids=role_ids or [],
    )
    return await service.get_all_for_export(session=session, filters=filters)


async def search_users(
    *,
    session: AsyncSession,
    filters: UserSearchFilter,
    limit: int = 20,
) -> list[User]:
    query = service.build_base_query()
    if filters.keyword:
        keyword = filters.keyword.strip()
        query = query.where(
            cast(Any, User.username).contains(keyword)
            | cast(Any, User.nickname).contains(keyword)
            | cast(Any, User.email).contains(keyword)
        )
    if filters.exclude_role_id is not None:
        excluded = aliased(UserRole)
        query = query.where(
            ~select(excluded.user_id)
            .where(
                excluded.user_id == User.id,
                excluded.role_id == filters.exclude_role_id,
            )
            .exists()
        )
    result = await session.execute(query.order_by(cast(Any, User.username).asc()).limit(limit))
    users = list(result.scalars().all())
    return await _attach_roles_to_users(session=session, users=users)


def users_to_csv(users: list[User]) -> str:
    return service.export_to_csv(users)


async def authenticate(
    *, session: AsyncSession, username: str, password: str
) -> User | None:
    """
    Authenticate by username + password.

    Always runs password verification even when user doesn't exist,
    ensuring constant response time to prevent username enumeration attacks.

    Also handles transparent password hash upgrades (Bcrypt → Argon2).
    """
    user = await get_user_by_username(session=session, username=username)
    if not user:
        verify_password(password, _DUMMY_HASH)
        return None
    verified, upgraded_hash = verify_password(password, user.hashed_password)
    if not verified:
        return None
    # Upgrade hash algorithm transparently on successful login
    if upgraded_hash:
        user.hashed_password = upgraded_hash
        session.add(user)
        await session.commit()
    return user
