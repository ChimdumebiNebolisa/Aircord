from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aircord.ingestion.airnow_ingest import ingest_airnow, missing_required_environment  # noqa: E402


def main() -> None:
    missing = missing_required_environment()
    if missing:
        raise SystemExit(f"AirNow live ingestion skipped; missing environment: {', '.join(missing)}")
    try:
        result = ingest_airnow()
    except Exception as exc:
        raise SystemExit(f"AirNow live ingestion failed: {type(exc).__name__}") from exc
    print(
        "AirNow live ingestion succeeded: "
        f"monitor={result.monitor_id}, snapshot={result.snapshot_uri}, "
        f"distance_km={result.distance_km}, audit={result.audit_id}"
    )


if __name__ == "__main__":
    main()
