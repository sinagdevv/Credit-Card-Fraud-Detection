import numpy as np
import pandas as pd
import pytest

from sd008_gen.config import rng_streams
from sd008_gen.entities import make_entities
from sd008_gen.export import ALLOWLIST


def gen(cfg, seed=1):
    return make_entities(cfg, rng_streams(seed)["entities"])


@pytest.fixture(scope="module")
def ents(real_cfg):
    import copy
    cfg = copy.deepcopy(real_cfg)
    cfg["simulation"]["n_cardholders"], cfg["simulation"]["n_merchants"] = 200, 50
    return cfg, gen(cfg)


def test_same_seed_equal_and_different_seed_differs(ents):
    cfg, e = ents
    e2, e3 = gen(cfg), gen(cfg, 2)
    for t in ("cardholders", "cards", "merchants"):
        pd.testing.assert_frame_equal(e[t], e2[t])
    assert not e["cardholders"]["cardholder_id"].equals(e3["cardholders"]["cardholder_id"])
    assert not np.array_equal(e["holder_category_prefs"], e3["holder_category_prefs"])


def test_keys(ents):
    _, e = ents
    h, c, m = e["cardholders"], e["cards"], e["merchants"]
    for df, k in ((h, "cardholder_id"), (c, "card_id"), (m, "merchant_id")):
        assert df[k].is_unique
    assert c["cardholder_id"].isin(h["cardholder_id"]).all()
    n = c.groupby("cardholder_id").size().reindex(h["cardholder_id"])
    assert n.between(1, 4).all()


def test_dates(ents):
    cfg, e = ents
    start = pd.Timestamp(cfg["simulation"]["start_date"])
    c = e["cards"].merge(e["cardholders"][["cardholder_id", "account_open_date"]], on="cardholder_id")
    assert (c.account_open_date <= c.issue_date).all()
    assert (c.issue_date <= start).all() and (start < c.expiry_date).all()


def test_limits_vocab_mcc_region(ents):
    cfg, e = ents
    b = cfg["parameters"]["credit_limit_bounds"]["value"]
    assert e["cards"].credit_limit_php.between(b["min_php"], b["max_php"]).all()
    V = cfg["vocabularies"]
    for t, cols in (("cardholders", ["age_band", "income_band", "home_region", "urbanicity", "employment_segment"]),
                    ("cards", ["card_brand", "product_tier"]),
                    ("merchants", ["country_code", "merchant_size_band"])):
        for col in cols:
            assert e[t][col].isin(V[col]["values"]).all(), col
    m = e["merchants"]
    assert m.merchant_category.isin(V["merchant_category"]["mcc"]).all()
    assert (m.merchant_category.map(V["merchant_category"]["mcc"]) == m.mcc).all()
    by = V["merchant_region"]["by_country"]
    assert all(r in by[k] for k, r in zip(m.country_code, m.merchant_region))
    f = m[m.country_code != "PH"]
    assert len(f) and not f.merchant_region.isin(by["PH"]).any()
    assert (e["cards"].card_status == "active").all()


def test_columns_subset_of_allowlist_plus_latent(ents):
    _, e = ents
    for t in ("cardholders", "cards", "merchants"):
        assert all(c in ALLOWLIST[t] or c.startswith("latent_") for c in e[t].columns), t
