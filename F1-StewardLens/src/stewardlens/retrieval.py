"""Deterministic lexical retrieval for regulations and sample precedents."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Callable, Iterable, List, Optional, Sequence, TypeVar

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

