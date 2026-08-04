from __future__ import annotations

from aircord.ingestion.discover_cluster import discover


def test_live_discovery_reports_gate_a_evidence(monkeypatch):
    import aircord.ingestion.discover_cluster as module

    monkeypatch.setattr(module, "MODE", "live")
    monkeypatch.setattr(
        module.AirNowClient,
        "fetch",
        lambda _client, _bounds: [
            {
                "monitor_id": "m1",
                "latitude": 34.02,
                "longitude": -118.40,
                "observed_at": "2026-08-02T12:00:00Z",
                "pm25": 10,
            }
        ],
    )
    monkeypatch.setattr(
        module.PurpleAirClient,
        "fetch",
        lambda _client, _bounds: [
            {
                "sensor_id": "s1",
                "latitude": 34.021,
                "longitude": -118.401,
                "pm25_cf1": 25,
                "channel_a_pm25": 30,
                "channel_b_pm25": 20,
                "likely_indoor": False,
            },
            {
                "sensor_id": "s2",
                "latitude": 34.022,
                "longitude": -118.402,
                "pm25_cf1": 24,
                "channel_a_pm25": 24,
                "channel_b_pm25": 24,
                "likely_indoor": False,
            },
            {
                "sensor_id": "s3",
                "latitude": 34.023,
                "longitude": -118.403,
                "pm25_cf1": 23,
                "channel_a_pm25": 23,
                "channel_b_pm25": 23,
                "likely_indoor": False,
            },
        ],
    )

    result = discover("greater-la")

    assert result["gate_a_status"] == "passed"
    assert result["paired_anchor_count"] == 3
    assert result["disagreement_pair_count"] == 3
    assert result["degraded_sensor_candidate_count"] == 1
