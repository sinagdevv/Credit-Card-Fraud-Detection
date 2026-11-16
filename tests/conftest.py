import copy
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

D2 = Path(__file__).resolve().parents[1] / "deliverables/D2_Synthetic_Dataset_Generator"
sys.path.insert(0, str(D2))
CFG_PATH = D2 / "config/scenario_v0.yaml"


@pytest.fixture(scope="session")
def real_cfg():
    return yaml.safe_load(CFG_PATH.read_text())


@pytest.fixture
def small_cfg(real_cfg):
    cfg = copy.deepcopy(real_cfg)
    cfg["simulation"]["n_cardholders"] = 200
    cfg["simulation"]["n_merchants"] = 50
    return cfg


@pytest.fixture
def internal(real_cfg):
    """Tiny valid internal dataset (1 holder, 1 card, 2 merchants, 5 tx on one card, 3 labels)."""
    ch = pd.DataFrame({"cardholder_id": ["h1"], "age_band": ["25-34"], "income_band": ["lt_15k"],
                       "home_region": ["NCR"], "urbanicity": ["urban"],
                       "account_open_date": pd.to_datetime(["2020-01-01"]),
                       "employment_segment": ["self_employed"], "latent_s": [0.3]})
    cd = pd.DataFrame({"card_id": ["c1"], "cardholder_id": ["h1"], "card_brand": ["brand_a"],
                       "issue_date": pd.to_datetime(["2025-01-01"]),
                       "expiry_date": pd.to_datetime(["2029-01-01"]), "credit_limit_php": [50000.0],
                       "card_status": ["active"], "product_tier": ["gold"]})
    me = pd.DataFrame({"merchant_id": ["m1", "m2"], "merchant_category": ["grocery", "airline"],
                       "mcc": ["5411", "4511"], "country_code": ["PH", "US"],
                       "merchant_region": ["NCR", "US_West"], "merchant_size_band": ["small", "large"],
                       "online_capable": [False, True], "latent_merchant_vulnerability": [.1, .2]})
    ts = pd.to_datetime(["2026-02-01 10:00:00", "2026-02-01 10:30:00", "2026-02-01 12:00:00",
                         "2026-02-02 09:00:00", "2026-02-02 09:20:00"])
    amt = [100., 250., 80., 1000., 40.]
    ap = ["approved", "declined", "approved", "approved", "approved"]
    rows = []
    for k in range(5):
        pr = list(range(k))
        cnt = sum(ts[k] - pd.Timedelta("1h") < ts[j] for j in pr)
        sm = sum(amt[j] for j in pr if ap[j] == "approved" and ts[k] - pd.Timedelta("24h") < ts[j])
        h = (ts[k] - ts[pr[-1]]).total_seconds() / 3600 if pr else np.nan
        z = np.nan
        if len(pr) >= 3:
            L = [math.log(amt[j]) for j in pr]
            z = float(np.clip((math.log(amt[k]) - np.mean(L)) / max(np.std(L), .25), -10, 10))
        rows.append((cnt, sm, z, h))
    tx = pd.DataFrame({
        "transaction_id": [f"t{k}" for k in range(5)], "card_id": "c1",
        "merchant_id": ["m1", "m2", "m1", "m2", "m1"], "transaction_ts": ts, "amount_php": amt,
        "channel": ["POS", "ecommerce", "POS", "mail-phone", "contactless"],
        "foreign_transaction": [False, True, False, True, False], "authorization_status": ap,
        "entry_mode": ["chip", "tokenized", "chip", "manual", "contactless"],
        "device_trust_level": "trusted", "distance_from_home_km": [1., np.nan, 2., np.nan, 3.],
        "tx_count_prev_1h": [r[0] for r in rows], "amount_sum_prev_24h_php": [r[1] for r in rows],
        "spend_deviation_z": [r[2] for r in rows], "local_hour_sin": 0.0, "local_hour_cos": 1.0,
        "hours_since_prev_tx": [r[3] for r in rows],
        "y_true": [False, True, False, False, True], "r_investigated": [False, True, False, True, True],
        "mechanism": "none"})
    fl = pd.DataFrame({
        "transaction_id": ["t1", "t3", "t4"],
        "observed_fraud": pd.array([True, False, None], dtype="boolean"),
        "review_status": ["confirmed", "cleared", "pending"], "fraud_type": ["cnp", None, None],
        "alert_ts": pd.to_datetime(["2026-02-01 23:59:59", "2026-02-02 23:59:59", "2026-02-02 23:59:59"]),
        "review_ts": pd.to_datetime(["2026-02-03 10:00:00", "2026-02-04 10:00:00", pd.NaT]),
        "label_source": "analyst"})
    return dict(cardholders=ch, cards=cd, merchants=me, transactions=tx, fraud_labels=fl)
