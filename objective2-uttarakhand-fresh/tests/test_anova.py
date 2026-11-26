"""tests/test_anova.py - G8/S1: the ANOVA on an L9 array recovers a planted effect and calls the null factors null."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.optimize.anova import L9, anova


def _frame(effect_a=2.0, noise=0.05, years=5, seed=1):
    rng = np.random.default_rng(seed)
    rows = []
    for run, (a, b, c, d) in enumerate(L9):
        for y in range(years):
            rows.append({"A": a, "B": b, "C": c, "D": d, "y": effect_a * a + rng.normal(0, noise)})
    return pd.DataFrame(rows)


def test_l9_is_orthogonal():
    arr = np.array(L9)
    for i in range(4):
        assert sorted(np.bincount(arr[:, i])) == [3, 3, 3]
        for j in range(i + 1, 4):
            assert len({(a, b) for a, b in arr[:, [i, j]]}) == 9      # every level pair exactly once


def test_planted_factor_dominates_and_nulls_are_null():
    t = anova(_frame(), ["A", "B", "C", "D"], "y").set_index("factor")
    assert t.loc["A", "contribution_pct"] > 95 and t.loc["A", "p"] < 1e-6
    for f in "BCD":
        assert t.loc[f, "contribution_pct"] < 2.0 and t.loc[f, "p"] > 0.01


def test_contributions_sum_to_100_and_dof_add_up():
    df = _frame(effect_a=1.0, noise=0.5)
    t = anova(df, ["A", "B", "C", "D"], "y")
    assert t["contribution_pct"].sum() == pytest.approx(100.0)
    assert t["dof"].sum() == len(df) - 1
