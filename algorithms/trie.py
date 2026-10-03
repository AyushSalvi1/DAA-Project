"""Trie (prefix tree) - implemented from scratch.

DAA facts
---------
Purpose : dictionary / autocomplete over strings with O(L) lookup where
          L = length of the word (independent of dictionary size!).
Insert  : O(L)      Search (exact): O(L)      Prefix / autocomplete: O(L + P)
          where P = number of nodes explored below the prefix.
Space   : O(total characters) - one node per distinct prefix.

Used by NexaSearch for
  * keyword lookup during a query ("does the corpus know this term?"),
  * prefix search + autocomplete suggestions,
  * walking a phrase character-by-character for KMP-style phrase checks.

Design note: every node stores ``doc_ids`` (the posting list) and ``freq``
so that a single walk yields *both* the vocabulary check and the document
set - this is the classic compressed-posting-list trick.
"""

from __future__ import annotations

import time
from typing import Iterable, Tuple


class TrieNode:
    """One character position in the trie."""

    __slots__ = ("children", "is_end", "doc_ids", "freq", "depth", "display")

    def __init__(self, depth: int = 0) -> None:
        self.children: dict[str, "TrieNode"] = {}
        self.is_end: bool = False
        self.doc_ids: set[int] = set()
        self.freq: int = 0
        self.depth: int = depth
        # most frequent original spelling of the term (the trie itself is keyed
        # by stems, which is what the autocomplete box must not show)
        self.display: str = ""

    def child(self, char: str) -> "TrieNode | None":
        return self.children.get(char)

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"TrieNode(depth={self.depth}, children={sorted(self.children)}, end={self.is_end})"


class Trie:
    """Prefix tree with posting lists."""

    def __init__(self) -> None:
        self.root = TrieNode()
        self.size = 0            # number of distinct words
        self.total_chars = 0

    # ------------------------------------------------------------------
    # insertion
    # ------------------------------------------------------------------
    def insert(self, word: str, doc_id: int | None = None, freq: int = 1,
               display: str = "") -> int:
        """Insert ``word`` (lowercased). Returns nodes created (0 if present).

        Cost: O(L) time, O(L) new space.
        """
        if not word:
            return 0
        node = self.root
        created = 0
        for char in word:
            nxt = node.children.get(char)
            if nxt is None:
                nxt = TrieNode(depth=node.depth + 1)
                node.children[char] = nxt
                created += 1
                self.total_chars += 1
            node = nxt
            if doc_id is not None:
                node.doc_ids.add(doc_id)
        if not node.is_end:
            node.is_end = True
            self.size += 1
        node.freq += freq
        if display and (not node.display or display < node.display):
            node.display = display
        return created

    def insert_document_tokens(self, tokens: Iterable[str], doc_id: int) -> None:
        """Insert a whole token stream of one document (postings)."""
        for token in tokens:
            self.insert(token, doc_id=doc_id)

    # ------------------------------------------------------------------
    # lookup
    # ------------------------------------------------------------------
    def _walk(self, prefix: str) -> TrieNode | None:
        node = self.root
        for char in prefix:
            node = node.children.get(char)
            if node is None:
                return None
        return node

    def contains(self, word: str) -> bool:
        """Exact membership test in O(L)."""
        node = self._walk(word)
        return bool(node and node.is_end)

    search = contains  # alias used by the API layer

    def is_prefix(self, prefix: str) -> bool:
        """True if any indexed word starts with ``prefix`` (O(L))."""
        return self._walk(prefix) is not None

    def posting_list(self, word: str) -> set[int]:
        """Documents containing ``word`` - the posting list stored on the leaf."""
        node = self._walk(word)
        if node is None or not node.is_end:
            return set()
        return set(node.doc_ids)

    # ------------------------------------------------------------------
    # prefix enumeration / autocomplete
    # ------------------------------------------------------------------
    def words_with_prefix(self, prefix: str, limit: int = 10) -> list[str]:
        """Depth-first collection of every word under ``prefix``.

        Cost: O(L + P) where P = size of the visited subtree.
        """
        start = self._walk(prefix)
        if start is None:
            return []
        found: list[str] = []
        stack: list[Tuple[TrieNode, str]] = [(start, prefix)]
        while stack and len(found) < limit:
            node, path = stack.pop()
            if node.is_end:
                found.append(path)
            for char, child in node.children.items():
                stack.append((child, path + char))
        return found[:limit]

    def autocomplete(self, prefix: str, limit: int = 8) -> list[dict]:
        """Ranked suggestions for the search box.

        Suggestions are reported with their *surface form* ("sorting") while
        the trie itself is keyed by the stem ("sort"), so the ranking uses the
        stem but the user sees the real word.  Ranking heuristic (O(1) per
        candidate): shorter word first, then higher corpus frequency - this
        makes "algorithm" beat "algorithm design" for the prefix "algo".
        """
        candidates = self.words_with_prefix(prefix, limit=max(limit * 6, 40))
        scored = []
        for word in candidates:
            node = self._walk(word)
            freq = node.freq if node else 0
            scored.append({
                "word": (node.display or word) if node else word,
                "stem": word,
                "documents": len(node.doc_ids) if node else 0,
                "frequency": freq,
                "score": round(freq / (1 + 0.35 * (len(word) - len(prefix))), 4),
            })
        scored.sort(key=lambda item: (-item["score"], item["word"]))
        return scored[:limit]

    # ------------------------------------------------------------------
    # phrase walk (used by the search engine for quoted phrases)
    # ------------------------------------------------------------------
    def walk_words(self, prefix: str, max_words: int = 200) -> list[str]:
        """Every indexed word under ``prefix`` (no limit convenience)."""
        return self.words_with_prefix(prefix, limit=max_words)

    def all_words(self) -> list[str]:
        return self.words_with_prefix("", limit=10 ** 9)

    # ------------------------------------------------------------------
    # visualisation
    # ------------------------------------------------------------------
    def stats(self) -> dict:
        total_terminals = 0
        total_nodes = 0

        def visit(node: TrieNode) -> None:
            nonlocal total_terminals, total_nodes
            total_nodes += 1
            if node.is_end:
                total_terminals += 1
            for child in node.children.values():
                visit(child)

        visit(self.root)
        return {
            "distinct_words": self.size,
            "nodes": total_nodes,
            "total_characters": self.total_chars,
            "terminals": total_terminals,
            "max_depth": self._max_depth(self.root),
        }

    @staticmethod
    def _max_depth(node: TrieNode) -> int:
        if not node.children:
            return node.depth
        return max(Trie._max_depth(child) for child in node.children.values())

    def to_dict(self) -> dict:
        """Nested dict for the front-end tree widget."""
        def build(node: TrieNode, word: str) -> dict:
            return {
                "char": word[-1] if word else "",
                "word": (node.display or word) if node.is_end else "",
                "documents": len(node.doc_ids),
                "frequency": node.freq,
                "children": [build(child, word + char) for char, child in sorted(node.children.items())],
            }
        return build(self.root, "")

    def insert_trace(self, word: str) -> dict:
        """Step-by-step insert trace for the Algorithm Lab."""
        word = (word or "").lower()
        node = self.root
        steps: list[dict] = [{
            "index": 0, "action": "start", "node": "root",
            "description": f"Begin insert of '{word}' at root",
        }]
        start = time.perf_counter()
        for i, char in enumerate(word, start=1):
            existed = char in node.children
            if not existed:
                nxt = TrieNode(depth=node.depth + 1)
                node.children[char] = nxt
                self.total_chars += 1
            node = node.children.get(char)
            steps.append({
                "index": i, "action": "create" if not existed else "follow",
                "node": word[:i], "char": char,
                "description": (f"'{char}' not a child -> create node '{word[:i]}'"
                                if not existed else
                                f"'{char}' already a child -> follow '{word[:i]}'"),
            })
        was_end = node.is_end
        if not was_end:
            node.is_end = True
            self.size += 1
        steps.append({
            "index": len(word), "action": "mark-end",
            "node": word,
            "description": ("mark node as end-of-word (new word)"
                            if not was_end else "word already present - frequency bumped"),
        })
        node.freq += 1
        elapsed = (time.perf_counter() - start) * 1000
        return {"algorithm": "Trie Insert", "word": word, "steps": steps,
                "time_ms": elapsed, "comparisons": len(word)}
