from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from aircord.db.repositories import Repository
from aircord.ingestion.purpleair import PurpleAirClient
from aircord.ingestion.snapshots import RawSnapshotStore, S3SnapshotStore, SnapshotReference


REQUIRED_ENV = (
    "DATABASE_URL",
    "PURPLEAIR_API_KEY",
    "PURPLEAIR_SENSOR_ID",
    "AWS_REGION",
    "S3_BUCKET",
)


@dataclass(frozen=True)
class IngestionResult:
    sensor_id: str
    reading_id: str
    audit_id: str
    snapshot_key: str
    snapshot_uri: str
    observed_at: str


def missing_required_environment() -> list[str]:
    return [name for name in REQUIRED_ENV if not os.getenv(name)]


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _observed_at(value: Any, fallback: datetime) -> datetime:
    if value not in (None, ""):
        try:
            return _as_utc(datetime.fromisoformat(str(value).replace("Z", "+00:00")))
        except ValueError:
            pass
    return _as_utc(fallback)


def _snapshot_key(sensor_id: str, observed_at: datetime) -> str:
    timestamp = _as_utc(observed_at)
    return (
        f"raw/purpleair/sensor_id={sensor_id}/date={timestamp:%Y-%m-%d}/"
        f"{timestamp:%Y%m%dT%H%M%SZ}.json"
    )


def ingest_sensor(
    sensor_id: str | None = None,
    *,
    client: PurpleAirClient | None = None,
    snapshot_store: RawSnapshotStore | None = None,
    repository: Repository | None = None,
    now: datetime | None = None,
) -> IngestionResult:
    sensor_id = sensor_id or os.getenv("PURPLEAIR_SENSOR_ID")
    if not sensor_id:
        raise RuntimeError("PURPLEAIR_SENSOR_ID is required for live ingestion")

    if client is None:
        api_key = os.getenv("PURPLEAIR_API_KEY")
        if not api_key:
            raise RuntimeError("PURPLEAIR_API_KEY is required for live ingestion")
        client = PurpleAirClient(api_key=api_key)

    if snapshot_store is None:
        region = os.getenv("AWS_REGION")
        bucket = os.getenv("S3_BUCKET")
        if not region:
            raise RuntimeError("AWS_REGION is required for live ingestion")
        if not bucket:
            raise RuntimeError("S3_BUCKET is required for live ingestion")
        snapshot_store = S3SnapshotStore(bucket=bucket, region=region)

    if repository is None:
        if not os.getenv("DATABASE_URL"):
            raise RuntimeError("DATABASE_URL is required for live ingestion")
        repository = Repository(backend="cockroach")

    captured_at = _as_utc(now or datetime.now(timezone.utc))
    snapshot = client.fetch_sensor(str(sensor_id))
    normalized = snapshot.normalized
    observed_at = _observed_at(normalized.get("last_seen_at"), captured_at)
    pm25_cf1 = normalized.get("pm25_cf1")
    if pm25_cf1 in (None, ""):
        raise RuntimeError(f"PurpleAir sensor has no pm25_cf1 reading: {sensor_id}")

    snapshot_key = _snapshot_key(str(sensor_id), observed_at)
    snapshot_reference: SnapshotReference = snapshot_store.put_json(snapshot_key, snapshot.payload)

    observed_at_text = observed_at.isoformat().replace("+00:00", "Z")
    with repository.transaction() as transaction:
        sensor = transaction.upsert_sensor(
            str(sensor_id),
            normalized.get("name"),
            normalized.get("latitude"),
            normalized.get("longitude"),
            likely_indoor=bool(normalized.get("likely_indoor")),
            last_seen=normalized.get("last_seen_at") or observed_at_text,
        )
        reading = transaction.create_sensor_reading(
            str(sensor_id),
            observed_at_text,
            float(pm25_cf1),
            normalized.get("channel_a_pm25"),
            normalized.get("channel_b_pm25"),
            normalized.get("humidity"),
            normalized.get("rssi"),
            pm25_atm=normalized.get("pm25_atm"),
            raw_s3_key=snapshot_key,
        )
        audit = transaction.create_audit_log(
            "purpleair_ingest",
            "sensor_reading_ingested",
            "sensor_reading",
            str(reading["reading_id"]),
            details={
                "sensor_id": sensor["sensor_id"],
                "snapshot_key": snapshot_key,
                "snapshot_uri": snapshot_reference.uri,
                "observed_at": observed_at_text,
            },
            source_snapshot_uri=snapshot_reference.uri,
        )

    return IngestionResult(
        sensor_id=str(sensor["sensor_id"]),
        reading_id=str(reading["reading_id"]),
        audit_id=str(audit["audit_id"]),
        snapshot_key=snapshot_key,
        snapshot_uri=snapshot_reference.uri,
        observed_at=observed_at_text,
    )
