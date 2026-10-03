"""Breadth-First Search - implemented from scratch (queue + adjacency list).

DAA facts
---------
Time  : O(V + E)  (each vertex enqueued once, each edge examined twice)
Space : O(V) for the visited array + queue

Properties: finds the **shortest path in edge count** (unweighted graphs);
detects cycles (a revisited vertex on the current path); produces a
minimum-depth spanning structure; used in peer-to-peer broadcast, in
maze/level generation and in "find all nodes within k hops".

In NexaSearch the document graph is unweighted, so BFS answers
"which documents are 1, 2 or 3 links away from this one?".
"""

from __future__ import annotations

from collections import deque
from typing import Hashable


def bfs(graph: dict[Hashable, list[Hashable]], start: Hashable,
        goal: Hashable | None = None, max_depth: int | None = None) -> dict:
    """Breadth-first traversal from ``start``.

    Parameters
    ----------
    graph : adjacency list ``{node: [neighbours]}``
    start : source vertex
    goal  : stop as soon as this vertex is dequeued (still correct, since
            the first time it is reached is on a shortest path)
    max_depth : optional depth cap so the Algorithm Lab cannot hang on a
            huge graph.
    """
    visited: set[Hashable] = set()
    visit_order: list[Hashable] = []      # discovery order -> reproducible output
    parent: dict[Hashable, Hashable | None] = {start: None}
    depth: dict[Hashable, int] = {start: 0}
    order: list[Hashable] = []
    steps: list[dict] = []
    queue: deque = deque([start])
    visited.add(start)
    visit_order.append(start)
    edge_examinations = 0

    while queue:
        node = queue.popleft()
        order.append(node)
        steps.append({
            "action": "dequeue", "node": node, "depth": depth[node],
            "queue": list(queue),
            "description": f"Dequeue '{node}' (depth {depth[node]})",
        })
        if goal is not None and node == goal:
            steps.append({"action": "found", "node": node,
                          "description": f"Goal '{goal}' reached - BFS guarantees shortest path"})
            break
        if max_depth is not None and depth[node] >= max_depth:
            steps.append({"action": "depth-cap", "node": node,
                          "description": f"depth cap {max_depth} reached -> "
                                         f"do not expand '{node}'"})
            continue
        for neighbour in graph.get(node, []):
            edge_examinations += 1
            if neighbour not in visited:
                visited.add(neighbour)
                visit_order.append(neighbour)
                parent[neighbour] = node
                depth[neighbour] = depth[node] + 1
                queue.append(neighbour)
                steps.append({
                    "action": "enqueue", "node": neighbour, "from": node,
                    "depth": depth[neighbour], "queue": list(queue),
                    "description": f"Discovered '{neighbour}' via '{node}' "
                                   f"(depth {depth[neighbour]})",
                })
            else:
                steps.append({
                    "action": "skip", "node": neighbour, "from": node,
                    "queue": list(queue),
                    "description": f"'{neighbour}' already visited -> skip (cycle/back-edge)",
                })

    return {
        "algorithm": "BFS",
        "traversal_order": order,
        "visited": visit_order,
        "parents": {str(k): (str(v) if v is not None else None) for k, v in parent.items()},
        "depths": {str(k): v for k, v in depth.items()},
        "path_to_goal": reconstruct_path(parent, goal) if goal is not None and goal in parent else None,
        "levels": group_by_depth(order, depth),
        "edge_examinations": edge_examinations,
        "steps": steps,
        "details": {
            "nodes_visited": len(visited),
            "queue_operations": len(order) * 2,
            "note": "FIFO queue gives shortest path by number of edges - O(V + E).",
        },
    }


def reconstruct_path(parent: dict[Hashable, Hashable | None],
                     goal: Hashable) -> list[Hashable]:
    """Walk the parent chain backwards - O(path length)."""
    path: list[Hashable] = []
    node: Hashable | None = goal
    while node is not None:
        path.append(node)
        node = parent.get(node)
    return list(reversed(path))


def group_by_depth(order: list[Hashable],
                   depth: dict[Hashable, int]) -> list[list[Hashable]]:
    levels: list[list[Hashable]] = []
    for node in order:
        d = depth.get(node, 0)
        while len(levels) <= d:
            levels.append([])
        levels[d].append(node)
    return levels
