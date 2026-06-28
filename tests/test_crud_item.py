from app.crud import item as crud
from app.schemas.item import ItemCreate, ItemUpdate


async def test_create_and_get_item(session):
    created = await crud.create_item(session, ItemCreate(name="foo", description="bar"))
    assert created.id is not None
    fetched = await crud.get_item(session, created.id)
    assert fetched is not None
    assert fetched.name == "foo"
    assert fetched.description == "bar"


async def test_get_missing_returns_none(session):
    assert await crud.get_item(session, 9999) is None


async def test_list_items(session):
    await crud.create_item(session, ItemCreate(name="a"))
    await crud.create_item(session, ItemCreate(name="b"))
    items = await crud.list_items(session)
    assert len(items) == 2


async def test_update_item(session):
    created = await crud.create_item(session, ItemCreate(name="old"))
    updated = await crud.update_item(session, created, ItemUpdate(name="new"))
    assert updated.name == "new"


async def test_delete_item(session):
    created = await crud.create_item(session, ItemCreate(name="x"))
    assert created.id is not None
    await crud.delete_item(session, created)
    assert await crud.get_item(session, created.id) is None
