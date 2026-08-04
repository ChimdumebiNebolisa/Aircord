from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aircord.reconciliation.live_memory import run_memory_loop  # noqa: E402


def main() -> None:
    try:
        result = run_memory_loop()
    except Exception as exc:
        raise SystemExit(f"Aircord memory loop failed: {type(exc).__name__}") from exc
    print(
        "Aircord memory loop succeeded: "
        f"sensor={result.sensor_id}, monitor={result.monitor_id}, "
        f"reputation={result.reputation_score}, decision={result.decision}, "
        f"cell={result.cell_id}, resolution={result.resolution_id}, "
        f"audits={result.reputation_audit_id},{result.resolution_audit_id}"
    )


if __name__ == "__main__":
    main()
