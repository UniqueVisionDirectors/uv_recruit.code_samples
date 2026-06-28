# 作業引き継ぎ（tasks.md）

> このファイルは、セッションをまたいで作業を再開するための引き継ぎメモです。
> 次回セッションでは、まずこのファイルを読んでから作業を再開してください。
> 最終更新: 2026-06-28

---

## 0. このプロジェクトの概要

- リポジトリ: `uv_recruit.code_samples`（GitHub: `UniqueVisionDirectors/uv_recruit.code_samples`、SSH）
- 内容: **Docker だけで起動・開発できる FastAPI + PostgreSQL のサンプル API**
- 技術: Python 3.14 / uv / FastAPI / SQLModel / SQLAlchemy(async) / psycopg3 / Alembic / PostgreSQL 18 / Ruff / mypy / pytest
- 設計・計画ドキュメントの場所:
  - `docs/superpowers/specs/2026-06-28-fastapi-postgres-docker-design.md`（API 設計）
  - `docs/superpowers/plans/2026-06-28-fastapi-postgres-docker.md`（API 実装計画）
  - `docs/superpowers/specs/2026-06-28-vscode-devcontainer-design.md`（VS Code 設計）
  - `docs/superpowers/plans/2026-06-28-vscode-devcontainer.md`（VS Code 実装計画）

---

## 1. 完了済み（main ブランチに集約済み）

- ✅ FastAPI アプリ本体（`app/` 配下：core / db / models / schemas / crud / api）
- ✅ `Item` の CRUD 一式 + `/health`（DB ping）エンドポイント
- ✅ Docker 構成（`Dockerfile` / `compose.yaml` / `docker-entrypoint.sh`）
  - uv をコンテナ内で実行、実ディレクトリをバインドマウント、`.venv` は名前付き volume へ退避
  - PostgreSQL 18 はデータディレクトリを `/var/lib/postgresql` にマウント（18 の仕様変更対応済み）
- ✅ Alembic 非同期マイグレーション（`items` テーブル作成済み）
- ✅ pytest によるテスト 15 件（全 PASS）
- ✅ 静的解析：Ruff（PEP8 強制）+ mypy(strict) + pre-commit。全ゲート通過
- ✅ VS Code Dev Containers 環境（`.devcontainer/devcontainer.json`、`.vscode/` の settings/extensions/launch/tasks）
- ✅ `CLAUDE.md`（プロジェクト方針：KISS/YAGNI/DRY/対称性）
- ✅ `README.md`（起動方法・開発コマンド・VS Code 手順・本番向け注意）

---

## 2. 残タスク（優先順）

### タスクA: リモートへの push【最優先・ユーザー作業 / 作業再開の前提】
- **作業の再開は push 完了後に行う。**
- 状態: **push 準備完了済み**。`main` は `origin/main` より 19 コミット先行、fast-forward 可能、作業ツリーはクリーン。
- ユーザーが実行するコマンド（SSH 鍵の都合でユーザーのみ実行可）:
  ```
  git push origin main
  ```
- 再開時の確認: `git status -sb` の先頭行が `## main...origin/main`（ahead 表記なし）なら push 済み。
  - もし `rejected (non-fast-forward)` だった場合は `git fetch` してから取り込み方を判断する。

### タスクB: ポート番号衝突問題の解決（portless 導入）【次のメイン作業】
- 目的（**一般要求**）: ローカル環境のポート番号衝突を恒常的に解決したい。
- 現状の具体的動機: 別プロジェクト `/home/kyohei/wg_quality.project-manager` を**同じホスト（WSL2）で並行開発**しており、ポートが衝突する。
  - 並行プロジェクトのホスト使用ポート例: `5174`(Vite) / `5432`,`5433`,`5435`(Postgres系) / `3306` / `9999`
  - 本プロジェクトのホスト公開ポート: `8000`(app) のみ（`db` は内部ネットワークのみ・未公開）。将来 `db` を公開すると `5432` が直接衝突する。
- 採用検討ツール: **vercel-labs/portless**（`localhost:8000` → `https://app.localhost` の名前付き URL リバースプロキシ）
  - ドキュメント:
    - https://github.com/vercel-labs/portless
    - https://zenn.dev/ait/articles/portless-local-dev-named-url
- **調査済みの要点（再調査不要）**:
  - 仕組み: ホストの 443/80 でプロキシ常駐。`.localhost` はブラウザが 127.0.0.1 に自動解決。初回にローカル CA を生成し OS 信頼ストアへ追加（自動 HTTPS）。
  - **Docker/compose との併用は `portless alias <name> <port>` 方式**（静的ルート登録）。例: `portless alias app 8000` → `https://app.localhost`。compose 側は `ports: 8000` 公開のままでよい。
  - 前提: **Node.js 24+** がホストに必要（`npm install -g portless`）。443 バインドと CA 信頼に管理者権限が必要。
  - **要検証（WSL2 特有）**: `.localhost` 解決・CA 信頼・443 バインドが WSL 側か Windows 側か。ブラウザが Windows 側の場合、`portless hosts sync`（/etc/hosts 追加）や mDNS 等の扱いを確認する必要がある。
- 進め方: **新規ブランチを切ってから**、ブレインストーミング（superpowers:brainstorming）→ 設計書 → 実装計画（writing-plans）→ 実装、の順で進める。
  - 最初の確認事項（ブレストの最初の問い）: ホストに Node.js 24+ があるか（`node -v`）、ブラウザは Windows 側か WSL 側か。

### タスクC: マージ済みブランチの整理【完了】
- ✅ `feat/fastapi-postgres-docker` は `main` にマージ後、削除済み。
- 作業は **main ブランチで再開する**（portless 着手時に新規ブランチを切るかは再開時に判断）。

---

## 3. 開発環境メモ（コマンドはすべてコンテナ内実行）

```bash
# 起動（アプリ http://localhost:8000 , Docs http://localhost:8000/docs）
docker compose up --build

# テスト / lint / format / 型チェック
docker compose run --rm app uv run pytest
docker compose run --rm app uv run ruff check .
docker compose run --rm app uv run ruff format .
docker compose run --rm app uv run mypy app

# マイグレーション
docker compose run --rm app uv run alembic revision --autogenerate -m "message"
docker compose run --rm app uv run alembic upgrade head

# 停止（ポート解放）
docker compose down
```

- 注意: `docker compose run` は entrypoint で `uv sync` + `alembic upgrade` が走る。JSON 検証など軽い用途では `--no-deps --entrypoint python` で上書きすると速い。

---

## 4. 再開方法（次セッションでの最初の一手）

1. このファイル（`tasks.md`）と `CLAUDE.md` を読む。
2. `git status -sb` で push 済みか確認（タスクA）。**push 完了が再開の前提。**
3. **main ブランチで再開**する。メイン作業はタスクB（portless 導入）。superpowers:brainstorming で設計を始める。
4. 並行開発・ポート衝突の背景はメモリにも記録済み（`parallel-dev-port-collision`）。
