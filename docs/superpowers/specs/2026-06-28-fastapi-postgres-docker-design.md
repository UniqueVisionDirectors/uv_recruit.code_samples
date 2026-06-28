# FastAPI + PostgreSQL + Docker サンプルアプリケーション 設計書

- 日付: 2026-06-28
- ステータス: 承認済み（実装計画フェーズへ）

## 1. 目的・スコープ

FastAPI を用いた API サーバーを作成し、Docker だけで起動・開発できる構成を整える。

- API サーバーのみ（フロントエンド不要）
- データベースは PostgreSQL
- サンプルとして `Item` エンティティの CRUD 一式を提供
- ライブラリ・言語は最新安定版を採用
- PEP8 準拠を静的解析で強制し、開発環境を整備
- **ローカルに Python / uv を入れず、Docker だけで起動・開発・テストできる**
  - `uv` の実行もコンテナ内で行う
  - 実ディレクトリをバインドマウントしてホット編集を反映

非スコープ: 認証・認可、フロントエンド、CI/CD パイプライン本体（設定ファイルの雛形提供のみ）。

## 2. 採用バージョン（2026-06-28 時点の最新安定版）

| 項目 | バージョン | 備考 |
|---|---|---|
| Python | 3.14 (3.14.6) | 最新安定版 |
| uv | 最新（公式イメージから取得） | パッケージ/プロジェクト管理 |
| FastAPI | 0.138.1 | requires Python>=3.10 |
| SQLModel | 0.0.39 | SQLAlchemy 2.0.x + Pydantic 2.11+ を同梱 |
| uvicorn | 0.49.0 | ASGI サーバー |
| psycopg (3) | 3.3.4 | 非同期 DB ドライバ。Python 3.14 対応済（asyncpg は 3.14 対応が遅れるため不採用） |
| Alembic | 1.18.5 | マイグレーション |
| pydantic-settings | 最新 | 環境変数読込 |
| pytest | 9.1.1 | テスト |
| pytest-asyncio | 1.1.0 | 非同期テスト |
| httpx | 最新 | テスト用 HTTP クライアント |
| Ruff | 0.15.20 | リンター＋フォーマッタ（PEP8 強制） |
| mypy | 2.1.0 | 静的型チェック（Python 3.14 対応・安定版） |
| pre-commit | 4.6.0 | コミット時フック |
| PostgreSQL | 18 | 公式イメージ |

> 補足: Astral 製の型チェッカー `ty` は最新 0.0.55 でまだベータ（API 非安定）のため見送り、安定版 mypy を採用。

## 3. 全体アーキテクチャ

`docker compose up` で `app`（FastAPI）と `db`（PostgreSQL 18）が起動する。

```
[ホスト: ソース編集] ⇄ bind mount ⇄ [app コンテナ: uv run uvicorn --reload]
                                            │ postgresql+psycopg://
                                            ▼
                                   [db コンテナ: PostgreSQL 18]
                                   (data: named volume)
```

- プロジェクトディレクトリをバインドマウントでコンテナ内 `/app` に接続。ホスト編集が即反映され、uvicorn `--reload` でホットリロード。
- `uv` はコンテナ内で実行（公式 uv イメージからバイナリを COPY）。依存は `pyproject.toml` / `uv.lock` で管理。
- `.venv` はホストと衝突しないよう名前付き volume にして bind mount から退避（`/app/.venv`）。
- DB データは名前付き volume で永続化。

## 4. ディレクトリ構成

```
uv_recruit.code_samples/
├── compose.yaml              # app + db のオーケストレーション
├── Dockerfile                # app イメージ（uv 入り, Python3.14 ベース）
├── .dockerignore
├── pyproject.toml            # 依存定義＋ツール設定（uv 管理）
├── uv.lock                   # ロックファイル
├── .env.example              # 環境変数サンプル
├── .pre-commit-config.yaml   # pre-commit フック（任意・ホスト利用時）
├── alembic.ini               # マイグレーション設定
├── migrations/               # Alembic マイグレーション
│   ├── env.py
│   └── versions/
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI アプリ生成・ルーター登録・lifespan
│   ├── core/
│   │   └── config.py         # 設定（pydantic-settings, 環境変数読込）
│   ├── db/
│   │   └── session.py        # 非同期エンジン・セッション・get_session 依存
│   ├── models/
│   │   └── item.py           # SQLModel テーブルモデル(Item)
│   ├── schemas/
│   │   └── item.py           # 入出力スキーマ(ItemCreate/ItemUpdate/ItemRead)
│   ├── crud/
│   │   └── item.py           # DB 操作ロジック（CRUD 関数）
│   └── api/
│       ├── routes_health.py  # /health（DB ping 含む）
│       └── routes_item.py    # /items CRUD エンドポイント
└── tests/
    ├── conftest.py           # テスト用 DB/クライアント fixture
    └── test_items.py         # CRUD の E2E テスト
```

### コンポーネントの責務（単一責任で分離）

- `core/config.py` — 環境変数を型付きで読込（`DATABASE_URL` 等）。他層はここ経由で設定取得。
- `db/session.py` — 非同期エンジン生成と `get_session()` 依存性。DB 接続の唯一の入口。
- `models/` — DB テーブル定義（SQLModel, `table=True`）。
- `schemas/` — API の入出力契約。テーブルモデルと API 契約を分離。
- `crud/` — DB 操作の純粋ロジック。ルーターから呼ばれ、テスト容易。
- `api/` — HTTP ルーティングのみ。crud へ委譲。

## 5. データモデル・API 仕様

### エンティティ `Item`

| フィールド | 型 | 備考 |
|---|---|---|
| id | int | 主キー（自動採番） |
| name | str | 必須 |
| description | str \| None | 任意 |
| created_at | datetime | 作成時刻（サーバー側設定） |

### エンドポイント

| メソッド | パス | 説明 | 主なステータス |
|---|---|---|---|
| GET | `/health` | アプリ稼働＋DB 接続(`SELECT 1`)確認 | 200 / 503 |
| POST | `/items` | 作成 | 201 |
| GET | `/items` | 一覧（limit/offset ページング） | 200 |
| GET | `/items/{id}` | 取得 | 200 / 404 |
| PATCH | `/items/{id}` | 部分更新 | 200 / 404 |
| DELETE | `/items/{id}` | 削除 | 204 / 404 |

### データフロー

`api 層`（HTTP・バリデーション）→ `crud 層`（DB 操作）→ `db/session`（非同期セッション）→ PostgreSQL。
OpenAPI ドキュメントは `/docs` で自動提供。

### エラーハンドリング

- 存在しない ID は 404（`HTTPException`）。
- バリデーションエラーは FastAPI 標準の 422。
- `/health` は DB 接続失敗時に 503 を返す。

## 6. 開発フロー（すべてコンテナ内で実行）

| 操作 | コマンド |
|---|---|
| 起動 | `docker compose up`（初回ビルド→`uv sync`→マイグレーション→uvicorn 起動） |
| Lint | `docker compose run --rm app uv run ruff check .` |
| Format | `docker compose run --rm app uv run ruff format .` |
| 型チェック | `docker compose run --rm app uv run mypy app` |
| テスト | `docker compose run --rm app uv run pytest` |
| マイグレーション作成 | `docker compose run --rm app uv run alembic revision --autogenerate -m "..."` |
| マイグレーション適用 | `docker compose run --rm app uv run alembic upgrade head` |

- Ruff / mypy / pytest の設定はすべて `pyproject.toml` に集約。
- Ruff は PEP8 系（E/W/F）＋ isort(I)＋pyupgrade(UP)＋bugbear(B) 等を有効化。
- `.pre-commit-config.yaml` を用意（ホストに pre-commit がある場合に利用可。なくてもコンテナ内コマンドで同等チェック可能）。

## 7. テスト戦略

- pytest + pytest-asyncio + httpx の AsyncClient（ASGITransport）で API を E2E テスト。
- テスト用 DB は compose 内の `db`（専用テスト DB or トランザクションロールバック）を利用。
- 各エンドポイントの正常系＋主要な異常系（404）を網羅。
- TDD で進める（テスト先行 → 実装）。

## 8. 起動・コンテナ設計の要点

- Dockerfile: Python 3.14 公式 slim ベースに、`ghcr.io/astral-sh/uv` からuv バイナリを COPY。
- compose: `app` は bind mount（`.:/app`）＋ `/app/.venv` を名前付き volume で退避。`db` の起動を `depends_on` + healthcheck で待機。
- エントリポイント: `uv sync` → `alembic upgrade head` → `uvicorn app.main:app --reload --host 0.0.0.0`。
- 環境変数 `DATABASE_URL` は compose から注入（例: `postgresql+psycopg://postgres:postgres@db:5432/app`）。

## 9. リスク・留意点

- Python 3.14 は新しいため、一部ライブラリのホイール未提供リスク → DB ドライバは 3.14 対応済の psycopg3 を採用済。ビルド時に検証する。
- バインドマウント環境で `.venv` をホストと共有すると壊れるため、必ず volume で退避する。
