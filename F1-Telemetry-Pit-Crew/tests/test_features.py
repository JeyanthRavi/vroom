from telemetry_pit_crew.features import extract_segment_evidence
from telemetry_pit_crew.sample_data import SEGMENTS, make_lap


def test_extracts_all_segments():
    evidence = extract_segment_evidence(make_lap("A"), make_lap("B"), SEGMENTS)
    assert len(evidence) == len(SEGMENTS)
    assert all(item.id.startswith("ev-") for item in evidence)


def test_delta_is_antisymmetric():
    ab = extract_segment_evidence(make_lap("A"), make_lap("B"), SEGMENTS)
    ba = extract_segment_evidence(make_lap("B"), make_lap("A"), SEGMENTS)
    for first, second in zip(ab, ba):
        assert abs(first.delta_a_minus_b + second.delta_a_minus_b) < 1e-9

