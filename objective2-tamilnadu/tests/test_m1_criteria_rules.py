"""
tests/test_m1_criteria_rules.py
================================
The MATLAB export (scripts/c20_m1_export.py) builds its seven design criteria for ANY regime with rule_criteria(). The Fluent study
(ansys/criteria_common/scenarios.py) is written for regime 0 only, so for regimes 1 and 2 there is no shared file to read. These tests pin the
generalisation: for regime 0 the rules must reproduce scenarios.py exactly, and for every regime the seven designs must be well formed and
start from that regime's funnel winner.
"""
import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

BASE = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def c20(monkeypatch_module=None):
    import os
    old = os.getcwd()
    os.chdir(BASE)                                   # the export script uses project-root-relative paths
    argv = sys.argv
    sys.argv = ["c20_m1_export.py"]
    try:
        spec = importlib.util.spec_from_file_location("c20_m1_export_under_test", BASE / "scripts" / "c20_m1_export.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        yield m
    finally:
        sys.argv = argv
        os.chdir(old)


def test_rules_reproduce_the_regime_0_scenarios_exactly(c20):
    c20.check_rules_reproduce_scenarios()            # raises AssertionError on any mismatch


@pytest.mark.parametrize("regime", [0, 1, 2])
def test_seven_designs_are_well_formed_for_every_regime(c20, regime):
    win = pd.read_csv(BASE / "results" / "c16_funnel_winners.csv")
    r = win[win.regime == regime].iloc[0]
    opt = dict(R_in=float(r.R_in_m), fraction=float(r.fraction), arrangement=r.arrangement, N=int(r.N))
    d = c20.rule_criteria(opt, r, regime)
    assert [s["key"] for s in d] == ["criteria_0_optimal_reference", "criteria_1_max_all", "criteria_2_min_all", "criteria_3_ok_not_optimal",
                                     "criteria_4_only_30_capsules", "criteria_5_10pct_of_optimal", "criteria_6_50pct_of_optimal"]
    assert d[0]["R_in"] == opt["R_in"] and d[0]["fraction"] == opt["fraction"]           # criterion 0 IS the funnel winner
    assert d[1]["flow"] == 0.050 and d[2]["flow"] == 0.010                               # max / min of the flow knob
    counts = [c20.n_for(s["R_in"], s["fraction"]) for s in (d[4], d[5], d[6])]
    assert counts == [30, round(0.10 * opt["N"]), round(0.50 * opt["N"])]                # the capsule-count criteria
    for s in d:
        assert 0.0 < s["fraction"] <= 0.40 + 1e-9 and 0.010 <= s["R_in"] <= 0.040 + 1e-9
