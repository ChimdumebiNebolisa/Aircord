from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from aircord.db.repositories import Repository


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL is not configured")
def test_cockroach_repository_round_trip():
    repository = Repository(backend="cockroach")
    sensor_id = f"repository-smoke-{uuid4().hex[:12]}"

    with repository.transaction(rollback=True) as transaction:
        sensor = transaction.create_sensor(
            sensor_id,
            "Aircord repository smoke sensor",
            34.02,
            -118.40,
        )
        reading = transaction.create_sensor_reading(
            sensor_id,
            datetime.now(timezone.utc),
            12.3,
            12.0,
            12.6,
            45.0,
            -50.0,
        )
        audit = transaction.create_audit_log(
            "repository_smoke",
            "smoke_insert",
            "sensor",
            sensor_id,
            details={"source": "pytest"},
        )

        assert transaction.read_sensor(sensor_id)["sensor_id"] == sensor_id
        assert transaction.read_sensor_reading(reading["reading_id"])["sensor_id"] == sensor_id
        assert transaction.read_audit_log(audit["audit_id"])["entity_id"] == sensor_id
