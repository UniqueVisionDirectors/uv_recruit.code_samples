async def test_create_item(client):
    resp = await client.post("/items", json={"name": "foo", "description": "bar"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] > 0
    assert body["name"] == "foo"


async def test_get_item(client):
    created = (await client.post("/items", json={"name": "x"})).json()
    resp = await client.get(f"/items/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "x"


async def test_get_missing_item_404(client):
    resp = await client.get("/items/99999")
    assert resp.status_code == 404


async def test_list_items(client):
    await client.post("/items", json={"name": "a"})
    await client.post("/items", json={"name": "b"})
    resp = await client.get("/items")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_update_item(client):
    created = (await client.post("/items", json={"name": "old"})).json()
    resp = await client.patch(f"/items/{created['id']}", json={"name": "new"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "new"


async def test_update_missing_item_404(client):
    resp = await client.patch("/items/99999", json={"name": "new"})
    assert resp.status_code == 404


async def test_delete_item(client):
    created = (await client.post("/items", json={"name": "z"})).json()
    resp = await client.delete(f"/items/{created['id']}")
    assert resp.status_code == 204
    assert (await client.get(f"/items/{created['id']}")).status_code == 404


async def test_delete_missing_item_404(client):
    resp = await client.delete("/items/99999")
    assert resp.status_code == 404
