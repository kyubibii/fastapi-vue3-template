import uuid

from app.api.routes.base import CRUDRouterBase
from app.crud import items as items_crud
from app.models.user import User
from app.schemas.item import (
    ItemCreate,
    ItemListFilter,
    ItemPublic,
    ItemsPublic,
    ItemUpdate,
)


def get_item_filters(
    owner_id: uuid.UUID | None = None,
    title: str | None = None,
) -> ItemListFilter:
    return ItemListFilter(owner_id=owner_id, title=title)


class ItemRouter(
    CRUDRouterBase[
        ItemCreate,
        ItemUpdate,
        ItemPublic,
        ItemsPublic,
        ItemListFilter,
        uuid.UUID,
    ]
):
    prefix = "/items"
    tag = "items"
    entity_name = "Item"
    entity_label = "物品"
    id_type = uuid.UUID
    create_schema = ItemCreate
    update_schema = ItemUpdate
    public_schema = ItemPublic
    list_schema = ItemsPublic
    service = items_crud.service
    filter_dependency = get_item_filters
    permissions = {
        "read": "content.items.read",
        "export": "content.items.export",
        "create": "content.items.create",
        "update": "content.items.update",
        "delete": "content.items.delete",
    }

    def build_create_kwargs(
        self, *, current_user: User, body: ItemCreate
    ) -> dict[str, uuid.UUID]:
        return {"owner_id": current_user.id}


router = ItemRouter().build_router()
