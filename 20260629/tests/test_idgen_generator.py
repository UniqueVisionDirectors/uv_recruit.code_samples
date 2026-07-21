import random
import re

import pytest

from app.idgen.base import EPOCH_MS, MAX_SEQUENCE, MAX_WORKER_ID, decode_base62
from app.idgen.generator import UserIdGenerator

ID_RE = re.compile(r"^[0-9A-Za-z]{10}$")


def _fixed_clock(ms_since_epoch: int):
    return lambda: EPOCH_MS + ms_since_epoch


def test_issue_matches_format():
    gen = UserIdGenerator(0, now_ms=_fixed_clock(1000), rng=random.Random(0))
    assert ID_RE.match(gen.issue())


def test_single_generator_unique_within_one_ms():
    gen = UserIdGenerator(0, now_ms=_fixed_clock(7), rng=random.Random(0))
    ids = [gen.issue() for _ in range(MAX_SEQUENCE + 1)]  # 4096 件
    assert len(set(ids)) == MAX_SEQUENCE + 1


def test_ids_sortable_by_issue_order():
    clock = {"ms": 0}
    gen = UserIdGenerator(
        0, now_ms=lambda: EPOCH_MS + clock["ms"], rng=random.Random(0)
    )
    first = gen.issue()
    clock["ms"] = 5
    second = gen.issue()
    assert first < second  # 後発のほうが文字列順で大きい


def test_worker_id_occupies_worker_bits():
    gen = UserIdGenerator(5, now_ms=_fixed_clock(3), rng=random.Random(0))
    value = decode_base62(gen.issue())
    assert (value >> 12) & MAX_WORKER_ID == 5


def test_rejects_out_of_range_worker_id():
    with pytest.raises(ValueError):
        UserIdGenerator(MAX_WORKER_ID + 1)


def test_rejects_timestamp_before_epoch():
    gen = UserIdGenerator(0, now_ms=lambda: EPOCH_MS - 1, rng=random.Random(0))
    with pytest.raises(ValueError):
        gen.issue()
