from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx


PURPLEAIR_SENSORS_URL = "https://api.purpleair.com/v1/sensors"
PURPLEAIR_FIELDS = (
    "name",
    "latitude",
    "longitude",
    "location_type",
    "last_seen",
    "pm2.5_atm",
    "pm2.5_cf_1",
    "pm2.5_cf_1_a",
    "pm2.5_cf_1_b",
    "humidity",
    "temperature",
    "uptime",
    "rssi",
)


def _tabular_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    fields = payload.get("fields")
    data = payload.get("data")
    if not isinstance(fields, list) or not isinstance(data, list):
        raise RuntimeError("PurpleAir returned an unexpected response shape")
    return [dict(zip(fields, values)) for values in data if isinstance(values, list)]


def _iso_timestamp(value: Any) -> str | None:
    if value in (None, ""):
        return None
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat().replace("+00:00", "Z")
    except (TypeError, ValueError, OverflowError):
        return None


def normalize_purpleair_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert PurpleAir's fields/data response into Aircord-shaped rows."""
    normalized = []
    for row in _tabular_rows(payload):
        sensor_id = row.get("sensor_index")
        if sensor_id in (None, ""):
            continue
        normalized.append(
            {
                "sensor_id": str(sensor_id),
                "name": row.get("name"),
                "latitude": row.get("latitude"),
                "longitude": row.get("longitude"),
                "likely_indoor": row.get("location_type") == 1,
                "last_seen_at": _iso_timestamp(row.get("last_seen")),
                "pm25_atm": row.get("pm2.5_atm"),
                "pm25_cf1": row.get("pm2.5_cf_1"),
                "channel_a_pm25": row.get("pm2.5_cf_1_a"),
                "channel_b_pm25": row.get("pm2.5_cf_1_b"),
                "humidity": row.get("humidity"),
                "temperature": row.get("temperature"),
                "uptime": row.get("uptime"),
                "rssi": row.get("rssi"),
                "source": "purpleair",
                "raw": row,
            }
        )
    return normalized


@dataclass(frozen=True)
class PurpleAirSensorSnapshot:
    sensor_id: str
    normalized: dict[str, Any]
    payload: dict[str, Any]


@dataclass(frozen=True)
class PurpleAirClient:
    api_key: str | None = None
    http_get: Any | None = None

    def _fetch_payload(self, params: dict[str, str]) -> dict[str, Any]:
        api_key = self.api_key or os.getenv("PURPLEAIR_API_KEY")
        if not api_key:
            raise RuntimeError("PURPLEAIR_API_KEY is required for live ingestion; use fixture mode locally")

        try:
            response = (self.http_get or httpx.get)(
                PURPLEAIR_SENSORS_URL,
                params=params,
                headers={"X-API-Key": api_key},
                timeout=30.0,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError("PurpleAir request failed") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("PurpleAir returned an unexpected response shape")
        return payload

    def fetch(self, bounds: tuple[float, float, float, float]) -> list[dict[str, Any]]:
        west, south, east, north = bounds
        payload = self._fetch_payload(
            {
                "fields": ",".join(PURPLEAIR_FIELDS),
                "nwlng": str(west),
                "nwlat": str(north),
                "selng": str(east),
                "selat": str(south),
            }
        )
        return normalize_purpleair_rows(payload)

    def fetch_sensor(self, sensor_id: str) -> PurpleAirSensorSnapshot:
        if not sensor_id:
            raise ValueError("PURPLEAIR_SENSOR_ID is required for single-sensor ingestion")
        payload = self._fetch_payload(
            {
                "fields": ",".join(PURPLEAIR_FIELDS),
                "show_only": str(sensor_id),
            }
        )
        rows = normalize_purpleair_rows(payload)
        row = next((candidate for candidate in rows if candidate["sensor_id"] == str(sensor_id)), None)
        if row is None:
            raise RuntimeError(f"PurpleAir sensor was not returned: {sensor_id}")
        return PurpleAirSensorSnapshot(sensor_id=str(sensor_id), normalized=row, payload=payload)

