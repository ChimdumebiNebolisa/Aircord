from aircord.db.repositories import Repository
from aircord.reconciliation.comparison import compare_cell
from aircord.reconciliation.run_once import reconcile_cluster


def test_degraded_sensor_changes_estimate(demo_db):
    before = compare_cell(demo_db, "cell-culver")
    reconcile_cluster(demo_db)
    after = compare_cell(demo_db, "cell-culver")
    detail = Repository(demo_db).many("SELECT decision FROM resolution_sensors WHERE resolution_id = (SELECT resolution_id FROM resolutions WHERE cell_id = 'cell-culver' LIMIT 1)")
    assert before["raw_estimate"] != before["aircord_estimate"]
    assert after["aircord_estimate"] != before["static_correction_estimate"]
    assert "downweighted" in {row["decision"] for row in detail}

