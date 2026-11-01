"""Deterministic lexical retrieval for regulations and sample precedents."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Callable, Iterable, List, Optional, Sequence, TypeVar

from stewardlens.contracts import Incident, RegulationClause


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "at",
    "by",
    "for",
    "from",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "was",
    "with",
}
T = TypeVar("T")


def tokenize(text: str) -> List[str]:
    """Normalize text into useful retrieval terms."""

    return [token for token in _TOKEN_RE.findall(text.lower()) if token not in _STOP_WORDS]


def score_text(query: str, document: str) -> float:
    """Return cosine similarity between term-frequency vectors.

    This dependency-free baseline is intentionally transparent and stable. It
    can later be replaced by embeddings without changing repository contracts.
    """

    query_counts = Counter(tokenize(query))
    document_counts = Counter(tokenize(document))
    if not query_counts or not document_counts:
        return 0.0
    dot_product = sum(
        count * document_counts.get(token, 0) for token, count in query_counts.items()
    )
    query_norm = math.sqrt(sum(count * count for count in query_counts.values()))
    document_norm = math.sqrt(sum(count * count for count in document_counts.values()))
    return dot_product / (query_norm * document_norm)


def _rank(items: Iterable[T], score_fn: Callable[[T], float], limit: int) -> List[T]:
    if limit < 0:
        raise ValueError("limit must be non-negative")
    scored = [(score_fn(item), index, item) for index, item in enumerate(items)]
    scored.sort(key=lambda row: (-row[0], row[1]))
    return [item for score, _, item in scored[:limit] if score > 0]


def retrieve_regulations(
    query: str,
    clauses: Sequence[RegulationClause],
    *,
    season: Optional[int] = None,
    limit: int = 5,
) -> List[RegulationClause]:
    """Rank clauses by lexical relevance, restricted to an applicable season."""

    eligible = [clause for clause in clauses if season is None or clause.season == season]
    return _rank(
        eligible,
        lambda clause: score_text(
            query, f"{clause.article} {clause.title} {clause.text}"
        ),
        limit,
    )


def retrieve_precedents(
    incident: Incident,
    candidates: Sequence[Incident],
    *,
    limit: int = 3,
) -> List[Incident]:
    """Rank comparable incidents while excluding the active incident itself."""

    query = f"{incident.category} {incident.summary}"

    def similarity(candidate: Incident) -> float:
        if candidate.id == incident.id:
            return 0.0
        candidate_text = f"{candidate.category} {candidate.summary}"
        lexical = score_text(query, candidate_text)
        category_bonus = 0.25 if candidate.category == incident.category else 0.0
        if lexical == 0.0 and category_bonus == 0.0:
            return 0.0
        season_bonus = 0.05 if candidate.season == incident.season else 0.0
        return lexical + category_bonus + season_bonus

    return _rank(candidates, similarity, limit)


class TfidfRetriever:
    """Small deterministic retriever used by the measured offline path."""

    def __init__(self, identifiers: Sequence[str], documents: Sequence[str]):
        if len(identifiers) != len(documents) or not documents:
            raise ValueError("identifiers and non-empty documents must align")
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.identifiers = list(identifiers)
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
        self.matrix = self.vectorizer.fit_transform(documents)

    def search(self, query: str, limit: int = 5) -> List[str]:
        if limit < 0:
            raise ValueError("limit must be non-negative")
        scores = (self.matrix @ self.vectorizer.transform([query]).T).toarray()[:, 0]
        order = sorted(range(len(scores)), key=lambda index: (-scores[index], index))
        return [self.identifiers[index] for index in order[:limit] if scores[index] > 0]


class SentenceEmbeddingRetriever:
    """Optional embedding retriever with an explicit deterministic fallback.

    No model is downloaded unless the caller supplies an encoder or explicitly
    asks for the optional provider. Default construction stays offline.
    """

    def __init__(
        self,
        identifiers: Sequence[str],
        documents: Sequence[str],
        encoder: Optional[Any] = None,
    ):
        self.fallback = TfidfRetriever(identifiers, documents)
        self.identifiers = list(identifiers)
        self.encoder = encoder
        self.embeddings = None if encoder is None else encoder.encode(list(documents))

    @property
    def backend(self) -> str:
        return "tfidf-fallback" if self.encoder is None else "sentence-embedding"

    def search(self, query: str, limit: int = 5) -> List[str]:
        if self.encoder is None:
            return self.fallback.search(query, limit)
        import numpy as np

        query_vector = np.asarray(self.encoder.encode([query])[0], dtype=float)
        documents = np.asarray(self.embeddings, dtype=float)
        denominator = np.linalg.norm(documents, axis=1) * np.linalg.norm(query_vector)
        scores = np.divide(
            documents @ query_vector,
            denominator,
            out=np.zeros(len(documents), dtype=float),
            where=denominator != 0,
        )
        order = sorted(range(len(scores)), key=lambda index: (-scores[index], index))
        return [self.identifiers[index] for index in order[:limit] if scores[index] > 0]

