"""Review, alert and customer-report labels (spec 5.11 Eqs 19, 20, 20b; 10 steps 11-12)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .export import ALLOWLIST


def _pv(cfg, name):
    return cfg["parameters"][name]["value"]


def _trunc_lognormal_hours(rng, mu, sigma, lo, hi, n):
    """LogNormal(mu, sigma) in hours truncated to [lo, hi] by resampling (not clipping)."""
    out = np.empty(n)
    todo = np.arange(n)
    while len(todo):
        x = np.exp(rng.normal(mu, sigma, len(todo)))
        ok = (x >= lo) & (x <= hi)
        out[todo[ok]] = x[ok]
        todo = todo[~ok]
    return out


def _hours(h):
    return pd.to_timedelta(np.round(h * 3600).astype("int64"), unit="s")


def make_labels(cfg: dict, tx_internal: pd.DataFrame, rng: np.random.Generator) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (fraud_labels internal frame, copy of tx_internal + r_investigated, observed_fraud)."""
    tx = tx_internal.copy()
    n = len(tx)
    th, s = _pv(cfg, "alert_coefficients"), _pv(cfg, "logistic_scale_s")
    r_r = _pv(cfg, "review_coverage")
    dly, cr = _pv(cfg, "review_delay"), _pv(cfg, "customer_report_probability_and_delay")
    sens, spec = _pv(cfg, "review_sensitivity"), _pv(cfg, "review_specificity")
    end = pd.Timestamp(cfg["simulation"]["end_date"]) + pd.Timedelta(hours=23, minutes=59, seconds=59)
    y = tx["y_true"].to_numpy(bool)

    z = tx["spend_deviation_z"].fillna(0.0).abs().to_numpy()  # null z contributes 0
    score = (th["theta_0"] + th["theta_z"] * z + th["theta_v"] * np.log1p(tx["tx_count_prev_1h"].to_numpy())
             + th["theta_F"] * tx["foreign_transaction"].to_numpy(float)
             + th["theta_d"] * (tx["device_trust_level"] == "unknown").to_numpy(float)
             + rng.logistic(0.0, s, n))
    day = tx["transaction_ts"].dt.normalize()
    cap = np.round(r_r * day.groupby(day).transform("size").to_numpy())
    rank = pd.Series(score).groupby(day.to_numpy()).rank(method="first", ascending=False).to_numpy()
    R = rank <= cap
    alert_ts = day + pd.Timedelta(hours=23, minutes=59, seconds=59)

    # analyst reviews
    D = _trunc_lognormal_hours(rng, dly["mu_D_log_hours"], dly["sigma_D"], *dly["truncate_hours"], n)
    review_ts = alert_ts + _hours(D)
    obs_an = np.where(y, rng.random(n) < sens, rng.random(n) < 1 - spec)
    pending = R & (review_ts > end)
    a = R

    # customer reports (R=0 only)
    DC = _trunc_lognormal_hours(rng, cr["mu_C_log_hours"], cr["sigma_C"], *cr["truncate_hours"], n)
    rep_ts = tx["transaction_ts"] + _hours(DC)
    reported = ~R & (rng.random(n) < np.where(y, cr["p_report"], cr["p_false"])) & (rep_ts <= end)

    obs = np.where(a, obs_an, True)
    guess = np.where(tx["channel"].isin(["ecommerce", "mail-phone"]), "cnp", "ato")
    ftype = np.where(y, tx["mechanism"].to_numpy(object), guess)
    keep = a | reported
    out = pd.DataFrame({
        "transaction_id": tx["transaction_id"],
        "observed_fraud": pd.array(np.where(pending, None, obs), dtype="boolean"),
        "review_status": np.where(pending, "pending", np.where(obs, "confirmed", "cleared")),
        "fraud_type": pd.Series(np.where(obs & ~pending, ftype, None), dtype=object),
        "alert_ts": alert_ts.where(a),
        "review_ts": pd.Series(np.where(a, review_ts, rep_ts)).where(~pending),
        "label_source": np.where(a, "analyst", "customer"),
        "y_true": y, "r_investigated": R,
    })[keep.tolist()].reset_index(drop=True)
    assert list(out.columns[:len(ALLOWLIST["fraud_labels"])]) == ALLOWLIST["fraud_labels"]
    tx["r_investigated"] = R
    tx["observed_fraud"] = pd.array(np.where(keep & ~pending, obs, None), dtype="boolean")
    return out, tx
