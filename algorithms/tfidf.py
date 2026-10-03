"""TF-IDF implemented by hand (no scikit-learn, no numpy).

Definitions used
----------------
Term frequency, normalised by the document length (a "longer document
simply mentions the word more" correction)::

    TF(t, d) = (count of t in d) / (total tokens in d)

Inverse document frequency - a term that appears in *every* document
carries no discriminating power::

    IDF(t) = log( (1 + N) / (1 + df(t)) ) + 1        (smoothed IDF)

Score of a term for a document::

    TFIDF(t, d) = TF(t, d) * IDF(t)

Query-document similarity is the cosine of the TF-IDF vectors, computed by
hand with an explicit sparse dictionary (only non-zero coordinates are
touched, so a query with 3 terms costs O(3 * average postings) instead of
O(V * L)).

Complexity: building the vectors is O(total tokens); one query is
O(sum of postings lengths of the query terms) = O(k * df).
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Iterable, Mapping, Sequence


def term_frequency(tokens: Sequence[str], term: str) -> float:
    """TF(t, d) = count / total tokens."""
    if not tokens:
        return 0.0
    return tokens.count(term) / len(tokens)


def raw_term_frequency(tokens: Sequence[str], term: str) -> int:
    return tokens.count(term)


def inverse_document_frequency(document_frequency: int, total_documents: int) -> float:
    """Smoothed IDF - always >= 0 and never zero for a term that exists."""
    return math.log((1 + total_documents) / (1 + document_frequency)) + 1.0


def tfidf_weight(tf: float, idf: float) -> float:
    return tf * idf


class TfidfModel:
    """Sparse TF-IDF model over a fixed corpus (manual implementation)."""

    def __init__(self, documents: Mapping[int, Sequence[str]]) -> None:
        """``documents`` maps document id -> token list."""
        self.documents: dict[int, list[str]] = {
            int(doc_id): list(tokens) for doc_id, tokens in documents.items()
        }
        self.total_documents = len(self.documents)
        self.term_frequencies: dict[int, Counter] = {
            doc_id: Counter(tokens) for doc_id, tokens in self.documents.items()
        }
        self.doc_lengths: dict[int, int] = {
            doc_id: len(tokens) for doc_id, tokens in self.documents.items()
        }
        self.document_frequency: Counter = Counter()
        for counter in self.term_frequencies.values():
            self.document_frequency.update(counter.keys())
        self.idf: dict[str, float] = {}
        self.rebuild_idf()

    # -- model construction --------------------------------------------
    def rebuild_idf(self) -> None:
        self.idf = {
            term: inverse_document_frequency(df, self.total_documents)
            for term, df in self.document_frequency.items()
        }

    def normalized_tf(self, doc_id: int, term: str) -> float:
        length = self.doc_lengths.get(doc_id, 0)
        if not length:
            return 0.0
        return self.term_frequencies.get(doc_id, {}).get(term, 0) / length

    def vector(self, doc_id: int) -> dict[str, float]:
        """Sparse L2-normalised TF-IDF vector of one document."""
        raw = {
            term: tfidf_weight(self.normalized_tf(doc_id, term), self.idf.get(term, 0.0))
            for term, count in self.term_frequencies.get(doc_id, {}).items()
        }
        return self._l2_normalize(raw)

    @staticmethod
    def _l2_normalize(vector: dict[str, float]) -> dict[str, float]:
        norm = math.sqrt(sum(value * value for value in vector.values()))
        if norm == 0:
            return {term: 0.0 for term in vector}
        return {term: value / norm for term, value in vector.items()}

    def query_vector(self, query_tokens: Sequence[str]) -> dict[str, float]:
        """Query TF-IDF vector - query treated as one extra document."""
        counter = Counter(query_tokens)
        raw = {term: tfidf_weight(count / len(query_tokens), self.idf.get(term, 0.0))
               for term, count in counter.items()}
        return self._l2_normalize(raw)

    # -- scoring -------------------------------------------------------
    def cosine_similarity(self, vector_a: dict[str, float],
                          vector_b: dict[str, float]) -> float:
        """Sparse cosine similarity - iterate the smaller dict."""
        if len(vector_a) > len(vector_b):
            vector_a, vector_b = vector_b, vector_a
        return sum(value * vector_b.get(term, 0.0) for term, value in vector_a.items())

    def score_query(self, query_tokens: Sequence[str]) -> list[dict]:
        """Rank every document by cosine similarity to the query.

        Cost: O(V) to build vectors + O(sum of posting lengths).
        """
        if not query_tokens or not self.total_documents:
            return []
        query_vector = self.query_vector(query_tokens)
        results = []
        for doc_id in self.documents:
            doc_vector = self.vector(doc_id)
            score = self.cosine_similarity(query_vector, doc_vector)
            matched = {term: round(doc_vector.get(term, 0.0), 4)
                       for term in query_vector if term in doc_vector}
            results.append({
                "doc_id": doc_id,
                "tfidf_score": round(score, 6),
                "matched_terms": matched,
                "terms": len(query_vector),
            })
        results.sort(key=lambda item: (-item["tfidf_score"], item["doc_id"]))
        return results

    def term_report(self, terms: Iterable[str]) -> list[dict]:
        """Per-term TF / IDF / TF-IDF table for the visualizer."""
        report = []
        for term in terms:
            df = self.document_frequency.get(term, 0)
            idf = self.idf.get(term, inverse_document_frequency(df, self.total_documents))
            examples = []
            for doc_id, counter in self.term_frequencies.items():
                count = counter.get(term, 0)
                if count:
                    tf = count / self.doc_lengths[doc_id]
                    examples.append({
                        "doc_id": doc_id,
                        "count": count,
                        "tf": round(tf, 5),
                        "tfidf": round(tf * idf, 5),
                    })
            examples.sort(key=lambda item: -item["tfidf"])
            report.append({
                "term": term,
                "document_frequency": df,
                "total_documents": self.total_documents,
                "idf": round(idf, 5),
                "rarity_percent": round(100 * df / self.total_documents, 2) if self.total_documents else 0.0,
                "occurrences": examples[:10],
            })
        return report

    def stats(self) -> dict:
        lengths = list(self.doc_lengths.values())
        return {
            "documents": self.total_documents,
            "vocabulary": len(self.document_frequency),
            "total_tokens": sum(lengths),
            "avg_document_length": round(sum(lengths) / len(lengths), 2) if lengths else 0,
            "max_document_length": max(lengths) if lengths else 0,
        }
