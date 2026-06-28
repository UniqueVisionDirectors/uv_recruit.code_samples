# VS Code Dev Containers 開発環境 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** VS Code Dev Containers でコンテナ内開発を可能にし、Ruff/mypy/Pylance によるエディタ上の静的解析サジェスチョン・デバッグ・タスクを整える。

**Architecture:** 既存の `compose.yaml` の `app` サービスに VS Code を接続して `/app` を開く。コンテナ内 `/app/.venv` を参照することで補完・型チェック・lint が実環境ベースで効く。設定は `.vscode/` フォルダと `.devcontainer/` に配置する。

**Tech Stack:** VS Code Dev Containers, Ruff 拡張, Mypy Type Checker 拡張, Pylance, Python 拡張, Docker 拡張, Even Better TOML。

## Global Constraints

- 接続先サービス `app`、作業フォルダ `/app`、インタプリタ `/app/.venv/bin/python`。
- 既存 `compose.yaml`（`app`/`db`）はそのまま再利用し、`docker compose up`（コンテナ外）の挙動は変えない。
- 全 JSON ファイルはコメントを付けず厳密 JSON とし、`python -m json.tool` で妥当性検証できること。
- 型チェックは mypy（strict, `pyproject.toml`）を主役、Pylance は `basic`（補完中心）。
- コミットメッセージ末尾に `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` を付与。

---

### Task 1: VS Code 推奨拡張機能とエディタ設定

**Files:**
- Create: `.vscode/extensions.json`
- Create: `.vscode/settings.json`

**Interfaces:**
- Produces: `.vscode/settings.json`（インタプリタ・保存時 Ruff・mypy・Pylance・pytest 設定）。後続の launch/tasks と同じ前提（`uv` / `/app/.venv`）を共有。

- [ ] **Step 1: `.vscode/extensions.json` を作成**

```json
{
  "recommendations": [
    "ms-vscode-remote.remote-containers",
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "ms-python.mypy-type-checker",
    "ms-azuretools.vscode-docker",
    "tamasfe.even-better-toml"
  ]
}
```

- [ ] **Step 2: 妥当性を検証**

Run: `docker compose run --rm app python -m json.tool .vscode/extensions.json > /dev/null && echo OK`
Expected: `OK`
（`db` 起動や `uv sync` の待ちが入る場合があるが、最終行に `OK` が出れば成功）

- [ ] **Step 3: `.vscode/settings.json` を作成**

```json
{
  "python.defaultInterpreterPath": "/app/.venv/bin/python",
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.autoImportCompletions": true,
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": ["tests"],
  "ruff.importStrategy": "fromEnvironment",
  "mypy-type-checker.importStrategy": "fromEnvironment",
  "mypy-type-checker.args": ["--config-file=pyproject.toml"],
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },
  "[toml]": {
    "editor.defaultFormatter": "tamasfe.even-better-toml"
  }
}
```

- [ ] **Step 4: 妥当性を検証**

Run: `docker compose run --rm app python -m json.tool .vscode/settings.json > /dev/null && echo OK`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add .vscode/extensions.json .vscode/settings.json
git commit -m "feat: add VS Code recommended extensions and editor settings"
```

---

### Task 2: デバッグ構成とタスク

**Files:**
- Create: `.vscode/launch.json`
- Create: `.vscode/tasks.json`

**Interfaces:**
- Consumes: Task 1 の前提（`/app/.venv`、`uv`）。
- Produces: 「FastAPI (uvicorn)」デバッグ構成と lint/format/typecheck/test タスク。

- [ ] **Step 1: `.vscode/launch.json` を作成**

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI (uvicorn)",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload"
      ],
      "jinja": false,
      "justMyCode": false,
      "console": "integratedTerminal"
    }
  ]
}
```

- [ ] **Step 2: 妥当性を検証**

Run: `docker compose run --rm app python -m json.tool .vscode/launch.json > /dev/null && echo OK`
Expected: `OK`

- [ ] **Step 3: `.vscode/tasks.json` を作成**

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "lint: ruff check",
      "type": "shell",
      "command": "uv run ruff check .",
      "problemMatcher": []
    },
    {
      "label": "format: ruff",
      "type": "shell",
      "command": "uv run ruff format .",
      "problemMatcher": []
    },
    {
      "label": "typecheck: mypy",
      "type": "shell",
      "command": "uv run mypy app",
      "problemMatcher": []
    },
    {
      "label": "test: pytest",
      "type": "shell",
      "command": "uv run pytest",
      "group": "test",
      "problemMatcher": []
    }
  ]
}
```

- [ ] **Step 4: 妥当性を検証**

Run: `docker compose run --rm app python -m json.tool .vscode/tasks.json > /dev/null && echo OK`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add .vscode/launch.json .vscode/tasks.json
git commit -m "feat: add VS Code debug config and dev tasks"
```

---

### Task 3: Dev Container 定義

**Files:**
- Create: `.devcontainer/devcontainer.json`

**Interfaces:**
- Consumes: 既存 `compose.yaml`（`app` サービス）、Task 1 の拡張機能 ID。
- Produces: コンテナ内開発の入口。拡張機能の自動インストールとポート設定。

- [ ] **Step 1: `.devcontainer/devcontainer.json` を作成**

`overrideCommand: true` により Dev Containers 内では uvicorn を自動起動せず、デバッグ起動でポート 8000 を使えるようにする。`forwardPorts` と `portsAttributes` で app/db を識別（将来の portless 連携の前提）。

```json
{
  "name": "uv_recruit FastAPI",
  "dockerComposeFile": ["../compose.yaml"],
  "service": "app",
  "workspaceFolder": "/app",
  "overrideCommand": true,
  "forwardPorts": [8000, 5432],
  "portsAttributes": {
    "8000": { "label": "app (FastAPI)" },
    "5432": { "label": "db (PostgreSQL)" }
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "charliermarsh.ruff",
        "ms-python.mypy-type-checker",
        "ms-azuretools.vscode-docker",
        "tamasfe.even-better-toml"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/app/.venv/bin/python"
      }
    }
  }
}
```

- [ ] **Step 2: 妥当性を検証**

Run: `docker compose run --rm app python -m json.tool .devcontainer/devcontainer.json > /dev/null && echo OK`
Expected: `OK`

- [ ] **Step 3: `compose.yaml` の `app` サービスが解決可能か確認**

Run: `docker compose config --services`
Expected: `app` と `db` が一覧に出る（devcontainer の `service: app` が有効であることの確認）。

- [ ] **Step 4: Commit**

```bash
git add .devcontainer/devcontainer.json
git commit -m "feat: add dev container definition for app service"
```

---

### Task 4: ドキュメント更新

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: Task 1〜3 の成果物。
- Produces: VS Code での開き方の説明。

- [ ] **Step 1: `README.md` に「VS Code 開発」節を追記**

`README.md` の末尾（「注意（本番運用に向けて）」節の直前）に以下を挿入する。

```markdown
## VS Code 開発（Dev Containers）

1. VS Code に「Dev Containers」拡張（`ms-vscode-remote.remote-containers`）を入れる。
2. このフォルダを開き、コマンドパレットから **Dev Containers: Reopen in Container** を実行。
3. コンテナ内 `/app/.venv` を参照して補完・型チェック（mypy）・lint（Ruff）が効く。保存時に自動整形される。
4. デバッグ実行: 実行とデバッグから **FastAPI (uvicorn)** を起動（ブレークポイント可）。
5. タスク: コマンドパレットの **Tasks: Run Task** から lint / format / typecheck / test を実行。

> Dev Containers 内ではアプリは自動起動しない（デバッグ起動用にポート 8000 を空けるため）。
> コンテナ外からの `docker compose up` はこれまで通り uvicorn を自動起動する。
```

- [ ] **Step 2: マークダウンが壊れていないか目視確認**

Run: `grep -n "VS Code 開発（Dev Containers）" README.md`
Expected: 追記した見出し行が表示される。

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document VS Code dev container workflow"
```

---

## Self-Review

**Spec coverage:**
- Dev Containers（app接続・/app・overrideCommand）→ Task 3 ✓
- 作成ファイル5種（extensions/settings/launch/tasks/devcontainer）→ Task 1〜3 ✓
- 推奨拡張機能7種 → Task 1（extensions.json）/ Task 3（customizations）✓
- エディタ挙動（保存時Ruff・mypy主役・Pylance basic・pytest）→ Task 1 ✓
- デバッグ/タスク → Task 2 ✓
- portless 見据えた forwardPorts/portsAttributes → Task 3 ✓
- 検証方針（JSON妥当性）→ 各 Task の検証ステップ ✓
- README 明記（overrideCommand の挙動）→ Task 4 ✓

**Placeholder scan:** プレースホルダなし。全 JSON を実内容で記載。

**Type consistency:** 拡張機能 ID は extensions.json（Task 1）と devcontainer customizations（Task 3）で一致（Dev Containers 拡張はホスト専用のため customizations 側には含めない、という差異は意図的）。インタプリタパス `/app/.venv/bin/python` を settings.json と devcontainer で統一。
