"""
tests/test_flow_dependent_fr.py
==================================
The optional flow-dependent collector heat removal factor (collector.flow_dependent_fr, off by default).
"""

import copy
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.io_utils import load_system_config
from src.simulation.collector_model import apply_flow_dependent_fr, heat_removal_factor


def _cfg(enabled):
    c = copy.deepcopy(load_system_config())
    c["collector"]["flow_dependent_fr"]["enabled"] = enabled
    return c


def test_off_by_default_and_returns_the_same_object():
    cfg = load_system_config()
    assert cfg["collector"]["flow_dependent_fr"]["enabled"] is False
    assert apply_flow_dependent_fr(cfg, 0.01) is cfg


def test_scale_is_one_at_the_reference_flow():
    c = _cfg(True)
    out = apply_flow_dependent_fr(c, c["collector"]["flow_dependent_fr"]["reference_flow_kg_s"])
    assert out["collector"]["fr_tau_alpha"] == pytest.approx(c["collector"]["fr_tau_alpha"], rel=1e-12)
    assert out["collector"]["fr_ul_W_m2K"] == pytest.approx(c["collector"]["fr_ul_W_m2K"], rel=1e-12)


def test_heat_removal_factor_rises_with_flow_and_stays_below_one():
    c = _cfg(True)
    f = [heat_removal_factor(q, c) for q in (0.010, 0.020, 0.030, 0.040, 0.050)]
    assert all(a < b for a, b in zip(f, f[1:])) and f[-1] < 1.0


def test_hand_calculated_value():
    # A = 1.5 m2, U_L = 5.0, F' = 0.84, cp = 4186, m = 0.030: x = 1.5*5*0.84/(0.030*4186) = 0.050167; F_R = F' * (1 - exp(-x))/x
    import math
    x = 1.5 * 5.0 * 0.84 / (0.030 * 4186.0)
    assert heat_removal_factor(0.030, _cfg(True)) == pytest.approx(0.84 * (1 - math.exp(-x)) / x, rel=1e-12)


def test_low_flow_lowers_collector_coefficients():
    c = _cfg(True)
    lo, hi = apply_flow_dependent_fr(c, 0.010), apply_flow_dependent_fr(c, 0.050)
    assert lo["collector"]["fr_tau_alpha"] < c["collector"]["fr_tau_alpha"] < hi["collector"]["fr_tau_alpha"]
    assert load_system_config()["collector"]["fr_tau_alpha"] == 0.75        # the cached config was not mutated
