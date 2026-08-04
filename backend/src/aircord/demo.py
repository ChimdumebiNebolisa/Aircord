"""Judge-facing read-only view of Aircord's persisted memory loop."""

from __future__ import annotations

import math
from typing import Any

from aircord.config import MEDICAL_DIRECTIVE_CAVEAT, REFERENCE_CAVEAT
from aircord.db.repositories import Repository
from aircord.reputation.vector import build_behavioral_fingerprint


DEFAULT_SENSOR_ID = "54917"
DEFAULT_CELL_ID = f"greater-la-sensor-{DEFAULT_SENSOR_ID}"
MCP_QUERY_PATH = "docs/cockroachdb_mcp_queries.sql"
MCP_QUESTIONS = (
    "Why was sensor 54917 downweighted?",
    "What evidence did Aircord use?",
    "What is the latest reputation score?",
    "Show the latest resolution and audit trail.",
    "Show the latest backtest result and caveats.",
)
DEMO_CAVEATS = (
    "The backtest has a small sample and is not a broad accuracy claim.",
    "PurpleAir PM2.5 and AirNow AQI are different units in this MVP comparison.",
    "The regulatory monitor is an evaluation reference, not absolute truth.",
    "PurpleAir is points-billed; live polling should remain bounded.",
)


def _number(value: Any) -> float | None:
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def _json_object(value: Any) -> Any:
    if isinstance(value, str):
        try:
            import json

            return json.loads(value)
        except (TypeError, ValueError):
            return value
    return value


def _distance_km(sensor: dict[str, Any] | None, monitor: dict[str, Any] | None) -> float | None:
    if not sensor or not monitor:
        return None
    sensor_lat = _number(sensor.get("latitude", sensor.get("lat")))
    sensor_lon = _number(sensor.get("longitude", sensor.get("lon")))
    monitor_lat = _number(monitor.get("latitude", monitor.get("lat")))
    monitor_lon = _number(monitor.get("longitude", monitor.get("lon")))
    if None in (sensor_lat, sensor_lon, monitor_lat, monitor_lon):
        return None
    lat1, lon1, lat2, lon2 = map(math.radians, (sensor_lat, sensor_lon, monitor_lat, monitor_lon))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    haversine = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return round(6371.0 * 2 * math.asin(math.sqrt(haversine)), 2)


def latest_sensor_reading(repository: Repository, sensor_id: str) -> dict[str, Any] | None:
    return repository.one(
        "SELECT * FROM sensor_readings WHERE sensor_id = ? ORDER BY observed_at DESC LIMIT 1",
        (sensor_id,),
    )


def latest_monitor(repository: Repository) -> dict[str, Any] | None:
    if repository.backend == "cockroach":
        return repository.one(
            "SELECT * FROM monitors ORDER BY observed_at DESC NULLS LAST, updated_at DESC LIMIT 1"
        )
    return repository.one("SELECT * FROM monitors ORDER BY observed_at DESC LIMIT 1")


def latest_audit_rows(repository: Repository, sensor_id: str, cell_id: str, limit: int = 12) -> list[dict[str, Any]]:
    if repository.backend == "cockroach":
        resolution_ids = "SELECT resolution_id::STRING FROM resolutions WHERE cell_id = ?"
    else:
        resolution_ids = "SELECT resolution_id FROM resolutions WHERE cell_id = ?"
    return repository.many(
        f"""
        SELECT * FROM audit_log
        WHERE (entity_type = 'sensor' AND entity_id = ?)
           OR (entity_type = 'resolution' AND entity_id IN ({resolution_ids}))
           OR actor IN ('purpleair_ingest', 'airnow_ingest', 'aircord_memory', 'backtest_runner')
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (sensor_id, cell_id, limit),
    )


def latest_backtest(repository: Repository) -> dict[str, Any] | None:
    run = repository.latest_backtest()
    if not run:
        return None
    return {
        **run,
        "summaries": repository.backtest_summaries(run["backtest_run_id"]),
    }


def similarity_view(
    repository: Repository,
    sensor: dict[str, Any] | None,
    reading: dict[str, Any] | None,
    monitor: dict[str, Any] | None,
    estimate: dict[str, Any] | None,
    sensor_id: str,
) -> dict[str, Any]:
    if repository.backend != "cockroach":
        return {
            "status": "empty",
            "message": "Vector similarity is available in CockroachDB mode only.",
            "fingerprint_dimensions": 8,
            "fingerprint_features": {},
            "nearest": [],
        }
    if not sensor or not reading:
        return {
            "status": "empty",
            "message": "A sensor and reading are required to compute similarity.",
            "fingerprint_dimensions": 8,
            "fingerprint_features": {},
            "nearest": [],
        }
    vector, features = build_behavioral_fingerprint(
        sensor,
        reading,
        monitor,
        confidence=_number((estimate or {}).get("confidence")),
    )
    nearest = repository.similar_sensor_embeddings(vector, exclude_sensor_id=sensor_id, limit=5)
    return {
        "status": "ok",
        "message": "Lower cosine distance means the handcrafted behavioral features are more similar; it is not an accuracy score.",
        "fingerprint_dimensions": len(vector),
        "fingerprint_features": features,
        "nearest": [
            {
                "sensor_id": row["sensor_id"],
                "cosine_distance": row.get("cosine_distance"),
                "updated_at": row.get("updated_at"),
                "source": (_json_object(row.get("feature_json")) or {}).get("source", "unknown"),
                "label": (_json_object(row.get("feature_json")) or {}).get("label"),
            }
            for row in nearest
        ],
    }


def build_demo_summary(
    repository: Repository,
    sensor_id: str = DEFAULT_SENSOR_ID,
) -> dict[str, Any]:
    cell_id = f"greater-la-sensor-{sensor_id}"
    sensor = repository.read_sensor(sensor_id)
    reading = latest_sensor_reading(repository, sensor_id)
    monitor = latest_monitor(repository)
    reputation = repository.sensor_reputation(sensor_id)
    estimate = repository.latest_estimate(cell_id)
    resolution = repository.latest_resolution(cell_id)
    audits = latest_audit_rows(repository, sensor_id, cell_id)
    backtest = latest_backtest(repository)
    similarity = similarity_view(repository, sensor, reading, monitor, estimate, sensor_id)
    has_live_memory = any((sensor, reading, reputation, estimate, resolution))
    return {
        "status": "ok" if has_live_memory else "empty",
        "message": "CockroachDB-backed Aircord memory is available." if has_live_memory else "No persisted Aircord memory was found for this sensor.",
        "sensor_id": sensor_id,
        "cell_id": cell_id,
        "sensor": sensor,
        "latest_sensor_reading": reading,
        "airnow_reference": {
            "monitor": monitor,
            "distance_km": _distance_km(sensor, monitor),
        },
        "sensor_reputation": reputation,
        "latest_cell_estimate": estimate,
        "latest_resolution": resolution,
        "audit_rows": audits,
        "similarity": similarity,
        "latest_backtest": backtest,
        "caveats": list(DEMO_CAVEATS),
        "mcp": {
            "status": "documented_fallback",
            "query_path": MCP_QUERY_PATH,
            "questions": list(MCP_QUESTIONS),
            "message": "These questions are backed by the read-only SQL file until Managed MCP OAuth and cluster authorization are completed.",
        },
        "reference_caveat": REFERENCE_CAVEAT,
        "medical_directive_caveat": MEDICAL_DIRECTIVE_CAVEAT,
    }


def section_response(summary: dict[str, Any], key: str, sensor_id: str) -> dict[str, Any]:
    value = summary.get(key)
    if value in (None, {}, []):
        return {
            "status": "empty",
            "sensor_id": sensor_id,
            "data": None,
            "message": f"No {key.replace('_', ' ')} is stored for sensor {sensor_id}.",
        }
    return {"status": "ok", "sensor_id": sensor_id, "data": value}
