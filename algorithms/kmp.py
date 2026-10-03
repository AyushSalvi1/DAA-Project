"""Knuth-Morris-Pratt string matching - implemented from scratch.

DAA facts
---------
The naive matcher restarts the text pointer after every mismatch, so its
worst case is O((n - m + 1) * m).  KMP removes that restart by
pre-computing the **LPS array** (Longest Proper Prefix which is also a
Suffix) so that after a mismatch we *reuse* the already matched prefix.

build_lps : O(m) time, O(m) space.
search    : O(n + m) time, O(m) space - i.e. O(n) in the text length and
            *independent of pattern length*, which is the whole point.

Amortised argument: ``i`` (text pointer) and ``j`` (pattern pointer) each
move forward at most n and m times; every j-decrement is paid for by a
later j-increment, so total work is linear.

Implemented by hand: no ``str.find`` / regex engine anywhere.
"""

from __future__ import annotations

import time


def build_lps(pattern: str) -> tuple[list[int], list[dict]]:
    """Build the LPS (failure-function) array.

    ``lps[i]`` = length of the longest **proper** prefix of ``pattern[0..i]``
    that is also a suffix of it.  "Proper" matters: a word cannot be its own
    fallback, otherwise the matcher would loop forever.

    The subtle line is the fallback branch: when ``pattern[i] != pattern[j]``
    we set ``j = lps[j-1]`` and **re-test the same i**.  Advancing i here (the
    obvious-looking bug) loses matches - that is exactly what this
    implementation avoids.

    Returns ``(lps, steps)`` where ``steps`` drives the visualizer.
    """
    m = len(pattern)
    lps = [0] * m
    steps: list[dict] = []
    length = 0          # length of the current matched prefix
    i = 1

    while i < m:
        steps.append({
            "i": i, "j": length, "value": pattern[i],
            "length": length,
            "description": f"pattern[{i}] = '{pattern[i]}' vs pattern[{length}] = "
                           f"'{pattern[length]}'",
            "lps_snapshot": list(lps[: i + 1]),
        })
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            steps[-1]["action"] = "match->extend"
            steps[-1]["description"] += f" -> lps[{i}] = {length}"
            i += 1
        elif length != 0:
            # fall back and retry the SAME character - this is the whole point
            steps[-1]["action"] = "mismatch->fallback"
            steps[-1]["description"] += f" -> length = lps[{length - 1}] = {lps[length - 1]}"
            length = lps[length - 1]
        else:
            lps[i] = 0
            steps[-1]["action"] = "mismatch->zero"
            steps[-1]["description"] += f" -> lps[{i}] = 0"
            i += 1

    if m:
        steps.append({
            "i": m - 1, "j": length, "value": pattern[-1], "length": length,
            "action": "done", "lps_snapshot": list(lps),
            "description": f"LPS complete: {lps}",
        })
    return lps, steps


def kmp_search(text: str, pattern: str, trace: bool = True) -> dict:
    """Return every (possibly overlapping) occurrence of ``pattern`` in ``text``.

    ``trace=False`` skips the per-character step log, which is what the
    search pipeline uses when it only needs the match count (building a dict
    per character would dominate the runtime).
    """
    n, m = len(text), len(pattern)
    if m == 0:
        return {
            "algorithm": "KMP", "matches": [], "match_count": 0, "comparisons": 0,
            "time_ms": 0.0, "lps": [], "lps_steps": [], "steps": [],
            "details": {"note": "Empty pattern - nothing to search for."},
        }
    if m > n:
        return {
            "algorithm": "KMP", "matches": [], "match_count": 0, "comparisons": 0,
            "time_ms": 0.0, "lps": build_lps(pattern)[0], "lps_steps": [],
            "steps": [], "details": {"note": f"Pattern length {m} > text length {n}."},
        }

    if trace:
        lps, lps_steps = build_lps(pattern)
    else:
        lps, lps_steps = _fast_lps(pattern), []

    matches: list[int] = []
    steps: list[dict] = []
    comparisons = 0
    i = j = 0
    start = time.perf_counter()

    while i < n:
        comparisons += 1
        if text[i] == pattern[j]:
            if trace:
                steps.append({
                    "i": i, "j": j, "char": text[i], "pattern_char": pattern[j],
                    "action": "match", "matched_prefix": j + 1,
                    "description": f"text[{i}]='{text[i]}' == pattern[{j}] -> j = {j + 1}",
                })
            j += 1
            if j == m:
                matches.append(i - m + 1)
                if trace:
                    steps.append({
                        "i": i, "j": j - 1, "char": text[i], "pattern_char": pattern[m - 1],
                        "action": "found", "position": i - m + 1,
                        "description": f"FULL MATCH at index {i - m + 1}; "
                                       f"fall back to lps[{m - 1}] = {lps[m - 1]} to allow overlap",
                    })
                j = lps[j - 1]
            i += 1
        elif j > 0:
            fallback = lps[j - 1]
            if trace:
                steps.append({
                    "i": i, "j": j, "char": text[i], "pattern_char": pattern[j],
                    "action": "fallback", "new_j": fallback, "matched_prefix": j,
                    "description": f"mismatch, text[{i}]='{text[i]}' != pattern[{j}]='{pattern[j]}' "
                                   f"-> j = lps[{j - 1}] = {fallback} "
                                   f"(same text char is re-tested, no re-scan)",
                })
            # NB: i is *not* advanced - the fallback prefix must be re-tested
            # against this same character, exactly as in build_lps.
            j = fallback
        else:
            if trace:
                steps.append({
                    "i": i, "j": j, "char": text[i], "pattern_char": pattern[j],
                    "action": "mismatch", "matched_prefix": 0,
                    "description": f"mismatch, j = 0 -> only i advances (text[{i}]='{text[i]}')",
                })
            i += 1

    elapsed = (time.perf_counter() - start) * 1000
    return {
        "algorithm": "KMP",
        "matches": matches,
        "match_count": len(matches),
        "comparisons": comparisons,
        "time_ms": elapsed,
        "lps": lps,
        "lps_steps": lps_steps,
        "steps": steps,
        "details": {
            "text_length": n, "pattern_length": m,
            "note": f"{comparisons} character comparisons for n={n}, m={m} "
                    f"(bound 2n = {2 * n}). "
                    f"Naive worst case would be (n-m+1)*m = {(n - m + 1) * m}.",
        },
    }


def _fast_lps(pattern: str) -> list[int]:
    """LPS without building the visualizer's step trace (same O(m) result).

    Note the missing ``i += 1`` in the fallback branch: after
    ``length = lps[length - 1]`` the *same* text character is re-tested.
    """
    m = len(pattern)
    lps = [0] * m
    length = 0
    i = 1
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        elif length:
            length = lps[length - 1]
        else:
            lps[i] = 0
            i += 1
    return lps


def naive_search(text: str, pattern: str) -> dict:
    """Baseline matcher, kept so the dashboard can show KMP's advantage."""
    n, m = len(text), len(pattern)
    matches: list[int] = []
    comparisons = 0
    steps: list[dict] = []
    start = time.perf_counter()
    if m:
        for i in range(n - m + 1):
            j = 0
            while j < m:
                comparisons += 1
                if text[i + j] != pattern[j]:
                    steps.append({"i": i, "j": j, "char": text[i + j],
                                  "pattern_char": pattern[j], "action": "mismatch",
                                  "description": f"mismatch, restart at i={i + 1}"})
                    break
                steps.append({"i": i, "j": j, "char": text[i + j],
                              "pattern_char": pattern[j], "action": "match",
                              "description": f"text[{i + j}] matches pattern[{j}]"})
                j += 1
            if j == m:
                matches.append(i)
    elapsed = (time.perf_counter() - start) * 1000
    return {
        "algorithm": "Naive / Brute Force",
        "matches": matches, "match_count": len(matches), "comparisons": comparisons,
        "time_ms": elapsed,
        "details": {"text_length": n, "pattern_length": m,
                    "note": f"Worst case O(n*m) = {n * m} comparisons."},
    }
