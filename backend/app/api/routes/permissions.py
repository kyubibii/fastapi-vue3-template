from fastapi import APIRouter

from app.api.deps import SessionDep, SuperuserDep
from app.crud import permissions as perm_crud
from app.schemas.rbac import (
    PermissionGroupPublic,
    PermissionPagePublic,
    PermissionPublic,
    PermissionTreeResponse,
)

router = APIRouter(prefix="/permissions", tags=["permissions"])


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
