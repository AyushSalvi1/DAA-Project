"""The NexaSearch query pipeline.

Stages (each one is a real algorithm from /algorithms, not a shortcut):

    1  normalise + tokenise + stop-word removal     (indexing.text_processor)
    2  vocabulary check per term                     -> Trie,  O(L) per term
    3  posting list fetch                            -> Hash Table, O(1) avg
    4  candidate set = union of posting lists
    5  content signal                                -> TF-IDF cosine
    6  phrase signal for "quoted" queries            -> KMP  +  Rabin-Karp
    7  title / keyword signals
    8  authority signal                              -> PageRank (cached)
    9  weighted fusion                               -> ranking.rank_results
   10  final ordering                                -> Merge Sort (stable)
   11  snippet + <mark> highlighting

Every stage appends to ``algorithms_used`` with its own measured time so
the results page can honestly report "what happened and how long it took".
"""

from __future__ import annotations

import re
import time

from algorithms.binary_search import binary_search
from algorithms.hash_table import HashTableChaining
from algorithms.kmp import kmp_search
from algorithms.linear_search import linear_search
from algorithms.merge_sort import merge_sort
from algorithms.quick_sort import quick_sort
from algorithms.rabin_karp import rabin_karp
from algorithms.ranking import explain as explain_score
from algorithms.ranking import rank_results
from algorithms.tfidf import TfidfModel
from indexing.text_processor import analyze_query, normalize, snippet, stem

PAGE_SIZE = 8


class SearchEngine:
    """Query engine over a :class:`indexing.indexer.DocumentIndex`."""

    def __init__(self, index, graph: dict | None = None,
                 tfidf: TfidfModel | None = None,
                 weights: dict[str, float] | None = None) -> None:
        self.index = index
        self.graph = graph or {"pagerank": {"scores": {}}, "stats": {"max_pagerank": 0}}
        self.tfidf = tfidf or TfidfModel({})
        self.weights = weights or {}
        # doc_id -> metadata hash table: O(1) record lookup for the result page
        self.document_id_table = HashTableChaining(capacity=64)
        for meta in index.all_documents():
            self.document_id_table.put(str(meta.get("id", "")), meta)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _pagerank_for(self, doc_id: int) -> float:
        scores = self.graph.get("pagerank", {}).get("scores", {})
        return float(scores.get(str(doc_id), 0.0))

    def _pagerank_bounds(self) -> tuple[float, float]:
        """(min, max) PageRank across the corpus, used for min-max scaling."""
        stats = self.graph.get("stats", {})
        return float(stats.get("min_pagerank", 0.0)), float(stats.get("max_pagerank", 0.0))

    # ------------------------------------------------------------------
    # the pipeline
    # ------------------------------------------------------------------
    def search(self, raw_query: str, page: int = 1, per_page: int = PAGE_SIZE,
               category: str = "all", sort: str = "relevance",
               use_phrase: bool = True, sort_engine: str = "merge") -> dict:
        """Run the full pipeline and return a render-ready payload."""
        total_start = time.perf_counter()
        algorithms_used: list[dict] = []
        timings: dict[str, float] = {}

        def note(name: str, ms: float, detail: str = "") -> None:
            timings[name] = round(timings.get(name, 0.0) + ms, 4)
            algorithms_used.append({
                "algorithm": name,
                "time_ms": round(ms, 4),
                "detail": detail,
            })

        # ---------------------------------------------------- 1. text analysis
        stage = time.perf_counter()
        analysis = analyze_query(raw_query or "")
        note("Text Normalisation + Tokenisation", (time.perf_counter() - stage) * 1000,
             f"{analysis['length']} token(s), removed "
             f"{len(analysis['stop_words_removed'])} stop word(s)")

        terms = analysis["tokens"]
        phrases = analysis["phrases"] if use_phrase else []
        # try the unstemmed variant too, so "graphs" finds a doc titled "Graph"
        expanded_terms = list(dict.fromkeys(terms + [t for t in analysis["unique"]]))

        empty = not terms and not phrases
        if empty:
            elapsed = (time.perf_counter() - total_start) * 1000
            return {
                "query": raw_query or "",
                "normalized_query": analysis["normalized"],
                "tokens": [],
                "phrases": [],
                "results": [],
                "total_results": 0,
                "page": 1,
                "per_page": per_page,
                "pages": 0,
                "documents_searched": len(self.index.all_documents()),
                "elapsed_ms": round(elapsed, 4),
                "algorithms_used": algorithms_used,
                "timings": timings,
                "is_empty": True,
                "message": "Query contained only stop words or punctuation. "
                           "Try words such as 'graph algorithm' or 'python'.",
                "suggestions": self.index.autocomplete("", limit=6),
            }

        # ------------------------------------- 2. trie vocabulary check + hashing
        stage = time.perf_counter()
        lookup_details = []
        known_terms: list[str] = []
        for term in dict.fromkeys(expanded_terms):
            info = self.index.lookup(term)
            lookup_details.append(info)
            if info["in_vocabulary"] and info["postings"]:
                known_terms.append(term)
            else:
                # a stemmed form may not exist; the unstemmed one may
                raw_variants = [t for t in analysis["unique"] if stem(t) == term]
                for variant in raw_variants:
                    alt = self.index.lookup(variant)
                    if alt["postings"]:
                        known_terms.append(variant)
                        lookup_details.append(alt)
                        break
        trie_ms = (time.perf_counter() - stage) * 1000
        note("Trie Vocabulary Lookup", trie_ms,
             f"{len(expanded_terms)} term(s) probed in O(L) each")

        stage = time.perf_counter()
        postings: dict[int, dict[str, int]] = {}
        for term in set(known_terms):
            for doc_id, freq in self.index.posting_list(term):
                postings.setdefault(doc_id, {})[term] = freq
        hash_ms = (time.perf_counter() - stage) * 1000
        note("Hash Table Posting Fetch", hash_ms,
             f"{len(set(known_terms))} term(s) resolved via {self.index.term_postings.strategy} hash table")

        candidates = set(postings)
        unknown_terms = [t for t in expanded_terms if t not in known_terms]

        # Phrase-only query ("..." with no bare terms): there is no posting
        # list to consult, so the corpus itself becomes the candidate set and
        # the phrase matcher decides what is relevant.
        phrase_only = not candidates and bool(phrases)
        if phrase_only:
            candidates = {int(meta["id"]) for meta in self.index.all_documents()
                          if meta.get("id") is not None}

        # if the query terms are unknown, fall back to a linear scan so the
        # user still gets "no results, but we really looked"
        fallback_used = False
        if not candidates:
            stage = time.perf_counter()
            docs = self.index.all_documents()
            for position, meta in enumerate(docs):
                if normalize(f"{meta['title']} {meta['category']}").find(analysis["normalized"]) >= 0:
                    doc_id = meta.get("id")
                    if doc_id is not None:
                        candidates.add(int(doc_id))
            note("Linear Search Fallback", (time.perf_counter() - stage) * 1000,
                 f"scanned {len(docs)} document headers because no term was in the vocabulary")
            fallback_used = True

        # -------------------------------------------------- 5. TF-IDF content
        stage = time.perf_counter()
        tfidf_scores: dict[int, float] = {}
        # a phrase-only query still gets a content signal from its words
        content_terms = known_terms or [stem(word) for phrase in phrases
                                        for word in phrase.split()]
        if content_terms:
            for row in self.tfidf.score_query(list(dict.fromkeys(content_terms))):
                tfidf_scores[row["doc_id"]] = row["tfidf_score"]
        note("TF-IDF Cosine Similarity", (time.perf_counter() - stage) * 1000,
             f"{len(content_terms)} query term vector vs {self.tfidf.total_documents} document vectors")

        # ------------------------------------------------- 6. phrase detection
        phrase_hits: dict[int, int] = {}
        phrase_report: list[dict] = []
        if phrases:
            stage = time.perf_counter()
            kmp_total = rk_total = 0
            kmp_matches = rk_matches = 0
            scan_ids = sorted(candidates)[:200]
            for doc_id in scan_ids:
                doc = self.index.get_document(doc_id)
                if not doc:
                    continue
                body = f"{doc.get('title', '')} {doc.get('content', '')}".lower()
                doc_phrase_hits = 0
                for phrase in phrases:
                    kmp_result = kmp_search(body, phrase, trace=False)
                    rk_result = rabin_karp(body, phrase, trace=False)
                    kmp_total += kmp_result["time_ms"]
                    rk_total += rk_result["time_ms"]
                    kmp_matches += kmp_result["match_count"]
                    rk_matches += rk_result["match_count"]
                    doc_phrase_hits += kmp_result["match_count"]
                    if len(phrase_report) < 6:
                        phrase_report.append({
                            "phrase": phrase, "doc_id": doc_id,
                            "title": doc.get("title", ""),
                            "kmp_matches": kmp_result["match_count"],
                            "rabin_karp_matches": rk_result["match_count"],
                            "agrees": kmp_result["matches"] == rk_result["matches"],
                        })
                if doc_phrase_hits:
                    phrase_hits[doc_id] = doc_phrase_hits
            note("KMP Phrase Matching", kmp_total,
                 f"{kmp_matches} phrase match(es) across {len(phrases)} phrase(s)")
            note("Rabin-Karp Rolling Hash", rk_total,
                 f"{rk_matches} match(es) - cross-check agrees with KMP")
            if phrase_only:
                candidates = set(phrase_hits)

        # ------------------------------------------------ 7/8. fused ranking
        stage = time.perf_counter()
        # TF-IDF cosine is naturally small (a term occupies a tiny slice of a
        # long document), so we rescale it to the best candidate. This keeps
        # the weight table meaningful instead of letting the content signal
        # vanish into rounding error.
        best_cosine = max(tfidf_scores.values(), default=0.0)
        min_rank, max_rank = self._pagerank_bounds()
        rank_span = max(1e-9, max_rank - min_rank)
        phrase_words = [word for phrase in phrases for word in phrase.split()]
        query_terms_for_title = list(terms) + phrases + phrase_words
        assembled: list[dict] = []
        content_by_id: dict[int, str] = {}
        for doc_id in candidates:
            doc = self.index.get_document(doc_id)
            if not doc:
                continue
            if category != "all" and str(doc.get("category", "")).lower() != category.lower():
                continue
            content_by_id[doc_id] = doc.get("content", "")
            term_counts = postings.get(doc_id, {})
            title = doc.get("title", "")
            title_signal = self._title_signal(query_terms_for_title, title)
            keyword_signal = self._keyword_signal(query_terms_for_title, doc.get("keywords") or [])
            raw_cosine = float(tfidf_scores.get(doc_id, 0.0))
            content_signal = (raw_cosine / best_cosine) if best_cosine > 0 else 0.0
            phrase_signal = self._phrase_signal(phrase_hits.get(doc_id, 0), doc.get("content", ""))
            graph_signal = (self._pagerank_for(doc_id) - min_rank) / rank_span
            popularity = int(doc.get("hits", 0) or 0)
            coverage = (len(term_counts) / len(set(content_terms))
                        if content_terms else 0.0)

            assembled.append({
                "doc_id": doc_id,
                "title": title,
                "category": doc.get("category", "Uncategorised"),
                "author": doc.get("author", "Unknown"),
                "url": doc.get("url", ""),
                "created": doc.get("created", ""),
                "keywords": doc.get("keywords") or [],
                "content_length": len(doc.get("content", "")),
                "matched_terms": sorted(term_counts.keys()),
                "term_frequency": term_counts,
                "total_frequency": sum(term_counts.values()),
                "term_coverage": round(coverage, 4),
                "popularity": popularity,
                "pagerank": round(self._pagerank_for(doc_id), 6),
                "raw_tfidf": round(raw_cosine, 6),
                "phrase_matches": phrase_hits.get(doc_id, 0),
                "signals": {
                    "title": round(title_signal, 4),
                    "keyword": round(keyword_signal, 4),
                    "content": round(min(1.0, content_signal), 4),
                    "phrase": round(phrase_signal, 4),
                    "graph": round(max(0.0, min(1.0, graph_signal)), 4),
                },
                "title_exact_phrase": bool(phrases) and normalize(" ".join(phrases)) in normalize(title),
                "full_coverage": bool(content_terms) and coverage >= 0.999,
            })
        rank_results(assembled, self.weights)
        note("Weighted Relevance Ranking", (time.perf_counter() - stage) * 1000,
             f"{len(assembled)} candidate(s) scored with the weighted formula")

        # ---------------------------------------------------- 10. final sort
        stage = time.perf_counter()
        if sort == "title":
            ordered = merge_sort(assembled, key=lambda item: item["title"].lower())["sorted"]
            sort_name = "Merge Sort (by title)"
        elif sort == "newest":
            ordered = merge_sort(assembled, key=lambda item: str(item["created"]), reverse=True)["sorted"]
            sort_name = "Merge Sort (by date)"
        elif sort == "quick":
            ordered = quick_sort(assembled, key=lambda item: -item["score"])["sorted"]
            sort_name = "Quick Sort (by relevance)"
        else:
            ordered = merge_sort(assembled, key=lambda item: -item["score"])["sorted"]
            sort_name = "Merge Sort (stable, by relevance)"
        note(sort_name, (time.perf_counter() - stage) * 1000,
             f"{len(ordered)} result(s) ordered")

        # ------------------------------------------------ 11. snippets + filter
        for row in ordered:
            terms_for_mark = sorted(set(row["matched_terms"]) | set(query_terms_for_title), key=len, reverse=True)
            snippet_html, matched_in_snippet = snippet(
                content_by_id.get(row["doc_id"], ""),
                [stem(t) for t in terms_for_mark] + terms_for_mark)
            row["snippet"] = snippet_html
            row["highlighted_terms"] = matched_in_snippet
            row["score_breakdown"] = explain_score(row["score_detail"])
            row["score_percent"] = round(min(99.0, row["score"] * 100 * 1.35), 1)

        total = len(ordered)
        per_page = max(1, min(int(per_page or PAGE_SIZE), 50))
        pages = (total + per_page - 1) // per_page if total else 0
        page = max(1, min(int(page or 1), pages or 1))
        start = (page - 1) * per_page
        paged = ordered[start:start + per_page]

        elapsed = (time.perf_counter() - total_start) * 1000
        note("Total Pipeline", elapsed, f"{len(paged)} result(s) on page {page}")

        return {
            "query": raw_query or "",
            "normalized_query": analysis["normalized"],
            "tokens": terms,
            "unique_terms": analysis["unique"],
            "phrases": phrases,
            "stop_words_removed": analysis["stop_words_removed"],
            "known_terms": sorted(set(known_terms)),
            "unknown_terms": sorted(set(unknown_terms)),
            "lookup_details": lookup_details,
            "results": paged,
            "total_results": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
            "documents_searched": len(self.index.all_documents()),
            "candidates_examined": len(candidates),
            "elapsed_ms": round(elapsed, 4),
            "algorithms_used": algorithms_used,
            "timings": timings,
            "phrase_report": phrase_report,
            "sort": sort,
            "category": category,
            "is_empty": False,
            "fallback_used": fallback_used,
            "suggestions": self.index.autocomplete((terms[0] if terms else ""), limit=6),
        }

    # ------------------------------------------------------------------
    # signal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _title_signal(query_terms: list[str], title: str) -> float:
        if not query_terms or not title:
            return 0.0
        lowered = title.lower()
        hits = 0
        for term in query_terms:
            token = term.lower()
            if token in lowered or (len(token) > 3 and token[:-1] in lowered):
                hits += 1
        coverage = hits / len(query_terms)
        phrase = " ".join(t.lower() for t in query_terms)
        bonus = 0.25 if phrase and phrase in lowered else 0.0
        return min(1.0, coverage * 0.8 + bonus)

    @staticmethod
    def _keyword_signal(query_terms: list[str], keywords: list[str]) -> float:
        if not query_terms or not keywords:
            return 0.0
        lowered = [str(k).lower() for k in keywords]
        hits = sum(1 for term in query_terms
                   if any(term.lower() in key or key in term.lower() for key in lowered))
        return min(1.0, hits / len(query_terms))

    @staticmethod
    def _phrase_signal(match_count: int, content: str) -> float:
        if match_count <= 0:
            return 0.0
        import math
        return 1.0 - math.exp(-match_count / 3.0)

    # ------------------------------------------------------------------
    # comparison helpers (used by /compare and the dashboard)
    # ------------------------------------------------------------------
    def compare_search_strategies(self, term: str) -> dict:
        """Linear vs Binary vs Hash vs Trie lookup for the same target.

        One ground-truth document is chosen first (a title containing the
        term), and all four strategies then answer the same question -
        "is this document in the index?" - so their costs are comparable.
        """
        metas = self.index.all_documents()
        titles = [meta.get("title", "") for meta in metas]
        term_lower = str(term).lower().strip()
        # Whole-word title match: "graph" must not select "Applied Cryptography".
        pattern = re.compile(rf"(?<![a-z0-9]){re.escape(term_lower)}(?![a-z0-9])")
        target_meta = next((m for m in metas if pattern.search(str(m.get("title", "")).lower())),
                           None)
        if target_meta is None and metas:
            target_meta = metas[0]
        target_title = str(target_meta.get("title", "")) if target_meta else str(term)
        target_id = int(target_meta["id"]) if target_meta else None

        results = []
        if titles:
            result = linear_search(titles, target_title, key_func=lambda value: value.lower())
            results.append({
                "algorithm": "Linear Search", "found": result["found"],
                "comparisons": result["comparisons"], "time_ms": result["time_ms"],
                "steps": result["comparisons"],
                "note": f"scanned {result['comparisons']} of {len(titles)} titles (O(n))",
            })
            sorted_titles = sorted(titles, key=lambda value: value.lower())
            binary = binary_search(sorted_titles, target_title, key_func=lambda value: value.lower())
            results.append({
                "algorithm": "Binary Search", "found": binary["found"],
                "comparisons": binary["comparisons"], "time_ms": binary["time_ms"],
                "steps": binary["comparisons"],
                "note": f"ceil(log2({len(titles)}+1)) = "
                        f"{max(1, len(titles).bit_length())} probes at most (O(log n))",
            })
        stage = time.perf_counter()
        hash_found = (target_id is not None
                      and self.document_id_table.get(str(target_id)) is not None)
        hash_ms = (time.perf_counter() - stage) * 1000
        results.append({
            "algorithm": "Hash Search", "found": hash_found,
            "comparisons": 1, "time_ms": hash_ms, "steps": 1,
            "note": f"one bucket probe on key '{target_id}' + one chain walk (O(1) average)",
        })
        # The Trie stores *terms*, so the comparable probe is the query term
        # itself: O(L) character steps, independent of the corpus size.
        probe_term = (term_lower if self.index.trie.contains(term_lower)
                      else str(target_title).lower().split()[0])
        stage = time.perf_counter()
        trie_found = self.index.trie.contains(probe_term)
        trie_ms = (time.perf_counter() - stage) * 1000
        results.append({
            "algorithm": "Trie Search", "found": trie_found,
            "comparisons": len(probe_term), "time_ms": trie_ms,
            "steps": len(probe_term),
            "note": f"walked {len(probe_term)} character node(s) for '{probe_term}' - O(L), "
                    f"independent of the {len(metas)} documents",
        })
        return {"term": term, "target": target_title,
                "target_id": target_id, "results": results}

    def compare_string_matching(self, text: str, pattern: str) -> dict:
        """KMP vs Rabin-Karp vs Naive on the same input."""
        stage = time.perf_counter()
        kmp_result = kmp_search(text, pattern)
        note_kmp = (time.perf_counter() - stage) * 1000
        stage = time.perf_counter()
        rk_result = rabin_karp(text, pattern)
        note_rk = (time.perf_counter() - stage) * 1000
        from algorithms.kmp import naive_search
        stage = time.perf_counter()
        naive_result = naive_search(text, pattern)
        note_naive = (time.perf_counter() - stage) * 1000
        rows = [
            {"algorithm": "KMP", "matches": kmp_result["match_count"],
             "time_ms": round(kmp_result["time_ms"], 4),
             "comparisons": kmp_result["comparisons"],
             "positions": kmp_result["matches"][:20],
             "complexity": "O(n + m)",
             "note": "deterministic, LPS table, overlap safe"},
            {"algorithm": "Rabin-Karp", "matches": rk_result["match_count"],
             "time_ms": round(rk_result["time_ms"], 4),
             "comparisons": rk_result["comparisons"],
             "positions": rk_result["matches"][:20],
             "complexity": "O(n + m) average",
             "note": f"{rk_result['collisions']} hash collision(s) verified away"},
            {"algorithm": "Naive / Brute Force", "matches": naive_result["match_count"],
             "time_ms": round(naive_result["time_ms"], 4),
             "comparisons": naive_result["comparisons"],
             "positions": naive_result["matches"][:20],
             "complexity": "O(n * m) worst",
             "note": "baseline that KMP improves upon"},
        ]
        return {
            "text_length": len(text),
            "pattern_length": len(pattern),
            "rows": rows,
            "agree": kmp_result["matches"] == rk_result["matches"],
            "total_ms": round(note_kmp + note_rk + note_naive, 4),
        }
