from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from aircord.config import DB_PATH
from aircord.db.repositories import Repository
from aircord.fixtures import seed_demo
from aircord.reconciliation.methods import raw_estimate, static_correction_estimate, trust_weighted_estimate
from aircord.backtest.alignment import align_rows
from aircord.reputation.scoring import decision_for_score


METHODS = ("raw_purpleair", "static_correction", "aircord")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_backtest(path: Path = DB_PATH, cluster_id: str = "greater-la") -> dict:
    seed_demo(path)
    aligned = align_rows(Repository(path).readings_for_backtest(cluster_id))
    run_id = f"backtest-{uuid4().hex[:12]}"
    now = _now()
    if len(aligned) < 3:
        with Repository(path).transaction() as transaction:
            transaction.execute(
                "INSERT INTO backtest_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (run_id, cluster_id, "", "", "insufficient_data", "no_claim", "Fewer than three aligned observations", now, now),
            )
        return {"backtest_run_id": run_id, "status": "insufficient_data", "claim_status": "no_claim", "summaries": [], "failure_reason": "Fewer than three aligned observations"}
    segments: dict[str, dict[str, list[float]]] = {"all": {method: [] for method in METHODS}, "healthy": {method: [] for method in METHODS}, "degraded": {method: [] for method in METHODS}}
    for group in aligned:
        rows = group["rows"]
        reference = float(group["reference_aqi"])
        values = [float(row["pm25_cf1"]) for row in rows]
        weighted = []
        for row in rows:
            score = float(row.get("reputation_score") or 0.0)
            _decision, weight, _reasons = decision_for_score(
                score,
                json.loads(row.get("features_json") or "{}"),
                bool(row.get("likely_indoor")),
            )
            weighted.append((float(row["pm25_cf1"]), weight))
        estimates = {
            "raw_purpleair": raw_estimate(values),
            "static_correction": static_correction_estimate(values),
            "aircord": trust_weighted_estimate(weighted),
        }
        degraded = any(float(row.get("reputation_score") or 0.0) < 0.7 for row in rows)
        for method, estimate in estimates.items():
            segments["all"][method].append(abs(estimate - reference))
            segments["degraded" if degraded else "healthy"][method].append(abs(estimate - reference))
    summaries = []
    with Repository(path).transaction() as transaction:
        transaction.execute(
            "INSERT INTO backtest_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (run_id, cluster_id, aligned[0]["observed_at"], aligned[-1]["observed_at"], "passed", "measured", None, now, now),
        )
        for segment, methods in segments.items():
            for method, errors in methods.items():
                if not errors:
                    continue
                summary = {
                    "backtest_run_id": run_id,
                    "segment": segment,
                    "method": method,
                    "observation_count": len(errors),
                    "mean_absolute_error": round(statistics.mean(errors), 2),
                    "median_absolute_error": round(statistics.median(errors), 2),
                }
                summaries.append(summary)
                transaction.execute(
                    "INSERT INTO backtest_summaries VALUES (?, ?, ?, ?, ?, ?)",
                    (run_id, segment, method, summary["observation_count"], summary["mean_absolute_error"], summary["median_absolute_error"]),
                )
        transaction.create_audit_log(
            "backtest_runner",
            "backtest_completed",
            "backtest",
            run_id,
            reason="Computed from aligned fixture time series",
            created_at=now,
        )
    return {"backtest_run_id": run_id, "status": "passed", "claim_status": "measured", "summaries": summaries, "failure_reason": None}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cluster", default="greater-la")
    parser.add_argument("--window-days", type=int, default=14)
    args = parser.parse_args()
    print(run_backtest(DB_PATH, args.cluster))


if __name__ == "__main__":
    main()
