import random
import time

from app.idgen.base import Clock


def _default_clock() -> int:
    return time.time_ns() // 1_000_000


class ProblemIssuer:
    """出題用スタブ。``issue`` を実装してユーザーIDを返す。

    足場（実装済み。``issue`` だけが穴埋め）:
      - ``now_ms``: 現在時刻(ミリ秒)を返す関数。テストでクロックを注入できるよう外出し。
      - ``rng``: 乱数生成器。連番にしない（開始位置のランダム化）に使う。

    要件（詳細は docs/tutorial の各章を参照）:
      - base62（0-9A-Za-z）10文字
      - 発行順に文字列ソート可能
      - 連番にしない
      - 同一のID発行は禁止
    """

    def __init__(
        self,
        *,
        now_ms: Clock | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self._now_ms: Clock = now_ms or _default_clock
        self._rng = rng or random.Random()

    def issue(self) -> str:
        raise NotImplementedError("ここにID発行ロジックを実装してください")
