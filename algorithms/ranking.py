"""Weighted relevance ranking for NexaSearch.

The score of a document for a query is a *linear combination of normalised
signals*.  Every signal is scaled to [0, 1] so the weights are directly
comparable and the final score stays interpretable (this matters for the
viva: "why weight 0.30?" is answerable).

    FinalScore(d, q) =  w_title   * TitleScore
                      + w_keyword * KeywordScore
                      + w_content * ContentScore        (TF-IDF cosine)
                      + w_phrase  * PhraseScore         (KMP / Rabin-Karp)
                      + w_graph   * GraphScore          (PageRank, normalised)

Default weights (sum = 1.0):

    title   0.30   a word in the title is a very strong intent signal
    keyword 0.25   author-declared keywords / tags
    content 0.25   TF-IDF cosine between query and body text
    phrase  0.10   exact phrase occurrence (multi-word queries only)
    graph   0.10   PageRank prestige of the document in the link graph

Plus small multiplicative "boosts" that behave like field boosts in classic
IR (e.g. full term coverage, a phrase in the title) and a tie-break on
document popularity (hit count).
"""

from __future__ import annotations

import math
from typing import Iterable, Mapping

DEFAULT_WEIGHTS: dict[str, float] = {
    "title": 0.30,
    "keyword": 0.25,
    "content": 0.25,
    "phrase": 0.10,
    "graph": 0.10,
}


def normalize_weights(weights: Mapping[str, float] | None = None) -> dict[str, float]:
    """Scale any weight set so the total is 1.0 (keeps ranking comparable)."""
    merged = dict(DEFAULT_WEIGHTS)
    if weights:
        for key, value in weights.items():
            if key in merged:
                try:
                    merged[key] = max(0.0, float(value))
                except (TypeError, ValueError):
                    continue
    total = sum(merged.values())
    if total <= 0:
        return dict(DEFAULT_WEIGHTS)
    return {key: round(value / total, 4) for key, value in merged.items()}


def title_score(query_terms: Iterable[str], title: str) -> float:
    """Fraction of query terms present in the title, with an exact-phrase bonus."""
    terms = [t for t in query_terms if t]
    if not terms:
        return 0.0
    lowered = (title or "").lower()
    hits = sum(1 for term in terms if term in lowered)
    coverage = hits / len(terms)
    phrase_bonus = 0.25 if " ".join(terms) in lowered else 0.0
    return min(1.0, coverage * 0.8 + phrase_bonus)


def keyword_score(query_terms: Iterable[str], keywords: Iterable[str]) -> float:
    """Coverage over author-declared keywords/tags."""
    terms = [t for t in query_terms if t]
    if not terms:
        return 0.0
    keyword_list = [str(k).lower() for k in keywords]
    if not keyword_list:
        return 0.0
    hits = sum(1 for term in terms if any(term in keyword for keyword in keyword_list))
    return hits / len(terms)


def content_score(tfidf_cosine: float) -> float:
    """TF-IDF cosine -> [0, 1] (cosine is already bounded)."""
    return max(0.0, min(1.0, float(tfidf_cosine)))


def phrase_score(match_count: int, doc_length: int) -> float:
    """Exact-phrase evidence, saturating so one huge document cannot dominate.

    score = 1 - exp(-matches / 3)  -> 0, 0.28, 0.49, 0.63 ... 1.0
    """
    if match_count <= 0:
        return 0.0
    return 1.0 - math.exp(-match_count / 3.0)


def graph_score(pagerank: float, max_pagerank: float) -> float:
    """PageRank relative to the most central document -> [0, 1]."""
    if max_pagerank <= 0:
        return 0.0
    return max(0.0, min(1.0, pagerank / max_pagerank))


def compute_score(signals: Mapping[str, float],
                  weights: Mapping[str, float] | None = None,
                  popularity: int = 0,
                  title_exact_phrase: bool = False,
                  full_coverage: bool = False) -> dict:
    """Combine the signals into the final relevance score.

    ``signals`` keys: ``title``, ``keyword``, ``content``, ``phrase``, ``graph``.
    """
    active = normalize_weights(weights)
    parts = {key: round(float(signals.get(key, 0.0)), 6) for key in active}
    weighted = {key: round(active[key] * parts[key], 6) for key in active}
    base = sum(weighted.values())

    # --- multiplicative boosts (classic IR field boosting) -------------
    boost = 1.0
    boost_reasons: list[str] = []
    if full_coverage:
        boost *= 1.12
        boost_reasons.append("every query term present x1.12")
    if title_exact_phrase and parts["title"] > 0:
        boost *= 1.15
        boost_reasons.append("exact phrase in title x1.15")
    if popularity >= 5:
        boost *= 1.05
        boost_reasons.append("popular document x1.05")
    if parts["content"] > 0.75 and parts["title"] > 0:
        boost *= 1.08
        boost_reasons.append("strong title+body agreement x1.08")

    final = base * boost
    # tiny deterministic popularity term keeps ties from being arbitrary
    final += min(0.01, popularity * 0.0008)

    return {
        "final_score": round(final, 6),
        "base_score": round(base, 6),
        "signals": parts,
        "weights": active,
        "weighted_parts": weighted,
        "boost": round(boost, 4),
        "boost_reasons": boost_reasons,
    }


def explain(scored: Mapping) -> list[dict]:
    """Human-readable breakdown rows for the results page / explanation box."""
    signals = scored.get("signals", {})
    weights = scored.get("weights", {})
    weighted = scored.get("weighted_parts", {})
    rows = []
    labels = {
        "title": "Title match",
        "keyword": "Keyword match",
        "content": "Content TF-IDF",
        "phrase": "Exact phrase",
        "graph": "PageRank graph score",
    }
    for key in ("title", "keyword", "content", "phrase", "graph"):
        rows.append({
            "signal": labels[key],
            "value": round(float(signals.get(key, 0.0)), 4),
            "weight": weights.get(key, 0.0),
            "contribution": round(float(weighted.get(key, 0.0)), 4),
        })
    rows.append({
        "signal": "Popularity boost",
        "value": scored.get("boost", 1.0),
        "weight": "-",
        "contribution": round(float(scored.get("final_score", 0.0)) - float(scored.get("base_score", 0.0)), 4),
    })
    return rows


def rank_results(candidates: list[dict],
                 weights: Mapping[str, float] | None = None) -> list[dict]:
    """Score + sort candidates.

    Sorting uses our own Merge Sort when the candidate list is large enough
    to matter, otherwise the in-order hand-written insertion scan (cheaper
    for tiny lists).  This is what the "Ranking uses Merge Sort" note on the
    dashboard refers to.
    """
    from algorithms.merge_sort import merge_sort

    active = normalize_weights(weights)
    for candidate in candidates:
        scored = compute_score(
            candidate.get("signals", {}),
            active,
            popularity=candidate.get("popularity", 0),
            title_exact_phrase=candidate.get("title_exact_phrase", False),
            full_coverage=candidate.get("full_coverage", False),
        )
        candidate["score_detail"] = scored
        candidate["score"] = scored["final_score"]

    if len(candidates) >= 12:
        ordered = merge_sort(candidates, key=lambda item: (-item["score"], item.get("doc_id", 0)))["sorted"]
        candidates[:] = ordered
    else:
        # insertion sort on the negated score (stable, O(k^2), trivial for k<12)
        for i in range(1, len(candidates)):
            current = candidates[i]
            j = i - 1
            while j >= 0 and (candidates[j]["score"] < current["score"]):
                candidates[j + 1] = candidates[j]
                j -= 1
            candidates[j + 1] = current
    return candidates


FORMULA_TEXT = (
    "FinalScore(d,q) = 0.30*TitleScore + 0.25*KeywordScore + 0.25*ContentScore(TF-IDF) "
    "+ 0.10*PhraseScore + 0.10*PageRankScore,  then x field-boost,  then + popularity tie-break"
)

RANKING_FORMULA = FORMULA_TEXT

WEIGHT_EXPLANATIONS: list[dict] = [
    {"key": "title", "label": "Title match", "weight": DEFAULT_WEIGHTS["title"],
     "why": "A query word in the title is the strongest single intent signal a user can give."},
    {"key": "keyword", "label": "Keyword match", "weight": DEFAULT_WEIGHTS["keyword"],
     "why": "Author-declared keywords are curated metadata, so they beat incidental body text."},
    {"key": "content", "label": "Content TF-IDF", "weight": DEFAULT_WEIGHTS["content"],
     "why": "Cosine TF-IDF measures overall topical overlap and normalises for document length."},
    {"key": "phrase", "label": "Exact phrase", "weight": DEFAULT_WEIGHTS["phrase"],
     "why": "Verified by KMP *and* Rabin-Karp; a quoted phrase is a much rarer, stronger signal."},
    {"key": "graph", "label": "PageRank graph score", "weight": DEFAULT_WEIGHTS["graph"],
     "why": "Query-independent authority pre-computed once over the link graph, min-max scaled."},
]
