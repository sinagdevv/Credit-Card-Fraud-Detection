import copy
import hashlib
import importlib
import json
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest
import yaml

from sd008_gen import export as ex
from sd008_gen.config import rng_streams
from sd008_gen.entities import make_entities
from sd008_gen.events import simulate_events
from sd008_gen.labels import make_labels

gen_mod = importlib.import_module("sd008_gen.generate")
H = pd.Timedelta(hours=1)


def _small(real_cfg):
    cfg = copy.deepcopy(real_cfg)
    cfg["simulation"].update(n_cardholders=200, n_merchants=50, end_date="2026-03-31")
    return cfg


@pytest.fixture(scope="module")
def lab(real_cfg):
    cfg = _small(real_cfg)
    s = rng_streams(cfg["simulation"]["seed"])
    ent = make_entities(cfg, s["entities"])
    tx, _ = simulate_events(cfg, ent, s)
    fl, tx2 = make_labels(cfg, tx, s["review"])
    return cfg, ent, tx, fl, tx2


def test_daily_capacity(lab):
    cfg, _, tx, _, tx2 = lab
    r_r = cfg["parameters"]["review_coverage"]["value"]
    day = tx2["transaction_ts"].dt.normalize()
    g = tx2.groupby(day)["r_investigated"].agg(["sum", "size"])
    assert (g["sum"] == np.round(r_r * g["size"])).all()
    assert g["sum"].sum() > 0
    assert len(tx2) == len(tx) and (tx2["transaction_id"] == tx["transaction_id"]).all()


def test_daily_capacity_catches_wrong_count(lab):
    cfg, _, _, _, tx2 = lab
    day = tx2["transaction_ts"].dt.normalize()
    g = tx2.groupby(day)["r_investigated"].agg(["sum", "size"])
    assert not (g["sum"] == np.round(0.05 * g["size"])).all()


def test_label_rows_match_investigated_or_customer(lab):
    _, _, _, fl, tx2 = lab
    assert fl["transaction_id"].is_unique
    assert set(fl["transaction_id"]) <= set(tx2["transaction_id"])
    inv = set(tx2.loc[tx2["r_investigated"], "transaction_id"])
    an = fl[fl["label_source"] == "analyst"]
    assert set(an["transaction_id"]) == inv
    assert set(fl["label_source"]) <= {"analyst", "customer"}


def test_alert_ts(lab):
    _, _, tx, fl, _ = lab
    ts = tx.set_index("transaction_id")["transaction_ts"]
    an, cu = fl[fl["label_source"] == "analyst"], fl[fl["label_source"] == "customer"]
    assert len(an) and len(cu)
    exp = ts[an["transaction_id"]].dt.normalize().to_numpy() + pd.Timedelta("23:59:59")
    assert (an["alert_ts"].to_numpy() == exp).all()
    assert cu["alert_ts"].isna().all()


def test_review_delays(lab):
    _, _, tx, fl, _ = lab
    ts = tx.set_index("transaction_id")["transaction_ts"]
    an = fl[(fl["label_source"] == "analyst") & fl["review_ts"].notna()]
    d = an["review_ts"] - an["alert_ts"]
    assert len(an) and (d >= H).all() and (d <= pd.Timedelta(days=60)).all()
    cu = fl[fl["label_source"] == "customer"]
    d = cu["review_ts"].to_numpy() - ts[cu["transaction_id"]].to_numpy()
    assert (d >= np.timedelta64(1, "h")).all() and (d <= np.timedelta64(90, "D")).all()


def test_pending_and_status_consistency(lab):
    _, _, _, fl, _ = lab
    p = fl[fl["review_status"] == "pending"]
    assert len(p) > 0
    assert p["observed_fraud"].isna().all() and p["review_ts"].isna().all()
    assert p["fraud_type"].isna().all() and (p["label_source"] == "analyst").all()
    rest = fl[fl["review_status"] != "pending"]
    assert rest["observed_fraud"].notna().all() and rest["review_ts"].notna().all()
    assert (rest.loc[rest["review_status"] == "confirmed", "observed_fraud"] == True).all()  # noqa: E712
    assert (rest.loc[rest["review_status"] == "cleared", "observed_fraud"] == False).all()  # noqa: E712
    assert set(fl["review_status"]) <= {"pending", "confirmed", "cleared"}


def test_customer_rows(lab):
    _, _, _, fl, tx2 = lab
    cu = fl[fl["label_source"] == "customer"]
    assert (cu["review_status"] == "confirmed").all()
    assert (cu["observed_fraud"] == True).all()  # noqa: E712
    t = tx2.set_index("transaction_id").loc[cu["transaction_id"]]
    assert t["y_true"].all() and not t["r_investigated"].any()


def test_no_label_after_simulation_end(lab):
    cfg, _, _, fl, _ = lab
    end = pd.Timestamp(cfg["simulation"]["end_date"]) + pd.Timedelta("23:59:59")
    assert (fl["review_ts"].dropna() <= end).all()
    assert (fl["alert_ts"].dropna() <= end).all()


def test_fraud_type(lab):
    _, _, tx, fl, _ = lab
    t = tx.set_index("transaction_id").loc[fl["transaction_id"]]
    obs = fl["observed_fraud"].fillna(False).to_numpy(bool)
    assert fl.loc[~obs, "fraud_type"].isna().all()
    assert fl.loc[obs, "fraud_type"].notna().all()
    y = t["y_true"].to_numpy()
    m = obs & y
    assert (fl.loc[m, "fraud_type"].to_numpy() == t.loc[m, "mechanism"].to_numpy()).all()
    f = obs & ~y
    exp = np.where(t.loc[f, "channel"].isin(["ecommerce", "mail-phone"]), "cnp", "ato")
    assert (fl.loc[f, "fraud_type"].to_numpy() == exp).all()


def test_false_confirmations_fraud_type(lab):
    cfg, _, tx, _, _ = lab
    cfg = copy.deepcopy(cfg)
    cfg["parameters"]["review_specificity"]["value"] = 0.0
    fl, _ = make_labels(cfg, tx, rng_streams(cfg["simulation"]["seed"])["review"])
    t = tx.set_index("transaction_id").loc[fl["transaction_id"]]
    conf = (fl["review_status"] == "confirmed").to_numpy()
    y = t["y_true"].to_numpy()
    f = conf & ~y
    assert f.sum() > 0
    exp = np.where(t.loc[f, "channel"].isin(["ecommerce", "mail-phone"]), "cnp", "ato")
    assert (fl.loc[f, "fraud_type"].to_numpy() == exp).all()
    tc = conf & y
    assert tc.sum() > 0
    assert (fl.loc[tc, "fraud_type"].to_numpy() == t.loc[tc, "mechanism"].to_numpy()).all()


def test_gap_summary(lab):
    _, ent, _, _, tx2 = lab
    g = ex.label_gap_summary(tx2, ent["merchants"])
    assert list(g.columns) == ["group", "value", *ex.GAP_COLUMNS]
    ov = g[g["group"] == "overall"].iloc[0]
    assert ov["n_transactions"] == len(tx2)
    assert g.loc[g["group"] == "month", "n_transactions"].sum() == ov["n_transactions"]
    assert (g["n_actual_fraud_observed"] + g["n_false_fraud_observed"] == g["n_observed_fraud"]).all()


# ---- generate() ----

@pytest.fixture(scope="module")
def small_yaml_cfg(real_cfg):
    return _small(real_cfg)


def test_generate_writes_files_deterministically(small_yaml_cfg, tmp_path):
    r1 = gen_mod.generate(small_yaml_cfg, tmp_path / "a")
    r2 = gen_mod.generate(small_yaml_cfg, tmp_path / "b")
    names = [f"{t}.csv" for t in ex.TABLES] + ["label_gap_summary.csv", "manifest.json"]
    d1, d2 = r1["run_dir"], r2["run_dir"]
    for n in names:
        assert (d1 / n).is_file(), n
    assert not r1["problems"]
    for n in names:
        assert hashlib.sha256((d1 / n).read_bytes()).digest() == hashlib.sha256((d2 / n).read_bytes()).digest(), n
    for t in ex.TABLES:
        hdr = (d1 / f"{t}.csv").read_text().splitlines()[0].split(",")
        assert hdr == ex.ALLOWLIST[t]
    assert not ex.prohibited_columns({t: pd.read_csv(d1 / f"{t}.csv", nrows=1) for t in ex.TABLES})
    assert json.loads((d1 / "manifest.json").read_text())["seed"] == small_yaml_cfg["simulation"]["seed"]


def test_generate_validation_failure_writes_nothing(small_yaml_cfg, tmp_path, monkeypatch):
    monkeypatch.setattr(gen_mod, "validate_all", lambda exports, cfg: {"fake_check": ["boom"]})
    with pytest.raises(RuntimeError):
        gen_mod.generate(small_yaml_cfg, tmp_path)
    assert not any(tmp_path.iterdir()) if tmp_path.exists() else True


def test_generate_bad_scale(small_yaml_cfg, tmp_path):
    with pytest.raises(ValueError):
        gen_mod.generate(small_yaml_cfg, tmp_path, scale="huge")


def test_cli_smoke(small_yaml_cfg, tmp_path):
    cfg = copy.deepcopy(small_yaml_cfg)
    cfgp = tmp_path / "small.yaml"
    cfgp.write_text(yaml.safe_dump(cfg))
    cwd = gen_mod.__file__.rsplit("/sd008_gen/", 1)[0]
    p = subprocess.run([sys.executable, "-m", "sd008_gen.generate", "--config", str(cfgp),
                        "--out", str(tmp_path / "out")], cwd=cwd, capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stderr
    runs = list((tmp_path / "out").glob("run_*"))
    assert len(runs) == 1 and (runs[0] / "manifest.json").is_file()
