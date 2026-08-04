from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aircord.demo import DEFAULT_SENSOR_ID, build_demo_summary  # noqa: E402
from aircord.db.repositories import Repository  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Print Aircord's CockroachDB-backed judge demo state")
    parser.add_argument("--sensor-id", default=DEFAULT_SENSOR_ID)
    parser.add_argument(
        "--write-frontend-snapshot",
        action="store_true",
        help="Write the same live result to frontend/public/demo-summary.json",
    )
    args = parser.parse_args()

    summary = build_demo_summary(Repository(backend="cockroach"), args.sensor_id)
    payload = json.dumps(summary, indent=2, sort_keys=True, default=str)
    if args.write_frontend_snapshot:
        snapshot_path = Path(__file__).resolve().parents[2] / "frontend" / "public" / "demo-summary.json"
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
