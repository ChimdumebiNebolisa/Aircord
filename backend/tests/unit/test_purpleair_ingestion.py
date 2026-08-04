from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone

from aircord.ingestion.purpleair import PurpleAirSensorSnapshot
from aircord.ingestion.purpleair_ingest import ingest_sensor
from aircord.ingestion.snapshots import SnapshotReference


class FakeSnapshotStore:
    def __init__(self):
        self.calls = []

    def put_json(self, key, payload):
        self.calls.append((key, payload))
        return SnapshotReference(f"s3://aircord-test/{key}", None)


class FakeTransaction:
    def __init__(self):
        self.sensor = None
        self.reading = None
        self.audit = None

    def upsert_sensor(self, sensor_id, name, latitude, longitude, **kwargs):
        self.sensor = {
            "sensor_id": sensor_id,
            "name": name,
            "latitude": latitude,
            "longitude": longitude,
            "likely_indoor": kwargs["likely_indoor"],
        }
        return self.sensor

    def create_sensor_reading(self, sensor_id, observed_at, pm25_cf1, channel_a, channel_b, humidity, rssi, **kwargs):
        self.reading = {
            "reading_id": "reading-test",
            "sensor_id": sensor_id,
            "observed_at": observed_at,
            "pm25_cf1": pm25_cf1,
            "raw_s3_key": kwargs["raw_s3_key"],
        }
        return self.reading

    def create_audit_log(self, actor, action, entity_type, entity_id, **kwargs):
        self.audit = {
            "audit_id": "audit-test",
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

    @contextmanager
    def transaction(self):
        yield self.transaction_value


class FakePurpleAirClient:
    def __init__(self, snapshot):
        self.snapshot = snapshot

    def fetch_sensor(self, sensor_id):
        assert sensor_id == "123"
        return self.snapshot


def test_ingestion_uploads_raw_payload_and_writes_sensor_reading_and_audit():
    payload = {"fields": ["sensor_index", "pm2.5_cf_1"], "data": [[123, 13.0]]}
    snapshot = PurpleAirSensorSnapshot(
        sensor_id="123",
        normalized={
            "sensor_id": "123",
            "name": "Culver",
            "latitude": 34.02,
            "longitude": -118.4,
            "likely_indoor": False,
            "last_seen_at": "2026-08-04T18:00:00Z",
            "pm25_atm": 12.0,
            "pm25_cf1": 13.0,
            "channel_a_pm25": 14.0,
            "channel_b_pm25": 12.0,
            "humidity": 45.0,
            "rssi": -50.0,
        },
        payload=payload,
    )
    store = FakeSnapshotStore()
    repository = FakeRepository()

    result = ingest_sensor(
        "123",
        client=FakePurpleAirClient(snapshot),
        snapshot_store=store,
        repository=repository,
        now=datetime(2026, 8, 4, 18, 1, tzinfo=timezone.utc),
    )

    transaction = repository.transaction_value
    expected_key = "raw/purpleair/sensor_id=123/date=2026-08-04/20260804T180000Z.json"
    assert result.snapshot_key == expected_key
    assert store.calls == [(expected_key, payload)]
    assert transaction.sensor["sensor_id"] == "123"
    assert transaction.reading["pm25_cf1"] == 13.0
    assert transaction.reading["raw_s3_key"] == expected_key
    assert transaction.audit["actor"] == "purpleair_ingest"
    assert transaction.audit["details"]["snapshot_uri"] == f"s3://aircord-test/{expected_key}"
