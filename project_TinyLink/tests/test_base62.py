from backend.base62 import decode, encode


def test_encodes_zero():
    assert encode(0) == "0"


def test_encodes_125():
    assert encode(125) == "21"


def test_round_trip():
    for n in [1, 62, 125, 100_000, 10_000_000_000]:
        assert decode(encode(n)) == n


def test_decode_invalid_char():
    import pytest

    with pytest.raises(ValueError):
        decode("ab!")


def test_negative_raises():
    import pytest

    with pytest.raises(ValueError):
        encode(-1)
