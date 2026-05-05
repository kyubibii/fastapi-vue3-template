from fastapi import APIRouter, HTTPException, status

from app.api.deps import SessionDep, SuperuserDep
from app.crud import roles as roles_crud
from app.schemas.rbac import (
    AssignRolePermissions,
    RoleCreate,
    RolePublic,
    RolesPublic,
    RoleUpdate,
)

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/", response_model=RolesPublic)
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


@router.post("/", response_model=RolePublic, status_code=status.HTTP_201_CREATED)
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


@router.get("/{role_id}", response_model=RolePublic)
async def get_role(
    role_id: int,
    session: SessionDep,
    _: SuperuserDep,
) -> RolePublic:
    role = await roles_crud.get_role_by_id(session=session, role_id=role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return RolePublic.model_validate(role, from_attributes=True)


@router.patch("/{role_id}", response_model=RolePublic)
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


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
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


@router.put("/{role_id}/permissions", status_code=status.HTTP_200_OK)
async def assign_role_permissions(
    role_id: int,
    session: SessionDep,
    body: AssignRolePermissions,
    _: SuperuserDep,
) -> dict:
    """Replace all permissions assigned to a role."""
    role = await roles_crud.get_role_by_id(session=session, role_id=role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    await roles_crud.assign_role_permissions(
        session=session, role_id=role_id, permission_ids=body.permission_ids
    )
    return {"message": "Permissions updated"}


@router.get("/{role_id}/permissions", response_model=list[int])
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
