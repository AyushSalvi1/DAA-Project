"""PageRank - Google's link-analysis ranking, implemented from scratch.

DAA facts
---------
Model: a random surfer.  With probability ``d`` (damping, 0.85) the surfer
follows a random outgoing link, with probability ``1-d`` it teleports to a
uniformly random page.  Let P be the probability distribution over pages::

    P(t+1) = d * SUM_over_pages_i ( P(t,i) * OutDegree(i)^-1 * M[i][j] )
             + (1 - d) / N

Implementation: the dense matrix formulation is O(N^2) per iteration
(useless for a real web), so we use the **edge-list** formulation which is
O(E) per iteration - the same sum, but iterating over edges instead of
scanning an N x N matrix.  Convergence is detected with the L1 norm
difference between successive iterations.

Complexity: O(I * (V + E)) time for I iterations, O(V + E) space.
Convergence is checked against an L1 tolerance of 1e-6.  The power iteration
shrinks the error by roughly the damping factor per pass, so a few tens of
iterations usually suffice; the cap of 200 keeps a pathological graph bounded
while staying O(1) work per edge.

Why it belongs in a search engine: it measures *authority*, which is
independent of the query, so it can be pre-computed once and cached.  We
combine it as the "graph" signal in algorithms/ranking.py.
"""

from __future__ import annotations

from typing import Hashable


def pagerank(adjacency: dict[Hashable, list[Hashable]], damping: float = 0.85,
             iterations: int = 200, tolerance: float = 1e-6) -> dict:
    """Compute PageRank over an unweighted adjacency list."""
    nodes = sorted(adjacency.keys(), key=str)
    n = len(nodes)
    if n == 0:
        return {"algorithm": "PageRank", "scores": {}, "iterations": 0,
                "history": [], "converged": False, "damping": damping,
                "ranking": [], "top_score": 0.0, "min_score": 0.0,
                "total_nodes": 0, "total_edges": 0,
                "details": {"note": "Empty graph - no scores to compute."}}

    index = {node: i for i, node in enumerate(nodes)}
    out_degree = {node: len([nb for nb in adjacency[node] if nb in index]) for node in nodes}

    # dangling nodes (no outgoing edges) redistribute their mass to everyone
    rank = {node: 1.0 / n for node in nodes}
    history: list[dict] = []
    converged = False
    used_iterations = 0

    for iteration in range(1, iterations + 1):
        used_iterations = iteration
        dangling_mass = sum(rank[node] for node in nodes if out_degree[node] == 0)
        base = (1.0 - damping) / n + damping * dangling_mass / n
        new_rank = {node: base for node in nodes}

        # O(E) edge-list scatter instead of an O(V^2) matrix multiply
        for node in nodes:
            degree = out_degree[node]
            if degree == 0:
                continue
            share = damping * rank[node] / degree
            for neighbour in adjacency[node]:
                if neighbour in new_rank:
                    new_rank[neighbour] += share

        delta = sum(abs(new_rank[node] - rank[node]) for node in nodes)
        rank = new_rank
        history.append({
            "iteration": iteration,
            "delta": round(delta, 10),
            "top": [{"node": str(k), "score": round(v, 6)}
                    for k, v in sorted(rank.items(), key=lambda item: -item[1])[:5]],
        })
        if delta < tolerance:
            converged = True
            break

    ranked = sorted(rank.items(), key=lambda item: (-item[1], str(item[0])))
    return {
        "algorithm": "PageRank",
        "damping": damping,
        "iterations": used_iterations,
        "converged": converged,
        # Full precision here on purpose: a rounded score per node would make
        # the scores sum to 1 only up to n * 5e-7, which shows up as a fake
        # "PageRank does not converge" observation.
        "scores": {str(node): score for node, score in rank.items()},
        "ranking": [{"node": str(node), "score": round(score, 6)} for node, score in ranked],
        "top_score": ranked[0][1] if ranked else 0.0,
        "min_score": ranked[-1][1] if ranked else 0.0,
        "total_nodes": n,
        "total_edges": sum(out_degree.values()),
        "history": history,
        "details": {
            "note": f"Converged in {used_iterations} iterations "
                    f"(L1 delta < {tolerance}). Cost O(I*(V+E)) = "
                    f"O({used_iterations} * ({n} + {sum(out_degree.values())})).",
        },
    }


def hub_scores(pagerank_result: dict, top_n: int = 10) -> list[dict]:
    return pagerank_result.get("ranking", [])[:top_n]


def authority_labels(scores: dict[str, float]) -> dict[str, str]:
    """Bucket documents into readable authority tiers for the UI."""
    if not scores:
        return {}
    values = sorted(scores.values(), reverse=True)
    top = values[0] or 1.0
    labels = {}
    for node, score in scores.items():
        relative = score / top
        if relative >= 0.8:
            labels[node] = "hub"
        elif relative >= 0.5:
            labels[node] = "well-linked"
        elif relative >= 0.2:
            labels[node] = "normal"
        else:
            labels[node] = "peripheral"
    return labels
