import numpy as np
import pandas as pd
import pytest

from sd008_gen import export as ex
from sd008_gen import validate as v

TS = pd.to_datetime


@pytest.fixture
def tables(internal):
    return ex.build_exports(internal)


def test_valid_dataset_passes(tables, real_cfg):
    assert {k: x for k, x in v.validate_all(tables, real_cfg).items() if x} == {}


def _set(t, col, val):
    def f(tb):
        tb[t][col] = val
    return f


def _cell(t, col, i, val):
    def f(tb):
        s = tb[t][col].copy()
        s.iloc[i] = val
        tb[t][col] = s
    return f


def _add_col(t, col):
    return lambda tb: tb[t].__setitem__(col, 1)


BREAKS = [
    ("dup_pk", "keys", _set("merchants", "merchant_id", ["m1", "m1"])),
    ("orphan_fk", "keys", _set("transactions", "card_id", "zz")),
    ("review_before_alert", "temporal", _set("fraud_labels", "review_ts", TS(["2026-02-01 10:00:00", "2026-02-04 10:00:00", pd.NaT]))),
    ("tx_after_expiry", "temporal", _set("cards", "expiry_date", TS(["2026-02-02"]))),
    ("bad_channel", "vocabularies", _set("transactions", "channel", ["POS", "ecommerce", "POS", "mail-phone", "crypto"])),
    ("entry_mode_channel", "vocabularies", _cell("transactions", "entry_mode", 0, "manual")),
    ("amount_zero", "amounts", _cell("transactions", "amount_php", 2, 0.0)),
    ("amount_negative", "amounts", _cell("transactions", "amount_php", 2, -80.0)),
    ("amount_over_cap", "amounts", _cell("transactions", "amount_php", 2, 1e12)),
    ("pending_with_value", "labels", _set("fraud_labels", "observed_fraud", pd.array([True, False, True], dtype="boolean"))),
    ("confirmed_false", "labels", _set("fraud_labels", "observed_fraud", pd.array([False, False, None], dtype="boolean"))),
    ("prohibited_col", "no_prohibited", _add_col("transactions", "latent_x")),
    ("wrong_count_1h", "rolling_features", _cell("transactions", "tx_count_prev_1h", 2, 5)),
    # t2 prior rows: t0 approved 100, t1 declined 250 -> correct 100; counting the decline gives 350
    ("declined_counted_in_sum", "rolling_features", _cell("transactions", "amount_sum_prev_24h_php", 2, 350.0)),
    ("wrong_hours_since", "rolling_features", _cell("transactions", "hours_since_prev_tx", 2, 9.0)),
    ("wrong_z", "rolling_features", _cell("transactions", "spend_deviation_z", 4, 0.0)),
    ("distance_on_pos", "nulls", _cell("transactions", "distance_from_home_km", 1, 5.0)),
    ("null_distance_on_ecom", "nulls", _cell("transactions", "distance_from_home_km", 0, np.nan)),
    # leakage: row 0 sees the later 10:30 event in its 1h window / prev-gap
    ("leak_count_includes_future", "rolling_features", _cell("transactions", "tx_count_prev_1h", 0, 1)),
    ("leak_hours_since_future", "rolling_features", _cell("transactions", "hours_since_prev_tx", 0, 0.5)),
    ("leak_sum_includes_future", "rolling_features", _cell("transactions", "amount_sum_prev_24h_php", 0, 100.0)),
]


@pytest.mark.parametrize("name,check,mutate", BREAKS, ids=[b[0] for b in BREAKS])
def test_break_is_reported(name, check, mutate, tables, real_cfg):
    mutate(tables)
    res = v.validate_all(tables, real_cfg)
    assert res[check], f"{check} missed {name}"
