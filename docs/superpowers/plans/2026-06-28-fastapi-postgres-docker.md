# FastAPI + PostgreSQL + Docker サンプルアプリ Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Docker だけで起動・開発・テストできる、PostgreSQL を使った FastAPI の `Item` CRUD サンプル API を構築する。

**Architecture:** `docker compose up` で `app`（FastAPI/uvicorn）と `db`（PostgreSQL 18）が起動。プロジェクトをバインドマウントし、`uv` をコンテナ内で実行。アプリは api / crud / db / models / schemas / core の層に分離。

**Tech Stack:** Python 3.14, uv, FastAPI 0.138.1, SQLModel 0.0.39, SQLAlchemy 2.0(async), psycopg3 3.3.4, uvicorn 0.49.0, Alembic 1.18.5, pydantic-settings, pytest 9.1.1, pytest-asyncio 1.1.0, httpx, Ruff 0.15.20, mypy 2.1.0, pre-commit 4.6.0, PostgreSQL 18.

## Global Constraints

- Python は 3.14 系を使用（Dockerfile のベースイメージ `python:3.14-slim-bookworm`）。
- すべてのコマンドはコンテナ内で実行する（ホストに Python / uv をインストールしない）。
- DB ドライバは psycopg3。接続 URL スキームは `postgresql+psycopg://`。
- 依存とツール設定（Ruff/mypy/pytest）は `pyproject.toml` に集約。
- `.venv` はバインドマウントから退避し名前付き volume に置く（`/app/.venv`）。
- Ruff で PEP8（E/W/F）+ isort(I) + pyupgrade(UP) + bugbear(B) を有効化、`line-length=88`。
- 非同期 SQLAlchemy を使用（`AsyncSession`）。
- コミットメッセージ末尾に `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` を付与。

---

### Task 1: プロジェクトスキャフォールド（pyproject.toml・補助ファイル）

**Files:**
- Create: `pyproject.toml`
- Create: `.dockerignore`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `app/__init__.py`

**Interfaces:**
- Produces: `pyproject.toml`（プロジェクト名 `app`、依存一覧、`[tool.ruff]` / `[tool.mypy]` / `[tool.pytest.ini_options]` 設定）。後続タスクの全コマンドが依存。

- [ ] **Step 1: `pyproject.toml` を作成**

```toml
[project]
name = "app"
version = "0.1.0"
description = "FastAPI + PostgreSQL + Docker sample API"
requires-python = ">=3.14"
dependencies = [
    "fastapi==0.138.1",
    "uvicorn[standard]==0.49.0",
    "sqlmodel==0.0.39",
    "psycopg[binary]==3.3.4",
    "alembic==1.18.5",
    "pydantic-settings>=2.7,<3",
]

[dependency-groups]
dev = [
    "pytest==9.1.1",
    "pytest-asyncio==1.1.0",
    "httpx>=0.28,<0.29",
    "ruff==0.15.20",
    "mypy==2.1.0",
    "pre-commit==4.6.0",
]

[tool.ruff]
line-length = 88
target-version = "py314"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "UP", "B"]

[tool.mypy]
python_version = "3.14"
plugins = ["pydantic.mypy"]
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["app"]
```

- [ ] **Step 2: `.dockerignore` を作成**

```
.git
.venv
__pycache__
*.pyc
.pytest_cache
.mypy_cache
.ruff_cache
docs
*.md
```

- [ ] **Step 3: `.gitignore` を作成**

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
.env
```

- [ ] **Step 4: `.env.example` を作成**

```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=app
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/app
```

- [ ] **Step 5: `app/__init__.py` を作成（空ファイル）**

```python
```

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .dockerignore .gitignore .env.example app/__init__.py
git commit -m "chore: scaffold project with pyproject and tooling config"
```

---

### Task 2: Docker 構成（Dockerfile・compose・entrypoint）— スタック起動

**Files:**
- Create: `Dockerfile`
- Create: `docker-entrypoint.sh`
- Create: `compose.yaml`
- Create: `app/main.py`（最小の動作確認用、Task 8 で拡張）

**Interfaces:**
- Consumes: Task 1 の `pyproject.toml`。
- Produces: 起動可能な `app` / `db` スタック。`app/main.py` に `app = FastAPI()` と `GET /` を提供（後続で health/items を追加）。

- [ ] **Step 1: `Dockerfile` を作成**

```dockerfile
FROM python:3.14-slim-bookworm

# uv バイナリを公式イメージからコピー
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

- [ ] **Step 2: `docker-entrypoint.sh` を作成**

```bash
#!/usr/bin/env bash
set -euo pipefail

# 依存を同期（バインドマウント後に実行され、.venv は volume 上に作られる）
uv sync

# DB マイグレーションを適用（migrations が存在する場合のみ）
if [ -f alembic.ini ]; then
  uv run alembic upgrade head
fi

exec "$@"
```

- [ ] **Step 3: `compose.yaml` を作成**

```yaml
services:
  db:
    image: postgres:18
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: app
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d app"]
      interval: 5s
      timeout: 5s
      retries: 10

  app:
    build: .
    environment:
      DATABASE_URL: postgresql+psycopg://postgres:postgres@db:5432/app
    volumes:
      - .:/app
      - venv:/app/.venv
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy

volumes:
  pgdata:
  venv:
```

- [ ] **Step 4: 最小の `app/main.py` を作成**

```python
from fastapi import FastAPI

app = FastAPI(title="uv_recruit sample API")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "ok"}
```

- [ ] **Step 5: スタックをビルドして起動確認**

Run: `docker compose up -d --build`
Expected: `app` と `db` が起動。`db` は healthy。

- [ ] **Step 6: ルートエンドポイントを確認**

Run: `curl -s http://localhost:8000/`
Expected: `{"message":"ok"}`

- [ ] **Step 7: uv.lock を生成（コンテナ内）**

Run: `docker compose run --rm app uv lock`
Expected: ホストに `uv.lock` が生成される（バインドマウント経由）。

- [ ] **Step 8: Commit**

```bash
git add Dockerfile docker-entrypoint.sh compose.yaml app/main.py uv.lock
git commit -m "feat: add Docker compose stack with uv-in-container setup"
```

---

### Task 3: 設定モジュール（core/config.py）

**Files:**
- Create: `app/core/__init__.py`
- Create: `app/core/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `app.core.config.Settings`（属性 `database_url: str`）と `get_settings() -> Settings`（lru_cache 済）。後続タスクが DB URL を取得するために使用。

- [ ] **Step 1: 失敗するテストを書く** — `tests/test_config.py`

```python
from app.core.config import Settings


def test_settings_reads_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h:5432/d")
    settings = Settings()
    assert settings.database_url == "postgresql+psycopg://u:p@h:5432/d"
```

- [ ] **Step 2: テスト失敗を確認**

Run: `docker compose run --rm app uv run pytest tests/test_config.py -v`
Expected: FAIL（`ModuleNotFoundError: app.core.config`）

- [ ] **Step 3: `app/core/__init__.py` を作成（空）**

```python
```

- [ ] **Step 4: `app/core/config.py` を実装**

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/app"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 5: テスト成功を確認**

Run: `docker compose run --rm app uv run pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/core/ tests/test_config.py
git commit -m "feat: add typed settings module"
```

---

### Task 4: DB セッション（db/session.py）

**Files:**
- Create: `app/db/__init__.py`
- Create: `app/db/session.py`

**Interfaces:**
- Consumes: `app.core.config.get_settings`。
- Produces:
  - `engine`（`AsyncEngine`）
  - `async_session_maker`（`async_sessionmaker[AsyncSession]`）
  - `async def get_session() -> AsyncIterator[AsyncSession]`（FastAPI 依存性）

- [ ] **Step 1: `app/db/__init__.py` を作成（空）**

```python
```

- [ ] **Step 2: `app/db/session.py` を実装**

```python
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

engine: AsyncEngine = create_async_engine(
    get_settings().database_url,
    echo=False,
    future=True,
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        yield session
```

- [ ] **Step 3: import が通ることを確認**

Run: `docker compose run --rm app uv run python -c "import app.db.session"`
Expected: エラーなく終了

- [ ] **Step 4: Commit**

```bash
git add app/db/
git commit -m "feat: add async database engine and session dependency"
```

---

### Task 5: モデルとスキーマ（Item）

**Files:**
- Create: `app/models/__init__.py`
- Create: `app/models/item.py`
- Create: `app/schemas/__init__.py`
- Create: `app/schemas/item.py`

**Interfaces:**
- Produces:
  - `app.models.item.Item`（SQLModel table。`id: int|None`(PK), `name: str`, `description: str|None`, `created_at: datetime`）
  - `app.schemas.item.ItemCreate`（`name: str`, `description: str|None=None`）
  - `app.schemas.item.ItemUpdate`（`name: str|None=None`, `description: str|None=None`）
  - `app.schemas.item.ItemRead`（`id: int`, `name: str`, `description: str|None`, `created_at: datetime`）

- [ ] **Step 1: `app/models/__init__.py` を作成（空）**

```python
```

- [ ] **Step 2: `app/models/item.py` を実装**

```python
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Item(SQLModel, table=True):
    __tablename__ = "items"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
```

- [ ] **Step 3: `app/schemas/__init__.py` を作成（空）**

```python
```

- [ ] **Step 4: `app/schemas/item.py` を実装**

```python
from datetime import datetime

from pydantic import BaseModel


class ItemCreate(BaseModel):
    name: str
    description: str | None = None


class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ItemRead(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
```

- [ ] **Step 5: import が通ることを確認**

Run: `docker compose run --rm app uv run python -c "import app.models.item, app.schemas.item"`
Expected: エラーなく終了

- [ ] **Step 6: Commit**

```bash
git add app/models/ app/schemas/
git commit -m "feat: add Item model and request/response schemas"
```

---

### Task 6: Alembic セットアップと初期マイグレーション

**Files:**
- Create: `alembic.ini`
- Create: `migrations/env.py`
- Create: `migrations/script.py.mako`
- Create: `migrations/versions/` (ディレクトリ、`.gitkeep`)

**Interfaces:**
- Consumes: `app.models.item.Item`, `app.core.config.get_settings`。
- Produces: `items` テーブルを作成する初期マイグレーション。`alembic upgrade head` で適用可能。

- [ ] **Step 1: `alembic.ini` を作成**

```ini
[alembic]
script_location = migrations
prepend_sys_path = .

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARNING
handlers = console
qualname =

[logger_sqlalchemy]
level = WARNING
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 2: `migrations/script.py.mako` を作成**

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
import sqlmodel
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: str | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 3: `migrations/env.py` を作成（async 対応 + autogenerate 用 metadata）**

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool
from sqlmodel import SQLModel

from app.core.config import get_settings
from app.models import item  # noqa: F401  models を import して metadata に登録

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


run_migrations_online()
```

- [ ] **Step 4: `migrations/versions/.gitkeep` を作成（空）**

```
```

- [ ] **Step 5: 初期マイグレーションを autogenerate（DB 起動が必要）**

Run:
```bash
docker compose up -d db
docker compose run --rm app uv run alembic revision --autogenerate -m "create items table"
```
Expected: `migrations/versions/<rev>_create_items_table.py` が生成され、`op.create_table("items", ...)` を含む。

- [ ] **Step 6: マイグレーション適用を確認**

Run: `docker compose run --rm app uv run alembic upgrade head`
Expected: エラーなく `Running upgrade ... create items table`。

- [ ] **Step 7: テーブル存在を確認**

Run: `docker compose exec db psql -U postgres -d app -c "\dt"`
Expected: `items` と `alembic_version` テーブルが表示される。

- [ ] **Step 8: Commit**

```bash
git add alembic.ini migrations/
git commit -m "feat: add alembic async migrations and initial items table"
```

---

### Task 7: CRUD レイヤ（crud/item.py）— TDD

**Files:**
- Create: `app/crud/__init__.py`
- Create: `app/crud/item.py`
- Create: `tests/conftest.py`
- Test: `tests/test_crud_item.py`

**Interfaces:**
- Consumes: `app.models.item.Item`, `app.schemas.item.ItemCreate/ItemUpdate`, `AsyncSession`。
- Produces（すべて `async`、`session: AsyncSession` を第1引数に取る）:
  - `create_item(session, data: ItemCreate) -> Item`
  - `get_item(session, item_id: int) -> Item | None`
  - `list_items(session, limit: int = 100, offset: int = 0) -> list[Item]`
  - `update_item(session, item: Item, data: ItemUpdate) -> Item`
  - `delete_item(session, item: Item) -> None`

- [ ] **Step 1: `tests/conftest.py` を作成（テスト用 DB セッション fixture）**

`Item` のテーブルを作成し、各テストで独立した `AsyncSession` を提供する。テスト用 DB は `DATABASE_URL` をそのまま利用し、関数ごとにテーブルを作成・破棄する。

```python
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import get_settings
from app.models import item  # noqa: F401  metadata 登録


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(get_settings().database_url, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()
```

- [ ] **Step 2: 失敗するテストを書く** — `tests/test_crud_item.py`

```python
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
    await crud.delete_item(session, created)
    assert await crud.get_item(session, created.id) is None
```

- [ ] **Step 3: テスト失敗を確認**

Run: `docker compose run --rm app uv run pytest tests/test_crud_item.py -v`
Expected: FAIL（`ModuleNotFoundError: app.crud.item`）

- [ ] **Step 4: `app/crud/__init__.py` を作成（空）**

```python
```

- [ ] **Step 5: `app/crud/item.py` を実装**

```python
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

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
```

- [ ] **Step 6: テスト成功を確認**

Run: `docker compose run --rm app uv run pytest tests/test_crud_item.py -v`
Expected: PASS（5 件）

- [ ] **Step 7: Commit**

```bash
git add app/crud/ tests/conftest.py tests/test_crud_item.py
git commit -m "feat: add Item CRUD layer with tests"
```

---

### Task 8: API ルーターと main.py 配線 — TDD

**Files:**
- Create: `app/api/__init__.py`
- Create: `app/api/routes_health.py`
- Create: `app/api/routes_item.py`
- Modify: `app/main.py`
- Test: `tests/test_api_items.py`
- Test: `tests/test_health.py`

**Interfaces:**
- Consumes: `app.crud.item`, `app.db.session.get_session`, `app.schemas.item.*`。
- Produces:
  - `routes_health.router`（`GET /health`）
  - `routes_item.router`（prefix `/items` の CRUD）
  - `app.main.app` に両 router を登録

- [ ] **Step 1: `tests/conftest.py` に HTTP クライアント fixture を追加**

`get_session` を上書きしてテスト用セッションを注入し、httpx の AsyncClient を提供する。

```python
# tests/conftest.py に追記
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db.session import get_session
from app.main import app


@pytest_asyncio.fixture
async def client(session):
    async def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

- [ ] **Step 2: 失敗するテストを書く** — `tests/test_api_items.py`

```python
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
```

- [ ] **Step 3: テスト失敗を確認**

Run: `docker compose run --rm app uv run pytest tests/test_api_items.py -v`
Expected: FAIL（404 等、ルーター未登録）

- [ ] **Step 4: `app/api/__init__.py` を作成（空）**

```python
```

- [ ] **Step 5: `app/api/routes_item.py` を実装**

```python
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
```

- [ ] **Step 6: `app/api/routes_health.py` を実装**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ok"}
```

- [ ] **Step 7: `app/main.py` を更新してルーターを登録**

```python
from fastapi import FastAPI

from app.api import routes_health, routes_item

app = FastAPI(title="uv_recruit sample API")

app.include_router(routes_health.router)
app.include_router(routes_item.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "ok"}
```

- [ ] **Step 8: items テスト成功を確認**

Run: `docker compose run --rm app uv run pytest tests/test_api_items.py -v`
Expected: PASS（9 件）

- [ ] **Step 9: health テストを書く** — `tests/test_health.py`

```python
async def test_health_ok(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

- [ ] **Step 10: health テスト成功を確認**

Run: `docker compose run --rm app uv run pytest tests/test_health.py -v`
Expected: PASS

- [ ] **Step 11: Commit**

```bash
git add app/api/ app/main.py tests/test_api_items.py tests/test_health.py tests/conftest.py
git commit -m "feat: add health and Item CRUD API routes with tests"
```

---

### Task 9: pre-commit・最終品質ゲート・README

**Files:**
- Create: `.pre-commit-config.yaml`
- Create: `README.md`（既存を上書き）

**Interfaces:**
- Consumes: 全タスクの成果物。
- Produces: lint/format/type-check/test がすべて通る状態と、起動手順ドキュメント。

- [ ] **Step 1: `.pre-commit-config.yaml` を作成**

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.20
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v2.1.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, sqlmodel]
        args: [app]
```

- [ ] **Step 2: Ruff フォーマットを適用**

Run: `docker compose run --rm app uv run ruff format .`
Expected: ファイルが整形される（必要に応じて）。

- [ ] **Step 3: Ruff lint を実行**

Run: `docker compose run --rm app uv run ruff check .`
Expected: `All checks passed!`

- [ ] **Step 4: mypy 型チェックを実行**

Run: `docker compose run --rm app uv run mypy app`
Expected: `Success: no issues found`
（エラーがあれば該当箇所を修正してから再実行）

- [ ] **Step 5: 全テストを実行**

Run: `docker compose run --rm app uv run pytest -v`
Expected: 全テスト PASS

- [ ] **Step 6: `README.md` を作成**

````markdown
# uv_recruit code samples — FastAPI + PostgreSQL (Docker)

Docker だけで起動・開発できる FastAPI サンプル API。

## 必要なもの

- Docker / Docker Compose のみ（ローカルに Python・uv は不要）

## 起動

```bash
cp .env.example .env   # 任意
docker compose up --build
```

- API: http://localhost:8000
- OpenAPI ドキュメント: http://localhost:8000/docs
- ヘルスチェック: http://localhost:8000/health

## エンドポイント

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/health` | 稼働 + DB 接続確認 |
| POST | `/items` | Item 作成 |
| GET | `/items` | Item 一覧 |
| GET | `/items/{id}` | Item 取得 |
| PATCH | `/items/{id}` | Item 更新 |
| DELETE | `/items/{id}` | Item 削除 |

## 開発コマンド（すべてコンテナ内）

```bash
# Lint / Format
docker compose run --rm app uv run ruff check .
docker compose run --rm app uv run ruff format .

# 型チェック
docker compose run --rm app uv run mypy app

# テスト
docker compose run --rm app uv run pytest

# マイグレーション
docker compose run --rm app uv run alembic revision --autogenerate -m "message"
docker compose run --rm app uv run alembic upgrade head
```
````

- [ ] **Step 7: Commit**

```bash
git add .pre-commit-config.yaml README.md app/ tests/
git commit -m "chore: add pre-commit config, README, and pass quality gates"
```

---

## Self-Review

**Spec coverage:**
- 全体アーキ（Docker/uv-in-container/bind mount）→ Task 2 ✓
- 採用バージョン → Task 1（pyproject）/ Task 2（Dockerfile）✓
- ディレクトリ構成・層分離 → Task 3〜8 ✓
- Item モデル・スキーマ → Task 5 ✓
- CRUD + /health API → Task 7, 8 ✓
- Alembic マイグレーション → Task 6 ✓
- 開発フロー（lint/format/type/test コマンド）→ Task 9 ✓
- 静的解析（Ruff/mypy/pre-commit）→ Task 1（設定）/ Task 9（実行・フック）✓
- テスト戦略（pytest-asyncio + httpx）→ Task 7, 8 ✓
- エラーハンドリング（404/503/422）→ Task 8 ✓

**Placeholder scan:** プレースホルダなし。全コードステップに実コードを記載。

**Type consistency:** crud 関数シグネチャ（Task 7 Produces）と api 層の呼び出し（Task 8）が一致。`get_session` の名称が Task 4 / 7 / 8 で一貫。`ItemRead.model_validate(..., from_attributes=True)` を全ルートで統一。
