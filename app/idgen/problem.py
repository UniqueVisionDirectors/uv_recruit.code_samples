import random
import time

from app.idgen.base import MAX_WORKER_ID, Clock


def _default_clock() -> int:
    return time.time_ns() // 1_000_000


class ProblemIssuer:
    """出題用スタブ。学習者は ``issue`` を実装してユーザーIDを返す。

    インターフェース:
      - ``worker_id``: このプロセスの識別子（0..63）。
      - ``now_ms``: 現在時刻(ミリ秒)を返す関数。
      - ``rng``: 乱数生成器。

    要件（詳細は docs/tutorial の各章を参照）:
      - base62（0-9A-Za-z）10文字
      - 発行順に文字列ソート可能
      - 連番回避
      - 同一のID発行は禁止
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
