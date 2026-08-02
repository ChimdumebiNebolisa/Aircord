from fastapi.testclient import TestClient

from aircord.fixtures import seed_demo
from aircord.main import app


def test_inspection_endpoints_match_contract_shape(demo_db, monkeypatch):
    import aircord.api.dependencies as dependencies
    import aircord.main as main

    monkeypatch.setattr(dependencies, "DB_PATH", demo_db)
    monkeypatch.setattr(main, "DB_PATH", demo_db)
    seed_demo(demo_db)
    with TestClient(app) as client:
        cluster = client.get("/clusters/active")
        cells = client.get("/clusters/active/cells")
        detail = client.get("/cells/cell-culver")
        showcase = client.get("/showcases/degraded-sensor")
        backtest = client.get("/backtests/latest")
        accepted = client.post("/backtests", json={"window_start": "2026-07-20T00:00:00Z", "window_end": "2026-08-01T00:00:00Z"})
    assert cluster.status_code == 200
    assert {"cluster_id", "name", "gate_a_status", "gate_a_notes"} <= cluster.json().keys()
    assert cells.status_code == 200 and len(cells.json()) == 3
    assert {"cell_id", "estimate", "resolution", "reference_caveat", "medical_directive_caveat"} <= detail.json().keys()
    assert showcase.status_code == 200 and {"sensor_id", "cell_id", "raw_or_static_estimate", "aircord_estimate", "reputation_reason"} <= showcase.json().keys()
    assert backtest.status_code == 200 and backtest.json()["claim_status"] == "pending"
    assert accepted.status_code == 202 and accepted.json()["status"] == "pending"
