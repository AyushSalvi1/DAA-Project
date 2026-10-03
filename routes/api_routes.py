"""JSON API consumed by the front-end (autocomplete, AJAX, visualizers)."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from indexing.graph_builder import related_documents

bp = Blueprint("api", __name__, url_prefix="/api")


def service():
    return current_app.extensions["nexasearch"]


def _int(value, default, low, high):
    try:
        return max(low, min(high, int(value)))
    except (TypeError, ValueError):
        return default


@bp.get("/autocomplete")
def autocomplete():
    svc = service()
    prefix = str(request.args.get("q", ""))[:60]
    limit = _int(request.args.get("limit", 8), 8, 1, 20)
    if not prefix:
        return jsonify({"prefix": "", "suggestions": []})
    return jsonify({"prefix": prefix, "suggestions": svc.index.autocomplete(prefix, limit)})


@bp.get("/search")
def api_search():
    svc = service()
    query = str(request.args.get("q", ""))[:300]
    if not query.strip():
        return jsonify({"error": "empty query", "results": []}), 400
    page_size = request.args.get("per_page", request.args.get("limit", 8))
    payload = svc.search(
        query,
        page=_int(request.args.get("page", 1), 1, 1, 500),
        per_page=_int(page_size, 8, 1, 50),
        category=str(request.args.get("category", "all"))[:60],
        sort=str(request.args.get("sort", "relevance"))[:30],
    )
    svc.db.record_search(
        query=query, normalized=payload.get("normalized_query", ""),
        tokens=payload.get("tokens", []),
        result_count=payload.get("total_results", 0),
        documents_searched=payload.get("documents_searched", 0),
        execution_time=payload.get("elapsed_ms", 0.0),
        algorithms=[row["algorithm"] for row in payload.get("algorithms_used", [])],
    )
    return jsonify(payload)


@bp.get("/document/<int:doc_id>")
def api_document(doc_id: int):
    svc = service()
    doc = svc.db.get_document(doc_id)
    if not doc:
        return jsonify({"error": "not found"}), 404
    doc = dict(doc)
    doc["pagerank"] = next((n["pagerank"] for n in svc.graph["nodes"] if n["id"] == doc_id), 0.0)
    doc["related"] = [
        {"id": row["id"], "title": row["title"], "category": row["category"]}
        for row in related_documents(svc.graph, doc_id, 5)
    ]
    return jsonify(doc)


@bp.get("/stats")
def api_stats():
    return jsonify(service().dashboard())


@bp.get("/index")
def api_index():
    svc = service()
    return jsonify({
        "index": svc.index.stats(),
        "graph": svc.graph["stats"],
        "tfidf": svc.tfidf.stats(),
        "hash_table": svc.index.term_postings.stats(),
        "trie": svc.index.trie.stats(),
        "last_rebuild": svc.last_rebuild,
    })


@bp.get("/history")
def api_history():
    svc = service()
    limit = _int(request.args.get("limit", 10), 10, 1, 50)
    return jsonify({"history": svc.db.recent_searches(limit)})


@bp.get("/terms")
def api_terms():
    svc = service()
    limit = _int(request.args.get("limit", 20), 20, 1, 100)
    prefix = str(request.args.get("prefix", request.args.get("q", "")))[:60].strip()
    if prefix:
        return jsonify({"prefix": prefix.lower(),
                        "terms": svc.index.terms_with_prefix(prefix, limit)})
    return jsonify({"prefix": "", "terms": svc.index.top_terms(limit)})


@bp.get("/categories")
def api_categories():
    return jsonify({"categories": service().db.categories()})


@bp.get("/health")
def health():
    svc = service()
    try:
        svc.db.scalar("SELECT 1")
        database_ok = True
    except Exception:
        database_ok = False
    status = 200 if database_ok else 503
    return jsonify({
        "status": "ok" if database_ok else "degraded",
        "database": database_ok,
        "documents": svc.index.stats()["documents"],
        "terms": svc.index.stats()["unique_terms"],
        "last_rebuild": svc.last_rebuild,
    }), status
