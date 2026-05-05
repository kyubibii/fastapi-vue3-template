import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, SessionDep, SuperuserDep, permission_required
from app.crud import permissions as perm_crud
from app.crud import users as users_crud
from app.schemas.rbac import AssignUserRoles, NavigationResponse
from app.schemas.user import UserCreate, UserPublic, UsersPublic, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: CurrentUser) -> UserPublic:
    """Return the authenticated user's profile."""
    return UserPublic.model_validate(current_user, from_attributes=True)


@router.get("/me/navigation", response_model=NavigationResponse)
async def get_my_navigation(
    current_user: CurrentUser,
    session: SessionDep,
) -> NavigationResponse:
    """
    Return the permission-filtered navigation tree for the current user.

    The frontend uses this response to:
    - Render the sidebar menu (groups → pages)
    - Gate button visibility (page.permissions[].full_code)
    """
    groups = await perm_crud.get_navigation_for_user(
        session=session,
        user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    return NavigationResponse(groups=groups)


@router.get("/", response_model=UsersPublic)
async def list_users(
    session: SessionDep,
    _: Annotated[None, Depends(permission_required("user_mgmt.users.read"))],
    skip: int = 0,
    limit: int = 100,
) -> UsersPublic:
    users, count = await users_crud.get_users(session=session, skip=skip, limit=limit)
    return UsersPublic(
        data=[UserPublic.model_validate(u, from_attributes=True) for u in users],
        count=count,
    )


@router.post("/", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_user(
    session: SessionDep,
    body: UserCreate,
    current_user: Annotated[
        None, Depends(permission_required("user_mgmt.users.create"))
    ],
) -> UserPublic:
    existing = await users_crud.get_user_by_username(
        session=session, username=body.username
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{body.username}' already taken",
        )
    creator_id = current_user.id if hasattr(current_user, "id") else None  # type: ignore[union-attr]
    user = await users_crud.create_user(
        session=session, user_in=body, created_by=creator_id
    )
    return UserPublic.model_validate(user, from_attributes=True)


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(
    user_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[None, Depends(permission_required("user_mgmt.users.read"))],
) -> UserPublic:
    user = await users_crud.get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserPublic.model_validate(user, from_attributes=True)


@router.patch("/{user_id}", response_model=UserPublic)
async def update_user(
    user_id: uuid.UUID,
    session: SessionDep,
    body: UserUpdate,
    current_user: Annotated[
        None, Depends(permission_required("user_mgmt.users.update"))
    ],
) -> UserPublic:
    user = await users_crud.get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    updater_id = current_user.id if hasattr(current_user, "id") else None  # type: ignore[union-attr]
    updated = await users_crud.update_user(
        session=session, db_user=user, user_in=body, updated_by=updater_id
    )
    return UserPublic.model_validate(updated, from_attributes=True)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    session: SessionDep,
    current_user: Annotated[
        None, Depends(permission_required("user_mgmt.users.delete"))
    ],
) -> None:
    user = await users_crud.get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    deleter_id = current_user.id if hasattr(current_user, "id") else None  # type: ignore[union-attr]
    await users_crud.soft_delete_user(
        session=session, db_user=user, deleted_by=deleter_id
    )


@router.put("/{user_id}/roles", status_code=status.HTTP_200_OK)
async def assign_user_roles(
    user_id: uuid.UUID,
    session: SessionDep,
    body: AssignUserRoles,
    _: SuperuserDep,
) -> dict:
    """Replace all roles assigned to a user. Superuser only."""
    user = await users_crud.get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await perm_crud.assign_user_roles(
        session=session, user_id=user_id, role_ids=body.role_ids
    )
    return {"message": "Roles updated"}


@router.get("/{user_id}/roles", response_model=list[int])
async def get_user_roles(
    user_id: uuid.UUID,
    session: SessionDep,
    _: SuperuserDep,
) -> list[int]:
    """Get role IDs assigned to a user. Superuser only."""
    return await perm_crud.get_user_role_ids(session=session, user_id=user_id)
