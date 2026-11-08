"""Spec 8.1 validation checks. Each check_x(tables, cfg) -> list of problems; works on exported tables only."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .export import ALLOWLIST, non_key_features, prohibited_columns

TOL = 1e-6
SD_DDOF = 0  # running SD of prior log amounts: population SD. Spec says only "running SD" (ambiguous).
NULLABLE = {"distance_from_home_km", "spend_deviation_z", "hours_since_prev_tx", "observed_fraud",
            "fraud_type", "alert_ts", "review_ts"}  # 9 nullable; device_trust_level is non-null in v0 (8)
PKS = {"cardholders": "cardholder_id", "cards": "card_id", "merchants": "merchant_id",
       "transactions": "transaction_id", "fraud_labels": "transaction_id"}
FKS = [("cards", "cardholder_id", "cardholders"), ("transactions", "card_id", "cards"),
       ("transactions", "merchant_id", "merchants"), ("fraud_labels", "transaction_id", "transactions")]
CATEGORICAL = {
    "cardholders": ["age_band", "income_band", "home_region", "urbanicity", "employment_segment"],
    "cards": ["card_brand", "card_status", "product_tier"],
    "merchants": ["merchant_category", "country_code", "merchant_region", "merchant_size_band"],
    "transactions": ["channel", "authorization_status", "entry_mode", "device_trust_level"],
    "fraud_labels": ["review_status", "fraud_type", "label_source"],
}


def _vocab(cfg, col):
    v = cfg["vocabularies"][col]
    if "values" in v:
        return set(v["values"])
    if "mcc" in v:
        return set(v["mcc"])
    return {r for rs in v["by_country"].values() for r in rs}


def _ts(s):
    return pd.to_datetime(s)


def _n(mask, msg):
    n = int(np.sum(mask))
    return [f"{msg}: {n} row(s)"] if n else []


def check_keys(tables, cfg):
    p = []
    for t, k in PKS.items():
        s = tables[t][k]
        p += _n(s.isna(), f"{t}.{k} null")
        p += _n(s.duplicated(), f"{t}.{k} duplicate")
    for t, col, parent in FKS:
        p += _n(~tables[t][col].isin(tables[parent][PKS[parent]]), f"{t}.{col} orphan FK -> {parent}")
    return p


def check_temporal(tables, cfg):
    p = []
    ch, cd, tx, fl = (tables[k] for k in ("cardholders", "cards", "transactions", "fraud_labels"))
    c = cd.merge(ch[["cardholder_id", "account_open_date"]], on="cardholder_id", how="left")
    p += _n(_ts(c["account_open_date"]) > _ts(c["issue_date"]), "cards: account_open_date > issue_date")
    p += _n(_ts(c["issue_date"]) >= _ts(c["expiry_date"]), "cards: issue_date >= expiry_date")
    t = tx.merge(cd[["card_id", "issue_date", "expiry_date"]], on="card_id", how="left")
    ts = _ts(t["transaction_ts"])
    p += _n(ts < _ts(t["issue_date"]), "transactions: transaction_ts < issue_date")
    p += _n(ts >= _ts(t["expiry_date"]), "transactions: transaction_ts >= expiry_date")
    f = fl.merge(tx[["transaction_id", "transaction_ts"]], on="transaction_id", how="left")
    tts, a, r = _ts(f["transaction_ts"]), _ts(f["alert_ts"]), _ts(f["review_ts"])
    p += _n(a < tts, "fraud_labels: alert_ts < transaction_ts")
    p += _n(r < a, "fraud_labels: review_ts < alert_ts")
    p += _n(r < tts, "fraud_labels: review_ts < transaction_ts (label before transaction)")
    return p


def check_vocabularies(tables, cfg):
    p = []
    for t, cols in CATEGORICAL.items():
        for c in cols:
            p += _n(~tables[t][c].dropna().isin(_vocab(cfg, c)), f"{t}.{c} outside vocabulary")
    m = tables["merchants"]
    mcc = m["merchant_category"].map(cfg["vocabularies"]["merchant_category"]["mcc"])
    p += _n(mcc.astype(str) != m["mcc"].astype(str), "merchants: mcc does not match merchant_category")
    by = cfg["vocabularies"]["merchant_region"]["by_country"]
    ok = [r in by.get(c, ()) for c, r in zip(m["country_code"], m["merchant_region"])]
    p += _n(~np.array(ok, dtype=bool), "merchants: merchant_region inconsistent with country_code")
    tx = tables["transactions"]
    allowed = {"POS": {"chip"}, "contactless": {"contactless"}, "mail-phone": {"manual"},
               "ecommerce": {"tokenized", "manual"}}
    ok = [e in allowed.get(c, ()) for c, e in zip(tx["channel"], tx["entry_mode"])]
    p += _n(~np.array(ok, dtype=bool), "transactions: entry_mode inconsistent with channel")
    t = tx.merge(m[["merchant_id", "country_code"]], on="merchant_id", how="left")
    p += _n(t["foreign_transaction"].astype(bool) != (t["country_code"] != "PH"),
            "transactions: foreign_transaction inconsistent with merchant country_code")
    return p


def check_amounts(tables, cfg):
    cap = cfg["parameters"]["amount_bounds"]["value"]["max_php"]
    a = pd.to_numeric(tables["transactions"]["amount_php"], errors="coerce")
    return (_n(~np.isfinite(a), "transactions.amount_php non-finite/missing")
            + _n(a <= 0, "transactions.amount_php <= 0") + _n(a > cap, f"transactions.amount_php > cap {cap}"))


def check_labels(tables, cfg):
    f = tables["fraud_labels"]
    o, s = f["observed_fraud"], f["review_status"]
    p = _n((s == "pending") & o.notna(), "fraud_labels: pending with non-null observed_fraud")
    p += _n((s == "confirmed") & (o.isna() | (o == False)), "fraud_labels: confirmed but observed_fraud not True")  # noqa: E712
    p += _n((s == "cleared") & (o.isna() | (o == True)), "fraud_labels: cleared but observed_fraud not False")  # noqa: E712
    p += _n(f["fraud_type"].notna() & ~(o == True), "fraud_labels: fraud_type set but observed_fraud not True")  # noqa: E712
    p += _n(f["transaction_id"].duplicated(), "fraud_labels: transaction_id duplicated")
    p += _n((f["label_source"] == "customer") != f["alert_ts"].isna(), "fraud_labels: alert_ts null iff label_source=customer violated")
    return p


def check_no_prohibited(tables, cfg):
    p = [f"prohibited column {c}" for c in prohibited_columns(tables)]
    for t, cols in ALLOWLIST.items():
        if t not in tables:
            p.append(f"missing table {t}")
        elif list(tables[t].columns) != cols:
            p.append(f"{t}: columns differ from allowlist: extra {sorted(set(tables[t].columns) - set(cols))}, "
                     f"missing {sorted(set(cols) - set(tables[t].columns))}")
    extra = set(tables) - set(ALLOWLIST)
    p += [f"unexpected table {t}" for t in sorted(extra)]
    if len(non_key_features()) != 38:
        p.append(f"allowlist has {len(non_key_features())} non-key features, expected 38")
    return p


def check_nulls(tables, cfg):
    p = []
    for t, df in tables.items():
        for c in df.columns:
            if c not in NULLABLE:
                p += _n(df[c].isna(), f"{t}.{c} null in non-nullable column")
    tx = tables["transactions"]
    online = tx["channel"].isin(["ecommerce", "mail-phone"])
    p += _n(online != tx["distance_from_home_km"].isna(),
            "transactions.distance_from_home_km null must be exactly ecommerce/mail-phone")
    return p


def check_rolling_features(tables, cfg):
    """Recompute 5.9 features per card from strictly earlier events (by transaction_ts only; ties excluded)."""
    st = cfg["parameters"]["spend_deviation_settings"]["value"]
    floor, clip, min_n = st["sigma_floor"], st["clip_abs"], st["min_prior_transactions"]
    tx = tables["transactions"].reset_index(drop=True)
    t_all = _ts(tx["transaction_ts"]).astype("datetime64[ns]").astype("int64").to_numpy()
    amt = pd.to_numeric(tx["amount_php"], errors="coerce").to_numpy(float)
    appr = (tx["authorization_status"] == "approved").to_numpy()
    H = 3_600_000_000_000
    n = len(tx)
    cnt, sm, hrs, z = np.zeros(n), np.zeros(n), np.full(n, np.nan), np.full(n, np.nan)
    for _, idx in tx.groupby("card_id", sort=False).indices.items():
        idx = idx[np.argsort(t_all[idx], kind="stable")]
        t, a = t_all[idx], amt[idx]
        lo = np.searchsorted(t, t, "left")  # events with t_j < t_k
        cnt[idx] = lo - np.searchsorted(t, t - H, "right")
        c = np.concatenate([[0.0], np.cumsum(np.where(appr[idx], a, 0.0))])
        sm[idx] = c[lo] - c[np.searchsorted(t, t - 24 * H, "right")]
        has = lo > 0
        hrs[idx[has]] = (t[has] - t[lo[has] - 1]) / H
        la = np.log(np.where(a > 0, a, np.nan))  # non-positive amounts are reported by check_amounts
        shift = la.mean() if len(la) else 0.0
        c1 = np.concatenate([[0.0], np.cumsum(la - shift)])
        c2 = np.concatenate([[0.0], np.cumsum((la - shift) ** 2)])
        k = lo.astype(float)
        enough = lo >= min_n
        kk = np.where(enough, k, 1.0)
        m = c1[lo] / kk
        var = np.maximum(c2[lo] / kk - m * m, 0.0) * (kk / np.maximum(kk - SD_DDOF, 1.0))
        zz = np.clip((la - (m + shift)) / np.maximum(np.sqrt(var), floor), -clip, clip)
        z[idx[enough]] = zz[enough]

    def cmp(col, exp):
        got = pd.to_numeric(tx[col], errors="coerce").to_numpy(float)
        bad = (np.isnan(got) != np.isnan(exp)) | (np.abs(np.nan_to_num(got) - np.nan_to_num(exp)) > TOL)
        return _n(bad, f"transactions.{col} differs from recomputation")

    return (cmp("tx_count_prev_1h", cnt) + cmp("amount_sum_prev_24h_php", sm)
            + cmp("hours_since_prev_tx", hrs) + cmp("spend_deviation_z", z))


CHECKS = {
    "keys": check_keys, "temporal": check_temporal, "vocabularies": check_vocabularies,
    "amounts": check_amounts, "labels": check_labels, "no_prohibited": check_no_prohibited,
    "nulls": check_nulls, "rolling_features": check_rolling_features,
}


def validate_all(tables, cfg):
    return {name: fn(tables, cfg) for name, fn in CHECKS.items()}
