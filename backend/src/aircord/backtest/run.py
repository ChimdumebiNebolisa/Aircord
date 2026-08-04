from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from aircord.config import DB_PATH
from aircord.db.backtest_schema import COCKROACH_BACKTEST_SCHEMA
from aircord.db.connection import database_url_configured
from aircord.db.repositories import Repository
from aircord.fixtures import seed_demo
from aircord.reconciliation.methods import raw_estimate, static_correction_estimate, trust_weighted_estimate
from aircord.backtest.alignment import align_rows, align_sensor_monitor_rows
from aircord.backtest.metrics import MIN_METRIC_SAMPLES, absolute_errors, summarize_errors
from aircord.reconciliation.methods import reference_blended_estimate
from aircord.reputation.scoring import decision_for_score, score_live_pair


METHODS = ("raw_purpleair", "static_correction", "aircord")
LIVE_BACKTEST_CAVEAT = (
    "Limited live comparison: normalized PurpleAir readings are paired with the available "
    "AirNow monitor snapshot; this is not an accuracy claim."
)

def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _number(value: Any) -> float | None:
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def _sensor_pm25(row: dict[str, Any]) -> tuple[float | None, str | None]:
    pm25_cf1 = _number(row.get("pm25_cf1"))
    if pm25_cf1 is not None:
        return pm25_cf1, None
    pm25_atm = _number(row.get("pm25_atm"))
    if pm25_atm is not None:
        return pm25_atm, "pm25_cf1 missing; used pm25_atm"
    return None, "PurpleAir PM2.5 missing"


def _live_observation(
    aligned: dict[str, Any],
    *,
    evaluation_end: datetime,
) -> dict[str, Any]:
    reading = dict(aligned["sensor"])
    monitor = dict(aligned["monitor"])
    monitor["latest_aqi"] = _number(monitor.get("latest_aqi", monitor.get("aqi")))
    pm25, pm25_note = _sensor_pm25(reading)
    score = score_live_pair(
        reading,
        monitor,
        likely_indoor=bool(reading.get("likely_indoor", reading.get("indoor_flag", False))),
        now=evaluation_end,
    )
    decision, weight, reasons = decision_for_score(
        score.score,
        score.features,
        likely_indoor=bool(reading.get("likely_indoor", reading.get("indoor_flag", False))),
    )
    degraded_reasons = list(reasons)
    if pm25 is None:
        degraded_reasons.append("missing_pm25")
    if _number(reading.get("channel_a")) is None or _number(reading.get("channel_b")) is None:
        degraded_reasons.append("missing_channel")
    if score.features["freshness_score"] < 0.5:
        degraded_reasons.append("stale")
    degraded_reasons = list(dict.fromkeys(degraded_reasons))
    reference = monitor["latest_aqi"]
    aircord = None
    aircord_basis = None
    if pm25 is not None and reference is not None:
        aircord, aircord_basis = reference_blended_estimate(pm25, reference, weight)
    if score.features["channel_agreement_score"] < 0.75 and "channel_divergence" not in degraded_reasons:
        degraded_reasons.append("channel_divergence")
    degraded = bool(degraded_reasons)
    return {
        "sensor_id": aligned["sensor_id"],
        "reading_id": aligned.get("reading_id"),
        "observed_at": aligned["observed_at"],
        "reference_aqi": reference,
        "pm25": pm25,
        "pm25_note": pm25_note,
        "raw_purpleair": pm25,
        "static_correction": round(pm25 * 0.75, 1) if pm25 is not None else None,
        "aircord": aircord,
        "aircord_basis": aircord_basis,
        "score": score.score,
        "weight": weight,
        "decision": decision,
        "features": score.features,
        "degraded": degraded,
        "degraded_reasons": degraded_reasons,
        "time_gap_minutes": aligned["time_gap_minutes"],
    }


def compute_sensor_monitor_backtest(
    sensor_id: str,
    monitor_id: str,
    sensor_rows: list[dict[str, Any]],
    monitor_rows: list[dict[str, Any]],
    *,
    window_start: datetime,
    window_end: datetime,
    max_gap_minutes: float = 180.0,
) -> dict[str, Any]:
    """Compute the live sensor/monitor backtest without writing to a database."""
    aligned = align_sensor_monitor_rows(
        sensor_rows,
        monitor_rows,
        max_gap_minutes=max_gap_minutes,
    )
    observations = [_live_observation(item, evaluation_end=window_end) for item in aligned]
    valid = [item for item in observations if item["raw_purpleair"] is not None and item["reference_aqi"] is not None]
    degraded = [item for item in valid if item["degraded"]]
    segments = {"all": valid, "degraded": degraded}
    summaries: list[dict[str, Any]] = []
    for segment, segment_rows in segments.items():
        for method in METHODS:
            predictions = [row[method] for row in segment_rows]
            references = [row["reference_aqi"] for row in segment_rows]
            errors = absolute_errors(predictions, references)
            summary = summarize_errors(errors)
            if summary["mean_absolute_error"] is None:
                continue
            summaries.append(
                {
                    "segment": segment,
                    "method": method,
                    **summary,
                    "notes": "Measured on aligned observations; not an accuracy claim.",
                }
            )

    caveats = [
        LIVE_BACKTEST_CAVEAT,
        "PurpleAir PM2.5 and AirNow AQI are different units; errors are proxy comparisons.",
    ]
    if len(monitor_rows) <= 1:
        caveats.append("Only one AirNow monitor observation was available; monitor history is limited.")
    if len(observations) != len(valid):
        caveats.append(f"Excluded {len(observations) - len(valid)} aligned reading(s) with missing PM2.5 or reference values.")
    if len(valid) < MIN_METRIC_SAMPLES:
        caveats.append(f"At least {MIN_METRIC_SAMPLES} valid aligned observations are required before metrics are emitted.")
    if len(degraded) < MIN_METRIC_SAMPLES:
        caveats.append("Degraded-subset metrics are withheld until the degraded subset has enough observations.")

    status = "passed" if len(valid) >= MIN_METRIC_SAMPLES else "insufficient_data"
    return {
        "status": status,
        "claim_status": "measured" if status == "passed" else "no_claim",
        "sensor_id": sensor_id,
        "monitor_id": monitor_id,
        "window_start": _iso(window_start),
        "window_end": _iso(window_end),
        "sample_count": len(valid),
        "aligned_count": len(observations),
        "degraded_sample_count": len(degraded),
        "summaries": summaries,
        "caveats": caveats,
        "failure_reason": None if status == "passed" else f"Fewer than {MIN_METRIC_SAMPLES} valid aligned observations",
    }


def _ensure_cockroach_backtest_schema(repository: Repository) -> None:
    if repository.backend != "cockroach":
        return
    with repository.transaction() as transaction:
        for statement in COCKROACH_BACKTEST_SCHEMA:
            transaction.execute(statement)


def _persist_sensor_monitor_backtest(repository: Repository, result: dict[str, Any]) -> dict[str, Any]:
    run_id = f"backtest-{uuid4().hex[:12]}"
    created_at = _now()
    _ensure_cockroach_backtest_schema(repository)
    with repository.transaction() as transaction:
        transaction.execute(
            """
            INSERT INTO backtest_runs
              (backtest_run_id, cluster_id, window_start, window_end, status, claim_status, failure_reason, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                "greater-la",
                result["window_start"],
                result["window_end"],
                result["status"],
                result["claim_status"],
                result["failure_reason"],
                created_at,
                created_at,
            ),
        )
        for summary in result["summaries"]:
            if repository.backend == "cockroach":
                transaction.execute(
                    """
                    INSERT INTO backtest_summaries
                      (backtest_run_id, segment, method, observation_count, mean_absolute_error, median_absolute_error, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        summary["segment"],
                        summary["method"],
                        summary["observation_count"],
                        summary["mean_absolute_error"],
                        summary["median_absolute_error"],
                        summary["notes"],
                    ),
                )
            else:
                transaction.execute(
                    "INSERT INTO backtest_summaries VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        run_id,
                        summary["segment"],
                        summary["method"],
                        summary["observation_count"],
                        summary["mean_absolute_error"],
                        summary["median_absolute_error"],
                    ),
                )
        transaction.create_audit_log(
            "backtest_runner",
            "backtest_completed",
            "backtest",
            run_id,
            details={
                "sensor_id": result["sensor_id"],
                "monitor_id": result["monitor_id"],
                "status": result["status"],
                "sample_count": result["sample_count"],
                "degraded_sample_count": result["degraded_sample_count"],
                "caveats": result["caveats"],
            },
            reason=result["failure_reason"] or LIVE_BACKTEST_CAVEAT,
            created_at=created_at,
        )
    return {"backtest_run_id": run_id, **result}


def run_sensor_monitor_backtest(
    repository: Repository,
    sensor_id: str,
    monitor_id: str,
    *,
    window_days: int = 3,
    max_gap_minutes: float = 180.0,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Run the reproducible live-data backtest for one sensor/monitor pair."""
    sensor = repository.read_sensor(sensor_id)
    if not sensor:
        raise RuntimeError(f"Sensor is not present in the selected repository: {sensor_id}")
    monitor = repository.one("SELECT * FROM monitors WHERE monitor_id = ?", (monitor_id,))
    if not monitor:
        raise RuntimeError(f"Monitor is not present in the selected repository: {monitor_id}")
    end = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    start = end - timedelta(days=window_days)
    sensor_rows = repository.many(
        "SELECT * FROM sensor_readings WHERE sensor_id = ? AND observed_at >= ? AND observed_at <= ? ORDER BY observed_at",
        (sensor_id, start, end),
    )
    sensor_rows = [
        {
            **row,
            "sensor_id": sensor_id,
            "likely_indoor": sensor.get("likely_indoor", sensor.get("indoor_flag", False)),
        }
        for row in sensor_rows
    ]
    monitor_rows = [dict(monitor)]
    if repository.backend == "sqlite":
        monitor_history = repository.many(
            "SELECT monitor_id, observed_at, aqi AS latest_aqi FROM monitor_readings WHERE monitor_id = ? AND observed_at >= ? AND observed_at <= ? ORDER BY observed_at",
            (monitor_id, start, end),
        )
        if monitor_history:
            monitor_rows = monitor_history
    result = compute_sensor_monitor_backtest(
        sensor_id,
        monitor_id,
        sensor_rows,
        monitor_rows,
        window_start=start,
        window_end=end,
        max_gap_minutes=max_gap_minutes,
    )
    result["data_source"] = (
        "SQLite fixture history" if repository.backend == "sqlite"
        else "CockroachDB normalized PurpleAir readings + AirNow monitor snapshot"
    )
    return _persist_sensor_monitor_backtest(repository, result)


def format_sensor_monitor_backtest(result: dict[str, Any]) -> str:
    labels = {
        "raw_purpleair": "Raw PurpleAir MAE",
        "static_correction": "Static correction MAE",
        "aircord": "Aircord MAE",
    }
    summaries = {(row["segment"], row["method"]): row for row in result.get("summaries", [])}
    lines = [
        "Aircord backtest",
        f"status: {result['status']} / claim_status={result['claim_status']}",
        f"data source: {result.get('data_source', 'fixture')}",
        f"sensor: {result['sensor_id']} monitor: {result['monitor_id']}",
        f"time range: {result['window_start']} to {result['window_end']}",
        f"sample count: {result['sample_count']} (aligned={result.get('aligned_count', result['sample_count'])})",
    ]
    for method in METHODS:
        summary = summaries.get(("all", method))
        if summary:
            lines.append(f"{labels[method]}: {summary['mean_absolute_error']} (n={summary['observation_count']})")
        else:
            lines.append(f"{labels[method]}: insufficient data (need at least {MIN_METRIC_SAMPLES} valid samples)")
    lines.append(f"degraded sample count: {result['degraded_sample_count']}")
    for method in METHODS:
        summary = summaries.get(("degraded", method))
        if summary:
            lines.append(f"degraded {labels[method]}: {summary['mean_absolute_error']} (n={summary['observation_count']})")
        else:
            lines.append(f"degraded {labels[method]}: insufficient data")
    if result.get("failure_reason"):
        lines.append(f"result caveat: {result['failure_reason']}")
    lines.append("caveats:")
    lines.extend(f"- {caveat}" for caveat in result.get("caveats", []))
    return "\n".join(lines)


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
    parser.add_argument("--window-days", type=int, default=3)
    parser.add_argument("--sensor-id")
    parser.add_argument("--monitor-id")
    parser.add_argument("--max-gap-minutes", type=float, default=180.0)
    args = parser.parse_args()
    if bool(args.sensor_id) != bool(args.monitor_id):
        parser.error("--sensor-id and --monitor-id must be provided together")
    if args.sensor_id and args.monitor_id:
        repository = Repository(backend="cockroach" if database_url_configured() else "sqlite")
        result = run_sensor_monitor_backtest(
            repository,
            args.sensor_id,
            args.monitor_id,
            window_days=args.window_days,
            max_gap_minutes=args.max_gap_minutes,
        )
        print(format_sensor_monitor_backtest(result))
        return
    print(run_backtest(DB_PATH, args.cluster))


if __name__ == "__main__":
    main()
