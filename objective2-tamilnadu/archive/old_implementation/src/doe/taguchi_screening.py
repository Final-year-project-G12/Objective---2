"""
src/doe/taguchi_screening.py
===============================
Taguchi L9 orthogonal-array screening + ANOVA, ported from Manvitha's
Rajasthan report ("G8 S1"): "Taguchi L9 + ANOVA, 9 pairs x 9 runs x 5
years" -- a cheap first pass (9 simulator runs per regime x PCM pair, not
hundreds) to check whether any design variable's effect is small enough to
fix before spending the full Sobol DOE budget on it. Report finding for
Rajasthan: "No variable could be fixed: each explains at least 5% of one
response" -- screening is still worth running for Tamil Nadu even if the
same conclusion holds, since that conclusion is itself the useful result
(it justifies searching all 4 variables, not an assumption).

L9(3^4): 4 factors (capsule_diameter_m, flow_rate_kg_s, capsule_count,
arrangement), each at 3 levels (low/mid/high; arrangement's 3 categorical
values ARE its 3 levels), 9 runs -- the standard Taguchi L9 orthogonal
array, balanced so every factor's main effect is estimable from 9 runs
despite 3^4=81 possible combinations.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.io_utils import load_design_bounds

# The standard L9(3^4) orthogonal array (columns = factors A,B,C,D; values = level index 0/1/2)
L9_ARRAY = np.array([
    [0, 0, 0, 0],
    [0, 1, 1, 1],
    [0, 2, 2, 2],
    [1, 0, 1, 2],
    [1, 1, 2, 0],
    [1, 2, 0, 1],
    [2, 0, 2, 1],
    [2, 1, 0, 2],
    [2, 2, 1, 0],
])

FACTOR_NAMES = ["capsule_diameter_m", "flow_rate_kg_s", "capsule_count", "capsule_arrangement"]


@dataclass
class TaguchiCaseSpec:
    case_id: str
    regime_id: int
    pcm_id: object
    capsule_diameter_m: float
    n_capsule: int
    flow_rate_kg_s: float
    capsule_arrangement: str
    run_index: int
    sampling_method: str = "taguchi_l9"


def _three_levels(lo: float, hi: float) -> list:
    return [lo, (lo + hi) / 2.0, hi]


def generate_taguchi_cases(state: str, regime_id: int, pcm_id, arrangements_allowed: list):
    """One L9 screening plan for one (regime, PCM) pair -- 9 runs.
    capsule_count's 3 levels use 2/16/30% of design_bounds' capsule_count
    range in count terms (report: "fraction levels 2/16/30%" for Rajasthan's
    PCM-volume-fraction design variable; Tamil Nadu's own design variable is
    capsule COUNT directly, not a fraction, so the 3 levels are the min/mid/
    max of design_bounds_shared.yaml's capsule_count range, the direct
    equivalent)."""
    bounds = load_design_bounds()
    d_levels = _three_levels(bounds["capsule_diameter_m"]["min"], bounds["capsule_diameter_m"]["max"])
    f_levels = _three_levels(bounds["flow_rate_kg_s"]["min"], bounds["flow_rate_kg_s"]["max"])
    n_levels = _three_levels(bounds["capsule_count"]["min"], bounds["capsule_count"]["max"])
    arr_levels = (arrangements_allowed + arrangements_allowed)[:3]   # exactly 3 levels needed for L9

    cases = []
    for run_idx, row in enumerate(L9_ARRAY):
        d_lvl, f_lvl, n_lvl, a_lvl = row
        cases.append(TaguchiCaseSpec(
            case_id=f"c{regime_id}_{_slug(pcm_id)}_l9_run{run_idx}",
            regime_id=regime_id, pcm_id=pcm_id,
            capsule_diameter_m=float(d_levels[d_lvl]),
            n_capsule=int(round(n_levels[n_lvl])),
            flow_rate_kg_s=float(f_levels[f_lvl]),
            capsule_arrangement=arr_levels[a_lvl],
            run_index=run_idx,
        ))
    return cases


def anova_contribution(results_df: pd.DataFrame, response_col: str) -> dict:
    """Mean ANOVA contribution (%) of each of the 4 factors to one response,
    from the 9 L9 runs' results. results_df must have columns 'run_index'
    (0-8, matching L9_ARRAY's rows) and `response_col`.

    Standard Taguchi L9 ANOVA: for each factor, sum of squares between its 3
    levels' group means (3 runs per level), relative to total sum of
    squares, as a percentage -- the report's own method (section 6.2,
    "Mean ANOVA contribution of each variable").
    """
    y = results_df.set_index("run_index")[response_col].reindex(range(9)).to_numpy(dtype=float)
    grand_mean = y.mean()
    ss_total = float(np.sum((y - grand_mean) ** 2))
    if ss_total <= 0:
        return {name: 0.0 for name in FACTOR_NAMES}

    contributions = {}
    for col_idx, name in enumerate(FACTOR_NAMES):
        levels = L9_ARRAY[:, col_idx]
        ss_factor = 0.0
        for lvl in (0, 1, 2):
            group = y[levels == lvl]
            ss_factor += len(group) * (group.mean() - grand_mean) ** 2
        contributions[name] = 100.0 * ss_factor / ss_total
    return contributions


def _slug(name):
    return "".join(c if c.isalnum() else "_" for c in str(name))[:24]
