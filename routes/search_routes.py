"""Search, browsing and graph routes."""

from __future__ import annotations

import math
from typing import Any

from flask import Blueprint, current_app, jsonify, render_template, request

from algorithms.bfs import bfs
from algorithms.dfs import dfs
from algorithms.dijkstra import dijkstra
from algorithms.ranking import RANKING_FORMULA, WEIGHT_EXPLANATIONS

bp = Blueprint("search", __name__)

MAX_QUERY_LENGTH = 300
PAGE_SIZE = 8


def service():
    return current_app.extensions["nexasearch"]


def _clean(value: str | None, limit: int = MAX_QUERY_LENGTH) -> str:
    """Trim, collapse whitespace and cap the length of any user string."""
    if not value:
        return ""
    text = " ".join(str(value).split())
    return text[:limit]


@bp.route("/")
def home():
    svc = service()
    return render_template(
        "index.html",
        title="Search",
        query="",
        suggestions=svc.index.autocomplete("", limit=8),
        stats=svc.index.stats(),
        categories=svc.db.categories(),
        recent=svc.db.recent_searches(8),
        top_terms=[term["term"] for term in svc.index.top_terms(10)],
    )


@bp.route("/search")
def search():
    svc = service()
    raw = request.args.get("q", "")
    query = _clean(raw)
    page = max(1, request.args.get("page", 1, type=int) or 1)
    per_page = max(1, min(40, request.args.get("per_page", PAGE_SIZE, type=int) or PAGE_SIZE))
    category = _clean(request.args.get("category", "all"), 60) or "all"
    sort = _clean(request.args.get("sort", "relevance"), 30) or "relevance"
    min_score = request.args.get("min_score", 0.0, type=float) or 0.0

    error = None
    payload: dict[str, Any] = {}
    if query:
        try:
            payload = svc.search(query, page=page, per_page=per_page,
                                  category=category, sort=sort)
            if min_score > 0:
                filtered = [row for row in payload["results"] if row["score"] >= min_score]
                payload["results"] = filtered
                payload["relevance_filter"] = min_score
            svc.db.record_search(
                query=query,
                normalized=payload.get("normalized_query", ""),
                tokens=payload.get("tokens", []),
                result_count=payload.get("total_results", 0),
                documents_searched=payload.get("documents_searched", 0),
                execution_time=payload.get("elapsed_ms", 0.0),
                algorithms=[row["algorithm"] for row in payload.get("algorithms_used", [])],
            )
            if payload.get("results"):
                svc.db.bump_hits([row["doc_id"] for row in payload["results"]])
        except Exception as exc:  # pragma: no cover - defensive, logged to console
            current_app.logger.exception("search failed for %r", query)
            error = f"The search could not be completed: {exc}"
    else:
        error = "Type a search query to begin."

    return render_template(
        "search.html",
        title="Search Results",
        query=query,
        payload=payload,
        error=error,
        categories=svc.db.categories(),
        recent=svc.db.recent_searches(8),
        category=category,
        sort=sort,
        page=page,
        per_page=per_page,
        min_score=min_score,
        formula=RANKING_FORMULA,
        weights=WEIGHT_EXPLANATIONS,
        stats=svc.index.stats(),
    )


@bp.route("/document/<int:doc_id>")
def document(doc_id: int):
    svc = service()
    doc = svc.db.get_document(doc_id)
    if not doc:
        return render_template("error.html", title="Not Found",
                               message="That document does not exist.",
                               code=404), 404
    svc.db.click_document(doc_id)
    node = next((n for n in svc.graph["nodes"] if n["id"] == doc_id), None)
    from indexing.graph_builder import related_documents
    return render_template(
        "document.html",
        title=doc["title"],
        doc=doc,
        node=node,
        related=related_documents(svc.graph, doc_id, limit=6) if svc.graph["nodes"] else [],
        recent=svc.db.recent_searches(6),
    )


@bp.route("/graph")
def graph_page():
    svc = service()
    nodes = svc.graph["nodes"]
    default_start = nodes[0]["id"] if nodes else 0
    goal_ids = [node["id"] for node in nodes if node["id"] != default_start]
    return render_template(
        "graph.html",
        title="Document Graph",
        graph_nodes=nodes,
        edges=svc.graph["edges"],
        stats=svc.graph["stats"],
        pagerank=svc.graph["pagerank"],
        default_start=default_start,
        goal_ids=goal_ids,
        recent=svc.db.recent_searches(6),
    )


@bp.route("/graph/traverse")
def graph_traverse():
    """BFS, DFS and Dijkstra over the document graph - JSON for the viewer."""
    svc = service()
    algorithm = _clean(request.args.get("algorithm", "bfs"), 20).lower()
    if algorithm not in {"bfs", "dfs", "dijkstra"}:
        return jsonify({"error": "algorithm must be bfs, dfs or dijkstra"}), 400
    node_ids = [node["id"] for node in svc.graph["nodes"]]
    if not node_ids:
        return jsonify({"error": "the graph is empty - add documents first"}), 404

    adjacency = svc.graph["adjacency"]
    try:
        start = int(request.args.get("start", node_ids[0]))
    except (TypeError, ValueError):
        start = node_ids[0]
    if start not in svc.graph["adjacency"]:
        start = node_ids[0]

    goal_raw = request.args.get("goal", "")
    goal: int | None = None
    if goal_raw not in ("", "none", "null"):
        try:
            candidate = int(goal_raw)
            goal = candidate if candidate in svc.graph["adjacency"] else None
        except (TypeError, ValueError):
            goal = None

    depth_arg = request.args.get("depth", type=int)
    max_depth = depth_arg if depth_arg and depth_arg > 0 else None
    if algorithm == "bfs":
        result = bfs(adjacency, start, goal, max_depth=max_depth)
    elif algorithm == "dfs":
        result = dfs(adjacency, start, goal, max_depth=max_depth)
    else:
        result = dijkstra(svc.graph["weighted_adjacency"], start, goal)

    titles = {node["id"]: node["title"] for node in svc.graph["nodes"]}
    # Dijkstra settles nodes instead of producing a traversal_order; both are
    # reported as "traversal" so the graph viewer can render either one.
    # Ids stay numeric so the canvas can match them against the node map.
    sequence = result.get("traversal_order") or result.get("settled") or []
    order = [[item, titles.get(item, str(item))] for item in sequence]
    # BFS/DFS name the answer `path_to_goal`, Dijkstra calls it `shortest_path`.
    route = result.get("shortest_path") or result.get("path_to_goal") or []
    path = [[item, titles.get(item, str(item))] for item in route]
    return jsonify({
        "algorithm": result["algorithm"],
        "start": start,
        "goal": goal,
        "traversal": order,
        "levels": [[item for item in level] for level in (result.get("levels") or [])],
        "distances": result.get("distances"),
        "shortest_path": path,
        "shortest_distance": result.get("shortest_distance"),
        "steps": result.get("steps", [])[:400],
        "details": result.get("details", {}),
        "stats": svc.graph["stats"],
    })


@bp.route("/browse")
def browse():
    svc = service()
    page = max(1, request.args.get("page", 1, type=int) or 1)
    category = _clean(request.args.get("category", "all"), 60) or "all"
    sort = _clean(request.args.get("sort", "newest"), 30) or "newest"
    search_term = _clean(request.args.get("q", ""), 120)
    per_page = 10
    documents, total = svc.db.list_documents(
        limit=per_page, offset=(page - 1) * per_page, category=category,
        sort=sort, search=search_term)
    pages = math.ceil(total / per_page) if total else 0
    return render_template(
        "browse.html",
        title="Browse Corpus",
        documents=documents,
        total=total, page=page, pages=pages,
        categories=svc.db.categories(),
        category=category, sort=sort, search_term=search_term,
        recent=svc.db.recent_searches(6),
    )
