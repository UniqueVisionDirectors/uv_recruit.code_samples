# web/ UIリデザイン Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `web/`（Vue 3 + Vite + TS の教材フロント）を、統一デザインシステムとビュー切替（router不使用）でモダン・アクセシブルな日本語UIに作り直す。

**Architecture:** `style.css` を共通トークン＋プリミティブ（card/btn/badge/table/status）に刷新し見た目を統一。`App.vue` がデータ所有＋ポーリング＋トップレベルのタブ状態 `activeView` を持ち、`IssueView`／`JobsView` を切替表示。`JobsView` がローカル `selectedJobId` を所有し、`JobList`⇄`JobDetail` を切替。教材シグナル（ID妥当性バッジ・conflict_count 大型メトリック）を強調。

**Tech Stack:** Vue 3 `<script setup lang="ts">`, Vite, TypeScript, Scoped CSS（**新規依存なし**）。

## Global Constraints

- **作業ブランチ:** すべて `main` 上で作業・コミットする（ブランチを切らない。ユーザー指示）。
- **コミットメッセージ末尾:** 各コミットの末尾に次の trailer を付ける（1行空けて）: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`。
- **不変の契約（変更禁止）:**
  - Vite proxy（`/api/app/*`→app:8000、`/api/runner/*`→runner:9000）。`vite.config.ts` を変更しない。
  - `src/lib/api.ts` の型 `UserRead`/`RunJob` と4関数（`createUser`/`listUsers`/`startRun`/`listRuns`）の入出力契約。`startRun` は `crypto.randomUUID()` で job_id 採番、target は絶対URL（選択肢 `http://app:8000`／`http://lb:8080`、ラベル app／lb）。
  - `src/lib/validate.ts` の純関数契約。`src/lib/validate.test.ts` を変更せず緑のまま維持。
  - `App.vue` のポーリング単一出典パターン（`anyRunning()` の間だけ 1.5s 間隔で GET /runs、全終了で停止、`onUnmounted` でタイマー停止）を意味的に維持。
  - app/(FastAPI)・runner/(Rust) のコードは変更しない。
- **コード規約（既存に合わせる）:** `<script setup lang="ts">`、関数に明示的な戻り型（`: void`/`: Promise<void>`）、未使用ローカル変数・引数を作らない（tsconfig: `noUnusedLocals`/`noUnusedParameters`）。ESLint は `flat/essential`（整形ルールなし）。
- **品質ゲート（各タスクの検証はコンテナ内で実行・全緑が条件）:**
  `docker compose run --rm web sh -c "npm run typecheck && npm run lint && npm run test"`
  （リポジトリルート `/home/kyohei/uv_recruit.code_samples` から実行）。
- **ラベル:** 日本語UI。現状踏襲＋明確化。変更したラベルは最終タスクで対応表として報告。

## テスト方針（明示）

本リデザインは主に視覚的な作り直しであり、新規ロジックは「ビュー切替（ref トグル）」「`selectedJob` の id 一致検索」など自明なものに限られる。現状 vitest は **node 環境**（DOM未設定）で動き、`validate.test.ts` は純関数をテストする。Vue コンポーネントの DOM テストには happy-dom/jsdom の追加依存と環境設定が必要だが、spec は「依存追加なし」、CLAUDE.md は YAGNI を要求しているため、**新規 DOM テストは追加しない**。各タスクは品質ゲート（typecheck/lint/test/build）緑と `validate.test.ts` の契約維持で検証し、視覚は最終タスクで手動確認する。

## File Structure

- 変更 `web/index.html` — `lang="ja"`、`<title>` を教材名に。
- 変更 `web/src/style.css` — Vite スターター残骸を全削除し、共通トークン＋プリミティブに刷新。
- 削除 `web/src/assets/hero.png`, `web/src/assets/vue.svg`, `web/src/assets/vite.svg` — どこからも参照されない Vite 残骸。
- 変更 `web/src/components/IssuePanel.vue` — 単発発行。label/a11y、発行結果ID＋妥当性バッジ表示。
- 変更 `web/src/components/UserTable.vue` — 集計バッジ＋行ごとの妥当性バッジ（✓/✕）、table プリミティブ。
- 変更 `web/src/components/JobLauncher.vue` — ラベル付きフォーム、card/btn。
- 変更 `web/src/components/JobList.vue` — キーボード選択可能な行、状態インジケータ、`select` emit。
- 変更 `web/src/components/JobDetail.vue` — 戻るボタン、conflict_count 大型メトリック、メトリクスグリッド、状態、error。
- 新規 `web/src/components/IssueView.vue` — IssuePanel＋UserTable の薄いラッパ。
- 新規 `web/src/components/JobsView.vue` — JobLauncher＋List/Detail 切替。`selectedJobId` を所有。
- 変更 `web/src/App.vue` — ヘッダー＋タブナビ（`activeView`）、IssueView/JobsView 切替。データ所有＋ポーリング維持、選択ロジックは JobsView へ移譲。

---

### Task 1: デザインシステム基盤（style.css 刷新 + index.html + 残骸削除）

**Files:**
- Modify: `web/src/style.css`（全面書き換え）
- Modify: `web/index.html`
- Delete: `web/src/assets/hero.png`, `web/src/assets/vue.svg`, `web/src/assets/vite.svg`

**Interfaces:**
- Consumes: なし
- Produces: グローバルCSSプリミティブ（後続タスクが使用）— `.card` / `.btn` `.btn--primary` / `.field` / `.badge` `.badge--ok` `.badge--ng` `.badge--warn` / `.table` / `.error-msg` / `.status` `.status--running` `.status--completed` `.status--failed` / `.spinner`、および `input`/`select`/`code` の既定スタイル。CSS変数（色・余白・`--radius`・`--shadow`・`--mono`）。`#app` はコンテナ（max-width 1100px・中央寄せ）。

- [ ] **Step 1: `web/src/style.css` を全面書き換え**

```css
:root {
  /* palette (light) — 既存の紫アクセントを継承 */
  --accent: #aa3bff;
  --accent-bg: rgba(170, 59, 255, 0.1);
  --accent-border: rgba(170, 59, 255, 0.45);
  --ok: #15803d;
  --ok-bg: rgba(21, 128, 61, 0.12);
  --ng: #dc2626;
  --ng-bg: rgba(220, 38, 38, 0.12);
  --warn: #ea580c;
  --warn-bg: rgba(234, 88, 12, 0.12);

  --text: #4b4458;
  --text-h: #08060d;
  --text-muted: #8b8595;
  --bg: #faf9fb;
  --surface: #ffffff;
  --border: #e5e4e7;
  --code-bg: #f4f3ec;

  /* spacing & shape */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --radius: 10px;
  --radius-sm: 6px;
  --shadow: rgba(0, 0, 0, 0.06) 0 4px 12px -2px, rgba(0, 0, 0, 0.04) 0 2px 4px -1px;

  --sans: system-ui, 'Segoe UI', Roboto, sans-serif;
  --mono: ui-monospace, Consolas, monospace;

  font: 16px/1.6 var(--sans);
  color-scheme: light dark;
  color: var(--text);
  background: var(--bg);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

@media (prefers-color-scheme: dark) {
  :root {
    --accent: #c084fc;
    --accent-bg: rgba(192, 132, 252, 0.15);
    --accent-border: rgba(192, 132, 252, 0.5);
    --ok: #4ade80;
    --ok-bg: rgba(74, 222, 128, 0.15);
    --ng: #f87171;
    --ng-bg: rgba(248, 113, 113, 0.15);
    --warn: #fb923c;
    --warn-bg: rgba(251, 146, 60, 0.15);

    --text: #9ca3af;
    --text-h: #f3f4f6;
    --text-muted: #6b7280;
    --bg: #0f1015;
    --surface: #16171d;
    --border: #2e303a;
    --code-bg: #1f2028;
  }
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
}

h1,
h2,
h3 {
  color: var(--text-h);
  font-weight: 600;
  line-height: 1.25;
}

p {
  margin: 0;
}

code {
  font-family: var(--mono);
  font-size: 0.875em;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--code-bg);
  color: var(--text-h);
}

#app {
  max-width: 1100px;
  margin: 0 auto;
  padding: var(--space-5) var(--space-4) var(--space-6);
}

/* card */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: var(--space-5);
  box-shadow: var(--shadow);
}

/* buttons */
.btn {
  font: inherit;
  font-weight: 500;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-h);
  cursor: pointer;
  transition: border-color 0.15s, filter 0.15s;
}

.btn:hover:not(:disabled) {
  border-color: var(--accent-border);
}

.btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn--primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.btn--primary:hover:not(:disabled) {
  filter: brightness(1.08);
}

/* form controls */
.field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.field > span {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-muted);
}

input,
select {
  font: inherit;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-h);
}

input:focus-visible,
select:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 1px;
}

/* badges */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--code-bg);
  color: var(--text-h);
  white-space: nowrap;
}

.badge--ok {
  background: var(--ok-bg);
  color: var(--ok);
}

.badge--ng {
  background: var(--ng-bg);
  color: var(--ng);
}

.badge--warn {
  background: var(--warn-bg);
  color: var(--warn);
}

/* table */
.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.table th,
.table td {
  text-align: left;
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--border);
}

.table th {
  color: var(--text-muted);
  font-weight: 600;
  font-size: 0.8rem;
}

/* error */
.error-msg {
  color: var(--ng);
  background: var(--ng-bg);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
  font-size: 0.9rem;
}

/* status indicator */
.status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 0.85rem;
}

.status--running {
  color: var(--accent);
}

.status--completed {
  color: var(--ok);
}

.status--failed {
  color: var(--ng);
}

.spinner {
  width: 12px;
  height: 12px;
  border: 2px solid var(--accent-bg);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .spinner {
    animation: none;
  }
}
```

- [ ] **Step 2: `web/index.html` の lang と title を更新**

`<html lang="en">` を `<html lang="ja">` に、`<title>web</title>` を `<title>ユーザーID発行 API デモ</title>` に変更する。他は変更しない。

- [ ] **Step 3: 未参照の Vite 残骸アセットを削除**

```bash
git rm web/src/assets/hero.png web/src/assets/vue.svg web/src/assets/vite.svg
```

- [ ] **Step 4: 品質ゲートを実行（全緑を確認）**

Run: `docker compose run --rm web sh -c "npm run typecheck && npm run lint && npm run test"`
Expected: typecheck/lint パス、vitest は `validate.test.ts` が PASS。
（この時点で既存コンポーネントは旧クラス名を一部参照したまま見た目が崩れるが、ビルド/型/lint/test は緑。後続タスクで各コンポーネントを刷新する。）

- [ ] **Step 5: コミット**

```bash
git add web/src/style.css web/index.html
git commit -m "feat(web): デザインシステム基盤（共通トークン＋プリミティブ）に刷新

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: IssuePanel（単発発行）刷新

**Files:**
- Modify: `web/src/components/IssuePanel.vue`

**Interfaces:**
- Consumes: `createUser`（`api.ts`）, `UserRead`（型）, `validateId`（`validate.ts`、戻り値 `{ len: boolean; charset: boolean }`）, Task 1 のプリミティブ（`.card`/`.field`/`.btn--primary`/`.badge`/`.error-msg`）。
- Produces: emit `issued: [user: UserRead]`（既存契約を維持。親は payload を使わず refresh する）。

- [ ] **Step 1: `web/src/components/IssuePanel.vue` を書き換え**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { createUser } from '../lib/api'
import type { UserRead } from '../lib/api'
import { validateId } from '../lib/validate'

const emit = defineEmits<{
  issued: [user: UserRead]
}>()

const name = ref('')
const error = ref('')
const loading = ref(false)
const lastIssued = ref<UserRead | null>(null)

async function issue(): Promise<void> {
  if (!name.value.trim()) return
  error.value = ''
  loading.value = true
  try {
    const user = await createUser(name.value.trim())
    lastIssued.value = user
    emit('issued', user)
    name.value = ''
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'エラーが発生しました'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="card issue-panel">
    <h2>単発発行</h2>
    <p class="hint">名前を入力してIDを1件発行し、要件（10文字・base62）を確認します。</p>
    <form class="issue-form" @submit.prevent="issue">
      <label class="field">
        <span>名前</span>
        <input v-model="name" type="text" placeholder="例: 山田太郎" :disabled="loading" />
      </label>
      <button class="btn btn--primary" type="submit" :disabled="loading || !name.trim()">
        {{ loading ? '発行中…' : '発行' }}
      </button>
    </form>
    <p v-if="error" class="error-msg" role="alert">{{ error }}</p>
    <div v-if="lastIssued" class="result">
      <span class="result-label">発行されたID</span>
      <code>{{ lastIssued.id }}</code>
      <span class="badge" :class="validateId(lastIssued.id).len ? 'badge--ok' : 'badge--ng'">
        {{ validateId(lastIssued.id).len ? '✓ 10文字' : '✕ 文字数' }}
      </span>
      <span class="badge" :class="validateId(lastIssued.id).charset ? 'badge--ok' : 'badge--ng'">
        {{ validateId(lastIssued.id).charset ? '✓ base62' : '✕ base62' }}
      </span>
    </div>
  </section>
</template>

<style scoped>
.hint {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-bottom: var(--space-4);
}

.issue-form {
  display: flex;
  gap: var(--space-3);
  align-items: flex-end;
  flex-wrap: wrap;
}

.issue-form .field {
  flex: 1 1 220px;
}

.error-msg {
  margin-top: var(--space-3);
}

.result {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--border);
}

.result-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-muted);
}
</style>
```

- [ ] **Step 2: 品質ゲートを実行**

Run: `docker compose run --rm web sh -c "npm run typecheck && npm run lint && npm run test"`
Expected: 全緑。

- [ ] **Step 3: コミット**

```bash
git add web/src/components/IssuePanel.vue
git commit -m "feat(web): IssuePanel を刷新（label/a11y・発行結果ID表示）

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: UserTable（一覧＋妥当性）刷新

**Files:**
- Modify: `web/src/components/UserTable.vue`

**Interfaces:**
- Consumes: props `users: UserRead[]`（既存）, `validateId`/`summarize`（`validate.ts`。`summarize` の戻り値 `{ total, valid, invalid, sortedOk }`）, Task 1 プリミティブ（`.card`/`.badge`/`.table`）。
- Produces: なし（純表示）。

- [ ] **Step 1: `web/src/components/UserTable.vue` を書き換え**

```vue
<script setup lang="ts">
import { computed } from 'vue'
import type { UserRead } from '../lib/api'
import { validateId, summarize } from '../lib/validate'

const props = defineProps<{
  users: UserRead[]
}>()

const ids = computed(() => props.users.map((u) => u.id))
const summary = computed(() => summarize(ids.value))
const rows = computed(() =>
  props.users.map((u) => ({ ...u, v: validateId(u.id) })),
)
</script>

<template>
  <section class="card user-table">
    <h2>ユーザー一覧</h2>
    <div class="summary" role="group" aria-label="妥当性集計">
      <span class="badge">合計 {{ summary.total }}</span>
      <span class="badge badge--ok">妥当 {{ summary.valid }}</span>
      <span class="badge" :class="summary.invalid > 0 ? 'badge--ng' : ''">不正 {{ summary.invalid }}</span>
      <span class="badge" :class="summary.sortedOk ? 'badge--ok' : 'badge--ng'">
        ソート整合 {{ summary.sortedOk ? '✓ OK' : '✕ NG' }}
      </span>
    </div>
    <div class="table-wrap">
      <table v-if="rows.length" class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>名前</th>
            <th>作成日時</th>
            <th>10文字</th>
            <th>base62</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.id">
            <td><code>{{ row.id }}</code></td>
            <td>{{ row.name }}</td>
            <td class="muted">{{ row.created_at }}</td>
            <td>
              <span class="badge" :class="row.v.len ? 'badge--ok' : 'badge--ng'">{{ row.v.len ? '✓' : '✕' }}</span>
            </td>
            <td>
              <span class="badge" :class="row.v.charset ? 'badge--ok' : 'badge--ng'">{{ row.v.charset ? '✓' : '✕' }}</span>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">ユーザーがいません。上のフォームから発行してください。</p>
    </div>
  </section>
</template>

<style scoped>
.summary {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.table-wrap {
  overflow-x: auto;
}

.muted {
  color: var(--text-muted);
  font-size: 0.85rem;
}

.empty {
  color: var(--text-muted);
}
</style>
```

- [ ] **Step 2: 品質ゲートを実行**

Run: `docker compose run --rm web sh -c "npm run typecheck && npm run lint && npm run test"`
Expected: 全緑。

- [ ] **Step 3: コミット**

```bash
git add web/src/components/UserTable.vue
git commit -m "feat(web): UserTable を刷新（集計バッジ・妥当性バッジ）

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: JobLauncher（ジョブ起動）刷新

**Files:**
- Modify: `web/src/components/JobLauncher.vue`

**Interfaces:**
- Consumes: `startRun`（`api.ts`）, Task 1 プリミティブ（`.card`/`.field`/`.btn--primary`/`.error-msg`）。
- Produces: emit `launched: []`（既存契約を維持）。

- [ ] **Step 1: `web/src/components/JobLauncher.vue` を書き換え**

`<script setup>` のロジック（target/n/concurrency/loading/error と `launch()`、コメント）は現状を維持し、template と scoped style のみ刷新する。

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { startRun } from '../lib/api'

const emit = defineEmits<{
  launched: []
}>()

// runner は target をベースURLとして使い、サーバ間で `{target}/users` に POST する。
// そのため docker ネットワーク内部の絶対URL（scheme+port）を渡す。
const target = ref('http://app:8000')
const n = ref(1000)
const concurrency = ref(1)
const loading = ref(false)
const error = ref('')

async function launch(): Promise<void> {
  error.value = ''
  loading.value = true
  try {
    await startRun({ target: target.value, n: n.value, concurrency: concurrency.value })
    emit('launched')
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'エラーが発生しました'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="card job-launcher">
    <h2>ジョブ起動</h2>
    <p class="hint">大量のID発行を並列で実行し、衝突回数（conflict_count）を観測します。</p>
    <form class="launch-form" @submit.prevent="launch">
      <label class="field">
        <span>ターゲット</span>
        <select v-model="target" :disabled="loading">
          <option value="http://app:8000">app</option>
          <option value="http://lb:8080">lb</option>
        </select>
      </label>
      <label class="field">
        <span>N（件数）</span>
        <input v-model.number="n" type="number" min="1" :disabled="loading" />
      </label>
      <label class="field">
        <span>並列度</span>
        <select v-model.number="concurrency" :disabled="loading">
          <option :value="1">1</option>
          <option :value="100">100</option>
          <option :value="1000">1000</option>
        </select>
      </label>
      <button class="btn btn--primary" type="submit" :disabled="loading">
        {{ loading ? '起動中…' : '起動' }}
      </button>
    </form>
    <p v-if="error" class="error-msg" role="alert">{{ error }}</p>
  </section>
</template>

<style scoped>
.hint {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-bottom: var(--space-4);
}

.launch-form {
  display: flex;
  gap: var(--space-3);
  align-items: flex-end;
  flex-wrap: wrap;
}

.launch-form .field {
  flex: 1 1 140px;
}

.error-msg {
  margin-top: var(--space-3);
}
</style>
```

- [ ] **Step 2: 品質ゲートを実行**

Run: `docker compose run --rm web sh -c "npm run typecheck && npm run lint && npm run test"`
Expected: 全緑。

- [ ] **Step 3: コミット**

```bash
git add web/src/components/JobLauncher.vue
git commit -m "feat(web): JobLauncher を刷新（ラベル付きフォーム・card）

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: JobList（ジョブ一覧）刷新

**Files:**
- Modify: `web/src/components/JobList.vue`

**Interfaces:**
- Consumes: props `jobs: RunJob[]`（既存）, Task 1 プリミティブ（`.table`/`.status`/`.spinner`）。
- Produces: emit `select: [jobId: string]`（既存契約を維持）。行は `role="button"` + `tabindex="0"` でキーボード選択可能。

- [ ] **Step 1: `web/src/components/JobList.vue` を書き換え**

```vue
<script setup lang="ts">
import type { RunJob } from '../lib/api'

defineProps<{
  jobs: RunJob[]
}>()

const emit = defineEmits<{
  select: [jobId: string]
}>()

const statusLabel: Record<string, string> = {
  running: '実行中',
  completed: '完了',
  failed: '失敗',
}
</script>

<template>
  <section class="job-list">
    <h2>ジョブ一覧</h2>
    <div class="table-wrap">
      <table v-if="jobs.length" class="table">
        <thead>
          <tr>
            <th>job_id</th>
            <th>target</th>
            <th>N</th>
            <th>並列度</th>
            <th>状態</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="job in jobs"
            :key="job.job_id"
            class="row"
            role="button"
            tabindex="0"
            @click="emit('select', job.job_id)"
            @keydown.enter.prevent="emit('select', job.job_id)"
            @keydown.space.prevent="emit('select', job.job_id)"
          >
            <td><code>{{ job.job_id.slice(0, 8) }}</code></td>
            <td>{{ job.target }}</td>
            <td>{{ job.n }}</td>
            <td>{{ job.concurrency }}</td>
            <td>
              <span class="status" :class="`status--${job.status}`">
                <span v-if="job.status === 'running'" class="spinner" aria-hidden="true"></span>
                <span v-else aria-hidden="true">{{ job.status === 'completed' ? '✓' : job.status === 'failed' ? '✕' : '•' }}</span>
                {{ statusLabel[job.status] ?? job.status }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">ジョブがありません。上のフォームから起動してください。</p>
    </div>
  </section>
</template>

<style scoped>
.table-wrap {
  overflow-x: auto;
}

.row {
  cursor: pointer;
}

.row:hover {
  background: var(--accent-bg);
}

.row:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}

.empty {
  color: var(--text-muted);
}
</style>
```

- [ ] **Step 2: 品質ゲートを実行**

Run: `docker compose run --rm web sh -c "npm run typecheck && npm run lint && npm run test"`
Expected: 全緑。

- [ ] **Step 3: コミット**

```bash
git add web/src/components/JobList.vue
git commit -m "feat(web): JobList を刷新（キーボード選択可・状態インジケータ）

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: JobDetail（ジョブ詳細・衝突強調）刷新

**Files:**
- Modify: `web/src/components/JobDetail.vue`

**Interfaces:**
- Consumes: props `job: RunJob | null`（既存）, Task 1 プリミティブ（`.status`/`.spinner`/`.error-msg`）。
- Produces: emit `back: []`（新規。一覧へ戻る。Task 8 の JobsView が listen する）。

- [ ] **Step 1: `web/src/components/JobDetail.vue` を書き換え**

```vue
<script setup lang="ts">
import type { RunJob } from '../lib/api'

defineProps<{
  job: RunJob | null
}>()

const emit = defineEmits<{
  back: []
}>()

const statusLabel: Record<string, string> = {
  running: '実行中',
  completed: '完了',
  failed: '失敗',
}
</script>

<template>
  <section class="job-detail">
    <div class="detail-head">
      <button class="btn back-btn" type="button" @click="emit('back')">← 一覧へ戻る</button>
      <h2>ジョブ詳細</h2>
    </div>
    <p v-if="!job" class="empty">ジョブを選択してください</p>
    <template v-else>
      <div class="status-row">
        <span class="status" :class="`status--${job.status}`">
          <span v-if="job.status === 'running'" class="spinner" aria-hidden="true"></span>
          <span v-else aria-hidden="true">{{ job.status === 'completed' ? '✓' : job.status === 'failed' ? '✕' : '•' }}</span>
          {{ statusLabel[job.status] ?? job.status }}
        </span>
        <code class="job-id">{{ job.job_id }}</code>
      </div>

      <div
        class="conflict-card"
        :class="job.conflict_count > 0 ? 'conflict-card--warn' : 'conflict-card--zero'"
      >
        <span class="conflict-label">conflict_count（衝突）</span>
        <span class="conflict-value">{{ job.conflict_count }}</span>
        <span class="conflict-note">{{ job.conflict_count > 0 ? '衝突が発生しました' : '衝突なし' }}</span>
      </div>

      <dl class="metrics">
        <div class="metric">
          <dt>created_count</dt>
          <dd>{{ job.created_count }}</dd>
        </div>
        <div class="metric">
          <dt>attempt_count</dt>
          <dd>{{ job.attempt_count }}</dd>
        </div>
        <div class="metric">
          <dt>duration_ms</dt>
          <dd>{{ job.duration_ms ?? '—' }}</dd>
        </div>
        <div class="metric">
          <dt>N / 並列度</dt>
          <dd>{{ job.n }} / {{ job.concurrency }}</dd>
        </div>
      </dl>

      <p v-if="job.error" class="error-msg" role="alert">{{ job.error }}</p>
    </template>
  </section>
</template>

<style scoped>
.detail-head {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.detail-head h2 {
  margin: 0;
}

.back-btn {
  font-size: 0.85rem;
  padding: var(--space-1) var(--space-3);
}

.status-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  margin-bottom: var(--space-4);
}

.job-id {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.conflict-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-5);
  border: 2px solid var(--border);
  border-radius: var(--radius);
  margin-bottom: var(--space-4);
}

.conflict-card--zero {
  background: var(--surface);
}

.conflict-card--warn {
  background: var(--warn-bg);
  border-color: var(--warn);
}

.conflict-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-muted);
}

.conflict-value {
  font-size: 3.5rem;
  font-weight: 700;
  line-height: 1;
  color: var(--text-h);
}

.conflict-card--warn .conflict-value {
  color: var(--warn);
}

.conflict-note {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--space-3);
  margin: 0;
}

.metric {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: var(--space-3);
}

.metric dt {
  font-size: 0.8rem;
  font-family: var(--mono);
  color: var(--text-muted);
}

.metric dd {
  margin: 4px 0 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-h);
}

.empty {
  color: var(--text-muted);
}
</style>
```

- [ ] **Step 2: 品質ゲートを実行**

Run: `docker compose run --rm web sh -c "npm run typecheck && npm run lint && npm run test"`
Expected: 全緑。（`back` emit は現状の `App.vue` では未 listen だが、未 listen の emit は型エラーにならない。）

- [ ] **Step 3: コミット**

```bash
git add web/src/components/JobDetail.vue
git commit -m "feat(web): JobDetail を刷新（戻る・conflict_count 大型メトリック）

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: IssueView（単発発行ビュー）新規作成

**Files:**
- Create: `web/src/components/IssueView.vue`

**Interfaces:**
- Consumes: `IssuePanel`（emit `issued: [user]`）, `UserTable`（prop `users`）, `UserRead`（型）, `.error-msg`。
- Produces: props `{ users: UserRead[]; fetchError: string }`、emit `issued: []`（payload なしで親へ再 emit）。

- [ ] **Step 1: `web/src/components/IssueView.vue` を作成**

```vue
<script setup lang="ts">
import IssuePanel from './IssuePanel.vue'
import UserTable from './UserTable.vue'
import type { UserRead } from '../lib/api'

defineProps<{
  users: UserRead[]
  fetchError: string
}>()

const emit = defineEmits<{
  issued: []
}>()
</script>

<template>
  <div class="view-stack">
    <IssuePanel @issued="emit('issued')" />
    <p v-if="fetchError" class="error-msg" role="alert">{{ fetchError }}</p>
    <UserTable :users="users" />
  </div>
</template>

<style scoped>
.view-stack {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
</style>
```

- [ ] **Step 2: 品質ゲートを実行**

Run: `docker compose run --rm web sh -c "npm run typecheck && npm run lint && npm run test"`
Expected: 全緑。（この時点で IssueView は未使用だが、`.vue` の型/lint チェック対象。`noUnusedLocals` はコンポーネント未使用を咎めないため緑。）

- [ ] **Step 3: コミット**

```bash
git add web/src/components/IssueView.vue
git commit -m "feat(web): IssueView を追加（IssuePanel＋UserTable ラッパ）

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: JobsView（負荷ジョブビュー・一覧⇄詳細切替）新規作成

**Files:**
- Create: `web/src/components/JobsView.vue`

**Interfaces:**
- Consumes: `JobLauncher`（emit `launched`）, `JobList`（prop `jobs`、emit `select: [jobId]`）, `JobDetail`（prop `job`、emit `back`）, `RunJob`（型）, `.card`/`.error-msg`。
- Produces: props `{ jobs: RunJob[]; jobsError: string }`、emit `launched: []`。ローカル state `selectedJobId: string | null` を所有し、`selectedJob` を `jobs` から id 一致で導出。

- [ ] **Step 1: `web/src/components/JobsView.vue` を作成**

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import JobLauncher from './JobLauncher.vue'
import JobList from './JobList.vue'
import JobDetail from './JobDetail.vue'
import type { RunJob } from '../lib/api'

const props = defineProps<{
  jobs: RunJob[]
  jobsError: string
}>()

const emit = defineEmits<{
  launched: []
}>()

// 選択は純粋に表示の関心事なので JobsView がローカルに所有し、App のポーリングと直交させる。
// 詳細は GET /runs の単一出典（props.jobs）から id 一致で導出するため個別取得しない。
const selectedJobId = ref<string | null>(null)

const selectedJob = computed<RunJob | null>(() =>
  selectedJobId.value === null
    ? null
    : (props.jobs.find((j) => j.job_id === selectedJobId.value) ?? null),
)

function onSelect(jobId: string): void {
  selectedJobId.value = jobId
}

function onBack(): void {
  selectedJobId.value = null
}
</script>

<template>
  <div class="view-stack">
    <JobLauncher @launched="emit('launched')" />
    <p v-if="jobsError" class="error-msg" role="alert">{{ jobsError }}</p>
    <div class="card">
      <JobDetail v-if="selectedJobId !== null" :job="selectedJob" @back="onBack" />
      <JobList v-else :jobs="jobs" @select="onSelect" />
    </div>
  </div>
</template>

<style scoped>
.view-stack {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
</style>
```

- [ ] **Step 2: 品質ゲートを実行**

Run: `docker compose run --rm web sh -c "npm run typecheck && npm run lint && npm run test"`
Expected: 全緑。

- [ ] **Step 3: コミット**

```bash
git add web/src/components/JobsView.vue
git commit -m "feat(web): JobsView を追加（一覧⇄詳細切替・selectedJobId 所有）

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: App.vue（ヘッダー＋タブ切替）— 統合

**Files:**
- Modify: `web/src/App.vue`

**Interfaces:**
- Consumes: `IssueView`（props `users`/`fetchError`、emit `issued`）, `JobsView`（props `jobs`/`jobsError`、emit `launched`）, `listUsers`/`listRuns`（`api.ts`）, `UserRead`/`RunJob`（型）。
- Produces: 最終的なアプリ。データ所有（users/jobs）＋ポーリング単一出典を維持。トップレベル state `activeView: 'issue' | 'jobs'`。選択ロジック（旧 `selectedJobId`/`selectedJob`/`onSelectJob`）は JobsView へ移譲し、App からは削除。

- [ ] **Step 1: `web/src/App.vue` を書き換え**

```vue
<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import IssueView from './components/IssueView.vue'
import JobsView from './components/JobsView.vue'
import { listUsers, listRuns } from './lib/api'
import type { UserRead, RunJob } from './lib/api'

type View = 'issue' | 'jobs'
const activeView = ref<View>('issue')

const users = ref<UserRead[]>([])
const fetchError = ref('')

async function refresh(): Promise<void> {
  fetchError.value = ''
  try {
    users.value = await listUsers(100, 0)
  } catch (e) {
    fetchError.value = e instanceof Error ? e.message : 'フェッチエラー'
  }
}

function onIssued(): void {
  void refresh()
}

const jobs = ref<RunJob[]>([])
const jobsError = ref('')

// runner はジョブを非同期実行し、完了/失敗時にだけ jobs を更新する。running が残る間だけ
// 一覧をポーリングし、全ジョブが終了したら止める（無駄な定常ポーリングを避ける）。
let jobsTimerId: ReturnType<typeof setInterval> | null = null

function anyRunning(): boolean {
  return jobs.value.some((j) => j.status === 'running')
}

async function refreshJobs(): Promise<void> {
  jobsError.value = ''
  try {
    jobs.value = await listRuns()
  } catch (e) {
    jobsError.value = e instanceof Error ? e.message : 'フェッチエラー'
  }
}

function stopJobsPolling(): void {
  if (jobsTimerId !== null) {
    clearInterval(jobsTimerId)
    jobsTimerId = null
  }
}

function ensureJobsPolling(): void {
  if (jobsTimerId !== null || !anyRunning()) return
  jobsTimerId = setInterval(() => {
    void (async () => {
      await refreshJobs()
      if (!anyRunning()) stopJobsPolling()
    })()
  }, 1500)
}

function onLaunched(): void {
  void (async () => {
    await refreshJobs()
    ensureJobsPolling()
  })()
}

onMounted(() => {
  void refresh()
  void (async () => {
    await refreshJobs()
    ensureJobsPolling()
  })()
})

onUnmounted(() => {
  stopJobsPolling()
})
</script>

<template>
  <header class="app-header">
    <h1>ユーザーID発行 API デモ</h1>
    <p class="subtitle">
      IDを発行して要件（10文字・base62・発行順ソート整合）を確認し、負荷ジョブで衝突を観測します。
    </p>
  </header>

  <nav class="tabs" aria-label="表示切替">
    <button
      class="tab"
      type="button"
      :class="{ 'tab--active': activeView === 'issue' }"
      :aria-pressed="activeView === 'issue'"
      @click="activeView = 'issue'"
    >
      単発発行
    </button>
    <button
      class="tab"
      type="button"
      :class="{ 'tab--active': activeView === 'jobs' }"
      :aria-pressed="activeView === 'jobs'"
      @click="activeView = 'jobs'"
    >
      負荷ジョブ
    </button>
  </nav>

  <main>
    <IssueView
      v-if="activeView === 'issue'"
      :users="users"
      :fetch-error="fetchError"
      @issued="onIssued"
    />
    <JobsView
      v-else
      :jobs="jobs"
      :jobs-error="jobsError"
      @launched="onLaunched"
    />
  </main>
</template>

<style scoped>
.app-header {
  margin-bottom: var(--space-5);
}

.app-header h1 {
  font-size: 1.75rem;
  letter-spacing: -0.02em;
  margin: 0 0 var(--space-2);
}

.subtitle {
  color: var(--text-muted);
  font-size: 0.95rem;
}

.tabs {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-5);
  border-bottom: 1px solid var(--border);
}

.tab {
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  background: none;
  border: none;
  color: var(--text-muted);
  padding: var(--space-3) var(--space-4);
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}

.tab:hover {
  color: var(--text-h);
}

.tab:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}

.tab--active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}
</style>
```

- [ ] **Step 2: 品質ゲート＋本番ビルドを実行**

Run: `docker compose run --rm web sh -c "npm run typecheck && npm run lint && npm run test && npm run build"`
Expected: 全緑＋ `vite build` 成功。

- [ ] **Step 3: 手動視覚確認（任意だが推奨）**

スタックを起動して画面を確認する:
`docker compose up -d --build db app solution runner web`
ブラウザで `http://localhost:5173` を開き、(1) 単発発行→ID＋妥当性バッジ表示、(2) タブで負荷ジョブへ切替、(3) ジョブ起動→一覧に running 表示→行クリックで詳細、conflict_count 強調、(4)「← 一覧へ戻る」で一覧へ。
衝突を観測したい場合は demo 構成（target=lb）:
`ID_STRATEGY=stage1 docker compose -f compose.yaml -f compose.demo.yaml up -d --build db app1 app2 app3 lb runner web`

- [ ] **Step 4: コミット**

```bash
git add web/src/App.vue
git commit -m "feat(web): App をタブ切替＋ヘッダーに刷新（ビュー切替で統合）

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## ラベル対応表（最終報告用）

| 旧ラベル | 新ラベル | 備考 |
| --- | --- | --- |
| ユーザー管理（h1） | ユーザーID発行 API デモ（h1） | 教材名に明確化 |
| ユーザーID発行（h2） | 単発発行 | タブ名と一致させる |
| ユーザー一覧 | ユーザー一覧 | 変更なし |
| ジョブ管理（h1） | （タブ「負荷ジョブ」に集約） | h1 廃止しタブ化 |
| ジョブ起動 / ジョブ一覧 / ジョブ詳細 | 同左 | 変更なし |
| status / 10桁 | 状態 / 10文字 | 日本語明確化（10桁→10文字） |

> チュートリアル本文（`docs/tutorial/`）が本画面のラベルを参照している場合は、上記変更箇所の追従要否を最終報告で確認する。

## 完了条件

- 全9タスクのコミットが `main` 上に存在。
- 最終ゲート `typecheck && lint && test && build` が全緑、`validate.test.ts` 緑維持。
- 不変の契約（proxy/型/api・validate 契約/ポーリング単一出典/app・runner 不変更）を全て満たす。
- 変更点要約とラベル対応表を報告。
