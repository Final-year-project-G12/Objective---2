"""
scripts/m1_export.py  -  MATLAB checkpoint M1 (plan section 0.2 / R18), Python side: export the frozen Objective 2 simulations
==================================================================================================================================
M1 = "show the frozen O2 tank simulations in MATLAB with no learned controller (always-charge B0 only): water-only tank vs the PCM
design on the same real day, the PCMs, water temperature, capsule liquid fraction, heat given to the water and the energy balance".
Gate: the MATLAB figures match the O2 node-model numbers (ranking and energy balance).

This script runs, per regime, the frozen designs on the select year 2021 at the report time step (37.5 s), centre anchor, B0 (the
kernel always circulates when the sun is up; the shield acts inside the kernel):
  * water_only            the installed design (the reference baseline; O2 recommends PCM in every regime)
  * pick                  the funnel's best PCM design (tested reference)
  * alt_<pcm>             the best design of each other O1 PCM of the regime
and writes, under results/m1_matlab/:
  hourly_r<c>_<case>.csv  the kernel's hourly record (8760 rows)
  summary.csv             Python's own numbers per run: useful energy, E_del45 annual and window, E_stored initial, residual
MATLAB (matlab/m1_checkpoint.m) recomputes these numbers from the hourly records alone and draws the M1 figures.
Usage: python scripts/m1_export.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.design.box import full_dt                         # noqa: E402
from src.design.space import geometry_bounds, to_design    # noqa: E402
from src.simulation.run_case import run_case                # noqa: E402
from src.weather import roles                               # noqa: E402
from src.weather.inventory import CURRENT_MEDOIDS, REGIMES  # noqa: E402

OUT = ROOT / "results" / "m1_matlab"
YEAR = 2021
KEEP = ["hour_index", "hour_of_day", "I_t_Wm2", "T_amb_C", "T_w_C", "T_w_mean_C", "T_bottom_C", "T_pcm_C", "f_melt",
        "Q_collector_Wh", "Q_load_Wh", "Q_load_net_Wh", "Q_pcm_Wh", "Q_loss_Wh", "Q_unmet_Wh", "draw_kg", "Edel_target_Wh",
        "E_stored_kWh", "T_w_max_C", "T_pcm_max_C"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for cid in REGIMES:
        sel = json.loads((ROOT / "results" / f"g10_selection_r{cid}.json").read_text())
        ch = sel["chosen"]
        cases = [("water_only", None, ch), ("pick", ch["pcm"], ch)] + \
                [(f"alt_{a['pcm']}", a["pcm"], a) for a in sel["alternatives_best_per_pcm"] if a["pcm"] != ch["pcm"]]
        w = roles.load_point_year("rajasthan", cid, CURRENT_MEDOIDS[cid], YEAR, "select")
        for name, pcm, d in cases:
            dv = to_design(float(d["R_in_m"]), float(d["fraction"]), 0.03, d["arrangement"])
            r = run_case("rajasthan", cid, pcm, dv, design_bounds=geometry_bounds(), weather=w, tank_model="multinode", n_nodes=10,
                         stack_anchor="center", compute_tes_metrics=True, night_day_stride=0, record_hourly=True,
                         system_config_overrides={"solver": {"timestep_s": full_dt()}})
            tag = "".join(ch_ if ch_.isalnum() else "_" for ch_ in name.encode("ascii", "ignore").decode()).strip("_")
            h = r["hourly"][KEEP].copy()
            h.insert(0, "local_date", w["local_date"].to_numpy()[: len(h)])
            h.to_csv(OUT / f"hourly_r{cid}_{tag}.csv", index=False)
            m, t = r["metrics"], r["tes"]
            rows.append({"regime": cid, "case": tag, "pcm": pcm or "", "R_in_m": d["R_in_m"], "fraction": d["fraction"] if pcm else 0.0,
                         "N": d["N"] if pcm else 0, "useful_kWh": m["useful_energy_kWh"], "E_del45_annual_kWh": t["E_del45_annual_kWh"],
                         "E_del45_window_kWh": t["E_del45_window_kWh"], "E_stored_initial_kWh": m["E_stored_initial_kWh"],
                         "residual_pct": m["residual_pct_of_collector"], "max_water_C": m["max_water_temp_C"],
                         "max_pcm_C": m["max_pcm_temp_C"], "year": YEAR, "dt_s": full_dt(), "anchor": "center"})
            print(cid, tag, flush=True)
    pd.DataFrame(rows).to_csv(OUT / "summary.csv", index=False)


if __name__ == "__main__":
    main()
