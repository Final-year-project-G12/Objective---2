"""
scripts/g21_sizing_study.py
==============================
Plan section 6A item 3: a clearly labelled SUPPLEMENTARY sizing-sensitivity diagnostic. The fixed system is 50 L on 1.5 m2 (33.3 L/m2), below the 40-100 L/m2 of
IS 12976:2023 section 4.2. This script asks whether the PCM benefit of the frozen chosen design changes when ONLY the tank volume changes (in memory, through
system_config_overrides; no config file is edited and tank volume is never an optimisation variable). Collector (1.5 m2) and demand (300 L/day) stay fixed.

Tank volumes: 50 L (the fixed case), 60 L (40 L/m2), 75 L (50 L/m2), 112.5 L (75 L/m2, the standard's f-chart reference), 150 L (100 L/m2).
Two variants per volume, for the frozen chosen design of the regime (results/g10_selection_r<c>.json):
  same_fraction  the PCM volume fraction of the tank is kept (capsule count scales with the tank, PCM mass scales)
  same_count     the capsule count is kept (PCM mass fixed, so the PCM share shrinks as the tank grows)
Every case is paired against the exact water-only tank of the SAME volume, flow and weather year. Explore years 2016-2020 only (no select or test year).
Metrics reported: g_window, g_annual, d_overheat, PCM and water peaks, feasibility (65 C / 75 C), and the plain-tank solar fraction.
The result is a diagnostic of direction and size, not a design recommendation, and it uses the 10-node tank at the chosen stack anchor.

Usage: python scripts/g21_sizing_study.py <cluster_id>   ->  results/g21_sizing_r<c>.csv
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.design.schema import DesignVector
from src.design.space import capsule_outer_volume_m3, geometry_bounds, load_space, wall_m
from src.optimize.evaluate import _weather
from src.simulation.run_case import run_case
from src.weather import roles

OUT = Path("results")
SP = load_space()
VOLUMES_L = (50.0, 60.0, 75.0, 112.5, 150.0)


def dv_for(r, n, q, arr):
    return DesignVector(capsule_diameter_m=2.0 * (r + wall_m()), n_capsule=int(n), flow_rate_kg_s=float(q), capsule_arrangement=arr)


def kw(cid, y, vol_l):
    return dict(design_bounds=geometry_bounds(), weather=_weather(cid, y, "explore"), tank_model=SP["model"]["tank_model"], n_nodes=SP["model"]["n_nodes"],
                stack_anchor=SP["model"]["stack_anchor"], compute_tes_metrics=True, night_day_stride=0,
                system_config_overrides={"tank": {"volume_L": float(vol_l)}})


def main(cid):
    ch = json.load(open(OUT / f"g10_selection_r{cid}.json", encoding="utf-8"))["chosen"]
    pcm, r, f0, q, arr = ch["pcm"], float(ch["R_in_m"]), float(ch["fraction"]), float(ch["flow"]), ch["arrangement"]
    n_fixed = int(ch["N"])
    v_cap = capsule_outer_volume_m3(r)
    rows = []
    for vol in VOLUMES_L:
        n_frac = int(round(f0 * (vol / 1000.0) / v_cap))
        for variant, n in (("same_fraction", n_frac), ("same_count", n_fixed)):
            row = {"regime": cid, "pcm": pcm, "arrangement": arr, "tank_L": vol, "L_per_m2": vol / 1.5, "variant": variant, "N": n, "R_in_mm": r * 1000, "flow": q}
            per = []
            for y in roles.years_for("explore"):
                res = run_case("rajasthan", cid, pcm, dv_for(r, n, q, arr), **kw(cid, y, vol))
                if not res["valid"]:
                    row.update({"valid": False, "reason": res.get("reason", "")})
                    per = []
                    break
                pl = run_case("rajasthan", cid, None, dv_for(r, n, q, arr), **kw(cid, y, vol))
                m, t, mp, tp = res["metrics"], res["tes"], pl["metrics"], pl["tes"]
                per.append((t["E_del45_window_kWh"] - tp["E_del45_window_kWh"], t["E_del45_annual_kWh"] - tp["E_del45_annual_kWh"],
                            (m["shield_water_h"] + m["shield_pcm_h"]) - mp["shield_water_h"], m["max_pcm_temp_C"], m["max_water_temp_C"],
                            mp["solar_fraction"], m["pcm_mass_kg"]))
            if per:
                a = np.array(per)
                row.update({"valid": True, "g_window": a[:, 0].mean(), "g_window_sd": a[:, 0].std(ddof=1), "g_annual": a[:, 1].mean(), "d_overheat": a[:, 2].mean(),
                            "t_pcm_max": a[:, 3].max(), "t_water_max": a[:, 4].max(), "plain_solar_fraction": a[:, 5].mean(), "pcm_mass_kg": a[0, 6],
                            "feasible_65_75": bool(a[:, 3].max() <= 65.0 and a[:, 4].max() <= 75.0)})
            rows.append(row)
            print(f"{vol:6.1f} L {variant:13s} N={n:3d} valid={row.get('valid')} g_window={row.get('g_window')}", flush=True)
            pd.DataFrame(rows).to_csv(OUT / f"g21_sizing_r{cid}.csv", index=False)


if __name__ == "__main__":
    main(int(sys.argv[1]))
