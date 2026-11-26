"""
scripts/g15_issue6_anchor.py
===============================
Issue 6 (progress log sections 18/21): the tank model places the PCM stack at the tank centre (configs/design_space.yaml:23,
read at src/optimize/evaluate.py:53; applied in src/simulation/tank_model_multinode.py:80). The stack of a chosen design is 3 layers, about 0.25 m of
the 0.634 m tank height, so the position is not neutral. This script re-evaluates, with the stack anchored at the tank BOTTOM, CENTRE and TOP:
the chosen design and the best design of every other O1 PCM of the regime (g10_selection_r<c>.json, frozen, not re-optimised), on the explore
(2016-2020) and select (2021-2023) years, paired against the water-only tank at the same flow (which does not depend on the anchor: G11 control N1).
No position is chosen; the output is for reporting the dependence and checking whether the PCM ranking and the sign of the gain survive it.
Usage: python scripts/g15_issue6_anchor.py <cluster_id>  ->  results/g15_anchor_r<c>.csv
"""

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.design.space import geometry_bounds, load_space, to_design
from src.optimize.baseline import plain_at
from src.optimize.evaluate import _weather
from src.simulation.run_case import run_case
from src.weather import roles

OUT = Path("results")


def main(cid):
    log = json.load(open(OUT / f"g10_selection_r{cid}.json", encoding="utf-8"))
    designs = [("chosen", log["chosen"])] + [("best_of_pcm", a) for a in log["alternatives_best_per_pcm"]]
    sp = load_space()
    rows = []
    for role, d in designs:
        dv = to_design(d["R_in_m"], d["fraction"], d["flow"], d["arrangement"])
        for anchor in ("bottom", "center", "top"):
            for purpose in ("explore", "select"):
                for y in roles.years_for(purpose):
                    r = run_case("uttarakhand", cid, d["pcm"], dv, design_bounds=geometry_bounds(), weather=_weather(cid, y, purpose),
                                 tank_model=sp["model"]["tank_model"], n_nodes=sp["model"]["n_nodes"], stack_anchor=anchor,
                                 compute_tes_metrics=True, night_day_stride=0)
                    m, t = r["metrics"], r["tes"]
                    p = plain_at(cid, y, d["flow"], purpose)
                    rows.append({
                        "regime": cid, "role": role, "pcm": d["pcm"], "pcm_rank": d["pcm_rank"], "anchor": anchor, "purpose": purpose, "year": y,
                        "g_window": t["E_del45_window_kWh"] - p["E_del45_window_kWh"],
                        "g_annual": t["E_del45_annual_kWh"] - p["E_del45_annual_kWh"],
                        "d_overheat": (m["shield_water_h"] + m["shield_pcm_h"]) - p["shield_water_h"],
                        "d_shield_water_h": m["shield_water_h"] - p["shield_water_h"], "shield_pcm_h": m["shield_pcm_h"],
                        "t_pcm_max": m["max_pcm_temp_C"], "t_water_max": m["max_water_temp_C"],
                    })
        print("done", role, d["pcm"], flush=True)
        pd.DataFrame(rows).to_csv(OUT / f"g15_anchor_r{cid}.csv", index=False)


if __name__ == "__main__":
    main(int(sys.argv[1]))
