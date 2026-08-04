from fastapi.testclient import TestClient

from aircord.api.dependencies import get_repository
from aircord.demo import build_demo_summary
from aircord.db.repositories import Repository
from aircord.fixtures import seed_demo
from aircord.main import app


def test_demo_summary_has_clear_empty_state_for_missing_live_sensor(demo_db):
    summary = build_demo_summary(Repository(demo_db), "54917")

    assert summary["status"] == "empty"
    assert summary["sensor"] is None
    assert summary["latest_sensor_reading"] is None
    assert summary["message"]


def test_demo_api_returns_empty_state_without_faking_sensor_data(demo_db):
    seed_demo(demo_db)
    app.dependency_overrides[get_repository] = lambda: Repository(demo_db)
    try:
        with TestClient(app) as client:
            response = client.get("/api/sensors/54917/latest")
            summary = client.get("/api/demo-summary")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "empty"
    assert response.json()["reading"] is None
    assert summary.status_code == 200
    assert summary.json()["status"] == "empty"
