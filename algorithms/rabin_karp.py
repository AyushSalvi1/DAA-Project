"""Rabin-Karp string matching (rolling hash) - implemented from scratch.

DAA facts
---------
Rabin-Karp hashes the pattern once, then slides a **window** of size m
across the text recomputing each window hash in O(1) with::

    H(i+1) = (H(i) - text[i] * B^(m-1)) * B + text[i+m]      (mod p)

so the pre-filtering pass is O(n).  When a window hash equals the pattern
hash we must still verify with a real character comparison, because hashing
is many-to-one -> **false positives / hash collisions** are expected.

Practical cost: O(n + m) on average, but O(n * m) worst case (every
window hash collides).  Its selling point is *multiple pattern search*:
compute all pattern hashes once, then one pass over the text.

Implemented by hand - no ``hash()`` slicing tricks on the text.
"""

from __future__ import annotations

import time

PRIME = 1_000_003
BASE = 31


def _hash(text: str, base: int = BASE, mod: int = PRIME) -> int:
    """Polynomial rolling hash of a whole string, O(len(text))."""
    h = 0
    for char in text:
        h = (h * base + ord(char)) % mod
    return h


def build_rolling_table(text: str, m: int, base: int = BASE,
                        mod: int = PRIME) -> list[int]:
    """All window hashes H(i) for i in [0, len(text) - m].

    Precomputing the table turns the search into a pure O(n) scan, which is
    what we use when matching a phrase against many documents.
    """
    n = len(text)
    if m == 0 or m > n:
        return []
    base_m = pow(base, m - 1, mod)
    table = [0] * (n - m + 1)
    current = _hash(text[:m], base, mod)
    table[0] = current
    for i in range(1, n - m + 1):
        current = ((current - ord(text[i - 1]) * base_m) * base
                   + ord(text[i + m - 1])) % mod
        table[i] = current
    return table


def rabin_karp(text: str, pattern: str, base: int = BASE,
               mod: int = PRIME, trace: bool = True) -> dict:
    """Slide-and-compare matcher returning all match positions.

    ``trace=False`` skips the per-window step log (the search pipeline only
    needs the counts).
    """
    n, m = len(text), len(pattern)
    if m == 0:
        return {"algorithm": "Rabin-Karp", "matches": [], "match_count": 0,
                "hash_comparisons": 0, "char_comparisons": 0, "collisions": 0,
                "time_ms": 0.0, "steps": [], "pattern_hash": 0,
                "details": {"note": "Empty pattern - nothing to search for."}}
    if m > n:
        return {"algorithm": "Rabin-Karp", "matches": [], "match_count": 0,
                "hash_comparisons": 0, "char_comparisons": 0, "collisions": 0,
                "time_ms": 0.0, "steps": [], "pattern_hash": _hash(pattern, base, mod),
                "details": {"note": f"Pattern ({m}) longer than text ({n})."}}

    pattern_hash = _hash(pattern, base, mod)
    matches: list[int] = []
    steps: list[dict] = []
    hash_comparisons = 0
    char_comparisons = 0
    collisions = 0

    start = time.perf_counter()
    window = _hash(text[:m], base, mod)
    base_m = pow(base, m - 1, mod)

    for i in range(n - m + 1):
        if i > 0:
            window = ((window - ord(text[i - 1]) * base_m) * base
                      + ord(text[i + m - 1])) % mod
        hash_comparisons += 1
        if window == pattern_hash:
            # Hash matched -> possible false positive, verify character-wise.
            verified = True
            compared = 0
            for k in range(m):
                compared += 1
                if text[i + k] != pattern[k]:
                    verified = False
                    break
            char_comparisons += compared
            if verified:
                matches.append(i)
                if trace:
                    steps.append({
                        "index": i, "window": text[i:i + m], "hash": window,
                        "action": "match", "verified": True,
                        "description": f"window hash {window} == pattern hash {pattern_hash} "
                                       f"and verification passed -> match at {i}",
                    })
            else:
                collisions += 1
                if trace:
                    steps.append({
                        "index": i, "window": text[i:i + m], "hash": window,
                        "action": "collision", "verified": False,
                        "description": f"HASH COLLISION at {i}: same hash, different text -> "
                                       f"rejected after {compared} character comparisons",
                    })
        elif trace:
            steps.append({
                "index": i, "window": text[i:i + m], "hash": window,
                "action": "skip",
                "description": f"window hash {window} != pattern hash {pattern_hash} -> slide",
            })

    elapsed = (time.perf_counter() - start) * 1000
    return {
        "algorithm": "Rabin-Karp",
        "matches": matches,
        "match_count": len(matches),
        "hash_comparisons": hash_comparisons,
        "char_comparisons": char_comparisons,
        "comparisons": hash_comparisons + char_comparisons,
        "collisions": collisions,
        "time_ms": elapsed,
        "pattern_hash": pattern_hash,
        "base": base,
        "modulus": mod,
        "steps": steps,
        "details": {
            "text_length": n, "pattern_length": m,
            "note": f"{hash_comparisons} hash comparisons (O(n) filter) + "
                    f"{char_comparisons} verification comparisons; {collisions} false positive(s).",
        },
    }


def rabin_karp_multi(text: str, patterns: list[str], base: int = BASE,
                     mod: int = PRIME) -> dict:
    """Multi-pattern variant: one pass over the text, many patterns.

    This is Rabin-Karp's real niche - with k patterns, naive/KMP would need
    k passes, here it stays O(n + sum(len(p))).
    """
    results: dict[str, list[int]] = {}
    for pattern in patterns:
        results[pattern] = rabin_karp(text, pattern, base, mod)["matches"]
    return {
        "algorithm": "Rabin-Karp (multi-pattern)",
        "results": results,
        "note": f"One rolling pass can screen {len(patterns)} patterns at once.",
    }
