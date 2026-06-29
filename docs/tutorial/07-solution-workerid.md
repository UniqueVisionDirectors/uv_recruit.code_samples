# 【解答例②】worker-id 設計

問題②は「3台が互いを知らないまま、それでも重複しないIDを作るには？」でした。<br>
答えは、**各台に「自分は何番のサーバーか」という区別子を持たせる** ことです。これを **worker-id** と呼びます。

## アイデア：番号空間を台ごとに分ける

これまで、IDは「**時刻 ＋ 連番**」で作っていました。<br>
ここに、各台に固有の **worker-id** を挟み込みます。

| 上位ビット | 中位ビット | 下位ビット |
| --- | --- | --- |
| 時刻 | **worker-id** | 連番 |

- app 1 は worker-id = 1、app 2 は = 2、app 3 は = 3 …というように、**台ごとに違う番号** を割り当てます。
- すると、たとえ **同じミリ秒・同じ連番** でも、**worker-id が違えば必ず別のID** になります。
- 前章の「偶然の重なり」が起きる余地そのものが、**台ごとに分かれて消える** のです。

## 自分の実装に worker-id を足す

ステージ1で作った `ProblemIssuer` を拡張しましょう。<br>
実は、コンストラクタには最初から **`self._worker_id`**（このプロセスの番号）が用意されています。<br>
あとは、これを `issue()` の中で **IDに埋め込む** だけです。

`value` を組み立てている行に、worker-id を1つ挟みます（`WORKER_SHIFT` は `app/idgen/base.py` にあります）。

```python
# 変更前
value = (ms << MS_SHIFT) | sequence

# 変更後
value = (ms << MS_SHIFT) | (self._worker_id << WORKER_SHIFT) | sequence
```

できたら、**あなたの実装** のステージ2テストを走らせます。

```bash
docker compose run --rm app uv run pytest -m exercise2 -v
```

すべて **緑** になれば、あなたの `ProblemIssuer` が worker-id で衝突しなくなったことの確認は完了です。問題②はクリアです。

## 原理そのものを決定的に確かめる

前章の最後では、素朴解（ステージ1）が **必ず衝突する** ことを決定的に確かめました（`test_stage1_naive_collides_across_processes`）。<br>
ここでは、その対になる証明 ―― **worker-id を入れた解答（ステージ2）なら、同じ条件でも衝突が 0 になる** ことを見ます。

```bash
docker compose run --rm app uv run pytest tests/test_idgen_collision.py -v
```

2つのテストが、同じミリ秒に **8192件**（＝枠 4096 の2倍）を発行して対比します。

- `test_stage1_naive_collides_across_processes`（**worker-id なし**）：番号は 4096通りしかないので、**鳩の巣原理により必ず衝突** します。
- `test_stage2_distinct_worker_ids_never_collide`（**worker-id あり**）：台ごとに番号空間が分かれるため、8192件すべてが別のIDになり、**衝突は 0** です。

::: tip これは解答例（参照解）に対する「原理の証明」です
このテストは、**解答例の実装** を相手に「素朴解は必ず衝突／worker-id 版は衝突 0」という **原理そのもの** を決定的に示すものです。<br>
**あなたの実装の採点ではありません**（採点は上の `-m exercise2` で完了済み）。そのため、あなたが何を書いていても **常に緑** になります。
:::

## 修正版を3台で再観測する

実機でも確かめましょう。worker-id を効かせた構成（`stage2`）で起動し直します。

```bash
ID_STRATEGY=stage2 docker compose -f compose.yaml -f compose.demo.yaml up -d --build db app app1 app2 app3 lb runner web
```

web（<http://localhost:5173>）から、前章と同じく **target=`lb（3台・LB経由）`・並列度 1000** でジョブを起動してみてください。<br>
前章では衝突が現れた3台でも、今度は `conflict_count` が **0** のまま完了するはずです。

## まとめ

- 1台のときは、自分の `counter` を覚えていれば重複を避けられた。
- 複数台になると、互いを知らない台どうしが **同じ番号空間** を取り合い、**確率的に衝突** した。
- **worker-id** で台ごとに番号空間を分けることで、衝突の余地そのものをなくせた。

おつかれさまでした。<br>
これで、単一サーバーから水平スケールまで、**重複しないID発行** のひと通りを体験しました。
