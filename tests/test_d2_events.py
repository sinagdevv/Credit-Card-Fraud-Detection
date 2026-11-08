import copy
import math

import numpy as np
import pandas as pd
import pytest

from sd008_gen import export as ex
from sd008_gen import validate as val
from sd008_gen.config import rng_streams
from sd008_gen.entities import make_entities
from sd008_gen.events import simulate_events

TX = ex.ALLOWLIST["transactions"]


def _run(real_cfg, seed=None):
    cfg = copy.deepcopy(real_cfg)
    cfg["simulation"].update(n_cardholders=200, n_merchants=50, end_date="2026-03-31")  # 90 d > 60 d pilot
    if seed is not None:
        cfg["simulation"]["seed"] = seed
    s = rng_streams(cfg["simulation"]["seed"])
    ent = make_entities(cfg, s["entities"])
    tx, info = simulate_events(cfg, ent, s)
    return cfg, ent, tx, info


@pytest.fixture(scope="module")
def sim(real_cfg):
    return _run(real_cfg)


def test_columns(sim):
    _, _, tx, _ = sim
    internal = [c for c in tx.columns if c not in TX]
    assert list(tx.columns[:len(TX)]) == TX
    assert {"y_true", "mechanism"} <= set(internal)
    assert all(c in ("y_true", "mechanism") or c.startswith("latent_") for c in internal)
    assert not set(internal) & set(TX)


def test_order_and_unique_ids(sim):
    _, _, tx, _ = sim
    assert len(tx) > 0
    assert tx["transaction_id"].is_unique
    key = list(zip(tx["transaction_ts"], tx["transaction_id"]))
    assert key == sorted(key)


def test_card_time_constraints(sim):
    cfg, ent, tx, _ = sim
    assert not tx.duplicated(["card_id", "transaction_ts"]).any()
    exp = tx["card_id"].map(ent["cards"].set_index("card_id")["expiry_date"])
    assert (tx["transaction_ts"] < exp).all()
    lo = pd.Timestamp(cfg["simulation"]["start_date"])
    hi = pd.Timestamp(cfg["simulation"]["end_date"]) + pd.Timedelta(days=1)
    assert tx["transaction_ts"].between(lo, hi, inclusive="left").all()


def test_merchant_channel_consistency(sim):
    _, ent, tx, _ = sim
    m = tx.merge(ent["merchants"], on="merchant_id", how="left")
    assert m["country_code"].notna().all()
    assert (m["foreign_transaction"].to_numpy() == (m["country_code"] != "PH").to_numpy()).all()
    cnp = tx["channel"].isin(["ecommerce", "mail-phone"])
    assert (tx["distance_from_home_km"].isna() == cnp).all()
    ecom = tx["channel"] == "ecommerce"
    assert tx.loc[ecom, "entry_mode"].isin(["tokenized", "manual"]).all()
    assert not tx.loc[~ecom, "entry_mode"].isin(["tokenized"]).any()
    assert tx.groupby("channel")["entry_mode"].nunique().drop("ecommerce", errors="ignore").max() == 1


def test_negative_foreign_check_catches_bug(sim):
    _, ent, tx, _ = sim
    bad = tx.copy()
    bad["foreign_transaction"] = ~bad["foreign_transaction"]
    m = bad.merge(ent["merchants"], on="merchant_id")
    assert not (m["foreign_transaction"].to_numpy() == (m["country_code"] != "PH").to_numpy()).all()


def _tables(ent, tx):
    t = {k: ent[k][ex.ALLOWLIST[k]] for k in ("cardholders", "cards", "merchants")}
    t["transactions"] = tx[TX]
    t["fraud_labels"] = pd.DataFrame(columns=ex.ALLOWLIST["fraud_labels"])
    return t


def test_rolling_features(sim):
    cfg, ent, tx, _ = sim
    assert val.check_rolling_features(_tables(ent, tx), cfg) == []
    bad = tx.copy()
    bad.loc[bad.index[-1], "tx_count_prev_1h"] += 1
    assert val.check_rolling_features(_tables(ent, bad), cfg) != []  # the check can fail


def test_declined_not_in_24h_sum(sim):
    _, _, tx, _ = sim
    for _, g in tx.groupby("card_id"):
        g = g.reset_index(drop=True)
        for i in np.flatnonzero((g["authorization_status"] == "declined").to_numpy()):
            later = g[(g["transaction_ts"] > g.loc[i, "transaction_ts"])
                      & (g["transaction_ts"] <= g.loc[i, "transaction_ts"] + pd.Timedelta(hours=24))]
            if len(later):
                j = later.index[0]
                prior = g[(g["transaction_ts"] < g.loc[j, "transaction_ts"])
                          & (g["transaction_ts"] > g.loc[j, "transaction_ts"] - pd.Timedelta(hours=24))
                          & (g["authorization_status"] == "approved")]
                assert math.isclose(g.loc[j, "amount_sum_prev_24h_php"], prior["amount_php"].sum(), abs_tol=0.01)
                return
    pytest.skip("no declined row followed by another within 24h")


def test_fraud_requires_mechanism(sim):
    # pending builder change if this fails: y_true must be False when mechanism == "none"
    _, _, tx, _ = sim
    assert not (tx["y_true"] & (tx["mechanism"] == "none")).any()


def test_burst_rows_all_fraud(sim):
    _, _, tx, _ = sim
    b = tx[tx["mechanism"] == "burst"]
    assert b["y_true"].all()


def test_beta0(sim):
    _, _, _, info = sim
    assert "beta0" in info and math.isfinite(info["beta0"]) and -30 <= info["beta0"] <= 5


def test_fraud_rate_band(sim):
    cfg, _, tx, _ = sim
    r_f = cfg["parameters"]["underlying_fraud_target"]["value"]
    # small sample (200 holders, 90 d) plus burst expansion and discards: only a loose band is meaningful
    assert 0.3 * r_f <= tx["y_true"].mean() <= 3 * r_f


def test_determinism(real_cfg, sim):
    _, _, tx, _ = sim
    _, _, tx2, _ = _run(real_cfg)
    assert tx.equals(tx2)
    _, _, tx3, _ = _run(real_cfg, seed=sim[0]["simulation"]["seed"] + 1)
    assert not tx.equals(tx3)


def test_no_prohibited_exported_columns(sim):
    _, _, tx, _ = sim
    assert ex.prohibited_columns({"transactions": tx[TX]}) == []
    assert ex.prohibited_columns({"transactions": tx}) != []  # internal columns are caught
