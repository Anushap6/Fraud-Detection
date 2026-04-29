import pytest
from risk_rules import label_risk, score_transaction


# Baseline transaction: every signal below its lowest threshold → score must be 0.
BASE_TX = {
    "device_risk_score": 10,
    "is_international": 0,
    "amount_usd": 100,
    "velocity_24h": 1,
    "failed_logins_24h": 0,
    "prior_chargebacks": 0,
}


# ---------------------------------------------------------------------------
# label_risk — boundary values
# ---------------------------------------------------------------------------

def test_label_risk_low_below_boundary():
    assert label_risk(0) == "low"
    assert label_risk(29) == "low"


def test_label_risk_medium_at_and_above_boundary():
    assert label_risk(30) == "medium"
    assert label_risk(59) == "medium"


def test_label_risk_high_at_and_above_boundary():
    assert label_risk(60) == "high"
    assert label_risk(100) == "high"


# ---------------------------------------------------------------------------
# score_transaction — baseline and bounds
# ---------------------------------------------------------------------------

def test_clean_transaction_scores_zero():
    assert score_transaction(BASE_TX) == 0


def test_score_capped_at_100():
    maxed = {
        "device_risk_score": 85,
        "is_international": 1,
        "amount_usd": 1500,
        "velocity_24h": 10,
        "failed_logins_24h": 8,
        "prior_chargebacks": 3,
    }
    # Raw sum: 25+15+25+20+20+20 = 125; must clamp to 100.
    assert score_transaction(maxed) == 100


# ---------------------------------------------------------------------------
# device_risk_score — both tiers
# ---------------------------------------------------------------------------

def test_device_risk_high_tier_adds_25():
    assert score_transaction({**BASE_TX, "device_risk_score": 75}) == 25


def test_device_risk_mid_tier_adds_10():
    assert score_transaction({**BASE_TX, "device_risk_score": 50}) == 10


def test_device_risk_below_threshold_adds_nothing():
    assert score_transaction({**BASE_TX, "device_risk_score": 39}) == 0


# ---------------------------------------------------------------------------
# is_international
# ---------------------------------------------------------------------------

def test_international_adds_15():
    assert score_transaction({**BASE_TX, "is_international": 1}) == 15


def test_domestic_adds_nothing():
    assert score_transaction({**BASE_TX, "is_international": 0}) == 0


# ---------------------------------------------------------------------------
# amount_usd — both tiers
# ---------------------------------------------------------------------------

def test_amount_large_tier_adds_25():
    assert score_transaction({**BASE_TX, "amount_usd": 1000}) == 25


def test_amount_mid_tier_adds_10():
    assert score_transaction({**BASE_TX, "amount_usd": 500}) == 10


def test_amount_below_threshold_adds_nothing():
    assert score_transaction({**BASE_TX, "amount_usd": 499}) == 0


# ---------------------------------------------------------------------------
# velocity_24h — both tiers
# ---------------------------------------------------------------------------

def test_velocity_high_tier_adds_20():
    assert score_transaction({**BASE_TX, "velocity_24h": 8}) == 20


def test_velocity_mid_tier_adds_5():
    assert score_transaction({**BASE_TX, "velocity_24h": 4}) == 5


def test_velocity_below_threshold_adds_nothing():
    assert score_transaction({**BASE_TX, "velocity_24h": 2}) == 0


# ---------------------------------------------------------------------------
# failed_logins_24h — both tiers (previously untested)
# ---------------------------------------------------------------------------

def test_failed_logins_high_tier_adds_20():
    assert score_transaction({**BASE_TX, "failed_logins_24h": 5}) == 20


def test_failed_logins_mid_tier_adds_10():
    assert score_transaction({**BASE_TX, "failed_logins_24h": 3}) == 10


def test_failed_logins_below_threshold_adds_nothing():
    assert score_transaction({**BASE_TX, "failed_logins_24h": 1}) == 0


# ---------------------------------------------------------------------------
# prior_chargebacks — both tiers
# ---------------------------------------------------------------------------

def test_prior_chargebacks_multi_adds_20():
    assert score_transaction({**BASE_TX, "prior_chargebacks": 2}) == 20


def test_prior_chargebacks_one_adds_5():
    assert score_transaction({**BASE_TX, "prior_chargebacks": 1}) == 5


def test_prior_chargebacks_none_adds_nothing():
    assert score_transaction({**BASE_TX, "prior_chargebacks": 0}) == 0
