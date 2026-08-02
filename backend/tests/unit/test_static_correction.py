from aircord.reconciliation.methods import raw_estimate, static_correction_estimate, trust_weighted_estimate


def test_methods_are_deterministic_and_comparable():
    values = [100, 120, 140]
    assert raw_estimate(values) == 120
    assert static_correction_estimate(values) == 90
    assert trust_weighted_estimate([(100, 1), (140, 0)]) == 100

