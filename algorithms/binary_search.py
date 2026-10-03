"""Binary search - implemented from scratch (iterative *and* recursive).

DAA facts
---------
Purpose : locate a key in a **sorted** sequence by repeatedly halving.
Average : O(log n)  Best: O(log log n) - O(1) when found immediately
         Worst: O(log n)  (ceiling of log2(n+1) probes).
Space   : O(1) iterative, O(log n) for the recursive form (call stack).

This module deliberately refuses to "cheat": if the caller hands us an
unsorted array we raise ``ValueError`` instead of silently returning a
wrong answer, because the log n guarantee depends entirely on the
pre-condition that the data is sorted.
"""

from __future__ import annotations

import math
import time
from typing import Any, Callable, Sequence


def is_sorted(data: Sequence[Any], key_func: Callable[[Any], Any] | None = None) -> bool:
    """O(n) verification of the binary-search pre-condition.

    The optional projection matters: if the caller searches case-insensitively
    the data must be sorted *under the same projection*.
    """
    probe = key_func or (lambda value: value)
    return all(probe(data[i]) <= probe(data[i + 1]) for i in range(len(data) - 1))


def _require_sorted(data: Sequence[Any], key_func: Callable[[Any], Any] | None = None) -> None:
    if not is_sorted(data, key_func):
        raise ValueError(
            "Binary Search requires sorted input. Sort the data first "
            "(see algorithms/merge_sort.py or algorithms/quick_sort.py)."
        )


def binary_search(data: Sequence[Any], key: Any,
                  key_func: Callable[[Any], Any] | None = None) -> dict:
    """Iterative binary search with a step trace for the visualizer."""
    if not data:
        return {
            "algorithm": "Binary Search", "found": False, "index": None,
            "value": None, "comparisons": 0, "time_ms": 0.0, "steps": [],
            "details": {"note": "Empty dataset - nothing to search."},
        }
    probe = key_func or (lambda value: value)
    _require_sorted(data, key_func)
    target = probe(key)
    low, high = 0, len(data) - 1
    steps: list[dict] = []
    comparisons = 0
    start = time.perf_counter()

    while low <= high:
        mid = low + (high - low) // 2
        current = probe(data[mid])
        comparisons += 1
        if current == target:
            elapsed = (time.perf_counter() - start) * 1000
            steps.append({
                "low": low, "mid": mid, "high": high, "value": str(data[mid])[:40],
                "decision": "match",
                "description": f"data[{mid}] == key -> found at index {mid}",
            })
            return {
                "algorithm": "Binary Search", "found": True, "index": mid,
                "value": data[mid], "comparisons": comparisons, "time_ms": elapsed,
                "steps": steps,
                "details": {
                    "note": f"{comparisons} probes = ceil(log2({len(data)}+1)) = "
                            f"{math.ceil(math.log2(len(data) + 1))} at most.",
                },
            }
        if current < target:
            steps.append({
                "low": low, "mid": mid, "high": high, "value": str(data[mid])[:40],
                "decision": "go-right",
                "description": f"data[{mid}] < key -> discard [{low}..{mid}], low = {mid + 1}",
            })
            low = mid + 1
        else:
            steps.append({
                "low": low, "mid": mid, "high": high, "value": str(data[mid])[:40],
                "decision": "go-left",
                "description": f"data[{mid}] > key -> discard [{mid}..{high}], high = {mid - 1}",
            })
            high = mid - 1

    elapsed = (time.perf_counter() - start) * 1000
    steps.append({
        "low": low, "mid": None, "high": high, "value": None,
        "decision": "exhausted",
        "description": "Range collapsed (low > high) -> key absent",
    })
    return {
        "algorithm": "Binary Search", "found": False, "index": None,
        "value": None, "comparisons": comparisons, "time_ms": elapsed,
        "steps": steps,
        "details": {"note": f"Not found after {comparisons} probes."},
    }


def binary_search_recursive(data: Sequence[Any], key: Any, low: int | None = None,
                            high: int | None = None,
                            key_func: Callable[[Any], Any] | None = None) -> dict:
    """Recursive formulation - same complexity, O(log n) stack space.

    Used to demonstrate that halving drives both the time *and* the
    recursion-depth analysis.
    """
    if not data:
        return {"algorithm": "Binary Search (recursive)", "found": False, "index": None,
                "value": None, "comparisons": 0, "time_ms": 0.0, "steps": [],
                "details": {"note": "Empty dataset."}}
    probe = key_func or (lambda value: value)
    _require_sorted(data, key_func)
    low = 0 if low is None else low
    high = len(data) - 1 if high is None else high

    target = probe(key)
    state = {"comparisons": 0, "steps": [], "depth": 0}
    start = time.perf_counter()

    def helper(lo: int, hi: int, depth: int):
        state["depth"] = max(state["depth"], depth)
        if lo > hi:
            state["steps"].append({"low": lo, "mid": None, "high": hi, "value": None,
                                   "decision": "exhausted",
                                   "description": "Base case: range empty"})
            return None
        mid = lo + (hi - lo) // 2
        current = probe(data[mid])
        state["comparisons"] += 1
        state["steps"].append({
            "low": lo, "mid": mid, "high": hi, "depth": depth,
            "value": str(data[mid])[:40],
            "decision": "match" if current == target else ("go-right" if current < target else "go-left"),
            "description": f"depth {depth}: data[{mid}] = {current!r}",
        })
        if current == target:
            return mid
        if current < target:
            return helper(mid + 1, hi, depth + 1)
        return helper(lo, mid - 1, depth + 1)

    index = helper(low, high, 0)
    elapsed = (time.perf_counter() - start) * 1000
    return {
        "algorithm": "Binary Search (recursive)",
        "found": index is not None,
        "index": index,
        "value": data[index] if index is not None else None,
        "comparisons": state["comparisons"],
        "max_recursion_depth": state["depth"],
        "time_ms": elapsed,
        "steps": state["steps"],
        "details": {"note": f"Maximum recursion depth {state['depth']} -> O(log n) stack space."},
    }


def binary_search_all(data: Sequence[Any], key: Any,
                      key_func: Callable[[Any], Any] | None = None) -> list[int]:
    """Return *all* indices matching ``key`` (lower-bound + scan).

    Cost is O(log n + k) where k is the number of matches.
    """
    probe = key_func or (lambda value: value)
    target = probe(key)
    indices: list[int] = []
    lo, hi = 0, len(data) - 1
    start = None
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if probe(data[mid]) >= target:
            start = mid
            hi = mid - 1
        else:
            lo = mid + 1
    if start is None:
        return indices
    for i in range(start, len(data)):
        if probe(data[i]) == target:
            indices.append(i)
        else:
            break
    return indices
