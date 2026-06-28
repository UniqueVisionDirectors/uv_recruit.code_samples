import pytest

from app.idgen.base import (
    ID_LENGTH,
    decode_base62,
    encode_base62,
)


def test_encode_is_fixed_length_and_charset():
    s = encode_base62(0)
    assert s == "0000000000"
    assert len(s) == ID_LENGTH


def test_encode_decode_roundtrip():
    for v in [0, 1, 61, 62, 12345, 62**10 - 1]:
        assert decode_base62(encode_base62(v)) == v


def test_lexicographic_order_matches_value_order():
    smaller = encode_base62(1000)
    larger = encode_base62(2000)
    assert smaller < larger  # 素朴な文字列比較で値順になる


def test_encode_rejects_too_large_value():
    with pytest.raises(ValueError):
        encode_base62(62**10)


def test_encode_rejects_negative_value():
    with pytest.raises(ValueError):
        encode_base62(-1)
