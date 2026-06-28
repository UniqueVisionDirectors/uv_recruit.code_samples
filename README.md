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
| POST | `/users` | ユーザー作成（ID を自動発行、201 / 衝突時 409） |
| GET | `/users/{id}` | ユーザー取得（200 / 404） |

## 教材：ユーザーID発行API

設計書: `docs/superpowers/specs/2026-06-28-user-id-issuance-teaching-design.md`

### ステージ1：ID発行ロジックを書く
- 出題用 API（`ID_STRATEGY=problem`）の `app/idgen/problem.py` の `ProblemIssuer.issue` を実装する。
- 要件: base62(0-9A-Za-z) 10文字 / 発行順ソート可 / 連番回避 / 最大100億件以上。
- 確認: `docker compose run --rm app uv run pytest tests/test_idgen_problem.py`

### ステージ2：並列化しても衝突させない
- 複数コンテナ（LB配下）で発行しても ID が重複しないようにする。
- 解答例: `app/idgen/generator.py`（プロセス毎に distinct な `WORKER_ID`）。
- 衝突は負荷・マシン依存で確率的に起きる（決定的な証明は `tests/test_idgen_collision.py`）。
  実機で観測 → 修正を確認:
  ```bash
  # 素朴解（衝突する）
  ID_STRATEGY=stage1 docker compose -f compose.yaml -f compose.demo.yaml up -d --build db app1 app2 app3 lb
  docker compose -f compose.yaml -f compose.demo.yaml run --rm -e TARGET_URL=http://lb:8080 app uv run python scripts/collision_demo.py
  # 修正後（衝突しない）
  ID_STRATEGY=stage2 docker compose -f compose.yaml -f compose.demo.yaml up -d --build db app1 app2 app3 lb
  docker compose -f compose.yaml -f compose.demo.yaml run --rm -e TARGET_URL=http://lb:8080 app uv run python scripts/collision_demo.py
  # 後片付け
  docker compose -f compose.yaml -f compose.demo.yaml down -v
  ```

### 解答例 API
`docker compose up solution`（http://localhost:8001/docs）で stage2 実装を直接試せる。

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

## 技術スタック

Python 3.14 / uv / FastAPI / SQLModel / SQLAlchemy(async) / psycopg3 /
Alembic / uvicorn / pytest / Ruff / mypy / PostgreSQL 18

## 構成

```txt
app/
  core/    設定（環境変数）
  db/      非同期エンジン・セッション
  models/  SQLModel テーブル定義
  schemas/ リクエスト/レスポンススキーマ
  crud/    DB 操作ロジック
  api/     HTTP ルーター
migrations/ Alembic マイグレーション
tests/      pytest テスト
```

## VS Code 開発（Dev Containers）

1. VS Code に「Dev Containers」拡張（`ms-vscode-remote.remote-containers`）を入れる。
2. このフォルダを開き、コマンドパレットから **Dev Containers: Reopen in Container** を実行。
3. コンテナ内 `/app/.venv` を参照して補完・型チェック（mypy）・lint（Ruff）が効く。保存時に自動整形される。
4. デバッグ実行: 実行とデバッグから **FastAPI (uvicorn)** を起動（ブレークポイント可）。
5. タスク: コマンドパレットの **Tasks: Run Task** から lint / format / typecheck / test を実行。

> Dev Containers 内ではアプリは自動起動しない（デバッグ起動用にポート 8000 を空けるため）。
> コンテナ外からの `docker compose up` はこれまで通り uvicorn を自動起動する。

## 注意（本番運用に向けて）

このリポジトリは「Docker だけで開発を完結させる」ことを目的とした開発用構成です。
本番では次の対応を推奨します。

- コンテナを非 root ユーザーで実行する
- `--reload` を無効化し、依存はイメージビルド時に固定インストールする（実行時 `uv sync` を避ける）
- DB ポートやアプリポートの公開範囲を絞る／シークレットを安全に管理する
