from __future__ import annotations

import os
from typing import Any

from aircord.db.repositories import Repository


def build_memory_readback(
    sensor_id: str | None = None,
    *,
    repository: Repository | None = None,
) -> dict[str, Any]:
    sensor_id = sensor_id or os.getenv("PURPLEAIR_SENSOR_ID")
    if not sensor_id:
        raise RuntimeError("PURPLEAIR_SENSOR_ID is required for memory readback")
    repository = repository or Repository(backend="cockroach")
    cell_id = f"greater-la-sensor-{sensor_id}"
    return {
        "sensor": repository.read_sensor(str(sensor_id)),
        "latest_sensor_reading": repository.one(
            "SELECT * FROM sensor_readings WHERE sensor_id = ? ORDER BY observed_at DESC LIMIT 1",
            (str(sensor_id),),
        ),
        "latest_monitor": repository.one(
            "SELECT * FROM monitors ORDER BY observed_at DESC NULLS LAST, updated_at DESC LIMIT 1"
        ),
        "sensor_reputation": repository.sensor_reputation(str(sensor_id)),
        "latest_cell_estimate": repository.latest_estimate(cell_id),
        "latest_resolution": repository.latest_resolution(cell_id),
        "audit_rows": repository.many(
            """
            SELECT * FROM audit_log
            WHERE (entity_type = 'sensor' AND entity_id = ?)
               OR (entity_type = 'resolution' AND entity_id IN (
                   SELECT resolution_id::text FROM resolutions WHERE cell_id = ?
               ))
               OR actor = 'airnow_ingest'
            ORDER BY created_at DESC
            LIMIT 10
            """,
            (str(sensor_id), cell_id),
        ),
    }


def format_memory_readback(readback: dict[str, Any]) -> str:
    sensor = readback.get("sensor") or {}
    reading = readback.get("latest_sensor_reading") or {}
    monitor = readback.get("latest_monitor") or {}
    reputation = readback.get("sensor_reputation") or {}
    estimate = readback.get("latest_cell_estimate") or {}
    resolution = readback.get("latest_resolution") or {}
    lines = [
        "Aircord memory readback",
        f"sensor: {sensor.get('sensor_id', 'missing')} ({sensor.get('name') or 'unnamed'})",
        f"latest sensor reading: id={reading.get('reading_id', 'missing')} pm25_cf1={reading.get('pm25_cf1')} observed_at={reading.get('observed_at')}",
        f"latest monitor: id={monitor.get('monitor_id', 'missing')} aqi={monitor.get('latest_aqi')} observed_at={monitor.get('observed_at')}",
        f"sensor reputation: score={reputation.get('reputation_score')} channel_agreement={reputation.get('channel_agreement_score')} drift={reputation.get('drift_score')}",
        f"latest cell estimate: cell_id={estimate.get('cell_id', 'missing')} estimate_aqi={estimate.get('estimate_aqi')} confidence={estimate.get('confidence')}",
        f"latest resolution: id={resolution.get('resolution_id', 'missing')} reasoning={resolution.get('reasoning_text')}",
        "latest audit rows:",
    ]
    for row in readback.get("audit_rows", []):
        lines.append(
            f"- {row.get('created_at')}: actor={row.get('actor')} action={row.get('action')} "
            f"entity={row.get('entity_type')}:{row.get('entity_id')}"
        )
    return "\n".join(lines)
