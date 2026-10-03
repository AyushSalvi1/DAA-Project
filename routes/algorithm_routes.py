"""Algorithm Lab, analysis dashboard and comparison routes."""

from __future__ import annotations

import random
import time
from time import perf_counter

from flask import Blueprint, current_app, jsonify, render_template, request

from algorithms.binary_search import binary_search, binary_search_recursive
from algorithms.bfs import bfs
from algorithms.dfs import dfs
from algorithms.dijkstra import dijkstra
from algorithms.hash_table import (HashTableChaining, HashTableOpenAddressing,
                                   djb2_hash)
from algorithms.heap import heap_sort
from algorithms.kmp import build_lps, kmp_search, naive_search
from algorithms.merge_sort import merge_sort
from algorithms.quick_sort import quick_sort
from algorithms.rabin_karp import rabin_karp
from algorithms.registry import ALGORITHMS, CATEGORIES, COMPLEXITY_CLASSES, by_category
from algorithms.trie import Trie

bp = Blueprint("algorithms", __name__, url_prefix="/algorithms")

MAX_TEXT = 6000
MAX_ITEMS = 5000

VISUALIZERS = [
    {"id": "binary_search", "name": "Binary Search", "category": "Searching",
     "description": "Halve a sorted array until the target is found or the range collapses.",
     "fields": ["array", "target"]},
    {"id": "kmp", "name": "KMP String Matching", "category": "String Matching",
     "description": "Build the LPS array, then match without ever moving the text pointer back.",
     "fields": ["text", "pattern"]},
    {"id": "rabin_karp", "name": "Rabin-Karp String Matching", "category": "String Matching",
     "description": "Slide a rolling hash window and verify only hash candidates.",
     "fields": ["text", "pattern"]},
    {"id": "trie", "name": "Trie Insert & Prefix Search", "category": "Searching",
     "description": "Insert words character by character, then walk a prefix subtree.",
     "fields": ["words", "prefix"]},
    {"id": "hash", "name": "Hash Table", "category": "Searching",
     "description": "Insert keys, watch collisions appear, compare chaining with linear probing.",
     "fields": ["keys", "probe"]},
    {"id": "bfs", "name": "BFS Traversal", "category": "Graph",
     "description": "Level-by-level traversal of a graph using a FIFO queue.",
     "fields": ["edges", "start"]},
    {"id": "dfs", "name": "DFS Traversal", "category": "Graph",
     "description": "Depth-first traversal with an explicit stack, showing backtracking.",
     "fields": ["edges", "start"]},
    {"id": "dijkstra", "name": "Dijkstra Shortest Path", "category": "Graph",
     "description": "Settle the closest node first using a hand-built binary min-heap.",
     "fields": ["weighted_edges", "start", "goal"]},
    {"id": "merge_sort", "name": "Merge Sort", "category": "Sorting",
     "description": "Split, recurse, then merge two sorted runs.",
     "fields": ["values"]},
    {"id": "quick_sort", "name": "Quick Sort", "category": "Sorting",
     "description": "Partition around a median-of-three pivot and recurse.",
     "fields": ["values"]},
]

SAMPLE_GRAPHS = {
    "bfs": {
        "name": "Six-node social graph",
        "edges": "A-B, A-C, B-D, C-E, D-F, E-F",
    },
    "dijkstra": {
        "name": "Weighted six-node graph",
        "weighted_edges": "A-B:4, A-C:2, B-C:1, B-D:5, C-D:8, C-E:10, D-F:6, E-F:3",
    },
}


def service():
    return current_app.extensions["nexasearch"]


def _timed(func) -> tuple[float, dict]:
    """Run ``func`` and return ``(elapsed_ms, result)``."""
    start = perf_counter()
    result = func()
    return (perf_counter() - start) * 1000, result


def _body(key: str, default: str = "", limit: int = MAX_TEXT) -> str:
    """Read an input from a JSON body, a form post or the query string."""
    raw = (request.get_json(silent=True) or {}).get(key)
    if raw is None:
        raw = request.form.get(key)
    if raw is None:
        raw = request.args.get(key, default)
    if isinstance(raw, (list, tuple)):
        raw = " ".join(str(item) for item in raw)
    return str(raw or "")[:limit]


# ----------------------------------------------------------------------
# pages
# ----------------------------------------------------------------------
@bp.route("/")
def algorithms_dashboard():
    svc = service()
    grouped = by_category()
    return render_template(
        "algorithms.html",
        title="Algorithm Analysis",
        algorithms=ALGORITHMS,
        grouped=grouped,
        categories=CATEGORIES,
        complexity_classes=COMPLEXITY_CLASSES,
        index_stats=svc.index.stats(),
        graph_stats=svc.graph["stats"],
        tfidf_stats=svc.tfidf.stats(),
        pagerank=svc.graph["pagerank"],
        recent=svc.db.recent_searches(6),
    )


@bp.route("/visualizer")
def visualizer():
    svc = service()
    return render_template(
        "visualizer.html",
        title="Algorithm Lab",
        visualizers=VISUALIZERS,
        selected=_safe_choice(request.args.get("algo", "kmp")),
        index_stats=svc.index.stats(),
        recent=svc.db.recent_searches(6),
    )


@bp.route("/complexity")
def complexity():
    svc = service()
    sizes = [10, 100, 1000, 10000, 100000]
    series = []
    for n in sizes:
        series.append({
            "n": n,
            "O(1)": 1,
            "O(log n)": max(1, n.bit_length()),
            "O(n)": n,
            "O(n log n)": n * max(1, n.bit_length()),
            "O(n^2)": n * n,
            "O(2^n)": math_pow2(n),
        })
    return render_template(
        "complexity.html",
        title="Complexity Explorer",
        complexity_classes=COMPLEXITY_CLASSES,
        series=series,
        algorithms=ALGORITHMS,
        index_stats=svc.index.stats(),
        recent=svc.db.recent_searches(6),
    )


def math_pow2(n: int) -> float:
    """Clamped 2^n so the chart stays renderable for n = 100000."""
    if n > 64:
        return 1.8e19
    return float(2 ** n)


def _safe_choice(value: str | None) -> str:
    allowed = {entry["id"] for entry in VISUALIZERS}
    return value if value in allowed else "kmp"


# ----------------------------------------------------------------------
# lab endpoints
# ----------------------------------------------------------------------
@bp.post("/lab/<algorithm>")
def run_lab(algorithm: str):
    """Execute one visualizer with user-supplied input."""
    if algorithm not in {entry["id"] for entry in VISUALIZERS}:
        return jsonify({"error": f"unknown algorithm '{algorithm}'",
                        "valid": [entry["id"] for entry in VISUALIZERS]}), 400
    try:
        handler = {
            "binary_search": _lab_binary_search,
            "kmp": _lab_kmp,
            "rabin_karp": _lab_rabin_karp,
            "trie": _lab_trie,
            "hash": _lab_hash,
            "bfs": _lab_bfs,
            "dfs": _lab_dfs,
            "dijkstra": _lab_dijkstra,
            "merge_sort": _lab_merge_sort,
            "quick_sort": _lab_quick_sort,
        }[algorithm]
        payload = handler()
        payload.setdefault("algorithm", algorithm)
        return jsonify(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # pragma: no cover - defensive
        current_app.logger.exception("visualizer %s failed", algorithm)
        return jsonify({"error": f"{type(exc).__name__}: {exc}"}), 500


def _parse_int_list(raw: str, limit: int = 40) -> list[int]:
    tokens = [t for t in raw.replace(",", " ").split() if t]
    if not tokens:
        raise ValueError("Provide at least one number.")
    if len(tokens) > limit:
        raise ValueError(f"At most {limit} numbers are allowed.")
    values = []
    for token in tokens:
        try:
            values.append(int(token))
        except ValueError:
            try:
                values.append(int(round(float(token))))
            except ValueError as exc:
                raise ValueError(f"'{token}' is not a number.") from exc
    return values


def _lab_binary_search() -> dict:
    values = _parse_int_list(_body("array", "11 22 33 44 55 66 77 88 99"))
    values.sort()
    target_raw = _body("target", "55", 40)
    try:
        target = int(target_raw)
    except ValueError:
        raise ValueError("Target must be an integer.")
    result = binary_search(values, target)
    recursive = binary_search_recursive(values, target)
    return {
        "title": "Binary Search",
        "input": {"array": values, "target": target},
        "found": result["found"],
        "index": result["index"],
        "comparisons": result["comparisons"],
        "time_ms": round(result["time_ms"], 4),
        "steps": result["steps"],
        "recursive_comparisons": recursive["comparisons"],
        "recursive_depth": recursive.get("max_recursion_depth", 0),
        "complexity": {"time": "O(log n)", "space": "O(1) iterative / O(log n) recursive",
                       "best": "O(1)", "average": "O(log n)", "worst": "O(log n)"},
        "explanation": (
            f"The array of {len(values)} sorted values needs at most "
            f"{max(1, len(values).bit_length())} probes. Each probe discards half the range, "
            "so the number of steps grows logarithmically, not linearly."),
    }


def _lab_kmp() -> dict:
    text = _body("text", "ABABDABACDABABCABAB")
    pattern = _body("pattern", "ABABCABAB")
    if not text:
        raise ValueError("Text cannot be empty.")
    if not pattern:
        raise ValueError("Pattern cannot be empty.")
    lps, lps_steps = build_lps(pattern)
    result = kmp_search(text, pattern)
    naive = naive_search(text, pattern)
    return {
        "title": "Knuth-Morris-Pratt",
        "input": {"text": text, "pattern": pattern},
        "matches": result["matches"],
        "match_count": result["match_count"],
        "comparisons": result["comparisons"],
        "lps": lps,
        "lps_steps": lps_steps,
        "steps": result["steps"][:500],
        "time_ms": round(result["time_ms"], 4),
        "naive_comparisons": naive["comparisons"],
        "naive_time_ms": round(naive["time_ms"], 4),
        "complexity": {"time": "O(n + m)", "space": "O(m)", "best": "O(n)",
                       "average": "O(n + m)", "worst": "O(n + m)"},
        "explanation": (
            f"KMP made {result['comparisons']} character comparisons; the naive matcher needed "
            f"{naive['comparisons']}. The LPS array is the reason: after a mismatch at pattern "
            f"position j the matcher jumps to lps[j-1] instead of restarting the text scan."),
    }


def _lab_rabin_karp() -> dict:
    text = _body("text", "ABABDABACDABABCABAB")
    pattern = _body("pattern", "ABABCABAB")
    if not text or not pattern:
        raise ValueError("Both text and pattern are required.")
    result = rabin_karp(text, pattern)
    kmp_result = kmp_search(text, pattern)
    return {
        "title": "Rabin-Karp (rolling hash)",
        "input": {"text": text, "pattern": pattern},
        "matches": result["matches"],
        "match_count": result["match_count"],
        "hash_comparisons": result["hash_comparisons"],
        "char_comparisons": result["char_comparisons"],
        "collisions": result["collisions"],
        "pattern_hash": result["pattern_hash"],
        "steps": result["steps"][:400],
        "time_ms": round(result["time_ms"], 4),
        "agrees_with_kmp": result["matches"] == kmp_result["matches"],
        "complexity": {"time": "O(n + m) average, O(n*m) worst", "space": "O(1) auxiliary",
                       "best": "O(n)", "average": "O(n + m)", "worst": "O(n*m)"},
        "explanation": (
            f"The window hash is updated in O(1) per slide. {result['hash_comparisons']} hash "
            f"comparisons filtered the text down to {result['char_comparisons']} character "
            f"comparisons; {result['collisions']} false positive(s) were caught by verification. "
            f"KMP agrees: {result['matches'] == kmp_result['matches']}."),
    }


def _lab_trie() -> dict:
    raw = _body("words", "machine machine learning machine vision algorithm algorithms "
                         "graph graphs network", 600)
    words = [w.strip().lower() for w in raw.replace(",", " ").split() if w.strip()]
    if not words:
        raise ValueError("Provide at least one word to insert.")
    if len(words) > 60:
        raise ValueError("At most 60 words per run.")
    trie = Trie()
    traces = [trie.insert_trace(word) for word in dict.fromkeys(words)]
    prefix = _body("prefix", words[0][:3] if words else "a", 40).lower().strip()
    suggestions = trie.autocomplete(prefix, limit=10) if prefix else []
    return {
        "title": "Trie (prefix tree)",
        "input": {"words": words, "prefix": prefix},
        "suggestions": [row["word"] for row in suggestions],
        "suggestion_detail": suggestions,
        "steps": [step for trace in traces[:6] for step in trace["steps"]][:400],
        "insert_traces": [{"word": trace["word"], "time_ms": round(trace["time_ms"], 5)}
                          for trace in traces[:12]],
        "stats": trie.stats(),
        "tree": trie.to_dict(),
        "time_ms": round(sum(trace["time_ms"] for trace in traces), 4),
        "complexity": {"time": "O(L) insert / O(L) search / O(L + P) prefix",
                       "space": "O(total characters)", "best": "O(L)", "average": "O(L)",
                       "worst": "O(L)"},
        "explanation": (
            f"{len(dict.fromkeys(words))} words produced {trie.stats()['nodes']} nodes "
            f"(shared prefixes reuse nodes). Lookup for the prefix '{prefix}' returned "
            f"{len(suggestions)} suggestion(s) in cost O(L + P) - P being the explored subtree."),
    }


def _lab_hash() -> dict:
    raw = _body("keys", "algorithm, algorithm, hash, trie, search, index, query, rank",
                400)
    keys = [k.strip().lower() for k in raw.replace(",", " ").split() if k.strip()]
    if not keys:
        raise ValueError("Provide at least one key.")
    if len(keys) > 40:
        raise ValueError("At most 40 keys per run.")

    capacity = max(4, min(16, len(keys)))
    chaining = HashTableChaining(capacity)
    open_table = HashTableOpenAddressing(capacity)
    steps = []
    for key in dict.fromkeys(keys):
        steps.append(chaining.put(key, True))
    for key in dict.fromkeys(keys):
        open_table.put(key, True)

    probe = _body("probe", keys[0], 40).lower().strip() or keys[0]
    hash_value = djb2_hash(probe)
    return {
        "title": "Hash Table",
        "input": {"keys": keys, "capacity": capacity, "probe": probe},
        "hash_value": hash_value,
        "bucket": hash_value % capacity,
        "steps": [step for trace in steps[:6] for step in trace["steps"]][:400],
        "chaining": {
            "snapshot": chaining.snapshot(),
            "stats": chaining.stats(),
        },
        "open_addressing": {
            "snapshot": open_table.snapshot(),
            "stats": open_table.stats(),
        },
        "lookup": {
            "chaining": chaining.contains(probe),
            "open_addressing": open_table.contains(probe),
        },
        "time_ms": round(sum(step.get("time_ms", 0.0) for step in steps), 4),
        "complexity": {"time": "O(1) average", "space": "O(n)",
                       "best": "O(1)", "average": "O(1)", "worst": "O(n) - all keys collide"},
        "explanation": (
            f"djb2('{probe}') = {hash_value}, bucket = {hash_value} % {capacity} = "
            f"{hash_value % capacity}. Chaining reported {chaining.stats()['collisions']} "
            f"collision(s) with max chain length {chaining.stats()['max_chain_length']}; "
            f"open addressing reported {open_table.stats()['collisions']} probe(s) with "
            f"{open_table.stats()['rehashes']} rehash(es)."),
    }


def _parse_graph_edges(raw: str) -> tuple[list[str], list[tuple[str, int, int]]]:
    """Accept 'A-B, B-C' or a JSON-ish 'A-B:3' for weighted graphs."""
    nodes: list[str] = []
    edges: list[tuple[str, int, int]] = []
    seen: set[str] = set()

    def add(node: str) -> int:
        node = node.strip()
        if node and node not in seen:
            seen.add(node)
            nodes.append(node)
        return nodes.index(node) if node in nodes else -1

    for chunk in raw.replace("\n", ",").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        weight = 1.0
        if ":" in chunk:
            chunk, weight_raw = chunk.split(":", 1)
            try:
                weight = float(weight_raw)
            except ValueError:
                weight = 1.0
        if "-" in chunk:
            left, right = chunk.split("-", 1)
        else:
            continue
        source, target = add(left), add(right)
        if source < 0 or target < 0 or source == target:
            continue
        edges.append((left.strip(), right.strip(), weight))
    return nodes, edges


def _lab_bfs() -> dict:
    raw = _body("edges", SAMPLE_GRAPHS["bfs"]["edges"])
    nodes, edges = _parse_graph_edges(raw)
    if len(nodes) < 2:
        raise ValueError("Provide edges like 'A-B, B-C, C-D'.")
    adjacency: dict[str, list[str]] = {node: [] for node in nodes}
    for left, right, _ in edges:
        adjacency[left].append(right)
        adjacency[right].append(left)
    start = _body("start", nodes[0], 20) or nodes[0]
    if start not in adjacency:
        start = nodes[0]
    clock = time.perf_counter()
    result = bfs(adjacency, start)
    elapsed = (time.perf_counter() - clock) * 1000
    return {
        "title": "Breadth-First Search",
        "input": {"nodes": nodes, "edges": [[l, r] for l, r, _ in edges], "start": start},
        "traversal": result["traversal_order"],
        "levels": result["levels"],
        "steps": result["steps"][:400],
        "edge_examinations": result["edge_examinations"],
        "time_ms": round(elapsed, 4),
        "complexity": {"time": "O(V + E)", "space": "O(V)", "best": "O(V)",
                       "average": "O(V + E)", "worst": "O(V + E)"},
        "explanation": (
            f"The FIFO queue produced levels {result['levels']}. Each vertex is enqueued once "
            f"and each edge examined twice, so the traversal is O(V + E) = "
            f"O({len(nodes)} + {len(edges)})."),
    }


def _lab_dfs() -> dict:
    raw = _body("edges", SAMPLE_GRAPHS["bfs"]["edges"])
    nodes, edges = _parse_graph_edges(raw)
    if len(nodes) < 2:
        raise ValueError("Provide edges like 'A-B, B-C, C-D'.")
    adjacency: dict[str, list[str]] = {node: [] for node in nodes}
    for left, right, _ in edges:
        adjacency[left].append(right)
        adjacency[right].append(left)
    start = _body("start", nodes[0], 20) or nodes[0]
    if start not in adjacency:
        start = nodes[0]
    mode = "recursive" if _body("mode", "iterative", 20) == "recursive" else "iterative"
    clock = time.perf_counter()
    result = dfs(adjacency, start, mode=mode)
    elapsed = (time.perf_counter() - clock) * 1000
    max_depth = result["details"].get("max_call_depth") or result["details"].get("nodes_visited", 0)
    return {
        "title": "Depth-First Search",
        "input": {"nodes": nodes, "edges": [[l, r] for l, r, _ in edges],
                  "start": start, "mode": mode},
        "traversal": result["traversal_order"],
        "steps": result["steps"][:400],
        "edge_examinations": result["edge_examinations"],
        "details": result["details"],
        "time_ms": round(elapsed, 4),
        "complexity": {"time": "O(V + E)", "space": "O(V)", "best": "O(V)",
                       "average": "O(V + E)", "worst": "O(V + E)"},
        "explanation": (
            f"The {'call stack' if mode == 'recursive' else 'LIFO stack'} forced the traversal "
            f"order {result['traversal_order']}. DFS descended {max_depth} level(s) deep and, "
            "unlike BFS, does not guarantee a shortest path."),
    }


def _lab_dijkstra() -> dict:
    raw = _body("weighted_edges", SAMPLE_GRAPHS["dijkstra"]["weighted_edges"])
    nodes, edges = _parse_graph_edges(raw)
    if len(nodes) < 2:
        raise ValueError("Provide edges like 'A-B:4, B-C:1'.")
    weighted: dict[str, list[tuple[str, float]]] = {node: [] for node in nodes}
    for left, right, weight in edges:
        if weight < 0:
            raise ValueError("Dijkstra requires non-negative edge weights.")
        weighted[left].append((right, weight))
        weighted[right].append((left, weight))
    start = _body("start", nodes[0], 20) or nodes[0]
    if start not in weighted:
        start = nodes[0]
    goal_raw = _body("goal", nodes[-1], 20)
    goal = goal_raw if goal_raw in weighted else None
    clock = time.perf_counter()
    result = dijkstra(weighted, start, goal)
    elapsed = (time.perf_counter() - clock) * 1000
    return {
        "title": "Dijkstra's Algorithm",
        "input": {"nodes": nodes, "edges": [[l, r, w] for l, r, w in edges],
                  "start": start, "goal": goal},
        "steps": result["steps"][:400],
        "distances": result["distances"],
        "shortest_path": result["shortest_path"],
        "shortest_distance": result["shortest_distance"],
        "settled": result["settled"],
        "relaxations": result["relaxations"],
        "heap_comparisons": result["heap_comparisons"],
        "time_ms": round(elapsed, 4),
        "complexity": {"time": "O((V + E) log V)", "space": "O(V)", "best": "O((V + E) log V)",
                       "average": "O((V + E) log V)", "worst": "O((V + E) log V)"},
        "explanation": (
            f"{result['relaxations']} relaxation(s) improved a distance and the custom binary "
            f"min-heap performed {result['heap_comparisons']} comparison(s). Settling order: "
            f"{result['settled']}."),
    }


def _lab_merge_sort() -> dict:
    values = _parse_int_list(_body("values", "38 27 43 3 9 82 10 55 1 25"), 60)
    result = merge_sort(values, trace=True)
    return {
        "title": "Merge Sort",
        "input": {"values": values},
        "sorted": result["sorted"],
        "steps": result["steps"][:400],
        "comparisons": result["comparisons"],
        "time_ms": round(result["time_ms"], 4),
        "complexity": {"time": "Theta(n log n)", "space": "Theta(n)", "best": "Theta(n log n)",
                       "average": "Theta(n log n)", "worst": "Theta(n log n)"},
        "explanation": (
            f"{result['comparisons']} comparison(s) merged {len(values)} values. Because the "
            "split is always even, every level costs Theta(n) and there are log n levels, so "
            "the bound holds for sorted, reversed and random input alike."),
    }


def _lab_quick_sort() -> dict:
    values = _parse_int_list(_body("values", "38 27 43 3 9 82 10 55 1 25"), 60)
    result = quick_sort(values, trace=True)
    return {
        "title": "Quick Sort",
        "input": {"values": values},
        "sorted": result["sorted"],
        "steps": result["steps"][:400],
        "comparisons": result["comparisons"],
        "partitions": result["partitions"],
        "max_depth": result["max_recursion_depth"],
        "time_ms": round(result["time_ms"], 4),
        "complexity": {"time": "Theta(n log n) average, Theta(n^2) worst", "space": "O(log n)",
                       "best": "Theta(n log n)", "average": "Theta(n log n)", "worst": "Theta(n^2)"},
        "explanation": (
            f"{result['partitions']} partition step(s), {result['comparisons']} comparison(s), "
            f"maximum pivot depth {result['max_recursion_depth']}. Median-of-three pivoting keeps already "
            "sorted input in the balanced case instead of degrading to Theta(n^2)."),
    }


# ----------------------------------------------------------------------
# benchmarks and comparisons
# ----------------------------------------------------------------------
@bp.post("/benchmark")
def benchmark():
    from core.benchmark import (benchmark_graph, benchmark_searching,
                               benchmark_sorting, benchmark_string_matching)
    kind = (_body("kind", "all", 30) or "all").lower()
    svc = service()
    payload: dict = {}
    if kind in ("all", "searching"):
        payload["searching"] = benchmark_searching()
    if kind in ("all", "string"):
        payload["string_matching"] = benchmark_string_matching()
    if kind in ("all", "sorting"):
        payload["sorting"] = benchmark_sorting()
    if kind in ("all", "graph"):
        payload["graph"] = benchmark_graph()
    if not payload:
        return jsonify({"error": f"unknown benchmark kind '{kind}'"}), 400

    saved = 0
    try:
        if "searching" in payload:
            for row in payload["searching"]["rows"]:
                svc.db.save_benchmark("searching", row["algorithm"], row["input_size"],
                                      row["time_ms"], row["comparisons"], row["case"])
                saved += 1
        if "sorting" in payload:
            for row in payload["sorting"]["rows"]:
                svc.db.save_benchmark("sorting", "Merge Sort", row["input_size"],
                                      row["merge_ms"], row["merge_comparisons"])
                svc.db.save_benchmark("sorting", "Quick Sort", row["input_size"],
                                      row["quick_ms"], row["quick_comparisons"])
                saved += 2
        if "string_matching" in payload:
            for row in payload["string_matching"]["rows"]:
                svc.db.save_benchmark("string_matching", "KMP", row["text_length"],
                                      row["kmp_ms"], row["kmp_comparisons"])
                svc.db.save_benchmark("string_matching", "Rabin-Karp", row["text_length"],
                                      row["rk_ms"], row["rk_comparisons"])
                saved += 2
    except Exception:  # pragma: no cover - persistence is best-effort
        current_app.logger.exception("could not persist benchmarks")
    payload["saved_rows"] = saved
    payload["generated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    return jsonify(payload)


@bp.post("/compare/string")
def compare_string():
    svc = service()
    text = _body("text", "the quick brown fox jumps over the lazy dog the fox is quick")
    pattern = _body("pattern", "quick", 100)
    if not pattern:
        return jsonify({"error": "A pattern is required."}), 400
    return jsonify(svc.engine.compare_string_matching(text, pattern))


@bp.post("/compare/search")
def compare_search():
    svc = service()
    term = _body("term", "algorithm", 60) or "algorithm"
    return jsonify(svc.engine.compare_search_strategies(term))


@bp.post("/tfidf")
def tfidf_report():
    svc = service()
    terms = [t for t in _body("terms", "algorithm, machine, graph, security, python").split(",")
             if t.strip()]
    from indexing.text_processor import stem
    normalised = [stem(t.strip().lower()) for t in terms][:12]
    report = svc.tfidf.term_report(normalised)
    query = _body("query", " ".join(terms), MAX_TEXT)
    from indexing.text_processor import analyze
    scored = svc.tfidf.score_query(analyze(query)["tokens"])[:12]
    titles = {int(doc["id"]): doc["title"] for doc in svc.db.all_documents()}
    return jsonify({
        "terms": report,
        "query": query,
        "scores": [{"doc_id": row["doc_id"],
                    "title": titles.get(row["doc_id"], ""),
                    "score": row["tfidf_score"],
                    "matched": row["matched_terms"]} for row in scored],
        "formula": {
            "tf": "TF(t,d) = count(t in d) / total tokens in d",
            "idf": "IDF(t) = ln((1 + N) / (1 + df(t))) + 1",
            "tfidf": "TFIDF(t,d) = TF(t,d) * IDF(t)",
            "similarity": "score(d, q) = cosine( TFIDF(d), TFIDF(q) )",
        },
        "stats": svc.tfidf.stats(),
    })


@bp.post("/sort-benchmark")
def sort_benchmark():
    def option(key, default=None):
        raw = _body(key, "" if default is None else str(default), 40)
        return raw if raw != "" else default

    try:
        n = int(option("size", 2000))
    except (TypeError, ValueError):
        n = 2000
    n = max(10, min(20000, n))
    pattern = (option("pattern", "random") or "random").lower()
    rng = random.Random(1234)
    if pattern == "sorted":
        data = sorted(rng.randrange(1_000_000) for _ in range(n))
    elif pattern == "reversed":
        data = sorted((rng.randrange(1_000_000) for _ in range(n)), reverse=True)
    else:
        data = [rng.randrange(1_000_000) for _ in range(n)]

    merge = merge_sort(data)
    quick = quick_sort(data)
    heap_ms, heap = _timed(lambda: heap_sort(data))
    return jsonify({
        "size": n, "pattern": pattern,
        "merge": {"ms": round(merge["time_ms"], 4), "comparisons": merge["comparisons"]},
        "quick": {"ms": round(quick["time_ms"], 4), "comparisons": quick["comparisons"],
                  "partitions": quick["partitions"], "depth": quick["max_recursion_depth"]},
        "heap": {"ms": round(heap_ms, 4), "comparisons": heap["comparisons"]},
        "all_correct": merge["sorted"] == quick["sorted"] == heap["sorted"],
    })
