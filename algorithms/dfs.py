"""Depth-First Search - implemented from scratch (explicit stack / recursion).

DAA facts
---------
Time  : O(V + E)
Space : O(V) for the stack (recursion depth <= V)
Two flavours implemented:
  * iterative  - explicit LIFO stack (no recursion-limit hazards),
  * recursive  - shows the call stack that the interpreter manages.

Properties: follows one branch to the end before backtracking; used for
cycle detection, topological sorting, connected components, maze solving
and "deep dive" recommendations.  Unlike BFS, DFS does *not* guarantee
the shortest path.
"""

from __future__ import annotations

from typing import Hashable


def dfs(graph: dict[Hashable, list[Hashable]], start: Hashable,
        goal: Hashable | None = None, mode: str = "iterative",
        max_depth: int | None = None) -> dict:
    """Depth-first traversal from ``start``.

    ``mode`` is ``"iterative"`` (explicit stack, no recursion) or
    ``"recursive"`` (shows the interpreter call stack).
    ``max_depth`` optionally stops the descent, so the Algorithm Lab cannot
    hang on a very deep graph.
    """
    if mode == "recursive":
        return _dfs_recursive(graph, start, goal, max_depth)
    return _dfs_iterative(graph, start, goal, max_depth)


def _dfs_iterative(graph: dict[Hashable, list[Hashable]], start: Hashable,
                   goal: Hashable | None, max_depth: int | None = None) -> dict:
    visited: set[Hashable] = set()
    visit_order: list[Hashable] = []      # discovery order -> reproducible output
    parent: dict[Hashable, Hashable | None] = {start: None}
    depth: dict[Hashable, int] = {start: 0}
    order: list[Hashable] = []
    steps: list[dict] = []
    stack: list[Hashable] = [start]
    edge_examinations = 0
    found = False

    while stack:
        node = stack.pop()
        if node in visited:
            steps.append({"action": "pop-visited", "node": node,
                          "description": f"'{node}' already visited -> discard"})
            continue
        visited.add(node)
        visit_order.append(node)
        order.append(node)
        steps.append({
            "action": "visit", "node": node, "depth": depth[node],
            "stack": list(stack),
            "description": f"Visit '{node}' (depth {depth[node]}), push its neighbours",
        })
        if goal is not None and node == goal:
            found = True
            steps.append({"action": "found", "node": node,
                          "description": f"Goal '{goal}' reached (DFS path is NOT guaranteed shortest)"})
            break
        if max_depth is not None and depth[node] >= max_depth:
            steps.append({"action": "depth-cap", "node": node,
                          "description": f"depth cap {max_depth} reached -> do not expand"})
            continue
        neighbours = list(graph.get(node, []))
        for neighbour in reversed(neighbours):
            edge_examinations += 1
            if neighbour not in visited:
                parent[neighbour] = node
                depth[neighbour] = depth[node] + 1
                stack.append(neighbour)
                steps.append({
                    "action": "push", "node": neighbour, "from": node,
                    "stack": list(stack),
                    "description": f"Push '{neighbour}' onto the stack",
                })

    return {
        "algorithm": "DFS (iterative stack)",
        "traversal_order": order,
        "visited": visit_order,
        "parents": {str(k): (str(v) if v is not None else None) for k, v in parent.items()},
        "depths": {str(k): v for k, v in depth.items()},
        "path_to_goal": _reconstruct(parent, goal) if found else None,
        "steps": steps,
        "mode": "iterative",
        "edge_examinations": edge_examinations,
        "details": {
            "nodes_visited": len(visited),
            "note": "LIFO stack -> go deep first. Space O(V), time O(V + E).",
        },
    }


def _dfs_recursive(graph: dict[Hashable, list[Hashable]], start: Hashable,
                   goal: Hashable | None, max_depth: int | None = None) -> dict:
    visited: set[Hashable] = set()
    visit_order: list[Hashable] = []
    parent: dict[Hashable, Hashable | None] = {start: None}
    depth: dict[Hashable, int] = {start: 0}
    order: list[Hashable] = []
    steps: list[dict] = []
    stack_trace: list[str] = []
    state = {"found": False, "max_depth": 0, "calls": 0, "edges": 0}

    def visit(node: Hashable) -> None:
        state["calls"] += 1
        stack_trace.append(str(node))
        state["max_depth"] = max(state["max_depth"], len(stack_trace))
        visited.add(node)
        visit_order.append(node)
        order.append(node)
        steps.append({
            "action": "call", "node": node, "depth": len(stack_trace),
            "stack": list(stack_trace),
            "description": f"dfs('{node}') called - call stack depth {len(stack_trace)}",
        })
        if goal is not None and node == goal:
            state["found"] = True
            return
        if max_depth is not None and depth[node] >= max_depth:
            steps.append({"action": "depth-cap", "node": node, "stack": list(stack_trace),
                          "description": f"depth cap {max_depth} reached -> return early"})
            stack_trace.pop()
            return
        for neighbour in graph.get(node, []):
            state["edges"] += 1
            if neighbour not in visited:
                parent[neighbour] = node
                depth[neighbour] = depth[node] + 1
                visit(neighbour)
                if state["found"]:
                    stack_trace.pop()
                    return
        stack_trace.pop()
        steps.append({
            "action": "return", "node": node, "stack": list(stack_trace),
            "description": f"dfs('{node}') returns - backtrack",
        })

    visit(start)
    return {
        "algorithm": "DFS (recursive)",
        "traversal_order": order,
        "visited": visit_order,
        "parents": {str(k): (str(v) if v is not None else None) for k, v in parent.items()},
        "depths": {str(k): v for k, v in depth.items()},
        "path_to_goal": _reconstruct(parent, goal) if state["found"] else None,
        "steps": steps,
        "mode": "recursive",
        "edge_examinations": state["edges"],
        "details": {
            "nodes_visited": len(visited),
            "function_calls": state["calls"],
            "max_call_depth": state["max_depth"],
            "note": f"Recursion depth reached {state['max_depth']} -> O(V) stack space.",
        },
    }


def connected_components(graph: dict[Hashable, list[Hashable]]) -> dict:
    """Every component found by repeated DFS - a classic DFS application."""
    seen: set[Hashable] = set()
    components: list[list[Hashable]] = []
    for node in graph:
        if node in seen:
            continue
        component: list[Hashable] = []
        stack = [node]
        seen.add(node)
        while stack:
            current = stack.pop()
            component.append(current)
            for neighbour in graph.get(current, []):
                if neighbour not in seen:
                    seen.add(neighbour)
                    stack.append(neighbour)
        components.append(component)
    return {"algorithm": "DFS (components)",
            "component_count": len(components),
            "components": components}


def has_cycle(graph: dict[Hashable, list[Hashable]]) -> dict:
    """Cycle detection with DFS colouring (white / grey / black)."""
    colour: dict[Hashable, int] = {node: 0 for node in graph}
    steps: list[dict] = []

    def visit(node: Hashable, parent_node: Hashable | None) -> bool:
        colour[node] = 1
        steps.append({"action": "enter", "node": node,
                      "description": f"'{node}' grey (on the current path)"})
        for neighbour in graph.get(node, []):
            if colour.get(neighbour, 0) == 1:
                steps.append({"action": "cycle", "node": neighbour,
                              "description": f"'{neighbour}' is grey -> back edge = CYCLE"})
                return True
            if colour.get(neighbour, 0) == 0 and visit(neighbour, node):
                return True
        colour[node] = 2
        steps.append({"action": "exit", "node": node,
                      "description": f"'{node}' black (fully explored)"})
        return False

    found = any(visit(node, None) for node in graph if colour.get(node, 0) == 0)
    return {"algorithm": "DFS cycle detection", "has_cycle": found, "steps": steps}


def _reconstruct(parent: dict[Hashable, Hashable | None], goal: Hashable) -> list[Hashable]:
    path: list[Hashable] = []
    node: Hashable | None = goal
    while node is not None:
        path.append(node)
        node = parent.get(node)
    return list(reversed(path))
