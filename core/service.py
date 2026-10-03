"""Application service layer.

Holds the long-lived objects (database, index, graph, TF-IDF model, search
engine) and knows how to rebuild them.  Flask stores one instance on
``app.extensions["nexasearch"]``, so requests share a single index and the
admin UI can trigger a rebuild without a restart.
"""

from __future__ import annotations

import threading
import time
from typing import Any

from algorithms.tfidf import TfidfModel
from database.database import Database
from indexing.graph_builder import build_graph
from indexing.indexer import DocumentIndex, build_index
from indexing.search_engine import SearchEngine
from indexing.text_processor import analyze


class NexaService:
    """Everything the routes need, plus incremental index maintenance."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db = Database(db_path)
        self.index = DocumentIndex()
        self.graph: dict = {"nodes": [], "edges": [], "adjacency": {},
                            "weights": {}, "weighted_adjacency": {},
                            "pagerank": {"scores": {}}, "stats": {"max_pagerank": 0}}
        self.tfidf = TfidfModel({})
        self.engine: SearchEngine | None = None
        self.lock = threading.RLock()
        self.boot_time_ms = 0.0
        self.last_rebuild = ""
        self.build_counts = {"full": 0, "incremental": 0}

    # ------------------------------------------------------------------
    def bootstrap(self, seed: bool = True) -> dict:
        """Initialise everything from the database."""
        start = time.perf_counter()
        from core.seed_data import seed_database

        seed_info = None
        if seed:
            seed_info = seed_database(self.db)
        info = self.rebuild(reason="bootstrap")
        self.boot_time_ms = (time.perf_counter() - start) * 1000
        info["seed"] = seed_info
        info["boot_time_ms"] = round(self.boot_time_ms, 2)
        return info

    # ------------------------------------------------------------------
    def rebuild(self, reason: str = "manual") -> dict:
        """Full rebuild: index + graph + PageRank + TF-IDF + engine."""
        with self.lock:
            start = time.perf_counter()
            documents = self.db.all_documents()
            self.index = build_index(documents)
            self.graph = build_graph(documents)
            self.db.save_graph(self.graph)
            tokenised = {
                int(doc["id"]): analyze(f"{doc['title']} {doc['content']} "
                                        f"{' '.join(doc['keywords'])}")["tokens"]
                for doc in documents
            }
            self.tfidf = TfidfModel(tokenised)
            self.engine = SearchEngine(self.index, self.graph, self.tfidf)
            elapsed = (time.perf_counter() - start) * 1000
            self.last_rebuild = time.strftime("%Y-%m-%d %H:%M:%S")
            self.build_counts["full"] += 1
            return {
                "documents": len(documents),
                "index_time_ms": round(self.index.build_time_ms, 3),
                "graph_time_ms": round(elapsed - self.index.build_time_ms, 3),
                "total_time_ms": round(elapsed, 3),
                "pagerank_iterations": self.graph["pagerank"].get("iterations", 0),
                "vocabulary": self.index.stats()["unique_terms"],
                "reason": reason,
                "timestamp": self.last_rebuild,
            }

    # ------------------------------------------------------------------
    def reindex_document(self, doc_id: int) -> dict:
        """Incrementally re-add one document after create or update."""
        with self.lock:
            self.index.remove_document(int(doc_id))
            document = self.db.get_document(doc_id)
            if document:
                self.index.add_document(document)
            self._refresh_derived()
            self.build_counts["incremental"] += 1
            return {"doc_id": doc_id, "indexed": bool(document),
                    "vocabulary": self.index.stats()["unique_terms"]}

    def remove_document(self, doc_id: int) -> dict:
        with self.lock:
            # DocumentIndex.remove_document rebuilds the trie itself
            self.index.remove_document(int(doc_id))
            self._refresh_derived()
            self.build_counts["incremental"] += 1
            return {"doc_id": doc_id, "vocabulary": self.index.stats()["unique_terms"]}

    def _refresh_derived(self) -> None:
        """Recompute graph, PageRank and TF-IDF after an index change."""
        documents = self.db.all_documents()
        self.graph = build_graph(documents)
        self.db.save_graph(self.graph)
        tokenised = {
            int(doc["id"]): analyze(f"{doc['title']} {doc['content']} "
                                    f"{' '.join(doc['keywords'])}")["tokens"]
            for doc in documents
        }
        self.tfidf = TfidfModel(tokenised)
        self.engine = SearchEngine(self.index, self.graph, self.tfidf)

    # ------------------------------------------------------------------
    def search(self, query: str, **kwargs: Any) -> dict:
        if not self.engine:
            self.rebuild(reason="lazy")
        assert self.engine is not None
        return self.engine.search(query, **kwargs)

    def dashboard(self) -> dict:
        """Aggregate numbers for the admin dashboard."""
        index_stats = self.index.stats()
        search_stats = self.db.search_statistics()
        table_counts = self.db.table_counts()
        return {
            "index": index_stats,
            "search": search_stats,
            "tables": table_counts,
            "graph": self.graph["stats"],
            "tfidf": self.tfidf.stats(),
            "pagerank": {
                "iterations": self.graph["pagerank"].get("iterations", 0),
                "converged": self.graph["pagerank"].get("converged", False),
                "top": self.graph["pagerank"].get("ranking", [])[:8],
            },
            "top_terms": self.index.top_terms(12),
            "categories": self.db.categories(),
            "popular_queries": self.db.popular_queries(8),
            "most_matched": self.db.most_matched_documents(8),
            "recent_searches": self.db.recent_searches(8),
            "last_rebuild": self.last_rebuild,
        }
