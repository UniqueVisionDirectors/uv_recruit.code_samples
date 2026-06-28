# 付録

> **この章の目的（存在理由）**
> 本筋を追い終えた読者が、さらに深掘りするための受け皿。

<!-- SKELETON (Step2): 以下は記載アウトライン。Step3 で本文化する。 -->

## IDのビット構造の詳細

- 41bit 時刻 | 6bit worker-id | 12bit 連番、EPOCH、base62 エンコード
- 📊 図: ビット構造

## 設計判断

- なぜ DB の一意制約に頼らないのか
- なぜ worker-id は明示設定（`WORKER_ID`）なのか

## トラブルシュート

- ポート競合、`problem` 戦略で POST が `NotImplementedError` になる、等
