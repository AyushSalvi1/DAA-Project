# Algorithm catalogue

Every algorithm below is implemented from scratch in `algorithms/`. This
document states the recurrence, the invariant that proves it correct, the cost
in the *actual* counters the code maintains, and where the algorithm is used
inside the search engine. Everything here is exercised by
`tests/test_algorithms.py`.

---

## 1. Linear search — `linear_search.py`

Sequential scan; returns the first index whose projected value equals the
projected key.

* **Invariant.** After examining `data[0..i]`, no match occurs before `i`.
  Holds because the loop returns immediately on the first equality.
* **Cost.** Exactly `len(data)` key comparisons in the worst case, 1 in the
  best case → **Θ(n) / Θ(1)**, space **Θ(1)**.
* **Note.** `key_func` is applied to the *key as well as* the elements;
  projecting only the data is the classic bug that makes a case-insensitive
  search silently fail.
* **Used for.** The honest baseline in the linear/binary/hash/trie comparison,
  and the fallback scan when no query term exists in the vocabulary.

## 2. Binary search — `binary_search.py`

Halving search over a **sorted** sequence, iterative and recursive.

* **Invariant.** The key, if present, always lies inside `[low, high]`; each
  probe compares the midpoint and discards the half that cannot contain it,
  so the range shrinks by half every iteration.
* **Cost.** `⌈log₂(n+1)⌉` comparisons → **O(log n)**, space **O(1)**
  iterative / **O(log n)** call stack recursive.
* **Note.** Unsorted input raises `ValueError` instead of returning a wrong
  answer — the log n guarantee depends entirely on that pre-condition.
  Sortedness is verified under the *same* projection used for the search.
* **Used for.** Sorted-title lookup in the search-strategy comparison.

## 3. Trie (prefix tree) — `trie.py`

Each node is one character position and stores its children, a terminal flag,
a posting list (`doc_ids`) and a frequency.

* **Invariant.** After inserting a word `w`, following `w` from the root
  reaches exactly one node marked terminal; shared prefixes share nodes.
* **Cost.** insert **O(L)**, exact search **O(L)**, prefix enumeration
  **O(L + P)** (P = explored subtree), space **Θ(total characters)**.
  Independent of dictionary size — the reason a trie is O(L) and a hash table
  is "O(1) on average but O(L) to hash the key".
* **Note.** A trie has no cheap delete, so removing a document rebuilds the
  trie from the surviving posting lists. Each node also remembers the most
  frequent original spelling of its term, because the index is keyed by *stems*
  while the user must be shown real words.
* **Used for.** Vocabulary checks, autocomplete, `/api/autocomplete`.

## 4. Hash table — `hash_table.py`

Two complete collision strategies, both hand-written:

| | Separate chaining | Open addressing (linear probing) |
| --- | --- | --- |
| average | O(1) | O(1) for load factor α < 0.75 |
| worst | O(n) (all keys collide) | O(n) |
| resize | doubling at α > 0.75 | doubling at α > 0.75 |

* **Hash function.** djb2, `h = h·33 + c`; a polynomial base-31 variant is
  provided for comparison.
* **Invariant.** Every key is reachable from `hash(key) mod capacity`;
  lookups therefore only ever inspect one bucket (chaining) or one probe
  sequence (open addressing).
* **Note.** Deleted open-addressing slots hold a **tombstone**, not `None`:
  clearing the slot truncates the probe chain and hides keys stored further
  along it.
* **Used for.** `term → posting list` and `doc_id → document` maps — the two
  hot lookups in the query path. A Python `dict` is only used for the
  serialised view returned to the UI.

## 5. KMP — `kmp.py`

Pre-computes the **LPS array** (`lps[i]` = longest *proper* prefix of
`pattern[0..i]` that is also a suffix of it) so the text pointer never moves
backwards after a mismatch.

* **LPS invariant.** After processing `pattern[0..i]`, `lps[0..i]` are the
  correct failure values; on a mismatch the fallback branch re-tests the
  **same** character at `lps[length-1]` and must *not* advance `i` — the
  obvious-looking `i += 1` there loses matches.
* **Search invariant.** If a match starts at position `s`, then on a mismatch
  at `i` the next possible start lies in `[s+1, s + lps[matched]]`, so
  restarting anywhere inside the matched prefix is provably unnecessary.
* **Cost.** build LPS **O(m)**, search **O(n + m)** time and **O(m)** space —
  i.e. O(n) in the text length and independent of the pattern length. Naive
  worst case is `(n−m+1)·m`.
* **Verified.** 3,000 random `(text, pattern)` pairs cross-checked against the
  brute-force matcher, plus overlap cases (`"abab"` in `"abababab"` → 0, 2, 4).
* **Used for.** Quoted-phrase matching.

## 6. Rabin–Karp — `rabin_karp.py`

Polynomial rolling hash over a sliding window:

```
H(i+1) = (H(i) − text[i]·B^(m−1))·B + text[i+m]   (mod p)
```

* **Invariant.** `window` always equals the hash of `text[i : i+m]`; a hash
  equality is only a *candidate*, never a proof, so every candidate is
  verified character by character.
* **Cost.** Pre-filter **O(n)**, verification O(m) per true candidate →
  **O(n + m) average, O(n·m) worst case** (every window collides), space
  **O(1)**.
* **Used for.** An independent cross-check of KMP on the same corpus; the
  search page reports whether the two agree on every phrase they examined.

## 7. Binary min-heap — `heap.py`

Complete binary tree in a flat list, so index arithmetic replaces pointers:
`parent(i) = (i−1)//2`, `left = 2i+1`, `right = 2i+2`.

* **Invariant.** `heap[parent] ≤ heap[child]`, therefore the root is the
  global minimum.
* **Cost.** push / extract-min **O(log n)**, peek **O(1)**, Floyd heapify
  **Θ(n)** (not Θ(n log n)), space **Θ(n)**.
* **Note.** Entries carry an insertion counter, so equal priorities come out
  FIFO. Without it the heap orders ties by array position, which silently
  changes Dijkstra's settle order between runs.
* **Used for.** Dijkstra's priority queue, and heap sort as the third sorting
  benchmark.

## 8. BFS — `bfs.py`

FIFO queue (`collections.deque`, hand-written traversal).

* **Invariant.** Vertices leave the queue in non-decreasing depth, so the
  first time a vertex is reached it is via a **shortest path in edge count**.
* **Cost.** Each vertex enqueued once, each edge examined once from each
  endpoint → **O(V + E)** time, **O(V)** space. Reported as
  `edge_examinations`.
* **Note.** `visited` is reported in *discovery* order; iterating a Python set
  would randomise the output on every process start.
* **Used for.** "documents within k hops", the BFS levels panel on `/graph`.

## 9. DFS — `dfs.py`

Explicit LIFO stack *and* a recursive formulation that reports the interpreter
call stack depth.

* **Invariant.** A vertex is marked visited the moment it is popped/entered,
  so it is expanded at most once; the stack size is bounded by the path length.
* **Cost.** **O(V + E)** time, **O(V)** space (`max_call_depth` proves the
  stack bound).
* **Used for.** Components, cycle detection (white/grey/black colouring), and
  "deep dive" traversal on `/graph`.

## 10. Dijkstra — `dijkstra.py`

Settle the closest unsettled vertex, relax its out-edges, repeat.

* **Invariant.** When a vertex is settled its distance is final: any shorter
  path would have to arrive through an unsettled vertex whose distance is
  smaller, which contradicts the extract-min choice. Requires **non-negative
  edge weights** — the code rejects a negative edge explicitly instead of
  returning nonsense.
* **Cost.** With a binary heap **O((V + E) log V)** time, **O(V)** extra
  space; with an adjacency matrix and linear extraction it would be O(V²).
* **Used for.** Document-to-document "shortest path" over the similarity graph,
  where edge weight `2 − similarity` makes similar documents cheap to reach.

## 11. Merge sort — `merge_sort.py`

Top-down divide and conquer.

* **Recurrence.** `T(n) = 2T(n/2) + Θ(n)` → **Θ(n log n)** for every input
  (no O(n) best case, unlike insertion sort).
* **Invariant.** `merge(a, b)` returns the sorted union of two sorted runs and
  emits the smallest remaining element each step, so it is correct by
  induction on the run length.
* **Space.** **Θ(n)** merge buffer + **Θ(log n)** call stack. **Stable** — it
  takes the left run on ties (`<=`), which keeps equally relevant documents in
  their earlier tie-break order.
* **Used for.** The default result ordering in the search pipeline.

## 12. Quick sort — `quick_sort.py`

Lomuto partition, median-of-three pivot, **explicit stack**.

* **Recurrence.** balanced `T(n) = 2T(n/2) + Θ(n)` → Θ(n log n); skewed
  `T(n) = T(n−1) + Θ(n)` → **Θ(n²)**.
* **Invariant.** After partitioning on `high`, everything in `[low, i]` is
  ≤ pivot and everything in `[i+2, high]` is > pivot, so both sub-ranges can
  be solved independently.
* **Space.** **O(log n)** expected. The larger side is pushed first so the
  smaller side is processed immediately, which caps the explicit stack at
  O(log n) even on skewed input.
* **Note.** Median-of-three keeps already-sorted input in the balanced case —
  exactly the shape a ranking pipeline hands it. Not stable; in place.
* **Used for.** The `sort=quick` ordering mode and the sorting benchmark.

## 13. Heap sort — `heap.py`

Repeated extract-min.

* **Invariant.** Each extraction returns the smallest remaining element, so the
  output is ascending after n extractions.
* **Cost.** **Θ(n log n)** time, **Θ(n)** space (it is not in-place).

## 14. TF-IDF + cosine — `tfidf.py`

```
TF(t,d)  = count(t in d) / |d|
IDF(t)   = ln( (1 + N) / (1 + df(t)) ) + 1          (smoothed, always > 0)
TFIDF    = TF · IDF
score(d,q) = cos( TFIDF(d), TFIDF(q) )
```

* **Cost.** Model build **O(total tokens)**; one query is
  **O(Σ df(t))** over its terms because the vectors are sparse dictionaries and
  only non-zero coordinates are touched — not O(V·L).
* **Note.** IDF is smoothed so a term appearing in every document still scores
  a small positive value instead of zero.
* **Used for.** The content signal (weight 0.25). The raw cosine is rescaled
  against the best candidate in the pipeline, because a cosine of 0.003 on a
  long document would otherwise be invisible next to the title signal.

## 15. Weighted ranking — `ranking.py`

```
FinalScore(d,q) = Σ wᵢ · signalᵢ        (weights sum to 1)
                × field boosts           (full coverage ×1.12, phrase-in-title ×1.15, …)
                + popularity tie-break   (≤ 0.01)
```

* **Why linear.** Every signal is normalised to [0, 1], so the weights are
  directly comparable and the score stays interpretable — "why is title worth
  0.30?" has a checkable answer, and the results page prints the contribution
  of each signal per document.
* **Cost.** O(d) scoring + O(d log d) ordering; candidates ≥ 12 use the
  project's own Merge Sort, smaller lists use an insertion scan.
* **Used for.** The final ordering of every search.

## 16. PageRank — `pagerank.py`

Random-surfer model with damping `d = 0.85`:

```
P(t+1) = d · Σ_i P(t,i) · (1 / outdeg(i)) · M[i][j]  +  (1 − d) / N
```

Dangling nodes (no out-edges) redistribute their mass to every node.

* **Implementation note.** The dense formulation is O(N²) per iteration; the
  edge-list formulation used here is **O(E)** per iteration for the same sum.
* **Convergence.** Iterates until the L1 norm between successive iterations is
  below `1e-6`, capped at 200 iterations. Scores are returned **unrounded** —
  rounding 49 values to six decimals makes them sum to 0.999998, which looks
  exactly like a failure to converge.
* **Cost.** **O(I · (V + E))** time, **O(V + E)** space. On the sample corpus
  it converges in ~52 iterations.
* **Used for.** The graph signal (0.10) and the "most connected document"
  ranking on the dashboard.

---

## Supporting structures

### Inverted index — `indexing/indexer.py`

`term → sorted (doc_id, tf)` postings, with **field weighting** (a keyword-list
token counts ×4, a title token ×3, a body token ×1). Building it is
**O(total tokens)**; answering a query costs **O(Σ df(t))** for the query's
terms instead of scanning documents.

### Document graph — `indexing/graph_builder.py`

Two edge sources: explicit `[[slug]]` cross-references (weight 1.0) and
keyword-similarity edges with a Jaccard overlap plus a same-category bonus
(weight capped at 1.0). Construction is **O(V²)** over 49 documents — fine
here, and the honest statement of when an inverted-index-free approach stops
being acceptable. The edge weight is inverted (`2 − similarity`) so that
Dijkstra minimises distance to *similar* documents.

### Text processing — `indexing/text_processor.py`

Normalise (NFKD, strip punctuation, collapse whitespace) → tokenise → drop
stop words → Porter-lite stem. Each stage is **O(L)** in the input length.
Snippet highlighting HTML-escapes the body and matches on **word boundaries**,
so `graph` is not marked inside `cryptography` and no document can inject
markup into a page.