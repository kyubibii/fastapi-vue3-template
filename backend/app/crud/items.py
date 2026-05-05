import csv
import io
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate


async def get_item_by_id(
    *, session: AsyncSession, item_id: uuid.UUID
) -> Item | None:
    result = await session.execute(
        select(Item).where(Item.id == item_id, Item.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def get_items(
    *,
    session: AsyncSession,
    owner_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Item], int]:
    query = select(Item).where(Item.deleted_at.is_(None))
    if owner_id:
        query = query.where(Item.owner_id == owner_id)
    count_result = await session.execute(query)
    count = len(count_result.scalars().all())
    result = await session.execute(
        query.order_by(Item.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all()), count


async def create_item(
    *,
    session: AsyncSession,
    item_in: ItemCreate,
    owner_id: uuid.UUID,
    created_by: uuid.UUID | None = None,
) -> Item:
    item = Item(
        title=item_in.title,
        description=item_in.description,
        owner_id=owner_id,
        created_by=created_by,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def update_item(
    *,
    session: AsyncSession,
    db_item: Item,
    item_in: ItemUpdate,
    updated_by: uuid.UUID | None = None,
) -> Item:
    update_data = item_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    db_item.updated_at = datetime.now(timezone.utc)
    db_item.updated_by = updated_by
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item


async def soft_delete_item(
    *,
    session: AsyncSession,
    db_item: Item,
    deleted_by: uuid.UUID | None = None,
) -> Item:
    db_item.deleted_at = datetime.now(timezone.utc)
    db_item.deleted_by = deleted_by
    session.add(db_item)
    await session.commit()
    return db_item


async def get_all_items_for_export(
    *, session: AsyncSession, owner_id: uuid.UUID | None = None
) -> list[Item]:
    """Fetch all (non-deleted) items without pagination for CSV export."""
    query = select(Item).where(Item.deleted_at.is_(None))
    if owner_id:
        query = query.where(Item.owner_id == owner_id)
    result = await session.execute(query.order_by(Item.created_at.asc()))
    return list(result.scalars().all())


def items_to_csv(items: list[Item]) -> str:
    """Serialize items to a UTF-8 CSV string."""
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["id", "title", "description", "owner_id", "created_at"],
    )
    writer.writeheader()
    for item in items:
        writer.writerow(
            {
                "id": str(item.id),
                "title": item.title,
                "description": item.description or "",
                "owner_id": str(item.owner_id),
                "created_at": item.created_at.isoformat() if item.created_at else "",
            }
        )
    return output.getvalue()
