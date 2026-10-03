"""Linear search (sequential search) - implemented from scratch.

DAA facts
---------
Purpose : find the position of a key inside an unsorted array/list.
Average : O(n)   Best: O(1)   Worst: O(n)
Space   : O(1) auxiliary.

Why it matters here: linear search is the honest baseline against which
binary search, hashing and Trie lookup are compared.  It is the only
search that works on *unsorted* data, which is exactly why the search
engine needs a pre-processing (indexing) stage.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Iterable, Sequence


def linear_search(data: Sequence[Any], key: Any,
                  key_func: Callable[[Any], Any] | None = None) -> dict:
    """Scan ``data`` left to right and return the first index whose value
    equals ``key``.

    Parameters
    ----------
    data : sequence
        The collection to scan (need not be sorted).
    key : Any
        Value we are hunting for.
    key_func : callable, optional
        Projection applied to both the key and every element before
        comparison, e.g. ``str.lower`` for case-insensitive search.
    """
    probe = key_func or (lambda value: value)
    target = probe(key)
    steps: list[dict] = []
    comparisons = 0
    start = time.perf_counter()

    for index in range(len(data)):
        comparisons += 1
        current = probe(data[index])
        matched = current == target
        steps.append({
            "index": index,
            "value": data[index] if not isinstance(data[index], (dict, list)) else str(data[index])[:40],
            "comparing_with": key,
            "matched": matched,
            "description": f"Compare data[{index}] ({current!r}) with key ({target!r})",
        })
        if matched:
            elapsed = (time.perf_counter() - start) * 1000
            return {
                "algorithm": "Linear Search",
                "found": True,
                "index": index,
                "value": data[index],
                "comparisons": comparisons,
                "elements_scanned": index + 1,
                "time_ms": elapsed,
                "steps": steps,
                "details": {
                    "note": f"Early exit after {index + 1} of {len(data)} elements "
                            f"- best case O(1) when the key is first."
                },
            }

    elapsed = (time.perf_counter() - start) * 1000
    return {
        "algorithm": "Linear Search",
        "found": False,
        "index": None,
        "value": None,
        "comparisons": comparisons,
        "elements_scanned": len(data),
        "time_ms": elapsed,
        "steps": steps,
        "details": {"note": f"Worst case: all {len(data)} elements compared - O(n)."},
    }


def linear_search_trace(data: Iterable[Any], key: Any,
                        key_func: Callable[[Any], Any] | None = None) -> list[dict]:
    """Return every comparison the algorithm performs (no early exit)."""
    probe = key_func or (lambda value: value)
    target = probe(key)
    trace = []
    for index, value in enumerate(data):
        trace.append({
            "index": index,
            "value": str(value)[:40],
            "matched": probe(value) == target,
            "description": "data[%d] vs key" % index,
        })
    return trace
