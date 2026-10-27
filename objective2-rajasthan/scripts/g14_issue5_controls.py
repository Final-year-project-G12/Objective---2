"""
scripts/g14_issue5_controls.py
=================================
Issue 5 (progress log sections 18/20): controls that can actually be informative. G11 ran thickness-at-constant-mass and "PCM fraction x2" from
the CHOSEN design, which sits at the 20 % cap: R 10-30 mm then needs up to 2248 capsules (geometry invalid) and "x2" is clipped back to the base.
Here both controls run from an INTERIOR anchor declared before the run: the middle levels of the S1 screening grid, i.e.
    R_in = 25 mm, outer PCM fraction = 10 % (the count follows from count_for_fraction), flow = 0.030 kg/s, staggered, stack centre,
    PCM = the regime's chosen PCM, explore years 2016-2020 (no select or test year is touched).
Blocks (all paired against the water-only tank at the same flow, same machinery as G11):
  base            the anchor
  thickness_const_mass   R_in 10,15,20,25,30,40 mm with N = round(N_anchor * (25/R)^3), i.e. constant INNER PCM volume (= mass). The outer volume,
                         and so the displaced water volume, still changes with R: reported as `outer_fraction` (a confound, not removed)
  fraction        N x 0.5, x1, x2 (x2 = min(2 N, largest count inside the 20 % cap); a first run with N = 2 x 70 = 140 gave 20.1 % and was rejected by the cap, so the cap count is used and reported as such); positive control: the gain should change by more than the band
Usage: python scripts/g14_issue5_controls.py <cluster_id>  ->  results/g14_controls_r<c>.csv
"""

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("g11_ablation", ROOT / "scripts" / "g11_ablation.py")
g11 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g11)
from src.design.space import capsule_outer_volume_m3, count_for_fraction, v_tank_m3

OUT = Path("results")
R0, F0, Q0, ARR0 = 0.025, 0.10, 0.030, "staggered"


def main(cid):
    ch = json.loads((OUT / f"g10_selection_r{cid}.json").read_text(encoding="utf-8"))["chosen"]
    pcm = ch["pcm"]
    n0 = int(count_for_fraction(R0, F0))
    rows = []

    def add(block, level, r, n):
        res = g11.run(cid, pcm, g11.design_from(r, n, Q0, ARR0))
        row = {"regime": cid, "pcm": pcm, "block": block, "level": level, "R_in_mm": r * 1000, "N": n,
               "outer_fraction": n * capsule_outer_volume_m3(r) / v_tank_m3(), "valid": res is not None}
        if res is not None:
            mean, sd = res
            for k in mean.index:
                row[k], row[k + "_sd"] = mean[k], sd[k]
        rows.append(row)
        print(block, level, row["valid"], row.get("g_window"), flush=True)

    add("base", "anchor", R0, n0)
    for rmm in (10, 15, 20, 25, 30, 40):
        r = rmm / 1000.0
        add("thickness_const_mass", f"R{rmm}", r, max(1, round(n0 * (R0 / r) ** 3)))
    cap_n = int(0.20 * v_tank_m3() / capsule_outer_volume_m3(R0))        # largest count inside the 20 % cap
    for lab, n in (("x0.5", max(1, round(n0 * 0.5))), ("x1", n0), ("x2", min(2 * n0, cap_n))):
        add("fraction", lab, R0, n)
    pd.DataFrame(rows).to_csv(OUT / f"g14_controls_r{cid}.csv", index=False)


if __name__ == "__main__":
    main(int(sys.argv[1]))
