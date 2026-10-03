"""Dijkstra's shortest-path algorithm - implemented from scratch on top of
our own binary min-heap (no ``heapq``).

DAA facts
---------
Time  : O((V + E) log V) with a binary heap (log E with lazy deletion)
       O(V^2) with an adjacency matrix and linear min-extraction
Space : O(V + E) for the adjacency list, O(V) extra for distance/parent
Pre-condition: **all edge weights must be non-negative**.  A negative edge
breaks the greedy argument ("once settled, never revisited") - Bellman-Ford
is required there.

Why a priority queue?  Naive Dijkstra re-scans all V vertices to find the
minimum each round -> O(V^2).  Extracting the minimum from a heap is
O(log V), hence O((V + E) log V) overall, and Floyd heapify gives the
binary-heap-only lower bound (Omega((V+E) log V)) on comparison sorts.
"""

from __future__ import annotations

from typing import Hashable

from algorithms.heap import BinaryHeap


def dijkstra(graph: dict[Hashable, list], source: Hashable,
              goal: Hashable | None = None) -> dict:
    """Single-source (optionally single-target) shortest paths.

    ``graph`` maps a node to a list of ``(neighbour, weight)`` tuples.
    """
    distances: dict[Hashable, float] = {source: 0}
    parent: dict[Hashable, Hashable | None] = {source: None}
    settled: list[Hashable] = []          # settle order (list: reproducible output)
    settled_set: set[Hashable] = set()
    heap = BinaryHeap()
    heap.push(0, source)
    steps: list[dict] = []
    relaxations = 0
    stale_skips = 0

    while heap:
        distance, node = heap.pop()
        if node in settled_set:
            stale_skips += 1
            steps.append({"action": "skip", "node": node,
                          "description": f"Stale heap entry for '{node}' -> skip"})
            continue
        settled.append(node)
        settled_set.add(node)
        steps.append({
            "action": "settle", "node": node, "distance": distance,
            "heap": heap.as_levels(),
            "description": f"Extract-min '{node}' with final distance {distance} "
                           f"(greedy: no shorter path can appear later)",
        })
        if goal is not None and node == goal:
            steps.append({"action": "found", "node": node,
                          "description": f"Goal '{goal}' settled at distance {distance}"})
            break
        for neighbour, weight in graph.get(node, []):
            if weight < 0:
                raise ValueError(
                    "Dijkstra requires non-negative edge weights; "
                    "use Bellman-Ford for negative weights."
                )
            new_distance = distance + weight
            if new_distance < distances.get(neighbour, float("inf")):
                relaxations += 1
                improved = neighbour in distances
                distances[neighbour] = new_distance
                parent[neighbour] = node
                heap.push(new_distance, neighbour)
                steps.append({
                    "action": "relax", "node": neighbour, "from": node,
                    "weight": weight, "new_distance": new_distance,
                    "heap": heap.as_levels(),
                    "description": f"Relax edge {node}->{neighbour} (w={weight}): "
                                   f"{'improved' if improved else 'discovered'} "
                                   f"dist[{neighbour}] = {new_distance}",
                })

    return {
        "algorithm": "Dijkstra (binary min-heap priority queue)",
        "source": source,
        "distances": {str(k): v for k, v in distances.items()},
        # Raw node ids: dictionary *keys* are stringified for JSON, but list
        # values keep their type so callers can use them as map lookups.
        "settled": list(settled),
        "parents": {str(k): (str(v) if v is not None else None) for k, v in parent.items()},
        "shortest_path": _reconstruct(parent, goal) if goal is not None and goal in parent else None,
        "shortest_distance": distances.get(goal) if goal is not None else None,
        "steps": steps,
        "relaxations": relaxations,
        "heap_comparisons": heap.comparisons,
        "stale_skips": stale_skips,
        "details": {
            "nodes_settled": len(settled),
            "reachable_nodes": len(distances),
            "note": f"O((V+E) log V) with the custom binary heap "
                    f"({heap.comparisons} heap comparisons, {relaxations} relaxations).",
        },
    }


def shortest_path_tree(graph: dict[Hashable, list], source: Hashable) -> dict:
    """Distance labels + parents for every reachable node."""
    return dijkstra(graph, source)


def _reconstruct(parent: dict[Hashable, Hashable | None], goal: Hashable) -> list[Hashable]:
    path: list[Hashable] = []
    node: Hashable | None = goal
    while node is not None:
        path.append(node)
        node = parent.get(node)
    return list(reversed(path))
