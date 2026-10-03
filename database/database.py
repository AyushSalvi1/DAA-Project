"""SQLite data-access layer for NexaSearch.

Security notes
--------------
* **Every** value that reaches SQLite goes through a bound parameter
  (``?`` placeholders). No query is ever built by string concatenation of
  user input, so SQL injection has no attack surface.
* Identifiers that *must* be dynamic (sort column / order) are validated
  against an explicit allow-list.
* Write helpers use ``PRAGMA foreign_keys = ON`` so cascades behave.
* ``check_same_thread=False`` is used with a lock because the Flask dev
  server may serve requests from more than one thread.
"""

from __future__ import annotations

import os
import sqlite3
import threading
from typing import Any, Iterable, Sequence

try:  # optional, only used for the "log in as admin" demo
    from werkzeug.security import generate_password_hash, check_password_hash
except Exception:  # pragma: no cover - werkzeug always ships with Flask
    generate_password_hash = None  # type: ignore[assignment]
    check_password_hash = None  # type: ignore[assignment]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "instance", "nexasearch.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")

SORTABLE_COLUMNS = {
    "relevance": "id",
    "newest": "created_at",
    "oldest": "created_at",
    "title": "title",
    "hits": "hits",
    "category": "category",
}
SORT_ORDERS = {"asc": "ASC", "desc": "DESC"}

_write_lock = threading.Lock()


class Database:
    """Thin, explicit repository around a single SQLite file."""

    def __init__(self, path: str | None = None) -> None:
        self.path = path or os.environ.get("NEXASEARCH_DB") or DEFAULT_DB_PATH
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._local = threading.local()
        self.fts_available = True
        # Bulk-import fast path: skip the per-document df/IDF recomputation
        # and do one pass at the end (see ``Database.recompute_keyword_stats``).
        self.defer_keyword_stats = False
        self.init_schema()

    # ------------------------------------------------------------------
    # connection handling
    # ------------------------------------------------------------------
    @property
    def connection(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.path, check_same_thread=False, timeout=15)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            self._local.conn = conn
        return conn

    def close(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None

    def query(self, sql: str, params: Sequence[Any] = ()) -> list[sqlite3.Row]:
        """SELECT helper - returns a list of Row objects."""
        return list(self.connection.execute(sql, tuple(params)).fetchall())

    def query_one(self, sql: str, params: Sequence[Any] = ()) -> sqlite3.Row | None:
        return self.connection.execute(sql, tuple(params)).fetchone()

    def scalar(self, sql: str, params: Sequence[Any] = (), default: Any = 0) -> Any:
        row = self.query_one(sql, params)
        if row is None:
            return default
        value = row[0]
        return default if value is None else value

    def execute(self, sql: str, params: Sequence[Any] = ()) -> sqlite3.Cursor:
        """Write helper - commits and returns the cursor."""
        with _write_lock:
            cursor = self.connection.execute(sql, tuple(params))
            self.connection.commit()
            return cursor

    def execute_many(self, sql: str, seq: Iterable[Sequence[Any]]) -> None:
        with _write_lock:
            self.connection.executemany(sql, list(seq))
            self.connection.commit()

    def executemany_write(self, sql: str, seq: Iterable[Sequence[Any]]) -> None:
        """Write many rows inside one transaction (fast bulk import)."""
        with _write_lock:
            cursor = self.connection.executemany(sql, list(seq))
            self.connection.commit()
            return cursor

    # ------------------------------------------------------------------
    # schema / bootstrap
    # ------------------------------------------------------------------
    def init_schema(self) -> None:
        """Create every table if missing (runs automatically on boot)."""
        if not os.path.exists(SCHEMA_PATH):
            raise FileNotFoundError(f"schema.sql not found at {SCHEMA_PATH}")
        sql = open(SCHEMA_PATH, "r", encoding="utf-8").read()
        with _write_lock:
            try:
                self.connection.executescript(sql)
                self.connection.commit()
            except sqlite3.OperationalError as exc:
                if "fts5" in str(exc).lower():
                    # Build without the FTS5 virtual table.
                    self.fts_available = False
                    stripped = "\n".join(
                        line for line in sql.splitlines()
                        if "VIRTUAL TABLE" not in line.upper()
                    )
                    self.connection.executescript(stripped)
                    self.connection.commit()
                else:
                    raise

    def is_empty(self) -> bool:
        return self.scalar("SELECT COUNT(*) FROM documents", default=0) == 0

    # ------------------------------------------------------------------
    # documents
    # ------------------------------------------------------------------
    @staticmethod
    def _split_keywords(keywords: Any) -> list[str]:
        if isinstance(keywords, (list, tuple, set)):
            return [str(k).strip() for k in keywords if str(k).strip()]
        return [k.strip() for k in str(keywords or "").split(",") if k.strip()]

    @staticmethod
    def _row_to_document(row: sqlite3.Row | None) -> dict | None:
        if row is None:
            return None
        doc = dict(row)
        doc["keywords"] = [k.strip() for k in str(doc.get("keywords", "")).split(",") if k.strip()]
        # aliases used by the templates and the ranking pipeline
        doc["created"] = doc.get("created_at", "")
        doc["updated"] = doc.get("updated_at", "")
        return doc

    def add_document(self, title: str, content: str, category: str = "Uncategorised",
                     author: str = "NexaSearch Editorial", url: str = "",
                     keywords: Any = "", summary: str = "", slug: str | None = None) -> int:
        """Insert a document and return its new id."""
        title = (title or "").strip()
        content = content or ""
        if not title:
            raise ValueError("A document needs a non-empty title.")
        if len(content.strip()) < 10:
            raise ValueError("Document content must be at least 10 characters long.")
        keyword_list = self._split_keywords(keywords)
        slug = (slug or self._slugify(title)).strip()
        if self.get_document_by_slug(slug):
            slug = f"{slug}-{int(__import__('time').time() * 1000) % 100000}"
        summary = summary.strip() or (content.strip().split(". ")[0][:240] + ".")
        cursor = self.execute(
            """INSERT INTO documents
               (title, slug, content, summary, category, author, url, keywords,
                token_count, hits, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,1,datetime('now'),datetime('now'))""",
            (title, slug, content, summary, category, author, url,
             ", ".join(keyword_list), len(content.split())),
        )
        doc_id = int(cursor.lastrowid)
        self._reindex_single(doc_id)
        if self.fts_available:
            self._fts_sync(doc_id, "insert")
        return doc_id

    def update_document(self, doc_id: int, **fields: Any) -> bool:
        """Partial update with an allow-list of columns."""
        allowed = {"title", "content", "summary", "category", "author", "url",
                   "keywords", "slug", "is_published", "hits"}
        updates: dict[str, Any] = {}
        for key, value in fields.items():
            if key not in allowed:
                continue
            if key == "keywords":
                updates["keywords"] = ", ".join(self._split_keywords(value))
            elif key == "content":
                updates["token_count"] = len(str(value or "").split())
                updates["summary"] = (fields.get("summary") or "") or \
                    (str(value).strip().split(". ")[0][:240] + ".")
                updates["content"] = value or ""
            else:
                updates[key] = value
        if not updates:
            return False
        assignments = ", ".join(f"{column} = ?" for column in updates)
        params = list(updates.values()) + [datetime_now(), doc_id]
        cursor = self.execute(
            f"UPDATE documents SET {assignments}, updated_at = ? WHERE id = ?", params)
        if cursor.rowcount:
            self._reindex_single(doc_id)
            if self.fts_available:
                self._fts_sync(doc_id, "delete")
                self._fts_sync(doc_id, "insert")
            return True
        return False

    def delete_document(self, doc_id: int) -> bool:
        if not self.get_document(doc_id):
            return False
        if self.fts_available:
            self._fts_sync(int(doc_id), "delete")
        cursor = self.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        return cursor.rowcount > 0

    def get_document(self, doc_id: int) -> dict | None:
        return self._row_to_document(
            self.query_one("SELECT * FROM documents WHERE id = ?", (doc_id,)))

    def get_document_by_slug(self, slug: str) -> dict | None:
        return self._row_to_document(
            self.query_one("SELECT * FROM documents WHERE slug = ?", (str(slug),)))

    def list_documents(self, limit: int = 50, offset: int = 0,
                       category: str = "all", sort: str = "newest",
                       order: str = "desc", search: str = "") -> tuple[list[dict], int]:
        """Paginated, filtered, sorted document listing."""
        clauses = ["is_published = 1"]
        params: list[Any] = []
        if category and category != "all":
            clauses.append("category = ?")
            params.append(category)
        if search:
            clauses.append("(title LIKE ? OR content LIKE ? OR keywords LIKE ?)")
            needle = f"%{search}%"
            params.extend([needle, needle, needle])
        where = " AND ".join(clauses)
        column = SORTABLE_COLUMNS.get(sort, "created_at")
        direction = SORT_ORDERS.get((order or "desc").lower(), "DESC")
        if sort == "relevance":
            column, direction = "hits", "DESC"
        total = int(self.scalar(f"SELECT COUNT(*) FROM documents WHERE {where}",
                                params, default=0))
        limit = max(1, min(int(limit or 50), 500))
        offset = max(0, int(offset or 0))
        rows = self.query(
            f"SELECT * FROM documents WHERE {where} ORDER BY {column} {direction}, id DESC "
            f"LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        return [self._row_to_document(row) for row in rows], total

    def all_documents(self, include_unpublished: bool = False) -> list[dict]:
        clause = "" if include_unpublished else "WHERE is_published = 1"
        rows = self.query(f"SELECT * FROM documents {clause} ORDER BY id")
        return [self._row_to_document(row) for row in rows]

    def categories(self) -> list[dict]:
        rows = self.query(
            "SELECT category, COUNT(*) AS count FROM documents "
            "WHERE is_published = 1 GROUP BY category ORDER BY count DESC, category")
        return [{"category": row["category"], "count": row["count"]} for row in rows]

    def duplicate_count(self, title: str) -> int:
        return int(self.scalar("SELECT COUNT(*) FROM documents WHERE title = ?",
                               ((title or "").strip(),), default=0))

    # ------------------------------------------------------------------
    # keyword tables
    # ------------------------------------------------------------------
    def _reindex_single(self, doc_id: int) -> None:
        """Recompute the keyword rows for one document from its text.

        Three statements per document (not three per term): with ~350 distinct
        terms per article, issuing one transaction each made seeding take
        seconds instead of milliseconds.
        """
        from indexing.text_processor import analyze

        doc = self.get_document(doc_id)
        if not doc:
            return
        title_tokens = set(analyze(doc["title"])["tokens"])
        content_tokens = set(analyze(f"{doc['title']} {doc['content']}")["tokens"])
        keyword_tokens = set(analyze(" ".join(doc["keywords"]))["tokens"])
        frequencies: dict[str, int] = {}
        for token in analyze(f"{doc['title']} {doc['content']} "
                             f"{' '.join(doc['keywords'])}")["tokens"]:
            frequencies[token] = frequencies.get(token, 0) + 1
        if not frequencies:
            return

        self.execute("DELETE FROM document_keywords WHERE document_id = ?", (doc_id,))
        self.execute_many(
            """INSERT INTO keywords(term, doc_freq, total_freq) VALUES (?,1,?)
               ON CONFLICT(term) DO UPDATE SET total_freq = total_freq + excluded.total_freq""",
            [(term, freq) for term, freq in frequencies.items()])

        terms = list(frequencies)
        placeholders = ",".join("?" * len(terms))
        ids = {row["term"]: row["id"] for row in self.query(
            f"SELECT id, term FROM keywords WHERE term IN ({placeholders})", terms)}
        self.execute_many(
            """INSERT OR REPLACE INTO document_keywords
               (document_id, keyword_id, frequency, in_title, in_content)
               VALUES (?,?,?,?,?)""",
            [(doc_id, ids[term], freq, int(term in title_tokens),
              int(term in content_tokens or term in keyword_tokens))
             for term, freq in frequencies.items() if term in ids])

        if self.defer_keyword_stats:
            return
        self.recompute_keyword_stats()

    def recompute_keyword_stats(self) -> None:
        """Recount df / total_freq from document_keywords and refresh IDF.

        Recomputing (instead of incrementing) keeps the statistics exact even
        after document updates and deletions, which is what a real indexer
        does with a rebuild pass.

        The IDF values are computed in Python because SQLite builds without
        SQLITE_ENABLE_MATH_FUNCTIONS do not provide ``ln()``/``log()``.
        """
        self.execute(
            """UPDATE keywords SET
                   doc_freq = (SELECT COUNT(*) FROM document_keywords dk
                               WHERE dk.keyword_id = keywords.id),
                   total_freq = (SELECT COALESCE(SUM(dk.frequency), 0)
                                 FROM document_keywords dk
                                 WHERE dk.keyword_id = keywords.id)""")
        self.execute("DELETE FROM keywords WHERE doc_freq = 0")
        self.refresh_idf()

    def refresh_idf(self) -> None:
        """IDF(t) = ln((1 + N) / (1 + df)) + 1  (smoothed, always positive)."""
        import math

        total = int(self.scalar("SELECT COUNT(*) FROM documents WHERE is_published = 1",
                                default=0)) or 1
        rows = self.query("SELECT id, doc_freq FROM keywords")
        if not rows:
            return
        updates = [(math.log((1.0 + total) / (1.0 + max(1, row["doc_freq"]))) + 1.0,
                    row["id"]) for row in rows]
        self.executemany_write("UPDATE keywords SET idf = ? WHERE id = ?", updates)

    def keyword_stats(self, limit: int = 25) -> dict:
        total = int(self.scalar("SELECT COUNT(*) FROM keywords", default=0))
        rows = self.query(
            "SELECT term, doc_freq, total_freq, ROUND(idf, 5) AS idf "
            "FROM keywords ORDER BY doc_freq DESC, term ASC LIMIT ?", (limit,))
        return {
            "total_keywords": total,
            "top": [dict(row) for row in rows],
        }

    def keyword_count(self) -> int:
        return int(self.scalar("SELECT COUNT(*) FROM keywords", default=0))

    def document_keyword_count(self) -> int:
        return int(self.scalar("SELECT COUNT(*) FROM document_keywords", default=0))

    # ------------------------------------------------------------------
    # search history / statistics
    # ------------------------------------------------------------------
    def record_search(self, query: str, normalized: str, tokens: list[str],
                      result_count: int, documents_searched: int,
                      execution_time: float, algorithms: list[str],
                      is_filtered: bool = False) -> int:
        cursor = self.execute(
            """INSERT INTO search_history
               (query, normalized, tokens, result_count, documents_searched,
                execution_time, algorithms, is_filtered)
               VALUES (?,?,?,?,?,?,?,?)""",
            (query, normalized, " ".join(tokens), int(result_count),
             int(documents_searched), float(execution_time),
             ", ".join(algorithms), int(bool(is_filtered))))
        # keep the table bounded - a demo app should not grow forever
        self.execute("DELETE FROM search_history WHERE id NOT IN "
                     "(SELECT id FROM search_history ORDER BY id DESC LIMIT 500)")
        return int(cursor.lastrowid)

    def recent_searches(self, limit: int = 10) -> list[dict]:
        rows = self.query(
            "SELECT * FROM search_history ORDER BY id DESC LIMIT ?", (max(1, min(limit, 50)),))
        return [dict(row) for row in rows]

    def clear_history(self) -> int:
        cursor = self.execute("DELETE FROM search_history")
        return cursor.rowcount

    def delete_search(self, search_id: int) -> bool:
        return self.execute("DELETE FROM search_history WHERE id = ?", (search_id,)).rowcount > 0

    def popular_queries(self, limit: int = 8) -> list[dict]:
        rows = self.query(
            """SELECT query, COUNT(*) AS count, ROUND(AVG(execution_time), 3) AS avg_ms
               FROM search_history GROUP BY query
               ORDER BY count DESC, query ASC LIMIT ?""", (limit,))
        return [dict(row) for row in rows]

    def _recent_doc_ids(self) -> list[int]:
        """Placeholder kept for API compatibility with older call sites."""
        return []

    def bump_hits(self, doc_ids: Iterable[int]) -> None:
        rows = []
        for doc_id in doc_ids:
            rows.append((int(doc_id),))
        if not rows:
            return
        with _write_lock:
            for (doc_id,) in rows:
                self.connection.execute(
                    """INSERT INTO search_statistics (document_id, times_shown, last_shown_at)
                       VALUES (?, 1, datetime('now'))
                       ON CONFLICT(document_id) DO UPDATE SET
                           times_shown = times_shown + 1,
                           last_shown_at = datetime('now')""", (doc_id,))
                self.connection.execute(
                    "UPDATE documents SET hits = hits + 1 WHERE id = ?", (doc_id,))
            self.connection.commit()

    def most_matched_documents(self, limit: int = 8) -> list[dict]:
        rows = self.query(
            """SELECT d.id, d.title, d.category, s.times_shown, s.times_clicked
               FROM search_statistics s
               JOIN documents d ON d.id = s.document_id
               ORDER BY s.times_shown DESC, d.title ASC LIMIT ?""", (limit,))
        return [dict(row) for row in rows]

    def click_document(self, doc_id: int) -> None:
        self.execute(
            """INSERT INTO search_statistics (document_id, times_shown, times_clicked)
               VALUES (?, 0, 1)
               ON CONFLICT(document_id) DO UPDATE SET times_clicked = times_clicked + 1""",
            (int(doc_id),))

    def search_statistics(self) -> dict:
        total_searches = int(self.scalar("SELECT COUNT(*) FROM search_history", default=0))
        avg_ms = float(self.scalar(
            "SELECT COALESCE(AVG(execution_time), 0) FROM search_history", default=0))
        slowest = self.query(
            "SELECT query, ROUND(MAX(execution_time),3) AS ms FROM search_history "
            "GROUP BY query ORDER BY ms DESC LIMIT 5")
        empty_results = int(self.scalar(
            "SELECT COUNT(*) FROM search_history WHERE result_count = 0", default=0))
        unique_queries = int(self.scalar(
            "SELECT COUNT(DISTINCT query) FROM search_history", default=0))
        return {
            "total_searches": total_searches,
            "unique_queries": unique_queries,
            "average_time_ms": round(avg_ms, 3),
            "empty_result_searches": empty_results,
            "success_rate": round(
                100 * (total_searches - empty_results) / total_searches, 2)
            if total_searches else 0.0,
            "slowest": [dict(row) for row in slowest],
        }

    # ------------------------------------------------------------------
    # graph + links
    # ------------------------------------------------------------------
    def save_graph(self, graph: dict) -> None:
        with _write_lock:
            self.connection.execute("DELETE FROM document_links")
            self.connection.execute("DELETE FROM document_graph_stats")
            self.connection.executemany(
                "INSERT OR REPLACE INTO document_links (source_id, target_id, edge_type, weight) "
                "VALUES (?,?,?,?)",
                [(e["source"], e["target"], e["type"], e["weight"]) for e in graph["edges"]])
            self.connection.executemany(
                "INSERT OR REPLACE INTO document_graph_stats "
                "(document_id, pagerank, in_degree, out_degree, updated_at) "
                "VALUES (?,?,?,?,datetime('now'))",
                [(n["id"], n["pagerank"], n["in_degree"], n["out_degree"])
                 for n in graph["nodes"]])
            self.connection.commit()

    def graph_stats_rows(self) -> list[dict]:
        return [dict(row) for row in self.query(
            "SELECT * FROM document_graph_stats ORDER BY pagerank DESC")]

    # ------------------------------------------------------------------
    # users (demo authentication)
    # ------------------------------------------------------------------
    def ensure_user(self, username: str, password: str, role: str = "viewer") -> int:
        existing = self.query_one("SELECT id FROM users WHERE username = ?", (username,))
        if existing:
            return int(existing["id"])
        if generate_password_hash is None:  # pragma: no cover
            raise RuntimeError("password hashing unavailable")
        cursor = self.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
            (username, generate_password_hash(password), role))
        return int(cursor.lastrowid)

    def authenticate(self, username: str, password: str) -> dict | None:
        row = self.query_one("SELECT * FROM users WHERE username = ?", (username,))
        if not row or check_password_hash is None:
            return None
        if check_password_hash(row["password_hash"], password):
            return {"id": row["id"], "username": row["username"], "role": row["role"]}
        return None

    def user_count(self) -> int:
        return int(self.scalar("SELECT COUNT(*) FROM users", default=0))

    # ------------------------------------------------------------------
    # FTS5 mirror (optional feature, never on the critical path)
    # ------------------------------------------------------------------
    def _fts_sync(self, doc_id: int, action: str) -> None:
        if not self.fts_available:
            return
        try:
            if action == "delete":
                self.connection.execute(
                    "INSERT INTO documents_fts(documents_fts, rowid, title, content, keywords) "
                    "VALUES ('delete', ?, '', '', '')", (int(doc_id),))
                return
            doc = self.get_document(doc_id)
            if not doc:
                return
            self.connection.execute(
                "INSERT INTO documents_fts (rowid, title, content, keywords) VALUES (?,?,?,?)",
                (int(doc_id), doc["title"], doc["content"], ", ".join(doc["keywords"])))
            self.connection.commit()
        except sqlite3.OperationalError:
            self.fts_available = False

    def fts_search(self, phrase: str, limit: int = 10) -> list[dict]:
        """SQL FTS5 baseline - only used for the 'SQL vs algorithms' card."""
        if not self.fts_available:
            return []
        try:
            rows = self.query(
                "SELECT d.*, bm25(documents_fts) AS score FROM documents_fts "
                "JOIN documents d ON d.id = documents_fts.rowid "
                "WHERE documents_fts MATCH ? ORDER BY score LIMIT ?",
                (f'"{phrase}"', limit))
            return [dict(row) for row in rows]
        except sqlite3.OperationalError:
            return []

    # ------------------------------------------------------------------
    # benchmarks
    # ------------------------------------------------------------------
    def save_benchmark(self, category: str, algorithm: str, input_size: int,
                       time_ms: float, comparisons: int = 0, extra: str = "") -> None:
        self.execute(
            "INSERT INTO benchmark_results (category, algorithm, input_size, time_ms, "
            "comparisons, extra) VALUES (?,?,?,?,?,?)",
            (category, algorithm, int(input_size), float(time_ms), int(comparisons), extra))

    def clear_benchmarks(self) -> None:
        self.execute("DELETE FROM benchmark_results")

    def saved_benchmarks(self, limit: int = 100) -> list[dict]:
        return [dict(row) for row in self.query(
            "SELECT * FROM benchmark_results ORDER BY id DESC LIMIT ?", (limit,))]

    # ------------------------------------------------------------------
    # maintenance
    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Wipe user data but keep the schema (used by the admin 'reset' demo)."""
        for table in ("search_history", "search_statistics", "document_keywords",
                      "keywords", "document_links", "document_graph_stats",
                      "benchmark_results", "documents"):
            self.execute(f"DELETE FROM {table}")
        if self.fts_available:
            self.execute("DELETE FROM documents_fts")
        self.execute("DELETE FROM sqlite_sequence WHERE name IN "
                     "('documents','keywords','search_history','benchmark_results')")

    def vacuum(self) -> None:
        with _write_lock:
            self.connection.execute("VACUUM")
            self.connection.commit()

    def table_counts(self) -> dict:
        tables = ["documents", "keywords", "document_keywords", "search_history",
                  "search_statistics", "users", "document_links", "benchmark_results"]
        return {table: int(self.scalar(f"SELECT COUNT(*) FROM {table}", default=0))
                for table in tables}

    @staticmethod
    def _slugify(text: str) -> str:
        import re
        slug = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
        return slug[:80] or "document"

    @staticmethod
    def export_json(documents: list[dict]) -> str:
        import json
        return json.dumps(documents, indent=2, ensure_ascii=False)


def datetime_now() -> str:
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
