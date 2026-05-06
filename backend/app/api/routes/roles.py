import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import SessionDep, SuperuserDep
from app.crud import permissions as perm_crud
from app.crud import roles as roles_crud
from app.schemas.rbac import (
    AssignRolePermissions,
    AssignRoleUsers,
    RoleCreate,
    RolePublic,
    RolesPublic,
    RoleUpdate,
)
from app.schemas.user import UserSearchPublic, UserSearchResults

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get(
    "/",
    response_model=RolesPublic,
    summary="查询角色列表",
    description="按分页条件查询角色列表。",
)
async def list_roles(
    session: SessionDep,
    _: SuperuserDep,
    skip: int = 0,
    limit: int = 100,
) -> RolesPublic:
    roles, count = await roles_crud.get_roles(session=session, skip=skip, limit=limit)
    return RolesPublic(
        data=[RolePublic.model_validate(r, from_attributes=True) for r in roles],
        count=count,
    )


@router.post(
    "/",
    response_model=RolePublic,
    status_code=status.HTTP_201_CREATED,
    summary="创建角色",
    description="创建一个新的角色定义。",
)
async def create_role(
    session: SessionDep,
    body: RoleCreate,
    _: SuperuserDep,
) -> RolePublic:
    existing = await roles_crud.get_role_by_code(session=session, code=body.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role code '{body.code}' already exists",
        )
    role = await roles_crud.create_role(session=session, role_in=body)
    return RolePublic.model_validate(role, from_attributes=True)


@router.get(
    "/{role_id}",
    response_model=RolePublic,
    summary="获取角色详情",
    description="按角色 ID 获取单个角色详情。",
)
async def get_role(
    role_id: int,
    session: SessionDep,
    _: SuperuserDep,
) -> RolePublic:
    role = await roles_crud.get_role_by_id(session=session, role_id=role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return RolePublic.model_validate(role, from_attributes=True)


@router.patch(
    "/{role_id}",
    response_model=RolePublic,
    summary="更新角色",
    description="按角色 ID 更新角色名称或说明。",
)
async def update_role(
    role_id: int,
    session: SessionDep,
    body: RoleUpdate,
    _: SuperuserDep,
) -> RolePublic:
    role = await roles_crud.get_role_by_id(session=session, role_id=role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    updated = await roles_crud.update_role(session=session, db_role=role, role_in=body)
    return RolePublic.model_validate(updated, from_attributes=True)


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除角色",
    description="删除指定角色，并清理它的角色权限关联。",
)
async def delete_role(
    role_id: int,
    session: SessionDep,
    _: SuperuserDep,
) -> None:
    role = await roles_crud.get_role_by_id(session=session, role_id=role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role.is_builtin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a builtin role",
        )
    await roles_crud.delete_role(session=session, db_role=role)


@router.put(
    "/{role_id}/permissions",
    status_code=status.HTTP_200_OK,
    summary="分配角色权限",
    description="覆盖指定角色当前关联的全部权限。",
)
async def assign_role_permissions(
    role_id: int,
    session: SessionDep,
    body: AssignRolePermissions,
    _: SuperuserDep,
) -> dict[str, str]:
    """Replace all permissions assigned to a role."""
    role = await roles_crud.get_role_by_id(session=session, role_id=role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    await roles_crud.assign_role_permissions(
        session=session, role_id=role_id, permission_ids=body.permission_ids
    )
    return {"message": "Permissions updated"}


@router.get(
    "/{role_id}/permissions",
    response_model=list[int],
    summary="获取角色权限",
    description="返回指定角色当前关联的权限 ID 列表。",
)
async def get_role_permissions(
    role_id: int,
    session: SessionDep,
    _: SuperuserDep,
) -> list[int]:
    """Return permission IDs assigned to a role."""
    role = await roles_crud.get_role_by_id(session=session, role_id=role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return await roles_crud.get_role_permission_ids(session=session, role_id=role_id)


@router.get(
    "/{role_id}/users",
    response_model=UserSearchResults,
    summary="查询角色用户",
    description="查询指定角色下已分配的用户，并支持关键字过滤。",
)
async def get_role_users(
    role_id: int,
    session: SessionDep,
    _: SuperuserDep,
    keyword: str | None = None,
) -> UserSearchResults:
    role = await roles_crud.get_role_by_id(session=session, role_id=role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    users = await roles_crud.get_role_users(
        session=session,
        role_id=role_id,
        keyword=keyword,
    )
    return UserSearchResults(
        data=[UserSearchPublic.model_validate(user, from_attributes=True) for user in users]
    )


@router.put(
    "/{role_id}/users",
    status_code=status.HTTP_200_OK,
    summary="分配角色用户",
    description="覆盖指定角色当前关联的全部用户。",
)
async def assign_role_users(
    role_id: int,
    session: SessionDep,
    body: AssignRoleUsers,
    _: SuperuserDep,
) -> dict[str, str]:
    role = await roles_crud.get_role_by_id(session=session, role_id=role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    user_ids = [uuid.UUID(user_id) for user_id in body.user_ids]
    await perm_crud.replace_role_users(session=session, role_id=role_id, user_ids=user_ids)
    return {"message": "Role users updated"}
