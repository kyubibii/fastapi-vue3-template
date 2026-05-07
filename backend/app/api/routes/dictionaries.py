import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import SessionDep, permission_required
from app.api.routes.base import CRUDRouterBase
from app.crud import dictionary as dictionary_crud
from app.schemas.dictionary import (
    DictionaryItemCreate,
    DictionaryItemListFilter,
    DictionaryItemPublic,
    DictionaryItemsPublic,
    DictionaryItemUpdate,
    DictionaryOptionsPublic,
    DictionaryTypeCreate,
    DictionaryTypeListFilter,
    DictionaryTypePublic,
    DictionaryTypesPublic,
    DictionaryTypeUpdate,
)

router = APIRouter(tags=["dictionaries"])


def get_dictionary_type_filters(
    type_code: str | None = None,
    type_name: str | None = None,
) -> DictionaryTypeListFilter:
    return DictionaryTypeListFilter(type_code=type_code, type_name=type_name)


def get_dictionary_item_filters(
    type_id: uuid.UUID | None = None,
    item_code: str | None = None,
    item_label: str | None = None,
    enabled: bool | None = None,
) -> DictionaryItemListFilter:
    return DictionaryItemListFilter(
        type_id=type_id,
        item_code=item_code,
        item_label=item_label,
        enabled=enabled,
    )


class DictionaryTypeRouter(
    CRUDRouterBase[
        DictionaryTypeCreate,
        DictionaryTypeUpdate,
        DictionaryTypePublic,
        DictionaryTypesPublic,
        DictionaryTypeListFilter,
        uuid.UUID,
    ]
):
    prefix = "/dictionaries"
    tag = "dictionaries"
    entity_name = "DictionaryType"
    entity_label = "字典类型"
    id_type = uuid.UUID
    create_schema = DictionaryTypeCreate
    update_schema = DictionaryTypeUpdate
    public_schema = DictionaryTypePublic
    list_schema = DictionaryTypesPublic
    service = dictionary_crud.type_service
    filter_dependency = get_dictionary_type_filters
    permissions = {
        "read": "system.dictionaries.read",
        "create": "system.dictionaries.create",
        "update": "system.dictionaries.update",
        "delete": "system.dictionaries.delete",
    }


class DictionaryItemRouter(
    CRUDRouterBase[
        DictionaryItemCreate,
        DictionaryItemUpdate,
        DictionaryItemPublic,
        DictionaryItemsPublic,
        DictionaryItemListFilter,
        uuid.UUID,
    ]
):
    prefix = "/dictionary-items"
    tag = "dictionaries"
    entity_name = "DictionaryItem"
    entity_label = "字典项"
    id_type = uuid.UUID
    create_schema = DictionaryItemCreate
    update_schema = DictionaryItemUpdate
    public_schema = DictionaryItemPublic
    list_schema = DictionaryItemsPublic
    service = dictionary_crud.item_service
    filter_dependency = get_dictionary_item_filters
    permissions = {
        "read": "system.dictionaries.read",
        "create": "system.dictionaries.create",
        "update": "system.dictionaries.update",
        "delete": "system.dictionaries.delete",
    }


@router.get(
    "/dictionaries/by-code/{type_code}/items",
    response_model=DictionaryOptionsPublic,
    summary="按字典类型编码查询可用字典项",
    description="返回指定类型下 enabled=true 的字典项，按 sort_order 升序。",
)
async def list_enabled_dictionary_items_by_type_code(
    type_code: str,
    session: SessionDep,
    _: None = Depends(permission_required("system.dictionaries.read")),
) -> DictionaryOptionsPublic:
    if not type_code.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="type_code is required",
        )

    options = await dictionary_crud.get_enabled_items_by_type_code(
        session=session,
        type_code=type_code,
    )
    return DictionaryOptionsPublic(type_code=type_code.strip().lower(), data=options)


router.include_router(DictionaryTypeRouter().build_router())
router.include_router(DictionaryItemRouter().build_router())
