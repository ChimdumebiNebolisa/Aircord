from aircord.backtest.run import run_backtest


def test_measured_claim_is_only_emitted_after_alignment(demo_db):
    result = run_backtest(demo_db)
    assert result["status"] == "passed"
    assert result["claim_status"] == "measured"
    assert all(summary["observation_count"] > 0 for summary in result["summaries"])

