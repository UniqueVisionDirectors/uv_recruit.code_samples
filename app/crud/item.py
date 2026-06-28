from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate


async def create_item(session: AsyncSession, data: ItemCreate) -> Item:
    item = Item(name=data.name, description=data.description)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def get_item(session: AsyncSession, item_id: int) -> Item | None:
    return await session.get(Item, item_id)


async def list_items(
    session: AsyncSession, limit: int = 100, offset: int = 0
) -> list[Item]:
    result = await session.execute(select(Item).offset(offset).limit(limit))
    return list(result.scalars().all())


async def update_item(session: AsyncSession, item: Item, data: ItemUpdate) -> Item:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def delete_item(session: AsyncSession, item: Item) -> None:
    await session.delete(item)
    await session.commit()
