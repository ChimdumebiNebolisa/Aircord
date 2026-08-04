from __future__ import annotations

import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from aircord.db.repositories import Repository
from aircord.ingestion.airnow import AirNowClient
from aircord.ingestion.snapshots import RawSnapshotStore, S3SnapshotStore, SnapshotReference


AIRNOW_LA_BOUNDS = (-118.8, 33.6, -117.6, 34.35)
REQUIRED_ENV = ("DATABASE_URL", "AIRNOW_API_KEY", "AWS_REGION", "S3_BUCKET")


@dataclass(frozen=True)
class AirNowIngestionResult:
    monitor_id: str
    snapshot_key: str
    snapshot_uri: str
    audit_id: str
    observed_at: str
    distance_km: float
    monitor: dict[str, Any]


def missing_required_environment() -> list[str]:
    return [name for name in REQUIRED_ENV if not os.getenv(name)]


def _number(value: Any) -> float | None:
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def _as_utc(value: Any, fallback: datetime) -> datetime:
    if value not in (None, ""):
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
        except ValueError:
            pass
    return fallback.astimezone(timezone.utc)


def _distance_km(first: dict[str, Any], second: dict[str, Any]) -> float | None:
    lat1, lon1 = _number(first.get("latitude")), _number(first.get("longitude"))
    lat2, lon2 = _number(second.get("latitude")), _number(second.get("longitude"))
    if None in (lat1, lon1, lat2, lon2):
        return None
    lat1, lon1, lat2, lon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    a = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(a))


def _latest_monitors(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        monitor_id = str(row.get("monitor_id") or "")
        if not monitor_id or _number(row.get("aqi")) is None:
            continue
        current = latest.get(monitor_id)
        if current is None or str(row.get("observed_at") or "") > str(current.get("observed_at") or ""):
            latest[monitor_id] = row
    return list(latest.values())


def _snapshot_key(captured_at: datetime) -> str:
    captured_at = captured_at.astimezone(timezone.utc)
    return (
        f"raw/airnow/date={captured_at:%Y-%m-%d}/"
        f"{captured_at:%Y%m%dT%H%M%SZ}.json"
    )


def ingest_airnow(
    sensor_id: str | None = None,
    *,
    client: AirNowClient | None = None,
    snapshot_store: RawSnapshotStore | None = None,
    repository: Repository | None = None,
    now: datetime | None = None,
    bounds: tuple[float, float, float, float] = AIRNOW_LA_BOUNDS,
) -> AirNowIngestionResult:
    sensor_id = sensor_id or os.getenv("PURPLEAIR_SENSOR_ID")
    if not sensor_id:
        raise RuntimeError("PURPLEAIR_SENSOR_ID is required to pair AirNow with a sensor")
    if client is None:
        client = AirNowClient(api_key=os.getenv("AIRNOW_API_KEY"))
    if snapshot_store is None:
        snapshot_store = S3SnapshotStore(
            bucket=os.getenv("S3_BUCKET", ""),
            region=os.getenv("AWS_REGION", ""),
        )
    if repository is None:
        repository = Repository(backend="cockroach")

    captured_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    sensor = repository.read_sensor(str(sensor_id))
    if not sensor:
        raise RuntimeError(f"PurpleAir sensor is not present in CockroachDB: {sensor_id}")

    snapshot = client.fetch_snapshot(bounds)
    candidates = _latest_monitors(snapshot.rows)
    if not candidates:
        raise RuntimeError("AirNow returned no current PM2.5 monitors in the Los Angeles bounds")
    paired = [
        (distance, row)
        for row in candidates
        if (distance := _distance_km(sensor, row)) is not None
    ]
    if not paired:
        raise RuntimeError("AirNow returned no monitors with usable coordinates")
    distance_km, selected = min(paired, key=lambda item: item[0])
    observed_at = _as_utc(selected.get("observed_at"), captured_at)
    observed_at_text = observed_at.isoformat().replace("+00:00", "Z")
    snapshot_key = _snapshot_key(captured_at)
    snapshot_reference: SnapshotReference = snapshot_store.put_json(snapshot_key, snapshot.payload)

    with repository.transaction() as transaction:
        monitor = transaction.upsert_monitor(
            selected["monitor_id"],
            selected.get("name"),
            selected.get("latitude"),
            selected.get("longitude"),
            _number(selected.get("aqi")),
            observed_at_text,
        )
        audit = transaction.create_audit_log(
            "airnow_ingest",
            "monitor_ingested",
            "monitor",
            selected["monitor_id"],
            details={
                "sensor_id": str(sensor_id),
                "snapshot_key": snapshot_key,
                "snapshot_uri": snapshot_reference.uri,
                "observed_at": observed_at_text,
                "distance_km": round(distance_km, 3),
                "pm25": selected.get("pm25"),
                "aqi": selected.get("aqi"),
            },
            source_snapshot_uri=snapshot_reference.uri,
        )

    return AirNowIngestionResult(
        monitor_id=str(monitor["monitor_id"]),
        snapshot_key=snapshot_key,
        snapshot_uri=snapshot_reference.uri,
        audit_id=str(audit["audit_id"]),
        observed_at=observed_at_text,
        distance_km=round(distance_km, 3),
        monitor=selected,
    )
