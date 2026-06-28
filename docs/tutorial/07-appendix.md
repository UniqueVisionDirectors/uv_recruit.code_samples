# 付録

## A. ID ビット構造

### 全体レイアウト

整数 value のビット配置（59 bit 有効、base62 × 10 文字に収まる）:

```
 bit 58 ............. 18 | bit 17 ...... 12 | bit 11 ......... 0
 ←──── ms (41 bit) ────→ | ← worker (6 bit)→ | ← sequence (12 bit) →
```

| フィールド | ビット幅 | 範囲 | 役割 |
|---|---|---|---|
| ms | 41 bit | 0 〜 2^41 − 1 | 現在時刻（エポック差分ミリ秒）|
| worker_id | 6 bit | 0 〜 63 | プロセス識別子 |
| sequence | 12 bit | 0 〜 4095 | 同一ミリ秒内の連番（乱数ベース）|

### エポック基準時刻

```python
EPOCH_MS = 1735689600000  # 2025-01-01T00:00:00Z
```

システム時刻との差分 `time_ms - EPOCH_MS` を ms フィールドに格納します。
41 bit で約 **69 年分**（〜2094 年まで）の時刻を表現できます。

### base62 エンコード

```python
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
# ↑ 62 文字。数字 → 大文字 → 小文字 の順
```

59 bit の整数を base62 × 10 文字にエンコードします（`62^10 = 8.39 × 10^17 > 2^59`）。

### 組み立て式

```python
value = (ms << 18) | (worker_id << 12) | sequence
id_str = encode_base62(value)   # → 10 文字
```

---

## B. 設計判断

### なぜ base62 × 10 文字か

| 選択肢 | 問題点 |
|---|---|
| 純連番（1, 2, 3, …）| 予測可能・分散生成不可 |
| UUID v4（ランダム 128bit）| 発行順にソートできない |
| Snowflake ID（Twitter）| 64bit → base10 で最大 19 桁（人間には読みにくい）|
| **この実装**（base62 × 10）| 発行順ソート可能・URL セーフ・コンパクト（10 文字）|

### なぜ worker-id が必要か

`(ms, sequence)` の 2 要素では、複数プロセスが独立して乱数シーケンスを選ぶ際に、同一ミリ秒で同一シーケンスが選ばれる可能性があります（誕生日問題）。
`worker_id` という第 3 の次元を加えることで、**同一 ms × 同一 sequence でも worker が異なれば衝突しない**ことを構造的に保証します。

### なぜ sequence の先頭を乱数にするか

純連番（seq=0, 1, 2, …）だと、同一ミリ秒の ID が連続した値になります。
乱数ベース（`seq_base` を ms ごとにランダム初期化）にすることで、ID を見ただけでは発行数を推測されにくくなります（予測困難性）。

### DB の一意性保証との関係

`users.id` は PostgreSQL の **PRIMARY KEY**（一意制約）で保護されています。
stage1 で ID が衝突した場合、DB 側の制約が 409 を返します（`duplicate key` エラーをキャッチして HTTP 409 に変換）。

この教材では ID 生成側で衝突させず、DB 保証には頼らないことを目標にしています。

---

## C. トラブルシュート

### `docker compose up --build` が失敗する

```bash
# ログを確認
docker compose logs app
docker compose logs runner
```

DB の healthcheck が通るまで数秒かかる場合があります。少し待ってから再実行してください。

### `POST /users` が 500 を返す

`app` サービスのデフォルト戦略は `ID_STRATEGY=problem`（未実装）です。
[04 章](/04-stage1) で `ProblemIssuer.issue()` を実装してください。

動作確認だけしたい場合は解答例 API（ポート 8001）を使ってください:

```bash
curl -s -X POST http://localhost:8001/users \
  -H 'Content-Type: application/json' \
  -d '{"name": "test"}'
```

### runner が `http://localhost:9000/healthz` に応答しない

runner はビルドに時間がかかる場合があります（Rust の初回コンパイル）。

```bash
docker compose logs -f runner
```

`Listening on 0.0.0.0:9000` が表示されるまで待ってください。

### デモスタックで lb が起動しない

nginx の設定ファイルが必要です:

```bash
ls demo/nginx.conf
```

ファイルが存在しない場合はリポジトリを最新にしてください。

### テストが失敗する

```bash
# 依存ライブラリのインストール状態を確認
docker compose run --rm app uv sync

# 全テストを実行
docker compose run --rm app uv run pytest -v
```

### ポート競合

デフォルトポート（8000/8001/5173/9000/5174）が他のプロセスに使われている場合は:

```bash
# 使用中のポートを確認
ss -tlnp | grep -E '8000|8001|5173|9000|5174'
```

---

## D. コード参照

| ファイル | 内容 |
|---|---|
| `app/idgen/base.py` | ALPHABET・定数・`encode_base62` |
| `app/idgen/problem.py` | 演習スタブ（実装対象）|
| `app/idgen/generator.py` | 解答例 `UserIdGenerator` |
| `app/idgen/factory.py` | `ID_STRATEGY` 切り替えロジック |
| `tests/test_idgen_problem.py` | 演習テスト |
| `tests/test_idgen_collision.py` | 衝突の決定的証明 |
| `tests/test_idgen_generator.py` | 解答例のユニットテスト |
| `compose.yaml` | 基本スタック（app/solution/runner/web/docs）|
| `compose.demo.yaml` | デモスタック（app1/2/3/lb）|
