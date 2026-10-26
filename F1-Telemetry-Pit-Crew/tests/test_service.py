from telemetry_pit_crew.service import TelemetryService


def test_demo_debrief_is_grounded():
    result = TelemetryService().compare("demo-A", "demo-B")
    assert len(result.priority_findings) == 3
    assert all(finding.evidence_ids for finding in result.priority_findings)
    assert "synthetic" in " ".join(result.data_limitations).lower()


def test_unknown_lap_is_rejected():
    try:
        TelemetryService().compare("missing", "demo-B")
    except KeyError:
        return
    raise AssertionError("Expected KeyError")

