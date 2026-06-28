from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import item as crud
from app.db.session import get_session
from app.schemas.item import ItemCreate, ItemRead, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])


@router.post("", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(
    data: ItemCreate, session: AsyncSession = Depends(get_session)
) -> ItemRead:
    item = await crud.create_item(session, data)
    return ItemRead.model_validate(item, from_attributes=True)


@router.get("", response_model=list[ItemRead])
async def list_items(
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
) -> list[ItemRead]:
    items = await crud.list_items(session, limit=limit, offset=offset)
    return [ItemRead.model_validate(i, from_attributes=True) for i in items]


@router.get("/{item_id}", response_model=ItemRead)
async def get_item(
    item_id: int, session: AsyncSession = Depends(get_session)
) -> ItemRead:
    item = await crud.get_item(session, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemRead.model_validate(item, from_attributes=True)


@router.patch("/{item_id}", response_model=ItemRead)
async def update_item(
    item_id: int,
    data: ItemUpdate,
    session: AsyncSession = Depends(get_session),
) -> ItemRead:
    item = await crud.get_item(session, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    updated = await crud.update_item(session, item, data)
    return ItemRead.model_validate(updated, from_attributes=True)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    item = await crud.get_item(session, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    await crud.delete_item(session, item)
