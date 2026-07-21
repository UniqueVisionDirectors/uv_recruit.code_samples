import random
import time

from app.idgen.base import MAX_WORKER_ID, Clock


def _default_clock() -> int:
    return time.time_ns() // 1_000_000


class ProblemIssuer:
    """出題用スタブ。``issue`` を実装してユーザーIDを返す。

    コンストラクタで渡される道具:
      - ``worker_id``: このプロセスの識別子（0..63）。
      - ``now_ms``: 現在時刻(ミリ秒)を返す関数。テストでクロックを注入できるよう外出し。
      - ``rng``: 乱数生成器。

    要件の詳細は docs/tutorial の各章を参照。
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
