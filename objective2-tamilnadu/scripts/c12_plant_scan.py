"""
scripts/c12_plant_scan.py   (diagnostic, NOT a selection step)
================================================================
Where does a PCM tank beat a water-only tank of the SAME total volume? Scans collector area x daily demand on the common 100 L tank for
one fixed design (R_in 40 mm, 30 %, staggered, 0.030 kg/s, centre anchor) with each regime's rank-1 O1 PCM, explore 2017-18, dt 150 s.
Reports paired gains (delivered energy at 45 C in the window, annual, solar fraction), the water-only solar fraction (how much of the demand
the plain tank already meets) and shield hours. Usage: python scripts/c12_plant_scan.py <cluster_id> -> results/c12_plant_scan_r<id>.csv
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import io_utils                                   # noqa: E402
from src.design.space import geometry_bounds, to_design    # noqa: E402
from src.simulation.run_case import run_case               # noqa: E402
from src.weather import roles                              # noqa: E402
from src.weather.inventory import CURRENT_MEDOIDS          # noqa: E402
from config import STATE                                   # noqa: E402

AREAS, DEMANDS, YEARS = (1.0, 1.5, 2.0, 2.5), (100, 150, 200, 300), (2017, 2018)


def main(cid):
    pcm = io_utils.o1_top3(STATE)[cid][0]
    dv = to_design(0.040, 0.30, 0.030, "staggered")
    ws = {y: roles.load_point_year(STATE, cid, CURRENT_MEDOIDS[cid], y, "explore") for y in YEARS}
    rows = []
    for a in AREAS:
        for q in DEMANDS:
            acc = []
            for y in YEARS:
                kw = dict(design_bounds=geometry_bounds(), weather=ws[y], tank_model="multinode", n_nodes=10, compute_tes_metrics=True,
                          night_day_stride=0, volume_multiplier=q / 100.0,
                          system_config_overrides={"solver": {"timestep_s": 150.0}, "collector": {"area_m2": a}})
                p, b = run_case(STATE, cid, pcm, dv, **kw), run_case(STATE, cid, None, dv, **kw)
                acc.append({"g_window": p["tes"]["E_del45_window_kWh"] - b["tes"]["E_del45_window_kWh"],
                            "g_annual": p["tes"]["E_del45_annual_kWh"] - b["tes"]["E_del45_annual_kWh"],
                            "sf_pcm": p["metrics"]["solar_fraction"], "sf_plain": b["metrics"]["solar_fraction"],
                            "shield_plain_h": b["metrics"]["shield_water_h"],
                            "shield_pcm_h": p["metrics"]["shield_water_h"] + p["metrics"]["shield_pcm_h"]})
            row = {"regime": cid, "pcm": pcm, "area_m2": a, "demand_L_day": q}
            row.update({k: sum(x[k] for x in acc) / len(acc) for k in acc[0]})
            rows.append(row)
            print(cid, a, q, round(row["g_window"], 1), round(row["sf_plain"], 3), flush=True)
    pd.DataFrame(rows).to_csv(Path("results") / f"c12_plant_scan_r{cid}.csv", index=False)


if __name__ == "__main__":
    main(int(sys.argv[1]))
