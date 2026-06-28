# `web/` UIリデザイン 設計

- 日付: 2026-06-29
- 対象: `web/`（教材サンプル「ユーザーID発行API」の可視化フロント。Vue 3 + Vite + TypeScript、Vite dev 5173）
- 目的: 素のHTMLから脱却し、モダン・統一的・アクセシブルな日本語UIに作り直す。教材シグナル（**IDの妥当性**と**衝突回数 conflict_count**）を視覚的に強調する。

## 背景と現状

現状アーキテクチャはクリーン:

- `App.vue` が users・jobs を所有し、ポーリングを単一出典で管理。5つのコンポーネント（`IssuePanel`/`UserTable`/`JobLauncher`/`JobList`/`JobDetail`）は概ね純表示。
- `lib/api.ts`（`createUser`/`listUsers`/`startRun`/`listRuns`、型 `UserRead`/`RunJob`）と `lib/validate.ts`（`isBase62`/`isLen10`/`isSortedAfter`/`validateId`/`summarize`）は契約として固定。

問題点:

- `style.css` が Vite スターターテンプレートの残骸（`.hero`/`#next-steps`/`#spacer`/`.ticks` 等）のまま。各コンポーネントが参照するクラス（`.badge-ok`/`.badge-ng`/`.summary-bar`/`.error-msg` など）は**未定義**で、実質スタイルのない生HTML。

## 教材文脈（この画面が伝えるもの）

ユーザーID発行APIを「触って・見て」学ぶ画面。2つの体験を提供する:

1. **単発発行**: IDを1件ずつ発行し、要件（10文字・base62・発行順ソート整合）を満たすか目で確認。
2. **負荷ジョブ**: 大量発行を並列で走らせ、**衝突回数（conflict_count）**を観測。

→ UI は特に「IDの妥当性」と「conflict_count」を視覚的に目立たせる。

## 決定事項（ユーザー合意済み）

- スタイリング: **Scoped CSS（依存追加なし）**。共通トークン＋プリミティブを `style.css` に置き、各コンポーネントの scoped CSS は固有レイアウトのみ。
- テーマ: **既存の紫アクセント（`--accent: #aa3bff`）を整理して継承**。ライト/ダーク両対応トークンを土台に、Vite残骸を削除。
- ナビゲーション: **ビュー切替（SPA風・vue-router 不使用）**。常時2カラム表示はこの方針で上書き。

## アーキテクチャ

### デザインシステム（統一の核）

`style.css` の Vite 残骸を全削除し、共通トークンとプリミティブに置換する。**これが「統一的UI」の肝**で、見た目の一貫性はここで担保する。

- **トークン**（`:root` ＋ `@media (prefers-color-scheme: dark)`）
  - 色: `--accent`（紫＝主操作/ブランド、既存値継承）、`--ok`（緑＝valid）、`--ng`（赤＝invalid）、`--warn`（橙〜赤＝衝突強調）、`--text`/`--text-h`/`--bg`/`--surface`/`--border`。
  - 余白: `--space-1..6`（4/8/12/16/24/32px）、`--radius`、`--shadow`。
  - タイポ: 見出し階層を教材向けに抑制（現 h1 56px は過大なので縮小）。
- **共通プリミティブ（全コンポーネントで再利用、グローバルCSS）**: カード `.card`、ボタン `.btn`（主/副）、入力・select の共通スタイル、バッジ `.badge`（ok/ng/neutral）、テーブル `.table`、ステータス表示（running スピナー / completed / failed）。
  - 各コンポーネントの scoped CSS は「固有レイアウト」だけを持つ。配色・形状・余白は共通プリミティブ/トークンに集約。

### ナビゲーション構造（ビュー切替・router 不使用）

トップレベルはタブ切替、負荷ジョブ内は一覧⇄詳細切替。

- **`App.vue`**: データ所有とポーリングを従来どおり維持（users・jobs を所有、polling 単一出典）。加えてトップレベルのナビ状態 `activeView: 'issue' | 'jobs'` を持つ。タブ（`role="tablist"` のセグメントコントロール）で切替し、各 View に props で渡す（1段の浅い受け渡し）。
  - タブ1「単発発行」→ `IssueView`
  - タブ2「負荷ジョブ」→ `JobsView`
- **`IssueView.vue`**（新規・薄いラッパ）: props `users`・`fetchError`、emits `issued`。`IssuePanel` ＋ `UserTable` を縦に並べる。
- **`JobsView.vue`**（新規・薄いラッパ）: props `jobs`・`jobsError`、emits `launched`。**ローカルなナビ状態 `selectedJobId` を所有**（選択は純粋に表示の関心事なので App から移し、ポーリングと直交させる）。
  - `JobLauncher` をビュー上部に**常時表示**（起動が起点・ポーリング契機のため）。
  - その下が切替領域: `selectedJobId === null` → `JobList`（行を選択可能）、選択あり → `JobDetail`（先頭に「← 一覧へ戻る」ボタン、衝突回数を大型メトリックで強調）。
  - 選択は `JobList` の `select` emit を受けて `selectedJobId` を設定。詳細は `jobs`（GET /runs の単一出典）から導出するため個別取得しない。

### 教材シグナルの強調

- **ID妥当性**（`UserTable`）: 各行に `10桁` / `base62` バッジ（ok=緑/ng=赤、かつ ✓/✕ やアイコン併記で色依存を回避）。集計バー（合計 / 妥当 / 不正 / ソート整合）をカード上部に大きめバッジで配置。`invalid > 0` やソートNGは赤系で目立たせる。
- **conflict_count（最重要）**（`JobDetail`）: 衝突回数を**専用の大型メトリックカード**に。0件＝中立、1件以上＝`--warn` の大きな数字＋「衝突」ラベル＋アイコンで強調。他メトリクス（created_count / attempt_count / duration_ms / status）は小さめのメトリクスグリッドに。
- **ジョブ状態**: running＝スピナー＋「実行中」、completed＝✓緑、failed＝✕赤＋error メッセージ表示。`JobList` 行はキーボードでも選択可能にし、選択行をハイライト。

### アクセシビリティ

- 全 input/select に `<label>` 紐付け（`for`/`id` または wrapping）。
- 状態は色のみに依存せずテキスト/アイコン併記。
- ジョブ行選択をキーボード操作可能に（現状の `div @click` を `<button>` 化等で改善）。タブは ARIA tab パターン。
- フォーカスリング・十分なコントラストを確保。レスポンシブ（モバイル〜デスクトップ。各 View 内は `@media (max-width:1024px)` で縦スタック）。

## データフロー

```
App.vue (owns: users, jobs, polling, activeView)
 ├─ tab nav (activeView)
 ├─ IssueView  [users, fetchError] --issued--> App.refresh()
 │    ├─ IssuePanel  --issued--> emit up
 │    └─ UserTable   [users]  (validate/summarize で妥当性表示)
 └─ JobsView   [jobs, jobsError] --launched--> App.refreshJobs()+polling
      ├─ JobLauncher --launched--> emit up
      └─ (selectedJobId===null ? JobList[jobs] --select--> set selectedJobId
                                : JobDetail[selectedJob] + 戻るボタン)
```

- ポーリング: runner が非同期実行し完了/失敗時に jobs を更新。`anyRunning()` が true の間だけ GET /runs を 1.5s 間隔でポーリングし、全終了で停止。タイマーリーク無し（`onUnmounted` で停止）。**この単一出典パターンを維持**。

## エラーハンドリング

- 各 API 呼び出しは既存どおり `try/catch`。`App` の `fetchError`/`jobsError`、`IssuePanel`/`JobLauncher` のローカル `error` をそれぞれ表示（共通の `.error-msg`/エラー表示プリミティブで統一）。
- `JobDetail` の `error`（failed 時）を可視化。

## テスト / 品質ゲート（すべてコンテナ内）

- `docker compose run --rm web npm run typecheck`（vue-tsc）緑。
- `docker compose run --rm web npm run lint`（ESLint flat config）緑。
- `docker compose run --rm web npm run test`（vitest、`validate.test.ts` を壊さない）緑。
- 衝突観測の手動確認（任意）: demo 構成 `ID_STRATEGY=stage1 docker compose -f compose.yaml -f compose.demo.yaml up -d --build db app1 app2 app3 lb runner web`、target=lb。

## 不変条件（壊さないもの）

- Vite proxy（`/api/app/*`→app:8000、`/api/runner/*`→runner:9000）を変更しない。
- 型 `UserRead`/`RunJob`、`api.ts` の4関数の入出力契約、各エンドポイント（`POST /api/app/users {name}`・`GET /api/app/users`・`POST /api/runner/runs {job_id,target,n,concurrency}`(202)・`GET /api/runner/runs`）。
- `startRun` は `crypto.randomUUID()` で job_id 採番。target は runner が `{target}/users` に投げる絶対URL（選択肢 `http://app:8000`／`http://lb:8080`、ラベル app／lb）。
- `lib/validate.ts` の純関数契約（`validate.test.ts` 緑のまま）。`api.ts`/`validate.ts` の内部リファクタは可だが契約とテストは壊さない。
- app/(FastAPI)・runner/(Rust) のコードは変更しない。
- App 所有のポーリング単一出典パターンを維持。

## ラベル方針

現状を踏襲/明確化（単発発行・ユーザー一覧・妥当性・ジョブ起動・ターゲット・N（件数）・並列度・ジョブ一覧・ジョブ詳細・conflict_count（衝突））。変更する場合は対応表を成果物として報告（チュートリアルが本画面を参照しているため）。

## 成果物

- 作り直した `web/` の UI（Vue 3 + TS、Scoped CSS、依存追加なし）。全ゲート緑。
- 変更点の要約と、（あれば）変更したラベルの対応表。

## スコープ外（YAGNI）

- vue-router の導入。
- UIライブラリ/新規依存の追加。
- app/runner/api/validate の契約・挙動変更。
- ポーリング方式の再設計。
