# 【解答例②】worker-id 設計

> **この章の目的（存在理由）**
> 第2の解。各プロセスに区別子（worker-id）を与え、衝突を構造的に消す。

<!-- SKELETON (Step2): 以下は記載アウトライン。Step3 で本文化する。 -->

## アイデア：プロセスごとに違う worker-id

- ID に worker-id を埋め込めば、同一ミリ秒でもプロセス間で枠が重ならない
- 📊 図: ID のビット内訳（時刻 | worker-id | 連番）

## 解答例（と任意の穴埋め第2段）

- 解答例: `UserIdGenerator(worker_id=WORKER_ID)`（stage2）
- 任意演習: 自分の `issue()` に `WORKER_ID` を組み込む
- ⚠️ worker-id 演習を穴埋め化するか（テスト含む）は **Task#2** で確定

## 再観測：衝突0

- `ID_STRATEGY=stage2` でデモスタック → 並列1000でも `conflict_count = 0`
- 📊 図: stage2 構成（worker-id 付き）

## まとめ

- 1台 → 複数台で何が変わったか、worker-id がなぜ効くか
