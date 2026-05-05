import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, SessionDep, permission_required
from app.crud import items as items_crud
from app.schemas.item import ItemCreate, ItemPublic, ItemsPublic, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=ItemsPublic)
async def list_items(
    session: SessionDep,
    current_user: Annotated[
        None, Depends(permission_required("content.items.read"))
    ],
    skip: int = 0,
    limit: int = 100,
) -> ItemsPublic:
    items, count = await items_crud.get_items(session=session, skip=skip, limit=limit)
    return ItemsPublic(
        data=[ItemPublic.model_validate(i, from_attributes=True) for i in items],
        count=count,
    )


@router.get("/export/csv")
async def export_items_csv(
    session: SessionDep,
    _: Annotated[None, Depends(permission_required("content.items.export"))],
) -> StreamingResponse:
    """Download all items as a UTF-8 CSV file."""
    items = await items_crud.get_all_items_for_export(session=session)
    csv_content = items_crud.items_to_csv(items)

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=items.csv"},
    )


@router.post("/", response_model=ItemPublic, status_code=status.HTTP_201_CREATED)
async def create_item(
    session: SessionDep,
    body: ItemCreate,
    current_user: Annotated[
        CurrentUser, Depends(permission_required("content.items.create"))
    ],
) -> ItemPublic:
    owner_id = current_user.id  # type: ignore[union-attr]
    item = await items_crud.create_item(
        session=session,
        item_in=body,
        owner_id=owner_id,
        created_by=owner_id,
    )
    return ItemPublic.model_validate(item, from_attributes=True)


@router.get("/{item_id}", response_model=ItemPublic)
async def get_item(
    item_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[None, Depends(permission_required("content.items.read"))],
) -> ItemPublic:
    item = await items_crud.get_item_by_id(session=session, item_id=item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return ItemPublic.model_validate(item, from_attributes=True)


@router.patch("/{item_id}", response_model=ItemPublic)
async def update_item(
    item_id: uuid.UUID,
    session: SessionDep,
    body: ItemUpdate,
    current_user: Annotated[
        CurrentUser, Depends(permission_required("content.items.update"))
    ],
) -> ItemPublic:
    item = await items_crud.get_item_by_id(session=session, item_id=item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    updater_id = current_user.id  # type: ignore[union-attr]
    updated = await items_crud.update_item(
        session=session, db_item=item, item_in=body, updated_by=updater_id
    )
    return ItemPublic.model_validate(updated, from_attributes=True)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: uuid.UUID,
    session: SessionDep,
    current_user: Annotated[
        CurrentUser, Depends(permission_required("content.items.delete"))
    ],
) -> None:
    item = await items_crud.get_item_by_id(session=session, item_id=item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    await items_crud.soft_delete_item(
        session=session, db_item=item, deleted_by=current_user.id  # type: ignore[union-attr]
    )
