import random

from app.idgen.base import EPOCH_MS
from app.idgen.generator import UserIdGenerator
from app.main import app


def _install_issuer(start_ms: int = 0):
    clock = {"ms": start_ms}
    app.state.issuer = UserIdGenerator(
        0, now_ms=lambda: EPOCH_MS + clock["ms"], rng=random.Random(0)
    )
    return clock


async def test_create_user_returns_valid_id(client):
    _install_issuer()
    resp = await client.post("/users", json={"name": "alice"})
    assert resp.status_code == 201
    body = resp.json()
    assert len(body["id"]) == 10
    assert body["name"] == "alice"


async def test_get_user(client):
    _install_issuer()
    created = (await client.post("/users", json={"name": "bob"})).json()
    resp = await client.get(f"/users/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "bob"


async def test_get_missing_user_404(client):
    resp = await client.get("/users/zzzzzzzzzz")
    assert resp.status_code == 404


async def test_ids_are_sorted_by_issue_order(client):
    clock = _install_issuer()
    first = (await client.post("/users", json={"name": "a"})).json()["id"]
    clock["ms"] = 10
    second = (await client.post("/users", json={"name": "b"})).json()["id"]
    assert first < second


async def test_list_users_returns_sorted(client):
    _install_issuer()
    for name in ["a", "b", "c"]:
        await client.post("/users", json={"name": name})
    resp = await client.get("/users?limit=10&offset=0")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 3
    ids = [u["id"] for u in body]
    assert ids == sorted(ids)  # 発行順＝ソート順


async def test_openapi_declares_conflict_and_examples(client):
    schema = (await client.get("/openapi.json")).json()
    post = schema["paths"]["/users"]["post"]
    assert "409" in post["responses"]  # 衝突が宣言されている
    user_create = schema["components"]["schemas"]["UserCreate"]
    assert "example" in user_create
    user_read = schema["components"]["schemas"]["UserRead"]
    assert "example" in user_read
