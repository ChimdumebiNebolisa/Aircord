from aircord.backtest.run import run_backtest


def test_gate_b_compares_three_methods_and_degraded_segment(demo_db):
    result = run_backtest(demo_db)
    assert result["status"] == "passed"
    assert result["claim_status"] == "measured"
    methods = {row["method"] for row in result["summaries"] if row["segment"] == "degraded"}
    assert methods == {"raw_purpleair", "static_correction", "aircord"}
    errors = {row["method"]: row["mean_absolute_error"] for row in result["summaries"] if row["segment"] == "degraded"}
    assert errors["aircord"] < errors["static_correction"]

