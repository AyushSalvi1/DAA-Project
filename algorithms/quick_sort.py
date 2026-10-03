"""Quick Sort (Hoare/Lomuto partition) - implemented from scratch with an
iterative stack so deep recursion can never blow the Python stack.

DAA facts
---------
Recurrence (balanced)   : T(n) = 2T(n/2) + Theta(n)  -> Theta(n log n)
Recurrence (unbalanced) : T(n) = T(n-1) + Theta(n)      -> Theta(n^2)
Best / Average : Theta(n log n)      Worst : Theta(n^2)
Space  : O(log n) expected for the recursion/aux stack, O(n) worst
In-place: yes (partition happens in place, no extra array)
Stability : no (swaps reorder equal keys)

Mitigation used here: **median-of-three pivot** with a last-element
truncation, which makes the already-sorted / reverse-sorted inputs hit the
balanced case instead of degrading to O(n^2) - exactly the input shape a
ranking pipeline produces.
"""

from __future__ import annotations

import random
import time
from typing import Any, Callable, Sequence


def quick_sort(data: Sequence[Any], key: Callable[[Any], Any] | None = None,
               trace: bool = False) -> dict:
    """Sort with quick sort using median-of-three pivoting."""
    probe = key or (lambda value: value)
    array = list(data)
    steps: list[dict] = []
    comparisons = [0]
    partitions = [0]
    max_depth = [0]

    def partition(low: int, high: int, depth: int) -> int:
        partitions[0] += 1
        max_depth[0] = max(max_depth[0], depth)
        # median-of-three: first, middle, last
        mid = (low + high) // 2
        trio = [(array[low], low), (array[mid], mid), (array[high], high)]
        trio.sort(key=lambda item: probe(item[0]))
        pivot_value, pivot_index = trio[1]
        array[pivot_index], array[high] = array[high], array[pivot_index]
        pivot = probe(array[high])

        i = low - 1
        for j in range(low, high):
            comparisons[0] += 1
            if probe(array[j]) <= pivot:
                i += 1
                array[i], array[j] = array[j], array[i]
        array[i + 1], array[high] = array[high], array[i + 1]
        if trace:
            steps.append({
                "action": "partition", "pivot": pivot_value, "pivot_index": high,
                "final_index": i + 1, "array": list(array), "range": [low, high],
                "depth": depth,
                "description": f"pivot {pivot_value!r} lands at index {i + 1}; "
                               f"left block [ {low}..{i} ] <= pivot < right block [ {i + 2}..{high} ]",
            })
        return i + 1

    def quick_sort_range(low: int, high: int, depth: int = 0) -> None:
        stack: list[tuple[int, int, int]] = [(low, high, depth)]
        while stack:
            low, high, depth = stack.pop()
            if low >= high:
                continue
            pivot_index = partition(low, high, depth)
            # push the larger side first so the smaller side is processed now:
            # keeps the auxiliary stack at O(log n) even on skewed input.
            if pivot_index - low > high - pivot_index:
                stack.append((pivot_index + 1, high, depth + 1))
                stack.append((low, pivot_index - 1, depth + 1))
            else:
                stack.append((low, pivot_index - 1, depth + 1))
                stack.append((pivot_index + 1, high, depth + 1))

    start = time.perf_counter()
    if array:
        quick_sort_range(0, len(array) - 1)
    elapsed = (time.perf_counter() - start) * 1000
    return {
        "algorithm": "Quick Sort",
        "sorted": array,
        "comparisons": comparisons[0],
        "time_ms": elapsed,
        "input_size": len(array),
        "partitions": partitions[0],
        "max_recursion_depth": max_depth[0],
        "steps": steps,
        "stable": False,
        "space_complexity": "O(log n) expected",
        "details": {"note": f"{partitions[0]} partition steps, max pivot depth "
                            f"{max_depth[0]}, {comparisons[0]} comparisons."},
    }


def quick_sort_values(values: list[Any]) -> list[Any]:
    return quick_sort(values)["sorted"]


def randomized_quick_sort(data: Sequence[Any],
                          key: Callable[[Any], Any] | None = None,
                          seed: int = 7) -> list[Any]:
    """Randomised variant - expected Theta(n log n) for *any* input order."""
    probe = key or (lambda value: value)
    array = list(data)
    rng = random.Random(seed)

    def partition(low: int, high: int) -> int:
        pivot_index = rng.randint(low, high)
        array[pivot_index], array[high] = array[high], array[pivot_index]
        pivot = probe(array[high])
        i = low - 1
        for j in range(low, high):
            if probe(array[j]) <= pivot:
                i += 1
                array[i], array[j] = array[j], array[i]
        array[i + 1], array[high] = array[high], array[i + 1]
        return i + 1

    def sort(low: int, high: int) -> None:
        stack = [(low, high)]
        while stack:
            low, high = stack.pop()
            if low >= high:
                continue
            p = partition(low, high)
            stack.append((p + 1, high))
            stack.append((low, p - 1))

    if array:
        sort(0, len(array) - 1)
    return array
