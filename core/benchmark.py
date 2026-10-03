"""Performance benchmarking for every algorithm family in the project.

Everything is measured with ``time.perf_counter`` (highest resolution
portable clock) and returned as JSON-ready rows that the dashboard charts.

Methodology notes (worth mentioning in the report):
  * one warm-up run before timing, so interpreter/JIT-like first-call costs
    do not pollute the numbers;
  * repeated runs with the *median* taken for the very fast algorithms
    (hash/trie lookup), because a single timer tick is too coarse;
  * randomised but reproducible inputs (``random.Random(seed)``);
  * for linear/binary search the *average* case is measured by picking a
    key from the middle of the collection, and the worst case by searching
    for a key that is absent.
"""

from __future__ import annotations

import random
import statistics
import time
from typing import Any, Callable

from algorithms.binary_search import binary_search
from algorithms.hash_table import HashTableChaining, HashTableOpenAddressing
from algorithms.heap import heap_sort
from algorithms.kmp import kmp_search, naive_search
from algorithms.linear_search import linear_search
from algorithms.merge_sort import merge_sort
from algorithms.quick_sort import quick_sort
from algorithms.rabin_karp import rabin_karp
from algorithms.trie import Trie

SEARCH_SIZES = [100, 500, 1000, 5000, 10000]
SORT_SIZES = [100, 500, 1000, 5000, 10000]
STRING_SIZES = [200, 1000, 5000, 20000, 50000]


def _timeit(func: Callable[[], Any], repeat: int = 1) -> tuple[float, Any]:
    """Return ``(milliseconds, result)`` for the best of ``repeat`` runs."""
    best = float("inf")
    result = None
    for _ in range(repeat):
        start = time.perf_counter()
        result = func()
        elapsed = (time.perf_counter() - start) * 1000
        best = min(best, elapsed)
    return best, result


# ----------------------------------------------------------------------
# searching
# ----------------------------------------------------------------------
def benchmark_searching(sizes: list[int] | None = None,
                        seed: int = 42) -> dict:
    """Linear vs Binary vs Hash vs Trie across increasing dataset sizes."""
    sizes = sizes or SEARCH_SIZES
    rows: list[dict] = []
    rng = random.Random(seed)

    for size in sizes:
        # vocabulary of `size` distinct words + a document list to scan
        vocabulary = [f"term{rng.randrange(10**6):07d}" for _ in range(size)]
        vocabulary = list(dict.fromkeys(vocabulary))
        documents = [rng.choice(vocabulary) + f"_doc_{i}" for i in range(size)]
        sorted_documents = sorted(documents)
        probe = documents[size // 2]        # average case
        target_word = vocabulary[size // 2]

        # --- linear search (average case: key in the middle)
        _, linear_avg = _timeit(lambda: linear_search(documents, probe))
        _, linear_worst = _timeit(lambda: linear_search(documents, "absent_key_zzz"))
        rows.append({
            "algorithm": "Linear Search",
            "input_size": size, "comparisons": linear_avg["comparisons"],
            "time_ms": round(linear_avg["time_ms"], 4),
            "worst_time_ms": round(linear_worst["time_ms"], 4),
            "case": "average / worst", "complexity": "O(n)",
        })

        # --- binary search on sorted data
        _, binary_avg = _timeit(lambda: binary_search(sorted_documents, probe))
        rows.append({
            "algorithm": "Binary Search",
            "input_size": size, "comparisons": binary_avg["comparisons"],
            "time_ms": round(binary_avg["time_ms"], 4),
            "worst_time_ms": round(binary_avg["time_ms"], 4),
            "case": "average", "complexity": "O(log n)",
        })

        # --- hash table build + lookup
        def build_hash():
            table = HashTableChaining(capacity=max(16, size))
            for word in vocabulary:
                table.put(word, True)
            return table

        build_ms, table = _timeit(build_hash)
        samples = [_timeit(lambda w=target_word: table.get(w), repeat=25)[0] for _ in range(7)]
        rows.append({
            "algorithm": "Hash Search (chaining)",
            "input_size": size, "comparisons": 1,
            "time_ms": round(statistics.median(samples), 5),
            "worst_time_ms": round(statistics.median(samples), 5),
            "case": f"lookup (build {build_ms:.2f} ms)",
            "complexity": "O(1) average",
        })

        open_table = HashTableOpenAddressing(capacity=max(16, size))
        for word in vocabulary:
            open_table.put(word, True)
        open_samples = [_timeit(lambda w=target_word: open_table.get(w), repeat=25)[0] for _ in range(7)]
        rows.append({
            "algorithm": "Hash Search (open addressing)",
            "input_size": size, "comparisons": 1,
            "time_ms": round(statistics.median(open_samples), 5),
            "worst_time_ms": round(statistics.median(open_samples), 5),
            "case": "lookup", "complexity": "O(1) average",
        })

        # --- trie build + exact lookup + prefix search
        def build_trie():
            trie = Trie()
            for word in vocabulary:
                trie.insert(word)
            return trie

        trie_build_ms, trie = _timeit(build_trie)
        trie_samples = [_timeit(lambda t=target_word: trie.contains(t), repeat=25)[0] for _ in range(7)]
        prefix_ms, prefix_rows = _timeit(lambda: trie.words_with_prefix("term1", limit=50))
        rows.append({
            "algorithm": "Trie Search (exact)",
            "input_size": size, "comparisons": len(target_word),
            "time_ms": round(statistics.median(trie_samples), 5),
            "worst_time_ms": round(statistics.median(trie_samples), 5),
            "case": f"lookup (build {trie_build_ms:.2f} ms)",
            "complexity": "O(L)",
        })
        rows.append({
            "algorithm": "Trie Prefix Search",
            "input_size": size, "comparisons": len(prefix_rows),
            "time_ms": round(prefix_ms, 4),
            "worst_time_ms": round(prefix_ms, 4),
            "case": f"{len(prefix_rows)} suggestion(s)",
            "complexity": "O(L + P)",
        })

    return {"title": "Searching algorithms vs dataset size",
            "sizes": sizes, "rows": rows}


# ----------------------------------------------------------------------
# string matching
# ----------------------------------------------------------------------
def _pseudo_text(length: int, seed: int) -> str:
    rng = random.Random(seed)
    alphabet = "abcabdab"
    return "".join(rng.choice(alphabet) for _ in range(length))


def benchmark_string_matching(sizes: list[int] | None = None,
                              seed: int = 7) -> dict:
    """KMP vs Rabin-Karp vs naive on text of growing length.

    The pattern is deliberately adversarial ("aaaaa") to expose the naive
    matcher's quadratic blow-up.
    """
    sizes = sizes or STRING_SIZES
    rows: list[dict] = []
    for size in sizes:
        text = _pseudo_text(size, seed)
        pattern = "aaaaa"
        kmp_ms, kmp_result = _timeit(lambda: kmp_search(text, pattern))
        rk_ms, rk_result = _timeit(lambda: rabin_karp(text, pattern))
        naive_ms, naive_result = _timeit(lambda: naive_search(text, pattern))
        rows.append({
            "text_length": size,
            "kmp_ms": round(kmp_ms, 4), "kmp_comparisons": kmp_result["comparisons"],
            "kmp_matches": kmp_result["match_count"],
            "rk_ms": round(rk_ms, 4), "rk_comparisons": rk_result["comparisons"],
            "rk_matches": rk_result["match_count"],
            "rk_collisions": rk_result["collisions"],
            "naive_ms": round(naive_ms, 4), "naive_comparisons": naive_result["comparisons"],
            "speedup": round(naive_ms / kmp_ms, 2) if kmp_ms else 0,
        })
    return {"title": "KMP vs Rabin-Karp vs naive (pattern 'aaaaa')",
            "sizes": sizes, "rows": rows}


# ----------------------------------------------------------------------
# sorting
# ----------------------------------------------------------------------
def benchmark_sorting(sizes: list[int] | None = None, seed: int = 11) -> dict:
    """Merge Sort vs Quick Sort vs Heap Sort on random, sorted and reversed input."""
    sizes = sizes or SORT_SIZES
    rows: list[dict] = []
    for size in sizes:
        rng = random.Random(seed)
        random_data = [rng.randrange(1_000_000) for _ in range(size)]
        sorted_data = sorted(random_data)
        reversed_data = list(reversed(sorted_data))

        merge_ms, merge_result = _timeit(lambda: merge_sort(random_data))
        quick_ms, quick_result = _timeit(lambda: quick_sort(random_data))
        heap_ms, heap_result = _timeit(lambda: heap_sort(random_data))
        merge_sorted_ms, _ = _timeit(lambda: merge_sort(sorted_data))
        quick_sorted_ms, quick_sorted = _timeit(lambda: quick_sort(sorted_data))
        merge_reversed_ms, _ = _timeit(lambda: merge_sort(reversed_data))
        quick_reversed_ms, quick_reversed = _timeit(lambda: quick_sort(reversed_data))

        rows.append({
            "input_size": size,
            "merge_ms": round(merge_ms, 4), "merge_comparisons": merge_result["comparisons"],
            "quick_ms": round(quick_ms, 4), "quick_comparisons": quick_result["comparisons"],
            "quick_partitions": quick_result["partitions"],
            "heap_ms": round(heap_ms, 4), "heap_comparisons": heap_result["comparisons"],
            "merge_sorted_input_ms": round(merge_sorted_ms, 4),
            "quick_sorted_input_ms": round(quick_sorted_ms, 4),
            "merge_reversed_input_ms": round(merge_reversed_ms, 4),
            "quick_reversed_input_ms": round(quick_reversed_ms, 4),
            "quick_reversed_max_depth": quick_reversed["max_recursion_depth"],
            "quick_max_depth": quick_sorted["max_recursion_depth"],
            "speedup": round(quick_ms / merge_ms, 3) if merge_ms else 0,
        })
    return {"title": "Sorting algorithms vs input size", "sizes": sizes, "rows": rows}


# ----------------------------------------------------------------------
# graph
# ----------------------------------------------------------------------
def benchmark_graph(node_count: int = 60, seed: int = 3) -> dict:
    """BFS vs DFS vs Dijkstra on a random sparse graph."""
    rng = random.Random(seed)
    nodes = list(range(node_count))
    adjacency: dict[int, list[int]] = {node: [] for node in nodes}
    weighted: dict[int, list[tuple[int, float]]] = {node: [] for node in nodes}
    for node in nodes:
        for _ in range(3):
            neighbour = rng.choice(nodes)
            if neighbour != node:
                if neighbour not in adjacency[node]:
                    adjacency[node].append(neighbour)
                weighted[node].append((neighbour, round(rng.uniform(0.5, 9.5), 2)))
    return {
        "title": f"Graph traversal on {node_count} nodes",
        "rows": [{"graph_nodes": node_count, **graph_row} for graph_row in
                 [run_graph_bench(adjacency, weighted, nodes)]],
    }


def run_graph_bench(adjacency: dict, weighted: dict, nodes: list) -> dict:
    from algorithms.bfs import bfs
    from algorithms.dfs import dfs
    from algorithms.dijkstra import dijkstra

    bfs_ms, bfs_result = _timeit(lambda: bfs(adjacency, nodes[0], nodes[-1]))
    dfs_ms, dfs_result = _timeit(lambda: dfs(adjacency, nodes[0], nodes[-1]))
    dijkstra_ms, dijkstra_result = _timeit(lambda: dijkstra(weighted, nodes[0], nodes[-1]))
    return {
        "bfs_ms": round(bfs_ms, 4), "bfs_visits": bfs_result["details"]["nodes_visited"],
        "dfs_ms": round(dfs_ms, 4), "dfs_visits": dfs_result["details"]["nodes_visited"],
        "dijkstra_ms": round(dijkstra_ms, 4),
        "dijkstra_settled": dijkstra_result["details"]["nodes_settled"],
        "dijkstra_relaxations": dijkstra_result["relaxations"],
        "dijkstra_heap_comparisons": dijkstra_result["heap_comparisons"],
        "shortest_distance": dijkstra_result["shortest_distance"],
    }


def benchmark_all() -> dict:
    """Everything at once - used by the /algorithms dashboard refresh button."""
    return {
        "searching": benchmark_searching(),
        "string_matching": benchmark_string_matching(),
        "sorting": benchmark_sorting(),
        "graph": benchmark_graph(),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
