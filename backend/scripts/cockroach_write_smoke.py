from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aircord.db.repositories import Repository  # noqa: E402


def main() -> None:
    sensor_id = f"repository-smoke-{uuid4().hex[:12]}"
    try:
        repository = Repository(backend="cockroach")
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
                details={"source": "cockroach_repository_smoke"},
            )

            if transaction.read_sensor(sensor["sensor_id"]) is None:
                raise RuntimeError("Sensor could not be read back")
            if transaction.read_sensor_reading(reading["reading_id"]) is None:
                raise RuntimeError("Sensor reading could not be read back")
            if transaction.read_audit_log(audit["audit_id"]) is None:
                raise RuntimeError("Audit log row could not be read back")
        print("CockroachDB repository write/read smoke succeeded: sensors=1, sensor_readings=1, audit_log=1 (rolled back)")
    except Exception as exc:
        raise SystemExit(f"CockroachDB repository write/read smoke failed: {type(exc).__name__}") from exc


if __name__ == "__main__":
    main()
