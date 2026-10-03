"""NexaSearch algorithm package.

Every algorithm in this package is implemented by hand (no library
equivalents such as ``sorted``, ``heapq``, ``sklearn`` or a trie/hash
package are used for the core logic) because this is a Design and Analysis
of Algorithms demonstration project.

Each module returns a *result dictionary* shaped like::

    {
        "algorithm": "Linear Search",
        "found": bool,
        "index": int | None,
        "comparisons": int,          # key comparisons actually performed
        "time_ms": float,            # wall-clock execution time
        "steps": [ {...}, ... ],     # trace used by the Algorithm Lab
        "details": { ... }
    }
"""

__all__ = [
    "registry",
    "linear_search",
    "binary_search",
    "trie",
    "hash_table",
    "kmp",
    "rabin_karp",
    "bfs",
    "dfs",
    "dijkstra",
    "heap",
    "merge_sort",
    "quick_sort",
    "tfidf",
    "ranking",
    "pagerank",
]
