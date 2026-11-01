import pytest
from f1_intelligence_lab.app import app
from fastapi.testclient import TestClient

client = TestClient(app)
SESSION = "2024-monza-q"
A = "2024-monza-q-nor-fastest"
B = "2024-monza-q-pia-fastest"


def test_catalog_and_every_listed_workstation_resolve():
    catalog = client.get("/api/ecosystem/catalog").json()
    assert {p["id"] for p in catalog["projects"]} == {"race-lab", "telemetry", "stewardlens", "pitwall", "scoutgrid", "claimcheck", "archive"}
    assert catalog["recorded_sessions"] >= 1
    assert catalog["synthetic_sessions"] == 1
    for project in catalog["projects"]:
        assert client.get(project["path"]).status_code == 200


def test_scout_uses_real_times_and_observed_extrema():
    result = client.get("/api/ecosystem/scout", params={"session_id": SESSION}).json()
    assert result["rows"][0]["driver"] == "NOR"
    assert result["rows"][1]["gap_to_fastest"] == pytest.approx(.109)
    lap = client.get(f"/telemetry/laps/{A}/telemetry").json()
    assert result["rows"][0]["top_speed"] == max(s["speed"] for s in lap["samples"])
    assert result["rows"][0]["samples"] == len(lap["samples"])


def test_replay_returns_unchanged_recorded_samples_and_duration():
    result = client.get("/api/ecosystem/replay", params={"session_id": SESSION}).json()
    assert result["duration"] == pytest.approx(79.436)
    assert result["laps"][0] == client.get(f"/telemetry/laps/{A}/telemetry").json()
    assert result["session"]["source_type"] != "synthetic"


@pytest.mark.parametrize("endpoint", ["scout", "replay"])
def test_missing_session_returns_404(endpoint):
    assert client.get(f"/api/ecosystem/{endpoint}", params={"session_id": "missing"}).status_code == 404


@pytest.mark.parametrize("value,status", [(79.327,"supported"),(79.328,"supported"),(79.33,"contradicted")])
def test_lap_time_claim_with_precision_tolerance(value,status):
    r = client.post("/api/ecosystem/check", json={"kind":"lap_time", "value":value, "session_id":SESSION,"lap_a_id":A})
    assert r.status_code == 200
    assert r.json()["status"] == status
    assert r.json()["observed"] == 79.327
    assert r.json()["evidence"]["source_urls"]


def test_signed_delta_claim_and_sign_reversal():
    payload = {"kind":"lap_delta", "value":-.109, "session_id":SESSION,"lap_a_id":A,"lap_b_id":B}
    assert client.post("/api/ecosystem/check",json=payload).json()["status"] == "supported"
    payload["value"] = .109
    assert client.post("/api/ecosystem/check",json=payload).json()["status"] == "contradicted"


@pytest.mark.parametrize("second", [A,"demo-B","missing"])
def test_delta_rejects_identical_cross_session_and_missing_laps(second):
    assert client.post("/api/ecosystem/check",json={"kind":"lap_delta","value":0,"session_id":SESSION,"lap_a_id":A,"lap_b_id":second}).status_code == 422


def test_official_penalty_claim_has_document_hash_and_source():
    result = client.post("/api/ecosystem/check",json={"kind":"penalty_seconds","value":10,"decision_id":"fia-2024-italian-gp-doc-55"}).json()
    assert result["status"] == "supported"
    assert len(result["evidence"]["sha256"]) == 64
    assert result["evidence"]["url"].startswith("https://api.fia.com/")
    assert client.post("/api/ecosystem/check",json={"kind":"penalty_seconds","value":5,"decision_id":"missing"}).status_code == 404


def test_unsupported_claim_and_nonfinite_value_are_rejected():
    assert client.post("/api/ecosystem/check",json={"kind":"best_driver","value":10}).status_code == 422
    assert client.post("/api/ecosystem/check",json={"kind":"lap_time","value":"NaN"}).status_code == 422


def test_synthetic_claim_is_never_labelled_real():
    lap = client.get("/telemetry/laps/demo-A/telemetry").json()
    result = client.post("/api/ecosystem/check",json={"kind":"lap_time","value":lap["lap_time"],"session_id":"synthetic-demo","lap_a_id":"demo-A"}).json()
    assert result["status"] == "supported"
    assert result["evidence"]["source_type"] == "synthetic"
