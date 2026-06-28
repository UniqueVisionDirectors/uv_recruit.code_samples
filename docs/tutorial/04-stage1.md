# ステージ1 — ID 発行ロジックを書く

## 目的

`app/idgen/problem.py` の `ProblemIssuer.issue()` に、ID 発行ロジックを実装します。
テストを通過させることがゴールです。

---

## 要件

`ProblemIssuer.issue()` が返す文字列は以下を満たすこと。

| 要件 | 内容 |
|---|---|
| **文字種** | base62（`0-9A-Za-z`）のみ |
| **長さ** | 10 文字 |
| **発行順ソート可能** | 先頭に時刻成分を持ち、発行順に文字列 `>` が成立すること |
| **純連番を避ける** | 連番（1, 2, 3, …）ではなく、予測困難性を持つこと |
| **ステージ2での非衝突** | 並列化（複数コンテナ）でも衝突しないようにするため、プロセスごとに distinct な worker-id を `WORKER_ID` 環境変数から受け取ること（ヒント）|

---

## ヒント: ID のビット構造

解答例 `UserIdGenerator` は、以下のビット構造を採用しています。

```
[ ms (41 bit) | worker_id (6 bit) | sequence (12 bit) ]
                               ↑ 合計 59 bit → base62 × 10 文字に収まる
```

- `ms` = 現在時刻のミリ秒 − `EPOCH_MS`（2025-01-01T00:00:00Z）
- `worker_id` = プロセス固有の ID（0〜63）
- `sequence` = 同一ミリ秒内の連番（`seq_base` + カウンタ をビットマスク）

**ステージ1ではまず `worker_id=0` で実装**して構いません（全プロセスで同じ値）。
ステージ2で `WORKER_ID` 環境変数を使うよう修正します。

---

## 実装ファイル

```
app/idgen/problem.py     ← ここに実装する
app/idgen/base.py        ← 定数・encode_base62 を利用可能
app/idgen/generator.py   ← 解答例（ネタバレ注意）
```

`base.py` で利用できる定数:

```python
ALPHABET        # "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ..."（62文字）
ID_LENGTH       # 10
SEQUENCE_BITS   # 12
MAX_SEQUENCE    # 4095
WORKER_BITS     # 6
MAX_WORKER_ID   # 63
WORKER_SHIFT    # 12
MS_SHIFT        # 18
EPOCH_MS        # 1735689600000 (2025-01-01T00:00:00Z)

encode_base62(value: int, length: int = ID_LENGTH) -> str
```

---

## テストの実行

実装したらコンテナ内でテストを実行してください:

```bash
docker compose run --rm app uv run pytest tests/test_idgen_problem.py -v
```

テストがすべてパスすれば実装完了です。

その他のテスト（参考）:

```bash
# 衝突テスト（後の章で使う）
docker compose run --rm app uv run pytest tests/test_idgen_collision.py -v

# ジェネレータ単体テスト
docker compose run --rm app uv run pytest tests/test_idgen_generator.py -v
```

---

## Web UI で単発発行を試す

テストが通ったら、ブラウザで `http://localhost:5173` を開いてください。

1. **「1件発行」** ボタンをクリック
2. 発行された ID が表示されることを確認
3. `http://localhost:8000/users` で一覧を確認

---

## 実装後の curl 確認

```bash
curl -s -X POST http://localhost:8000/users \
  -H 'Content-Type: application/json' \
  -d '{"name": "bob"}'
```

```json
{
  "id": "0Cg3T80001",
  "name": "bob",
  "created_at": "2025-06-28T12:35:00.123Z"
}
```

10 文字 base62 の ID が返れば成功です。

---

次の章では、この実装に **並列度を上げると何が起きるか** を観察します。
