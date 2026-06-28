"""穴埋め演習（ID発行）の受け入れテスト — テスト設計を内包する。

このファイルは、学習者が ``app/idgen/problem.py`` の ``ProblemIssuer.issue`` を
実装する演習の自動採点テストである。既定の pytest ゲートからは ``exercise``
マーカーで除外され（出荷時は未解答＝この演習群は赤）、学習者は
``pytest -m exercise`` で明示的に実行して red→green を体験する。

================================================================================
テスト設計
================================================================================

■ 1. ID要件の整理（検証可能な定義）
  R1 文字種     : 出力は [0-9A-Za-z] のみ
  R2 長さ       : 厳密に10文字
  R3 ソート可   : ミリ秒が進めば後発IDは文字列比較で大きい（ms 粒度で単調）。
                  同一ミリ秒内の順序は R4 によりランダムで不問。
  R4 連番回避   : 各ミリ秒の開始位置がランダム化され、開始が固定でない
  R5 単一一意性 : 1発行器は容量内（同一ミリ秒 4096件）で重複なし
  R6 並列一意性 : worker_id が異なる発行器は同一ミリ秒でも衝突しない
  R7 worker割当 : worker_id が worker ビット領域(6bit, シフト12)に正しく入る
  V1 worker範囲 : worker_id は 0..63 のみ、範囲外は ValueError（足場で提供）
  V2 時刻範囲   : ms<0 または ms>MAX_MS は ValueError（issue 内で検証＝穴埋め）

■ 2. デシジョンテーブル（2つのIDが衝突するか）
  同一ms | 同一worker | 同一seq | 衝突
  -------+-----------+--------+------
    Y    |    Y      |   Y    | する（TC5 の否定対象。積極観測は collision テスト）
    Y    |    Y      |   N    | しない（R5＝TC2）
    Y    |    N      |   -    | しない（worker ビット差＝R6/R7＝TC5/TC6）
    N    |    -      |   -    | しない（ms ビット差＝R3＝TC3）
  → 同一ms・異worker が「衝突しない」ことが ch08 の肝（TC5）。

■ 3. 同値分割・境界値分析
  worker_id     : 有効[0..63] / 境界 0,63 / 中間 37 / 無効 -1,64(→ValueError)
  sequence 容量 : 同一ミリ秒で 4096(=MAX_SEQUENCE+1, 上限境界) は全 distinct
  timestamp     : 有効[EPOCH..EPOCH+MAX_MS] / 無効 EPOCH-1, EPOCH+MAX_MS+1(→ValueError)
  長さ          : 9 / 10 / 11 → 10 のみ可
  文字種        : base62 集合の 内 / 外

■ 4. テストケース（要件・技法 → TC）
  TC1 R1+R2 : 多数発行が全て ^[0-9A-Za-z]{10}$            （EP: 文字種/長さ）
  TC2 R5    : 同一ms・単一発行器で 4096件 全 distinct      （BVA: 容量上限）
  TC3 R3    : 複数 ms で発行順 == ソート順                （ms 粒度の単調性）
  TC4 R4    : rng シード違いで先頭IDが十分ばらつく         （ランダム化の有無・強度）
  TC5 R6    : worker 0 と 1 が同一msで 8192件 全 distinct  （デシジョンテーブルの肝）
  TC6 R7    : worker_id∈{0,37,63} が worker ビットに一致   （BVA境界+混合ビット）
  V1  V1    : worker_id=-1,64 で ValueError               （BVA: worker 無効境界・足場）
  V2  V2    : ms<0 / ms>MAX_MS で ValueError              （BVA: 時刻無効境界・穴埋め）

■ 5. 偽陽性・偽陰性を出さない根拠
  偽陰性なし（正解実装で全 green）:
    各 TC は解答例 UserIdGenerator と同じ構造で必ず満たされる。乱数依存の TC4 は
    16シードで決定的（フレーク無し）。TC2/TC5 の容量・鳩の巣は決定的。
  偽陽性なし（誤実装で該当 TC が赤）:
    TC1=長さ/文字種, TC3=時刻不使用, TC4=開始固定(連番),
    TC5=worker 無視(鳩の巣で必ず衝突), TC6=worker ビット位置/逆順ミス,
    V2=時刻範囲チェック欠落 を各々検出。
  ※ 上記は実装後にミューテーションで実機確認する（report 参照）。

■ 6. 実装上の注意
  - クロックは ``_spin_safe_clock`` を使う：通常は固定 ms を返すが、実装が容量超過時
    のスピンに入った場合（過剰な now_ms 呼び出し）に ms を前進させ、固定クロック×
    丁度4096 で off-by-one な実装が無限ループ（CIハング）するのを防ぐ。正常実装は
    閾値未満なので ms は固定のまま＝容量・衝突の検証は成立する。
  - TC1–TC6・V2 は ``issue()`` を呼ぶため未実装スタブでは赤。V1 は ``__init__``（足場）
    のみを見るため未実装でも緑（既定ゲートに置く）。
"""

import random
import re
from collections.abc import Callable

import pytest

from app.idgen.base import (
    EPOCH_MS,
    MAX_MS,
    MAX_SEQUENCE,
    MAX_WORKER_ID,
    Clock,
    decode_base62,
)
from app.idgen.problem import ProblemIssuer

ID_RE = re.compile(r"[0-9A-Za-z]{10}")


def _fixed_clock(ms_since_epoch: int) -> Clock:
    """常に EPOCH+ms を返すクロック（同一ミリ秒を強制）。"""
    return lambda: EPOCH_MS + ms_since_epoch


def _spin_safe_clock(ms_since_epoch: int, *, spin_limit: int = 1_000_000) -> Clock:
    """通常は固定 ms を返すが、過剰に呼ばれたら(=実装がスピンしたら)前進する。

    正常実装は1発行あたり数回しか now_ms を呼ばないため閾値に達せず固定 ms のまま。
    容量超過時に固定クロックでスピンする off-by-one 実装の無限ループ（CIハング）を防ぐ。
    """
    state = {"ms": ms_since_epoch, "calls": 0}

    def clock() -> int:
        state["calls"] += 1
        if state["calls"] > spin_limit:
            state["ms"] += 1
            state["calls"] = 0
        return EPOCH_MS + state["ms"]

    return clock


# ── ch04: 基本要件 R1–R5（issue() の穴埋め＝未実装では赤）─────────────────


@pytest.mark.exercise
def test_tc1_charset_and_length() -> None:
    """TC1 (R1+R2): 発行した全IDが base62・10文字。"""
    issuer = ProblemIssuer(0, now_ms=_fixed_clock(1000), rng=random.Random(0))
    ids = [issuer.issue() for _ in range(100)]
    assert all(ID_RE.fullmatch(i) for i in ids)


@pytest.mark.exercise
def test_tc2_unique_within_one_ms_at_capacity() -> None:
    """TC2 (R5, BVA 容量上限): 同一ミリ秒・単一発行器で 4096件 全 distinct。"""
    issuer = ProblemIssuer(0, now_ms=_spin_safe_clock(7), rng=random.Random(0))
    ids = [issuer.issue() for _ in range(MAX_SEQUENCE + 1)]
    assert len(set(ids)) == MAX_SEQUENCE + 1


@pytest.mark.exercise
def test_tc3_sortable_by_issue_order() -> None:
    """TC3 (R3): ミリ秒を進めて発行 → 発行順 == 文字列ソート順。"""
    clock: dict[str, int] = {"ms": 0}

    def now_ms() -> int:
        return EPOCH_MS + clock["ms"]

    issuer = ProblemIssuer(0, now_ms=now_ms, rng=random.Random(0))
    ids: list[str] = []
    for ms in range(1, 51):
        clock["ms"] = ms
        ids.append(issuer.issue())
    assert ids == sorted(ids)


@pytest.mark.exercise
def test_tc4_randomized_start_not_sequential() -> None:
    """TC4 (R4): rng シード違いで先頭IDが十分ばらつく（開始のランダム化）。"""
    first_ids = {
        ProblemIssuer(0, now_ms=_fixed_clock(123), rng=random.Random(seed)).issue()
        for seed in range(16)
    }
    # 固定開始(連番)実装は全て同一(=1種)。ランダム化されていれば大きくばらつく。
    assert len(first_ids) >= 8


# ── ch08: 並列の一意性 R6/R7（worker-id の穴埋め＝未対応では赤）──────────────


@pytest.mark.exercise
def test_tc5_distinct_workers_never_collide_same_ms() -> None:
    """TC5 (R6, デシジョンテーブルの肝): worker 0 と 1 が同一msで全 distinct。"""
    a = ProblemIssuer(0, now_ms=_spin_safe_clock(42), rng=random.Random(1))
    b = ProblemIssuer(1, now_ms=_spin_safe_clock(42), rng=random.Random(1))
    ids = [a.issue() for _ in range(MAX_SEQUENCE + 1)]
    ids += [b.issue() for _ in range(MAX_SEQUENCE + 1)]
    assert len(set(ids)) == 2 * (MAX_SEQUENCE + 1)


@pytest.mark.exercise
@pytest.mark.parametrize("worker_id", [0, 37, MAX_WORKER_ID])
def test_tc6_worker_id_in_worker_bits(worker_id: int) -> None:
    """TC6 (R7, BVA境界+混合ビット): worker_id が worker ビット領域に一致。

    境界 0/63 に加え、混合ビット 37(0b100101) を入れることで、worker ビットの
    逆順・並べ替え・隣接領域への漏れを検出する（63 のみだと逆順でも 63 で素通り）。
    """
    issuer = ProblemIssuer(worker_id, now_ms=_fixed_clock(3), rng=random.Random(0))
    value = decode_base62(issuer.issue())
    assert (value >> 12) & MAX_WORKER_ID == worker_id


# ── 足場/時刻の妥当性 V1・V2（境界値分析）────────────────────────────────────


@pytest.mark.parametrize("bad_worker_id", [-1, MAX_WORKER_ID + 1])
def test_v1_rejects_out_of_range_worker_id(bad_worker_id: int) -> None:
    """V1 (BVA 無効境界・足場): worker_id 範囲外は ValueError（既定ゲート＝常緑）。"""
    with pytest.raises(ValueError):
        ProblemIssuer(bad_worker_id)


@pytest.mark.exercise
@pytest.mark.parametrize(
    "bad_clock",
    [
        pytest.param(lambda: EPOCH_MS - 1, id="before-epoch"),
        pytest.param(lambda: EPOCH_MS + MAX_MS + 1, id="after-max-ms"),
    ],
)
def test_v2_rejects_out_of_range_timestamp(bad_clock: Callable[[], int]) -> None:
    """V2 (BVA 無効境界・穴埋め): 表現不能な時刻は ValueError（issue 内で検証）。"""
    issuer = ProblemIssuer(0, now_ms=bad_clock, rng=random.Random(0))
    with pytest.raises(ValueError):
        issuer.issue()
