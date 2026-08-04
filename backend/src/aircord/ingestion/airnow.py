from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx


AIRNOW_DATA_URL = "https://www.airnowapi.org/aq/data/"


def _first(row: dict[str, Any], *names: str) -> Any:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return value
    return None


def normalize_airnow_rows(payload: Any) -> list[dict[str, Any]]:
    """Convert AirNow's monitoring-site response into Aircord-shaped rows."""
    rows = payload.get("data", []) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise RuntimeError("AirNow returned an unexpected response shape")

    normalized = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        parameter = str(_first(row, "Parameter", "ParameterName", "parameter") or "").upper()
        if parameter not in {"PM25", "PM2.5", "PM2_5"}:
            continue
        monitor_id = _first(row, "FullAQSCode", "AQSID", "StationID", "SiteCode", "SiteName")
        if monitor_id is None:
            continue
        observed_at = _first(row, "UTC", "ObservedAt", "observed_at")
        if observed_at is None:
            date_observed = _first(row, "DateObserved", "date_observed")
            hour_observed = _first(row, "HourObserved", "hour_observed")
            if date_observed is not None and hour_observed is not None:
                observed_at = f"{date_observed}T{int(hour_observed):02d}:00:00"

        normalized.append(
            {
                "monitor_id": str(monitor_id),
                "name": _first(row, "SiteName", "ReportingArea", "site_name"),
                "latitude": _first(row, "Latitude", "latitude"),
                "longitude": _first(row, "Longitude", "longitude"),
                "observed_at": observed_at,
                "aqi": _first(row, "AQI", "aqi"),
                "pm25": _first(row, "Value", "Concentration", "concentration", "pm25"),
                "parameter": parameter,
                "source": "airnow",
                "raw": row,
            }
        )
    return normalized


@dataclass(frozen=True)
class AirNowClient:
    api_key: str | None = None
    http_get: Any | None = None

    def _fetch_payload(self, bounds: tuple[float, float, float, float]) -> Any:
        api_key = self.api_key or os.getenv("AIRNOW_API_KEY")
        if not api_key:
            raise RuntimeError("AIRNOW_API_KEY is required for live ingestion; use fixture mode locally")

        west, south, east, north = bounds
        end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        # AirNow observations arrive on an hourly cadence; use a bounded recent
        # window so a request made between publication updates still has data.
        start = end - timedelta(hours=24)
        params = {
            "startDate": start.strftime("%Y-%m-%dT%H"),
            "endDate": end.strftime("%Y-%m-%dT%H"),
            "parameters": "PM25",
            "BBOX": f"{west},{south},{east},{north}",
            "dataType": "B",
            "format": "application/json",
            "verbose": "1",
            "monitorType": "0",
            "includerawconcentrations": "0",
            "API_KEY": api_key,
        }
        try:
            response = (self.http_get or httpx.get)(AIRNOW_DATA_URL, params=params, timeout=30.0)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError("AirNow request failed") from exc
        return payload

    def fetch_snapshot(self, bounds: tuple[float, float, float, float]) -> AirNowSnapshot:
        payload = self._fetch_payload(bounds)
        return AirNowSnapshot(payload=payload, rows=normalize_airnow_rows(payload))

    def fetch(self, bounds: tuple[float, float, float, float]) -> list[dict]:
        return self.fetch_snapshot(bounds).rows


@dataclass(frozen=True)
class AirNowSnapshot:
    payload: Any
    rows: list[dict[str, Any]]

