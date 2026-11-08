import copy

import numpy as np
import pytest
import yaml

from conftest import CFG_PATH
from sd008_gen.config import load_config, rng_streams


def test_load_real_config():
    assert load_config(CFG_PATH)["simulation"]["seed"]


def test_real_cfg_fixture_not_polluted(real_cfg):
    assert all(v["approved"] is True for v in real_cfg["parameters"].values())


def test_unapproved_parameter_raises_naming_key(real_cfg, tmp_path):
    cfg = copy.deepcopy(real_cfg)
    key = next(iter(cfg["parameters"]))
    cfg["parameters"][key]["approved"] = False
    p = tmp_path / "c.yaml"
    p.write_text(yaml.safe_dump(cfg))
    with pytest.raises(ValueError, match=key):
        load_config(p)


def test_streams_deterministic_and_distinct():
    a, b = rng_streams(7), rng_streams(7)
    assert {"entities", "events", "fraud", "review"} <= set(a)
    for n in a:
        assert np.array_equal(a[n].random(5), b[n].random(5))
    firsts = [tuple(s.random(5)) for s in rng_streams(7).values()]
    assert len(set(firsts)) == len(firsts)
    assert not np.array_equal(rng_streams(8)["entities"].random(5), rng_streams(7)["entities"].random(5))
