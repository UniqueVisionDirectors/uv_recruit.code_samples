# 衝突を観測する

## この章の目的

「**ステージ1（worker_id=0 で全プロセス固定）の実装**は、並列度を上げると衝突を起こす」——
これを、Web UI のジョブ実行で観察し、数学的に説明し、最後にユニットテストで決定的に証明します。

---

## デモスタックの起動

衝突を観察するには、nginx ロードバランサ（lb）と 3 つの app インスタンスからなる**デモスタック**が必要です。

基本スタックを停止してからデモスタックを起動します:

```bash
# 基本スタックを停止（データは保持）
docker compose down

# 基本スタック + デモスタックを同時に起動
docker compose -f compose.yaml -f compose.demo.yaml up --build -d
```

> **注意**: デモスタックの app1/app2/app3 は、デフォルト `ID_STRATEGY=stage1`（worker_id=0 固定）で起動します。

起動確認:

```bash
docker compose -f compose.yaml -f compose.demo.yaml ps
```

`lb`（ポート 8080）、`app1`/`app2`/`app3`、`runner`、`web` がすべて起動していることを確認してください。

---

## Web UI でジョブを投入する

`http://localhost:5173` を開き、ジョブ実行画面に移動してください。

### 並列度 1（衝突しない）

1. **target**: `lb`（nginx 経由で app1/2/3 に振り分け）
2. **n**: 100（100 件成功するまで発行）
3. **concurrency**: `1`（同時リクエスト数 1）
4. 「実行」→ ジョブ詳細を確認

```
conflict_count: 0
```

並列度 1 では同一ミリ秒にリクエストが集中しないため、衝突はほとんど起きません。

### 並列度 100

1. concurrency を `100` に変更して実行
2. ジョブ詳細を確認

`conflict_count` が 0 より大きくなることがあります（環境依存）。

### 並列度 1000

1. concurrency を `1000` に変更して実行
2. ジョブ詳細を確認

> **正直なフレーミング**: 環境（CPU コア数・IO 速度）によって結果は変わります。
> - 3 つの uvicorn プロセスが同一ミリ秒にリクエストを処理するかどうかはタイミング次第です。
> - 並列度 1000 では逆に **トランスポートエラー**（接続タイムアウトなど）が主体になることもあります。
> - `conflict_count` がゼロでも「衝突しない設計になっている」わけではありません。
>
> **衝突の決定的な証明は、次節のユニットテストです。**

---

## なぜ衝突するのか — 鳩の巣原理

ステージ1の `UserIdGenerator(worker_id=0)` のビット構造を振り返ります:

```
value = (ms << 18) | (worker_id << 12) | sequence
                      ~~~~~~~~~~~~~~~
                      worker_id = 0（全プロセス固定）
```

同一ミリ秒（`ms` 同じ）に複数プロセス（all `worker_id=0`）が発行すると:

```
value = (ms << 18) | (0 << 12) | sequence
```

`sequence` は各プロセスが**独立して**乱数ベースで生成します。
同一ミリ秒に 2 つのプロセスが発行する場合、以下の鳩の巣問題が生じます。

### 定量: 誕生日問題

1 ミリ秒内に発行できるシーケンス空間: **4096 通り**（12bit）。

同一ミリ秒に `k` 件リクエストが届いた場合（全プロセス合計）、衝突確率は:

```
P(衝突) ≈ 1 - exp(-k(k-1) / (2 × 4096))
```

| 1ms 当たりリクエスト数 k | 衝突確率（近似）|
|---|---|
| 10 | ≈ 1.2% |
| 50 | ≈ 26% |
| 100 | ≈ 71% |
| 200 | ほぼ 100% |

並列度を上げると **1 ミリ秒内に複数プロセスへ同時にリクエストが届く確率**が高まり、衝突確率が急増します。

---

## 決定的な証明 — ユニットテスト

実環境の「衝突するかどうか」はタイミング依存ですが、ユニットテストでは**同一ミリ秒を強制**して衝突を確実に再現できます。

```bash
docker compose run --rm app uv run pytest tests/test_idgen_collision.py -v
```

テスト内容:

```python
# tests/test_idgen_collision.py（抜粋）

_SAME_MS = lambda: EPOCH_MS + 42  # 全ジェネレータが同一ミリ秒を見る

def test_stage1_naive_collides_across_processes():
    gen_a = UserIdGenerator(0, now_ms=_SAME_MS, rng=random.Random(1))
    gen_b = UserIdGenerator(0, now_ms=_SAME_MS, rng=random.Random(2))
    ids = [gen_a.issue() for _ in range(_PER_GEN)]  # 4096件
    ids += [gen_b.issue() for _ in range(_PER_GEN)]  # さらに4096件
    # worker_id=0 固定のため、シーケンス空間は 4096 通りしかない。
    # 2プロセス合計 8192 件を発行したとき、重複が必ず生じる（鳩の巣原理）
    assert len(set(ids)) < len(ids)  # 衝突が観測される
```

**2 プロセスが同一ミリ秒に合計 8192 件発行した場合、シーケンス空間 4096 通りに収まらないため、重複は必ず生じます（鳩の巣原理）。**

このテストはハードウェアやタイミングに依存せず、常に PASS します。

---

次の章では、worker-id を修正して衝突をゼロにします。
