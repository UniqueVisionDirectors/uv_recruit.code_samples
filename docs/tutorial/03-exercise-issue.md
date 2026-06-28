# 【問題①】ID発行を実装する

前章で確認した要件を満たす **ID発行ロジックを、あなた自身の手で実装** します。<br>
これがこのサンプル最初の問題です。

## 問題

`app/idgen/problem.py` の `ProblemIssuer.issue()` を実装し、呼び出すたびに次の条件を満たすIDを返してください。

- base62（`0-9A-Za-z`）の **10文字**
- **発行順にソートできる**（あとに発行したIDほど、文字列比較で大きい）
- **連番にしない**（単純な通し番号にしない）
- 何度呼んでも **重複しない**

## 用意されているもの

`issue()` の中身だけが空いています。コンストラクタでは、実装に使える道具が渡されます。

| 道具 | 説明 |
| --- | --- |
| `self._now_ms()` | 現在時刻（ミリ秒）を返す |
| `self._rng` | 乱数生成器 |
| `self._worker_id` | プロセスの識別子 |

また `app/idgen/base.py` には、整数を base62 の10文字に変換する `encode_base62()` などの部品があります。

## まず動かしてみる

実装する前に、答え合わせ用のテストを走らせてみましょう。

```bash
docker compose run --rm app uv run pytest -m exercise -v
```

まだ `issue()` が空なので、すべて **失敗** します。

```sh
tests/test_idgen_problem.py::test_tc1_charset_and_length FAILED
tests/test_idgen_problem.py::test_tc2_unique_within_one_ms_at_capacity FAILED
tests/test_idgen_problem.py::test_tc3_sortable_by_issue_order FAILED
tests/test_idgen_problem.py::test_tc4_randomized_start_not_sequential FAILED
```

## 実装して、Greenにする

要件を満たすように `issue()` を実装し、もう一度テストを走らせてください。

```bash
docker compose run --rm app uv run pytest -m exercise -v
```

4つすべてが **成功（緑）** になれば、問題①はクリアです。

実装できたら、次の章で **解答例** と照らし合わせ、なぜその実装で要件を満たせるのかを確認しましょう。
