-- =====================================================================
--  NexaSearch - SQLite schema
--  Design and Analysis of Algorithms project
--  Every statement is idempotent (IF NOT EXISTS) so the application can
--  initialise the database automatically on every boot.
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- documents: the searchable corpus
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT    NOT NULL,
    slug            TEXT    UNIQUE,
    content         TEXT    NOT NULL DEFAULT '',
    summary         TEXT    NOT NULL DEFAULT '',
    category        TEXT    NOT NULL DEFAULT 'Uncategorised',
    author          TEXT    NOT NULL DEFAULT 'NexaSearch Editorial',
    url             TEXT    NOT NULL DEFAULT '',
    keywords        TEXT    NOT NULL DEFAULT '',      -- comma separated
    token_count     INTEGER NOT NULL DEFAULT 0,
    hits            INTEGER NOT NULL DEFAULT 0,      -- popularity / times shown
    is_published    INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
CREATE INDEX IF NOT EXISTS idx_documents_title    ON documents(title);

-- ---------------------------------------------------------------------
-- keywords: the vocabulary extracted from documents (feeds the Trie)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS keywords (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    term        TEXT    NOT NULL UNIQUE,
    doc_freq    INTEGER NOT NULL DEFAULT 0,   -- number of documents containing it
    total_freq  INTEGER NOT NULL DEFAULT 0,   -- raw occurrences in the corpus
    idf         REAL    NOT NULL DEFAULT 0.0, -- computed IDF value
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_keywords_docfreq ON keywords(doc_freq DESC);

-- ---------------------------------------------------------------------
-- document_keywords: many-to-many vocabulary <-> document
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS document_keywords (
    document_id  INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    keyword_id   INTEGER NOT NULL REFERENCES keywords(id)  ON DELETE CASCADE,
    frequency    INTEGER NOT NULL DEFAULT 1,
    in_title     INTEGER NOT NULL DEFAULT 0,
    in_content   INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (document_id, keyword_id)
);

CREATE INDEX IF NOT EXISTS idx_doc_keywords_keyword ON document_keywords(keyword_id);

-- ---------------------------------------------------------------------
-- search_history: recent queries + measured timings
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS search_history (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    query          TEXT    NOT NULL,
    normalized     TEXT    NOT NULL DEFAULT '',
    tokens         TEXT    NOT NULL DEFAULT '',
    result_count   INTEGER NOT NULL DEFAULT 0,
    documents_searched INTEGER NOT NULL DEFAULT 0,
    execution_time REAL    NOT NULL DEFAULT 0.0,
    algorithms     TEXT    NOT NULL DEFAULT '',
    is_filtered    INTEGER NOT NULL DEFAULT 0,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_history_created ON search_history(created_at DESC);

-- ---------------------------------------------------------------------
-- search_statistics: document-level hit counters (popularity signal)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS search_statistics (
    document_id   INTEGER PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,
    times_shown   INTEGER NOT NULL DEFAULT 0,
    times_clicked INTEGER NOT NULL DEFAULT 0,
    last_shown_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- document_links: the explicit edges of the document graph
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS document_links (
    source_id  INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    target_id  INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    edge_type  TEXT    NOT NULL DEFAULT 'reference',
    weight     REAL    NOT NULL DEFAULT 1.0,
    PRIMARY KEY (source_id, target_id)
);

-- ---------------------------------------------------------------------
-- document_graph_stats: cached PageRank so it is computed once, not per request
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS document_graph_stats (
    document_id INTEGER PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,
    pagerank    REAL NOT NULL DEFAULT 0.0,
    in_degree   INTEGER NOT NULL DEFAULT 0,
    out_degree  INTEGER NOT NULL DEFAULT 0,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- benchmark_results: persisted performance measurements
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS benchmark_results (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category    TEXT    NOT NULL,
    algorithm   TEXT    NOT NULL,
    input_size  INTEGER NOT NULL,
    time_ms     REAL    NOT NULL DEFAULT 0,
    comparisons INTEGER NOT NULL DEFAULT 0,
    extra       TEXT    NOT NULL DEFAULT '',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_bench_category ON benchmark_results(category, algorithm);

-- ---------------------------------------------------------------------
-- users: minimal auth (passwords are hashed with Werkzeug's PBKDF2)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'viewer',
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- Optional SQL-side index (SQLite FTS5 when the local build provides it).
-- The application's own Trie/Hash/TF-IDF index does NOT depend on this -
-- it exists so we can show a pure-SQL LIKE/BM25 baseline for comparison.
-- database.py degrades gracefully if FTS5 is unavailable.
-- ---------------------------------------------------------------------
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    title, content, keywords,
    tokenize='unicode61'
);
