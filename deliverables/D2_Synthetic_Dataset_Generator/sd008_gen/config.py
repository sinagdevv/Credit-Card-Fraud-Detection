"""Config loading and RNG stream derivation (spec §10 steps 1-2)."""
import numpy as np
import yaml

STREAMS = ("entities", "events", "fraud", "review", "pilot")


def load_config(path) -> dict:
    with open(path) as f:
        cfg = yaml.safe_load(f)
    bad = [k for k, v in cfg.get("parameters", {}).items() if v.get("approved") is not True]
    if bad:
        raise ValueError(f"parameters not approved: {bad}")
    return cfg


def rng_streams(seed: int) -> dict:
    children = np.random.SeedSequence(seed).spawn(len(STREAMS))
    return {n: np.random.Generator(np.random.PCG64(c)) for n, c in zip(STREAMS, children)}
