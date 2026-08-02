from __future__ import annotations

import argparse

from aircord.config import DB_PATH, MODE
from aircord.db.repositories import Repository
from aircord.fixtures import seed_demo


def discover(cluster_id: str = "greater-la") -> dict:
    seed_demo(DB_PATH)
    repository = Repository(DB_PATH)
    cluster = repository.one("SELECT * FROM clusters WHERE cluster_id = ?", (cluster_id,))
    if not cluster:
        raise ValueError(f"Unknown cluster: {cluster_id}")
    anchors = repository.many(
        "SELECT DISTINCT sensor_id FROM sensor_readings WHERE cell_id IN (SELECT cell_id FROM cells WHERE cluster_id = ?)",
        (cluster_id,),
    )
    return {
        "cluster_id": cluster_id,
        "mode": MODE,
        "gate_a_status": cluster["gate_a_status"],
        "paired_anchor_count": len(anchors),
        "notes": cluster["gate_a_notes"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cluster", default="greater-la")
    args = parser.parse_args()
    print(discover(args.cluster))


if __name__ == "__main__":
    main()

