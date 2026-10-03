"""Integration tests: database, index, graph, search pipeline and the web layer.

These exercise the *whole* stack against the seeded sample corpus (a
throw-away SQLite file), so they double as the end-to-end proof that the
application boots, indexes, ranks and renders.
"""

from __future__ import annotations

import pytest


# ======================================================================
# database
# ======================================================================
class TestDatabase:
    def test_schema_is_created_and_seeded(self, db):
        assert db.is_empty() is False
        assert db.table_counts()["documents"] >= 40
        assert db.keyword_count() > 100
        assert db.document_keyword_count() >= db.keyword_count()

    def test_add_read_update_delete(self, db):
        doc_id = db.add_document(
            title="Integration Fixture",
            content="A fixture document about hashing, chaining and load factor.",
            category="Testing", author="pytest", keywords="hashing,chaining")
        doc = db.get_document(doc_id)
        assert doc is not None
        assert doc["title"] == "Integration Fixture"
        assert doc["keywords"] == ["hashing", "chaining"]
        assert doc["created"] == doc["created_at"]

        assert db.update_document(doc_id, title="Renamed Fixture", keywords="hashing")
        assert db.get_document(doc_id)["title"] == "Renamed Fixture"
        assert db.get_document(doc_id)["keywords"] == ["hashing"]

        assert db.delete_document(doc_id) is True
        assert db.get_document(doc_id) is None
        assert db.delete_document(doc_id) is False

    def test_rejects_invalid_documents(self, db):
        with pytest.raises(ValueError):
            db.add_document(title="", content="long enough content here")
        with pytest.raises(ValueError):
            db.add_document(title="Too short", content="no")

    def test_slug_is_unique(self, db):
        first = db.add_document(title="Duplicate Title", content="Body of the first copy.")
        second = db.add_document(title="Duplicate Title", content="Body of the second copy.")
        assert first != second
        assert db.get_document(first)["slug"] != db.get_document(second)["slug"]
        db.delete_document(first)
        db.delete_document(second)

    def test_listing_filters_and_paginates(self, db):
        rows, total = db.list_documents(limit=5, offset=0, sort="title", order="asc")
        assert len(rows) == 5 and total >= 5
        titles = [row["title"] for row in rows]
        assert titles == sorted(titles)          # ascending by title

        descending, _ = db.list_documents(limit=5, sort="title", order="desc")
        assert [row["title"] for row in descending] == sorted(
            (row["title"] for row in descending), reverse=True)

        category = db.categories()[0]["category"]
        filtered, filtered_total = db.list_documents(limit=50, category=category)
        assert filtered_total == len(filtered)
        assert all(row["category"] == category for row in filtered)

        found, found_total = db.list_documents(search="cryptography")
        assert found_total > 0 and found_total <= total
        assert all("cryptography" in row["content"].lower() or
                   "cryptography" in row["title"].lower() or
                   "cryptography" in " ".join(row["keywords"]).lower()
                   for row in found)

    def test_keyword_statistics_are_consistent(self, db):
        db.recompute_keyword_stats()
        stats = db.keyword_stats(limit=10)
        assert stats["total_keywords"] == db.keyword_count()
        assert all(row["idf"] > 0 for row in stats["top"])
        assert all(row["doc_freq"] >= 1 for row in stats["top"])

    def test_search_history_round_trip(self, db):
        db.clear_history()
        db.record_search(query="graph algorithm", normalized="graph algorithm",
                         tokens=["graph", "algorithm"], result_count=7,
                         documents_searched=49, execution_time=1.25,
                         algorithms=["Trie Vocabulary Lookup"])
        entries = db.recent_searches(5)
        assert entries[0]["query"] == "graph algorithm"
        assert entries[0]["result_count"] == 7
        assert db.popular_queries(3)[0]["count"] == 1
        assert db.clear_history() >= 1
        assert db.recent_searches(5) == []

    def test_hit_counters_increase(self, db):
        doc_id = db.get_document(1)["id"]
        before = db.get_document(doc_id)["hits"]
        db.bump_hits([doc_id])
        assert db.get_document(doc_id)["hits"] == before + 1
        db.click_document(doc_id)
        row = next(r for r in db.most_matched_documents(20) if r["id"] == doc_id)
        assert row["times_clicked"] >= 1

    def test_authentication_round_trip(self, db):
        db.ensure_user("pytest-admin", "secret-pass", role="admin")
        assert db.authenticate("pytest-admin", "secret-pass")["role"] == "admin"
        assert db.authenticate("pytest-admin", "wrong") is None
        assert db.authenticate("ghost", "secret-pass") is None

    def test_sql_injection_attempt_is_inert(self, db):
        rows, total = db.list_documents(search="'; DROP TABLE documents; --")
        assert rows == [] and total == 0
        assert db.is_empty() is False

    def test_graph_is_persisted(self, db):
        rows = db.graph_stats_rows()
        assert rows
        assert all("pagerank" in row for row in rows)


# ======================================================================
# text processing
# ======================================================================
class TestTextProcessor:
    def test_normalisation_and_tokenisation(self):
        from indexing.text_processor import normalize, tokenize
        assert normalize("Hello,  WORLD!") == "hello world"
        assert tokenize("The quick brown foxes") == ["quick", "brown", "foxes"]
        assert tokenize("") == []

    def test_stemming_merges_singular_and_plural(self):
        from indexing.text_processor import stem
        assert stem("algorithms") == stem("algorithm")
        assert stem("graphs") == "graph"
        assert stem("is") == "is"           # too short to stem

    def test_phrase_extraction(self):
        from indexing.text_processor import analyze_query, extract_phrases
        assert extract_phrases('find "binary search" please') == ["binary search"]
        # stop-phrase guards apply to the quoted text itself
        assert extract_phrases('"how to" sort') == []
        assert extract_phrases("no quotes here") == []
        analysis = analyze_query('"binary search" algorithm')
        assert analysis["phrases"] == ["binary search"]
        assert "algorithm" in analysis["tokens"]

    def test_stop_word_only_query_is_empty(self):
        from indexing.text_processor import analyze_query
        analysis = analyze_query("the and of")
        assert analysis["tokens"] == []
        assert analysis["is_empty"] is True

    def test_snippet_escapes_html_and_respects_word_boundaries(self):
        from indexing.text_processor import snippet
        html, matched = snippet("A <script>alert(1)</script> graph about graphs.",
                                ["graph"])
        assert "<script>" not in html and "&lt;script&gt;" in html
        assert matched == ["graph"]
        assert html.count("<mark>graph</mark>") == 1

    def test_snippet_of_empty_text(self):
        from indexing.text_processor import snippet
        assert snippet("", ["graph"]) == ("", [])


# ======================================================================
# index
# ======================================================================
class TestDocumentIndex:
    def test_corpus_is_indexed(self, index):
        stats = index.stats()
        assert stats["documents"] >= 40
        assert stats["unique_terms"] > 300
        assert stats["postings"] > stats["documents"]
        assert stats["trie"]["nodes"] > stats["trie"]["distinct_words"]

    def test_lookup_returns_postings(self, index):
        info = index.lookup("algorithm")
        assert info["in_vocabulary"] is True
        assert info["document_count"] > 0
        assert all(isinstance(pid, int) for pid, _ in info["postings"])

    def test_unknown_term_is_reported(self, index):
        info = index.lookup("zzzznotaword")
        assert info["in_vocabulary"] is False
        assert info["postings"] == []
        assert info["doc_ids"] == []

    def test_autocomplete_and_prefix_terms(self, index):
        words = [row["word"] for row in index.autocomplete("mach", limit=10)]
        assert any(word.startswith("mach") for word in words)
        assert index.prefix_terms("zzzz") == []
        terms = [row["term"] for row in index.terms_with_prefix("algo", limit=10)]
        assert terms and all(term.startswith("algo") for term in terms)

    def test_add_and_remove_document_keep_the_index_consistent(self, index, db):
        doc_id = db.add_document(
            title="Zephyrs and Widgets",
            content="A zephyr widget document mentioning quicksilver gadgets.",
            category="Testing", keywords="zephyr,widget")
        try:
            index.add_document(db.get_document(doc_id))
            assert index.lookup("zephyr")["document_count"] == 1
            assert "zephyr" in [r["word"] for r in index.autocomplete("zephyr", limit=5)]
        finally:
            index.remove_document(doc_id)
            db.delete_document(doc_id)
        assert index.lookup("zephyr")["document_count"] == 0
        assert index.lookup("zephyr")["in_vocabulary"] is False   # trie rebuilt

    def test_top_terms_are_ordered_by_frequency(self, index):
        rows = index.top_terms(10)
        assert len(rows) == 10
        assert rows == sorted(rows, key=lambda row: (-row["frequency"], row["term"]))


# ======================================================================
# graph + pagerank
# ======================================================================
class TestGraph:
    def test_graph_shape(self, graph):
        assert graph["stats"]["nodes"] >= 40
        assert graph["stats"]["edges"] > 0
        assert graph["stats"]["reference_edges"] > 0
        assert graph["stats"]["similarity_edges"] > 0
        assert len(graph["adjacency"]) == graph["stats"]["nodes"]

    def test_pagerank_is_a_probability_distribution(self, graph):
        scores = graph["pagerank"]["scores"]
        assert abs(sum(scores.values()) - 1.0) < 1e-6
        assert graph["pagerank"]["converged"] is True
        assert graph["pagerank"]["iterations"] >= 1

    def test_related_documents_are_neighbours(self, graph):
        from indexing.graph_builder import related_documents
        doc_id = graph["nodes"][0]["id"]
        related = related_documents(graph, doc_id, limit=5)
        assert 0 < len(related) <= 5
        assert all(row["id"] != doc_id for row in related)
        assert [row["similarity"] for row in related] == \
               sorted((row["similarity"] for row in related), reverse=True)

    def test_weighted_edges_are_positive_for_dijkstra(self, graph):
        for node, edges in graph["weighted_adjacency"].items():
            for neighbour, weight in edges:
                assert weight > 0, f"{node}->{neighbour} has weight {weight}"

    def test_dijkstra_over_the_document_graph(self, graph):
        from algorithms.dijkstra import dijkstra
        ids = [node["id"] for node in graph["nodes"]]
        result = dijkstra(graph["weighted_adjacency"], ids[0], ids[3])
        assert result["shortest_distance"] > 0
        assert result["shortest_path"][0] == ids[0]
        assert result["shortest_path"][-1] == ids[3]


# ======================================================================
# search pipeline
# ======================================================================
class TestSearchPipeline:
    def test_single_term_query(self, service):
        payload = service.search("hashing")
        assert payload["total_results"] > 0
        assert payload["documents_searched"] >= 40
        top = payload["results"][0]
        assert top["score"] > 0
        assert top["snippet"]
        assert "<mark>" in top["snippet"]

    def test_results_are_sorted_by_relevance(self, service):
        payload = service.search("graph algorithm")
        scores = [row["score"] for row in payload["results"]]
        assert scores == sorted(scores, reverse=True)

    def test_every_stage_is_reported(self, service):
        payload = service.search("binary search")
        names = [row["algorithm"] for row in payload["algorithms_used"]]
        for expected in ("Text Normalisation + Tokenisation", "Trie Vocabulary Lookup",
                         "Hash Table Posting Fetch", "TF-IDF Cosine Similarity",
                         "Weighted Relevance Ranking", "Total Pipeline"):
            assert expected in names, f"missing stage {expected} in {names}"
        assert all(row["time_ms"] >= 0 for row in payload["algorithms_used"])

    def test_phrase_query_is_scored_by_the_string_matchers(self, service):
        payload = service.search('"merge sort"')
        assert payload["phrases"] == ["merge sort"]
        names = [row["algorithm"] for row in payload["algorithms_used"]]
        assert "KMP Phrase Matching" in names
        assert "Rabin-Karp Rolling Hash" in names
        assert payload["total_results"] > 0
        best = payload["results"][0]
        assert best["phrase_matches"] > 0
        assert best["signals"]["phrase"] > 0
        assert all(row["agrees"] for row in payload["phrase_report"])

    def test_kmp_and_rabin_karp_agree_on_the_corpus(self, service):
        payload = service.search('"hash table" "binary search"')
        assert all(row["kmp_matches"] == row["rabin_karp_matches"]
                   for row in payload["phrase_report"])

    def test_title_match_outranks_a_body_only_match(self, service):
        payload = service.search("sorting")
        top = payload["results"][0]
        assert "sort" in top["title"].lower()

    def test_category_filter(self, service):
        category = service.db.categories()[0]["category"]
        payload = service.search("algorithm", category=category)
        assert payload["total_results"] > 0
        assert all(row["category"] == category for row in payload["results"])

    def test_sort_options(self, service):
        by_title = service.search("algorithm", sort="title")
        titles = [row["title"] for row in by_title["results"]]
        assert titles == sorted(titles, key=str.lower)

        by_quick = service.search("algorithm", sort="quick")
        assert [row["score"] for row in by_quick["results"]] == \
               sorted((row["score"] for row in by_quick["results"]), reverse=True)

    def test_pagination_does_not_lose_results(self, service):
        first = service.search("algorithm", page=1, per_page=4)
        second = service.search("algorithm", page=2, per_page=4)
        assert len(first["results"]) == 4
        assert first["pages"] == second["pages"] >= 2
        assert {row["doc_id"] for row in first["results"]}.isdisjoint(
            {row["doc_id"] for row in second["results"]})

    def test_page_beyond_the_end_is_clamped(self, service):
        payload = service.search("algorithm", page=999)
        assert payload["page"] == payload["pages"]
        assert 0 < len(payload["results"]) <= payload["per_page"]

    def test_empty_query_is_handled(self, service):
        payload = service.search("the and of")
        assert payload["is_empty"] is True
        assert payload["results"] == []
        assert payload["message"]

    def test_unknown_terms_fall_back_to_a_linear_scan(self, service):
        payload = service.search("zzzqqqnothingmatches")
        names = [row["algorithm"] for row in payload["algorithms_used"]]
        assert payload["total_results"] == 0
        assert "Linear Search Fallback" in names or payload["candidates_examined"] == 0

    def test_ranking_exposes_every_signal(self, service):
        payload = service.search("graph traversal")
        row = payload["results"][0]
        assert set(row["signals"]) == {"title", "keyword", "content", "phrase", "graph"}
        assert all(0.0 <= value <= 1.0 for value in row["signals"].values())
        assert row["score_breakdown"]
        assert 0.0 < row["score_percent"] <= 100.0
        assert row["pagerank"] > 0

    def test_full_coverage_is_flagged(self, service):
        payload = service.search("sorting algorithms")
        assert any(row["full_coverage"] for row in payload["results"])

    def test_strategy_comparison(self, service):
        report = service.engine.compare_search_strategies("graph")
        names = [row["algorithm"] for row in report["results"]]
        assert names == ["Linear Search", "Binary Search", "Hash Search", "Trie Search"]
        assert all(row["found"] for row in report["results"])
        binary = next(r for r in report["results"] if r["algorithm"] == "Binary Search")
        linear = next(r for r in report["results"] if r["algorithm"] == "Linear Search")
        assert binary["comparisons"] < linear["comparisons"]

    def test_string_matching_comparison(self, service):
        report = service.engine.compare_string_matching("abababababab", "abab")
        assert report["agree"] is True
        assert len(report["rows"]) == 3
        # "abab" occurs at every even offset in a 12-character run of "ab"
        assert all(row["matches"] == 5 for row in report["rows"])
        assert all(row["positions"] == [0, 2, 4, 6, 8] for row in report["rows"])


# ======================================================================
# pages
# ======================================================================
class TestPages:
    @pytest.mark.parametrize("url", [
        "/", "/search", "/search?q=hashing", "/browse", "/browse?category=Algorithms",
        "/browse?sort=title&page=2", "/graph", "/algorithms/", "/algorithms/visualizer",
        "/algorithms/complexity", "/admin/login", "/document/1",
    ])
    def test_pages_render(self, client, url):
        response = client.get(url)
        assert response.status_code == 200
        assert b"NexaSearch" in response.data

    def test_home_page_shows_corpus_statistics(self, client):
        body = client.get("/").get_data(as_text=True)
        assert "Search Smarter" in body
        assert "Documents" in body

    def test_search_page_reports_the_pipeline(self, client):
        body = client.get("/search?q=binary+search").get_data(as_text=True)
        assert "TF-IDF" in body
        assert "Merge Sort" in body

    def test_search_without_a_query_prompts_the_user(self, client):
        response = client.get("/search")
        assert "Type a search query" in response.get_data(as_text=True)

    def test_self_hosted_fonts_are_served_as_fonts(self, client):
        """The stylesheet declares Inter / Space Grotesk / JetBrains Mono by
        name, so the woff2 files must actually be reachable and correctly
        typed - a browser ignores a font it cannot decode."""
        expected = {
            "inter-var-latin.woff2",
            "space-grotesk-var-latin.woff2",
            "jetbrains-mono-var-latin.woff2",
        }
        for name in expected:
            response = client.get(f"/static/fonts/{name}")
            assert response.status_code == 200
            assert response.headers["Content-Type"] == "font/woff2"
            assert response.data[:4] == b"wOF2"      # real woff2 magic bytes
            assert len(response.data) > 10_000
        css = client.get("/static/css/style.css").get_data(as_text=True)
        for name in expected:
            assert name in css
        assert "font-display: swap" in css

    def test_font_route_rejects_anything_that_is_not_a_font(self, client):
        assert client.get("/static/fonts/style.css").status_code == 404
        assert client.get("/static/fonts/../../app.py").status_code == 404
        assert client.get("/static/fonts/missing.woff2").status_code == 404

    def test_theme_is_applied_before_first_paint(self, client):
        """A returning light-theme visitor must not see a dark flash, so the
        stored theme is resolved by an inline head script, not at DOM ready."""
        body = client.get("/").get_data(as_text=True)
        assert "nexasearch.theme" in body
        assert body.index("nexasearch.theme") < body.index('src="/static/js/main.js"')

    def test_search_records_history(self, client, db):
        db.clear_history()
        client.get("/search?q=history+probe")
        assert any(row["query"] == "history probe" for row in db.recent_searches(5))
        db.clear_history()

    def test_document_page_shows_related_documents(self, client):
        body = client.get("/document/1").get_data(as_text=True)
        assert "Related" in body
        assert "PageRank" in body

    def test_missing_document_returns_404(self, client):
        response = client.get("/document/999999")
        assert response.status_code == 404

    def test_unknown_url_returns_404(self, client):
        assert client.get("/no-such-page").status_code == 404

    def test_graph_traverse_json(self, client):
        for algorithm in ("bfs", "dfs", "dijkstra"):
            payload = client.get(f"/graph/traverse?algorithm={algorithm}&start=1&depth=2").get_json()
            assert payload["algorithm"]
            assert payload["traversal"]
            # ids must stay numeric: the canvas matches them against the node map
            assert all(isinstance(row[0], int) and row[1] for row in payload["traversal"])

    def test_graph_traverse_depth_cap_limits_bfs(self, client):
        shallow = client.get("/graph/traverse?algorithm=bfs&start=1&depth=1").get_json()
        deep = client.get("/graph/traverse?algorithm=bfs&start=1").get_json()
        assert 0 < len(shallow["traversal"]) < len(deep["traversal"])
        assert shallow["levels"] is not None and len(shallow["levels"]) <= 2

    def test_graph_traverse_rejects_unknown_algorithm(self, client):
        assert client.get("/graph/traverse?algorithm=telepathy").status_code == 400

    def test_graph_traverse_with_a_goal(self, client):
        for algorithm in ("bfs", "dijkstra"):
            payload = client.get(f"/graph/traverse?algorithm={algorithm}&start=1&goal=3").get_json()
            assert payload["shortest_path"][0][0] == 1
            assert payload["shortest_path"][-1][0] == 3
        weighted = client.get("/graph/traverse?algorithm=dijkstra&start=1&goal=3").get_json()
        assert weighted["shortest_distance"] > 0


# ======================================================================
# algorithm lab
# ======================================================================
class TestAlgorithmLab:
    LAB_CASES = {
        "binary_search": {"array": "1,3,5,7,9", "target": "7"},
        "kmp": {"text": "abababab", "pattern": "abab"},
        "rabin_karp": {"text": "abababab", "pattern": "abab"},
        "trie": {"words": "alpha,algorithm,algorithms", "prefix": "algo"},
        "hash": {"keys": "alpha,beta,gamma", "probe": "beta"},
        "bfs": {"edges": "A-B, A-C, B-D", "start": "A"},
        "dfs": {"edges": "A-B, A-C, B-D", "start": "A"},
        "dijkstra": {"weighted_edges": "A-B:4, A-C:2, B-D:5, C-D:1, D:",
                     "start": "A", "goal": "D"},
        "merge_sort": {"values": "5,3,8,1"},
        "quick_sort": {"values": "5,3,8,1"},
    }

    @pytest.mark.parametrize("algorithm,data", sorted(LAB_CASES.items()))
    def test_lab_runs(self, client, algorithm, data):
        response = client.post(f"/algorithms/lab/{algorithm}", data=data)
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["algorithm"] == algorithm
        assert "complexity" in payload and payload["complexity"]["time"]

    def test_lab_rejects_unknown_algorithm(self, client):
        response = client.post("/algorithms/lab/telepathy", data={})
        assert response.status_code == 400
        assert "valid" in response.get_json()

    def test_lab_reports_bad_input(self, client):
        assert client.post("/algorithms/lab/kmp",
                           data={"text": "", "pattern": "x"}).status_code == 400
        assert client.post("/algorithms/lab/binary_search",
                           data={"array": "not,numbers"}).status_code == 400

    def test_lab_matches_the_algorithm_tests(self, client):
        payload = client.post("/algorithms/lab/kmp",
                              data={"text": "abababab", "pattern": "abab"}).get_json()
        assert payload["matches"] == [0, 2, 4]
        assert payload["lps"] == [0, 0, 1, 2]
        assert payload["naive_comparisons"] > payload["comparisons"]

    def test_lab_dijkstra_matches_the_hand_computed_path(self, client):
        # the lab treats "A-B:4" as an undirected edge
        payload = client.post("/algorithms/lab/dijkstra", data={
            "weighted_edges": "A-B:4, A-C:2, B-C:1, B-D:5, C-D:8, C-E:10, D-F:6, E-F:3",
            "start": "A", "goal": "F"}).get_json()
        assert payload["distances"]["F"] == 14.0        # A-C(2) + C-B(1) + B-D(5) + D-F(6)
        assert payload["shortest_path"] == ["A", "C", "B", "D", "F"]
        assert payload["settled"][0] == "A"
        assert payload["relaxations"] > 0
        assert payload["heap_comparisons"] > 0

    def test_string_comparison_endpoint(self, client):
        payload = client.post("/algorithms/compare/string",
                              data={"text": "abababab", "pattern": "abab"}).get_json()
        assert payload["agree"] is True
        assert [row["algorithm"] for row in payload["rows"]] == \
               ["KMP", "Rabin-Karp", "Naive / Brute Force"]

    def test_search_comparison_endpoint(self, client):
        payload = client.post("/algorithms/compare/search", data={"query": "graph"}).get_json()
        assert len(payload["results"]) == 4

    def test_sort_benchmark_endpoint(self, client):
        payload = client.post("/algorithms/sort-benchmark", data={"size": "24"}).get_json()
        assert payload["size"] == 24
        assert payload["all_correct"] is True
        assert payload["merge"]["comparisons"] > 0
        assert payload["quick"]["comparisons"] > 0
        assert payload["heap"]["comparisons"] > 0

    def test_tfidf_endpoint(self, client):
        payload = client.post("/algorithms/tfidf", data={"query": "graph algorithm"}).get_json()
        assert payload["scores"]
        assert all(0.0 <= row["score"] <= 1.0 for row in payload["scores"])
        assert payload["terms"] and payload["formula"]["tfidf"]

    def test_full_benchmark_endpoint(self, client):
        payload = client.post("/algorithms/benchmark", data={}).get_json()
        assert {"searching", "string_matching", "sorting", "graph"} <= set(payload)
        assert payload["searching"]["rows"]
        assert payload["saved_rows"] > 0
        assert payload["generated_at"]

    def test_benchmark_covers_sorted_and_reversed_sort_input(self, client):
        payload = client.post("/algorithms/benchmark", data={}).get_json()
        rows = payload["sorting"]["rows"]
        assert rows
        for row in rows:
            for key in ("merge_sorted_input_ms", "quick_sorted_input_ms",
                        "merge_reversed_input_ms", "quick_reversed_input_ms",
                        "quick_max_depth", "quick_reversed_max_depth"):
                assert key in row
                assert row[key] >= 0
            assert row["quick_reversed_max_depth"] < 40


# ======================================================================
# JSON API
# ======================================================================
class TestApi:
    def test_health(self, client):
        payload = client.get("/api/health").get_json()
        assert payload["status"] == "ok"
        assert payload["database"] is True
        assert payload["documents"] > 0

    def test_search(self, client):
        payload = client.get("/api/search?q=hashing&limit=3").get_json()
        assert len(payload["results"]) <= 3
        assert payload["total_results"] > 0

    def test_search_rejects_an_empty_query(self, client):
        assert client.get("/api/search?q=").status_code == 400

    def test_autocomplete(self, client):
        payload = client.get("/api/autocomplete?q=mach").get_json()
        assert payload["prefix"] == "mach"
        assert all(row["word"].startswith("mach") for row in payload["suggestions"])
        assert client.get("/api/autocomplete?q=").get_json()["suggestions"] == []

    def test_terms_with_and_without_a_prefix(self, client):
        top = client.get("/api/terms?limit=5").get_json()
        assert len(top["terms"]) == 5 and top["prefix"] == ""
        prefixed = client.get("/api/terms?prefix=algo&limit=5").get_json()
        assert prefixed["terms"]
        assert all(row["term"].startswith("algo") for row in prefixed["terms"])

    def test_index_and_stats(self, client):
        index = client.get("/api/index").get_json()
        assert index["index"]["documents"] > 0
        assert index["graph"]["nodes"] > 0
        assert index["tfidf"]["documents"] > 0
        stats = client.get("/api/stats").get_json()
        assert stats["index"]["documents"] == index["index"]["documents"]

    def test_document_endpoint_includes_related(self, client):
        payload = client.get("/api/document/1").get_json()
        assert payload["title"]
        assert payload["pagerank"] > 0
        assert isinstance(payload["related"], list)

    def test_document_endpoint_404(self, client):
        assert client.get("/api/document/999999").status_code == 404

    def test_categories_and_history(self, client):
        categories = client.get("/api/categories").get_json()["categories"]
        assert categories and all("count" in row for row in categories)
        assert isinstance(client.get("/api/history?limit=3").get_json()["history"], list)


# ======================================================================
# admin
# ======================================================================
class TestAdmin:
    NEW_DOC = {
        "title": "Admin Created Document",
        "content": "An admin fixture about shortest paths and heap queues.",
        "category": "Testing", "author": "pytest", "keywords": "dijkstra,heap",
    }

    def test_dashboards_are_readable_without_signing_in(self, client):
        # /admin/ and /admin/stats are read-only views; only mutations are gated
        for url in ("/admin/", "/admin/stats"):
            assert client.get(url).status_code == 200

    def test_mutating_pages_redirect_to_login(self, client):
        for url in ("/admin/document/new", "/admin/import"):
            response = client.get(url)
            assert response.status_code == 302
            assert "/admin/login" in response.headers["Location"]

    def test_mutations_are_refused_when_signed_out(self, client):
        assert client.post("/admin/reindex").status_code == 302
        assert client.post("/admin/history/clear").status_code == 302
        assert client.post("/admin/document/new", data=self.NEW_DOC).status_code == 302

    def test_login_rejects_bad_credentials(self, client):
        response = client.post("/admin/login",
                               data={"username": "admin", "password": "wrong"},
                               follow_redirects=True)
        assert response.status_code == 200
        assert "Invalid credentials" in response.get_data(as_text=True)
        assert client.get("/admin/document/new").status_code == 302

    def test_full_document_lifecycle(self, admin_client, db):
        response = admin_client.post("/admin/document/new", data=self.NEW_DOC,
                                     follow_redirects=True)
        assert response.status_code == 200
        doc_id = db.duplicate_count(self.NEW_DOC["title"])
        assert doc_id == 1
        document = next(d for d in db.all_documents()
                        if d["title"] == self.NEW_DOC["title"])
        try:
            assert "dijkstra" in document["keywords"]

            edit = admin_client.post(f"/admin/document/{document['id']}/edit", data={
                "title": "Admin Edited Document",
                "content": "Now it is about breadth first traversal instead.",
                "category": "Testing", "author": "pytest", "keywords": "bfs"})
            assert edit.status_code in (200, 302)
            assert db.get_document(document["id"])["title"] == "Admin Edited Document"

            assert admin_client.get(f"/admin/document/{document['id']}").status_code == 200
            assert admin_client.post("/admin/reindex", follow_redirects=True).status_code == 200

            deleted = admin_client.post(f"/admin/document/{document['id']}/delete",
                                        follow_redirects=True)
            assert deleted.status_code == 200
            assert db.get_document(document["id"]) is None
        finally:
            if db.get_document(document["id"]):
                db.delete_document(document["id"])

    def test_form_validation_errors_are_shown(self, admin_client):
        response = admin_client.post("/admin/document/new",
                                     data={"title": "", "content": "short"},
                                     follow_redirects=True)
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert "title" in body.lower() and "error" in body.lower()

    def test_import_page_accepts_uploaded_files(self, admin_client, db):
        from io import BytesIO
        body = ("Title: Imported Fixture\n\n"
                "An imported document about tries, hashing and posting lists.\n")
        response = admin_client.post(
            "/admin/import",
            data={"documents": (BytesIO(body.encode("utf-8")), "imported-fixture.txt")},
            content_type="multipart/form-data", follow_redirects=True)
        assert response.status_code == 200
        imported = [d for d in db.all_documents() if "Imported Fixture" in d["title"]]
        try:
            assert len(imported) == 1
            assert "tries" in imported[0]["content"]
        finally:
            for document in imported:
                db.delete_document(document["id"])

    def test_import_page_rejects_unsupported_extensions(self, admin_client, db):
        from io import BytesIO
        response = admin_client.post(
            "/admin/import",
            data={"documents": (BytesIO(b"not allowed here"), "payload.exe")},
            content_type="multipart/form-data", follow_redirects=True)
        assert response.status_code == 200
        assert "unsupported extension" in response.get_data(as_text=True)

    def test_stats_page_can_be_downloaded_as_json(self, admin_client):
        response = admin_client.get("/admin/stats?format=json")
        assert response.status_code == 200
        assert response.is_json
        assert response.get_json()["index"]["documents"] > 0

    def test_history_can_be_cleared(self, admin_client, db):
        db.record_search(query="to be cleared", normalized="to be cleared",
                         tokens=["clear"], result_count=1, documents_searched=1,
                         execution_time=0.1, algorithms=["x"])
        response = admin_client.post("/admin/history/clear", follow_redirects=True)
        assert response.status_code == 200
        assert db.recent_searches(5) == []

    def test_logout_ends_the_session(self, client):
        client.post("/admin/login",
                    data={"username": "admin", "password": "nexasearch123"})
        assert client.get("/admin/document/new").status_code == 200
        client.get("/admin/logout")
        assert client.get("/admin/document/new").status_code == 302


# ======================================================================
# end-to-end: a new document must become searchable
# ======================================================================
def test_new_document_is_immediately_searchable(client, db):
    title = "Zephyr Routing Tables"
    created = client.post("/admin/login",
                          data={"username": "admin", "password": "nexasearch123"},
                          follow_redirects=True)
    assert created.status_code == 200
    response = client.post("/admin/document/new", data={
        "title": title,
        "content": "Zephyr routing tables balance quicksilver widgets across nodes.",
        "category": "Testing", "author": "pytest", "keywords": "zephyr,quicksilver",
    }, follow_redirects=True)
    assert response.status_code == 200
    document = next(d for d in db.all_documents() if d["title"] == title)
    try:
        results = client.get("/api/search?q=quicksilver").get_json()["results"]
        assert document["id"] in [row["doc_id"] for row in results]
        suggestions = client.get("/api/autocomplete?q=zephyr").get_json()["suggestions"]
        assert any(row["word"].startswith("zephyr") for row in suggestions)
    finally:
        db.delete_document(document["id"])
        client.post(f"/admin/document/{document['id']}/delete", follow_redirects=True)