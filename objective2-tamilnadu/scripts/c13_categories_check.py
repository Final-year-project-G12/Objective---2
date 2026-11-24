"""
scripts/c13_categories_check.py (diagnostic): PCM minus water-only tank in EVERY reported category, at several demands (2.0 m2, 100 L tank).
Design R 40 mm, 30 %, staggered, 0.030 kg/s, rank-1 O1 PCM, explore 2017, dt 150, night scenarios every 30th day.  -> results/c13_categories_r<id>.csv
"""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import io_utils
from src.design.space import geometry_bounds, to_design
from src.simulation.run_case import run_case
from src.weather import roles
from src.weather.inventory import CURRENT_MEDOIDS
from config import STATE

def main(cid):
    pcm = io_utils.o1_top3(STATE)[cid][0]; dv = to_design(0.040, 0.30, 0.030, "staggered")
    w = roles.load_point_year(STATE, cid, CURRENT_MEDOIDS[cid], 2017, "explore"); rows = []
    for q in (100, 150, 175, 200, 300):
        kw = dict(design_bounds=geometry_bounds(), weather=w, tank_model="multinode", n_nodes=10, compute_tes_metrics=True, night_day_stride=30,
                  volume_multiplier=q / 100.0, system_config_overrides={"solver": {"timestep_s": 150.0}})
        p, b = run_case(STATE, cid, pcm, dv, **kw), run_case(STATE, cid, None, dv, **kw)
        tp, tb, mp, mb = p["tes"], b["tes"], p["metrics"], b["metrics"]
        rows.append({"regime": cid, "demand": q,
                     "delivered_window_kWh": tp["E_del45_window_kWh"] - tb["E_del45_window_kWh"], "delivered_annual_kWh": tp["E_del45_annual_kWh"] - tb["E_del45_annual_kWh"],
                     "solar_fraction": mp["solar_fraction"] - mb["solar_fraction"], "hold_h": tp["tau_hold_mean_h"] - tb["tau_hold_mean_h"],
                     "serve_h": tp["tau_serve_mean_h"] - tb["tau_serve_mean_h"], "serve_frac_45": tp["serve_frac_45_mean"] - tb["serve_frac_45_mean"],
                     "shield_h": (mp["shield_water_h"] + mp["shield_pcm_h"]) - mb["shield_water_h"], "peak_water_C": mp["max_water_temp_C"] - mb["max_water_temp_C"]})
        print(cid, q, flush=True)
    pd.DataFrame(rows).to_csv(Path("results") / f"c13_categories_r{cid}.csv", index=False)

if __name__ == "__main__":
    main(int(sys.argv[1]))
