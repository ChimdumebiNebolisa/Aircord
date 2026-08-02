from aircord.db.repositories import Repository
from aircord.reconciliation.comparison import compare_cell
from aircord.reconciliation.run_once import reconcile_cluster


def test_reconciliation_commits_memory_and_audit_atomically(demo_db):
    reconcile_cluster(demo_db)
    repository = Repository(demo_db)
    estimate_count = repository.one("SELECT COUNT(*) AS count FROM estimates")["count"]
    resolution_count = repository.one("SELECT COUNT(*) AS count FROM resolutions")["count"]
    audit_count = repository.one("SELECT COUNT(*) AS count FROM audit_log")["count"]
    decisions = repository.many("SELECT decision FROM resolution_sensors")
    assert estimate_count == 3
    assert resolution_count == 3
    assert audit_count >= 6
    assert {row["decision"] for row in decisions} >= {"downweighted", "ignored"}
    comparison = compare_cell(demo_db, "cell-culver")
    assert comparison["aircord_estimate"] != comparison["static_correction_estimate"]

