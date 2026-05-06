from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import SessionDep, SuperuserDep
from app.crud import permissions as perm_crud
from app.models.rbac import (
    Permission,
    PermissionGroup,
    PermissionPage,
)
from app.schemas.rbac import (
    PermissionGroupCreate,
    PermissionGroupPublic,
    PermissionPageCreate,
    PermissionPagePublic,
    PermissionPublic,
    PermissionTreeResponse,
)

router = APIRouter(prefix="/permissions", tags=["permissions"])

_BUILTIN_ACTIONS = [
    ("读取", "read"),
    ("创建", "create"),
    ("更新", "update"),
    ("删除", "delete"),
]


@router.get(
    "/tree",
    response_model=PermissionTreeResponse,
    summary="获取权限树",
    description="返回完整的权限组、页面与权限动作树。",
)
async def get_permission_tree(
    session: SessionDep,
    _: SuperuserDep,
) -> PermissionTreeResponse:
    """Return the full permission tree (groups → pages → permissions)."""
    groups = await perm_crud.get_all_groups(session=session)
    result = []
    for group in groups:
        pages = await perm_crud.get_pages_by_group(session=session, group_id=group.id)  # type: ignore[arg-type]
        page_list = []
        for page in pages:
            perms = await perm_crud.get_permissions_by_page(
                session=session, page_id=page.id  # type: ignore[arg-type]
            )
            page_list.append(
                PermissionPagePublic(
                    id=page.id,  # type: ignore[arg-type]
                    name=page.name,
                    code=page.code,
                    page_url=page.page_url,
                    sort_order=page.sort_order,
                    permissions=[
                        PermissionPublic.model_validate(p, from_attributes=True)
                        for p in perms
                    ],
                )
            )
        result.append(
            PermissionGroupPublic(
                id=group.id,  # type: ignore[arg-type]
                name=group.name,
                code=group.code,
                sort_order=group.sort_order,
                pages=page_list,
            )
        )
    return PermissionTreeResponse(groups=result)


@router.post(
    "/groups",
    response_model=PermissionGroupPublic,
    status_code=201,
    summary="创建权限组",
    description="创建新的权限组节点。",
)
async def create_group(
    session: SessionDep,
    body: PermissionGroupCreate,
    _: SuperuserDep,
) -> PermissionGroupPublic:
    existing = await session.execute(
        select(PermissionGroup).where(PermissionGroup.code == body.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Group code '{body.code}' exists")
    group = PermissionGroup(**body.model_dump())
    session.add(group)
    await session.commit()
    await session.refresh(group)
    return PermissionGroupPublic(
        id=group.id,  # type: ignore[arg-type]
        name=group.name,
        code=group.code,
        sort_order=group.sort_order,
        pages=[],
    )


@router.post(
    "/pages",
    response_model=PermissionPagePublic,
    status_code=201,
    summary="创建权限页面",
    description="创建权限页面，并自动生成内置增删改查动作。",
)
async def create_page(
    session: SessionDep,
    body: PermissionPageCreate,
    _: SuperuserDep,
) -> PermissionPagePublic:
    """
    Create a page and auto-generate 4 builtin permissions (read/create/update/delete).
    """
    # Resolve group to get its code for building full_code
    group = await session.get(PermissionGroup, body.group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Permission group not found")

    page = PermissionPage(**body.model_dump())
    session.add(page)
    await session.commit()
    await session.refresh(page)

    # Auto-create 4 builtin CRUD permissions
    builtin_perms: list[Permission] = []
    for action_name, action_code in _BUILTIN_ACTIONS:
        full_code = f"{group.code}.{page.code}.{action_code}"
        perm = Permission(
            page_id=page.id,
            name=f"{action_name}{page.name}",
            code=action_code,
            full_code=full_code,
            is_builtin=True,
        )
        session.add(perm)
        builtin_perms.append(perm)

    await session.commit()
    for p in builtin_perms:
        await session.refresh(p)

    return PermissionPagePublic(
        id=page.id,  # type: ignore[arg-type]
        name=page.name,
        code=page.code,
        page_url=page.page_url,
        sort_order=page.sort_order,
        permissions=[
            PermissionPublic.model_validate(p, from_attributes=True)
            for p in builtin_perms
        ],
    )


@router.post(
    "/pages/{page_id}/actions",
    response_model=PermissionPublic,
    status_code=201,
    summary="新增自定义权限动作",
    description="为指定权限页面新增一个自定义动作权限。",
)
async def add_custom_action(
    page_id: int,
    action_code: str,
    action_name: str,
    session: SessionDep,
    _: SuperuserDep,
) -> PermissionPublic:
    """Add a custom action (e.g. 'export') to an existing page."""
    page = await session.get(PermissionPage, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Permission page not found")
    group = await session.get(PermissionGroup, page.group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Permission group not found")

    full_code = f"{group.code}.{page.code}.{action_code}"
    existing = await perm_crud.get_permission_by_full_code(
        session=session, full_code=full_code
    )
    if existing:
        raise HTTPException(status_code=409, detail=f"Permission '{full_code}' already exists")

    perm = Permission(
        page_id=page_id,
        name=action_name,
        code=action_code,
        full_code=full_code,
        is_builtin=False,
    )
    session.add(perm)
    await session.commit()
    await session.refresh(perm)
    return PermissionPublic.model_validate(perm, from_attributes=True)
