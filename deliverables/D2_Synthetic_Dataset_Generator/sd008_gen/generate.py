"""Single entry point: config -> entities -> events -> labels -> exports -> validation -> files (spec 10)."""
from __future__ import annotations

import argparse
import copy
import time

from .config import load_config, rng_streams
from .entities import make_entities
from .events import simulate_events
from .export import build_exports, label_gap_summary, write_outputs
from .labels import make_labels
from .validate import validate_all


def generate(cfg: dict, out_root=None, scale: str = "test", return_internal: bool = False) -> dict:
    cfg = copy.deepcopy(cfg)
    if scale == "target":
        cfg["simulation"].update(cfg["simulation"]["target_scale"])
    elif scale != "test":
        raise ValueError(f"scale must be 'test' or 'target', got {scale!r}")
    st = rng_streams(cfg["simulation"]["seed"])
    ent = make_entities(cfg, st["entities"])
    tx, info = simulate_events(cfg, ent, st)
    lab, tx = make_labels(cfg, tx, st["review"])
    exports = build_exports({**ent, "transactions": tx, "fraud_labels": lab})
    gap = label_gap_summary(tx, ent["merchants"])
    problems = {k: v for k, v in validate_all(exports, cfg).items() if v}
    if problems:
        raise RuntimeError(f"validation failed, nothing written: {problems}")
    info = {**info, "n_labels": len(lab), "n_investigated": int(tx["r_investigated"].sum()),
            "review_status": lab["review_status"].value_counts().to_dict(),
            "label_source": lab["label_source"].value_counts().to_dict(),
            "n_observed_fraud": int(lab["observed_fraud"].fillna(False).sum()),
            "n_false_confirmations": int((lab["observed_fraud"].fillna(False) & ~lab["y_true"]).sum())}
    run_dir = write_outputs(exports, gap, cfg, out_root) if out_root else None
    res = dict(exports=exports, gap_summary=gap, info=info, problems=problems, run_dir=run_dir)
    if return_internal:
        res["internal"] = tx
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m sd008_gen.generate")
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scale", choices=["test", "target"], default="test")
    ap.add_argument("--seed", type=int)
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    if a.seed is not None:
        cfg["simulation"]["seed"] = a.seed
    t0 = time.time()
    r = generate(cfg, a.out, a.scale)
    print("run dir:", r["run_dir"])
    for k, v in r["exports"].items():
        print(f"  {k}: {len(v)} rows")
    i, n = r["info"], r["info"]["n_rows"]
    print(f"fraud rate {i['main_realized_rate']:.4f}; investigated {i['n_investigated'] / n:.4f}; "
          f"observed fraud {i['n_observed_fraud']}; labels {i['review_status']}")
    print(f"runtime {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
