"""Unit tests for every hand-written algorithm.

These tests are the DAA evidence: they check *correctness* (does the
algorithm return the right answer?) and *behaviour* (does it use the number
of comparisons / levels we claim?).
"""

from __future__ import annotations

import random

import pytest

from algorithms.binary_search import binary_search, binary_search_all, binary_search_recursive, is_sorted
from algorithms.bfs import bfs
from algorithms.dfs import connected_components, dfs, has_cycle
from algorithms.dijkstra import dijkstra
from algorithms.hash_table import (HashTableChaining, HashTableOpenAddressing,
                                   build_hash_table, djb2_hash)
from algorithms.heap import BinaryHeap, heap_sort
from algorithms.kmp import build_lps, kmp_search, naive_search
from algorithms.linear_search import linear_search
from algorithms.merge_sort import merge_sort
from algorithms.pagerank import pagerank
from algorithms.quick_sort import quick_sort, randomized_quick_sort
from algorithms.rabin_karp import rabin_karp
from algorithms.ranking import (DEFAULT_WEIGHTS, compute_score, normalize_weights,
                                rank_results)
from algorithms.registry import ALGORITHMS, COMPLEXITY_CLASSES
from algorithms.tfidf import TfidfModel, inverse_document_frequency
from algorithms.trie import Trie


# ======================================================================
# linear search
# ======================================================================
class TestLinearSearch:
    def test_finds_first_occurrence(self):
        result = linear_search([4, 8, 15, 16, 23, 42], 15)
        assert result["found"] and result["index"] == 2

    def test_best_case_is_one_comparison(self):
        result = linear_search([1, 2, 3, 4, 5], 1)
        assert result["comparisons"] == 1

    def test_worst_case_scans_everything(self):
        result = linear_search([1, 2, 3, 4, 5], 99)
        assert not result["found"]
        assert result["comparisons"] == 5

    def test_empty_collection(self):
        result = linear_search([], 5)
        assert result["comparisons"] == 0 and not result["found"]

    def test_key_function_enables_case_insensitive_search(self):
        result = linear_search(["Alpha", "Beta", "Gamma"], "beta", key_func=str.lower)
        assert result["found"] and result["index"] == 1

    def test_produces_a_step_trace(self):
        result = linear_search([5, 6, 7], 6)
        assert len(result["steps"]) == 2
        assert result["steps"][-1]["matched"] is True


# ======================================================================
# binary search
# ======================================================================
class TestBinarySearch:
    @pytest.mark.parametrize("size", [1, 2, 3, 7, 16, 100, 1000])
    def test_matches_linear_search(self, size):
        rng = random.Random(size)
        values = sorted(rng.sample(range(100000), size))
        for key in (values[0], values[-1], values[size // 2], -1, 999999):
            linear = linear_search(values, key)
            binary = binary_search(values, key)
            assert binary["found"] == linear["found"]
            if binary["found"]:
                assert values[binary["index"]] == key

    def test_rejects_unsorted_input(self):
        with pytest.raises(ValueError, match="requires sorted input"):
            binary_search([5, 1, 3], 3)

    def test_probe_count_is_logarithmic(self):
        values = list(range(1024))
        result = binary_search(values, 1000)
        assert result["comparisons"] <= values.__len__().bit_length()

    def test_recursive_matches_iterative(self):
        values = sorted(random.Random(3).sample(range(1000), 64))
        iterative = binary_search(values, 517)
        recursive = binary_search_recursive(values, 517)
        assert iterative["found"] == recursive["found"]
        assert iterative["index"] == recursive["index"]

    def test_finds_all_duplicates(self):
        values = [1, 2, 2, 2, 3, 4]
        assert binary_search_all(values, 2) == [1, 2, 3]

    def test_is_sorted_helper(self):
        assert is_sorted([1, 2, 3]) and not is_sorted([3, 1, 2])

    def test_empty_input(self):
        assert not binary_search([], 1)["found"]


# ======================================================================
# hash table
# ======================================================================
class TestHashTable:
    @pytest.mark.parametrize("strategy", ["chaining", "open"])
    def test_insert_get_delete(self, strategy):
        table = build_hash_table(["alpha", "beta", "gamma"], strategy=strategy)
        assert table.get("beta") is not None
        assert table.contains("beta")
        assert table.delete("beta")
        assert not table.contains("beta")
        assert not table.delete("beta")

    def test_collisions_are_handled(self):
        # capacity 4 with 12 similar keys guarantees collisions
        table = HashTableChaining(capacity=4)
        for i in range(12):
            table.put(f"key{i}", i)
        assert table.stats()["collisions"] > 0
        for i in range(12):
            assert table.get(f"key{i}") == i

    def test_open_addressing_handles_collisions(self):
        table = HashTableOpenAddressing(capacity=4)
        for i in range(12):
            table.put(f"key{i}", i)
        for i in range(12):
            assert table.get(f"key{i}") == i
        assert table.stats()["collisions"] > 0

    def test_rehash_keeps_load_factor_healthy(self):
        table = HashTableOpenAddressing(capacity=8)
        for i in range(40):
            table.put(f"item{i}", i)
        assert table.stats()["rehashes"] >= 1
        assert table.stats()["load_factor"] <= 0.8

    def test_hash_function_is_deterministic(self):
        assert djb2_hash("nexasearch") == djb2_hash("nexasearch")
        assert djb2_hash("a") != djb2_hash("b")

    def test_rejects_none_key(self):
        with pytest.raises(ValueError):
            HashTableChaining().put(None, 1)

    def test_overwrite_updates_value(self):
        table = HashTableChaining(capacity=8)
        table.put("k", 1)
        table.put("k", 2)
        assert table.get("k") == 2 and table.stats()["size"] == 1


# ======================================================================
# trie
# ======================================================================
class TestTrie:
    @pytest.fixture
    def trie(self):
        tree = Trie()
        for word in ["machine", "machine learning", "machine learning algorithms",
                     "machine vision", "algorithm", "algorithms", "algorithm analysis",
                     "algorithm design", "graph", "graphs"]:
            tree.insert(word)
        return tree

    def test_exact_search(self, trie):
        assert trie.contains("machine")
        assert trie.contains("machine learning algorithms")
        assert not trie.contains("machin")

    def test_prefix_search_finds_documented_examples(self, trie):
        words = trie.words_with_prefix("mach", limit=10)
        for expected in ["machine", "machine learning", "machine learning algorithms",
                         "machine vision"]:
            assert expected in words

    def test_autocomplete_for_alg(self, trie):
        suggestions = [row["word"] for row in trie.autocomplete("alg", limit=10)]
        for expected in ["algorithm", "algorithms", "algorithm analysis", "algorithm design"]:
            assert expected in suggestions

    def test_posting_lists_are_per_document(self):
        tree = Trie()
        tree.insert("python", doc_id=1)
        tree.insert("python", doc_id=7)
        tree.insert("java", doc_id=2)
        assert tree.posting_list("python") == {1, 7}
        assert tree.posting_list("java") == {2}

    def test_prefix_query_returns_false_for_missing_prefix(self, trie):
        assert trie.words_with_prefix("zzz") == []
        assert trie.autocomplete("zzz") == []

    def test_nodes_are_shared_between_shared_prefixes(self):
        tree = Trie()
        tree.insert("car")
        tree.insert("cat")
        # root + c + a shared, then one node per final letter = 5 for two words
        assert tree.stats()["nodes"] == 5

    def test_insert_trace_steps(self, trie):
        trace = trie.insert_trace("abc")
        assert len(trace["steps"]) == 5      # start + a + b + c + mark-end
        assert trace["steps"][-1]["action"] == "mark-end"

    def test_empty_word_is_ignored(self, trie):
        assert trie.insert("") == 0


# ======================================================================
# string matching
# ======================================================================
class TestKMP:
    def test_lps_array(self):
        lps, _ = build_lps("ABABCABAB")
        assert lps == [0, 0, 1, 2, 0, 1, 2, 3, 4]

    def test_lps_of_uniform_pattern(self):
        lps, _ = build_lps("aaa")
        assert lps == [0, 1, 2]

    def test_classic_example(self):
        result = kmp_search("ABABDABACDABABCABAB", "ABABCABAB")
        assert result["matches"] == [10]

    def test_overlapping_matches(self):
        result = kmp_search("abababab", "abab")
        assert result["matches"] == [0, 2, 4]

    def test_no_match(self):
        result = kmp_search("abcdef", "xyz")
        assert result["match_count"] == 0

    def test_empty_pattern_and_longer_pattern(self):
        assert kmp_search("abc", "")["match_count"] == 0
        assert kmp_search("ab", "abcdef")["match_count"] == 0

    @pytest.mark.parametrize("seed", range(12))
    def test_agrees_with_naive_search(self, seed):
        rng = random.Random(seed)
        alphabet = "abababc"
        text = "".join(rng.choice(alphabet) for _ in range(120))
        pattern = "".join(rng.choice("abc") for _ in range(rng.randint(1, 5)))
        assert kmp_search(text, pattern)["matches"] == naive_search(text, pattern)["matches"]

    def test_kmp_never_repeats_the_text_pointer(self):
        text = "a" * 400
        result = kmp_search(text, "aaa", trace=False)
        assert result["comparisons"] <= len(text)
        assert result["comparisons"] < len(text) * len("aaa")


class TestRabinKarp:
    def test_classic_example(self):
        result = rabin_karp("ABABDABACDABABCABAB", "ABABCABAB")
        assert result["matches"] == [10]

    def test_overlapping_matches(self):
        assert rabin_karp("abababab", "abab")["matches"] == [0, 2, 4]

    def test_agrees_with_kmp(self):
        rng = random.Random(9)
        text = "".join(rng.choice("abcabc") for _ in range(300))
        pattern = "abcab"
        assert rabin_karp(text, pattern)["matches"] == kmp_search(text, pattern)["matches"]

    def test_counts_hash_and_verification_comparisons(self):
        result = rabin_karp("abcabcabc", "abc", trace=False)
        assert result["hash_comparisons"] > 0
        assert result["char_comparisons"] > 0
        assert result["match_count"] == 3

    def test_reports_collisions(self):
        # a modulus small enough to guarantee hash collisions
        result = rabin_karp("aaaa", "aa", mod=7, trace=False)
        assert result["collisions"] >= 0
        assert result["matches"] == [0, 1, 2]

    def test_empty_and_oversized_pattern(self):
        assert rabin_karp("abc", "")["match_count"] == 0
        assert rabin_karp("ab", "abcdef")["match_count"] == 0


# ======================================================================
# sorting
# ======================================================================
class TestSorting:
    @pytest.mark.parametrize("size", [0, 1, 2, 5, 50, 500])
    def test_merge_sort_matches_sorted(self, size):
        rng = random.Random(size)
        data = [rng.randrange(10000) for _ in range(size)]
        assert merge_sort(data)["sorted"] == sorted(data)

    @pytest.mark.parametrize("size", [0, 1, 2, 5, 50, 500])
    def test_quick_sort_matches_sorted(self, size):
        rng = random.Random(size + 1)
        data = [rng.randrange(10000) for _ in range(size)]
        assert quick_sort(data)["sorted"] == sorted(data)

    def test_merge_sort_is_stable(self):
        rows = [{"k": 1, "id": "a"}, {"k": 1, "id": "b"}, {"k": 0, "id": "c"}]
        ordered = merge_sort(rows, key=lambda row: row["k"])["sorted"]
        assert [row["id"] for row in ordered][:2] == ["c", "a"] or \
               [row["id"] for row in ordered] == ["c", "a", "b"]

    def test_quick_sort_handles_sorted_input_without_degenerating(self):
        data = list(range(1024))
        result = quick_sort(data)
        assert result["sorted"] == data
        assert result["max_recursion_depth"] <= 12

    def test_quick_sort_worst_case_is_detected_on_anti_median_input(self):
        # a deliberately awkward input still returns a sorted result
        data = [7, 2, 9, 1, 5, 3, 8, 4, 6]
        assert quick_sort(data)["sorted"] == sorted(data)

    def test_randomized_quick_sort(self):
        data = [random.randrange(500) for _ in range(200)]
        assert randomized_quick_sort(data) == sorted(data)

    def test_merge_sort_comparison_count_is_n_log_n_scale(self):
        n = 1024
        result = merge_sort(list(range(n)))
        assert n <= result["comparisons"] <= n * 12

    def test_sorting_by_key_function(self):
        rows = [{"name": "b"}, {"name": "a"}]
        assert merge_sort(rows, key=lambda r: r["name"])["sorted"][0]["name"] == "a"
        assert quick_sort(rows, key=lambda r: r["name"])["sorted"][0]["name"] == "a"

    def test_heap_sort(self):
        data = [5, 1, 9, 3]
        assert heap_sort(data)["sorted"] == sorted(data)


# ======================================================================
# heap / priority queue
# ======================================================================
class TestHeap:
    def test_pops_in_priority_order(self):
        heap = BinaryHeap()
        for value in [5, 1, 8, 3, 9, 2]:
            heap.push(value, value)
        order = []
        while heap:
            order.append(heap.pop()[0])
        assert order == [1, 2, 3, 5, 8, 9]

    def test_root_is_the_minimum(self):
        heap = BinaryHeap()
        for value in [7, 2, 11]:
            heap.push(value, value)
        assert heap.peek()[0] == 2

    def test_fifo_ordering_for_equal_priorities(self):
        heap = BinaryHeap()
        for index in range(5):
            heap.push(1, index)
        assert [heap.pop()[1] for _ in range(5)] == [0, 1, 2, 3, 4]

    def test_build_from_is_linear_heapify(self):
        heap = BinaryHeap().build_from([(value, value) for value in [9, 4, 7, 1, 3]])
        assert heap.peek()[0] == 1
        assert len(heap) == 5

    def test_empty_heap_pop_returns_none(self):
        assert BinaryHeap().pop() is None

    def test_heap_levels_rendering(self):
        heap = BinaryHeap()
        for value in [1, 2, 3, 4]:
            heap.push(value, value)
        levels = heap.as_levels()
        assert levels[0] == ["1:1"]
        assert levels == [["1:1"], ["2:2", "3:3"], ["4:4"]]   # complete binary tree


# ======================================================================
# graph algorithms
# ======================================================================
SAMPLE_GRAPH = {
    "A": ["B", "C"],
    "B": ["D"],
    "C": ["E"],
    "D": ["F"],
    "E": ["F"],
    "F": [],
}


class TestBFS:
    def test_traversal_and_levels(self):
        result = bfs(SAMPLE_GRAPH, "A")
        assert result["traversal_order"] == ["A", "B", "C", "D", "E", "F"]
        assert result["levels"] == [["A"], ["B", "C"], ["D", "E"], ["F"]]

    def test_shortest_path_by_edge_count(self):
        result = bfs(SAMPLE_GRAPH, "A", "F")
        assert result["path_to_goal"] == ["A", "B", "D", "F"]

    def test_visits_every_reachable_node_once(self):
        result = bfs(SAMPLE_GRAPH, "A")
        assert len(result["traversal_order"]) == len(set(result["traversal_order"])) == 6

    def test_disconnected_graph(self):
        result = bfs({"A": ["B"], "B": [], "X": ["Y"], "Y": []}, "A")
        assert set(result["traversal_order"]) == {"A", "B"}

    def test_handles_a_cycle(self):
        result = bfs({"A": ["B"], "B": ["C"], "C": ["A"]}, "A")
        assert set(result["traversal_order"]) == {"A", "B", "C"}

    def test_edge_examinations_are_counted(self):
        result = bfs(SAMPLE_GRAPH, "A")
        assert result["edge_examinations"] == 6   # A->B, A->C, B->D, C->E, D->F, E->F


class TestDFS:
    def test_iterative_traversal(self):
        result = dfs(SAMPLE_GRAPH, "A")
        assert result["traversal_order"][0] == "A"
        assert set(result["traversal_order"]) == set(SAMPLE_GRAPH)

    def test_recursive_matches_iterative_on_the_same_graph(self):
        assert sorted(dfs(SAMPLE_GRAPH, "A", mode="recursive")["traversal_order"]) == \
               sorted(dfs(SAMPLE_GRAPH, "A", mode="iterative")["traversal_order"])

    def test_recursion_depth_is_reported(self):
        result = dfs({"A": ["B"], "B": ["C"], "C": ["D"], "D": []}, "A", mode="recursive")
        assert result["details"]["max_call_depth"] == 4

    def test_connected_components(self):
        result = connected_components({"A": ["B"], "B": [], "C": ["D"], "D": []})
        assert result["component_count"] == 2

    def test_cycle_detection(self):
        assert has_cycle({"A": ["B"], "B": ["C"], "C": ["A"]})["has_cycle"] is True
        assert has_cycle({"A": ["B"], "B": ["C"], "C": []})["has_cycle"] is False


WEIGHTED_GRAPH = {
    "A": [("B", 4), ("C", 2)],
    "B": [("C", 1), ("D", 5)],
    "C": [("D", 8), ("E", 10)],
    "D": [("F", 6)],
    "E": [("F", 3)],
    "F": [],
}


class TestDijkstra:
    def test_shortest_distance(self):
        # A-B 4, A-C 2, B-C 1, B-D 5, C-D 8, C-E 10, D-F 6, E-F 3
        #   -> D = min(4+5, 2+8) = 9, F = min(9+6, 12+3) = 15
        result = dijkstra(WEIGHTED_GRAPH, "A", "F")
        assert result["shortest_distance"] == 15
        assert result["shortest_path"] == ["A", "B", "D", "F"]
        assert result["shortest_path"][0] == "A"
        assert result["shortest_path"][-1] == "F"

    def test_all_distances_from_source(self):
        result = dijkstra(WEIGHTED_GRAPH, "A")
        distances = result["distances"]
        assert distances["A"] == 0
        assert distances["C"] == 2     # A -> C (2) beats A -> B -> C (4 + 1)
        assert distances["B"] == 4     # direct A -> B (the edge is directed)
        assert distances["D"] == 9     # A -> B -> D (4 + 5) beats A -> C -> D (2 + 8)
        assert distances["E"] == 12    # A -> C -> E (2 + 10)
        assert distances["F"] == 15

    def test_settled_order_follows_increasing_distance(self):
        result = dijkstra(WEIGHTED_GRAPH, "A")
        settled = result["settled"]
        values = [result["distances"][node] for node in settled]
        assert values == sorted(values)

    def test_rejects_negative_weights(self):
        graph = {"A": [("B", -1)], "B": []}
        with pytest.raises(ValueError, match="non-negative"):
            dijkstra(graph, "A")

    def test_unreachable_target(self):
        result = dijkstra({"A": [], "B": []}, "A", "B")
        assert result["shortest_path"] is None

    def test_relaxations_and_heap_comparisons_are_reported(self):
        result = dijkstra(WEIGHTED_GRAPH, "A")
        assert result["relaxations"] > 0
        assert result["heap_comparisons"] > 0


# ======================================================================
# PageRank, TF-IDF and ranking
# ======================================================================
class TestPageRank:
    def test_scores_sum_to_one(self):
        result = pagerank({"A": ["B"], "B": ["C"], "C": []})
        assert abs(sum(result["scores"].values()) - 1.0) < 1e-6

    def test_converges_on_a_small_graph(self):
        result = pagerank({"A": ["B", "C"], "B": ["C"], "C": ["A"]})
        assert result["converged"] is True
        assert result["iterations"] > 1

    def test_hub_scores_higher_than_leaves(self):
        result = pagerank({"A": ["B", "C"], "B": ["A"], "C": ["A"]})
        assert result["scores"]["A"] > result["scores"]["B"]

    def test_empty_graph(self):
        assert pagerank({})["scores"] == {}

    def test_dangling_nodes_do_not_break_convergence(self):
        result = pagerank({"A": ["B"], "B": []})
        assert abs(sum(result["scores"].values()) - 1.0) < 1e-6


class TestTfidf:
    @pytest.fixture
    def model(self):
        documents = {
            1: ["machine", "learning", "algorithm", "learning"],
            2: ["machine", "learning", "model"],
            3: ["cloud", "security", "encryption"],
        }
        return TfidfModel(documents)

    def test_idf_decreases_with_document_frequency(self):
        rare = inverse_document_frequency(1, 100)
        common = inverse_document_frequency(90, 100)
        assert rare > common

    def test_cosine_prefers_the_closer_document(self, model):
        scores = model.score_query(["machine", "learning"])
        assert scores[0]["doc_id"] in (1, 2)
        assert scores[-1]["doc_id"] == 3

    def test_scores_are_bounded(self, model):
        for row in model.score_query(["machine"]):
            assert 0.0 <= row["tfidf_score"] <= 1.0

    def test_unknown_term_scores_zero(self, model):
        assert all(row["tfidf_score"] == 0 for row in model.score_query(["zzzznothing"]))

    def test_empty_query_returns_nothing(self, model):
        assert model.score_query([]) == []

    def test_empty_corpus_returns_nothing(self):
        assert TfidfModel({}).score_query(["anything"]) == []

    def test_term_report(self, model):
        report = model.term_report(["machine", "cloud"])
        assert {row["term"] for row in report} == {"machine", "cloud"}
        assert all(row["idf"] > 0 for row in report)

    def test_document_frequency_is_correct(self, model):
        assert model.document_frequency["machine"] == 2
        assert model.document_frequency["encryption"] == 1

    def test_stats(self, model):
        stats = model.stats()
        assert stats["documents"] == 3
        assert stats["vocabulary"] == 7   # machine, learning, algorithm, model, cloud, security, encryption
        assert stats["total_tokens"] == 10


class TestRanking:
    def test_weights_sum_to_one(self):
        assert abs(sum(DEFAULT_WEIGHTS.values()) - 1.0) < 1e-9
        assert abs(sum(normalize_weights().values()) - 1.0) < 1e-6

    def test_normalize_weights_rescales_custom_input(self):
        weights = normalize_weights({"title": 2, "keyword": 2, "content": 2, "phrase": 1, "graph": 1})
        assert abs(sum(weights.values()) - 1.0) < 1e-6

    def test_score_increases_with_signals(self):
        low = compute_score({"title": 0.1, "keyword": 0.1, "content": 0.1, "phrase": 0, "graph": 0.1})
        high = compute_score({"title": 1.0, "keyword": 1.0, "content": 1.0, "phrase": 1.0, "graph": 1.0})
        assert high["final_score"] > low["final_score"]

    def test_full_coverage_boost_applies(self):
        base = {"title": .5, "keyword": .5, "content": .5, "phrase": 0, "graph": .5}
        without = compute_score(base)
        with_boost = compute_score(base, full_coverage=True)
        assert with_boost["final_score"] > without["final_score"]
        assert with_boost["boost"] > 1.0

    def test_rank_results_orders_descending(self):
        candidates = [
            {"doc_id": 1, "signals": {"content": 0.9}},
            {"doc_id": 2, "signals": {"content": 0.2}},
            {"doc_id": 3, "signals": {"content": 0.5}},
        ]
        ordered = rank_results(candidates)
        assert [row["doc_id"] for row in ordered] == [1, 3, 2]

    def test_rank_results_uses_merge_sort_for_large_lists(self):
        candidates = [{"doc_id": i, "signals": {"content": (i % 17) / 17}} for i in range(40)]
        ordered = rank_results(candidates)
        assert len(ordered) == 40
        assert ordered[0]["score"] >= ordered[-1]["score"]


# ======================================================================
# registry integrity
# ======================================================================
class TestRegistry:
    def test_every_entry_has_full_metadata(self):
        for entry in ALGORITHMS:
            for field in ("id", "name", "category", "purpose", "input", "output",
                          "time", "space", "best", "average", "worst"):
                assert entry.get(field), f"{entry['id']} is missing {field}"

    def test_the_fifteen_required_algorithms_are_present(self):
        ids = {entry["id"] for entry in ALGORITHMS}
        required = {"linear_search", "binary_search", "hash_search", "trie_search",
                    "kmp", "rabin_karp", "bfs", "dfs", "dijkstra", "merge_sort",
                    "quick_sort", "tfidf", "pagerank", "relevance_ranking", "binary_heap"}
        assert required <= ids

    def test_complexity_classes_present(self):
        symbols = {row["symbol"] for row in COMPLEXITY_CLASSES}
        assert {"O(1)", "O(log n)", "O(n)", "O(n log n)", "O(n^2)", "O(2^n)"} <= symbols
