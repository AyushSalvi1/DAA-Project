"""Binary min-heap / priority queue - implemented from scratch.

Used as the priority queue for Dijkstra's algorithm and for the
"pop the best candidate first" ordering in result expansion.

Properties (min-heap): the minimum element is always at the root (index 0),
and every parent <= its children.  Because the heap is a *complete* binary
tree stored in a flat list, index arithmetic replaces pointers:

    parent(i)    = (i - 1) // 2
    left child   = 2i + 1
    right child  = 2i + 2

insert   : O(log n)   extract-min : O(log n)   peek : O(1)
decrease-key : O(log n)   build-heap (Floyd) : O(n) - *not* O(n log n),
which is why Dijkstra is O((V + E) log V) and not O(V * E).

Ties: every entry carries a monotonically increasing insertion counter, so
equal priorities come out in FIFO order.  Without it the heap would order
equal keys by array position, which silently perturbs Dijkstra's settle
order and makes runs non-reproducible.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable

Entry = tuple[Any, int, Any]  # (priority, insertion order, value)


class BinaryHeap:
    """Array-backed binary min-heap of ``(priority, value)`` tuples."""

    def __init__(self, key: Callable[[Any], Any] | None = None) -> None:
        self._heap: list[Entry] = []
        self.key = key or (lambda item: item)
        self.comparisons = 0
        self._counter = 0

    # -- introspection -------------------------------------------------
    def __len__(self) -> int:
        return len(self._heap)

    def __bool__(self) -> bool:
        return bool(self._heap)

    @property
    def heap(self) -> list[tuple[Any, Any]]:
        """Flat backing array rendered as ``(priority, value)`` pairs."""
        return [(priority, value) for priority, _, value in self._heap]

    def as_levels(self) -> list[list[Any]]:
        """Heap rendered level-by-level for the visualizer."""
        levels: list[list[Any]] = []
        size = len(self._heap)
        start = 0
        width = 1
        while start < size:
            levels.append([f"{self._heap[i][0]}:{self._heap[i][2]}"
                           for i in range(start, min(start + width, size))])
            start += width
            width *= 2
        return levels

    # -- ordering ------------------------------------------------------
    def _precedes(self, left: Entry, right: Entry) -> bool:
        """Strict 'left must come out before right' test (priority, then FIFO)."""
        self.comparisons += 1
        left_key = self.key(left[0])
        right_key = self.key(right[0])
        if left_key != right_key:
            return left_key < right_key
        return left[1] < right[1]

    # -- core ----------------------------------------------------------
    def push(self, priority: Any, value: Any = None) -> None:
        """Insert in O(log n) - append then sift-up."""
        self._heap.append((priority, self._counter, value))
        self._counter += 1
        self._sift_up(len(self._heap) - 1)

    def _sift_up(self, index: int) -> list[dict]:
        steps: list[dict] = []
        while index > 0:
            parent = (index - 1) // 2
            if not self._precedes(self._heap[index], self._heap[parent]):
                break
            self._heap[parent], self._heap[index] = self._heap[index], self._heap[parent]
            steps.append({"action": "swap-up", "index": index, "parent": parent,
                          "description": f"parent({index})={parent} had larger priority -> swap"})
            index = parent
        return steps

    def peek(self) -> tuple[Any, Any] | None:
        return (self._heap[0][0], self._heap[0][2]) if self._heap else None

    def pop(self) -> tuple[Any, Any] | None:
        """Extract-min in O(log n) - swap root with last, sift-down."""
        if not self._heap:
            return None
        root = self._heap[0]
        last = self._heap.pop()
        if self._heap:
            self._heap[0] = last
            self._sift_down(0)
        return (root[0], root[2])

    extract_min = pop

    def _sift_down(self, index: int) -> list[dict]:
        steps: list[dict] = []
        size = len(self._heap)
        while True:
            left, right = 2 * index + 1, 2 * index + 2
            smallest = index
            if left < size and self._precedes(self._heap[left], self._heap[smallest]):
                smallest = left
            if right < size and self._precedes(self._heap[right], self._heap[smallest]):
                smallest = right
            if smallest == index:
                break
            self._heap[index], self._heap[smallest] = self._heap[smallest], self._heap[index]
            steps.append({"action": "swap-down", "index": index, "child": smallest,
                          "description": f"smaller child {smallest} -> swap with {index}"})
            index = smallest
        return steps

    def decrease_key(self, index: int, new_priority: Any) -> None:
        """Relaxation helper: O(log n) (sift-up only)."""
        self._heap[index] = (new_priority, self._heap[index][1], self._heap[index][2])
        self._sift_up(index)

    # -- bulk construction ---------------------------------------------
    def build_from(self, items: Iterable[tuple[Any, Any]]) -> "BinaryHeap":
        """Floyd heapify - O(n) bottom-up construction."""
        self._heap = [(priority, order, value)
                      for order, (priority, value) in enumerate(items)]
        self._counter = len(self._heap)
        for i in range(len(self._heap) // 2 - 1, -1, -1):
            self._sift_down(i)
        return self

    def heap_sort(self) -> list[Any]:
        """Repeated extract-min -> ascending order, O(n log n)."""
        out = []
        heap = BinaryHeap(self.key)
        heap._heap = list(self._heap)
        heap._counter = self._counter
        while heap._heap:
            out.append(heap.pop()[1])
        return out


def heap_sort(values: list[Any], reverse: bool = False) -> dict:
    """Heap sort built on the custom heap (extra log n array space)."""
    heap = BinaryHeap()
    for value in values:
        heap.push(value, value)
    ordered: list[Any] = []
    while heap:
        ordered.append(heap.pop()[0])
    if reverse:
        ordered.reverse()
    return {"algorithm": "Heap Sort", "sorted": ordered, "comparisons": heap.comparisons}