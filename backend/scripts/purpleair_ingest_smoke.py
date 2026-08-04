from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aircord.ingestion.purpleair_ingest import ingest_sensor, missing_required_environment  # noqa: E402


def main() -> None:
    missing = missing_required_environment()
    if missing:
        raise SystemExit(f"PurpleAir live ingestion skipped; missing environment: {', '.join(missing)}")
    try:
        result = ingest_sensor()
    except Exception as exc:
        raise SystemExit(f"PurpleAir live ingestion failed: {type(exc).__name__}") from exc
    print(
        "PurpleAir live ingestion succeeded: "
        f"sensor={result.sensor_id}, reading={result.reading_id}, "
        f"snapshot={result.snapshot_uri}, audit={result.audit_id}"
    )


if __name__ == "__main__":
    main()
