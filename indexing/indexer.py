"""In-memory inverted index built on top of our own Trie + Hash Table.

Data structures (all hand-written, see /algorithms):
  * Trie            : vocabulary + posting lists, O(L) membership,
                      O(L + P) prefix search for autocomplete.
  * HashTable       : term -> posting list and doc_id -> document for O(1)
                      access (we do not use a Python dict for these hot maps).
  * Inverted index  : term -> sorted list of (doc_id, tf).

The index is rebuilt from SQLite on boot and updated incrementally whenever
a document is added / edited / deleted through the admin UI, so a search
never has to touch the database.
"""

from __future__ import annotations

import time
from collections import Counter
from typing import Any, Iterable

from algorithms.hash_table import HashTableChaining
from algorithms.trie import Trie
from indexing.text_processor import analyze, analyze_pairs


class DocumentIndex:
    """Trie + hash table + inverted index over the document corpus."""

    def __init__(self) -> None:
        self.trie = Trie()
        self.term_postings: HashTableChaining = HashTableChaining(capacity=64)
        self.doc_store: HashTableChaining = HashTableChaining(capacity=64)
        self.doc_tokens: dict[int, list[str]] = {}
        self.doc_meta: dict[int, dict[str, Any]] = {}
        self.surface_forms: dict[str, Counter] = {}
        self.built_at: str = ""
        self.build_time_ms: float = 0.0

    # ------------------------------------------------------------------
    # building
    # ------------------------------------------------------------------
    def clear(self) -> None:
        self.trie = Trie()
        self.term_postings = HashTableChaining(capacity=64)
        self.doc_store = HashTableChaining(capacity=64)
        self.doc_tokens.clear()
        self.doc_meta.clear()
        self.surface_forms.clear()

    def add_document(self, doc: dict[str, Any]) -> dict:
        """Index one document; returns timing + token statistics."""
        start = time.perf_counter()
        doc_id = int(doc["id"])
        title = doc.get("title") or ""
        content = doc.get("content") or ""
        keywords = doc.get("keywords") or []

        # Field weighting: a token in the title or keyword list is counted
        # more often (classic field-boosting trick used by real indexes).
        title_analysis = analyze(title)
        content_analysis = analyze(f"{title} {content}")
        keyword_analysis = analyze(" ".join(keywords))
        title_tokens = title_analysis["tokens"]
        content_tokens = content_analysis["tokens"]
        keyword_tokens = keyword_analysis["tokens"]

        weighted: list[str] = []
        weighted.extend(title_tokens * 3)
        weighted.extend(keyword_tokens * 4)
        weighted.extend(content_tokens)

        counters = Counter(weighted)
        # Remember how each stem was actually written, so autocomplete can say
        # "sorting" while the index is keyed by "sort".
        for stemmed, surface in title_analysis["pairs"]:
            self.surface_forms.setdefault(stemmed, Counter())[surface] += 3
        for stemmed, surface in keyword_analysis["pairs"]:
            self.surface_forms.setdefault(stemmed, Counter())[surface] += 4
        for stemmed, surface in content_analysis["pairs"]:
            self.surface_forms.setdefault(stemmed, Counter())[surface] += 1

        for term, freq in counters.items():
            self.trie.insert(term, doc_id=doc_id, freq=freq,
                             display=self.display_form(term))
            existing = self.term_postings.get(term) or []
            existing.append((doc_id, freq))
            self.term_postings.put(term, existing)
        self.term_postings.put(f"__doc__{doc_id}", doc_id)

        self.doc_store.put(str(doc_id), doc)
        self.doc_tokens[doc_id] = content_tokens
        self.doc_meta[doc_id] = {
            "id": doc_id,
            "title": title,
            "category": doc.get("category", "Uncategorised"),
            "author": doc.get("author", "Unknown"),
            "url": doc.get("url", ""),
            "created": doc.get("created", ""),
            "hits": int(doc.get("hits", 0) or 0),
            "length": len(content_tokens),
            "term_count": len(counters),
        }
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "doc_id": doc_id,
            "tokens": len(weighted),
            "unique_terms": len(counters),
            "time_ms": elapsed,
        }

    def remove_document(self, doc_id: int) -> bool:
        """Delete a document and clean every posting list (O(terms in doc)).

        The Trie has no delete operation, so it is rebuilt from the surviving
        posting lists; leaving that to the caller is how a stale vocabulary
        creeps into the autocomplete box.
        """
        doc_id = int(doc_id)
        removed = doc_id in self.doc_meta
        for term, postings in list(self._all_terms()):
            filtered = [(pid, freq) for pid, freq in postings if pid != doc_id]
            if filtered:
                self.term_postings.put(term, filtered)
            else:
                self.term_postings.delete(term)
        self.doc_store.delete(str(doc_id))
        self.term_postings.delete(f"__doc__{doc_id}")
        self.doc_tokens.pop(doc_id, None)
        self.doc_meta.pop(doc_id, None)
        # surface forms are aggregated per document set, so drop this document's
        # contribution by re-collecting them from the surviving metadata
        self.surface_forms = {}
        for meta in self.doc_meta.values():
            self._collect_surfaces(meta)
        self.rebuild_trie()
        return removed

    def _collect_surfaces(self, doc: dict[str, Any]) -> None:
        """Remember how each stem was actually written in this document.

        Field weights match ``add_document`` (keyword x4, title x3, body x1)
        so a keyword spelling wins the display vote.
        """
        title = doc.get("title") or ""
        content = doc.get("content") or ""
        keywords = doc.get("keywords") or []
        for text, weight in ((title, 3), (" ".join(keywords), 4), (f"{title} {content}", 1)):
            for stemmed, surface in analyze_pairs(text):
                bucket = self.surface_forms.setdefault(stemmed, Counter())
                bucket[surface] += weight

    def display_form(self, term: str) -> str:
        """Most frequent original spelling of ``term`` (ties -> alphabetical)."""
        forms = self.surface_forms.get(term)
        if not forms:
            return term
        return min(forms, key=lambda form: (-forms[form], form))

    def rebuild_trie(self) -> None:
        """Rebuild the Trie from the posting lists (trie has no delete op).

        This is the honest DAA point: a Trie supports insert and search in
        O(L) but *deletion* is awkward, so document removal triggers a
        rebuild from the hash table which remains O(V * L).
        """
        self.trie = Trie()
        for term, postings in self._all_terms():
            display = self.display_form(term)
            for doc_id, freq in postings:
                self.trie.insert(term, doc_id=doc_id, freq=freq, display=display)

    def _all_terms(self) -> Iterable[tuple[str, list]]:
        for chain in self.term_postings.buckets:
            for key, value in chain:
                if not key.startswith("__doc__"):
                    yield key, value

    # ------------------------------------------------------------------
    # querying
    # ------------------------------------------------------------------
    def lookup(self, term: str) -> dict:
        """Vocabulary check via Trie + posting fetch via hash table."""
        start = time.perf_counter()
        in_vocab = self.trie.contains(term)
        postings = self.term_postings.get(term) or []
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "term": term,
            "in_vocabulary": in_vocab,
            "postings": postings,
            "doc_ids": sorted({pid for pid, _ in postings}),
            "document_count": len(postings),
            "time_ms": elapsed,
        }

    def posting_list(self, term: str) -> list[tuple[int, int]]:
        return self.term_postings.get(term) or []

    def candidates(self, terms: list[str]) -> tuple[set[int], dict]:
        """Union the posting lists of the query terms (OR semantics).

        Unknown terms are dropped - which is exactly what the Trie tells us.
        """
        known: list[str] = []
        unknown: list[str] = []
        for term in terms:
            if self.trie.contains(term):
                known.append(term)
            else:
                unknown.append(term)
        doc_ids: set[int] = set()
        for term in known:
            doc_ids.update(pid for pid, _ in self.posting_list(term))
        return doc_ids, {"known_terms": known, "unknown_terms": unknown}

    def get_document(self, doc_id: int) -> dict | None:
        return self.doc_store.get(str(int(doc_id)))

    # ------------------------------------------------------------------
    # autocomplete
    # ------------------------------------------------------------------
    def autocomplete(self, prefix: str, limit: int = 8) -> list[dict]:
        return self.trie.autocomplete(prefix.lower().strip(), limit=limit)

    def prefix_terms(self, prefix: str, limit: int = 50) -> list[str]:
        return self.trie.words_with_prefix(prefix.lower().strip(), limit=limit)

    # ------------------------------------------------------------------
    # statistics
    # ------------------------------------------------------------------
    def stats(self) -> dict:
        terms = {term: postings for term, postings in self._all_terms()}
        postings_total = sum(len(p) for p in terms.values())
        lengths = [meta["length"] for meta in self.doc_meta.values()]
        return {
            "documents": len(self.doc_meta),
            "unique_terms": len(terms),
            "postings": postings_total,
            "trie": self.trie.stats(),
            "hash_table": self.term_postings.stats(),
            "total_tokens": sum(lengths),
            "average_document_length": round(sum(lengths) / len(lengths), 2) if lengths else 0.0,
            "build_time_ms": round(self.build_time_ms, 3),
        }

    def top_terms(self, limit: int = 15) -> list[dict]:
        rows = [{"term": term, "documents": len(postings),
                 "frequency": sum(freq for _, freq in postings)}
                for term, postings in self._all_terms()]
        rows.sort(key=lambda row: (-row["frequency"], row["term"]))
        return rows[:limit]

    def terms_with_prefix(self, prefix: str, limit: int = 20) -> list[dict]:
        """Vocabulary entries under ``prefix``, most frequent first (O(L + P)).

        Reports the surface form the user would type plus the stem the index
        is actually keyed by.
        """
        wanted = self.prefix_terms(prefix, limit=max(limit * 8, 200))
        rows: list[dict] = []
        for stem in wanted:
            postings = self.posting_list(stem)
            if not postings:
                continue
            rows.append({"term": self.display_form(stem), "stem": stem,
                         "documents": len(postings),
                         "frequency": sum(freq for _, freq in postings)})
        rows.sort(key=lambda row: (-row["frequency"], row["term"]))
        return rows[:limit]

    def all_documents(self) -> list[dict]:
        return list(self.doc_meta.values())


def build_index(documents: list[dict[str, Any]]) -> DocumentIndex:
    """Build the whole index and record how long it took."""
    index = DocumentIndex()
    start = time.perf_counter()
    for doc in documents:
        index.add_document(doc)
    index.build_time_ms = (time.perf_counter() - start) * 1000
    index.built_at = time.strftime("%Y-%m-%d %H:%M:%S")
    return index
