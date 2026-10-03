"""Merge Sort - top-down divide & conquer, implemented from scratch.

DAA facts
---------
Recurrence : T(n) = 2T(n/2) + Theta(n)  ->  Theta(n log n) for every input
Best / Average / Worst : Theta(n log n) - *no* O(n) best case like insertion sort
Space    : Theta(n) auxiliary (the merged buffer) + Theta(log n) call stack
Stability: yes (equal keys keep their relative order - we compare ``<=``)
Stability matters in a search engine: an equally relevant document keeps its
earlier tie-break order.

The linear merge step is the heart of the algorithm: two sorted halves are
walked once, each element is emitted exactly once -> O(n).
"""

from __future__ import annotations

import time
from typing import Any, Callable, Sequence


def merge_sort(data: Sequence[Any], key: Callable[[Any], Any] | None = None,
               trace: bool = False) -> dict:
    """Sort ``data`` with merge sort. ``key`` allows sorting by a field."""
    probe = key or (lambda value: value)
    array = list(data)
    steps: list[dict] = []
    comparisons = [0]

    def merge(left: list[Any], right: list[Any]) -> list[Any]:
        merged: list[Any] = []
        i = j = 0
        while i < len(left) and j < len(right):
            comparisons[0] += 1
            if probe(left[i]) <= probe(right[j]):
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1
            if trace:
                steps.append({"action": "merge", "left": left, "right": right,
                              "merged": list(merged),
                              "description": f"take smallest -> {merged[-1]!r}"})
        merged.extend(left[i:])
        merged.extend(right[j:])
        if trace:
            steps.append({"action": "merge-done", "merged": list(merged),
                          "description": f"merged run = {merged}"})
        return merged

    def sort(chunk: list[Any], depth: int) -> list[Any]:
        if len(chunk) <= 1:
            return chunk
        mid = len(chunk) // 2
        if trace:
            steps.append({"action": "split", "array": list(chunk), "depth": depth,
                          "mid": mid,
                          "description": f"split {len(chunk)} elements at index {mid} "
                                         f"-> {mid} + {len(chunk) - mid}"})
        left = sort(chunk[:mid], depth + 1)
        right = sort(chunk[mid:], depth + 1)
        merged = merge(left, right)
        if trace:
            steps.append({"action": "merged", "array": list(merged), "depth": depth,
                          "description": f"merged two sorted halves of depth {depth}"})
        return merged

    start = time.perf_counter()
    sorted_array = sort(array, 0)
    elapsed = (time.perf_counter() - start) * 1000
    return {
        "algorithm": "Merge Sort",
        "sorted": sorted_array,
        "comparisons": comparisons[0],
        "time_ms": elapsed,
        "input_size": len(array),
        "steps": steps,
        "stable": True,
        "space_complexity": "Theta(n)",
        "details": {"note": f"Theta(n log n) = {max(1, len(array) * max(1, len(array).bit_length()))} "
                            f"order-of-magnitude operations for n={len(array)}."},
    }


def merge_sort_values(values: list[Any]) -> list[Any]:
    return merge_sort(values)["sorted"]
