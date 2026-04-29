import pandas as pd
import pytest

from analyze_fraud import summarize_results
from features import build_model_frame


# ---------------------------------------------------------------------------
# build_model_frame
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_transactions():
    return pd.DataFrame([
        {"transaction_id": 1, "account_id": 10, "amount_usd": 1200.0, "failed_logins_24h": 0},
        {"transaction_id": 2, "account_id": 10, "amount_usd": 400.0,  "failed_logins_24h": 1},
        {"transaction_id": 3, "account_id": 10, "amount_usd": 400.0,  "failed_logins_24h": 3},
    ])


@pytest.fixture
def sample_accounts():
    return pd.DataFrame([{"account_id": 10, "prior_chargebacks": 2}])


def test_build_model_frame_merges_prior_chargebacks(sample_transactions, sample_accounts):
    mf = build_model_frame(sample_transactions, sample_accounts)
    assert list(mf["prior_chargebacks"]) == [2, 2, 2]


def test_build_model_frame_is_large_amount(sample_transactions, sample_accounts):
    mf = build_model_frame(sample_transactions, sample_accounts)
    # txn 1: 1200 >= 1000 → 1; txns 2,3: 400 < 1000 → 0
    assert list(mf["is_large_amount"]) == [1, 0, 0]


def test_build_model_frame_login_pressure(sample_transactions, sample_accounts):
    mf = build_model_frame(sample_transactions, sample_accounts)
    # failed_logins_24h: 0 → none, 1 → low (bin (0,2]), 3 → high (bin (2,100])
    assert list(mf["login_pressure"]) == ["none", "low", "high"]


def test_build_model_frame_unknown_account_produces_null(sample_accounts):
    txns = pd.DataFrame([{"transaction_id": 99, "account_id": 999, "amount_usd": 100.0, "failed_logins_24h": 0}])
    mf = build_model_frame(txns, sample_accounts)
    assert pd.isna(mf.loc[0, "prior_chargebacks"])


# ---------------------------------------------------------------------------
# summarize_results
# ---------------------------------------------------------------------------

@pytest.fixture
def scored_df():
    return pd.DataFrame([
        {"transaction_id": 1, "risk_label": "high",   "amount_usd": 500.0},
        {"transaction_id": 2, "risk_label": "high",   "amount_usd": 300.0},
        {"transaction_id": 3, "risk_label": "medium", "amount_usd": 200.0},
        {"transaction_id": 4, "risk_label": "low",    "amount_usd": 50.0},
    ])


@pytest.fixture
def chargebacks_df():
    # Only txn 1 is a confirmed chargeback
    return pd.DataFrame([{"transaction_id": 1, "loss_amount_usd": 500.0}])


def test_summarize_transaction_counts(scored_df, chargebacks_df):
    result = summarize_results(scored_df, chargebacks_df).set_index("risk_label")
    assert result.loc["high", "transactions"] == 2
    assert result.loc["medium", "transactions"] == 1
    assert result.loc["low", "transactions"] == 1


def test_summarize_total_amount(scored_df, chargebacks_df):
    result = summarize_results(scored_df, chargebacks_df).set_index("risk_label")
    assert result.loc["high", "total_amount_usd"] == pytest.approx(800.0)
    assert result.loc["medium", "total_amount_usd"] == pytest.approx(200.0)


def test_summarize_avg_amount(scored_df, chargebacks_df):
    result = summarize_results(scored_df, chargebacks_df).set_index("risk_label")
    assert result.loc["high", "avg_amount_usd"] == pytest.approx(400.0)


def test_summarize_chargeback_count(scored_df, chargebacks_df):
    result = summarize_results(scored_df, chargebacks_df).set_index("risk_label")
    assert result.loc["high", "chargebacks"] == 1
    assert result.loc["medium", "chargebacks"] == 0
    assert result.loc["low", "chargebacks"] == 0


def test_summarize_chargeback_rate(scored_df, chargebacks_df):
    result = summarize_results(scored_df, chargebacks_df).set_index("risk_label")
    # 1 chargeback out of 2 high-risk transactions
    assert result.loc["high", "chargeback_rate"] == pytest.approx(0.5)
    assert result.loc["medium", "chargeback_rate"] == pytest.approx(0.0)
    assert result.loc["low", "chargeback_rate"] == pytest.approx(0.0)


def test_summarize_no_chargebacks_gives_zero_rate(scored_df):
    no_cb = pd.DataFrame(columns=["transaction_id", "loss_amount_usd"])
    result = summarize_results(scored_df, no_cb).set_index("risk_label")
    assert result["chargeback_rate"].sum() == pytest.approx(0.0)
