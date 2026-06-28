# uv_recruit code samples — ユーザーID発行API 教材

ユーザーID発行API（FastAPI + PostgreSQL）の実装・衝突可視化・負荷ランナー・7章チュートリアルをまとめた教材リポジトリ。

## 必要なもの

- Docker / Docker Compose のみ（ローカルに Python・Rust・Node は不要）

## 起動

```bash
cp .env.example .env   # 任意
docker compose up --build
```

| サービス | URL | 説明 |
|---|---|---|
| API (app) | http://localhost:8000 | ユーザーID発行API |
| Swagger | http://localhost:8000/docs | OpenAPI ドキュメント |
| web (可視化) | http://localhost:5173 | 単一発行UI + 負荷ジョブ操作 |
| runner (負荷ランナー) | http://localhost:9000/healthz | Rust 非同期負荷ランナー |
| docs (チュートリアル) | http://localhost:5174 | 7章チュートリアルサイト |
| solution (解答例) | http://localhost:8001/docs | stage2 実装を直接確認 |

## チュートリアル

**学習パスの全詳細は http://localhost:5174 の7章チュートリアルを参照。**

1. イントロ — 教材の概要と目的
2. セットアップ — Docker 起動・動作確認
3. API仕様 — エンドポイント解説
4. Stage 1 — ID発行ロジックの実装
5. 衝突の観察 — 負荷ランナー + WebUIで衝突を体感
6. Stage 2 — 並列衝突を防ぐ修正
7. 付録 — 設計背景・参考資料

> `scripts/collision_demo.py` + `compose.demo.yaml` による旧来のCLI確認も引き続き使用可能。

## エンドポイント（app）

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/health` | 稼働 + DB 接続確認 |
| POST | `/users` | ユーザー作成（201 / 衝突時 409） |
| GET | `/users/{id}` | ユーザー取得（200 / 404） |
| GET | `/users` | ユーザー一覧 |

## 開発コマンド（すべてコンテナ内）

```bash
# --- app (Python) ---
docker compose run --rm app uv run ruff check .
docker compose run --rm app uv run ruff format --check .
docker compose run --rm app uv run mypy app
docker compose run --rm app uv run pytest -q

# --- runner (Rust) --- ※テスト実行前に db を起動すること
docker compose up -d db
docker compose run --rm -e DATABASE_URL=postgresql://postgres:postgres@db:5432/app runner cargo fmt --check
docker compose run --rm -e DATABASE_URL=postgresql://postgres:postgres@db:5432/app runner cargo clippy -- -D warnings
docker compose run --rm -e DATABASE_URL=postgresql://postgres:postgres@db:5432/app runner cargo test

# --- web (TypeScript/Vue) ---
docker compose run --rm web npm run typecheck
docker compose run --rm web npm run lint
docker compose run --rm web npm run test

# マイグレーション（app）
docker compose run --rm app uv run alembic revision --autogenerate -m "message"
docker compose run --rm app uv run alembic upgrade head
```

## 技術スタック

- **app**: Python 3.14 / uv / FastAPI / SQLModel / SQLAlchemy(async) / psycopg3 / Alembic / uvicorn / pytest / Ruff / mypy
- **runner**: Rust / Axum / SQLx / tokio
- **web**: TypeScript / Vue 3 / Vite / Vitest / ESLint
- **infra**: PostgreSQL 18 / Docker Compose

## 構成

```txt
app/
  core/    設定（環境変数）
  db/      非同期エンジン・セッション
  models/  SQLModel テーブル定義
  schemas/ リクエスト/レスポンススキーマ
  crud/    DB 操作ロジック
  api/     HTTP ルーター
  idgen/   ID発行ロジック（problem.py / generator.py）
runner/    Rust 負荷ランナー（Axum）
web/       Vue 3 + Vite 可視化フロント
docs/
  tutorial/  VitePress 7章チュートリアルサイト
migrations/  Alembic マイグレーション
tests/       pytest テスト
scripts/     補助スクリプト（collision_demo.py など）
```

## VS Code 開発（Dev Containers）

1. VS Code に「Dev Containers」拡張（`ms-vscode-remote.remote-containers`）を入れる。
2. このフォルダを開き、コマンドパレットから **Dev Containers: Reopen in Container** を実行。
3. コンテナ内 `/app/.venv` を参照して補完・型チェック（mypy）・lint（Ruff）が効く。保存時に自動整形される。
4. デバッグ実行: 実行とデバッグから **FastAPI (uvicorn)** を起動（ブレークポイント可）。
5. タスク: コマンドパレットの **Tasks: Run Task** から lint / format / typecheck / test を実行。

> Dev Containers 内ではアプリは自動起動しない（デバッグ起動用にポート 8000 を空けるため）。
> コンテナ外からの `docker compose up` はこれまで通り uvicorn を自動起動する。

## コンテナとファイル所有権

`docker compose up` / `docker compose run` はデフォルトで root 実行のため、bind マウントに書き込むとホスト側ファイルが root 所有になることがあります。

**恒久対策（compose.yaml 適用済み）:**

- `docs` サービス: `user: "1000:1000"` でホスト UID として実行 → `.vitepress/cache` / `dist` が 1000 所有で作られる。
- `app` / `solution` サービス: `PYTHONDONTWRITEBYTECODE=1` / `MYPY_CACHE_DIR` / `RUFF_CACHE_DIR` / `PYTEST_ADDOPTS` でキャッシュを `/tmp`（コンテナ内）に逃がし、bind マウントへの書き込みを抑制。
- `runner` / `web`: named volume (`cargo_target`, `node_modules`) がホスト bind-mount を保護しているため root 実行のまま問題なし。

**一時的な `docker run` / `docker compose run` を使う場合:**

bind マウントに書き込む可能性があるときは `--user $(id -u):$(id -g)` を付けてください。

```bash
docker compose run --rm --user $(id -u):$(id -g) app uv run pytest -q
```

**root 所有ファイルが生じた場合:**

```bash
scripts/fix-ownership.sh
```

## 注意（本番運用に向けて）

このリポジトリは「Docker だけで開発を完結させる」ことを目的とした開発用構成です。
本番では次の対応を推奨します。

- コンテナを非 root ユーザーで実行する
- `--reload` を無効化し、依存はイメージビルド時に固定インストールする（実行時 `uv sync` を避ける）
- DB ポートやアプリポートの公開範囲を絞る／シークレットを安全に管理する
