import random
import time

from app.idgen.base import MAX_WORKER_ID, Clock


def _default_clock() -> int:
    return time.time_ns() // 1_000_000


class ProblemIssuer:
    """出題用スタブ。学習者は ``issue`` を実装してユーザーIDを返す。

    インターフェース（足場・実装済み。``issue`` だけが穴埋め）:
      - ``worker_id``: このプロセスの識別子（0..63）。並列時の衝突回避に使う。
      - ``now_ms``: 現在時刻(ミリ秒)を返す関数。テストでクロックを注入できるよう外出し。
      - ``rng``: 乱数生成器。連番回避（同一ミリ秒の開始位置のランダム化）に使う。

    要件（詳細は docs/tutorial の各章を参照）:
      - base62（0-9A-Za-z）10文字
      - 発行順に文字列ソート可能（先頭に時刻成分）
      - 連番回避（同一ミリ秒の開始位置をランダム化）
      - 単一発行器は容量内で一意
      - 並列（worker_id が異なる）でも衝突しない ← ステージ2（worker-id）
      - 表現不能な時刻（ms<0 / ms>MAX_MS）は ValueError
    """

    def __init__(
        self,
        worker_id: int,
        *,
        now_ms: Clock | None = None,
        rng: random.Random | None = None,
    ) -> None:
        if not 0 <= worker_id <= MAX_WORKER_ID:
            raise ValueError(f"worker_id must be in 0..{MAX_WORKER_ID}")
        self._worker_id = worker_id
        self._now_ms: Clock = now_ms or _default_clock
        self._rng = rng or random.Random()

    def issue(self) -> str:
        raise NotImplementedError("ここにID発行ロジックを実装してください")
