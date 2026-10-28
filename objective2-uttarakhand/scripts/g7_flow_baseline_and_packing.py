"""
scripts/g7_flow_baseline_and_packing.py
==========================================
G7 supplement (O2, 2026-10-26):
 1. Plain-tank (water-only) flow sweep on the multi-node tank, explore years 2018/2019, so the flow block of
    g7_sensitivity can be read as PCM gain at the SAME flow (flow also changes the plain tank itself).
 2. Geometric packing limit: the largest capsule volume fraction the packing engine accepts per radius and
    arrangement, ignoring the 20 % cap (is the cap geometric or administrative?).
Writes results/g7_plain_flow_baseline.csv and results/g7_max_packing_fraction.csv.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.design.geometry import compute_geometry
from src.design.schema import DesignVector
from src.io_utils import load_system_config
from src.simulation.run_case import run_case
from src.weather import roles
from src.weather.inventory import CURRENT_MEDOIDS

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g7_sensitivity as g7

OUT = Path("results")


def plain_flow_sweep():
    bounds = g7.permissive_bounds()
    rows = []
    for cid, point in CURRENT_MEDOIDS.items():
        for year in g7.YEARS:
            w = roles.load_point_year("uttarakhand", cid, point, year, purpose="explore")
            for fl in g7.FLOWS:
                dv = g7.design(0.020, 10, fl, "staggered")
                o = run_case("uttarakhand", cid, None, dv, design_bounds=bounds, weather=w, tank_model="multinode",
                             compute_tes_metrics=True, night_day_stride=g7.NIGHT_STRIDE)
                m, t = o["metrics"], o["tes"]
                rows.append({"regime": cid, "year": year, "flow": fl, "useful_energy_kWh": m["useful_energy_kWh"],
                             "solar_fraction": m["solar_fraction"], "E_del45_annual_kWh": t["E_del45_annual_kWh"],
                             "tau_hold_mean_h": t["tau_hold_mean_h"], "tau_serve_mean_h": t["tau_serve_mean_h"],
                             "max_water_C": m["max_water_temp_C"]})
                print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(OUT / "g7_plain_flow_baseline.csv", index=False)


def max_packing():
    cfg = load_system_config()
    bounds = g7.permissive_bounds()
    bounds = {**bounds, "pcm_volume_fraction": {"min": 0.0, "max": 1.0}}
    v_tank = cfg["tank"]["volume_L"] / 1000.0
    rows = []
    for rmm in g7.R_LEVELS_MM:
        r = rmm / 1000.0
        for arr in g7.ARRANGEMENTS:
            best_n, best_f, reason = 0, 0.0, ""
            lo, hi = 1, int(0.74 * v_tank / (4.0 / 3.0 * 3.14159265 * (r + g7.WALL) ** 3)) + 1
            while lo <= hi:                                   # largest feasible N (feasibility is monotone in N)
                mid = (lo + hi) // 2
                gm = compute_geometry(g7.design(r, mid, 0.03, arr), cfg, bounds)
                if gm["valid"]:
                    best_n, best_f, lo = mid, gm["pcm_volume_fraction"], mid + 1
                else:
                    reason, hi = gm["reason"], mid - 1
            rows.append({"R_in_mm": rmm, "arrangement": arr, "max_feasible_N": best_n,
                         "max_feasible_fraction": best_f, "first_failure_reason": reason})
    pd.DataFrame(rows).to_csv(OUT / "g7_max_packing_fraction.csv", index=False)
    print(pd.DataFrame(rows).to_string())


if __name__ == "__main__":
    max_packing()
    plain_flow_sweep()
