# ユーザーID発行API 教材 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 既存の FastAPI/PostgreSQL/Docker 基盤を流用し、題材を `Item` CRUD から「ユーザーID発行」へ置き換え、(1) 単一サーバーで動く穴埋め式エンドポイントと (2) 並列化しても衝突しない解答例を、テストとデモで体験できる初心者向け教材を作る。

**Architecture:** ID発行ロジックを `IdIssuer` プロトコルで差し替え可能にし、共通コア（User モデル/DB/スキーマ/ルーティング）を共有したまま「出題用（スタブ）」と「解答例（stage1/stage2）」を `ID_STRATEGY` 設定で切り替える。ID は `ミリ秒(41bit) + worker-id(6bit) + シーケンス(12bit)` を base62 で10文字固定長エンコードしたもの。stage1（worker-id 無し＝全プロセス worker_id=0）は並列下で構造的に衝突し、stage2（プロセス毎に distinct な worker-id）は原理的に衝突しない。

**Tech Stack:** Python 3.14 / uv / FastAPI / SQLModel / SQLAlchemy(async) / psycopg3 / Alembic / PostgreSQL 18 / pytest(+asyncio) / Ruff / mypy(strict) / Docker Compose / nginx(デモLB)。

## Global Constraints

- Python `>=3.14`。依存追加は最小限（YAGNI）。本計画では**新規ランタイム依存を増やさない**（nginx はイメージ、httpx は既存 dev 依存）。
- すべてのコマンドは**コンテナ内**で実行する：`docker compose run --rm app uv run <cmd>`。
- 静的解析ゲートを常に緑に保つ：`ruff check .` / `ruff format .` / `mypy app` / `pytest`。Ruff line-length=88、mypy strict。
- ID 文字集合（ASCII順＝値順）: `ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"`（62文字）。
- ID 構造（合計59bit、`62^10 ≈ 8.39e17` 内）: `ID_LENGTH=10`, `SEQUENCE_BITS=12`(`MAX_SEQUENCE=4095`), `WORKER_BITS=6`(`MAX_WORKER_ID=63`), `WORKER_SHIFT=12`, `MS_SHIFT=18`。`value = (ms << 18) | (worker_id << 12) | sequence`。
- 時刻: ミリ秒。`EPOCH_MS = 1735689600000`（2025-01-01T00:00:00Z）。`MAX_MS = 2**41 - 1`（約70年、〜2094年）。
- stage2 は**1コンテナ＝1 worker-id**（uvicorn の worker は1プロセス）。複数 worker プロセスを1コンテナで動かさない。
- CLAUDE.md 4原則（KISS / YAGNI / DRY＋直交性 / 対称性）を遵守。出題/解答・素朴解/正解は対称に表現し、差分は worker-id の有無のみ。

---

## ファイル構成

**新規作成**
- `app/models/user.py` — User テーブル（`id: str` PK 10文字）
- `app/schemas/user.py` — `UserCreate` / `UserRead`
- `app/crud/user.py` — `create_user` / `get_user` / `list_users`
- `app/idgen/__init__.py` — 空
- `app/idgen/base.py` — 定数・`encode_base62`/`decode_base62`・`IdIssuer` プロトコル・`Clock`
- `app/idgen/generator.py` — `UserIdGenerator`（解答例：stage1=worker_id 0 / stage2=distinct）
- `app/idgen/problem.py` — `ProblemIssuer`（出題用スタブ）
- `app/idgen/factory.py` — `build_issuer(settings) -> IdIssuer`
- `app/api/routes_user.py` — `/users` ルーター＋`get_issuer` 依存
- `tests/test_idgen_base.py` / `tests/test_idgen_generator.py` / `tests/test_idgen_collision.py` / `tests/test_idgen_problem.py`
- `tests/test_crud_user.py` / `tests/test_api_users.py`
- `compose.demo.yaml` / `demo/nginx.conf` / `scripts/collision_demo.py`
- `migrations/versions/0001_create_users.py`（初期マイグレーションを置換）

**変更**
- `app/main.py` — `create_app(issuer)` ファクトリ化、user ルーター結線
- `app/core/config.py` — `id_strategy` / `worker_id` 追加
- `migrations/env.py` — import を `item` → `user`
- `tests/conftest.py` — metadata 登録 import を `item` → `user`
- `compose.yaml` — `app` に `ID_STRATEGY`、`solution` サービス追加
- `README.md` — 教材構成・実行手順・衝突デモ

**削除**
- `app/models/item.py` / `app/schemas/item.py` / `app/crud/item.py` / `app/api/routes_item.py`
- `tests/test_api_items.py` / `tests/test_crud_item.py`
- `migrations/versions/15b778dd63a3_create_items_table.py`

---

### Task 1: User 永続化層（model / schema / crud）に置き換え

**Files:**
- Create: `app/models/user.py`, `app/schemas/user.py`, `app/crud/user.py`, `tests/test_crud_user.py`
- Modify: `tests/conftest.py:9`（`from app.models import item` → `user`）
- Delete: `app/models/item.py`, `app/schemas/item.py`, `app/crud/item.py`, `tests/test_crud_item.py`, `tests/test_api_items.py`

**Interfaces:**
- Produces: `User`（属性 `id: str`, `name: str`, `created_at: datetime`）／`UserCreate(name: str)`／`UserRead(id,name,created_at)`／`create_user(session, *, user_id: str, name: str) -> User`, `get_user(session, user_id: str) -> User | None`, `list_users(session, limit=100, offset=0) -> list[User]`。

- [ ] **Step 1: User モデル・スキーマを作成**

`app/models/user.py`:
```python
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(primary_key=True, max_length=10)
    name: str
    created_at: datetime = Field(default_factory=_utcnow)
```

`app/schemas/user.py`:
```python
from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str


class UserRead(BaseModel):
    id: str
    name: str
    created_at: datetime
```

- [ ] **Step 2: crud のテストを書く（失敗させる）**

`tests/test_crud_user.py`:
```python
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
```

- [ ] **Step 3: conftest の metadata 登録 import を user に変更**

`tests/conftest.py` の `from app.models import item  # noqa: F401  metadata 登録` を次へ置換:
```python
from app.models import user  # noqa: F401  metadata 登録
```

- [ ] **Step 4: テストが失敗することを確認**

Run: `docker compose run --rm app uv run pytest tests/test_crud_user.py -v`
Expected: FAIL（`app.crud.user` が無い / ImportError）

- [ ] **Step 5: crud を実装**

`app/crud/user.py`:
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.user import User


async def create_user(session: AsyncSession, *, user_id: str, name: str) -> User:
    user = User(id=user_id, name=name)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user(session: AsyncSession, user_id: str) -> User | None:
    return await session.get(User, user_id)


async def list_users(
    session: AsyncSession, limit: int = 100, offset: int = 0
) -> list[User]:
    result = await session.execute(
        select(User).order_by(User.id).offset(offset).limit(limit)
    )
    return list(result.scalars().all())
```

- [ ] **Step 6: 旧 Item 関連ファイルを削除**

```bash
git rm app/models/item.py app/schemas/item.py app/crud/item.py \
       tests/test_crud_item.py tests/test_api_items.py
```

- [ ] **Step 7: テストが通ることを確認**

Run: `docker compose run --rm app uv run pytest tests/test_crud_user.py -v`
Expected: PASS（3件）

- [ ] **Step 8: コミット**

```bash
git add app/models/user.py app/schemas/user.py app/crud/user.py \
        tests/test_crud_user.py tests/conftest.py
git commit -m "feat: replace Item with User persistence layer"
```

---

### Task 2: Alembic 初期マイグレーションを users に置換

**Files:**
- Create: `migrations/versions/0001_create_users.py`
- Modify: `migrations/env.py:9`（import を `item` → `user`）
- Delete: `migrations/versions/15b778dd63a3_create_items_table.py`

**Interfaces:** Produces: head リビジョン `0001_create_users`（`users` テーブル）。

- [ ] **Step 1: env.py の metadata 登録 import を user に変更**

`migrations/env.py` の `from app.models import item  # noqa: F401  models を import して metadata に登録` を次へ置換:
```python
from app.models import user  # noqa: F401  models を import して metadata に登録
```

- [ ] **Step 2: 旧マイグレーションを削除**

```bash
git rm migrations/versions/15b778dd63a3_create_items_table.py
```

- [ ] **Step 3: 新しい初期マイグレーションを作成**

`migrations/versions/0001_create_users.py`:
```python
"""create users table

Revision ID: 0001_create_users
Revises:
Create Date: 2026-06-28 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "0001_create_users"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=10), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("users")
```

- [ ] **Step 4: DB をリセットしてマイグレーション適用を確認**

Run:
```bash
docker compose down -v
docker compose run --rm app uv run alembic upgrade head
```
Expected: `Running upgrade -> 0001_create_users, create users table` のログ。エラーなし。

- [ ] **Step 5: コミット**

```bash
git add migrations/env.py migrations/versions/0001_create_users.py
git commit -m "feat: replace initial migration with users table"
```

---

### Task 3: ID コーデック層（`idgen/base.py`）

**Files:**
- Create: `app/idgen/__init__.py`（空）, `app/idgen/base.py`, `tests/test_idgen_base.py`

**Interfaces:**
- Produces: 定数（`ALPHABET`,`ID_LENGTH`,`SEQUENCE_BITS`,`MAX_SEQUENCE`,`SEQUENCE_MASK`,`WORKER_BITS`,`MAX_WORKER_ID`,`WORKER_SHIFT`,`MS_SHIFT`,`EPOCH_MS`,`MAX_MS`）／`encode_base62(value: int, length: int = ID_LENGTH) -> str`／`decode_base62(text: str) -> int`／`Clock = Callable[[], int]`／`class IdIssuer(Protocol): def issue(self) -> str: ...`。

- [ ] **Step 1: 空 `app/idgen/__init__.py` を作成**

```bash
mkdir -p app/idgen && : > app/idgen/__init__.py
```

- [ ] **Step 2: コーデックのテストを書く**

`tests/test_idgen_base.py`:
```python
import pytest

from app.idgen.base import (
    ID_LENGTH,
    decode_base62,
    encode_base62,
)


def test_encode_is_fixed_length_and_charset():
    s = encode_base62(0)
    assert s == "0000000000"
    assert len(s) == ID_LENGTH


def test_encode_decode_roundtrip():
    for v in [0, 1, 61, 62, 12345, 62**10 - 1]:
        assert decode_base62(encode_base62(v)) == v


def test_lexicographic_order_matches_value_order():
    smaller = encode_base62(1000)
    larger = encode_base62(2000)
    assert smaller < larger  # 素朴な文字列比較で値順になる


def test_encode_rejects_too_large_value():
    with pytest.raises(ValueError):
        encode_base62(62**10)


def test_encode_rejects_negative_value():
    with pytest.raises(ValueError):
        encode_base62(-1)
```

- [ ] **Step 3: テストが失敗することを確認**

Run: `docker compose run --rm app uv run pytest tests/test_idgen_base.py -v`
Expected: FAIL（`app.idgen.base` が無い）

- [ ] **Step 4: `app/idgen/base.py` を実装**

```python
from collections.abc import Callable
from typing import Protocol

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
_BASE = len(ALPHABET)  # 62
_INDEX = {ch: i for i, ch in enumerate(ALPHABET)}

ID_LENGTH = 10

SEQUENCE_BITS = 12
MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1  # 4095
SEQUENCE_MASK = MAX_SEQUENCE

WORKER_BITS = 6
MAX_WORKER_ID = (1 << WORKER_BITS) - 1  # 63

WORKER_SHIFT = SEQUENCE_BITS           # 12
MS_SHIFT = WORKER_BITS + SEQUENCE_BITS  # 18

EPOCH_MS = 1735689600000  # 2025-01-01T00:00:00Z
MAX_MS = (1 << 41) - 1

_MAX_VALUE = _BASE**ID_LENGTH - 1

Clock = Callable[[], int]


def encode_base62(value: int, length: int = ID_LENGTH) -> str:
    if value < 0:
        raise ValueError("value must be non-negative")
    if value > _MAX_VALUE:
        raise ValueError(f"value too large for {length} base62 chars")
    chars = []
    for _ in range(length):
        value, rem = divmod(value, _BASE)
        chars.append(ALPHABET[rem])
    return "".join(reversed(chars))


def decode_base62(text: str) -> int:
    value = 0
    for ch in text:
        value = value * _BASE + _INDEX[ch]
    return value


class IdIssuer(Protocol):
    def issue(self) -> str: ...
```

- [ ] **Step 5: テストが通ることを確認**

Run: `docker compose run --rm app uv run pytest tests/test_idgen_base.py -v`
Expected: PASS（5件）

- [ ] **Step 6: コミット**

```bash
git add app/idgen/__init__.py app/idgen/base.py tests/test_idgen_base.py
git commit -m "feat: add base62 codec and id field layout constants"
```

---

### Task 4: 解答例ジェネレータ `UserIdGenerator`

**Files:**
- Create: `app/idgen/generator.py`, `tests/test_idgen_generator.py`

**Interfaces:**
- Consumes: `app.idgen.base` の定数・`encode_base62`・`decode_base62`・`Clock`。
- Produces: `class UserIdGenerator:` `__init__(self, worker_id: int, *, now_ms: Clock | None = None, rng: random.Random | None = None)`、メソッド `issue(self) -> str`。worker_id 範囲外で `ValueError`。`issue` は `IdIssuer` を満たす。

- [ ] **Step 1: ジェネレータのテストを書く**

`tests/test_idgen_generator.py`:
```python
import random
import re

import pytest

from app.idgen.base import EPOCH_MS, MAX_SEQUENCE, MAX_WORKER_ID, decode_base62
from app.idgen.generator import UserIdGenerator

ID_RE = re.compile(r"^[0-9A-Za-z]{10}$")


def _fixed_clock(ms_since_epoch: int):
    return lambda: EPOCH_MS + ms_since_epoch


def test_issue_matches_format():
    gen = UserIdGenerator(0, now_ms=_fixed_clock(1000), rng=random.Random(0))
    assert ID_RE.match(gen.issue())


def test_single_generator_unique_within_one_ms():
    gen = UserIdGenerator(0, now_ms=_fixed_clock(7), rng=random.Random(0))
    ids = [gen.issue() for _ in range(MAX_SEQUENCE + 1)]  # 4096 件
    assert len(set(ids)) == MAX_SEQUENCE + 1


def test_ids_sortable_by_issue_order():
    clock = {"ms": 0}
    gen = UserIdGenerator(0, now_ms=lambda: EPOCH_MS + clock["ms"], rng=random.Random(0))
    first = gen.issue()
    clock["ms"] = 5
    second = gen.issue()
    assert first < second  # 後発のほうが文字列順で大きい


def test_worker_id_occupies_worker_bits():
    gen = UserIdGenerator(5, now_ms=_fixed_clock(3), rng=random.Random(0))
    value = decode_base62(gen.issue())
    assert (value >> 12) & MAX_WORKER_ID == 5


def test_rejects_out_of_range_worker_id():
    with pytest.raises(ValueError):
        UserIdGenerator(MAX_WORKER_ID + 1)


def test_rejects_timestamp_before_epoch():
    gen = UserIdGenerator(0, now_ms=lambda: EPOCH_MS - 1, rng=random.Random(0))
    with pytest.raises(ValueError):
        gen.issue()
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `docker compose run --rm app uv run pytest tests/test_idgen_generator.py -v`
Expected: FAIL（`app.idgen.generator` が無い）

- [ ] **Step 3: `app/idgen/generator.py` を実装**

```python
import random
import time

from app.idgen.base import (
    EPOCH_MS,
    MAX_MS,
    MAX_SEQUENCE,
    MAX_WORKER_ID,
    MS_SHIFT,
    SEQUENCE_MASK,
    WORKER_SHIFT,
    Clock,
    encode_base62,
)


def _default_clock() -> int:
    return time.time_ns() // 1_000_000


class UserIdGenerator:
    """発行順ソート可能・並列安全な ID ジェネレータ（解答例）。

    worker_id をプロセス毎に distinct にすれば、同一ミリ秒でも
    `(ms, worker_id, sequence)` が一意になり原理的に衝突しない（stage2）。
    全プロセスが worker_id=0 を使うと並列下で構造的に衝突する（stage1）。
    """

    def __init__(
        self,
        worker_id: int,
        *,
        now_ms: Clock | None = None,
        rng: random.Random | None = None,
    ) -> None:
        if not 0 <= worker_id <= MAX_WORKER_ID:
            raise ValueError(f"worker_id must be in 0..{MAX_WORKER_ID}")
        self._worker_id = worker_id
        self._now_ms: Clock = now_ms or _default_clock
        self._rng = rng or random.Random()
        self._current_ms = -1
        self._seq_base = 0
        self._counter = 0

    def issue(self) -> str:
        ms = self._now_ms() - EPOCH_MS
        if ms < 0 or ms > MAX_MS:
            raise ValueError("timestamp out of representable range")
        if ms != self._current_ms:
            self._current_ms = ms
            self._seq_base = self._rng.randrange(MAX_SEQUENCE + 1)
            self._counter = 0
        else:
            self._counter += 1
            if self._counter > MAX_SEQUENCE:
                # この ms のシーケンスを使い切った。次の ms までスピンして再採番。
                while self._now_ms() - EPOCH_MS == self._current_ms:
                    pass
                return self.issue()
        sequence = (self._seq_base + self._counter) & SEQUENCE_MASK
        value = (ms << MS_SHIFT) | (self._worker_id << WORKER_SHIFT) | sequence
        return encode_base62(value)
```

- [ ] **Step 4: テストが通ることを確認**

Run: `docker compose run --rm app uv run pytest tests/test_idgen_generator.py -v`
Expected: PASS（6件）

- [ ] **Step 5: コミット**

```bash
git add app/idgen/generator.py tests/test_idgen_generator.py
git commit -m "feat: add UserIdGenerator (sortable, worker-partitioned ids)"
```

---

### Task 5: 衝突デモンストレーション（教材の核）テスト

**Files:**
- Create: `tests/test_idgen_collision.py`

**Interfaces:** Consumes: `UserIdGenerator`, `app.idgen.base` 定数。新規プロダクションコードなし（既存挙動を「壊れる/直る」観点で検証する）。

> 鳩の巣原理で**決定的に**検証する。固定クロックの同一ミリ秒では `worker_id` を固定すると採れる値は `MAX_SEQUENCE+1=4096` 通りしか無い。各ジェネレータからちょうど 4096 件引けばスピンせず全 4096 値を一巡する。

- [ ] **Step 1: 衝突/不衝突のテストを書く**

`tests/test_idgen_collision.py`:
```python
import random

from app.idgen.base import EPOCH_MS, MAX_SEQUENCE
from app.idgen.generator import UserIdGenerator

_SAME_MS = lambda: EPOCH_MS + 42  # 全ジェネレータが同一ミリ秒を見る  # noqa: E731
_PER_GEN = MAX_SEQUENCE + 1  # 4096


def test_stage1_naive_collides_across_processes():
    # worker-id を持たない素朴解＝全プロセス worker_id=0。
    gen_a = UserIdGenerator(0, now_ms=_SAME_MS, rng=random.Random(1))
    gen_b = UserIdGenerator(0, now_ms=_SAME_MS, rng=random.Random(2))
    ids = [gen_a.issue() for _ in range(_PER_GEN)]
    ids += [gen_b.issue() for _ in range(_PER_GEN)]
    # 8192 件発行したが distinct 値は最大 4096 → 必ず重複する。
    assert len(ids) == 2 * _PER_GEN
    assert len(set(ids)) <= _PER_GEN
    assert len(set(ids)) < len(ids)  # 衝突が観測される


def test_stage2_distinct_worker_ids_never_collide():
    # 修正：プロセス毎に distinct な worker_id を付与。
    gen_a = UserIdGenerator(0, now_ms=_SAME_MS, rng=random.Random(1))
    gen_b = UserIdGenerator(1, now_ms=_SAME_MS, rng=random.Random(1))
    ids = [gen_a.issue() for _ in range(_PER_GEN)]
    ids += [gen_b.issue() for _ in range(_PER_GEN)]
    # worker ビットが異なるため全 8192 件が distinct。
    assert len(set(ids)) == 2 * _PER_GEN
```

- [ ] **Step 2: テストが通ることを確認（既存実装で成立する）**

Run: `docker compose run --rm app uv run pytest tests/test_idgen_collision.py -v`
Expected: PASS（2件）。stage1 は重複あり、stage2 は重複なし。

- [ ] **Step 3: コミット**

```bash
git add tests/test_idgen_collision.py
git commit -m "test: demonstrate stage1 collision and stage2 uniqueness"
```

---

### Task 6: 出題用スタブ `ProblemIssuer`

**Files:**
- Create: `app/idgen/problem.py`, `tests/test_idgen_problem.py`

**Interfaces:** Produces: `class ProblemIssuer:` `def issue(self) -> str`（学習者が実装する穴埋め。初期状態は `NotImplementedError`）。`IdIssuer` を満たす型である。

- [ ] **Step 1: スタブの足場テストを書く**

`tests/test_idgen_problem.py`:
```python
import pytest

from app.idgen.problem import ProblemIssuer


def test_problem_issuer_is_not_implemented_yet():
    # 学習者がここを実装する。未実装のうちは NotImplementedError。
    with pytest.raises(NotImplementedError):
        ProblemIssuer().issue()
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `docker compose run --rm app uv run pytest tests/test_idgen_problem.py -v`
Expected: FAIL（`app.idgen.problem` が無い）

- [ ] **Step 3: `app/idgen/problem.py` を実装**

```python
class ProblemIssuer:
    """出題用スタブ。学習者は `issue` を実装してユーザーIDを返す。

    要件（詳細は docs/superpowers/specs の設計書を参照）:
      - base62（0-9A-Za-z）10文字。
      - 発行順に文字列ソート可能（先頭に時刻成分）。
      - 連番を避ける程度の予測困難性。
      - ステージ2では、並列化（複数コンテナ）でも衝突しないようにする。
        ヒント: プロセス毎に distinct な worker-id を設定 `WORKER_ID` から受け取る。
    """

    def issue(self) -> str:
        raise NotImplementedError("ここにID発行ロジックを実装してください")
```

- [ ] **Step 4: テストが通ることを確認**

Run: `docker compose run --rm app uv run pytest tests/test_idgen_problem.py -v`
Expected: PASS（1件）

- [ ] **Step 5: コミット**

```bash
git add app/idgen/problem.py tests/test_idgen_problem.py
git commit -m "feat: add ProblemIssuer stub for learners"
```

---

### Task 7: 設定・ファクトリ・アプリ生成（`create_app`）

**Files:**
- Modify: `app/core/config.py`, `app/main.py`
- Create: `app/idgen/factory.py`

**Interfaces:**
- Consumes: `Settings`, `ProblemIssuer`, `UserIdGenerator`, `IdIssuer`, `routes_health`, `routes_user`(Task 8 で作成。本タスクでは結線のみ先に書くと import エラーになるため、routes_user 結線は Task 8 で行う)。
- Produces: `Settings.id_strategy: Literal["problem","stage1","stage2"]`, `Settings.worker_id: int`／`build_issuer(settings: Settings) -> IdIssuer`／`create_app(issuer: IdIssuer) -> FastAPI`（`app.state.issuer` に保持）、モジュール変数 `app`。

> 注: 本タスクでは `create_app` に health のみ結線し、`app` を起動可能に保つ。`/users` ルーターは Task 8 で結線する（タスク境界をまたぐ import エラーを避けるため）。

- [ ] **Step 1: 設定に id_strategy / worker_id を追加**

`app/core/config.py` を次へ変更（`Settings` 本体を置換）:
```python
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/app"
    id_strategy: Literal["problem", "stage1", "stage2"] = "problem"
    worker_id: int = 0


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 2: `build_issuer` ファクトリを作成**

`app/idgen/factory.py`:
```python
from app.core.config import Settings
from app.idgen.base import IdIssuer
from app.idgen.generator import UserIdGenerator
from app.idgen.problem import ProblemIssuer


def build_issuer(settings: Settings) -> IdIssuer:
    if settings.id_strategy == "problem":
        return ProblemIssuer()
    if settings.id_strategy == "stage1":
        # 素朴解: worker-id 無し（全プロセス 0）。並列下で衝突する。
        return UserIdGenerator(worker_id=0)
    # stage2: プロセス毎に distinct な worker-id。
    return UserIdGenerator(worker_id=settings.worker_id)
```

- [ ] **Step 3: `app/main.py` を `create_app` ファクトリへ変更**

```python
from fastapi import FastAPI

from app.api import routes_health
from app.core.config import get_settings
from app.idgen.base import IdIssuer
from app.idgen.factory import build_issuer


def create_app(issuer: IdIssuer) -> FastAPI:
    application = FastAPI(title="uv_recruit user-id API")
    application.state.issuer = issuer
    application.include_router(routes_health.router)

    @application.get("/")
    async def root() -> dict[str, str]:
        return {"message": "ok"}

    return application


app = create_app(build_issuer(get_settings()))
```

- [ ] **Step 4: 既存テストとゲートが緑であることを確認**

Run: `docker compose run --rm app uv run pytest -q && docker compose run --rm app uv run mypy app`
Expected: PASS（health/idgen/crud のテストが通る）、mypy エラーなし。

- [ ] **Step 5: コミット**

```bash
git add app/core/config.py app/idgen/factory.py app/main.py
git commit -m "feat: app factory and issuer selection via ID_STRATEGY"
```

---

### Task 8: `/users` ルーターと API テスト

**Files:**
- Create: `app/api/routes_user.py`, `tests/test_api_users.py`
- Modify: `app/main.py`（user ルーター結線）
- Delete: `app/api/routes_item.py`

**Interfaces:**
- Consumes: `crud.user`, `get_session`, `IdIssuer`（`request.app.state.issuer`）, `UserCreate`/`UserRead`。
- Produces: `POST /users`(201, body `UserRead`／衝突時 409)、`GET /users/{user_id}`(200／404)。依存 `get_issuer(request) -> IdIssuer`。

- [ ] **Step 1: 旧 item ルーターを削除**

```bash
git rm app/api/routes_item.py
```

- [ ] **Step 2: API テストを書く**

`tests/test_api_users.py`:
```python
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
```

- [ ] **Step 3: `app/main.py` に user ルーターを結線**

`app/main.py` の import に追加し、`create_app` 内に結線:
```python
from app.api import routes_health, routes_user
```
`application.include_router(routes_health.router)` の直後に:
```python
    application.include_router(routes_user.router)
```

- [ ] **Step 4: テストが失敗することを確認**

Run: `docker compose run --rm app uv run pytest tests/test_api_users.py -v`
Expected: FAIL（`app.api.routes_user` が無い）

- [ ] **Step 5: `app/api/routes_user.py` を実装**

```python
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import user as crud
from app.db.session import get_session
from app.idgen.base import IdIssuer
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


def get_issuer(request: Request) -> IdIssuer:
    return cast(IdIssuer, request.app.state.issuer)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    session: AsyncSession = Depends(get_session),
    issuer: IdIssuer = Depends(get_issuer),
) -> UserRead:
    user_id = issuer.issue()
    try:
        user = await crud.create_user(session, user_id=user_id, name=data.name)
    except IntegrityError as exc:
        # 一意制約は「衝突の検出器」であって一意性の保証手段ではない。
        # アプリ側ロジックが衝突しなければ、ここには到達しない。
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="user id collision"
        ) from exc
    return UserRead.model_validate(user, from_attributes=True)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: str, session: AsyncSession = Depends(get_session)
) -> UserRead:
    user = await crud.get_user(session, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user, from_attributes=True)
```

- [ ] **Step 6: テストが通ることを確認**

Run: `docker compose run --rm app uv run pytest tests/test_api_users.py -v`
Expected: PASS（4件）

- [ ] **Step 7: 全テスト・全ゲートを確認**

Run:
```bash
docker compose run --rm app uv run ruff check .
docker compose run --rm app uv run ruff format --check .
docker compose run --rm app uv run mypy app
docker compose run --rm app uv run pytest -q
```
Expected: すべて PASS。

- [ ] **Step 8: コミット**

```bash
git add app/api/routes_user.py app/main.py tests/test_api_users.py
git commit -m "feat: add /users endpoints with issuer injection"
```

---

### Task 9: Compose に出題用/解答例サービスを用意

**Files:**
- Modify: `compose.yaml`

**Interfaces:** Produces: `app`（出題用, `ID_STRATEGY=problem`, host 8000）／`solution`（解答例, `ID_STRATEGY=stage2`, `WORKER_ID=1`, host 8001）。両者は同一イメージ・同一 DB。

- [ ] **Step 1: `compose.yaml` を更新**

`app` サービスの `environment` に `ID_STRATEGY` を追加し、`solution` サービスを追記:
```yaml
  app:
    build: .
    environment:
      DATABASE_URL: postgresql+psycopg://postgres:postgres@db:5432/app
      ID_STRATEGY: ${ID_STRATEGY:-problem}
    volumes:
      - .:/app
      - venv:/app/.venv
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy

  solution:
    build: .
    environment:
      DATABASE_URL: postgresql+psycopg://postgres:postgres@db:5432/app
      ID_STRATEGY: stage2
      WORKER_ID: "1"
    volumes:
      - .:/app
      - venv:/app/.venv
    ports:
      - "8001:8000"
    depends_on:
      db:
        condition: service_healthy
```

- [ ] **Step 2: 両サービスが起動し応答することを確認**

Run:
```bash
docker compose up -d --build db solution
docker compose run --rm app uv run python -c "import httpx; print(httpx.post('http://solution:8000/users', json={'name':'x'}).json())"
docker compose down
```
Expected: `solution` が 10文字 ID を返す JSON を出力。

- [ ] **Step 3: コミット**

```bash
git add compose.yaml
git commit -m "feat: add problem and solution compose services"
```

---

### Task 10: 並列衝突デモ（LB + 複数ワーカー + 観測スクリプト）

**Files:**
- Create: `compose.demo.yaml`, `demo/nginx.conf`, `scripts/collision_demo.py`

**Interfaces:** Produces: 3 つの app（`app1/app2/app3`, `WORKER_ID=1/2/3`, `ID_STRATEGY` は env 切替）＋ nginx `lb`（host 8080 → 各 app:8000 ラウンドロビン）。`scripts/collision_demo.py` が LB に並列 POST して 201/409/重複を集計。

- [ ] **Step 1: nginx 設定を作成**

`demo/nginx.conf`:
```nginx
events {}
http {
  upstream app_backend {
    server app1:8000;
    server app2:8000;
    server app3:8000;
  }
  server {
    listen 8080;
    location / {
      proxy_pass http://app_backend;
    }
  }
}
```

- [ ] **Step 2: デモ用 compose を作成**

`compose.demo.yaml`:
```yaml
services:
  app1:
    build: .
    environment:
      DATABASE_URL: postgresql+psycopg://postgres:postgres@db:5432/app
      ID_STRATEGY: ${ID_STRATEGY:-stage1}
      WORKER_ID: "1"
    volumes:
      - .:/app
      - venv:/app/.venv
    depends_on:
      db:
        condition: service_healthy

  app2:
    build: .
    environment:
      DATABASE_URL: postgresql+psycopg://postgres:postgres@db:5432/app
      ID_STRATEGY: ${ID_STRATEGY:-stage1}
      WORKER_ID: "2"
    volumes:
      - .:/app
      - venv:/app/.venv
    depends_on:
      db:
        condition: service_healthy

  app3:
    build: .
    environment:
      DATABASE_URL: postgresql+psycopg://postgres:postgres@db:5432/app
      ID_STRATEGY: ${ID_STRATEGY:-stage1}
      WORKER_ID: "3"
    volumes:
      - .:/app
      - venv:/app/.venv
    depends_on:
      db:
        condition: service_healthy

  lb:
    image: nginx:alpine
    volumes:
      - ./demo/nginx.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "8080:8080"
    depends_on:
      - app1
      - app2
      - app3
```

> `ID_STRATEGY=stage1`（既定）では3台とも worker_id=0 扱い → 衝突する。`ID_STRATEGY=stage2` では各台が `WORKER_ID` 1/2/3 を使う → 衝突しない。

- [ ] **Step 3: 観測スクリプトを作成**

`scripts/collision_demo.py`:
```python
import asyncio
import os

import httpx

TARGET = os.environ.get("TARGET_URL", "http://localhost:8080")
TOTAL = int(os.environ.get("TOTAL", "3000"))
CONCURRENCY = int(os.environ.get("CONCURRENCY", "50"))


async def _worker(client: httpx.AsyncClient, results: list[tuple[int, str | None]]) -> None:
    while True:
        try:
            idx = _worker.counter  # type: ignore[attr-defined]
        except AttributeError:
            idx = 0
        # シンプルなカウンタ消費
        async with _lock:
            if _state["sent"] >= TOTAL:
                return
            _state["sent"] += 1
        resp = await client.post(f"{TARGET}/users", json={"name": "u"})
        if resp.status_code == 201:
            results.append((201, resp.json()["id"]))
        else:
            results.append((resp.status_code, None))


_lock = asyncio.Lock()
_state = {"sent": 0}


async def main() -> None:
    results: list[tuple[int, str | None]] = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        await asyncio.gather(
            *[_worker(client, results) for _ in range(CONCURRENCY)]
        )
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
```

- [ ] **Step 4: 素朴解（stage1）で衝突を観測**

Run:
```bash
docker compose down -v
ID_STRATEGY=stage1 docker compose -f compose.yaml -f compose.demo.yaml up -d --build db app1 app2 app3 lb
docker compose run --rm -e TARGET_URL=http://lb:8080 app uv run python scripts/collision_demo.py
docker compose -f compose.yaml -f compose.demo.yaml down -v
```
Expected: `conflicts(409)` が 1 以上、または `duplicate_ids` が 1 以上 →「衝突を観測しました」。

- [ ] **Step 5: 修正後（stage2）で衝突しないことを確認**

Run:
```bash
docker compose down -v
ID_STRATEGY=stage2 docker compose -f compose.yaml -f compose.demo.yaml up -d --build db app1 app2 app3 lb
docker compose run --rm -e TARGET_URL=http://lb:8080 app uv run python scripts/collision_demo.py
docker compose -f compose.yaml -f compose.demo.yaml down -v
```
Expected: `conflicts(409)=0`, `duplicate_ids=0` →「衝突なし」。

- [ ] **Step 6: コミット**

```bash
git add compose.demo.yaml demo/nginx.conf scripts/collision_demo.py
git commit -m "feat: parallel collision demo (lb + workers + observer script)"
```

---

### Task 11: ドキュメント整備・最終ゲート・引き継ぎ整理

**Files:**
- Modify: `README.md`

**Interfaces:** Produces: 教材の使い方（2ステージ・出題/解答・衝突デモ）を README に記載。（旧 `tasks.md` は計画着手前に削除済み。）

- [ ] **Step 1: README を教材内容へ更新**

`README.md` に次の節を追加（既存の起動/開発コマンド節は維持し、`Item` への言及を `users` に置換）:
```markdown
## 教材：ユーザーID発行API

設計書: `docs/superpowers/specs/2026-06-28-user-id-issuance-teaching-design.md`

### ステージ1：ID発行ロジックを書く
- 出題用 API（`ID_STRATEGY=problem`）の `app/idgen/problem.py` の `ProblemIssuer.issue` を実装する。
- 要件: base62(0-9A-Za-z) 10文字 / 発行順ソート可 / 連番回避 / 最大100億件以上。
- 確認: `docker compose run --rm app uv run pytest tests/test_idgen_problem.py`

### ステージ2：並列化しても衝突させない
- 複数コンテナ（LB配下）で発行しても ID が重複しないようにする。
- 解答例: `app/idgen/generator.py`（プロセス毎に distinct な `WORKER_ID`）。
- 衝突を観測 → 修正を確認:
  ```bash
  # 素朴解（衝突する）
  ID_STRATEGY=stage1 docker compose -f compose.yaml -f compose.demo.yaml up -d --build db app1 app2 app3 lb
  docker compose run --rm -e TARGET_URL=http://lb:8080 app uv run python scripts/collision_demo.py
  # 修正後（衝突しない）
  ID_STRATEGY=stage2 docker compose -f compose.yaml -f compose.demo.yaml up -d --build db app1 app2 app3 lb
  docker compose run --rm -e TARGET_URL=http://lb:8080 app uv run python scripts/collision_demo.py
  ```

### 解答例 API
`docker compose up solution`（http://localhost:8001/docs）で stage2 実装を直接試せる。
```

- [ ] **Step 2: 全ゲートを最終確認**

Run:
```bash
docker compose run --rm app uv run ruff check .
docker compose run --rm app uv run ruff format --check .
docker compose run --rm app uv run mypy app
docker compose run --rm app uv run pytest -q
```
Expected: すべて PASS。

- [ ] **Step 3: コミット**

```bash
git add README.md
git commit -m "docs: document user-id issuance teaching material"
```

---

## Self-Review（計画作成者による点検結果）

- **Spec coverage**: 目的/2ステージ(§2)→Task6/8・Task5・Task10。ID要件(§3)→Task3/4。ID構造(§4)→Task3/4 の定数とパッキング。衝突観測の定量(§5)→Task5（鳩の巣で決定的）＋Task10（実機）。リポ構成(§6 出題/解答併置)→Task7 factory＋Task9 services。テスト方針(§7)→各 Task の TDD。原則対応(§8)→共通コア共有＋worker-id 差分。未確定(§9 worker-id 機構/LB)→Task10 で nginx＋明示 WORKER_ID として確定。
- **Placeholder scan**: 各ステップに実コードを記載。`ProblemIssuer` の `NotImplementedError` は仕様上の意図的スタブ（学習者の穴埋め）。
- **Type consistency**: `IdIssuer.issue() -> str`、`build_issuer(Settings)->IdIssuer`、`create_app(IdIssuer)->FastAPI`、`UserIdGenerator(worker_id, *, now_ms, rng)`、`create_user(session,*,user_id,name)` を全タスクで一致させた。`get_issuer` は `cast(IdIssuer, ...)` で mypy strict 対応。

## 既知の留意点（実装時に注意）

- stage2 は **1コンテナ=1プロセス=1 worker_id**。uvicorn を多 worker で動かすと同一 WORKER_ID を共有して衝突するため、デモは1 worker（`--reload` 既定）で行う。
- 並列衝突は実機(Task10)では負荷依存で確率的。`TOTAL`/`CONCURRENCY` を上げれば再現性が増す。決定的な教材的証明は Task5 の単体テストが担う。
- dev で旧 `items` テーブルが残る場合は `docker compose down -v` でリセットしてから Task2 のマイグレーションを適用する。
