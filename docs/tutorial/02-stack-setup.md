# 教材の構成と起動

> **この章の目的（存在理由）**
> 前章の一般論（3層）を、この教材の“動く具体物”に接続し、すぐ手元で触れる状態にする。一般論 → 具体例の橋渡し。

<!-- SKELETON (Step2): 以下は記載アウトライン。Step3 で本文化する。 -->

## 一般論を具体に：この教材の技術

- FE = Vue / BE = FastAPI / DB = PostgreSQL の対応を、前章の3層図に技術名を載せて示す
- 📊 図: 具体版の構成図（前章の図に技術名を載せた版）

## 環境を立ち上げる

- `docker compose up --build -d`（初回は数分かかる旨）
- `docker compose ps` で全サービスの起動確認

## 各サービスのURL

- 表: app(8000 / `/docs`), web(5173), runner(9000 `/healthz`), docs(5174), solution(8001 `/docs`)
- runner の healthz を curl で確認

## 停止・クリーンアップ

- `docker compose down`（データ保持）/ `down -v`（リセット）
