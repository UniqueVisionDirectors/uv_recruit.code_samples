# 環境を立ち上げる

## 前提

- Docker / Docker Compose がインストールされていること
- リポジトリをクローン済みであること

---

## 基本スタックの起動

```bash
docker compose up --build -d
```

初回はイメージのビルドがあるため数分かかります。

起動確認:

```bash
docker compose ps
```

全サービスが `running` または `healthy` になったら準備完了です。

---

## 各サービスの URL

| サービス | URL | 備考 |
|---|---|---|
| app (演習用 API) | `http://localhost:8000` | デフォルト戦略 `problem`（未実装）|
| solution (解答例 API) | `http://localhost:8001` | `stage2` 戦略で動作確認済み |
| Swagger UI | `http://localhost:8000/docs` | API ドキュメント＋実行ツール |
| OpenAPI JSON | `http://localhost:8000/openapi.json` | スキーマ定義 |
| web (Vue フロント) | `http://localhost:5173` | ジョブ投入・ID 一覧 |
| runner (Rust ランナー) | `http://localhost:9000` | 負荷ランナー API |
| docs (このサイト) | `http://localhost:5174` | チュートリアル |

---

## 動作確認

ブラウザで各 URL を開いてください。

**Swagger UI** (`http://localhost:8000/docs`) が開けば app は正常起動しています。

**ヘルスチェック** (runner):

```bash
curl -s http://localhost:9000/healthz
```

```json
{"status":"ok"}
```

**web フロントエンド** (`http://localhost:5173`) でページが表示されれば web は正常です。

---

## 停止・クリーンアップ

```bash
# 停止（データは保持）
docker compose down

# データも含めてリセット
docker compose down -v
```

---

## デモスタック（後の章で使用）

[05 章（衝突を観測）](/05-collision) では、nginx LB と複数 app インスタンスを使う「デモスタック」を追加で起動します。
今は基本スタックのみで先に進んでください。
