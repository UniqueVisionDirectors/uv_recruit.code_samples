import random
import time

from app.idgen.base import (
    EPOCH_MS,
    MAX_MS,
    MAX_SEQUENCE,
    MAX_WORKER_ID,
    MS_SHIFT,
    SEQUENCE_MASK,
    WORKER_SHIFT,
    Clock,
    encode_base62,
)


def _default_clock() -> int:
    return time.time_ns() // 1_000_000


class UserIdGenerator:
    """発行順ソート可能・並列安全な ID ジェネレータ（解答例）。

    worker_id をプロセス毎に distinct にすれば、同一ミリ秒でも
    `(ms, worker_id, sequence)` が一意になり原理的に衝突しない（stage2）。
    全プロセスが worker_id=0 を使うと並列下で構造的に衝突する（stage1）。
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
        self._current_ms = -1
        self._seq_base = 0
        self._counter = 0

    def issue(self) -> str:
        ms = self._now_ms() - EPOCH_MS
        if ms < 0 or ms > MAX_MS:
            raise ValueError("timestamp out of representable range")
        if ms != self._current_ms:
            self._current_ms = ms
            self._seq_base = self._rng.randrange(MAX_SEQUENCE + 1)
            self._counter = 0
        else:
            self._counter += 1
            if self._counter > MAX_SEQUENCE:
                # この ms のシーケンスを使い切った。次の ms までスピンして再採番。
                while self._now_ms() - EPOCH_MS == self._current_ms:
                    pass
                return self.issue()
        sequence = (self._seq_base + self._counter) & SEQUENCE_MASK
        value = (ms << MS_SHIFT) | (self._worker_id << WORKER_SHIFT) | sequence
        return encode_base62(value)
