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
| GET | `/items` | Item 一覧（`limit` / `offset`） |
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

## 注意（本番運用に向けて）

このリポジトリは「Docker だけで開発を完結させる」ことを目的とした開発用構成です。
本番では次の対応を推奨します。

- コンテナを非 root ユーザーで実行する
- `--reload` を無効化し、依存はイメージビルド時に固定インストールする（実行時 `uv sync` を避ける）
- DB ポートやアプリポートの公開範囲を絞る／シークレットを安全に管理する
