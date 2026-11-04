"""
src/optimize/selection_funnel.py
===================================
The S0 -> S1 -> S2 selection funnel and tie-break from her report's
sections on choosing the deployable design per regime.

STAGES
  S0  every candidate on the final Pareto fronts, across all PCMs and all
      arrangements for that regime.
  S1  SAFETY-FEASIBLE on the SELECT years (2021-2023), re-simulated for
      real (never surrogate-predicted): "Hard constraints on select years
      2021-2023: PCM peak at most 65 C, water peak at most 75 C."
  S2  candidates whose primary objective (g_window) is not
      distinguishable from the best one, given the repeatability band.

TIE-BREAK, applied within S2 in this order (hers, verbatim): "Pick the
lowest PCM mass, then fewest capsules, then the larger margin to 65 C."

THE BAND IS THE POINT. A difference smaller than the repeatability band is
not a result, and her report is explicit about reporting it that way:
"Candidates the band cannot tell apart are reported as indistinguishable,
not as a win." So S2 keeps every candidate within one band of the leader
and the tie-break decides among them on physical grounds (less material,
fewer parts, more thermal margin) rather than on a difference the
measurement cannot support.

The band itself comes from src/verify/repeatability.py.
"""

import numpy as np
import pandas as pd

PCM_PEAK_LIMIT_C = 65.0
WATER_PEAK_LIMIT_C = 75.0


def s1_safety_feasible(confirmed: pd.DataFrame) -> pd.DataFrame:
    """S1: keep candidates that respect both hard limits in EVERY select
    year. A candidate that passes on average but breaches in one year is
    not feasible -- the limit is per-year, not per-mean."""
    ok = confirmed[confirmed["valid"]].copy()
    per_design = ok.groupby(_design_keys(ok), dropna=False).agg(
        max_pcm_temp_C=("max_pcm_temp_C", "max"),
        max_water_temp_C=("max_water_temp_C", "max"),
        n_years=("year", "nunique"),
        g_window_kWh=("g_window_kWh", "mean"),
        g_window_min=("g_window_kWh", "min"),
        g_annual_kWh=("g_annual_kWh", "mean"),
        d_overheat_h=("d_overheat_h", "mean"),
        pcm_mass_kg=("pcm_mass_kg", "mean"),
        residual_pct=("residual_pct_of_collector", "max"),
    ).reset_index()
    feasible = per_design[(per_design["max_pcm_temp_C"] <= PCM_PEAK_LIMIT_C)
                          & (per_design["max_water_temp_C"] <= WATER_PEAK_LIMIT_C)]
    return feasible.copy()


def _design_keys(df):
    keys = ["cluster_id", "pcm_name", "arrangement", "n_capsule",
            "capsule_diameter_m", "flow_rate_kg_s"]
    return [k for k in keys if k in df.columns]


def s2_indistinguishable(feasible: pd.DataFrame, band_kWh: float,
                          objective: str = "g_window_kWh") -> pd.DataFrame:
    """S2: everything within one repeatability band of the best."""
    if feasible.empty:
        return feasible
    best = feasible[objective].max()
    keep = feasible[feasible[objective] >= best - band_kWh].copy()
    keep["gap_to_best_kWh"] = best - keep[objective]
    keep["within_band"] = True
    return keep


def tie_break(s2: pd.DataFrame) -> pd.DataFrame:
    """Her rule, in order: lowest PCM mass, then fewest capsules, then the
    largest margin to the 65 C PCM limit."""
    if s2.empty:
        return s2
    out = s2.copy()
    out["margin_to_65C"] = PCM_PEAK_LIMIT_C - out["max_pcm_temp_C"]
    return out.sort_values(
        by=["pcm_mass_kg", "n_capsule", "margin_to_65C"],
        ascending=[True, True, False]).reset_index(drop=True)


def select_per_regime(confirmed: pd.DataFrame, band_by_regime: dict,
                       objective: str = "g_window_kWh"):
    """Runs the whole funnel per regime. Returns (chosen_df, audit_df).

    `band_by_regime` maps cluster_id -> repeatability band in kWh.
    """
    chosen_rows, audit_rows = [], []
    for cid, g in confirmed.groupby("cluster_id"):
        band = float(band_by_regime.get(cid, 0.0))
        s0_n = len(g.groupby(_design_keys(g), dropna=False))
        feas = s1_safety_feasible(g)
        s2 = s2_indistinguishable(feas, band, objective)
        ranked = tie_break(s2)

        audit_rows.append({
            "cluster_id": cid, "band_kWh": band,
            "S0_candidates": s0_n, "S1_safety_feasible": len(feas),
            "S2_within_band": len(s2),
            "best_objective_kWh": float(feas[objective].max()) if len(feas) else float("nan"),
            "indistinguishable": len(s2) > 1,
        })
        if len(ranked):
            top = ranked.iloc[0].to_dict()
            top["cluster_id"] = cid
            top["n_indistinguishable"] = len(s2)
            top["band_kWh"] = band
            chosen_rows.append(top)

    return pd.DataFrame(chosen_rows), pd.DataFrame(audit_rows)
