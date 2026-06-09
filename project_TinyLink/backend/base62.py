"""Base62 encode/decode for short codes.

DB hands us monotonic integer ids (1, 2, 3, ...). We turn each id into a
compact string using 62 symbols (0-9, a-z, A-Z). 6 chars = 56.8B possible
codes -- enough for any hobby project.
"""

import string

ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase
BASE = len(ALPHABET)
_INDEX = {ch: i for i, ch in enumerate(ALPHABET)}


def encode(n: int) -> str:
    if n < 0:
        raise ValueError("base62 only encodes non-negative integers")
    if n == 0:
        return ALPHABET[0]
    out = []
    while n > 0:
        n, r = divmod(n, BASE)
        out.append(ALPHABET[r])
    return "".join(reversed(out))


def decode(s: str) -> int:
    n = 0
    for ch in s:
        if ch not in _INDEX:
            raise ValueError(f"invalid base62 character: {ch!r}")
        n = n * BASE + _INDEX[ch]
    return n
