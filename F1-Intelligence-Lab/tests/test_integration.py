from __future__ import annotations

from fastapi.testclient import TestClient

from f1_intelligence_lab.app import app


client = TestClient(app)


def test_portal_home_links_both_workbenches() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "F1 Intelligence Lab" in response.text
    assert 'href="/stewardlens/"' in response.text
    assert 'href="/telemetry/"' in response.text
    assert "not live timing" in response.text


def test_portal_health_describes_mounted_services() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "services": {
            "stewardlens": {"status": "mounted", "path": "/stewardlens/"},
            "telemetry": {"status": "mounted", "path": "/telemetry/"},
        },
    }


def test_stewardlens_is_mounted_with_working_api() -> None:
    home = client.get("/stewardlens/")
    incidents = client.get("/stewardlens/incidents")

    assert home.status_code == 200
    assert "StewardLens" in home.text
    assert incidents.status_code == 200
    assert len(incidents.json()) >= 1


def test_telemetry_is_mounted_with_working_api() -> None:
    home = client.get("/telemetry/")
    laps = client.get("/telemetry/laps")

    assert home.status_code == 200
    assert "Telemetry Pit Crew" in home.text
    assert laps.status_code == 200
    assert {lap["id"] for lap in laps.json()} >= {"demo-A", "demo-B"}


def test_existing_absolute_frontend_api_paths_remain_compatible() -> None:
    incidents = client.get("/incidents")
    comparison = client.post(
        "/comparisons",
        json={"lap_a_id": "demo-A", "lap_b_id": "demo-B"},
    )

    assert incidents.status_code == 200
    assert comparison.status_code == 200
    assert comparison.json()["priority_findings"]


def test_portal_openapi_only_advertises_portal_operations() -> None:
    schema = client.get("/openapi.json").json()

    assert set(schema["paths"]) == {"/health", "/api/ecosystem/catalog", "/api/ecosystem/scout", "/api/ecosystem/replay", "/api/ecosystem/check", "/api/races/demo", "/api/races/template", "/api/races/analyze", "/api/library/sessions", "/api/library/jobs", "/api/library/import", "/api/library/races/{session_id}", "/api/race-details/{sid}", "/api/race-details/{sid}/load"}

