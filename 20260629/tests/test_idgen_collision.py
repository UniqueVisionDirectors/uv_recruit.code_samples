import random

from app.idgen.base import EPOCH_MS, MAX_SEQUENCE
from app.idgen.generator import UserIdGenerator

_SAME_MS = lambda: EPOCH_MS + 42  # 全ジェネレータが同一ミリ秒を見る  # noqa: E731
_PER_GEN = MAX_SEQUENCE + 1  # 4096


def test_stage1_naive_collides_across_processes():
    # worker-id を持たない素朴解＝全プロセス worker_id=0。
    gen_a = UserIdGenerator(0, now_ms=_SAME_MS, rng=random.Random(1))
    gen_b = UserIdGenerator(0, now_ms=_SAME_MS, rng=random.Random(2))
    ids = [gen_a.issue() for _ in range(_PER_GEN)]
    ids += [gen_b.issue() for _ in range(_PER_GEN)]
    # 8192 件発行したが distinct 値は最大 4096 → 必ず重複する。
    assert len(ids) == 2 * _PER_GEN
    assert len(set(ids)) <= _PER_GEN
    assert len(set(ids)) < len(ids)  # 衝突が観測される


def test_stage2_distinct_worker_ids_never_collide():
    # 修正：プロセス毎に distinct な worker_id を付与。
    gen_a = UserIdGenerator(0, now_ms=_SAME_MS, rng=random.Random(1))
    gen_b = UserIdGenerator(1, now_ms=_SAME_MS, rng=random.Random(1))
    ids = [gen_a.issue() for _ in range(_PER_GEN)]
    ids += [gen_b.issue() for _ in range(_PER_GEN)]
    # worker ビットが異なるため全 8192 件が distinct。
    assert len(set(ids)) == 2 * _PER_GEN
