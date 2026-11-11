"""
tests/test_cfd_closure.py
==========================
Regression test for the named capsule closure switch (WP2-C, B2): pcm_integration.closure = "legacy" (default) must reproduce the frozen
c = 5, F = 2 bit-for-bit; "cfd_closure_v1" must read c and F from configs/cfd_closure_v1.yaml and change the result.
"""

import copy
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.io_utils import load_system_config
from src.simulation import cfd_closure as cc
from tests.test_capsule_closure_option import _year


def test_legacy_is_a_noop_and_frozen_config_has_no_closure_key():
    cfg = load_system_config()
    assert "closure" not in cfg["pcm_integration"]
    assert cc.apply_closure(cfg) is cfg
    legacy = copy.deepcopy(cfg)
    legacy["pcm_integration"]["closure"] = "legacy"
    assert cc.apply_closure(legacy) is legacy


def test_v1_file_values_are_applied_and_the_input_is_not_mutated():
    cfg = load_system_config()
    sel = copy.deepcopy(cfg)
    sel["pcm_integration"]["closure"] = "cfd_closure_v1"
    out = cc.apply_closure(sel)
    v1 = cc.load_closure("cfd_closure_v1")
    assert out["pcm_integration"]["conduction_coefficient_c"] == v1["conduction_coefficient_c"] == 10.0
    assert out["pcm_integration"]["liquid_convection_enhancement"] == v1["liquid_convection_enhancement"] == 5.0
    assert "conduction_coefficient_c" not in sel["pcm_integration"]
    assert v1["status"].startswith("UNVALIDATED")


def test_unknown_closure_is_rejected():
    cfg = copy.deepcopy(load_system_config())
    cfg["pcm_integration"]["closure"] = "cfd_closure_v9"
    with pytest.raises(ValueError):
        cc.apply_closure(cfg)


def test_year_run_legacy_is_bit_identical_and_v1_equals_explicit_c_and_F():
    base, _ = _year()
    legacy, _ = _year({"pcm_integration": {"closure": "legacy"}})
    assert legacy == base
    v1, res = _year({"pcm_integration": {"closure": "cfd_closure_v1"}})
    explicit, _ = _year({"pcm_integration": {"conduction_coefficient_c": 10.0, "liquid_convection_enhancement": 5.0}})
    assert v1 == explicit            # the named closure is exactly the two keys it stands for
    assert v1 != base
    assert res < 1e-6                # energy balance still closes
