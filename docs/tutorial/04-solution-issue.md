# 【解答例①】実装の解説

前章で実装した `issue()` の **答え合わせ** をしましょう。<br>
解答例のコードを見ながら、「なぜその組み立てで要件を満たせるのか」を確認します。

## 解答例のコード

```python
def issue(self) -> str:
    ms = self._now_ms() - EPOCH_MS          # ① 経過ミリ秒（時刻成分）

    if ms != self._current_ms:              # ② ミリ秒が変わった
        self._current_ms = ms
        self._seq_base = self._rng.randrange(MAX_SEQUENCE + 1)  # 開始位置をランダムに
        self._counter = 0
    else:                                   # ③ 同じミリ秒内
        self._counter += 1
        if self._counter > MAX_SEQUENCE:    # 4096 を超えたら次のミリ秒へ
            while self._now_ms() - EPOCH_MS == self._current_ms:
                pass
            return self.issue()

    sequence = (self._seq_base + self._counter) & SEQUENCE_MASK
    value = (ms << MS_SHIFT) | sequence     # ④ 1つの整数に
    return encode_base62(value)             # ⑤ base62 で10文字に
```

::: tip 上のコードは要点に絞っています
ここでは要件の核心だけを抜き出しています。実際の解答実装（`app/idgen/generator.py`）には、これに加えて **表現できる範囲を外れた時刻をはじく堅牢化**（範囲チェック）も入っています。要件そのものではないため、上では省略しています。
:::

## なぜ要件を満たすのか

整数 `value` は、次の2つの部分を桁で分けて1つにまとめたものです（`④`）。

| 上位ビット | 下位ビット |
| --- | --- |
| **時刻**（経過ミリ秒） | **連番**（sequence） |

### 発行順にソートできる

- 時刻成分を **いちばん上の桁** に置いています（`④` の `ms << MS_SHIFT`）。
- あとに発行されたIDほど時刻が大きい → 整数として大きい → base62 の文字列としても大きい。
- だから、**並べ替えると発行順** になります。

### 連番にしない

- もし同じミリ秒の連番を毎回 `0, 1, 2, …` から始めると、IDの並びが読めてしまいます。
- そこで、**ミリ秒が変わるたびに開始位置 `seq_base` を乱数で決め**（`②`）、そこから数えます。
- 開始位置が読めないので、単純な通し番号にはなりません。

### 何度呼んでも重複しない

- 同じミリ秒の中では、`counter` を1つずつ増やすので連番部分が必ず変わります（`③`）。
- 連番は最大 4096 個。それを超えたら **次のミリ秒まで待って** から続けます。
- 時刻が違えば上位ビットが違うので、別のミリ秒のIDと重なることもありません。

### base62 で10文字

- 最後に `encode_base62()` で、整数を `0-9A-Za-z` の **固定10文字** に変換します（`⑤`）。

## 動かして確認する

実際に発行してみましょう。前章で `issue()` を実装ずみなら、演習用の `app`（<http://localhost:8000/docs>）が使えます。
まだなら、解答例の `solution`（<http://localhost:8001/docs>）で試せます。

Swagger UI の `POST /users` から、次の内容で実行します。

```json
{ "name": "alice" }
```

`0uLvI2MYQL` のような **10文字のID** が返れば成功です。<br>
何人か続けて登録すると、あとから登録した人ほど **大きいID** になっていることを、`GET /users` の一覧で確認できます。<br>
（ブラウザUI <http://localhost:5173> でも、発行と一覧・妥当性チェックを試せます。）

次の章では、このAPIを **たくさんのアクセスにさらしたら何が起きるか** を考えます。
