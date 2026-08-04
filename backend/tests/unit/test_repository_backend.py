from __future__ import annotations

from datetime import datetime, timezone

import pytest

from aircord.db.repositories import Repository


def test_repository_uses_sqlite_when_database_url_is_missing(monkeypatch, demo_db):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    repository = Repository(demo_db)

    assert repository.backend == "sqlite"


def test_repository_uses_cockroach_when_database_url_is_present(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:password@example.com:26257/aircord")

    repository = Repository()

    assert repository.backend == "cockroach"


def test_repository_can_create_and_read_sensor_reading_and_audit_rows(monkeypatch, demo_db):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    repository = Repository(demo_db, backend="sqlite")
    observed_at = datetime(2026, 8, 4, 18, 0, tzinfo=timezone.utc)

    sensor = repository.create_sensor(
        "sensor-repository-test",
        "Repository test sensor",
        34.02,
        -118.40,
        cluster_id="greater-la",
        cell_id="cell-culver",
    )
    reading = repository.create_sensor_reading(
        "sensor-repository-test",
        observed_at,
        12.3,
        12.0,
        12.6,
        45.0,
        -50.0,
        reading_id="reading-repository-test",
        cell_id="cell-culver",
        temperature=24.0,
        raw_ref="test://repository",
    )
    audit = repository.create_audit_log(
        "repository_test",
        "smoke_insert",
        "sensor",
        sensor["sensor_id"],
        reason="Repository test audit row",
        audit_id="audit-repository-test",
    )

    assert repository.read_sensor(sensor["sensor_id"])["name"] == "Repository test sensor"
    assert repository.read_sensor_reading(reading["reading_id"])["sensor_id"] == sensor["sensor_id"]
    assert repository.read_audit_log(audit["audit_id"])["entity_id"] == sensor["sensor_id"]


def test_explicit_cockroach_backend_requires_database_url(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
        Repository(tmp_path / "unused.sqlite3", backend="cockroach").one("SELECT 1")
