import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, SessionDep, SuperuserDep
from app.api.routes.base import CRUDRouterBase
from app.constants import GenderEnum
from app.crud import permissions as perm_crud
from app.crud import users as users_crud
from app.schemas.rbac import AssignUserRoles, NavigationResponse
from app.schemas.user import (
    UserCreate,
    UserListFilter,
    UserPublic,
    UserSearchFilter,
    UserSearchPublic,
    UserSearchResults,
    UsersPublic,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


def get_user_filters(
    username: str | None = None,
    email: str | None = None,
    is_active: bool | None = None,
    gender: GenderEnum | None = None,
    role_ids: list[int] | None = Query(default=None),
) -> UserListFilter:
    return UserListFilter(
        username=username,
        email=email,
        is_active=is_active,
        gender=gender,
        role_ids=role_ids or [],
    )


class UserCRUDRouter(
    CRUDRouterBase[
        UserCreate,
        UserUpdate,
        UserPublic,
        UsersPublic,
        UserListFilter,
        uuid.UUID,
    ]
):
    prefix = ""
    tag = "users"
    entity_name = "User"
    entity_label = "用户"
    id_type = uuid.UUID
    create_schema = UserCreate
    update_schema = UserUpdate
    public_schema = UserPublic
    list_schema = UsersPublic
    service = users_crud.service
    filter_dependency = get_user_filters
    permissions = {
        "read": "user_mgmt.users.read",
        "export": "user_mgmt.users.export",
        "create": "user_mgmt.users.create",
        "update": "user_mgmt.users.update",
        "delete": "user_mgmt.users.delete",
    }


@router.get(
    "/me",
    response_model=UserPublic,
    summary="获取当前用户资料",
    description="返回当前登录用户的基本资料信息。",
)
async def get_me(current_user: CurrentUser) -> UserPublic:
    """Return the authenticated user's profile."""
    return UserPublic.model_validate(current_user, from_attributes=True)


@router.get(
    "/me/navigation",
    response_model=NavigationResponse,
    summary="获取当前用户导航权限",
    description="返回当前用户可见的菜单、页面和按钮权限树。",
)
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


@router.get(
    "/search",
    response_model=UserSearchResults,
    summary="搜索用户",
    description="按关键字搜索用户，并可排除已分配指定角色的用户。",
)
async def search_users(
    session: SessionDep,
    _: SuperuserDep,
    keyword: str | None = None,
    exclude_role_id: int | None = None,
    limit: int = 20,
) -> UserSearchResults:
    users = await users_crud.search_users(
        session=session,
        filters=UserSearchFilter(
            keyword=keyword,
            exclude_role_id=exclude_role_id,
        ),
        limit=limit,
    )
    return UserSearchResults(
        data=[UserSearchPublic.model_validate(user, from_attributes=True) for user in users]
    )

@router.put(
    "/{user_id}/roles",
    status_code=status.HTTP_200_OK,
    summary="分配用户角色",
    description="覆盖指定用户当前关联的全部角色。",
)
async def assign_user_roles(
    user_id: uuid.UUID,
    session: SessionDep,
    body: AssignUserRoles,
    _: SuperuserDep,
) -> dict[str, str]:
    """Replace all roles assigned to a user. Superuser only."""
    user = await users_crud.get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await perm_crud.assign_user_roles(
        session=session, user_id=user_id, role_ids=body.role_ids
    )
    return {"message": "Roles updated"}


@router.get(
    "/{user_id}/roles",
    response_model=list[int],
    summary="获取用户角色",
    description="返回指定用户当前关联的角色 ID 列表。",
)
async def get_user_roles(
    user_id: uuid.UUID,
    session: SessionDep,
    _: SuperuserDep,
) -> list[int]:
    """Get role IDs assigned to a user. Superuser only."""
    return await perm_crud.get_user_role_ids(session=session, user_id=user_id)


router.include_router(UserCRUDRouter().build_router())
