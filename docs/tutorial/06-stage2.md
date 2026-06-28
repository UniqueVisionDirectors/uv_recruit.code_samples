# ステージ2 — worker-id で直す

## 問題の根本原因

ステージ1の衝突は、**全プロセスが `worker_id=0` を使っていた**ことが原因です。

```
# ステージ1（素朴解）
value = (ms << 18) | (0 << 12) | sequence
                      ↑ 全プロセス同じ
```

プロセスごとに **distinct な `worker_id`** を付与すれば、同一ミリ秒でも `value` が異なります:

```
# ステージ2（修正）
Process 1: value = (ms << 18) | (1 << 12) | sequence
Process 2: value = (ms << 18) | (2 << 12) | sequence
Process 3: value = (ms << 18) | (3 << 12) | sequence
                                ↑ プロセスごとに異なる → 衝突しない
```

---

## ProblemIssuer を修正する

`app/idgen/problem.py` の `issue()` を修正し、`WORKER_ID` 環境変数からプロセス固有の worker-id を受け取るようにしてください。

修正のヒント:

```python
import os
worker_id = int(os.environ.get("WORKER_ID", "0"))
```

> **ヒント**: 解答例 `app/idgen/factory.py` の `stage2` 分岐と `app/core/config.py` の `Settings` を参照してください。

---

## テストで確認

```bash
docker compose run --rm app uv run pytest tests/test_idgen_collision.py -v
```

`test_stage2_distinct_worker_ids_never_collide` が PASS することを確認します:

```python
def test_stage2_distinct_worker_ids_never_collide():
    gen_a = UserIdGenerator(0, now_ms=_SAME_MS, rng=random.Random(1))
    gen_b = UserIdGenerator(1, now_ms=_SAME_MS, rng=random.Random(1))
    ids = [gen_a.issue() for _ in range(_PER_GEN)]   # worker_id=0 で 4096件
    ids += [gen_b.issue() for _ in range(_PER_GEN)]  # worker_id=1 で 4096件
    # worker ビットが異なるため全 8192 件が distinct
    assert len(set(ids)) == 2 * _PER_GEN
```

---

## デモスタックで再観測

デモスタックは `WORKER_ID=1/2/3` を app1/2/3 に設定しています。
`ID_STRATEGY` を `stage2` に変えて起動し直してください:

```bash
docker compose -f compose.yaml -f compose.demo.yaml down

ID_STRATEGY=stage2 docker compose -f compose.yaml -f compose.demo.yaml up -d
```

`http://localhost:5173` のジョブ実行画面で、concurrency=1000 でジョブを実行します:

1. **target**: `lb`
2. **n**: 1000
3. **concurrency**: `1000`
4. 「実行」→ ジョブ詳細を確認

```
conflict_count: 0
```

**`conflict_count` が 0 になっていれば、ステージ2 の実装が正しく機能しています。**

---

## 解答例 API との対比

`http://localhost:8001`（`solution` サービス）は初めから `stage2` 戦略で動作しています。

```bash
# solution API の Swagger
open http://localhost:8001/docs

# POST でユーザーを作成（解答例 API）
curl -s -X POST http://localhost:8001/users \
  -H 'Content-Type: application/json' \
  -d '{"name": "charlie"}'
```

自分の実装（`app` サービス）と解答例（`solution` サービス）を比較してみてください。
両者が同じ形式の 10 文字 base62 ID を返せば実装完了です。

---

## まとめ

| ステージ | worker_id | 衝突 |
|---|---|---|
| stage1（問題）| 全プロセス = 0 | 並列下で発生（確率的）|
| stage2（解決）| プロセスごとに distinct（1/2/3）| 構造的に発生しない |

**worker_id ビット（6bit）の役割**: 同一ミリ秒・同一シーケンス値でも、プロセスを識別するビットが異なるため `value` が一意になる。
これにより、最大 **64 プロセス × 4096 シーケンス × n ミリ秒** のスケールで衝突なしに ID を発行できます。

付録でビット構造の全体像を確認してください → [07 付録](/07-appendix)
