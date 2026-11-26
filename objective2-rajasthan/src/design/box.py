"""
src/design/box.py
====================
Common-plant rebuild (Unified Rebuild Plan, adopted 2026-11-22): the ONE place that states the search box, the two fidelities and the
robust stack-anchor rule, all read from configs/design_space.yaml. Every rebuild stage script imports these names instead of typing
bounds by hand.

Box (plan R4/R6): inner radius 10-40 mm, PCM fraction 2-40 %, flow FIXED at 0.030 kg/s (not searched), arrangements single-layer /
staggered / radial. Searched variables: R_in, fraction, arrangement.

Fidelities (plan L5, cheap-then-full screen; declared 2026-11-23 before any search run, docs/REBUILD_COMMON100L.md section 5):
  cheap  dt 150 s, ONE representative explore year per regime = the 2016-2019 year whose annual GHI is closest to the regime's
         2016-2019 mean (weather-only choice): regime 0 -> 2018, 1 -> 2017, 2 -> 2018 (Rajasthan, 3 regimes). Used by screening, DOE, search, grid.
  full   dt = model.report_timestep_s (37.5 s), every year of the role. Used for finalists, selection, test and report years.
  The cheap screen is used for selection only if, on the finalists, the Spearman rank correlation of the mean paired g_window between
  cheap and full is >= CHEAP_FULL_RHO_MIN (0.7), a threshold written down before the run.

Robust anchor (plan R7): every PCM evaluation runs at each of model.robust_anchors (bottom, center, top). The objective is the MEAN
paired gain over anchors (and years); the worst-anchor gain is kept for the rejection rule (worst < 0 or inside the band -> rejected).
"""

from functools import lru_cache

import pandas as pd

from src.design.space import load_space

REP_YEAR = {0: 2018, 1: 2017, 2: 2018}
CHEAP_DT_S = 150
CHEAP_FULL_RHO_MIN = 0.7
ARRANGEMENTS = ("single-layer", "staggered", "radial")


@lru_cache(maxsize=None)
def _v():
    return load_space()["variables"]


def r_bounds():
    v = _v()["inner_radius_m"]
    return float(v["min"]), float(v["max"])


def f_bounds():
    v = _v()["pcm_volume_fraction"]
    return float(v["min"]), float(v["max"])


def flow_fixed() -> float:
    v = _v()["flow_rate_kg_s"]
    assert v["min"] == v["max"], "rebuild expects a fixed flow (plan R6)"
    return float(v["min"])


def anchors():
    return tuple(load_space()["model"]["robust_anchors"])


def full_dt():
    return float(load_space()["model"]["report_timestep_s"])


def fidelity_years(cluster_id: int, purpose: str, fidelity: str):
    from src.weather import roles
    if fidelity == "cheap":
        assert purpose == "explore", "the cheap fidelity is defined on the explore years only"
        return [REP_YEAR[cluster_id]]
    return roles.years_for(purpose)


def fidelity_dt(fidelity: str) -> float:
    return CHEAP_DT_S if fidelity == "cheap" else full_dt()


def design_from_unit(u0, u1, u2):
    """u in [0,1)^3 -> (R_in, fraction, arrangement) over the box."""
    (r0, r1), (f0, f1) = r_bounds(), f_bounds()
    return r0 + (r1 - r0) * u0, f0 + (f1 - f0) * u1, ARRANGEMENTS[min(int(u2 * 3), 2)]


def hygiene(hourly: pd.DataFrame, threshold_C: float = 60.0) -> dict:
    """Plan R9: share of days on which the stored water reached >= 60 C for >= 1 h, and the longest run of days without it.
    Operationalised on the hottest stored layer: an hour counts if the top-node temperature stayed >= threshold for the whole hour
    (hourly minimum T_w_min_C); a day counts if it has at least one such hour."""
    day = hourly.assign(ok=hourly["T_w_min_C"] >= threshold_C).groupby(hourly["local_date"] if "local_date" in hourly else hourly.index // 24).ok.any()
    best = cur = 0
    for ok in day.to_numpy():
        cur = 0 if ok else cur + 1
        best = max(best, cur)
    return {"hyg_share_days": float(day.mean()), "hyg_longest_gap_days": int(best)}
