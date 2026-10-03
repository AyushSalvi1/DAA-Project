"""Document graph construction (links + weighted similarity).

Two edge sources, both visible to the user on the /graph page:

1. **Explicit links** - a document mentions another by slug in its content
   (this is how the sample corpus cross-references topics).
2. **Similarity edges** - two documents are linked when they share strong
   keywords; the edge weight is the Jaccard / cosine-style overlap, which
   gives Dijkstra something non-uniform to minimise.

The result is an adjacency list for BFS/DFS plus a weighted adjacency list
for Dijkstra, plus the PageRank authority scores.
"""

from __future__ import annotations

import math
import re
from typing import Any

from algorithms.pagerank import pagerank

LINK_RE = re.compile(r"\[\[([a-z0-9\-]+)\]\]", re.IGNORECASE)


def extract_links(content: str) -> list[str]:
    """Find ``[[doc-slug]]`` references inside a document body."""
    if not content:
        return []
    return [match.group(1).lower() for match in LINK_RE.finditer(content)]


def build_graph(documents: list[dict[str, Any]],
                similarity_threshold: float = 0.18) -> dict:
    """Build the unweighted (BFS/DFS) and weighted (Dijkstra) graphs.

    ``documents`` are dicts with ``id``, ``slug``, ``title``, ``category``,
    ``keywords`` and ``content``.
    """
    by_id = {int(doc["id"]): doc for doc in documents}
    by_slug = {str(doc.get("slug") or doc["title"]).lower().replace(" ", "-"): doc
               for doc in documents}

    adjacency: dict[int, list[int]] = {doc_id: [] for doc_id in by_id}
    weights: dict[int, dict[int, float]] = {doc_id: {} for doc_id in by_id}
    edge_sources: list[dict] = []

    # ---------------------------------------------------------- 1. explicit links
    for doc in documents:
        doc_id = int(doc["id"])
        for slug in extract_links(doc.get("content", "")):
            target = by_slug.get(slug)
            if target is None:
                # fall back to matching by id
                try:
                    target = by_id.get(int(slug))
                except (TypeError, ValueError):
                    target = None
            if target is None or int(target["id"]) == doc_id:
                continue
            target_id = int(target["id"])
            if target_id not in adjacency[doc_id]:
                adjacency[doc_id].append(target_id)
                weights[doc_id][target_id] = 1.0
                edge_sources.append({
                    "source": doc_id, "target": target_id, "type": "reference",
                    "weight": 1.0, "label": f"mentions {target['title']}",
                })

    # ------------------------------------------------------- 2. keyword similarity
    keyword_sets = {
        int(doc["id"]): {str(k).lower() for k in (doc.get("keywords") or [])}
        for doc in documents
    }
    ids = sorted(by_id.keys())
    for i, left in enumerate(ids):
        left_set = keyword_sets[left]
        if not left_set:
            continue
        for right in ids[i + 1:]:
            right_set = keyword_sets[right]
            if not right_set:
                continue
            union = left_set | right_set
            if not union:
                continue
            jaccard = len(left_set & right_set) / len(union)
            same_category = by_id[left].get("category") == by_id[right].get("category")
            if same_category:
                jaccard += 0.25
            if jaccard < similarity_threshold:
                continue
            weight = round(min(1.0, jaccard), 4)
            adjacency[left].append(right)
            adjacency[right].append(left)
            weights[left][right] = weight
            weights[right][left] = weight
            edge_sources.append({
                "source": left, "target": right,
                "type": "similarity", "weight": weight,
                "label": f"shares {len(left_set & right_set)} keyword(s)",
            })

    # ------------------------------------------------------------- PageRank
    rank_result = pagerank(adjacency)
    pagerank_scores = {int(node): score for node, score in rank_result["scores"].items()}

    # ---------------------------------------------- weighted adjacency (Dijkstra)
    weighted: dict[int, list[tuple[int, float]]] = {}
    for node in by_id:
        weighted[node] = [(nbr, 2.0 - weights[node][nbr]) for nbr in adjacency[node]]

    return {
        "nodes": [
            {
                "id": doc_id,
                "title": by_id[doc_id]["title"],
                "category": by_id[doc_id].get("category", "Uncategorised"),
                "pagerank": pagerank_scores.get(doc_id, 0.0),
                "in_degree": sum(1 for others in adjacency.values() if doc_id in others),
                "out_degree": len(adjacency[doc_id]),
            }
            for doc_id in ids
        ],
        "adjacency": adjacency,
        "weights": weights,
        "weighted_adjacency": weighted,
        "edges": edge_sources,
        "pagerank": rank_result,
        "stats": {
            "nodes": len(ids),
            "edges": sum(len(v) for v in adjacency.values()),
            "reference_edges": sum(1 for e in edge_sources if e["type"] == "reference"),
            "similarity_edges": sum(1 for e in edge_sources if e["type"] == "similarity"),
            "average_degree": round(sum(len(v) for v in adjacency.values()) / len(ids), 2) if ids else 0,
            "max_pagerank": max(pagerank_scores.values()) if pagerank_scores else 0.0,
            "min_pagerank": min(pagerank_scores.values()) if pagerank_scores else 0.0,
            "pagerank_iterations": rank_result["iterations"],
        },
    }


def related_documents(graph: dict, doc_id: int, limit: int = 5) -> list[dict]:
    """Neighbours ranked by (pagerank + edge weight)."""
    weights = graph["weights"].get(doc_id, {})
    node_lookup = {node["id"]: node for node in graph["nodes"]}
    rows = []
    for neighbour, weight in weights.items():
        node = node_lookup.get(neighbour)
        if not node:
            continue
        rows.append({
            "id": neighbour,
            "title": node["title"],
            "category": node["category"],
            "edge_weight": weight,
            "pagerank": node["pagerank"],
            "similarity": round(math.sqrt(weight * node["pagerank"] / max(1e-9, graph["stats"]["max_pagerank"])), 4),
        })
    rows.sort(key=lambda row: -row["similarity"])
    return rows[:limit]
