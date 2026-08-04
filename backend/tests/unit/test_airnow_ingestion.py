from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone

from aircord.ingestion.airnow import AirNowSnapshot
from aircord.ingestion.airnow_ingest import ingest_airnow
from aircord.ingestion.snapshots import SnapshotReference


class FakeAirNowClient:
    def __init__(self, snapshot):
        self.snapshot = snapshot

    def fetch_snapshot(self, _bounds):
        return self.snapshot


class FakeSnapshotStore:
    def __init__(self):
        self.calls = []

    def put_json(self, key, payload):
        self.calls.append((key, payload))
        return SnapshotReference(f"s3://aircord-test/{key}", None)


class FakeTransaction:
    def __init__(self):
        self.monitor = None
        self.audit = None

    def upsert_monitor(self, monitor_id, name, latitude, longitude, latest_aqi, observed_at, **kwargs):
        self.monitor = {
            "monitor_id": monitor_id,
            "name": name,
            "latitude": latitude,
            "longitude": longitude,
            "latest_aqi": latest_aqi,
            "observed_at": observed_at,
        }
        return self.monitor

    def create_audit_log(self, actor, action, entity_type, entity_id, **kwargs):
        self.audit = {
            "audit_id": "audit-airnow",
            "actor": actor,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": kwargs["details"],
        }
        return self.audit


class FakeRepository:
    def __init__(self):
        self.transaction_value = FakeTransaction()

    def read_sensor(self, sensor_id):
        return {"sensor_id": sensor_id, "latitude": 34.02, "longitude": -118.40}

    @contextmanager
    def transaction(self):
        yield self.transaction_value


def test_airnow_ingestion_stores_raw_payload_and_nearest_monitor():
    payload = [
        {
            "FullAQSCode": "060370001",
            "SiteName": "Nearest LA monitor",
            "Latitude": 34.021,
            "Longitude": -118.401,
            "Parameter": "PM25",
            "AQI": 41,
            "Value": 8.2,
            "UTC": "2026-08-04T21:00:00Z",
        },
        {
            "FullAQSCode": "060370002",
            "SiteName": "Far LA monitor",
            "Latitude": 34.25,
            "Longitude": -118.10,
            "Parameter": "PM25",
            "AQI": 65,
            "Value": 18.0,
            "UTC": "2026-08-04T21:00:00Z",
        },
    ]
    client = FakeAirNowClient(AirNowSnapshot(payload=payload, rows=[
        {
            "monitor_id": "060370001",
            "name": "Nearest LA monitor",
            "latitude": 34.021,
            "longitude": -118.401,
            "observed_at": "2026-08-04T21:00:00Z",
            "aqi": 41,
            "pm25": 8.2,
        },
        {
            "monitor_id": "060370002",
            "name": "Far LA monitor",
            "latitude": 34.25,
            "longitude": -118.10,
            "observed_at": "2026-08-04T21:00:00Z",
            "aqi": 65,
            "pm25": 18.0,
        },
    ]))
    store = FakeSnapshotStore()
    repository = FakeRepository()

    result = ingest_airnow(
        "54917",
        client=client,
        snapshot_store=store,
        repository=repository,
        now=datetime(2026, 8, 4, 21, 2, tzinfo=timezone.utc),
    )

    assert result.monitor_id == "060370001"
    assert result.snapshot_key == "raw/airnow/date=2026-08-04/20260804T210200Z.json"
    assert store.calls == [(result.snapshot_key, payload)]
    assert repository.transaction_value.monitor["latest_aqi"] == 41.0
    assert repository.transaction_value.audit["actor"] == "airnow_ingest"
