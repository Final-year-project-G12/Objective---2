"""
src/metrics/tes_metrics.py
=============================
Thermal-energy-storage metrics ported from Manvitha's Rajasthan report
(section 3.5 / Table 10). ADDITIVE ONLY: Tamil Nadu's existing metrics
(useful_energy_kWh, solar_fraction, etc. -- src/simulation/run_case.py)
are unchanged and remain the metrics every current output file/robustness
check uses. These are extra, optional diagnostic columns for the new
NSGA-II/active-learning chain, computed from the same `hourly` DataFrame
`run_case()` already returns (plus, for tau_hold/tau_serve, one short extra
"evening coast" simulation -- see below).

We do not have Manvitha's actual formulas (only the report's one-line
English definitions, reproduced in each docstring below) -- these are our
own literal translations, documented so a reader can check the
interpretation against the report's wording directly.

Delivery/comfort target: system_config["delivery"]["target_temp_C"], which
is 45.0 C for Tamil Nadu (confirmed in configs/system_config_shared.yaml)
-- the same value Rajasthan's report uses, so no window/threshold mismatch.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

WINDOW_START_HOUR = 18   # 18:00
WINDOW_END_HOUR = 9      # 09:00 next day -- "18:00-09:00" wraps past midnight


def _in_window(hour_of_day_series: pd.Series) -> pd.Series:
    """True for hours in [18:00, 24:00) U [0:00, 9:00) -- the evening/
    overnight 'g_window' the report uses as its primary metric window."""
    h = hour_of_day_series
    return (h >= WINDOW_START_HOUR) | (h < WINDOW_END_HOUR)


def draw_mass_table(demand) -> np.ndarray:
    """The demand model's 24-point draw curve as an array indexed by
    integer hour-of-day.

    Exists because the obvious `hour_of_day.map(demand.draw_mass_kg_for_hour)`
    makes 8760 Python calls (each running its own np.searchsorted) per
    metric evaluation, which -- now that a simulated year itself costs
    ~0.2 s -- cost more than the physics it is summarizing. The table is
    built from the same method, so the values are identical; only the
    lookup changes.
    """
    return np.array([demand.draw_mass_kg_for_hour(h) for h in range(24)], dtype=float)


def draw_mass_per_hour(hourly: pd.DataFrame, demand) -> np.ndarray:
    """Per-row draw mass (kg), vectorized. draw_mass_kg_for_hour() rounds
    and mods its argument internally, so rounding here matches it exactly."""
    idx = np.mod(np.round(hourly["hour_of_day"].to_numpy(dtype=float)).astype(int), 24)
    return draw_mass_table(demand)[idx]


def e_del_target(hourly: pd.DataFrame, demand, mains_temp_C: float, cp_w: float,
                  target_C: float, window_only: bool = False) -> float:
    """E_del,target (report section 3.5, 'E_del,45'):
    "Sum of m_dot*cp*(min(T_out, target) - T_mains) over draws."
    Annual (window_only=False) or restricted to the 18:00-09:00 window.

    hourly must have 'hour_of_day' and a delivery-temperature column
    ('T_w_C', which is the TOP/outlet node for the multi-node model and the
    single lumped node for the single-node model -- both are the correct
    "water actually leaving the tank" temperature)."""
    h = hourly["hour_of_day"]
    mask = (_in_window(h) if window_only else pd.Series(True, index=hourly.index)).to_numpy()
    draw_kg = draw_mass_per_hour(hourly, demand)
    delivered = np.clip(np.minimum(hourly["T_w_C"].to_numpy(dtype=float), target_C) - mains_temp_C,
                        0.0, None)
    e_w = draw_kg * cp_w * delivered
    return float(e_w[mask].sum() / 3.6e6)   # J -> kWh


def e_stored(final_T_w_C: float, m_water_kg: float, cp_w: float, mains_temp_C: float,
             final_h_pcm_J_kg: float = 0.0, h_pcm_at_mains_J_kg: float = 0.0,
             m_pcm_kg: float = 0.0) -> float:
    """E_stored (report: 'Energy above mains temperature held by water and
    PCM'), evaluated at one instant (pass the final hour's state, or any
    other snapshot the caller wants)."""
    e_water_J = m_water_kg * cp_w * max(final_T_w_C - mains_temp_C, 0.0)
    e_pcm_J = m_pcm_kg * max(final_h_pcm_J_kg - h_pcm_at_mains_J_kg, 0.0)
    return (e_water_J + e_pcm_J) / 3.6e6


def gain_vs_plain(hourly_pcm: pd.DataFrame, hourly_plain: pd.DataFrame, demand,
                   mains_temp_C: float, cp_w: float, target_C: float,
                   window_only: bool) -> float:
    """g_window / g_annual (report: 'E_del,target, PCM tank minus water-only
    tank at the same flow, weather and demand'). Caller must have run BOTH
    the PCM design and a paired water-only (n_capsule=0) design at the same
    flow/regime/weather/demand -- this function only takes the difference,
    it does not run anything."""
    e_pcm = e_del_target(hourly_pcm, demand, mains_temp_C, cp_w, target_C, window_only)
    e_plain = e_del_target(hourly_plain, demand, mains_temp_C, cp_w, target_C, window_only)
    return e_pcm - e_plain


def shield_hours(hourly: pd.DataFrame) -> int:
    """Hours in the year with at least one shield activation (water-side
    bypass or, for a PCM design, PCM-side charge block)."""
    return int((hourly["shield_activations"] > 0).sum())


def d_overheat(hourly_pcm: pd.DataFrame, hourly_plain: pd.DataFrame) -> dict:
    """d_overheat (report: 'Shield hours (water + PCM side) of the PCM tank
    minus the water-only tank's water-side hours. Positive by construction
    because the water-only tank has no PCM-side throttle.')  Also returns
    the split, same as the report's d_shield_water_h / shield_pcm_h."""
    pcm_hours = shield_hours(hourly_pcm)
    plain_hours = shield_hours(hourly_plain)
    return {
        "d_overheat_h": pcm_hours - plain_hours,
        "shield_hours_pcm_tank": pcm_hours,
        "shield_hours_plain_tank": plain_hours,
    }


@dataclass
class EveningScenarioResult:
    tau_hold_45_h: float
    tau_serve_45_h: float
    serve_frac_45: float


def evening_scenario(run_year_fn, weather_hourly: pd.DataFrame, demand_model, mains_temp_C: float,
                      design_runtime, pcm_props, system_config: dict, start_hour_index: int,
                      target_C: float = 45.0, max_hold_h: int = 72, max_serve_h: int = 15):
    """tau_hold,45 / tau_serve,45 / serve_frac_45 (report section 3.5):

      tau_hold,45 = "Hours from 18:00 that the tank alone (no draw, no sun)
                     keeps the outlet at or above 45 C, censored at 72 h."
      tau_serve / serve_frac_45 = "With the project demand profile and no
                     sun: hours from 18:00 until end-of-hour outlet first
                     drops below 45 C (max 15); share of drawn volume at or
                     above 45 C."

    Both need a DEDICATED short simulation starting from the real annual
    run's state at `start_hour_index` (an 18:00 hour), with GHI forced to
    zero (no sun) for every subsequent hour -- not post-processing of the
    main annual run, which has normal day/night cycling. This function
    builds that zero-GHI tail scenario and runs it twice (demand=0 for
    tau_hold, real demand for tau_serve), reusing whichever run_year
    function (single- or multi-node) the caller passes in.

    `run_year_fn` is tank_model.run_year or
    tank_model_multinode.run_year_multinode -- same signature either way.
    """
    tail_len = max(max_hold_h, max_serve_h) + 1
    tail = weather_hourly.iloc[start_hour_index:start_hour_index + tail_len].copy()
    if len(tail) < tail_len:
        # wrap around the year if the evening falls near year-end
        wrap = weather_hourly.iloc[:tail_len - len(tail)]
        tail = pd.concat([tail, wrap], ignore_index=True)
    tail["GHI_Wm2"] = 0.0
    tail["GHI_clearsky_Wm2"] = 0.0

    from src.simulation.demand_profile import DemandModel

    zero_demand_df = pd.DataFrame({"hour": range(24), "draw_fraction": 0.0, "draw_volume_L": 0.0,
                                    "draw_mass_kg": 0.0})
    zero_demand = DemandModel(zero_demand_df)

    res_hold = run_year_fn(tail, zero_demand, mains_temp_C, design_runtime, pcm_props,
                            system_config, record_hourly=True)
    hold_series = res_hold.hourly["T_w_C"] >= target_C
    tau_hold = float(hold_series.cumprod().sum())  # consecutive hours from the start staying >= target
    tau_hold = min(tau_hold, max_hold_h)

    res_serve = run_year_fn(tail, demand_model, mains_temp_C, design_runtime, pcm_props,
                             system_config, record_hourly=True)
    serve_series = (res_serve.hourly["T_w_C"] >= target_C).iloc[:max_serve_h]
    tau_serve = float(serve_series.cumprod().sum())

    h = res_serve.hourly.iloc[:max_serve_h]
    draw_mass = h["hour_of_day"].map(lambda hh: demand_model.draw_mass_kg_for_hour(hh))
    total_drawn = float(draw_mass.sum())
    served_at_target = float(draw_mass[h["T_w_C"] >= target_C].sum())
    serve_frac = served_at_target / total_drawn if total_drawn > 0 else float("nan")

    return EveningScenarioResult(tau_hold_45_h=tau_hold, tau_serve_45_h=tau_serve, serve_frac_45=serve_frac)
