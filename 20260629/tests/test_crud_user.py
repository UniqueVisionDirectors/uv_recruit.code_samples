from app.crud import user as crud


async def test_create_and_get_user(session):
    created = await crud.create_user(session, user_id="0000000abc", name="alice")
    assert created.id == "0000000abc"
    fetched = await crud.get_user(session, "0000000abc")
    assert fetched is not None
    assert fetched.name == "alice"


async def test_get_missing_user_returns_none(session):
    assert await crud.get_user(session, "zzzzzzzzzz") is None


async def test_list_users_sorted_by_id(session):
    await crud.create_user(session, user_id="0000000002", name="b")
    await crud.create_user(session, user_id="0000000001", name="a")
    users = await crud.list_users(session)
    assert [u.id for u in users] == ["0000000001", "0000000002"]
