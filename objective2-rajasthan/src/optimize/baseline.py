"""
src/optimize/baseline.py
===========================
The paired baseline: every PCM design is compared with a WATER-ONLY tank at the SAME flow, weather year, demand, shield, tank model
and time step (user decision 2026-10-26, plan section 5 "pair against the water-only tank").

Common-plant rebuild (2026-11-23): flow is fixed at 0.030 kg/s (plan R6), so the legacy 17-flow PCHIP grid is replaced by EXACT
water-only runs at that flow, one per (role, time step, regime, year), cached in results/plain_baseline_<role>_dt<dt>_r<c>.csv.
The water-only tank has no capsules, so it does not depend on the stack anchor or any capsule variable (negative control, tests).
A year missing from the cache is simulated exactly in memory (never interpolated). Test and report years can only be loaded under the
lock (src/weather/roles.py), so their baselines are built inside the locked run.
"""

from functools import lru_cache
from pathlib import Path

import pandas as pd

from src.design.space import geometry_bounds, load_space, to_design
from src.simulation.run_case import run_case
from src.weather import roles
from src.weather.inventory import CURRENT_MEDOIDS

OUT_DIR = Path(__file__).resolve().parents[2] / "results"
METRICS = ["useful_energy_kWh", "E_del45_window_kWh", "E_del45_annual_kWh", "shield_water_h", "max_water_temp_C"]


def _dt_tag(dt) -> str:
    return f"{float(dt):g}".replace(".", "p")


def grid_path(purpose: str, cluster_id: int, dt=150) -> Path:
    return OUT_DIR / f"plain_baseline_{purpose}_dt{_dt_tag(dt)}_r{cluster_id}.csv"


def simulate_plain(cluster_id: int, year: int, flow: float, purpose: str, dt, n_nodes=None, overrides=None) -> dict:
    sp = load_space()
    w = roles.load_point_year("rajasthan", cluster_id, CURRENT_MEDOIDS[cluster_id], year, purpose)
    ov = {"solver": {"timestep_s": dt}}
    if overrides:
        ov.update(overrides)
    o = run_case("rajasthan", cluster_id, None, to_design(0.02, 0.05, float(flow), "staggered"), design_bounds=geometry_bounds(),
                 weather=w, tank_model="multinode", n_nodes=n_nodes or sp["model"]["n_nodes"], compute_tes_metrics=True,
                 night_day_stride=0, record_hourly=False, system_config_overrides=ov)
    m, t = o["metrics"], o["tes"]
    return {"useful_energy_kWh": m["useful_energy_kWh"], "E_del45_window_kWh": t["E_del45_window_kWh"],
            "E_del45_annual_kWh": t["E_del45_annual_kWh"], "shield_water_h": m["shield_water_h"],
            "max_water_temp_C": m["max_water_temp_C"]}


def build_plain(cluster_id: int, purpose: str, dt, years=None, flow=None) -> pd.DataFrame:
    from src.design.box import flow_fixed
    flow = flow_fixed() if flow is None else flow
    rows = [{"regime": cluster_id, "year": y, "flow": flow, "dt_s": float(dt), **simulate_plain(cluster_id, y, flow, purpose, dt)}
            for y in (years or roles.years_for(purpose))]
    df = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(grid_path(purpose, cluster_id, dt), index=False)
    return df


@lru_cache(maxsize=None)
def _cached(purpose: str, cluster_id: int, dt: float):
    p = grid_path(purpose, cluster_id, dt)
    return pd.read_csv(p) if p.exists() else None


@lru_cache(maxsize=None)
def _exact(cluster_id: int, year: int, flow: float, purpose: str, dt: float):
    return simulate_plain(cluster_id, year, flow, purpose, dt)


def plain_at(cluster_id: int, year: int, flow: float, purpose: str = None, dt=150) -> dict:
    """Water-only tank metrics for (regime, year) at `flow` and time step `dt`: from the cache when present, else simulated exactly."""
    purpose = purpose or roles.role_of(year)
    df = _cached(purpose, cluster_id, float(dt))
    if df is not None:
        g = df[(df.year == year) & ((df.flow - flow).abs() < 1e-9)]
        if len(g) == 1:
            return {m: float(g[m].iloc[0]) for m in METRICS}
    return _exact(cluster_id, int(year), float(flow), purpose, float(dt))
