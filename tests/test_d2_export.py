import copy
import hashlib
import json

import pandas as pd
import pytest

from sd008_gen import export as ex


def test_non_key_feature_count():
    assert len(ex.non_key_features()) == 38


@pytest.mark.parametrize("col", ["latent_x", "Y_TRUE", "YTrue", "Y-True", "LatentX", "fraud_probability",
                                 "merchant_vulnerability"])
def test_prohibited_flagged(col):
    assert ex.prohibited_columns({"t": pd.DataFrame({col: [1]})}) == [f"t.{col}"]


def test_allowlist_not_flagged():
    for t, cols in ex.ALLOWLIST.items():
        assert ex.prohibited_columns({t: pd.DataFrame(columns=cols)}) == []


def test_build_exports(internal):
    before = {t: d.copy() for t, d in internal.items()}
    out = ex.build_exports(internal)
    for t in out:
        assert out[t] is not internal[t]
        assert list(out[t].columns) == ex.ALLOWLIST[t]
        pd.testing.assert_frame_equal(internal[t], before[t])
    assert "latent_s" in internal["cardholders"].columns
    out["merchants"].loc[0, "mcc"] = "x"
    assert internal["merchants"].loc[0, "mcc"] == "5411"


def test_build_exports_missing_column(internal):
    internal["cards"] = internal["cards"].drop(columns="product_tier")
    with pytest.raises(ValueError, match="product_tier"):
        ex.build_exports(internal)


@pytest.fixture
def gap(internal):
    fl = internal["fraud_labels"].set_index("transaction_id").observed_fraud
    tx = internal["transactions"]
    return ex.label_gap_summary(tx.assign(observed_fraud=tx.transaction_id.map(fl).astype("boolean")),
                                internal["merchants"])


def test_gap_summary_columns(gap):
    assert list(gap.columns) == ["group", "value", *ex.GAP_COLUMNS]
    assert not any(c.endswith("_id") or "ts" in c for c in gap.columns)
    ov = gap[gap.group == "overall"].iloc[0]
    assert (ov.n_transactions, ov.n_actual_fraud, ov.n_observed_fraud) == (5, 2, 1)
    assert ov.n_false_fraud_observed == 0 and ov.n_actual_fraud_observed == 1


def test_write_outputs(internal, gap, real_cfg, tmp_path):
    exp = ex.build_exports(internal)
    exp["cards"] = exp["cards"].assign(credit_limit_php=[50000.5])
    r1 = ex.write_outputs(exp, gap, real_cfg, tmp_path / "a")
    r2 = ex.write_outputs(exp, gap, real_cfg, tmp_path / "b")
    h = lambda r: {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(r.iterdir())}
    assert h(r1) == h(r2)
    man = json.loads((r1 / "manifest.json").read_text())
    assert man["seed"] == real_cfg["simulation"]["seed"]
    assert man["row_counts"]["transactions.csv"] == 5
    assert man["sha256"]["cards.csv"] == h(r1)["cards.csv"]
    assert "50000.50" in (r1 / "cards.csv").read_text()
    assert "250.00" in (r1 / "transactions.csv").read_text()
    with pytest.raises(FileExistsError):
        ex.write_outputs(exp, gap, real_cfg, tmp_path / "a")
    assert [p.name for p in (tmp_path / "a").iterdir()] == [r1.name]
