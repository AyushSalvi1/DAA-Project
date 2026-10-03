# NexaSearch

### *Search Smarter. Analyze Faster.*

An **algorithmic information-retrieval engine** built for a *Design and Analysis
of Algorithms* (DAA) project — a working search engine where **every algorithm
is implemented by hand** and every stage of the pipeline is measurable,
visualisable and testable from inside the UI.

No search framework, no NLP library, no machine-learning package, no external
API. Python's standard library plus Flask, and that is all.

---

## 1. Quick start

```bash
cd "C:\DAA Project"
python -m pip install -r requirements.txt
python app.py
```

Then open <http://127.0.0.1:5000>.

On the first run the application creates `instance/nexasearch.db`, seeds **49
sample documents** (≈2,070 distinct terms), builds the inverted index and
computes PageRank — roughly two seconds. Later runs reuse the database.

```bash
python -m pytest -q          # 233 tests
```

Optional environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `NEXASEARCH_DB` | `instance/nexasearch.db` | SQLite file location |
| `NEXASEARCH_HOST` / `NEXASEARCH_PORT` | `127.0.0.1` / `5000` | bind address |
| `NEXASEARCH_DEBUG` | `0` | set to `1` for the Flask reloader |
| `NEXASEARCH_SECRET` | dev value | Flask session signing key |

The Flask CLI works too: `flask --app app run` (the module exposes the
`create_app` factory and never boots an index at import time).

**Demo administrator** — `admin` / `nexasearch123` at `/admin/login`.
Passwords are stored as Werkzeug PBKDF2 hashes; `/admin/` and `/admin/stats`
are read-only dashboards, every mutating action is gated behind the session.

---

## 2. What the project does

A query travels through a real retrieval pipeline, and the results page shows
you exactly which algorithm ran at each stage and how long it took:

```
"binary" "search" graph
        │
        ▼
 1  normalise ▸ tokenise ▸ stop-words ▸ stem        (hand-written)
 2  vocabulary check per term                        Trie          O(L)
 3  posting-list fetch                               Hash table    O(1) avg
 4  candidate set = union of posting lists
 5  content relevance                                TF-IDF cosine
 6  phrase signal for "quoted" terms                 KMP + Rabin-Karp
 7  title / keyword signals
 8  authority signal                                 PageRank (cached)
 9  weighted fusion                                  ranking.py
10  final ordering                                   Merge Sort (stable)
11  snippet + whole-word <mark> highlighting
```

Ranking formula (`algorithms/ranking.py`):

```
score(d) = 0.30·title + 0.25·keyword + 0.25·content + 0.10·phrase + 0.10·graph
full coverage of every query term  →  × 1.12
```

The content signal is the TF-IDF cosine rescaled against the best candidate
(cosines are tiny for long documents, so a raw cosine would vanish into
rounding error), and the graph signal is PageRank min-max normalised across the
corpus. Both normalisations are reported in the score breakdown on the results
page.

---

## 3. The algorithms (all hand-written)

| # | Algorithm | Module | Complexity | Where it is used |
| --- | --- | --- | --- | --- |
| 1 | Linear search | `algorithms/linear_search.py` | O(n) best O(1) / worst O(n) | honest baseline in every comparison |
| 2 | Binary search (iterative + recursive) | `algorithms/binary_search.py` | O(log n), O(1) / O(log n) stack | sorted-title lookup; rejects unsorted input |
| 3 | Trie | `algorithms/trie.py` | O(L) insert/search, O(L+P) prefix | vocabulary, autocomplete, phrase walks |
| 4 | Hash table — chaining **and** linear probing | `algorithms/hash_table.py` | O(1) avg, O(n) worst | term→postings, doc-id→document |
| 5 | KMP (LPS failure function) | `algorithms/kmp.py` | O(n+m) | quoted-phrase search |
| 6 | Rabin–Karp (rolling hash) | `algorithms/rabin_karp.py` | O(n+m) avg, O(nm) worst | cross-check on KMP |
| 7 | Naive / brute force | `algorithms/kmp.py` | O(nm) worst | the baseline KMP beats |
| 8 | Binary min-heap | `algorithms/heap.py` | O(log n) push/pop, O(n) Floyd heapify | Dijkstra priority queue |
| 9 | BFS | `algorithms/bfs.py` | O(V+E) | "k-hop related documents", levels |
| 10 | DFS (iterative **and** recursive) | `algorithms/dfs.py` | O(V+E) | deep dives, components, cycle detection |
| 11 | Dijkstra | `algorithms/dijkstra.py` | O((V+E) log V) | similarity-weighted document distances |
| 12 | Merge sort (stable) | `algorithms/merge_sort.py` | Θ(n log n) | final result ordering |
| 13 | Quick sort (median-of-three) | `algorithms/quick_sort.py` | Θ(n log n) avg, Θ(n²) worst | alternative ordering mode |
| 14 | Heap sort | `algorithms/heap.py` | Θ(n log n) | third benchmark |
| 15 | TF-IDF + cosine | `algorithms/tfidf.py` | O(q·d) scoring | content signal |
| 16 | Weighted relevance fusion | `algorithms/ranking.py` | O(d log d) | final score |
| 17 | PageRank | `algorithms/pagerank.py` | O(I·(V+E)) | authority signal, "most connected" |

Every one of these returns its **comparison counts, levels/partitions/steps and
wall-clock time**, which is what the Algorithm Lab renders. The step traces are
produced during the real run — there is no separate "demo" code path.

`docs/ALGORITHMS.md` gives each one its correctness invariant, the recurrence
behind the complexity class, and the specific implementation detail that makes
the bound hold (LPS fallback in KMP, insertion counters in the heap, tombstones
in open addressing, Floyd heapify, …).

---

## 4. Pages

| Route | What it shows |
| --- | --- |
| `/` | hero search, corpus statistics, category chips, top terms, recent searches |
| `/search` | ranked results, per-signal score breakdown, phrase report, pipeline timings |
| `/browse` | filter / sort / paginate the corpus |
| `/document/<id>` | full text, metadata, PageRank, related documents |
| `/graph` | canvas rendering of the document graph + **BFS / DFS / Dijkstra** runner |
| `/algorithms/` | analysis dashboard: complexity table, index statistics, PageRank |
| `/algorithms/visualizer` | interactive Algorithm Lab (10 visualisers) |
| `/algorithms/complexity` | growth curves O(1) … O(2ⁿ) and a class reference |
| `/admin/` | dashboard, search history, full CRUD, bulk import, reindex |
| `/admin/stats` | system statistics (`?format=json` downloads them) |

### JSON API

```
GET /api/health                     service + index status
GET /api/search?q=…&limit=…&category=…&sort=…
GET /api/document/<id>              document + PageRank + related
GET /api/autocomplete?q=…           Trie prefix suggestions
GET /api/terms?prefix=…&limit=…     vocabulary under a prefix (or top terms)
GET /api/index                      index, graph, TF-IDF and hash-table statistics
GET /api/stats                      aggregate dashboard payload
GET /api/categories                 category counts
GET /api/history?limit=…            recent search history
GET /graph/traverse?algorithm=bfs|dfs|dijkstra&start=&goal=&depth=
```

---

## 5. Project layout

```
app.py                     Flask application factory, filters, error handlers, CLI
algorithms/                every data structure and algorithm, from scratch
  linear_search.py           binary_search.py     hash_table.py    trie.py
  kmp.py                     rabin_karp.py        heap.py          bfs.py
  dfs.py                     dijkstra.py          merge_sort.py    quick_sort.py
  tfidf.py                   ranking.py           pagerank.py      registry.py
indexing/
  text_processor.py         normalise ▸ tokenise ▸ stop-words ▸ stem ▸ snippet
  indexer.py                Trie + hash table inverted index, field weighting
  graph_builder.py          [[slug]] links, Jaccard similarity edges, PageRank
  search_engine.py          the 11-stage query pipeline
database/
  schema.sql                documents, keywords, document_keywords, search_history,
                            search_statistics, document_links, document_graph_stats,
                            benchmark_results, users, documents_fts (FTS5, optional)
  database.py               parameterised repository (no SQL string building)
core/
  corpus_part1..3.py        49 original educational documents
  seed_data.py              seeding + .txt import
  service.py                database + index + graph + TF-IDF lifecycle
  benchmark.py              searching / string / sorting / graph benchmarks
routes/                     search_routes, algorithm_routes, admin_routes, api_routes
templates/  static/         Jinja pages, CSS, canvas visualisers
tests/                      test_algorithms.py (125) + test_integration.py (108)
docs/ALGORITHMS.md           per-algorithm proof sketch, recurrence and complexity
data/sample_documents/      the same corpus as importable .txt files
```

---

## 6. Design notes worth marking

**Why an inverted index at all?** Because linear search over 49 documents is
already fast — the point is not speed, it is that the *same* query against
10⁵ documents flips the cost from O(n) to O(|posting list|), and the project
can *show* that with the linear/binary/hash/trie comparison table.

**A Trie cannot delete.** Removing a document therefore rebuilds the trie from
the surviving posting lists (`DocumentIndex.rebuild_trie`). This is a genuine
trade-off of the data structure, not a shortcut.

**The index is keyed by stems, the UI shows real words.** `"sorting"` and
`"sort"` share the trie leaf `sort` (so both queries hit), while the
autocomplete box reports the most frequent original spelling — you never see
"learn" suggested to a user.

**Highlighting respects word boundaries.** A naive `str.replace` marks `graph`
inside `cryptography`; `text_processor.snippet` uses look-around guards and
HTML-escapes first, so a document body can never inject markup into a page.

**PageRank scores are returned unrounded.** Rounding each of 49 scores to six
decimals makes them sum to 0.999998, which looks exactly like a failure to
converge. Only the displayed ranking is rounded.

**KMP never moves the text pointer backwards.** Both the LPS construction and
the search loop retry the *same* character after a fallback; the tests
cross-check 3,000 random input pairs against the brute-force matcher.

**Determinism.** Sets never leak into output (`BFS.visited`, Dijkstra's settle
order, hash-table iteration) — Python randomises string hashing per process, so
a `set` of node names would produce a different "traversal order" on every run.

---

## 7. Tests

```
tests/test_algorithms.py    125 tests - correctness *and* cost behaviour
                            (probe counts, heap orderings, LPS arrays,
                            agreement with brute force, convergence)
tests/test_integration.py   108 tests - database CRUD, index maintenance, graph
                            invariants, the full ranking pipeline, every page,
                            the Algorithm Lab, the JSON API, admin auth and
                            the document lifecycle, plus an end-to-end check
                            that a document created through the UI is
                            immediately searchable
```

Tests run against a throw-away SQLite file in a temp directory, so the real
corpus is never touched. KMP is fuzz-checked against naive search over 3,000
random `(text, pattern)` pairs; the corpus tests assert that KMP and
Rabin–Karp agree on every phrase they examine.

```bash
python -m pytest -q                     # 233 tests
python -m pytest tests/test_algorithms.py -q
python -m pyflakes algorithms core database indexing routes tests app.py
```

---

## 8. Sample corpus

49 original documents written for this project (no external text), grouped by
category: Artificial Intelligence, Machine Learning, Data Science, Cloud
Computing, Cybersecurity, Computer Networks, Operating Systems, Databases,
Algorithms, Web Development, Programming (Java/Python), and DevOps. Documents
cross-reference each other with `[[document-slug]]`, which is what produces the
"reference" edges of the document graph; keyword overlap produces the
"similarity" edges.

---

## 9. Security and robustness notes

* every SQL statement uses bound parameters; dynamic identifiers (sort column,
  direction) go through an explicit allow-list — `'; DROP TABLE documents; --`
  is stored as a literal search string and deletes nothing;
* document bodies are HTML-escaped before any markup is inserted;
* uploads are extension-checked (`.txt`, `.md`) and capped at 2 MB per file
  and 20 files per import;
* the search history table is trimmed to its most recent 500 rows;
* the lab endpoints accept JSON, form posts or query strings and reject
  oversized or non-numeric input with a 400 instead of a 500.