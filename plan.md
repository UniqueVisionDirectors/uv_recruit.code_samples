# 教材UX強化フェーズ 実装計画（フロント / runner / OpenAPI / チュートリアル）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成済みのユーザーID発行API（バックエンド）に、学習体験（UX）を付け足す ── ① Swagger UI を主役にした「触れる」API、② Vue 可視化フロント、③ Rust/Axum 負荷ランナー（ジョブ実行で 409 を測る）、④ VitePress チュートリアル ── を実装し、教材パッケージを完成させる。

**Architecture:** 関心を言語・ディレクトリ・コンテナで分離する。`app`(Python/FastAPI) は ID発行ドメインに純化（一覧と OpenAPI 強化のみ追加）。`runner`(Rust/Axum) は DB に `jobs` を持つ非同期負荷ランナーで、tokio マルチスレッド＋mpsc キューで負荷タスクと記録タスクを分け、**409 はジョブ単位の集約のみ DB に書く**（逐次書き込みしない＝ボトルネック回避）。`web`(Vue/Vite) はブラウザUIで、単発発行（並列1）と runner ジョブ（並列100/1000）を起動し可視化。`docs`(VitePress) が自習＋ライブ投影兼用の唯一の正典。

**Tech Stack:** Python 3.14 / FastAPI / SQLModel（既存）｜ Rust / Axum / tokio / sqlx / reqwest（新規 `runner/`）｜ Vite / Vue 3 / TypeScript（新規 `web/`）｜ VitePress + Mermaid（新規 `docs/tutorial/`）｜ Docker Compose / nginx(既存LB) / PostgreSQL 18。

---

## 現在地（最終更新: 2026-06-28）

**完了: Task 1〜10（12 コミット、Task 10 はローカル commit 4700895 で未 push）。次に着手: Task 11。**

- ✅ **グループA（app）完了**: Task 1（`GET /users`）、Task 2（OpenAPI 強化: 409/examples/メタ）。
- ✅ **グループB（runner, Rust/Axum）完了**: Task 3（雛形+healthz）、Task 4（`jobs` 永続化 sqlx）、Task 5（負荷エンジン tokio+mpsc）、Task 6（ジョブAPI `POST/GET /runs`）。
- ✅ **グループC（web, Vue）完了**: Task 7（雛形+/api proxy）、Task 8（ID 検証純関数）、Task 9（単発発行UI）、Task 10（ジョブ起動UI: JobLauncher/JobList/JobDetail+ポーリング）。
- ⬜ **未着手**: Task 11（compose 統合 e2e 衝突体験）、Task 12（VitePress 雛形）、Task 13（チュートリアル7章）、Task 14（README+最終ゲート）、**Task 15（全依存ライブラリの安全な最新化・Rust Edition 含む）**、**Task 16（コンテナ由来のファイル所有権の恒久対策＋最終確認）**。
- ⚠️ **既知の対処済み事項**: Task 7 の Vite scaffold（`docker run ... node` を root 実行）により `web/` 配下が一時 root 所有になっていたのを 2026-06-28 に host UID(1000) へ chown 済み。再発防止は Task 16 で恒久化する。

**実装メモ（再開時に重要）:**
- runner クレートは **lib+bin 構成**（`runner/src/lib.rs` が `pub mod api/engine/store`、`main.rs` と `tests/api.rs` が `runner::` で参照）。`AppState { store, client }`。sqlx は**ランタイムクエリ**（`query`/`query_as`、`!` マクロ不使用）でビルド時 DB 不要。
- web の ESLint は **flat config**（`eslint.config.js`、`@vue/eslint-config-typescript` v14 の `withVueTs`）。`.eslintrc.cjs` は非対応。`test` は `vitest run --passWithNoTests`。proxy は `/api/app`→app:8000、`/api/runner`→runner:9000。
- web の api.ts: `createUser`/`listUsers`（`UserRead {id,name,created_at}`）。非2xx は throw。Task 10 で `startRun`/`listRuns`/`getRun` と `RunJob` 型を追加。
- **デフォルト `app` は `ID_STRATEGY=problem`** で `issue()` が `NotImplementedError` を投げる（教材の穴埋め）。動作確認は `solution`(stage2) か demo スタックを使う。
- ホストの **5173 ポートが別コンテナ（promana_frontend）と衝突する可能性**あり（Task 11 e2e で注意）。
- Rust crate は固定済み（`runner/Cargo.lock`）: axum 0.8.9 / sqlx 0.8.6 / tokio 1.52 / reqwest 0.12.28。web: vite 8.1 / vue 3.5.38 / vitest 4.1.9 / eslint 10.6。
- 各タスクのレビューは task-scoped で完了。Minor 指摘は `.superpowers/sdd/progress.md`（ローカル scratch）に蓄積。**全タスク完了後に whole-branch review を実施すること。**

## 作業の再開方法（Resume）

> 新しいセッションで「**plan.md を確認し、作業を再開してください**」と指示されたら、この手順で進める。

1. **前提を読む**: `CLAUDE.md`（KISS / YAGNI / DRY＋直交性 / 対称性）と設計書 `docs/superpowers/specs/2026-06-28-teaching-ux-frontend-tutorial-design.md`。本ファイルが最新かつ唯一の実装計画。前フェーズ（ID発行API本体）は**完了済み**で、本計画には載せない。
2. **状態確認**: `git status -sb`。`## main...origin/main`（ahead 表記なし）なら push 済み。
3. **進捗の判定**: 下記 Task 群の `- [ ]`/`- [x]` を見て、**最初の未完了ステップ**から再開する。未着手なら **Task 1 から**。
4. **実行スキル**: `superpowers:subagent-driven-development`（推奨）または `superpowers:executing-plans` を使い **Task 単位**で進める。
5. **TDD を厳守**: 各 Task は「テスト先行 → 失敗確認 → 最小実装 → 通過確認 → コミット」。
6. **コマンドは全てコンテナ内**: Python は `docker compose run --rm app uv run <cmd>`、Rust は `docker compose run --rm runner cargo <cmd>`、Node は `docker compose run --rm web npm run <cmd>`（各サービス確立後）。
7. 各 Task 完了ごとに**コミット**し、対応するチェックボックスを `- [x]` に更新する。
8. **バージョン依存の確認**: Rust crate（axum/sqlx/tokio/reqwest）・Vite/Vue・VitePress の最新APIは、実装時に **context7 MCP** で確認してから書く（本計画のコードは構造を示すもの。API 細部は最新版に合わせる）。

## Global Constraints

- 既存の Python ゲートを常に緑に保つ: `ruff check .` / `ruff format --check .` / `mypy app` / `pytest`（Ruff line-length=88、mypy strict）。既存 23 テストを壊さない。
- 新コンポーネントのゲートも緑に保つ:
  - Rust: `cargo fmt --check` / `cargo clippy -- -D warnings` / `cargo test`。
  - Front: `npm run typecheck`(vue-tsc) / `npm run lint`(ESLint) / `npm run test`(Vitest)。
- すべてのコマンドは**コンテナ内**で実行する。
- **app は衝突を記録しない**（純度維持）。409 件数の集計は runner の `jobs` テーブルが担う。
- **runner のエンドポイント（`/runs` 等）は app の OpenAPI に含めない**。runner は別サービス・別ポート・別言語（Rust/Axum）で、FastAPI の `/openapi.json`・`/docs` は app のルートのみを対象とする（構成上自然に分離。Swagger UI の「Try it out」が指すのは app の API だけ）。runner は最低限 ① 負荷起動 `POST /runs`、② ジョブ一覧 `GET /runs`、③ ジョブ詳細 `GET /runs/{job_id}` を持つ（＋`GET /healthz`）。
- **runner は 409 を逐次 DB 書き込みしない**。負荷タスク→mpsc→集約タスクの分離で、DB へはジョブ単位の集約（開始 INSERT・完了 UPDATE・任意の定期スナップショット）だけを書く。
- worker-id 機構は現行の**明示 `WORKER_ID`＋3サービス**を維持（`--scale`/hostname へは寄せない）。
- ID 不変条件（既存）: base62(`0-9A-Za-z`) 10文字 / 発行順に文字列ソート可 / 連番回避。
- CLAUDE.md 4原則（KISS / YAGNI / DRY＋直交性 / 対称性）を遵守。

---

## ファイル構成（本フェーズで触る範囲）

**app（変更）**
- `app/api/routes_user.py` — `GET /users` 追加、`POST /users` に `responses`/`summary`/`tags`。
- `app/schemas/user.py` — `UserCreate`/`UserRead` に `examples`。
- `app/main.py` — FastAPI `title`/`description`/`version`。
- `tests/test_api_users.py` — 一覧・OpenAPI 検証を追加。

**runner（新規 `runner/`）**
- `runner/Cargo.toml` / `runner/Dockerfile` / `runner/.dockerignore`
- `runner/src/main.rs` — 起動・ルーティング・状態。
- `runner/src/api.rs` — `POST /runs` / `GET /runs` / `GET /runs/{job_id}` / `GET /healthz`。
- `runner/src/engine.rs` — 負荷エンジン（tokio＋mpsc＋集約、N成功まで＋安全上限）。
- `runner/src/store.rs` — sqlx による `jobs` 永続化。
- `runner/migrations/0001_create_jobs.sql` — `jobs` テーブル。
- `runner/tests/*.rs` — 集約ロジック・API 結合テスト。

**web（新規 `web/`）**
- `web/Dockerfile` / `web/package.json` / `web/vite.config.ts` / `web/tsconfig.json` / `web/.eslintrc.*`
- `web/src/lib/validate.ts` — ID 検証純関数。
- `web/src/lib/api.ts` — `/api` クライアント（app / runner）。
- `web/src/components/*` / `web/src/App.vue` — 単発発行・一覧・妥当性・ジョブ一覧/詳細。
- `web/src/lib/validate.test.ts` — 検証純関数の Vitest。

**docs（新規 `docs/tutorial/`）**
- `docs/tutorial/.vitepress/config.ts` — サイト設定・ナビ・Mermaid。
- `docs/tutorial/index.md` ＋ `docs/tutorial/01..07-*.md` — 章。
- `docs/tutorial/package.json` / `docs/tutorial/Dockerfile`（プレビュー用）。

**統合（変更）**
- `compose.yaml` — `web` / `runner` / `docs` サービス、`/api` プロキシ、runner→DB 結線。
- `README.md` — チュートリアルへ誘導。
- `web/nginx.conf`（任意・本番配信時）／`web/vite.config.ts` の proxy（dev）。

---

## グループA — app（Python, ドメイン純度維持）

### Task 1: `GET /users` 一覧エンドポイント

**Files:**
- Modify: `app/api/routes_user.py`, `tests/test_api_users.py`

**Interfaces:**
- Consumes: 既存 `crud.list_users(session, limit, offset) -> list[User]`, `get_session`, `UserRead`。
- Produces: `GET /users?limit&offset -> list[UserRead]`（200, `id` 昇順）。

- [x] **Step 1: 失敗するテストを書く**

`tests/test_api_users.py` に追記:
```python
async def test_list_users_returns_sorted(client):
    _install_issuer()
    for name in ["a", "b", "c"]:
        await client.post("/users", json={"name": name})
    resp = await client.get("/users?limit=10&offset=0")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 3
    ids = [u["id"] for u in body]
    assert ids == sorted(ids)  # 発行順＝ソート順
```

- [x] **Step 2: 失敗を確認**

Run: `docker compose run --rm app uv run pytest tests/test_api_users.py::test_list_users_returns_sorted -v`
Expected: FAIL（`GET /users` 未定義→404 で assert 失敗）

- [x] **Step 3: 一覧ルートを実装**

`app/api/routes_user.py`、`get_issuer` の定義後・`@router.post(...)` の前に追加:
```python
@router.get("", response_model=list[UserRead])
async def list_users(
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
) -> list[UserRead]:
    users = await crud.list_users(session, limit=limit, offset=offset)
    return [UserRead.model_validate(u, from_attributes=True) for u in users]
```

- [x] **Step 4: 通過を確認**

Run: `docker compose run --rm app uv run pytest tests/test_api_users.py -v`
Expected: PASS（既存4件＋新規1件）

- [x] **Step 5: コミット**

```bash
git add app/api/routes_user.py tests/test_api_users.py
git commit -m "feat(app): add GET /users list endpoint"
```

---

### Task 2: OpenAPI を教材品質に強化（409宣言・例・メタ情報）

**Files:**
- Modify: `app/api/routes_user.py`, `app/schemas/user.py`, `app/main.py`, `tests/test_api_users.py`

**Interfaces:**
- Produces: `/openapi.json` に `POST /users` の 409 レスポンス定義と `UserCreate`/`UserRead` の examples が含まれる。挙動（200/201/404/409）は不変。

- [x] **Step 1: 失敗するテストを書く**

`tests/test_api_users.py` に追記:
```python
async def test_openapi_declares_conflict_and_examples(client):
    schema = (await client.get("/openapi.json")).json()
    post = schema["paths"]["/users"]["post"]
    assert "409" in post["responses"]  # 衝突が宣言されている
    user_create = schema["components"]["schemas"]["UserCreate"]
    assert "example" in user_create or "examples" in str(user_create)
```

- [x] **Step 2: 失敗を確認**

Run: `docker compose run --rm app uv run pytest tests/test_api_users.py::test_openapi_declares_conflict_and_examples -v`
Expected: FAIL（409 未宣言）

- [x] **Step 3: スキーマに例を付ける**

`app/schemas/user.py` を置換:
```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "alice"}}
    )
    name: str


class UserRead(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "0uLvI2MYQL",
                "name": "alice",
                "created_at": "2026-06-28T06:03:23.931468",
            }
        }
    )
    id: str
    name: str
    created_at: datetime
```

- [x] **Step 4: POST に 409 宣言と summary/tags を付ける**

`app/api/routes_user.py` の `@router.post(...)` デコレータを置換:
```python
@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="ユーザーを作成しIDを発行",
    responses={
        409: {"description": "ID 衝突（アプリ側ロジックが一意でない場合に発生）"}
    },
)
```

- [x] **Step 5: アプリのメタ情報を設定**

`app/main.py` の `FastAPI(...)` 呼び出しを置換:
```python
    application = FastAPI(
        title="ユーザーID発行API（教材）",
        description=(
            "発行順ソート可能な base62 10文字 ID を払い出す教材用 API。"
            "/docs の Try it out から実際に発行できる。"
        ),
        version="0.2.0",
    )
```

- [x] **Step 6: 通過と全ゲートを確認**

Run:
```bash
docker compose run --rm app uv run pytest -q
docker compose run --rm app uv run ruff check . && docker compose run --rm app uv run mypy app
```
Expected: すべて PASS。

- [x] **Step 7: コミット**

```bash
git add app/api/routes_user.py app/schemas/user.py app/main.py tests/test_api_users.py
git commit -m "feat(app): enrich auto-generated OpenAPI (409, examples, metadata)"
```

---

## グループB — runner（Rust + Axum）

> 実装時、各 crate の最新 API を **context7** で確認する（axum の Router/extractor、sqlx の query マクロ、tokio mpsc、reqwest）。本グループのコードは構造とインターフェースを確定するもの。

### Task 3: runner 雛形（Axum + healthz + コンテナ + ゲート）

**Files:**
- Create: `runner/Cargo.toml`, `runner/src/main.rs`, `runner/Dockerfile`, `runner/.dockerignore`, `runner/rustfmt.toml`
- Modify: `compose.yaml`（`runner` サービス追加）

**Interfaces:**
- Produces: `runner` コンテナが `GET /healthz -> 200 {"status":"ok"}` を返す。`cargo fmt/clippy/test` が緑。

- [x] **Step 1: クレートと依存を定義**

`runner/Cargo.toml`:
```toml
[package]
name = "runner"
version = "0.1.0"
edition = "2021"

[dependencies]
axum = "0.7"
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
uuid = { version = "1", features = ["v4", "serde"] }
reqwest = { version = "0.12", default-features = false, features = ["json", "rustls-tls"] }
sqlx = { version = "0.8", default-features = false, features = ["runtime-tokio", "tls-rustls", "postgres", "uuid", "chrono", "macros"] }
chrono = { version = "0.4", features = ["serde"] }
tracing = "0.1"
tracing-subscriber = "0.3"

[dev-dependencies]
httpmock = "0.7"
```
> バージョンは実装時に context7 で最新安定を確認・固定する。

- [x] **Step 2: healthz だけの失敗するテストを書く**

`runner/src/main.rs`（初期）:
```rust
use axum::{routing::get, Json, Router};
use serde_json::{json, Value};

pub fn app() -> Router {
    Router::new().route("/healthz", get(healthz))
}

async fn healthz() -> Json<Value> {
    Json(json!({"status": "ok"}))
}

#[tokio::main]
async fn main() {
    let listener = tokio::net::TcpListener::bind("0.0.0.0:9000").await.unwrap();
    axum::serve(listener, app()).await.unwrap();
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::body::Body;
    use axum::http::{Request, StatusCode};
    use tower::ServiceExt; // oneshot

    #[tokio::test]
    async fn healthz_returns_ok() {
        let resp = app()
            .oneshot(Request::builder().uri("/healthz").body(Body::empty()).unwrap())
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::OK);
    }
}
```
> `tower` を dev/通常依存に追加（`ServiceExt::oneshot` 用）。実装時に context7 で axum テストの推奨形を確認。

- [x] **Step 3: Dockerfile とサービスを用意**

`runner/Dockerfile`:
```dockerfile
FROM rust:1-slim
WORKDIR /runner
COPY . .
RUN cargo build
CMD ["cargo", "run"]
```
`runner/.dockerignore`:
```
target
```
`compose.yaml` に追加（`volumes:` 宣言の前）:
```yaml
  runner:
    build: ./runner
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/app
    volumes:
      - ./runner:/runner
      - cargo_target:/runner/target
    ports:
      - "9000:9000"
    depends_on:
      db:
        condition: service_healthy
```
`volumes:` セクションに `cargo_target:` を追加。

- [x] **Step 4: テストとゲートが緑**

Run:
```bash
docker compose run --rm runner cargo test
docker compose run --rm runner cargo fmt --check
docker compose run --rm runner cargo clippy -- -D warnings
```
Expected: すべて PASS。

- [x] **Step 5: コミット**

```bash
git add runner compose.yaml
git commit -m "feat(runner): scaffold Axum service with healthz"
```

---

### Task 4: `jobs` 永続化（sqlx）

**Files:**
- Create: `runner/migrations/0001_create_jobs.sql`, `runner/src/store.rs`
- Modify: `runner/src/main.rs`（`mod store;` と起動時 migrate）

**Interfaces:**
- Produces: `Job` 構造体（`job_id: Uuid`, `target: String`, `n: i64`, `concurrency: i64`, `status: String`, `created_count: i64`, `conflict_count: i64`, `attempt_count: i64`, `started_at`, `finished_at: Option`, `duration_ms: Option<i64>`, `error: Option<String>`）。`JobStore` に `new(pool)`, `insert_running(job)`, `complete(job_id, counts, duration)`, `fail(job_id, error)`, `get(job_id) -> Option<Job>`, `list() -> Vec<Job>`。

- [x] **Step 1: マイグレーションを書く**

`runner/migrations/0001_create_jobs.sql`:
```sql
CREATE TABLE IF NOT EXISTS jobs (
    job_id        UUID PRIMARY KEY,
    target        TEXT        NOT NULL,
    n             BIGINT      NOT NULL,
    concurrency   BIGINT      NOT NULL,
    status        TEXT        NOT NULL,
    created_count BIGINT      NOT NULL DEFAULT 0,
    conflict_count BIGINT     NOT NULL DEFAULT 0,
    attempt_count BIGINT      NOT NULL DEFAULT 0,
    started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at   TIMESTAMPTZ,
    duration_ms   BIGINT,
    error         TEXT
);
```

- [x] **Step 2: store のテストを書く（DB 結合）**

`runner/src/store.rs` に `#[cfg(test)]` を含め、`insert_running` → `get` → `complete` → `get` が状態遷移することを検証するテストを書く（`DATABASE_URL` 必須、`sqlx::PgPool::connect`、テスト冒頭で `sqlx::migrate!()`）。
> 具体の sqlx マクロ/型は実装時に context7 で確認。`#[sqlx::test]` の利用可否も確認する。

- [x] **Step 3: 失敗を確認**

Run: `docker compose run --rm runner cargo test store`
Expected: FAIL（`store` 未実装）

- [x] **Step 4: `JobStore` を実装**（`insert_running`/`complete`/`fail`/`get`/`list`、`sqlx::query!`）。`main.rs` の起動時に `sqlx::migrate!("./migrations").run(&pool)` を実行。

- [x] **Step 5: 通過とゲート**

Run: `docker compose run --rm runner cargo test && docker compose run --rm runner cargo clippy -- -D warnings`
Expected: PASS。

- [x] **Step 6: コミット**

```bash
git add runner
git commit -m "feat(runner): persist jobs via sqlx (jobs table + JobStore)"
```

---

### Task 5: 負荷エンジン（tokio＋mpsc＋集約、N成功まで＋安全上限）

**Files:**
- Create: `runner/src/engine.rs`
- Modify: `runner/src/main.rs`（`mod engine;`）

**Interfaces:**
- Produces: `struct RunSpec { target: String, n: u64, concurrency: usize }`、`struct RunResult { created: u64, conflicts: u64, attempts: u64 }`、`async fn run_load(spec: RunSpec, client: reqwest::Client, max_attempts: u64) -> RunResult`。
- 設計: `concurrency` 個の負荷タスクが `POST {target}/users` を投げ、結果（Created/Conflict/Other）を `tokio::sync::mpsc` で**単一の集約器**へ送る。集約器が `created`/`conflicts`/`attempts` を更新し、`created >= n` か `attempts >= max_attempts` で停止信号（`tokio::sync::Notify` か `AtomicBool`）。**DB には触れない**（純ロジック）。

- [x] **Step 1: 集約ロジックの単体テストを書く**

`runner/src/engine.rs` の `#[cfg(test)]`：`httpmock` で 201 を返すモックサーバを立て、`run_load(n=50, concurrency=8, max_attempts=1000)` が `created == 50` を返すことを検証。別テストで「409 を一定割合返すモック」に対し `conflicts > 0 && created == n` を検証。

- [x] **Step 2: 失敗を確認**

Run: `docker compose run --rm runner cargo test engine`
Expected: FAIL（`engine` 未実装）

- [x] **Step 3: `run_load` を実装**

要点（実装時に context7 で reqwest/tokio の最新形を確認）:
```rust
// 擬似構造（細部は最新APIに合わせる）
pub async fn run_load(spec: RunSpec, client: reqwest::Client, max_attempts: u64) -> RunResult {
    let (tx, mut rx) = tokio::sync::mpsc::channel::<Outcome>(spec.concurrency * 2);
    let stop = std::sync::Arc::new(std::sync::atomic::AtomicBool::new(false));
    // 負荷タスク: stop が立つまで POST し続け、結果を tx で送る
    let mut handles = Vec::new();
    for _ in 0..spec.concurrency {
        let (tx, stop, client, target) = (tx.clone(), stop.clone(), client.clone(), spec.target.clone());
        handles.push(tokio::spawn(async move {
            while !stop.load(std::sync::atomic::Ordering::Relaxed) {
                let outcome = post_one(&client, &target).await;
                if tx.send(outcome).await.is_err() { break; }
            }
        }));
    }
    drop(tx);
    // 集約器（このタスク自身）
    let (mut created, mut conflicts, mut attempts) = (0u64, 0u64, 0u64);
    while let Some(o) = rx.recv().await {
        attempts += 1;
        match o { Outcome::Created => created += 1, Outcome::Conflict => conflicts += 1, Outcome::Other => {} }
        if created >= spec.n || attempts >= max_attempts {
            stop.store(true, std::sync::atomic::Ordering::Relaxed);
            break;
        }
    }
    for h in handles { let _ = h.await; }
    RunResult { created, conflicts, attempts }
}
```

- [x] **Step 4: 通過とゲート**

Run: `docker compose run --rm runner cargo test && docker compose run --rm runner cargo clippy -- -D warnings`
Expected: PASS。

- [x] **Step 5: コミット**

```bash
git add runner
git commit -m "feat(runner): load engine (tokio + mpsc aggregator, run-until-N)"
```

---

### Task 6: ジョブAPI（`POST /runs` / `GET /runs` / `GET /runs/{job_id}`）

**Files:**
- Create: `runner/src/api.rs`
- Modify: `runner/src/main.rs`（ルーティング結線、`AppState { store, client }`）

**Interfaces:**
- Consumes: `JobStore`, `run_load`。
- Produces:
  - `POST /runs` body `{ job_id: Uuid, target: String, n: u64, concurrency: usize }` → `insert_running` 後、`tokio::spawn` で `run_load` を実行し完了時に `store.complete(...)`。**即 202** を返す。
  - `GET /runs` → `Vec<Job>`（200）。`GET /runs/{job_id}` → `Job`（200）/404。

- [x] **Step 1: API 結合テストを書く**

`runner/tests/api.rs`：`httpmock` のモック target を立て、`POST /runs`（小さい n）→ 202、ポーリングで `GET /runs/{job_id}` が `status=="completed"` かつ `created==n` になることを検証。
> 実DB必須。テストは `DATABASE_URL` 前提。

- [x] **Step 2: 失敗を確認**

Run: `docker compose run --rm runner cargo test --test api`
Expected: FAIL（`/runs` 未実装）

- [x] **Step 3: `api.rs` を実装**し `main.rs` に結線（`/healthz` も維持）。`POST /runs` は `spawn` で非同期実行、`max_attempts` は `n * 4 + 10_000` 等の安全上限。

- [x] **Step 4: 通過とゲート**

Run:
```bash
docker compose run --rm runner cargo test
docker compose run --rm runner cargo fmt --check && docker compose run --rm runner cargo clippy -- -D warnings
```
Expected: すべて PASS。

- [x] **Step 5: コミット**

```bash
git add runner
git commit -m "feat(runner): async job API (POST/GET /runs with spawned load)"
```

---

## グループC — web（Vue 3 + Vite + TypeScript）

> Vite/Vue/Vitest/ESLint の最新セットアップは実装時に **context7** で確認。

### Task 7: web 雛形（Vite+Vue+TS, コンテナ, /api プロキシ, ゲート）

**Files:**
- Create: `web/package.json`, `web/vite.config.ts`, `web/tsconfig.json`, `web/index.html`, `web/src/main.ts`, `web/src/App.vue`, `web/.eslintrc.cjs`, `web/Dockerfile`, `web/.dockerignore`
- Modify: `compose.yaml`（`web` サービス）

**Interfaces:**
- Produces: `web` コンテナが Vite dev サーバ（`5173`）でアプリ shell を配信。`/api/app/*`→app、`/api/runner/*`→runner にプロキシ。`npm run typecheck`/`lint`/`test` が緑。

- [x] **Step 1: scaffolding を生成**

Run（コンテナ内、node イメージで一時生成 or 手書き）:
```bash
docker run --rm -v "$PWD/web":/web -w /web node:22-slim sh -c "npm create vite@latest . -- --template vue-ts && npm i && npm i -D vitest @vue/test-utils eslint"
```
> 生成物はコミット対象。`package.json` の scripts に `typecheck: "vue-tsc --noEmit"`, `lint: "eslint src"`, `test: "vitest run"` を追加。

- [x] **Step 2: プロキシを設定**

`web/vite.config.ts` の `server` に:
```ts
server: {
  host: true,
  proxy: {
    "/api/app": { target: "http://app:8000", rewrite: p => p.replace(/^\/api\/app/, "") },
    "/api/runner": { target: "http://runner:9000", rewrite: p => p.replace(/^\/api\/runner/, "") },
  },
},
```

- [x] **Step 3: Dockerfile とサービス**

`web/Dockerfile`:
```dockerfile
FROM node:22-slim
WORKDIR /web
COPY package*.json ./
RUN npm ci
COPY . .
CMD ["npm", "run", "dev", "--", "--host"]
```
`compose.yaml` に `web` サービス（`build: ./web`、`ports: ["5173:5173"]`、`volumes: ./web:/web` と匿名 `/web/node_modules`、`depends_on: [app, runner]`）。

- [x] **Step 4: 起動とゲートを確認**

Run:
```bash
docker compose run --rm web npm run typecheck
docker compose run --rm web npm run lint
docker compose up -d --build web && sleep 3 && curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 ; docker compose down
```
Expected: typecheck/lint PASS、HTTP 200。

- [x] **Step 5: コミット**

```bash
git add web compose.yaml
git commit -m "feat(web): scaffold Vue+Vite app with /api proxy"
```

---

### Task 8: ID 検証の純関数（TDD, Vitest）

**Files:**
- Create: `web/src/lib/validate.ts`, `web/src/lib/validate.test.ts`

**Interfaces:**
- Produces: `isBase62(s): boolean`, `isLen10(s): boolean`, `isSortedAfter(prev, cur): boolean`, `validateId(s): {len: boolean, charset: boolean}`, `summarize(ids: string[]): {total, valid, invalid, sortedOk}`。

- [x] **Step 1: 失敗するテストを書く**

`web/src/lib/validate.test.ts`:
```ts
import { describe, it, expect } from "vitest";
import { isBase62, isLen10, summarize } from "./validate";

describe("validate", () => {
  it("accepts base62 length-10", () => {
    expect(isBase62("0uLvI2MYQL")).toBe(true);
    expect(isLen10("0uLvI2MYQL")).toBe(true);
  });
  it("rejects non-base62 / wrong length", () => {
    expect(isBase62("0uLvI2-MYQ")).toBe(false);
    expect(isLen10("short")).toBe(false);
  });
  it("summarize counts invalid and sort order", () => {
    const s = summarize(["0000000001", "0000000002", "bad_id!!"]);
    expect(s.total).toBe(3);
    expect(s.invalid).toBe(1);
    expect(s.sortedOk).toBe(true);
  });
});
```

- [x] **Step 2: 失敗を確認**

Run: `docker compose run --rm web npm run test`
Expected: FAIL（`validate` 未実装）

- [x] **Step 3: `validate.ts` を実装**

```ts
const BASE62 = /^[0-9A-Za-z]+$/;
export const isBase62 = (s: string) => BASE62.test(s);
export const isLen10 = (s: string) => s.length === 10;
export const isSortedAfter = (prev: string, cur: string) => cur > prev;
export const validateId = (s: string) => ({ len: isLen10(s), charset: isBase62(s) });

export function summarize(ids: string[]) {
  let invalid = 0;
  let sortedOk = true;
  for (let i = 0; i < ids.length; i++) {
    const v = validateId(ids[i]);
    if (!v.len || !v.charset) invalid++;
    if (i > 0 && !isSortedAfter(ids[i - 1], ids[i])) sortedOk = false;
  }
  return { total: ids.length, valid: ids.length - invalid, invalid, sortedOk };
}
```

- [x] **Step 4: 通過を確認**

Run: `docker compose run --rm web npm run test`
Expected: PASS。

- [x] **Step 5: コミット**

```bash
git add web/src/lib/validate.ts web/src/lib/validate.test.ts
git commit -m "feat(web): id validation pure functions with tests"
```

---

### Task 9: 単発発行＋一覧＋妥当性可視化UI

**Files:**
- Create: `web/src/lib/api.ts`, `web/src/components/IssuePanel.vue`, `web/src/components/UserTable.vue`
- Modify: `web/src/App.vue`

**Interfaces:**
- Consumes: `validate.ts`、`/api/app` の `POST /users`・`GET /users`。
- Produces: `api.ts` に `createUser(name): Promise<UserRead>`, `listUsers(limit, offset): Promise<UserRead[]>`。UI は単発発行ボタン、発行ID一覧、妥当性バッジ（10桁/base62/ソート整合）と未達件数。

- [x] **Step 1: api クライアントを実装**（`fetch("/api/app/users", ...)`）。`UserRead` 型を定義。
- [x] **Step 2: `IssuePanel.vue`**（名前入力＋発行ボタン→`createUser`→一覧更新）と **`UserTable.vue`**（`listUsers`＋`summarize` でバッジ・件数表示）を実装、`App.vue` に組み込む。
- [x] **Step 3: 手動確認**

Run:
```bash
docker compose up -d --build db app web
# ブラウザ http://localhost:5173 で発行→一覧に10桁IDとバッジが出る
docker compose down
```
Expected: 発行が成功し、妥当なIDが緑バッジで一覧表示。

- [x] **Step 4: ゲート＆コミット**

```bash
docker compose run --rm web npm run typecheck && docker compose run --rm web npm run lint
git add web/src
git commit -m "feat(web): single-issue UI with validity visualization"
```

---

### Task 10: ジョブ起動UI（job-id採番・一覧・詳細・完了待ち）

**Files:**
- Create: `web/src/components/JobLauncher.vue`, `web/src/components/JobList.vue`, `web/src/components/JobDetail.vue`
- Modify: `web/src/lib/api.ts`, `web/src/App.vue`

**Interfaces:**
- Consumes: `/api/runner` の `POST /runs`・`GET /runs`・`GET /runs/{job_id}`。
- Produces: `api.ts` に `startRun(spec): Promise<void>`（`spec.job_id` はフロントで `crypto.randomUUID()` 採番）、`listRuns()`, `getRun(jobId)`。UI は target（app/lb）・N・並列度（1/100/1000）を選び起動→ジョブ一覧→詳細で `status`/`created`/`conflict_count` をポーリング表示。

- [x] **Step 1: api を拡張**（`startRun`/`listRuns`/`getRun`、`RunJob` 型）。
- [x] **Step 2: UI を実装**（`JobLauncher` で `job_id = crypto.randomUUID()` を採番して `POST /runs`、`JobList`＋`JobDetail` で 1〜2秒間隔ポーリング、完了で結果固定表示）。
- [ ] **Step 3: 手動確認**（Task 11 のスタックで実施）。
- [x] **Step 4: ゲート＆コミット**

```bash
docker compose run --rm web npm run typecheck && docker compose run --rm web npm run lint
git add web/src
git commit -m "feat(web): job launcher + list/detail with polling"
```

---

## グループD — 統合

### Task 11: compose 統合とエンドツーエンド衝突体験

**Files:**
- Modify: `compose.yaml`（runner を demo スタックでも使えるよう確認）, 必要なら `compose.demo.yaml`

**Interfaces:** Produces: `web`(5173)・`app`(8000)・`runner`(9000)・`db`・（demo時）`lb`+`app1/2/3` が協調。runner の target を `lb:8080` にして並列100/1000で 409 を観測、stage2 で 0 を確認。

> **検証メモ（2026-06-28, controller が curl=ブラウザUIと同一エンドポイントで実機確認）:**
> この統合で **2 件の e2e バグ**を発見・修正した（compose 自体は既存で変更不要）。
> 1. **web の target がホスト名のみ**（`app`/`lb`）→ runner は `{target}/users` にサーバ間 POST するため scheme+port 付き絶対URLが必要。`JobLauncher.vue` を `http://app:8000`/`http://lb:8080` に修正。
> 2. **runner の負荷エンジンがボディ無し POST** → app の `UserCreate` は `name` 必須で全リクエスト 422。`engine.rs post_one` を `json!({"name":"load"})` 送信に修正＋回帰防止テスト（mock の `json_body` 一致）を追加。runner ゲート（fmt/clippy/test）緑。
> **衝突の実機観測**: 並列100 では stage1/stage2 とも `created=2000/conflict=0`（クリーン）。並列600〜1000 では app(3×uvicorn)が飽和し大半が transport エラー（`Other`）になり、クリーンなスループットでは DB 律速で同一 ms のクロスプロセス重複が起きず `conflict_count=0` のまま（plan の「実機衝突は負荷依存／決定的証明は `tests/test_idgen_collision.py`」通り）。**409 経路自体は前フェーズの pytest 衝突テストで決定的に証明済み。** チュートリアル(Task13)では負荷チューニングと鳩の巣の定量説明でこの性質を扱う。

- [x] **Step 1: フルスタックを起動** ✓ db/app/runner/web 起動、`curl localhost:9000/healthz`→`{"status":"ok"}`、lb 経由 `POST /users`→201 確認。

- [x] **Step 2: ステージ1ジョブ実行** ✓ stage1 demo スタックで target=lb・N=2000・並列100 → `created=2000`/`conflict_count=0`（クリーン）。

- [~] **Step 3: 衝突スタック（stage1, 高並列）** ⚠️ target=lb・N=8000・並列600/1000 を実行したが、app 飽和（transport エラー多発）で `conflict_count=0`。実機の衝突は負荷依存（上記メモ）。決定的証明は前フェーズ `tests/test_idgen_collision.py`。

- [x] **Step 4: 修正スタック（stage2）** ✓ stage2 demo スタックで同条件（並列100）→ `created=2000`/`conflict_count=0`。worker-id 結線（`WORKER_ID`→distinct id）確認。終了後 `down` 済み。

- [ ] **Step 5: コミット**

```bash
git add compose.yaml compose.demo.yaml
git commit -m "feat: integrate web+runner into compose stacks (e2e collision demo)"
```

---

## グループE — docs（VitePress チュートリアル）

### Task 12: VitePress 雛形（ナビ・Mermaid・コンテナプレビュー）

**Files:**
- Create: `docs/tutorial/package.json`, `docs/tutorial/.vitepress/config.ts`, `docs/tutorial/index.md`, `docs/tutorial/Dockerfile`
- Modify: `compose.yaml`（任意の `docs` サービス）

**Interfaces:** Produces: `docs` コンテナが VitePress dev（`5174`）でサイトを配信。サイドバーに 7 章。Mermaid が描画される。

- [x] **Step 1: VitePress を導入**（`--user 1000:1000` で root 所有回避）

Run:
```bash
docker run --rm -v "$PWD/docs/tutorial":/d -w /d node:22-slim sh -c "npm init -y && npm i -D vitepress vitepress-plugin-mermaid mermaid"
```
`package.json` scripts に `docs:dev: "vitepress dev --host --port 5174"`, `docs:build: "vitepress build"`。

- [x] **Step 2: 設定とトップページ**（`withMermaid` ラップ・7章サイドバー・`type:module`）

`docs/tutorial/.vitepress/config.ts`（Mermaid 有効化・サイドバー7章・日本語フォントは既定で可、必要なら CSS で Noto Sans JP を指定）。`index.md` にイントロ。
> Mermaid プラグインの結線方法は実装時に context7 で確認。

- [x] **Step 3: 起動確認**（HTTP 200・Mermaid ロード確認）

Run:
```bash
docker compose up -d --build docs && sleep 4 && curl -s -o /dev/null -w "%{http_code}" http://localhost:5174 ; docker compose down
```
Expected: HTTP 200。

- [x] **Step 4: コミット**

```bash
git add docs/tutorial compose.yaml
git commit -m "docs: scaffold VitePress tutorial site (nav + mermaid)"
```

---

### Task 13: チュートリアル本文（7章・curl/Swagger・Mermaid・実機確認）

**Files:**
- Create: `docs/tutorial/01-intro.md` … `docs/tutorial/07-appendix.md`

**Interfaces:** Produces: 設計書 §6.1 の7章。各章はコピペ可能な手順、curl、Swagger 誘導、Mermaid 図を含む。

- [x] **Step 1: 01 イントロ / Webの基本構成**（Mermaid で stage1=LBなし / stage2=LB登場の対比図）。
- [x] **Step 2: 02 環境を立ち上げる**（ファイル名は `/02-setup` でサイドバーに整合）（`docker compose up`、各URL: API `/docs`・web 5173・runner 9000・docs 5174）。
- [x] **Step 3: 03 APIに触れる**（Swagger `/docs` の Try it out ＋ 同等 curl: `curl -X POST localhost:8000/users -H 'Content-Type: application/json' -d '{"name":"alice"}'` と `curl localhost:8000/users`）。
- [x] **Step 4: 04 ステージ1**（`ProblemIssuer.issue` 穴埋め要件、web 単発発行、`pytest tests/test_idgen_problem.py`）。
- [x] **Step 5: 05 衝突を観測**（実機衝突は負荷依存と明記＋決定的証明 test_idgen_collision.py を引用）（demo スタック起動、web のジョブで並列1→100→1000、ジョブ詳細の `conflict_count`、鳩の巣の定量説明＝設計書第5章を引用）。
- [x] **Step 6: 06 ステージ2**（worker-id 修正、再観測で 0、解答例 API との対比）。
- [x] **Step 7: 07 付録**（IDビット構造の図、設計判断、トラブルシュート）。
- [x] **Step 8: 実機確認**（docs:build 成功・curl スポット確認）（各章のコマンドを実際に1度なぞって通ることを確認）。
- [x] **Step 9: コミット**

```bash
git add docs/tutorial
git commit -m "docs: write 7-chapter tutorial (curl/swagger/mermaid)"
```

---

## グループF — 仕上げ

### Task 14: README 整理・全言語ゲート・引き継ぎ

**Files:**
- Modify: `README.md`

**Interfaces:** Produces: README は概要＋各URL＋チュートリアルへの誘導に整理。全ゲート緑。

- [x] **Step 1: README を整理**（教材の入口・各サービスURL・「詳細は docs/tutorial」へ誘導。冗長な手順はチュートリアルへ移し重複を排除）。

- [x] **Step 2: 全言語ゲートを最終確認**（app/runner/web すべて緑: pytest25/cargo9/vitest5）

Run:
```bash
docker compose run --rm app uv run ruff check . && docker compose run --rm app uv run ruff format --check . && docker compose run --rm app uv run mypy app && docker compose run --rm app uv run pytest -q
docker compose run --rm runner cargo fmt --check && docker compose run --rm runner cargo clippy -- -D warnings && docker compose run --rm runner cargo test
docker compose run --rm web npm run typecheck && docker compose run --rm web npm run lint && docker compose run --rm web npm run test
```
Expected: すべて PASS。

- [x] **Step 3: コミット**

```bash
git add README.md
git commit -m "docs: streamline README to onboard via tutorial"
```

---

### Task 15: 全依存ライブラリの安全な最新化（Rust Edition 含む）

> **位置づけ**: 全機能（Task 1〜14）完了後に実施する仕上げタスク。「相互依存関係を考慮したうえで安全に利用できる最大限の最新版」へ全言語のライブラリを引き上げ、全ゲート緑を維持する。最新版の確認は **context7 MCP**（利用可・課金なし）と各エコシステムの公式手段で行う。

**Files:**
- Modify: `pyproject.toml`, `uv.lock`（app/Python）
- Modify: `runner/Cargo.toml`（`edition` と各 crate）, `runner/Cargo.lock`
- Modify: `web/package.json`, `web/package-lock.json`（front）
- Modify: `docs/tutorial/package.json`, `docs/tutorial/package-lock.json`（VitePress; Task 12 完了後に存在）

**方針（KISS/YAGNI/安全第一）:**
- **安全な最大化**: メジャー含め最新へ寄せるが、相互依存で破綻するもの・stable で未提供のもの・他依存が要求する範囲を超えるものは上げない。各言語のゲートが緑であることが「安全」の定義。
- **言語横断は独立**: app / runner / web / docs はそれぞれ独立に更新（直交性）。1 サービスずつ「更新→ゲート→コミット」を回し、破壊時の切り分けを容易にする。
- すべて**コンテナ内**で実行。

- [x] **Step 1: app（Python）** ✓ pytest 8→9 等、ゲート緑

`docker compose run --rm app sh -c "uv lock --upgrade"` で lock を最新化（pyproject の制約内で最大化）。制約自体を上げたい場合は pyproject の下限/上限を見直してから `uv lock --upgrade`。その後ゲート:
```bash
docker compose run --rm app uv run ruff check . && docker compose run --rm app uv run ruff format --check . && docker compose run --rm app uv run mypy app && docker compose run --rm app uv run pytest -q
```
緑を確認してコミット（`git add pyproject.toml uv.lock`）。

- [x] **Step 2: runner（Rust）— crate と Edition** ✓ edition 2021→2024 / sqlx 0.9 / reqwest 0.13 / httpmock 0.8、ゲート緑

まず crate を最新化: `docker compose run --rm runner cargo update`（semver 範囲内）。さらに **Cargo.toml の各依存のメジャー/マイナー指定を最新安定へ引き上げ**（context7 で axum/sqlx/tokio/reqwest/uuid/chrono/tracing/httpmock/tower の最新安定を確認し、相互互換を保って固定）。**Edition は 2021→2024** へ（`edition = "2024"`; Rust 2024 は stable）。Edition 移行は `cargo fix --edition` を活用し、手動修正が要る箇所（2024 の規則変更: unsafe extern、prelude 変更、クロージャキャプチャ等）を潰す。ゲート:
```bash
docker compose up -d db
docker compose run --rm runner cargo fmt --check && docker compose run --rm runner cargo clippy -- -D warnings && docker compose run --rm runner cargo test
```
ベースイメージ `rust:1-slim` が edition 2024 を解釈できる版か確認（必要なら Dockerfile の Rust バージョンも引き上げ）。緑を確認してコミット（`git add runner`）。

- [x] **Step 3: web（Vue/Vite）** ✓ vue 3.5.39、ゲート緑

`docker compose run --rm web sh -c "npm update"` で semver 範囲内更新。メジャー更新（vite/vue/vitest/eslint/typescript-eslint 等）は context7 で互換を確認しつつ `package.json` のレンジを引き上げ→`npm install`→lock 更新。`npm ci` を使う Dockerfile があるため **lock を必ず更新・コミット**。ゲート:
```bash
docker compose run --rm web npm run typecheck && docker compose run --rm web npm run lint && docker compose run --rm web npm run test
docker compose build web   # npm ci が新 lock で通ることを確認
```
緑を確認してコミット（`git add web/package.json web/package-lock.json`）。

- [x] **Step 4: docs（VitePress）** ✓ build 緑、package-lock の name 修正

`docs/tutorial` で同様に `npm update`＋メジャーは互換確認のうえ引き上げ→lock 更新。`docs:build` が通ることを確認してコミット。

- [x] **Step 5: 全ゲート最終確認** ✓ controller が app25/runner9/web5/docs-build を再走し全緑

3〜4 言語すべてのゲートを通しで緑にし、e2e（Task 11 の衝突体験）が依然成立することを確認。

- [x] **Step 6: コミット/まとめ** ✓ サービス毎に個別コミット（c96461f/631e19c/a1a9bb3/ca7523d）

各 Step で個別コミット済みなら、最後に差分の要約を残す（更新前後の主要バージョン表を report かコミット本文に）。

---

### Task 16: コンテナ由来のファイル所有権の恒久対策＋最終確認

> **背景**: `docker run`/`docker compose run` は既定で root 実行のため、bind マウントへ書き込むと **ホスト側ファイルが root 所有**になり、ローカル（kyohei, uid=1000）から編集・削除できなくなる。Task 7 の Vite scaffold で実際に `web/` が root 所有になり、2026-06-28 に `docker run --rm -v "$PWD":/mnt alpine chown -R 1000:1000 ...` で修正済み。本タスクは**再発防止の恒久化**と**最終確認**を行う。

**Files:**
- Modify: `compose.yaml`（必要に応じて `user:` 指定）, 場合により `Dockerfile` 各種

**方針（安全第一・既存ゲートを壊さない）:**
- **恒久対策の検討と適用**: bind マウントへ書き込みうるサービス（app/runner/web/docs）の `docker compose run`/サービス実行を **ホスト UID:GID（1000:1000）で動かす**ようにする。手段の候補（KISS で1つ選ぶ）:
  - compose の各サービスに `user: "1000:1000"`（または `${UID}:${GID}`）を付与。ただし named volume（`venv`/`cargo_target`/`node_modules`）の所有権・書込み権、コンテナ内 `$HOME`/cache の書込み（cargo の `$CARGO_HOME`、npm の cache、uv のキャッシュ）に注意。動かなければ Dockerfile 側で非 root ユーザを作る、もしくは entrypoint で chown する方式へ。
  - 上記が副作用過多なら、**運用ルール**（README/plan に「bind マウントに書く一時 docker run は `--user $(id -u):$(id -g)` を付ける」）＋既存の chown ワンライナーを `scripts/` に用意、で代替（YAGNI）。
- いずれの方式でも、**全言語ゲートが緑のまま**であることを確認（所有権変更でキャッシュ書込みが壊れないこと）。

- [ ] **Step 1: 現状確認**

```bash
find . -path ./.git -prune -o -user root -print | head
```
root 所有が残っていれば `docker run --rm -v "$PWD":/mnt alpine sh -c 'find /mnt -path /mnt/.git -prune -o -user root -exec chown 1000:1000 {} +'` で是正。

- [ ] **Step 2: 恒久対策を適用**（上記方針から1つ選択し実装）。app/runner/web/docs で `docker compose run` を実行 → 生成物がホストで kyohei 所有になることを確認。

- [ ] **Step 3: 全ゲート再確認**（app/runner/web/docs）。ホットリロード・lock 更新・キャッシュ書込みが恒久対策後も機能すること。

- [ ] **Step 4: 最終確認＆コミット**

```bash
find . -path ./.git -prune -o -user root -print   # 出力が空であること
git add compose.yaml scripts 2>/dev/null; git commit -m "chore: run containers as host uid to prevent root-owned mounts"
```

---

## Self-Review（計画作成者による点検結果）

- **Spec coverage**: §3.1 一覧→Task1。§3.2 OpenAPI→Task2。§4 runner（ジョブ/エンジン/分離・非ボトルネック記録）→Task3–6。§5 web（単発・ジョブ・妥当性・台帳=ジョブ詳細）→Task7–10。§7 統合→Task11。§6 チュートリアル→Task12–13。README/最終ゲート→Task14。非目標（per-409記録なし・スライドなし・worker-id明示維持）は計画全体で遵守。
- **Placeholder scan**: Python は完全コード。Rust/Vue/VitePress は構造・主要コード・正確なコマンド・テスト仕様を記載し、バージョン依存 API は「context7 で確認」と明示（生成系 scaffolding はコマンドで生成）。
- **Type consistency**: `RunSpec/RunResult/Job`（runner）、`startRun(spec.job_id=randomUUID)`/`getRun`/`listRuns`（web↔runner）、`createUser`/`listUsers`（web↔app）、`GET /users`→`list[UserRead]`（app）を各タスク間で一致させた。runner の `POST /runs` body `{job_id,target,n,concurrency}` は Task6 と Task10 で一致。

## 既知の留意点（実装時に注意）

- **記録の非ボトルネック化**は runner の肝。負荷タスク→mpsc→単一集約器→ジョブ単位 DB 書き込み、を崩さない（per-リクエストの DB 書き込みを足さない）。
- 並列衝突は実機では負荷依存。stage1 で確実に見せるには並列度を上げる（1000）。決定的証明は既存の `tests/test_idgen_collision.py`（前フェーズ）。
- runner は同一 PostgreSQL の **別テーブル `jobs`** を sqlx 自前マイグレーションで管理（app の Alembic とは独立）。
- すべて新規 Node/Rust コマンドも**コンテナ内**で実行。`target`(cargo) と `node_modules` はボリュームで分離しホットリロードを保つ。
