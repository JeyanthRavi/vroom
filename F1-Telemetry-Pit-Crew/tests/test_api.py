from fastapi.testclient import TestClient
from telemetry_pit_crew.api import app

client = TestClient(app)


def test_health_and_comparison():
    assert client.get("/health").json() == {"status": "ok"}
    response = client.post("/comparisons", json={"lap_a_id": "demo-A", "lap_b_id": "demo-B"})
    assert response.status_code == 200
    assert response.json()["priority_findings"]


def test_real_cached_session_catalog_telemetry_and_comparison():
    sessions = client.get("/sessions")
    assert sessions.status_code == 200
    real = next(item for item in sessions.json() if item["id"] == "2024-monza-q")
    assert real["source_type"] == "openf1_processed"

    laps = client.get("/laps", params={"session_id": real["id"]}).json()
    assert {lap["driver"] for lap in laps} == {"NOR", "PIA"}
    assert all("samples" not in lap for lap in laps)

    telemetry = client.get(f"/laps/{laps[0]['id']}/telemetry")
    assert telemetry.status_code == 200
    assert len(telemetry.json()["samples"]) > 200

    comparison = client.post("/comparisons", json={
        "lap_a_id": laps[0]["id"], "lap_b_id": laps[1]["id"],
    })
    assert comparison.status_code == 200
    payload = comparison.json()
    assert payload["priority_findings"]
    assert "recorded" in payload["summary"]


def test_bad_session_and_same_lap_are_rejected():
    assert client.get("/laps", params={"session_id": "missing"}).status_code == 404
    response = client.post("/comparisons", json={"lap_a_id": "demo-A", "lap_b_id": "demo-A"})
    assert response.status_code == 422

