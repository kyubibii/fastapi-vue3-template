import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

# Argon2 hash of a random string — used to ensure constant-time response when
# a username doesn't exist, preventing user-enumeration via timing attacks.
_DUMMY_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4"
    "$dGVzdHNhbHRmb3J0aW1pbmc"
    "$MZKWkHHvtyCqVkSr9LB8VqFIRHJqY6lFKM9X6pOWxHI"
)


async def get_user_by_id(
    *, session: AsyncSession, user_id: uuid.UUID
) -> User | None:
    result = await session.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def get_user_by_username(
    *, session: AsyncSession, username: str
) -> User | None:
    result = await session.execute(
        select(User).where(User.username == username, User.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def get_users(
    *, session: AsyncSession, skip: int = 0, limit: int = 100
) -> tuple[list[User], int]:
    base_query = select(User).where(User.deleted_at.is_(None))
    count_result = await session.execute(base_query)
    count = len(count_result.scalars().all())
    result = await session.execute(
        base_query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all()), count


async def create_user(
    *,
    session: AsyncSession,
    user_in: UserCreate,
    created_by: uuid.UUID | None = None,
) -> User:
    user = User(
        username=user_in.username,
        nickname=user_in.nickname,
        avatar_url=user_in.avatar_url,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser,
        created_by=created_by,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_user(
    *,
    session: AsyncSession,
    db_user: User,
    user_in: UserUpdate,
    updated_by: uuid.UUID | None = None,
) -> User:
    update_data = user_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db_user.updated_at = datetime.now(timezone.utc)
    db_user.updated_by = updated_by
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def update_user_password(
    *,
    session: AsyncSession,
    db_user: User,
    new_password: str,
    updated_by: uuid.UUID | None = None,
) -> User:
    db_user.hashed_password = get_password_hash(new_password)
    db_user.updated_at = datetime.now(timezone.utc)
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
    db_user.deleted_at = datetime.now(timezone.utc)
    db_user.deleted_by = deleted_by
    session.add(db_user)
    await session.commit()
    return db_user


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
