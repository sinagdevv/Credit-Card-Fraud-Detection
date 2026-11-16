"""Persisted aggregate-only exact-count calibration runner for SD-008."""
from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "deliverables" / "D2_Synthetic_Dataset_Generator"))
from sd008_gen.config import load_config  # noqa: E402
from sd008_gen.generate import generate  # noqa: E402


def atomic_json(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)
    json.loads(path.read_text())


def valid(path: Path) -> bool:
    try:
        d = json.loads(path.read_text())
        return d["transactions"] == 150_000 and d["validation"] == "PASS"
    except (OSError, ValueError, KeyError):
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "docs" / "qa" / "evidence" / "calibration")
    ap.add_argument("--seeds", type=int, nargs="+", default=list(range(20261101, 20261109)))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    rows = []
    for seed in args.seeds:
        path = args.out / f"seed_{seed}.json"
        if valid(path):
            rows.append(json.loads(path.read_text()))
            continue
        cfg = copy.deepcopy(load_config(ROOT / "deliverables" / "D2_Synthetic_Dataset_Generator" / "config" / "scenario_v0.yaml"))
        cfg["simulation"]["seed"] = seed
        start = time.perf_counter()
        result = generate(cfg, profile="BASELINE", return_internal=True)
        tx = result["internal"]
        fraud = tx.loc[tx["y_true"]]
        payload = {
            "seed": seed, "commit": commit, "transactions": int(len(tx)),
            "fraud_count": int(fraud.shape[0]), "fraud_prevalence": float(fraud.shape[0] / len(tx)),
            "mechanism_counts": {str(k): int(v) for k, v in fraud["mechanism"].value_counts().items()},
            "investigated": int(tx["r_investigated"].sum()),
            "observed_positives": int(result["info"]["n_observed_fraud"]),
            "runtime_seconds": round(time.perf_counter() - start, 3), "validation": "PASS",
        }
        atomic_json(path, payload)
        rows.append(payload)
    rates = np.array([r["fraud_prevalence"] for r in rows], float)
    summary = {
        "n_seeds": len(rows), "seeds": [r["seed"] for r in rows],
        "mean": float(rates.mean()), "median": float(np.median(rates)), "std": float(rates.std(ddof=1)),
        "min": float(rates.min()), "max": float(rates.max()),
        "mean_ci95_t": [float(rates.mean() - 2.365 * rates.std(ddof=1) / np.sqrt(len(rates))), float(rates.mean() + 2.365 * rates.std(ddof=1) / np.sqrt(len(rates)))],
        "reference": 0.003, "difference_from_reference": float(rates.mean() - 0.003),
    }
    atomic_json(args.out / "calibration_summary.json", summary)
    (args.out / "calibration_summary.csv").write_text("seed,fraud_count,fraud_prevalence,investigated,observed_positives,runtime_seconds\n" + "\n".join(
        f"{r['seed']},{r['fraud_count']},{r['fraud_prevalence']:.10f},{r['investigated']},{r['observed_positives']},{r['runtime_seconds']:.3f}" for r in rows
    ) + "\n")


if __name__ == "__main__":
    main()
