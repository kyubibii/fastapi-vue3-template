import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.db import async_session_maker
from app.crud.permissions import check_permission, get_user_permission_codes
from app.crud.users import get_user_by_id
from app.models.user import User

# Accepts "Authorization: Bearer <token>" header; returns None if absent
_http_bearer = HTTPBearer(auto_error=False)


# ── Database session ───────────────────────────────────────────────────────────


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db)]


# ── Authentication ─────────────────────────────────────────────────────────────


async def get_current_user(
    session: SessionDep,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_http_bearer)
    ] = None,
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = security.decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = await get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser privileges required",
        )
    return current_user


SuperuserDep = Annotated[User, Depends(get_current_active_superuser)]


# ── RBAC permission check ──────────────────────────────────────────────────────


def permission_required(perm_code: str):
    """
    Dependency factory for RBAC permission checking.

    Usage:
        @router.get("/")
        async def list_items(
            current_user: Annotated[User, Depends(permission_required("content.items.read"))],
        ):

    Supports wildcard codes: "content.*", "content.items.*", "*"
    Superusers always pass regardless of perm_code.
    """

    async def _check(current_user: CurrentUser, session: SessionDep) -> User:
        if current_user.is_superuser:
            return current_user
        codes = await get_user_permission_codes(
            session=session, user_id=current_user.id
        )
        if not check_permission(perm_code, codes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{perm_code}' required",
            )
        return current_user

    return _check
