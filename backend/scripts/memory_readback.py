from __future__ import annotations

import argparse
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aircord.db.repositories import Repository  # noqa: E402
from aircord.reconciliation.readback import build_memory_readback, format_memory_readback  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Print Aircord's latest live memory loop state")
    parser.add_argument("--sensor-id", default=None)
    args = parser.parse_args()
    print(format_memory_readback(build_memory_readback(args.sensor_id, repository=Repository(backend="cockroach"))))


if __name__ == "__main__":
    main()
