import pytest
from stewardlens.contracts import Incident, RegulationClause
from stewardlens.retrieval import retrieve_precedents, retrieve_regulations, score_text, tokenize


def test_tokenize_normalizes_and_removes_common_stop_words():
    assert tokenize("A DRIVER rejoined the Track!") == ["driver", "rejoined", "track"]


def test_score_text_prefers_shared_meaningful_terms():
    query = "unsafe rejoin across racing line"
    assert score_text(query, "safe rejoin onto the racing line") > score_text(
        query, "late braking into a hairpin"
    )


def test_regulation_retrieval_filters_by_season_and_ranks_rejoin_clause():
    clauses = [
        RegulationClause(
            id="old-rejoin",
            season=2025,
            article="1",
            title="Safe rejoin",
            text="Rejoin only when safe.",
            source="sample://old",
        ),
        RegulationClause(
            id="current-contact",
            season=2026,
            article="2",
            title="Contact",
            text="Avoid contact during an overtake.",
            source="sample://contact",
        ),
        RegulationClause(
            id="current-rejoin",
            season=2026,
            article="3",
            title="Safe rejoining",
            text="A car must rejoin without entering an approaching car's path.",
            source="sample://rejoin",
        ),
    ]

    results = retrieve_regulations(
        "car rejoin into approaching path", clauses, season=2026, limit=2
    )

    assert [clause.id for clause in results] == ["current-rejoin"]


def test_precedent_retrieval_excludes_active_case_and_prefers_same_category():
    active = _incident("active", "causing a collision", "late braking caused contact")
    collision = _incident("collision", "causing a collision", "braking contact at corner")
    unrelated = _incident("unrelated", "track limits", "left the circuit four times")

    results = retrieve_precedents(active, [active, unrelated, collision], limit=3)

    assert [incident.id for incident in results] == ["collision"]


def test_negative_limit_is_rejected():
    with pytest.raises(ValueError, match="non-negative"):
        retrieve_regulations("contact", [], limit=-1)


def _incident(incident_id: str, category: str, summary: str) -> Incident:
    return Incident(
        id=incident_id,
        season=2026,
        event="Fictional event",
        session="Race",
        lap=1,
        driver_a="A",
        driver_b="B",
        category=category,
        summary=summary,
        evidence_ids=[],
    )
