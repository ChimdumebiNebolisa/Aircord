from __future__ import annotations

import httpx

from aircord.ingestion.airnow import AirNowClient
from aircord.ingestion.purpleair import PURPLEAIR_FIELDS, PurpleAirClient


class _Response:
    def __init__(self, payload: object):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


def test_airnow_fetch_uses_bounded_pm25_query(monkeypatch):
    captured: dict[str, object] = {}

    def fake_get(url: str, **kwargs: object) -> _Response:
        captured.update(url=url, **kwargs)
        return _Response(
            [
                {
                    "FullAQSCode": "060370001",
                    "SiteName": "Los Angeles",
                    "Latitude": 34.05,
                    "Longitude": -118.25,
                    "Parameter": "PM25",
                    "AQI": 42,
                    "Value": 8.1,
                    "UTC": "2026-08-02T12:00:00Z",
                }
            ]
        )

    monkeypatch.setattr(httpx, "get", fake_get)
    rows = AirNowClient(api_key="test-airnow").fetch((-118.6, 33.8, -118.0, 34.3))

    assert rows[0]["monitor_id"] == "060370001"
    assert rows[0]["pm25"] == 8.1
    assert captured["params"]["parameters"] == "PM25"
    assert captured["params"]["BBOX"] == "-118.6,33.8,-118.0,34.3"


def test_purpleair_fetch_decodes_sensor_rows(monkeypatch):
    captured: dict[str, object] = {}

    def fake_get(url: str, **kwargs: object) -> _Response:
        captured.update(url=url, **kwargs)
        return _Response(
            {
                "fields": [
                    "sensor_index",
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
                ],
                "data": [[123, "Culver", 34.02, -118.4, 0, 1785672000, 12.0, 13.0, 14.0, 12.0, 45, 72, 100, -50]],
            }
        )

    monkeypatch.setattr(httpx, "get", fake_get)
    rows = PurpleAirClient(api_key="test-purpleair").fetch((-118.6, 33.8, -118.0, 34.3))

    assert rows[0]["sensor_id"] == "123"
    assert rows[0]["pm25_cf1"] == 13.0
    assert rows[0]["likely_indoor"] is False
    assert captured["headers"] == {"X-API-Key": "test-purpleair"}
    assert captured["params"]["nwlng"] == "-118.6"


def test_purpleair_fetch_sensor_returns_raw_payload_and_normalized_row(monkeypatch):
    captured: dict[str, object] = {}
    payload = {
        "fields": [
            "sensor_index",
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
        ],
        "data": [[123, "Culver", 34.02, -118.4, 0, 1785672000, 12.0, 13.0, 14.0, 12.0, 45, 72, 100, -50]],
    }

    def fake_get(url: str, **kwargs: object) -> _Response:
        captured.update(url=url, **kwargs)
        return _Response(payload)

    monkeypatch.setattr(httpx, "get", fake_get)
    result = PurpleAirClient(api_key="test-purpleair").fetch_sensor("123")

    assert result.sensor_id == "123"
    assert result.normalized["pm25_cf1"] == 13.0
    assert result.payload is payload
    assert captured["params"] == {"fields": ",".join(PURPLEAIR_FIELDS), "show_only": "123"}
