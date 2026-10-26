import json

from telemetry_pit_crew.ingestion import load_cached_sessions
from telemetry_pit_crew.sample_data import demo_laps


def test_cached_session_is_loaded_and_validated(tmp_path):
    laps = list(demo_laps().values())
    fixture = {
        "schema_version": 1,
        "session": {"id": "test-session", "name": "Test", "source_type": "fixture"},
        "laps": [lap.model_dump() for lap in laps],
    }
    (tmp_path / "session.json").write_text(json.dumps(fixture), encoding="utf-8")

    sessions = load_cached_sessions(tmp_path)

    assert len(sessions) == 1
    metadata, loaded_laps = sessions[0]
    assert metadata["cached"] is True
    assert metadata["fixture_file"] == "session.json"
    assert [lap.id for lap in loaded_laps] == ["demo-A", "demo-B"]


def test_invalid_schema_and_single_lap_are_ignored(tmp_path):
    lap = next(iter(demo_laps().values()))
    (tmp_path / "old.json").write_text(json.dumps({"schema_version": 0}), encoding="utf-8")
    (tmp_path / "short.json").write_text(json.dumps({
        "schema_version": 1,
        "session": {"id": "short"},
        "laps": [lap.model_dump()],
    }), encoding="utf-8")

    assert load_cached_sessions(tmp_path) == []
