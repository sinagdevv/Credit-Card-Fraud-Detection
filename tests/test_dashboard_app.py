from pathlib import Path

import json

import pandas as pd

from streamlit.testing.v1 import AppTest


def test_dashboard_empty_state_smoke():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "dashboard" / "app.py"))
    app.run(timeout=30)
    assert not app.exception
    assert [title.value for title in app.title] == ["Fraud Intelligence"]


def test_dashboard_overview_smoke(tmp_path, monkeypatch):
    run = tmp_path / "run_1_test"; run.mkdir()
    tables = {
        "cardholders": {"cardholder_id": ["h1"]},
        "cards": {"card_id": ["c1"], "cardholder_id": ["h1"], "product_tier": ["gold"]},
        "merchants": {"merchant_id": ["m1"], "merchant_category": ["retail"], "country_code": ["PH"], "merchant_region": ["NCR"]},
        "transactions": {"transaction_id": ["t1"], "card_id": ["c1"], "merchant_id": ["m1"], "transaction_ts": ["2026-01-01T10:00:00"], "amount_php": [100.0], "channel": ["ecommerce"], "foreign_transaction": [False], "device_trust_level": ["trusted"], "tx_count_prev_1h": [0], "spend_deviation_z": [0.0], "distance_from_home_km": [1.0], "amount_sum_prev_24h_php": [100.0]},
        "fraud_labels": {"transaction_id": ["t1"], "observed_fraud": [True], "review_status": ["confirmed"], "label_source": ["analyst"], "alert_ts": ["2026-01-01T23:59:59"], "review_ts": ["2026-01-02T01:00:00"]},
    }
    for name, data in tables.items():
        pd.DataFrame(data).to_csv(run / f"{name}.csv", index=False)
    (run / "manifest.json").write_text(json.dumps({"seed": 1, "config_sha256": "test"}))
    monkeypatch.setenv("SD008_DATA_DIR", str(run))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "dashboard" / "app.py"))
    app.run(timeout=30)
    assert not app.exception
    assert [title.value for title in app.title] == ["Fraud Intelligence"]
