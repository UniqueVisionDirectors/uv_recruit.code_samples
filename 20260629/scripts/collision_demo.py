import asyncio
import os

import httpx

TARGET = os.environ.get("TARGET_URL", "http://localhost:8080")
# 既定値は衝突が観測されやすいよう高めに設定。衝突は負荷・マシン依存で確率的
# （決定的な証明は tests/test_idgen_collision.py）。TOTAL/CONCURRENCY で調整可能。
TOTAL = int(os.environ.get("TOTAL", "12000"))
CONCURRENCY = int(os.environ.get("CONCURRENCY", "200"))

_lock = asyncio.Lock()
_state = {"sent": 0}

Result = tuple[int, str | None]


async def _worker(client: httpx.AsyncClient, results: list[Result]) -> None:
    while True:
        async with _lock:
            if _state["sent"] >= TOTAL:
                return
            _state["sent"] += 1
        resp = await client.post(f"{TARGET}/users", json={"name": "u"})
        if resp.status_code == 201:
            results.append((201, resp.json()["id"]))
        else:
            results.append((resp.status_code, None))


async def main() -> None:
    results: list[Result] = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        await asyncio.gather(*[_worker(client, results) for _ in range(CONCURRENCY)])
    created = [i for s, i in results if s == 201 and i is not None]
    conflicts = sum(1 for s, _ in results if s == 409)
    distinct = len(set(created))
    print(f"target={TARGET} total_sent={_state['sent']}")
    print(f"created(201)={len(created)} conflicts(409)={conflicts}")
    print(f"distinct_ids={distinct} duplicate_ids={len(created) - distinct}")
    if conflicts or len(created) != distinct:
        print(">>> 衝突を観測しました（stage1 の素朴解）")
    else:
        print(">>> 衝突なし（stage2 の修正後）")


if __name__ == "__main__":
    asyncio.run(main())
