"""
src/optimize/evaluate.py
===========================
O2 G8 - the ONE function that turns a design into paired objectives by running the real simulator (multi-node tank, N = 10)
over the weather years of a role. Nothing here is a surrogate. Common-plant rebuild (2026-11-23): two fidelities (cheap 150 s on the
representative explore year; full 37.5 s on every year of the role) and the robust anchor objective (mean over bottom / centre / top),
see src/design/box.py.

Per weather year the gains are paired against the water-only tank at the same flow (baseline.plain_at):
  g_window   E_del,45 in 18:00-09:00 (in-situ) minus the plain tank's        [kWh/yr]   f1, primary
  g_annual   annual E_del,45 minus the plain tank's                          [kWh/yr]   f2
  g_useful   annual useful energy minus the plain tank's                     [kWh/yr]   (old metric, for reference)
  d_overheat (shield-water h + shield-PCM h) minus the plain tank's shield-water h   [h/yr]   f3 (lower is better)
  t_pcm_max  peak PCM temperature [C]; the design is FEASIBLE only if it is <= 65 C in every year (user decision)
Night hold/serve scenarios are skipped here (night_day_stride=0); they are computed for finalists.
"""

from functools import lru_cache

import numpy as np
import pandas as pd

from src.design.constraints import check_design
from src.design.space import geometry_bounds, load_space, to_design
from src.io_utils import load_system_config
from src.optimize.baseline import plain_at, simulate_plain
from src.simulation.run_case import run_case
from src.weather import roles
from src.weather.inventory import CURRENT_MEDOIDS

OBJECTIVE_KEYS = ("g_window", "g_annual", "g_useful", "d_overheat")


@lru_cache(maxsize=64)
def _weather(cluster_id: int, year: int, purpose: str):
    return roles.load_point_year("rajasthan", cluster_id, CURRENT_MEDOIDS[cluster_id], year, purpose)


def evaluate_design(cluster_id, pcm, r_in_m, fraction, flow, arrangement, purpose="explore", years=None, fidelity=None,
                    anchors=None, n_nodes=None, record_hygiene=False, system_config_overrides=None):
    """Simulate one design over the weather years of `purpose` at every robust anchor (plan R7) and pair it with the water-only tank.

    fidelity: "cheap" (dt 150 s, the regime's representative explore year) or "full" (dt 37.5 s, every year of the role); default
    cheap for explore, full otherwise (src/design/box.py). `years` overrides the year list. Objectives are MEANS over years and anchors;
    the worst-anchor mean gain (g_window_worst_anchor) is kept for the rejection rule. Feasible only if the PCM and water peaks stay
    within the limits in every year at every anchor."""
    from src.design import box
    fidelity = fidelity or ("cheap" if purpose == "explore" else "full")
    years = list(years) if years is not None else box.fidelity_years(cluster_id, purpose, fidelity)
    dt = box.fidelity_dt(fidelity)
    anchors = tuple(anchors) if anchors is not None else box.anchors()
    dv = to_design(r_in_m, fraction, flow, arrangement)
    cfg = load_system_config()
    out = {"cluster": cluster_id, "pcm": pcm, "R_in_m": r_in_m, "fraction_req": fraction, "flow": flow,
           "arrangement": arrangement, "N": dv.n_capsule, "fidelity": fidelity, "dt_s": dt}
    geom = check_design(dv, cfg, geometry_bounds())
    out["valid"], out["reason"] = bool(geom["valid"]), geom.get("reason") or ""
    if not geom["valid"]:
        return out
    out["fraction"] = geom["pcm_volume_fraction"]
    sp = load_space()
    ov = {"solver": {"timestep_s": dt}}
    if system_config_overrides:
        ov.update(system_config_overrides)
    per_year = []
    for y in years:
        if system_config_overrides or n_nodes is not None:      # perturbed model: the twin gets the same perturbation
            p = simulate_plain(cluster_id, y, flow, purpose, dt, n_nodes, system_config_overrides)
        else:
            p = plain_at(cluster_id, y, flow, purpose, dt)
        for anc in anchors:
            r = run_case("rajasthan", cluster_id, pcm, dv, design_bounds=geometry_bounds(), weather=_weather(cluster_id, y, purpose),
                         tank_model=sp["model"]["tank_model"], n_nodes=n_nodes or sp["model"]["n_nodes"], stack_anchor=anc,
                         compute_tes_metrics=True, night_day_stride=0, record_hourly=record_hygiene, system_config_overrides=ov)
            m, t = r["metrics"], r["tes"]
            row = {"year": y, "anchor": anc,
                   "g_window": t["E_del45_window_kWh"] - p["E_del45_window_kWh"],
                   "g_annual": t["E_del45_annual_kWh"] - p["E_del45_annual_kWh"],
                   "g_useful": m["useful_energy_kWh"] - p["useful_energy_kWh"],
                   "d_overheat": (m["shield_water_h"] + m["shield_pcm_h"]) - p["shield_water_h"],
                   "t_pcm_max": m["max_pcm_temp_C"], "t_water_max": m["max_water_temp_C"],
                   "hours_over_limit": m["hours_over_limit"], "residual_pct": m["residual_pct_of_collector"],
                   "pcm_mass_kg": m["pcm_mass_kg"], "E_del45_window_kWh": t["E_del45_window_kWh"],
                   "plain_E_del45_window_kWh": p["E_del45_window_kWh"]}
            if record_hygiene:
                from src.design.box import hygiene
                row.update(hygiene(r["hourly"]))
            per_year.append(row)
    out["per_year"] = per_year
    py = pd.DataFrame(per_year)
    for k in OBJECTIVE_KEYS:
        out[k] = float(py[k].mean())
        yearly = py.groupby("year")[k].mean()
        out[k + "_sd"] = float(yearly.std(ddof=1)) if len(yearly) > 1 else 0.0
    by_anchor = py.groupby("anchor")["g_window"].mean()
    out["g_window_worst_anchor"] = float(by_anchor.min())
    out["worst_anchor"] = str(by_anchor.idxmin())
    for a, v in by_anchor.items():
        out[f"g_window_{a}"] = float(v)
    out["t_pcm_max"] = float(py.t_pcm_max.max())
    out["t_water_max"] = float(py.t_water_max.max())
    out["pcm_mass_kg"] = float(py.pcm_mass_kg.iloc[0])
    out["residual_pct"] = float(py.residual_pct.max())
    out["feasible"] = bool(out["t_pcm_max"] <= sp["constraints"]["pcm_peak_limit_C"]
                           and out["t_water_max"] <= sp["constraints"]["water_peak_limit_C"])
    return out


def flatten(res: dict) -> dict:
    """One CSV-friendly row (drops the per-year list)."""
    return {k: v for k, v in res.items() if k != "per_year"}


def evaluate_night(cluster_id, pcm, r_in_m, fraction, flow, arrangement, purpose, years=None, stride=15, dt=None, anchor=None):
    """Night hold/serve scenarios (WP1 B) for a design AND its same-flow water-only twin, run exactly (no grid), on the
    given weather role. Returns per-year dict list with the PCM tank's values and the paired gains (PCM minus plain)."""
    years = list(years) if years is not None else roles.years_for(purpose)
    dv = to_design(r_in_m, fraction, flow, arrangement)
    sp = load_space()
    out = []
    for y in years:
        kw = dict(design_bounds=geometry_bounds(), weather=_weather(cluster_id, y, purpose),
                  tank_model=sp["model"]["tank_model"], n_nodes=sp["model"]["n_nodes"],
                  stack_anchor=anchor or sp["model"]["stack_anchor"], compute_tes_metrics=True, night_day_stride=stride,
                  system_config_overrides={"solver": {"timestep_s": dt}} if dt else None)
        a = run_case("rajasthan", cluster_id, pcm, dv, **kw)
        b = run_case("rajasthan", cluster_id, None, dv, **kw)
        ta, tb, ma, mb = a["tes"], b["tes"], a["metrics"], b["metrics"]
        row = {"year": y}
        for k in ("tau_hold_mean_h", "tau_serve_mean_h", "serve_frac_45_mean", "serve_T_out_min_mean_C"):
            row[k] = ta.get(k, np.nan)
            row["plain_" + k] = tb.get(k, np.nan)
            row["gain_" + k] = ta.get(k, np.nan) - tb.get(k, np.nan)
        row.update({"g_window": ta["E_del45_window_kWh"] - tb["E_del45_window_kWh"],
                    "g_annual": ta["E_del45_annual_kWh"] - tb["E_del45_annual_kWh"],
                    "g_useful": ma["useful_energy_kWh"] - mb["useful_energy_kWh"],
                    "d_overheat": (ma["shield_water_h"] + ma["shield_pcm_h"]) - mb["shield_water_h"],
                    "shield_water_h": ma["shield_water_h"], "shield_pcm_h": ma["shield_pcm_h"],        # issue 4: like-for-like split, reported beside f3
                    "plain_shield_water_h": mb["shield_water_h"],
                    "t_pcm_max": ma["max_pcm_temp_C"], "t_water_max": ma["max_water_temp_C"],
                    "sf_pcm": ma["solar_fraction"], "sf_plain": mb["solar_fraction"],
                    "residual_pct": ma["residual_pct_of_collector"], "pcm_mass_kg": ma["pcm_mass_kg"], "N": dv.n_capsule})
        out.append(row)
    return out
