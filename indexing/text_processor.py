"""Text processing pipeline: normalise -> tokenise -> stop-words -> stem.

Everything is hand-written (no NLTK, no regex library beyond ``re``) so the
token stream that feeds the Trie, hash table and TF-IDF model is fully
inspectable.

Stages
------
1. **Normalise**  - lowercase, strip accents/punctuation, collapse whitespace.
2. **Tokenise**   - split on non-alphanumeric boundaries (keeps C++ / O(n)
                    style tokens usable by stripping trailing punctuation).
3. **Stop words** - remove very common English function words (a compact
                    hand-listed set, not a downloaded corpus).
4. **Stem**       - a simplified suffix-stripping stemmer (Porter-lite):
                    plurals, -ing, -ed, -tion, -ment ... Good enough for a
                    demo and O(L) per token.

Stemming is intentionally simple: the goal is that "algorithms" and
"algorithm" land on the *same* trie leaf, not linguistic perfection.
"""

from __future__ import annotations

import re
import unicodedata

STOP_WORDS: set[str] = {
    "a", "about", "above", "after", "again", "all", "also", "am", "an",
    "and", "any", "are", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "did", "do", "does", "doing",
    "down", "during", "each", "few", "for", "from", "further", "had", "has",
    "have", "having", "he", "her", "here", "hers", "herself", "him", "himself",
    "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off",
    "on", "once", "only", "or", "other", "our", "ours", "ourselves", "out",
    "over", "own", "same", "she", "should", "so", "some", "such", "than",
    "that", "the", "their", "theirs", "them", "themselves", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "will", "with", "you", "your", "yours",
    "yourself", "yourselves",
}

# multi-word stop phrases that should never become part of a phrase search
STOP_PHRASES: set[str] = {"what is", "how to", "tell me about", "explain"}

TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)*|[a-z]\([a-z]\)", re.IGNORECASE)


def normalize(text: str | None) -> str:
    """Lowercase, strip accents, drop punctuation, collapse whitespace."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", str(text))
    ascii_text = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^a-z0-9\s]", " ", ascii_text)
    return re.sub(r"\s+", " ", ascii_text).strip()


def tokenize(text: str | None, remove_stopwords: bool = True) -> list[str]:
    """Split normalised text into index tokens."""
    normalized = normalize(text)
    if not normalized:
        return []
    tokens = TOKEN_RE.findall(normalized)
    if remove_stopwords:
        tokens = [token for token in tokens if token not in STOP_WORDS and len(token) > 1]
    return tokens


def stem(token: str) -> str:
    """Simplified suffix-stripping stemmer (Porter-lite)."""
    if len(token) <= 3 or not token.isalpha():
        return token
    for suffix in ("ational", "iveness", "fulness", "ousness", "ization",
                   "isation", "ability", "ibility", "ement", "ments", "ment",
                   "ness", "tion", "sion", "ing", "ers", "est", "ies", "ed",
                   "es", "ly", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            base = token[: -len(suffix)]
            if suffix == "ies":
                return base + "y"
            if suffix in ("ing", "ed", "es", "ly"):
                # restore a dropped final 'e' for silent-e roots (move->mover)
                if len(base) > 2 and base[-1] == base[-2] and base[-1] not in "aeiou":
                    base = base[:-1]
                if len(base) > 2 and base.endswith(("at", "bl", "iz", "us", "iv", "ou", "ur")):
                    base += "e"
            return base
    return token


def analyze(text: str | None, remove_stopwords: bool = True,
            do_stem: bool = True) -> dict:
    """Full pipeline - this is what the indexer and query parser both call.

    Returns ``{"raw", "normalized", "tokens", "unique", "stop_words_removed",
    "pairs"}`` so the UI can show exactly what the engine did to the query.
    ``pairs`` holds ``(stem, surface_form)`` for every kept token, which lets
    the index match on stems while still displaying real words.
    """
    raw_tokens = tokenize(text, remove_stopwords=False)
    kept = [t for t in raw_tokens if t not in STOP_WORDS and len(t) > 1]
    tokens = [stem(t) if do_stem else t for t in kept]
    pairs = [(stem(t) if do_stem else t, t) for t in kept]
    return {
        "raw": text or "",
        "normalized": normalize(text),
        "tokens": tokens,
        "unique": sorted(set(tokens)),
        "stop_words_removed": [t for t in raw_tokens if t in STOP_WORDS or len(t) <= 1],
        "length": len(tokens),
        "pairs": pairs,
    }


def analyze_pairs(text: str | None, remove_stopwords: bool = True) -> list[tuple[str, str]]:
    """``[(stem, original_surface_form), ...]`` for every kept token.

    The inverted index is keyed by the stem (so "sorting" and "sort" collide),
    but a user typing in the search box must be *shown* real words. Keeping
    the pair lets the indexer display "sorting" while matching "sort".
    """
    return analyze(text, remove_stopwords=remove_stopwords)["pairs"]


def analyze_query(query: str) -> dict:
    """Query-side analysis: detect phrases in double quotes, then analyse."""
    phrases = extract_phrases(query)
    remaining = re.sub(r"\"[^\"]*\"", " ", query or "")
    analysis = analyze(remaining)
    analysis["phrases"] = phrases
    analysis["is_empty"] = not analysis["tokens"] and not phrases
    return analysis


def extract_phrases(query: str | None) -> list[str]:
    """Pull "quoted phrases" out of the query and normalise them."""
    if not query:
        return []
    phrases = []
    for match in re.finditer(r"\"([^\"]+)\"", query):
        phrase = normalize(match.group(1))
        if len(phrase.split()) >= 1 and phrase not in STOP_PHRASES:
            phrases.append(phrase)
    return phrases


def _boundary_pattern(term: str) -> re.Pattern | None:
    """Case-insensitive pattern that only matches ``term`` on word boundaries.

    Without the look-around guards, "graph" would highlight inside
    "cryptography" - the classic substring-highlighting bug.
    """
    if not term:
        return None
    return re.compile(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", re.IGNORECASE)


def snippet(text: str, terms: list[str], width: int = 220,
            highlight_tag: str = "mark") -> tuple[str, list[str]]:
    """Build a result snippet centred on the first matching term.

    Returns ``(html, matched_terms)``.  The text is HTML-escaped before the
    ``<mark>`` tags are inserted, so user content can never inject markup, and
    only whole-word occurrences are marked.
    """
    from html import escape

    if not text:
        return "", []

    unique_terms = sorted({t for t in terms if t}, key=len, reverse=True)
    patterns = [(term, _boundary_pattern(escape(term))) for term in unique_terms]
    patterns = [(term, pattern) for term, pattern in patterns if pattern is not None]

    positions = []
    for _term, pattern in patterns:
        found = pattern.search(text)
        if found:
            positions.append(found.start())
    start = 0
    if positions:
        start = max(0, min(positions) - width // 3)
    snippet_text = text[start:start + width]
    if start > 0:
        snippet_text = "..." + snippet_text
    if start + width < len(text):
        snippet_text = snippet_text + "..."

    escaped = escape(snippet_text)
    matched: list[str] = []
    for term, pattern in patterns:
        if pattern.search(escaped):
            escaped = pattern.sub(
                f"<{highlight_tag}>\\g<0></{highlight_tag}>", escaped)
            matched.append(term)
    return escaped, matched


def highlight(text: str, terms: list[str], limit: int = 3) -> str:
    """Highlight terms in a short piece of text (title / abstract)."""
    snippet_text, _ = snippet(text, terms, width=limit * 90)
    return snippet_text


def keywords_from_text(text: str, limit: int = 12) -> list[str]:
    """Pick distinctive keywords (highest term frequency, stop words removed)."""
    tokens = analyze(text)["tokens"]
    counts: dict[str, int] = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [word for word, _ in ordered[:limit]]


def is_stopword(token: str) -> bool:
    return token in STOP_WORDS
