from datetime import datetime, timedelta, timezone

from aircord.backtest.alignment import align_sensor_monitor_rows
from aircord.backtest.metrics import absolute_errors, summarize_errors
from aircord.backtest.run import compute_sensor_monitor_backtest


BASE = datetime(2026, 8, 4, 22, 0, tzinfo=timezone.utc)


def test_sensor_monitor_alignment_uses_nearest_timestamp_and_deduplicates():
    sensor_rows = [
        {"sensor_id": "54917", "reading_id": "r1", "observed_at": "2026-08-04T21:10:00Z"},
        {"sensor_id": "54917", "reading_id": "duplicate", "observed_at": "2026-08-04T21:10:00Z"},
        {"sensor_id": "54917", "reading_id": "too-far", "observed_at": "2026-08-04T18:00:00Z"},
    ]
    monitor_rows = [
        {"monitor_id": "m1", "observed_at": "2026-08-04T21:00:00Z", "latest_aqi": 64.0},
        {"monitor_id": "m1", "observed_at": "2026-08-04T21:30:00Z", "latest_aqi": 70.0},
    ]

    aligned = align_sensor_monitor_rows(sensor_rows, monitor_rows, max_gap_minutes=30)

    assert len(aligned) == 1
    assert aligned[0]["reading_id"] == "r1"
    assert aligned[0]["reference_aqi"] == 64.0
    assert aligned[0]["time_gap_minutes"] == 10.0


def test_mae_is_deterministic_and_small_samples_emit_no_metric():
    assert absolute_errors([10.0, 20.0], [8.0, 25.0]) == [2.0, 5.0]
    small = summarize_errors([2.0, 5.0])
    enough = summarize_errors([2.0, 5.0, 1.0])

    assert small["observation_count"] == 2
    assert small["mean_absolute_error"] is None
    assert enough["mean_absolute_error"] == 2.67
    assert enough["median_absolute_error"] == 2.0


def test_backtest_filters_degraded_subset_and_keeps_zero_as_real_sensor_value():
    sensor_rows = [
        {"sensor_id": "54917", "reading_id": "r1", "observed_at": BASE - timedelta(minutes=30), "pm25_cf1": 0.0, "pm25_atm": 0.0, "channel_a": 0.0, "channel_b": 1.0},
        {"sensor_id": "54917", "reading_id": "r2", "observed_at": BASE - timedelta(minutes=20), "pm25_cf1": 0.0, "pm25_atm": 0.0, "channel_a": 0.0, "channel_b": 1.2},
        {"sensor_id": "54917", "reading_id": "r3", "observed_at": BASE - timedelta(minutes=10), "pm25_cf1": 0.0, "pm25_atm": 0.0, "channel_a": 0.0, "channel_b": 1.4},
    ]
    monitor_rows = [{"monitor_id": "060371302", "observed_at": BASE - timedelta(minutes=40), "latest_aqi": 64.0}]

    result = compute_sensor_monitor_backtest(
        "54917",
        "060371302",
        sensor_rows,
        monitor_rows,
        window_start=BASE - timedelta(hours=1),
        window_end=BASE,
    )

    summaries = {(row["segment"], row["method"]): row for row in result["summaries"]}
    assert result["status"] == "passed"
    assert result["sample_count"] == 3
    assert result["degraded_sample_count"] == 3
    assert summaries[("all", "raw_purpleair")]["mean_absolute_error"] == 64.0
    assert summaries[("all", "aircord")]["mean_absolute_error"] > 0.0
    assert ("degraded", "aircord") in summaries


def test_missing_pm_does_not_default_to_zero_or_emit_a_metric():
    sensor_rows = [
        {"sensor_id": "54917", "reading_id": "r1", "observed_at": BASE - timedelta(minutes=20), "pm25_cf1": None, "pm25_atm": None, "channel_a": None, "channel_b": None},
        {"sensor_id": "54917", "reading_id": "r2", "observed_at": BASE - timedelta(minutes=10), "pm25_cf1": 12.0, "pm25_atm": 12.0, "channel_a": 12.0, "channel_b": 12.0},
    ]
    monitor_rows = [{"monitor_id": "060371302", "observed_at": BASE - timedelta(minutes=30), "latest_aqi": 64.0}]

    result = compute_sensor_monitor_backtest(
        "54917",
        "060371302",
        sensor_rows,
        monitor_rows,
        window_start=BASE - timedelta(hours=1),
        window_end=BASE,
    )

    assert result["status"] == "insufficient_data"
    assert result["sample_count"] == 1
    assert result["summaries"] == []
    assert any("Excluded 1" in caveat for caveat in result["caveats"])
