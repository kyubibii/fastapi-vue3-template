import uuid
from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDServiceBase
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemListFilter, ItemUpdate


class ItemCRUDService(
    CRUDServiceBase[Item, ItemCreate, ItemUpdate, ItemListFilter, uuid.UUID]
):
    model = Item
    list_order_by = cast(Any, Item.created_at).desc()
    export_order_by = cast(Any, Item.created_at).asc()
    export_fields = ["id", "title", "description", "owner_id", "created_at"]
    export_filename = "items.csv"

    def apply_filters(self, query: Any, filters: ItemListFilter | None) -> Any:
        if not filters:
            return query
        if filters.owner_id:
            query = query.where(Item.owner_id == filters.owner_id)
        if filters.title:
            query = query.where(cast(Any, Item.title).contains(filters.title))
        return query


service = ItemCRUDService()


async def get_item_by_id(*, session: AsyncSession, item_id: uuid.UUID) -> Item | None:
    return await service.get_by_id(session=session, obj_id=item_id)


async def create_item(
    *,
    session: AsyncSession,
    item_in: ItemCreate,
    owner_id: uuid.UUID,
    created_by: uuid.UUID | None = None,
) -> Item:
    return await service.create(
        session=session,
        obj_in=item_in,
        owner_id=owner_id,
        created_by=created_by,
    )


async def get_items(
    *,
    session: AsyncSession,
    owner_id: uuid.UUID | None = None,
    title: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Item], int]:
    filters = ItemListFilter(owner_id=owner_id, title=title)
    return await service.get_multi(
        session=session,
        filters=filters,
        skip=skip,
        limit=limit,
    )


async def update_item(
    *,
    session: AsyncSession,
    db_item: Item,
    item_in: ItemUpdate,
    updated_by: uuid.UUID | None = None,
) -> Item:
    return await service.update(
        session=session,
        db_obj=db_item,
        obj_in=item_in,
        updated_by=updated_by,
    )


async def soft_delete_item(
    *,
    session: AsyncSession,
    db_item: Item,
    deleted_by: uuid.UUID | None = None,
) -> Item:
    deleted = await service.delete(
        session=session,
        db_obj=db_item,
        deleted_by=deleted_by,
    )
    if deleted is None:
        raise RuntimeError("Item service unexpectedly performed a hard delete")
    return deleted


async def get_all_items_for_export(
    *,
    session: AsyncSession,
    owner_id: uuid.UUID | None = None,
    title: str | None = None,
) -> list[Item]:
    filters = ItemListFilter(owner_id=owner_id, title=title)
    return await service.get_all_for_export(session=session, filters=filters)


def items_to_csv(items: list[Item]) -> str:
    return service.export_to_csv(items)
