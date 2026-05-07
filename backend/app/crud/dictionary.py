import uuid
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.base import CRUDServiceBase
from app.models.dictionary import DictionaryItem, DictionaryType
from app.schemas.dictionary import (
    DictionaryItemCreate,
    DictionaryItemListFilter,
    DictionaryItemUpdate,
    DictionaryOptionItemPublic,
    DictionaryTypeCreate,
    DictionaryTypeListFilter,
    DictionaryTypeUpdate,
)


def _normalize_code(value: str) -> str:
    return value.strip().lower()


class DictionaryTypeCRUDService(
    CRUDServiceBase[
        DictionaryType,
        DictionaryTypeCreate,
        DictionaryTypeUpdate,
        DictionaryTypeListFilter,
        uuid.UUID,
    ]
):
    model = DictionaryType
    list_order_by = cast(Any, DictionaryType.sort_order).asc()

    def apply_filters(self, query: Any, filters: DictionaryTypeListFilter | None) -> Any:
        if not filters:
            return query
        if filters.type_code:
            query = query.where(
                cast(Any, DictionaryType.type_code).contains(_normalize_code(filters.type_code))
            )
        if filters.type_name:
            query = query.where(
                cast(Any, DictionaryType.type_name).contains(filters.type_name.strip())
            )
        return query

    async def before_create(
        self,
        *,
        session: AsyncSession,
        obj_in: DictionaryTypeCreate,
        create_data: dict[str, Any],
    ) -> None:
        create_data["type_code"] = _normalize_code(create_data["type_code"])
        create_data["type_name"] = create_data["type_name"].strip()
        if create_data.get("description") is not None:
            create_data["description"] = create_data["description"].strip() or None

        existing = (
            await session.execute(
                select(DictionaryType).where(
                    DictionaryType.type_code == create_data["type_code"],
                    cast(Any, DictionaryType.is_deleted).is_(False),
                )
            )
        ).scalar_one_or_none()
        if existing:
            raise ValueError("Dictionary type code already exists")

    async def before_update(
        self,
        *,
        session: AsyncSession,
        db_obj: DictionaryType,
        obj_in: DictionaryTypeUpdate,
    ) -> None:
        update_data = obj_in.model_dump(exclude_unset=True)
        if not update_data:
            return

        target_code = db_obj.type_code
        if "type_code" in update_data and update_data["type_code"] is not None:
            target_code = _normalize_code(update_data["type_code"])
            obj_in.type_code = target_code

        if "type_name" in update_data and update_data["type_name"] is not None:
            obj_in.type_name = update_data["type_name"].strip()

        if "description" in update_data and update_data["description"] is not None:
            obj_in.description = update_data["description"].strip() or None

        if target_code != db_obj.type_code:
            duplicated = (
                await session.execute(
                    select(DictionaryType).where(
                        DictionaryType.type_code == target_code,
                        cast(Any, DictionaryType.is_deleted).is_(False),
                    )
                )
            ).scalar_one_or_none()
            if duplicated:
                raise ValueError("Dictionary type code already exists")

    async def after_delete(
        self,
        *,
        session: AsyncSession,
        db_obj: DictionaryType,
    ) -> None:
        await session.execute(
            update(DictionaryItem)
            .where(
                DictionaryItem.type_id == db_obj.id,
                cast(Any, DictionaryItem.is_deleted).is_(False),
            )
            .values(
                is_deleted=True,
                deleted_at=datetime.now(UTC),
                deleted_by=db_obj.deleted_by,
            )
        )
        await session.commit()


class DictionaryItemCRUDService(
    CRUDServiceBase[
        DictionaryItem,
        DictionaryItemCreate,
        DictionaryItemUpdate,
        DictionaryItemListFilter,
        uuid.UUID,
    ]
):
    model = DictionaryItem
    list_order_by = cast(Any, DictionaryItem.sort_order).asc()

    def apply_filters(self, query: Any, filters: DictionaryItemListFilter | None) -> Any:
        if not filters:
            return query
        if filters.type_id:
            query = query.where(DictionaryItem.type_id == filters.type_id)
        if filters.item_code:
            query = query.where(
                cast(Any, DictionaryItem.item_code).contains(_normalize_code(filters.item_code))
            )
        if filters.item_label:
            query = query.where(
                cast(Any, DictionaryItem.item_label).contains(filters.item_label.strip())
            )
        if filters.enabled is not None:
            query = query.where(DictionaryItem.enabled == filters.enabled)
        return query

    async def before_create(
        self,
        *,
        session: AsyncSession,
        obj_in: DictionaryItemCreate,
        create_data: dict[str, Any],
    ) -> None:
        create_data["item_code"] = _normalize_code(create_data["item_code"])
        create_data["item_label"] = create_data["item_label"].strip()
        create_data["item_value"] = create_data["item_value"].strip()

        dict_type = (
            await session.execute(
                select(DictionaryType).where(
                    DictionaryType.id == create_data["type_id"],
                    cast(Any, DictionaryType.is_deleted).is_(False),
                )
            )
        ).scalar_one_or_none()
        if not dict_type:
            raise ValueError("Dictionary type not found")

        duplicated = (
            await session.execute(
                select(DictionaryItem).where(
                    DictionaryItem.type_id == create_data["type_id"],
                    DictionaryItem.item_code == create_data["item_code"],
                    cast(Any, DictionaryItem.is_deleted).is_(False),
                )
            )
        ).scalar_one_or_none()
        if duplicated:
            raise ValueError("Dictionary item code already exists in this type")

    async def before_update(
        self,
        *,
        session: AsyncSession,
        db_obj: DictionaryItem,
        obj_in: DictionaryItemUpdate,
    ) -> None:
        update_data = obj_in.model_dump(exclude_unset=True)
        if not update_data:
            return

        target_type_id = db_obj.type_id
        if "type_id" in update_data and update_data["type_id"] is not None:
            target_type_id = update_data["type_id"]
            dict_type = (
                await session.execute(
                    select(DictionaryType).where(
                        DictionaryType.id == target_type_id,
                        cast(Any, DictionaryType.is_deleted).is_(False),
                    )
                )
            ).scalar_one_or_none()
            if not dict_type:
                raise ValueError("Dictionary type not found")

        target_code = db_obj.item_code
        if "item_code" in update_data and update_data["item_code"] is not None:
            target_code = _normalize_code(update_data["item_code"])
            obj_in.item_code = target_code

        if "item_label" in update_data and update_data["item_label"] is not None:
            obj_in.item_label = update_data["item_label"].strip()

        if "item_value" in update_data and update_data["item_value"] is not None:
            obj_in.item_value = update_data["item_value"].strip()

        duplicated = (
            await session.execute(
                select(DictionaryItem).where(
                    DictionaryItem.id != db_obj.id,
                    DictionaryItem.type_id == target_type_id,
                    DictionaryItem.item_code == target_code,
                    cast(Any, DictionaryItem.is_deleted).is_(False),
                )
            )
        ).scalar_one_or_none()
        if duplicated:
            raise ValueError("Dictionary item code already exists in this type")


type_service = DictionaryTypeCRUDService()
item_service = DictionaryItemCRUDService()


async def get_enabled_items_by_type_code(
    *,
    session: AsyncSession,
    type_code: str,
) -> list[DictionaryOptionItemPublic]:
    normalized_type_code = _normalize_code(type_code)
    rows = (
        await session.execute(
            select(DictionaryItem)
            .join(DictionaryType, DictionaryType.id == DictionaryItem.type_id)
            .where(
                DictionaryType.type_code == normalized_type_code,
                cast(Any, DictionaryType.is_deleted).is_(False),
                cast(Any, DictionaryItem.is_deleted).is_(False),
                DictionaryItem.enabled.is_(True),
            )
            .order_by(cast(Any, DictionaryItem.sort_order).asc())
        )
    ).scalars().all()

    return [
        DictionaryOptionItemPublic(
            code=row.item_code,
            label=row.item_label,
            value=row.item_value,
            sort_order=row.sort_order,
        )
        for row in rows
    ]
