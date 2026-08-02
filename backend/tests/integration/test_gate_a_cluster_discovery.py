from aircord.ingestion.discover_cluster import discover


def test_gate_a_fixture_reports_paired_anchors(demo_db, monkeypatch):
    import aircord.ingestion.discover_cluster as module

    monkeypatch.setattr(module, "DB_PATH", demo_db)
    result = discover("greater-la")
    assert result["gate_a_status"] == "passed"
    assert result["paired_anchor_count"] >= 3
    assert "Live Gate A" in result["notes"]

