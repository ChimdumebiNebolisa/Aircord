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
class PurpleAirClient:
    api_key: str | None = None

    def fetch(self, _bounds: tuple[float, float, float, float]) -> list[dict]:
        api_key = self.api_key or os.getenv("PURPLEAIR_API_KEY")
        if not api_key:
            raise RuntimeError("PURPLEAIR_API_KEY is required for live ingestion; use fixture mode locally")

        west, south, east, north = _bounds
        params = {
            "fields": ",".join(PURPLEAIR_FIELDS),
            "nwlng": str(west),
            "nwlat": str(north),
            "selng": str(east),
            "selat": str(south),
        }
        try:
            response = httpx.get(
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
        return normalize_purpleair_rows(payload)

