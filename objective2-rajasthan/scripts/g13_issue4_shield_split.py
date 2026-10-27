"""
scripts/g13_issue4_shield_split.py
=====================================
Issue 4 (progress log section 18, option B). d_overheat as stored in every G9/G10/G11 file is
    (shield_water_h + shield_pcm_h) - plain shield_water_h          (src/optimize/evaluate.py:61)
which adds a PCM-side per-node throttle (62 C, no counterpart in a water-only tank) to the water-side shield hours. This script reports the
two parts SEPARATELY for the chosen design and the best design of every other O1 PCM of a regime (g10_selection_r<c>.json), per weather year of
the EXPLORE (2016-2020) and SELECT (2021-2023) roles. Nothing in the optimisation, the shield or the limits is changed; f3 stays d_overheat.
The held-out years are not loaded (the held-out file has no shield breakdown and that test is already used).
Usage: python scripts/g13_issue4_shield_split.py <cluster_id>   -> results/g13_shield_split_r<c>.csv
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
        for purpose in ("explore", "select"):
            for y in roles.years_for(purpose):
                r = run_case("rajasthan", cid, d["pcm"], dv, design_bounds=geometry_bounds(), weather=_weather(cid, y, purpose),
                             tank_model=sp["model"]["tank_model"], n_nodes=sp["model"]["n_nodes"], stack_anchor=sp["model"]["stack_anchor"],
                             compute_tes_metrics=False, night_day_stride=0)
                m = r["metrics"]
                p = plain_at(cid, y, d["flow"], purpose)
                tw_plain = float("nan")
                if role == "chosen":          # exact water-only run (same flow) only for the chosen design, for the peak water temperature
                    tw_plain = run_case("rajasthan", cid, None, dv, design_bounds=geometry_bounds(), weather=_weather(cid, y, purpose),
                                        tank_model=sp["model"]["tank_model"], n_nodes=sp["model"]["n_nodes"],
                                        stack_anchor=sp["model"]["stack_anchor"], compute_tes_metrics=False,
                                        night_day_stride=0)["metrics"]["max_water_temp_C"]
                rows.append({
                    "regime": cid, "role": role, "pcm": d["pcm"], "pcm_rank": d["pcm_rank"], "purpose": purpose, "year": y,
                    "shield_water_h_pcm": m["shield_water_h"], "shield_pcm_h": m["shield_pcm_h"], "shield_water_h_plain": p["shield_water_h"],
                    "d_shield_water_h": m["shield_water_h"] - p["shield_water_h"],
                    "d_overheat_as_stored": (m["shield_water_h"] + m["shield_pcm_h"]) - p["shield_water_h"],
                    "t_water_max_pcm_C": m["max_water_temp_C"], "t_water_max_plain_C": tw_plain, "t_pcm_max_C": m["max_pcm_temp_C"],
                    "hours_over_limit_pcm": m["hours_over_limit"],
                })
        print("done", role, d["pcm"], flush=True)
        pd.DataFrame(rows).to_csv(OUT / f"g13_shield_split_r{cid}.csv", index=False)


if __name__ == "__main__":
    main(int(sys.argv[1]))
