# API に触れる

## Swagger UI で試してみる

ブラウザで `http://localhost:8000/docs` を開いてください。
FastAPI が自動生成した Swagger UI です。

---

## GET /users — ユーザー一覧

### Swagger で試す

1. `GET /users` をクリックして展開
2. **「Try it out」** をクリック
3. `limit`（取得件数）と `offset`（開始位置）を入力（空欄でも可）
4. **「Execute」** をクリック

レスポンス例（まだ登録なし）:

```json
[]
```

### curl で試す

```bash
curl http://localhost:8000/users
```

`limit` と `offset` を指定する場合:

```bash
curl "http://localhost:8000/users?limit=10&offset=0"
```

---

## POST /users — ユーザー登録

### 注意: 演習用 app（ポート 8000）について

`http://localhost:8000` の `app` は、デフォルト戦略 `ID_STRATEGY=problem` で起動しています。
`ProblemIssuer.issue()` はまだ未実装なので、`POST /users` を呼ぶと `500 Internal Server Error` が返ります。

**解答例 API（ポート 8001）** を使えば、今すぐ動作を確認できます:

```bash
curl -s -X POST http://localhost:8001/users \
  -H 'Content-Type: application/json' \
  -d '{"name": "alice"}'
```

レスポンス例:

```json
{
  "id": "0Cg3T80000",
  "name": "alice",
  "created_at": "2025-06-28T12:34:56.789Z"
}
```

`id` が **10 文字の base62** 文字列になっています。

### 章 04 を終えたら port 8000 で試す

[04 章](/04-stage1) で `ProblemIssuer.issue()` を実装したあとは、ポート 8000 でも同じコマンドが使えます:

```bash
curl -s -X POST http://localhost:8000/users \
  -H 'Content-Type: application/json' \
  -d '{"name": "alice"}'
```

---

## GET /users/{id} — ユーザー取得

```bash
# {id} を上で得た ID に置き換える
curl http://localhost:8000/users/0Cg3T80000
```

レスポンス例:

```json
{
  "id": "0Cg3T80000",
  "name": "alice",
  "created_at": "2025-06-28T12:34:56.789Z"
}
```

---

## Swagger UI での POST の試し方

1. `POST /users` をクリックして展開
2. **「Try it out」** をクリック
3. Request body に以下を入力:

```json
{"name": "alice"}
```

4. **「Execute」** をクリック

> **Tip**: 解答例 API（`http://localhost:8001/docs`）の Swagger でも試せます。

---

## 409 Conflict — ID 衝突

`POST /users` が同一 ID を持つユーザーの登録を試みると、409 が返ります。

```json
{
  "detail": "id already exists"
}
```

**この 409 が「ID 衝突」です**。ステージ1で並列度を上げると、この 409 が発生することを確認します（[05 章](/05-collision)）。
