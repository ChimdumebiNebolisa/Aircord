from __future__ import annotations

import argparse
from pathlib import Path

from aircord.config import DB_PATH
from aircord.db.repositories import Repository
from aircord.fixtures import seed_demo
from aircord.reconciliation.commit import VersionConflict, commit_candidate
from aircord.reconciliation.compute import compute_cell_candidate


def reconcile_cluster(path: Path = DB_PATH, cluster_id: str = "greater-la") -> list[str]:
    seed_demo(path)
    cells = Repository(path).many("SELECT cell_id FROM cells WHERE cluster_id = ? ORDER BY cell_id", (cluster_id,))
    committed: list[str] = []
    for row in cells:
        candidate = compute_cell_candidate(path, row["cell_id"])
        for _attempt in range(2):
            try:
                committed.append(commit_candidate(path, candidate))
                break
            except VersionConflict:
                candidate = compute_cell_candidate(path, row["cell_id"])
        else:
            raise RuntimeError(f"Could not commit {row['cell_id']} after retry")
    return committed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cluster", default="greater-la")
    args = parser.parse_args()
    for estimate_id in reconcile_cluster(DB_PATH, args.cluster):
        print(estimate_id)


if __name__ == "__main__":
    main()

