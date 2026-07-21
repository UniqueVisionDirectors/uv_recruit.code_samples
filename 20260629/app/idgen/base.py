from collections.abc import Callable
from typing import Protocol

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
_BASE = len(ALPHABET)  # 62
_INDEX = {ch: i for i, ch in enumerate(ALPHABET)}

ID_LENGTH = 10

SEQUENCE_BITS = 12
MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1  # 4095
SEQUENCE_MASK = MAX_SEQUENCE

WORKER_BITS = 6
MAX_WORKER_ID = (1 << WORKER_BITS) - 1  # 63

WORKER_SHIFT = SEQUENCE_BITS  # 12
MS_SHIFT = WORKER_BITS + SEQUENCE_BITS  # 18

EPOCH_MS = 1735689600000  # 2025-01-01T00:00:00Z
MAX_MS = (1 << 41) - 1

_MAX_VALUE = _BASE**ID_LENGTH - 1

Clock = Callable[[], int]


def encode_base62(value: int, length: int = ID_LENGTH) -> str:
    if value < 0:
        raise ValueError("value must be non-negative")
    if value > _MAX_VALUE:
        raise ValueError(f"value too large for {length} base62 chars")
    chars = []
    for _ in range(length):
        value, rem = divmod(value, _BASE)
        chars.append(ALPHABET[rem])
    return "".join(reversed(chars))


def decode_base62(text: str) -> int:
    value = 0
    for ch in text:
        value = value * _BASE + _INDEX[ch]
    return value


class IdIssuer(Protocol):
    def issue(self) -> str: ...
