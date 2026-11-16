"""Allowlisted export of the five analyst tables plus the aggregate label-gap summary (spec 6.1, 9, 10 steps 11-14)."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

import pandas as pd

ALLOWLIST: dict[str, list[str]] = {
    "cardholders": ["cardholder_id", "age_band", "income_band", "home_region", "urbanicity",
                    "account_open_date", "employment_segment"],
    "cards": ["card_id", "cardholder_id", "card_brand", "issue_date", "expiry_date", "credit_limit_php",
              "card_status", "product_tier"],
    "merchants": ["merchant_id", "merchant_category", "mcc", "country_code", "merchant_region",
                  "merchant_size_band", "online_capable"],
    "transactions": ["transaction_id", "card_id", "merchant_id", "transaction_ts", "amount_php", "channel",
                     "foreign_transaction", "authorization_status", "entry_mode", "device_trust_level",
                     "distance_from_home_km", "tx_count_prev_1h", "amount_sum_prev_24h_php",
                     "spend_deviation_z", "local_hour_sin", "local_hour_cos", "hours_since_prev_tx"],
    "fraud_labels": ["transaction_id", "observed_fraud", "review_status", "fraud_type", "alert_ts",
                     "review_ts", "label_source"],
}
TABLES = tuple(ALLOWLIST)
KEY_COLUMNS = {"cardholder_id", "card_id", "merchant_id", "transaction_id"}  # PK/FK columns per 9


def non_key_features() -> list[str]:
    return [f"{t}.{c}" for t, cols in ALLOWLIST.items() for c in cols if not c.endswith("_id")]


# Spec 6.1; an entry ending in '*' is a prefix, others are exact names (also matched as name_ prefixes).
PROHIBITED: tuple[str, ...] = (
    "latent_*", "Y_true", "true_fraud", "is_true_fraud", "fraud_ground_truth", "compromise_state",
    "ato_state", "cnp_compromise_state", "travel_state", "merchant_vulnerability", "spend_propensity",
    "travel_propensity", "fraud_probability", "review_probability",
)

GAP_GROUPS = ("overall", "month", "channel", "merchant_category", "foreign_transaction")
GAP_COLUMNS = ("n_transactions", "n_actual_fraud", "n_investigated", "n_observed_fraud",
               "n_actual_fraud_observed", "n_false_fraud_observed")


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")


def _squash(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def prohibited_columns(frames: dict) -> list[str]:
    bad = []
    for t, df in frames.items():
        for c in df.columns:
            n = _norm(c)
            s = _squash(c)
            for p in PROHIBITED:
                pn = _norm(p)
                hit = n.startswith(pn + "_") if p.endswith("*") else (n == pn or n.startswith(pn + "_"))
                # also compare with all non-alphanumerics removed, so YTrue matches Y_true
                ps = _squash(p)
                hit = hit or (s.startswith(ps) if p.endswith("*") else s == ps)
                if hit:
                    bad.append(f"{t}.{c}")
                    break
    return bad


def build_exports(internal: dict) -> dict:
    """New DataFrames holding only allowlisted columns, in allowlist order. Internal frames are untouched."""
    out = {}
    for t, cols in ALLOWLIST.items():
        missing = [c for c in cols if c not in internal[t].columns]
        if missing:
            raise ValueError(f"{t}: missing columns {missing}")
        out[t] = internal[t].loc[:, cols].copy()
    bad = prohibited_columns(out)
    if bad:
        raise ValueError(f"prohibited columns in export: {bad}")
    return out


def label_gap_summary(tx_internal: pd.DataFrame, merchants: pd.DataFrame) -> pd.DataFrame:
    """Aggregate ground-truth gap counts (spec 6.1). Output columns: group, value, <GAP_COLUMNS>.

    tx_internal needs: merchant_id, transaction_ts (datetime), channel, foreign_transaction,
      y_true (bool), r_investigated (bool), observed_fraud (nullable bool; null = no label row/pending).
    merchants needs: merchant_id, merchant_category.
    """
    d = tx_internal[["merchant_id", "transaction_ts", "channel", "foreign_transaction"]].copy()
    d = d.merge(merchants[["merchant_id", "merchant_category"]], on="merchant_id", how="left")
    y = tx_internal["y_true"].astype(bool).to_numpy()
    obs = tx_internal["observed_fraud"].fillna(False).astype(bool).to_numpy()
    d["n_transactions"] = 1
    d["n_actual_fraud"] = y
    d["n_investigated"] = tx_internal["r_investigated"].astype(bool).to_numpy()
    d["n_observed_fraud"] = obs
    d["n_actual_fraud_observed"] = y & obs
    d["n_false_fraud_observed"] = ~y & obs
    d["overall"] = "all"
    d["month"] = pd.to_datetime(d["transaction_ts"]).dt.strftime("%Y-%m")
    d["foreign_transaction"] = d["foreign_transaction"].astype(bool).astype(str)
    parts = []
    for g in GAP_GROUPS:
        s = d.groupby(g, sort=True)[list(GAP_COLUMNS)].sum().astype("int64").reset_index()
        s.insert(0, "group", g)
        parts.append(s.rename(columns={g: "value"}))
    return pd.concat(parts, ignore_index=True)[["group", "value", *GAP_COLUMNS]]


MONEY_COLUMNS = ("credit_limit_php", "amount_php", "amount_sum_prev_24h_php")  # decimal(12,2) / decimal per spec 9


def _csv_bytes(df: pd.DataFrame) -> bytes:
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            fmt = "%Y-%m-%d" if c.endswith("_date") else "%Y-%m-%dT%H:%M:%S"
            df[c] = df[c].dt.strftime(fmt)
        elif c in MONEY_COLUMNS:
            # string-format so to_csv's %.8f does not apply; NaN stays empty
            df[c] = df[c].map(lambda x: x if pd.isna(x) else f"{float(x):.2f}")
    return df.to_csv(index=False, float_format="%.8f", lineterminator="\n").encode()


def config_sha256(cfg: dict) -> str:
    return hashlib.sha256(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()


def write_outputs(exports: dict, gap_summary: pd.DataFrame, cfg: dict, out_root) -> Path:
    out_root = Path(out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    seed = cfg["simulation"]["seed"]
    sha = config_sha256(cfg)
    run_dir = out_root / f"run_{seed}_{sha[:8]}"
    if run_dir.exists():
        raise FileExistsError(f"run directory already exists: {run_dir}")
    files = {f"{t}.csv": exports[t] for t in TABLES}
    files["label_gap_summary.csv"] = gap_summary
    tmp = Path(tempfile.mkdtemp(prefix=".tmp_run_", dir=out_root))
    try:
        hashes = {}
        for name, df in files.items():
            b = _csv_bytes(df)
            (tmp / name).write_bytes(b)
            hashes[name] = hashlib.sha256(b).hexdigest()
        manifest = {
            "schema_version": cfg["meta"]["schema_version"],
            "seed": seed,
            "config_sha256": sha,
            "row_counts": {n: len(df) for n, df in files.items()},
            "sha256": hashes,
            "columns": {n: list(df.columns) for n, df in files.items()},
        }
        (tmp / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        os.replace(tmp, run_dir)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return run_dir
