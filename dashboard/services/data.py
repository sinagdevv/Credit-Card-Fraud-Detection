"""Safe loading and analyst-facing calculations for the dashboard."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

TABLES = ("cardholders", "cards", "merchants", "transactions", "fraud_labels")
PROHIBITED = ("y_true", "latent", "compromise", "fraud_probability", "risk_score")


def resolve_run(path: str | Path) -> Path:
    """Accept a run directory or a parent containing exactly one latest run."""
    root = Path(path).expanduser().resolve()
    if (root / "manifest.json").exists():
        return root
    runs = sorted(root.glob("run_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not runs:
        raise FileNotFoundError(f"No generated run found in {root}")
    return runs[0]


def load_dataset(path: str | Path) -> tuple[dict[str, pd.DataFrame], dict, Path]:
    run = resolve_run(path)
    manifest = json.loads((run / "manifest.json").read_text())
    frames = {}
    for table in TABLES:
        csv = run / f"{table}.csv"
        if not csv.exists():
            raise FileNotFoundError(f"Missing required table: {csv.name}")
        frames[table] = pd.read_csv(csv)
    assert_no_internal_columns(frames)
    tx = frames["transactions"]
    tx["transaction_ts"] = pd.to_datetime(tx["transaction_ts"], errors="raise")
    labels = frames["fraud_labels"]
    for col in ("alert_ts", "review_ts"):
        if col in labels:
            labels[col] = pd.to_datetime(labels[col], errors="coerce")
    return frames, manifest, run


def assert_no_internal_columns(frames: dict[str, pd.DataFrame]) -> None:
    leaked = [f"{name}.{col}" for name, frame in frames.items() for col in frame.columns
              if any(token in col.lower() for token in PROHIBITED)]
    if leaked:
        raise ValueError(f"Internal simulator columns are not allowed: {', '.join(leaked)}")


def analyst_transactions(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    tx = frames["transactions"].merge(
        frames["cards"][["card_id", "cardholder_id", "product_tier"]], on="card_id", how="left", validate="many_to_one"
    ).merge(
        frames["merchants"][["merchant_id", "merchant_category", "country_code", "merchant_region"]],
        on="merchant_id", how="left", validate="many_to_one"
    ).merge(
        frames["fraud_labels"][["transaction_id", "observed_fraud", "review_status", "label_source"]],
        on="transaction_id", how="left", validate="one_to_one"
    )
    tx["investigation_status"] = tx["review_status"].where(tx["label_source"].eq("analyst"), "not investigated")
    tx["label_status"] = tx["review_status"].fillna("unresolved / unlabeled")
    return tx


def kpis(tx: pd.DataFrame, frames: dict[str, pd.DataFrame]) -> dict[str, float | int]:
    analyst = tx["label_source"].eq("analyst")
    return {
        "transactions": len(tx), "value": float(tx["amount_php"].sum()), "average": float(tx["amount_php"].mean()),
        "observed_positives": int(tx["observed_fraud"].fillna(False).sum()),
        "review_coverage": float(analyst.mean()), "cardholders": len(frames["cardholders"]),
        "merchants": len(frames["merchants"]),
    }


def scenario_evidence(repo_root: Path) -> pd.DataFrame:
    evidence = repo_root / "docs" / "qa" / "evidence" / "scenario_reference.json"
    return pd.DataFrame(json.loads(evidence.read_text())["scenarios"])
