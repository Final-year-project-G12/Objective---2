"""
scripts/g7_sensitivity.py
============================
G7 (O2, plan WP3, 2026-10-26) - bounded sensitivity study that precedes any optimisation.
One regime per invocation (run the three in parallel):  python scripts/g7_sensitivity.py <cluster_id>

Weather: EXPLORE years only (2018, 2019) through src/weather/roles.py; no select/test year is touched.
PCMs: Objective 1's top-3 for the regime (decision D2). Reference tank: plain water-only, same weather,
demand, shield and tank model (paired baseline).

Blocks
  A thickness   inner radius 10,15,20,25,30,40 mm at CONSTANT PCM mass (inner-PCM volume = 5 % of the tank,
                count = round(target / V_in)); staggered, 0.030 kg/s; single-node AND multi-node tank.
  B count       R_in = 20 mm, capsule volume fraction 0.5 ... 20 % of the tank (outer volume); staggered, 0.030 kg/s.
  C flow        0.010 ... 0.050 kg/s at R_in = 20 mm, 5 % fraction (rank-1 PCM only).
  D arrangement single-layer / staggered / radial at R_in = 20 mm, 5 %, 0.030 kg/s (rank-1 PCM only).
Blocks B-D use the multi-node tank (decision D4); A also runs the single-node tank to expose model dependence.
Geometry is checked by the real packing engine with PERMISSIVE bounds (the old 8-37 count / 40-80 mm diameter
bounds are exactly what this study is asking whether to replace); fraction cap 20 % kept.

Writes results/g7_sensitivity_r<cluster>.csv. Night scenarios use every 30th day (12 days).
"""

import math
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.design.schema import DesignVector
from src.io_utils import get_regime, load_design_bounds, load_system_config
from src.simulation.run_case import run_case
from src.weather import roles
from src.weather.inventory import CURRENT_MEDOIDS

YEARS = (2018, 2019)
WALL = 0.0008
R_LEVELS_MM = (10, 15, 20, 25, 30, 40)
FRACTIONS = (0.005, 0.01, 0.02, 0.035, 0.05, 0.075, 0.10, 0.15, 0.20)
FLOWS = (0.010, 0.020, 0.030, 0.040, 0.050)
ARRANGEMENTS = ("single-layer", "staggered", "radial")
NIGHT_STRIDE = 30
KEEP = ["useful_energy_kWh", "solar_fraction", "residual_pct_of_collector", "pcm_mass_kg", "max_pcm_temp_C",
        "max_water_temp_C", "n_safety_violations", "n_shield_pcm_activations", "mean_f_melt", "max_f_melt"]
TES = ["E_del45_annual_kWh", "E_del45_window_kWh", "E_rec45_mean_kWh", "E_rec45_daily_max_mean_kWh",
       "latent_full_cycles_per_day", "tau_hold_mean_h", "tau_hold_p10_h", "tau_hold_censored_frac",
       "tau_serve_mean_h", "serve_frac_45_mean", "T_deliv_max_C", "T_pcm_max_C"]


def permissive_bounds():
    b = load_design_bounds()
    b = {**b, "pcm_thickness_m": {"min": 0.004, "max": 0.2}, "capsule_diameter_m": {"min": 0.01, "max": 0.2},
         "capsule_count": {"min": 1, "max": 5000, "step": 1}, "pcm_volume_fraction": {"min": 0.0, "max": 0.20}}
    return b


def design(r_in_m, n, flow, arrangement):
    return DesignVector(capsule_diameter_m=2.0 * (r_in_m + WALL), n_capsule=int(n), flow_rate_kg_s=flow,
                        capsule_arrangement=arrangement)


def n_for_inner_fraction(r_in_m, frac, v_tank):
    return max(1, round(frac * v_tank / (4.0 / 3.0 * math.pi * r_in_m ** 3)))


def n_for_outer_fraction(r_in_m, frac, v_tank):
    return max(1, round(frac * v_tank / (4.0 / 3.0 * math.pi * (r_in_m + WALL) ** 3)))


def one_run(cid, year, weather, model, pcm, dv, bounds, block, rank, level):
    t0 = time.time()
    out = run_case("rajasthan", cid, pcm, dv, design_bounds=bounds, weather=weather, tank_model=model,
                   compute_tes_metrics=True, night_day_stride=NIGHT_STRIDE)
    row = {"block": block, "regime": cid, "year": year, "model": model, "pcm": pcm or "PLAIN", "pcm_rank": rank,
           "level": level, "R_in_mm": (dv.capsule_diameter_m / 2 - WALL) * 1000, "D_mm": dv.capsule_diameter_m * 1000,
           "N": dv.n_capsule if pcm else 0, "flow": dv.flow_rate_kg_s, "arrangement": dv.capsule_arrangement,
           "valid": out["valid"], "reason": out["reason"] or ""}
    if out["valid"]:
        g = out["geometry"]
        row.update({"frac_outer": g["pcm_volume_fraction"] if pcm else 0.0, "n_layers": g.get("n_layers"),
                    "stack_height_m": g.get("stack_height_m")})
        row.update({k: out["metrics"].get(k) for k in KEEP})
        row.update({k: out["tes"].get(k) for k in TES})
    row["runtime_s"] = time.time() - t0
    return row


def main(cid):
    cfg = load_system_config()
    v_tank = cfg["tank"]["volume_L"] / 1000.0
    bounds = permissive_bounds()
    pcms = get_regime("rajasthan", cid)["pcm_shortlist"]
    point = CURRENT_MEDOIDS[cid]
    ref_dv = design(0.020, 10, 0.030, "staggered")
    rows = []

    def log(r):
        rows.append(r)
        print(f"r{cid} {r['block']} {r['model']} y{r['year']} {r['pcm'][:18]:18s} R={r['R_in_mm']:.0f} N={r['N']} "
              f"valid={r['valid']} {r['runtime_s']:.1f}s", flush=True)

    for year in YEARS:
        w = roles.load_point_year("rajasthan", cid, point, year, purpose="explore")
        for model in ("single", "multinode"):                                   # paired plain-tank references
            log(one_run(cid, year, w, model, None, ref_dv, bounds, "REF", 0, "plain"))
        for rank, pcm in enumerate(pcms, start=1):
            for model in ("single", "multinode"):                               # A thickness
                for rmm in R_LEVELS_MM:
                    r = rmm / 1000.0
                    n = n_for_inner_fraction(r, 0.05, v_tank)
                    log(one_run(cid, year, w, model, pcm, design(r, n, 0.030, "staggered"), bounds, "A_thickness",
                                rank, f"R{rmm}"))
            for f in FRACTIONS:                                                 # B count
                n = n_for_outer_fraction(0.020, f, v_tank)
                log(one_run(cid, year, w, "multinode", pcm, design(0.020, n, 0.030, "staggered"), bounds, "B_count",
                            rank, f"f{f:.3f}"))
        pcm1 = pcms[0]
        n5 = n_for_inner_fraction(0.020, 0.05, v_tank)
        for fl in FLOWS:                                                        # C flow
            log(one_run(cid, year, w, "multinode", pcm1, design(0.020, n5, fl, "staggered"), bounds, "C_flow", 1,
                        f"q{fl:.3f}"))
        for arr in ARRANGEMENTS:                                                # D arrangement
            log(one_run(cid, year, w, "multinode", pcm1, design(0.020, n5, 0.030, arr), bounds, "D_arrangement", 1,
                        arr))
    out = Path(f"results/g7_sensitivity_r{cid}.csv")
    pd.DataFrame(rows).to_csv(out, index=False)
    print("written", out)


if __name__ == "__main__":
    main(int(sys.argv[1]))
