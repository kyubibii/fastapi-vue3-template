from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_token,
)
from app.crud.users import authenticate
from app.models.auth import RefreshToken
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

_COOKIE_PATH = "/api/v1/auth"
_COOKIE_NAME = "refresh_token"


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path=_COOKIE_PATH,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    response: Response,
    session: SessionDep,
) -> TokenResponse:
    """Authenticate with username + password. Returns access token; sets httpOnly refresh cookie."""
    user = await authenticate(
        session=session, username=body.username, password=body.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    access_token = create_access_token(str(user.id))

    raw_refresh = create_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    session.add(
        RefreshToken(
            token_hash=hash_token(raw_refresh),
            user_id=user.id,
            expires_at=expires_at,
        )
    )
    await session.commit()

    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    session: SessionDep,
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> TokenResponse:
    """Use the httpOnly refresh token cookie to obtain a new access token (token rotation)."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )

    token_hash = hash_token(refresh_token)
    result = await session.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
    )
    db_token = result.scalar_one_or_none()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked refresh token",
        )

    now = datetime.now(timezone.utc)
    token_expiry = db_token.expires_at
    # Make timezone-aware if DB returned naive datetime
    if token_expiry.tzinfo is None:
        from datetime import timezone as tz
        token_expiry = token_expiry.replace(tzinfo=tz.utc)

    if token_expiry < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Revoke old token (rotation)
    db_token.revoked_at = now
    session.add(db_token)

    # Issue new tokens
    new_access = create_access_token(str(db_token.user_id))
    new_raw_refresh = create_refresh_token()
    new_expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    session.add(
        RefreshToken(
            token_hash=hash_token(new_raw_refresh),
            user_id=db_token.user_id,
            expires_at=new_expires_at,
        )
    )
    await session.commit()

    _set_refresh_cookie(response, new_raw_refresh)
    return TokenResponse(access_token=new_access)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    session: SessionDep,
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> dict:
    """Revoke the current refresh token and clear the cookie."""
    if refresh_token:
        token_hash = hash_token(refresh_token)
        result = await session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        db_token = result.scalar_one_or_none()
        if db_token and not db_token.revoked_at:
            db_token.revoked_at = datetime.now(timezone.utc)
            session.add(db_token)
            await session.commit()

    response.delete_cookie(key=_COOKIE_NAME, path=_COOKIE_PATH)
    return {"message": "Logged out successfully"}
