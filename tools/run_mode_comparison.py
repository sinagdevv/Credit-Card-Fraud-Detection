"""Aggregate-only stochastic versus exact-mode evidence runner."""
from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "deliverables" / "D2_Synthetic_Dataset_Generator"))
from sd008_gen.config import load_config  # noqa: E402
from sd008_gen.generate import generate  # noqa: E402


def save(path: Path, d: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)
    json.loads(path.read_text())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "docs" / "qa" / "evidence" / "mode_comparison")
    ap.add_argument("--seeds", type=int, nargs="+", default=[20261101, 20261102, 20261103])
    a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for seed in a.seeds:
        for mode in ("stochastic", "exact"):
            path = a.out / f"{mode}_{seed}.json"
            if path.exists():
                rows.append(json.loads(path.read_text())); continue
            cfg = copy.deepcopy(load_config(ROOT / "deliverables" / "D2_Synthetic_Dataset_Generator" / "config" / "scenario_v0.yaml"))
            cfg["simulation"]["seed"] = seed
            t = time.perf_counter()
            r = generate(cfg, profile="BASELINE" if mode == "exact" else None, return_internal=True)
            tx = r["internal"]; fraud = tx.loc[tx.y_true]
            daily = tx.groupby(tx.transaction_ts.dt.date).size()
            per_card = tx.groupby("card_id").size()
            d = {"mode": mode, "seed": seed, "transactions": len(tx), "fraud": int(len(fraud)),
                 "fraud_prevalence": float(len(fraud)/len(tx)), "investigation_coverage": float(tx.r_investigated.mean()),
                 "observed_positives": int(r["info"]["n_observed_fraud"]), "daily_mean": float(daily.mean()),
                 "daily_variance": float(daily.var(ddof=1)), "card_count_cv": float(per_card.std(ddof=1)/per_card.mean()),
                 "mechanisms": {str(k): int(v) for k,v in fraud.mechanism.value_counts().items()},
                 "runtime_seconds": round(time.perf_counter()-t,3)}
            save(path, d); rows.append(d)
    save(a.out / "summary.json", {"runs": rows})
    (a.out / "summary.csv").write_text("mode,seed,transactions,fraud,fraud_prevalence,investigation_coverage,observed_positives,daily_mean,daily_variance,card_count_cv,runtime_seconds\n" + "\n".join(
        ",".join(str(r[k]) for k in ("mode","seed","transactions","fraud","fraud_prevalence","investigation_coverage","observed_positives","daily_mean","daily_variance","card_count_cv","runtime_seconds")) for r in rows) + "\n")


if __name__ == "__main__": main()
