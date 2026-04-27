from risk_rules import label_risk, score_transaction


BASE_TX = {
    "device_risk_score": 10,
    "is_international": 0,
    "amount_usd": 100,
    "velocity_24h": 1,
    "failed_logins_24h": 0,
    "prior_chargebacks": 0,
}


def test_label_risk_thresholds():
    assert label_risk(10) == "low"
    assert label_risk(35) == "medium"
    assert label_risk(75) == "high"


def test_large_amount_adds_risk():
    tx = {**BASE_TX, "amount_usd": 1200}
    assert score_transaction(tx) >= 25


def test_high_device_risk_adds_risk():
    low_device = score_transaction({**BASE_TX, "device_risk_score": 10})
    high_device = score_transaction({**BASE_TX, "device_risk_score": 75})
    assert high_device > low_device


def test_international_adds_risk():
    domestic = score_transaction({**BASE_TX, "is_international": 0})
    international = score_transaction({**BASE_TX, "is_international": 1})
    assert international > domestic


def test_high_velocity_adds_risk():
    low_velocity = score_transaction({**BASE_TX, "velocity_24h": 1})
    high_velocity = score_transaction({**BASE_TX, "velocity_24h": 8})
    assert high_velocity > low_velocity


def test_prior_chargebacks_add_risk():
    no_cb = score_transaction({**BASE_TX, "prior_chargebacks": 0})
    one_cb = score_transaction({**BASE_TX, "prior_chargebacks": 1})
    multi_cb = score_transaction({**BASE_TX, "prior_chargebacks": 3})
    assert one_cb > no_cb
    assert multi_cb > one_cb
