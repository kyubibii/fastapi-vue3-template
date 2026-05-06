from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import distinct, select

from app.api.deps import SessionDep, permission_required
from app.core.runtime_settings import runtime_settings
from app.crud import settings as settings_crud
from app.models.setting import Setting
from app.schemas.setting import (
    SettingCreate,
    SettingGroupPublic,
    SettingGroupsPublic,
    SettingListFilter,
    SettingPublic,
    SettingsPublic,
    SettingUpdate,
)

router = APIRouter(prefix="/settings", tags=["settings"])


def _to_public(db_obj: Setting) -> SettingPublic:
    public = SettingPublic.model_validate(db_obj, from_attributes=True)
    if db_obj.is_sensitive:
        public.setting_value = "******"
    return public


@router.get(
    "/groups",
    response_model=SettingGroupsPublic,
    summary="查询配置分组",
    description="返回配置项分组列表，用于前端动态渲染 Tabs。",
)
async def list_setting_groups(
    session: SessionDep,
    _: Annotated[None, Depends(permission_required("system.settings.read"))],
) -> SettingGroupsPublic:
    result = await session.execute(
        select(distinct(Setting.setting_group)).where(Setting.is_deleted.is_(False))
    )
    groups = [
        SettingGroupPublic(setting_group=group)
        for group in sorted([row for row in result.scalars().all() if row])
    ]
    return SettingGroupsPublic(data=groups)


@router.get(
    "/",
    response_model=SettingsPublic,
    summary="查询配置项",
    description="按分组与名称查询配置项。",
)
async def list_settings(
    session: SessionDep,
    _: Annotated[None, Depends(permission_required("system.settings.read"))],
    setting_name: str | None = None,
    setting_group: str | None = None,
    is_sensitive: bool | None = None,
    skip: int = 0,
    limit: int = 100,
) -> SettingsPublic:
    filters = SettingListFilter(
        setting_name=setting_name,
        setting_group=setting_group,
        is_sensitive=is_sensitive,
    )
    rows, count = await settings_crud.service.get_multi(
        session=session, filters=filters, skip=skip, limit=limit
    )
    return SettingsPublic(data=[_to_public(item) for item in rows], count=count)


@router.post(
    "/",
    response_model=SettingPublic,
    status_code=status.HTTP_201_CREATED,
    summary="创建配置项",
    description="新增配置项。",
)
async def create_setting(
    session: SessionDep,
    body: SettingCreate,
    _: Annotated[None, Depends(permission_required("system.settings.create"))],
) -> SettingPublic:
    try:
        created = await settings_crud.service.create(session=session, obj_in=body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    runtime_settings.invalidate(body.setting_name)
    return _to_public(created)


@router.get(
    "/{setting_id}",
    response_model=SettingPublic,
    summary="读取配置项详情",
    description="按 ID 查询配置项详情。",
)
async def get_setting(
    setting_id: int,
    session: SessionDep,
    _: Annotated[None, Depends(permission_required("system.settings.read"))],
) -> SettingPublic:
    row = await settings_crud.service.get_by_id(session=session, obj_id=setting_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    return _to_public(row)


@router.patch(
    "/{setting_id}",
    response_model=SettingPublic,
    summary="更新配置项",
    description="按 ID 更新配置项。",
)
async def update_setting(
    setting_id: int,
    session: SessionDep,
    body: SettingUpdate,
    _: Annotated[None, Depends(permission_required("system.settings.update"))],
) -> SettingPublic:
    row = await settings_crud.service.get_by_id(session=session, obj_id=setting_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    try:
        updated = await settings_crud.service.update(
            session=session,
            db_obj=row,
            obj_in=body,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    runtime_settings.invalidate(updated.setting_name)
    return _to_public(updated)