import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dashboard.services.data import analyst_transactions, assert_no_internal_columns, kpis, load_dataset, scenario_evidence


def frames():
    return {"cardholders": pd.DataFrame({"cardholder_id":["h1"]}), "cards": pd.DataFrame({"card_id":["c1"], "cardholder_id":["h1"], "product_tier":["gold"]}), "merchants": pd.DataFrame({"merchant_id":["m1"], "merchant_category":["retail"], "country_code":["PH"], "merchant_region":["NCR"]}), "transactions": pd.DataFrame({"transaction_id":["t1"], "card_id":["c1"], "merchant_id":["m1"], "transaction_ts":[pd.Timestamp("2026-01-01")], "amount_php":[100.0], "channel":["ecommerce"], "foreign_transaction":[False], "device_trust_level":["trusted"], "tx_count_prev_1h":[0], "spend_deviation_z":[0.], "distance_from_home_km":[1.], "amount_sum_prev_24h_php":[100.]}), "fraud_labels": pd.DataFrame({"transaction_id":["t1"], "observed_fraud":[True], "review_status":["confirmed"], "label_source":["analyst"]})}


def test_analyst_join_and_kpis_are_observed_only():
    f = frames(); tx = analyst_transactions(f); result = kpis(tx, f)
    assert tx.loc[0, "label_status"] == "confirmed"
    assert result["observed_positives"] == 1 and result["review_coverage"] == 1


def test_internal_columns_are_rejected():
    f = frames(); f["transactions"]["y_true"] = True
    with pytest.raises(ValueError, match="Internal"):
        assert_no_internal_columns(f)


def test_load_requires_all_five_tables(tmp_path):
    (tmp_path / "manifest.json").write_text(json.dumps({}))
    with pytest.raises(FileNotFoundError):
        load_dataset(tmp_path)


def test_scenario_evidence_uses_versioned_artifact():
    root = Path(__file__).resolve().parents[1]
    evidence = scenario_evidence(root)
    assert evidence.loc[evidence.Scenario.eq("STRICT_REVIEW_BUDGET"), "Investigations"].item() == 772
