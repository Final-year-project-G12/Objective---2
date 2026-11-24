"""
scripts/c6_g1_pairs.py   (level L3, gate G1, per regime x O1 PCM)
==================================================================
For each of the regime's O1 PCMs and two designs (R 25 mm, staggered, f 30 % and 40 %), year 2017 (explore):
dt 150 vs 37.5 s (delivered-energy change), 10 vs 20 nodes, energy-closure residual, peak PCM/water temperature, determinism
(identical rerun), and the zero-latent-heat control (PCM with latent heat set to ~0 must not beat water-only by more than the
sensible-heat effect). Usage: python scripts/c6_g1_pairs.py <cluster_id>  -> results/c6_g1_pairs_r<id>.csv
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


def one(cid, w, pcm, dv, dt, nodes=10, ovr=None):
    r = run_case(STATE, cid, pcm, dv, design_bounds=geometry_bounds(), weather=w, tank_model="multinode", n_nodes=nodes,
                 compute_tes_metrics=True, night_day_stride=0, pcm_record_overrides=ovr,
                 system_config_overrides={"solver": {"timestep_s": dt}})
    m, t = r["metrics"], r["tes"]
    return {"win": t["E_del45_window_kWh"], "ann": t["E_del45_annual_kWh"], "res": m["residual_pct_of_collector"],
            "pcm_max": m["max_pcm_temp_C"], "w_max": m["max_water_temp_C"], "hours_over": m["hours_over_limit"]}


def main(cid):
    w = roles.load_point_year(STATE, cid, CURRENT_MEDOIDS[cid], 2017, "explore")
    rows = []
    for pcm in io_utils.o1_top3(STATE)[cid]:
        for f in (0.30, 0.40):
            dv = to_design(0.025, f, 0.030, "staggered")
            a150, a375 = one(cid, w, pcm, dv, 150.0), one(cid, w, pcm, dv, 37.5)
            n20 = one(cid, w, pcm, dv, 150.0, nodes=20)
            again = one(cid, w, pcm, dv, 150.0)
            zl = one(cid, w, pcm, dv, 150.0, ovr={"latent_heat_kJ_kg": 1e-6})
            rows.append({"regime": cid, "pcm": pcm, "fraction": f, "win_150": a150["win"], "win_37p5": a375["win"],
                         "dt_chg_pct": abs(a375["win"] - a150["win"]) / a150["win"] * 100,
                         "node_shift_pct": (n20["win"] - a150["win"]) / a150["win"] * 100,
                         "residual_pct": max(a150["res"], a375["res"], n20["res"]),
                         "pcm_max_C": max(a150["pcm_max"], a375["pcm_max"]), "water_max_C": max(a150["w_max"], a375["w_max"]),
                         "hours_over_limit": a375["hours_over"], "deterministic": a150["win"] == again["win"],
                         "zero_latent_win": zl["win"], "zero_latent_minus_real": zl["win"] - a150["win"]})
            print(cid, pcm, f, flush=True)
    pd.DataFrame(rows).to_csv(Path("results") / f"c6_g1_pairs_r{cid}.csv", index=False)


if __name__ == "__main__":
    main(int(sys.argv[1]))
