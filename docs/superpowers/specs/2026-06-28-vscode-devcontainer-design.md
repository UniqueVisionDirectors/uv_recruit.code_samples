# VS Code Dev Containers 開発環境 設計書

- 日付: 2026-06-28
- ステータス: レビュー待ち
- 関連: [FastAPI + PostgreSQL + Docker サンプルアプリ](./2026-06-28-fastapi-postgres-docker-design.md)

## 1. 目的・スコープ

VS Code でこのプロジェクトを快適に開発できる設定を整える。特に**エディタ上で静的解析によるサジェスチョン**（補完・型チェック・lint・保存時自動修正）が効くことを目標とする。

- VS Code の Dev Containers で「コンテナ内」で開発し、コンテナ内 `/app/.venv` を参照する
- 推奨拡張機能を定義し、開いた時に導入を促す
- Ruff（PEP8/lint/format）・mypy（厳密な型）・Pylance（補完）をエディタに統合
- デバッグ（FastAPI ブレークポイント）とタスク（lint/format/型/test）を用意
- 将来の portless 導入（ポート番号衝突問題の解決）を見据えたポート整合を行う

非スコープ: portless 本体の導入・設定（別タスクで実施）、CI 連携。

## 2. 背景・設計上の制約

- `.venv` と依存パッケージは**コンテナ内の名前付き volume**にあり、ホストには存在しない。
  → ホストの VS Code から静的解析を効かせるには、エディタがコンテナ内環境を参照する必要がある。
  → **Dev Containers**（コンテナ内で VS Code を開く）が「Docker だけで完結」方針と最も整合する。
- 既存の `compose.yaml`（`app` / `db` サービス）をそのまま再利用する。`docker compose up`（コンテナ外からの通常起動）の挙動は変えない。
- 型チェックは既に `pyproject.toml` で mypy strict を採用済み。エディタでは mypy を主役にし、Pylance は補完中心（basic）にして二重警告を避ける。

## 3. アプローチ

VS Code Dev Containers で `app` サービスのコンテナに接続して開発する。

```
[VS Code (ホスト)] --Dev Containers--> [app コンテナ /app, /app/.venv]
                                              │ (同 compose ネットワーク)
                                              ▼
                                        [db コンテナ PostgreSQL 18]
```

- 接続先サービス: `app`、作業フォルダ: `/app`
- Dev Containers では `overrideCommand` により自動起動（uvicorn）を抑止し、ポート 8000 をデバッグ起動が使えるようにする。コンテナ外の `docker compose up` は引き続き uvicorn を自動起動する（Dev Containers の override は接続コンテナのみに適用されるため）。

## 4. 作成ファイル

| ファイル | 役割 |
|---|---|
| `.devcontainer/devcontainer.json` | 既存 compose を参照し、接続先=`app`／作業ディレクトリ=`/app`／拡張機能の自動インストール／ポート設定 |
| `.vscode/settings.json` | エディタ設定（インタプリタ・補完・保存時フォーマット/lint・型チェック・テスト） |
| `.vscode/extensions.json` | 推奨拡張機能リスト |
| `.vscode/launch.json` | FastAPI デバッグ起動 |
| `.vscode/tasks.json` | lint / format / 型チェック / test タスク |

設定は `.vscode/` フォルダ方式（Dev Containers と相性が良く、`.code-workspace` 単一ファイルより一般的）で実装する。

## 5. 採用する拡張機能

| 拡張機能 | ID | 役割 |
|---|---|---|
| Dev Containers | `ms-vscode-remote.remote-containers` | コンテナ内で開く（ホスト側に必要） |
| Python | `ms-python.python` | Python 基盤・デバッグ・テスト連携 |
| Pylance | `ms-python.vscode-pylance` | 補完・IntelliSense（型チェックは basic で補助） |
| Ruff | `charliermarsh.ruff` | lint＋フォーマット（PEP8 即時サジェスト・保存時自動修正） |
| Mypy Type Checker | `ms-python.mypy-type-checker` | 厳密な型エラーをエディタ表示（主役） |
| Docker | `ms-azuretools.vscode-docker` | Dockerfile/compose 編集支援 |
| Even Better TOML | `tamasfe.even-better-toml` | `pyproject.toml` の補完・検証 |

`devcontainer.json` の `customizations.vscode.extensions` でコンテナに自動インストールし、`.vscode/extensions.json` でホスト側にも推奨を提示する（Dev Containers 拡張の導入を促すため）。

## 6. エディタ挙動（静的解析サジェスチョン）

`.vscode/settings.json` の要点:

- インタプリタ: `python.defaultInterpreterPath = /app/.venv/bin/python`
- 保存時に Ruff が自動整形＋import整理＋自動修正
  - `[python].editor.defaultFormatter = charliermarsh.ruff`
  - `editor.formatOnSave = true`
  - `editor.codeActionsOnSave = { source.fixAll.ruff, source.organizeImports.ruff }`（`explicit`）
- Ruff: `ruff.importStrategy = fromEnvironment`（`.venv` の ruff と `pyproject.toml` 設定を使用）
- mypy: `mypy-type-checker.importStrategy = fromEnvironment`、`mypy-type-checker.args = ["--config-file=pyproject.toml"]`（strict・pydantic plugin を反映）
- Pylance: `python.analysis.typeCheckingMode = basic`、`python.analysis.autoImportCompletions = true`
- テスト: `python.testing.pytestEnabled = true`、`python.testing.pytestArgs = ["tests"]`

## 7. デバッグ / タスク

- `launch.json`: 「FastAPI (uvicorn)」構成。`type=debugpy`、`module=uvicorn`、`args=["app.main:app","--host","0.0.0.0","--port","8000","--reload"]`、`justMyCode=false`。
- `tasks.json`: 以下を `uv run` で実行
  - `lint: ruff check` → `uv run ruff check .`
  - `format: ruff` → `uv run ruff format .`
  - `typecheck: mypy` → `uv run mypy app`
  - `test: pytest` → `uv run pytest`（`group: test`）

## 8. portless（ポート番号問題）を見据えた整合

portless 本体の導入は別タスク（#11）。本設計では将来導入しやすいよう、ポートを明示・ラベル付けするに留める。

- `devcontainer.json` に `forwardPorts = [8000, 5432]`
- `portsAttributes` でラベル付け: `8000` → "app (FastAPI)"、`5432` → "db (PostgreSQL)"

これにより VS Code 上でポートが識別しやすくなり、将来 `portless alias app 8000` で `https://app.localhost` を割り当てる際の前提（8000 がホストに公開・識別済み）が整う。

## 9. テスト・検証方針

エディタ動作はヘッドレスで実行できないため、次で品質を担保する。

- 全 JSON（`devcontainer.json` 含む）の妥当性をコンテナ内 `python -m json.tool` で検証（コメントは付けず厳密 JSON とする）
- 参照パス（`/app/.venv/bin/python`）・拡張機能 ID の正しさを目視確認
- 既存のアプリ起動・テスト（`docker compose up` / `pytest`）が引き続き通ることを確認

## 10. リスク・留意点

- WSL2 環境のため、ホスト(Windows)側 VS Code から WSL の Docker に接続する構成。Dev Containers は WSL 上の Docker と連携可能だが、初回は拡張機能の導入と再オープンが必要。
- `overrideCommand` により Dev Containers 内ではアプリが自動起動しない。通常の `docker compose up`（コンテナ外）は影響を受けない点を README/docstring で明示する。
