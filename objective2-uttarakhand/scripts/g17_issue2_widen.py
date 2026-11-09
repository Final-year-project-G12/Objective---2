"""
scripts/g17_issue2_widen.py
==============================
Issue 2 (progress log sections 18/23): WP6 boundary-artefact rule - widen each bound that the optimum sits on in a DIAGNOSTIC run and see whether the
primary metric g_window moves by more than the band. Not a re-search and not an adoption of new bounds: the approved box (configs/design_space.yaml)
is unchanged, the widened geometry bounds below exist only inside this script.
Diagnostic points around the frozen chosen design of a regime (its PCM, arrangement and flow unless stated), stack centre, explore years 2016-2020:
  A  R_in in {20, 30, 40, 45, 50, 60} mm at the chosen outer fraction (capsule count follows)
  B  outer fraction in {0.10, 0.15, 0.20, 0.25, 0.30, 0.40} at the chosen R_in
  C  joint widening: R_in in {40, 50} mm x fraction in {0.25, 0.30, 0.40}
  D  flow in {chosen, 0.050, 0.065, 0.080} kg/s at the chosen design (the upper flow bound is 0.050)
Paired against exact water-only runs at the same flow (no flow grid, so flows above 0.050 are allowed). Geometry is still checked exactly; designs that
fail the exact geometry check or the 65 C / 75 C peaks are recorded, not dropped. There is NO capsule-size source above 40 mm radius in the files read
(vendor catalogue is on the papers-needed list): results for R_in > 40 mm are labelled 'no source' in the docs.
Usage: python scripts/g17_issue2_widen.py <cluster_id>  ->  results/g17_widen_r<c>.csv
"""

import json
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.design.schema import DesignVector
from src.design.space import capsule_outer_volume_m3, geometry_bounds, load_space, v_tank_m3, wall_m
from src.optimize.evaluate import _weather
from src.simulation.run_case import run_case
from src.weather import roles

OUT = Path("results")
SP = load_space()


def wide_bounds():
    b = geometry_bounds()
    b["pcm_volume_fraction"] = {"min": 0.0, "max": 0.60}
    b["flow_rate_kg_s"] = {"min": 0.005, "max": 0.20}
    return b


def dv_for(r, n, q, arr):
    return DesignVector(capsule_diameter_m=2.0 * (r + wall_m()), n_capsule=int(n), flow_rate_kg_s=float(q), capsule_arrangement=arr)


def kw(cid, y):
    return dict(design_bounds=wide_bounds(), weather=_weather(cid, y, "explore"), tank_model=SP["model"]["tank_model"],
                n_nodes=SP["model"]["n_nodes"], stack_anchor=SP["model"]["stack_anchor"], compute_tes_metrics=True, night_day_stride=0)


@lru_cache(maxsize=None)
def plain(cid, q, y):
    r = run_case("uttarakhand", cid, None, dv_for(0.02, 5, q, "staggered"), **kw(cid, y))
    m, t = r["metrics"], r["tes"]
    return t["E_del45_window_kWh"], t["E_del45_annual_kWh"], m["shield_water_h"]


def main(cid):
    ch = json.load(open(OUT / f"g10_selection_r{cid}.json", encoding="utf-8"))["chosen"]
    pcm, r0, f0, q0, arr = ch["pcm"], float(ch["R_in_m"]), float(ch["fraction"]), float(ch["flow"]), ch["arrangement"]
    pts = []
    for rmm in (20, 30, 40, 45, 50, 60):
        pts.append(("A_radius", f"R{rmm}", rmm / 1000.0, f0, q0))
    for f in (0.10, 0.15, 0.20, 0.25, 0.30, 0.40):
        pts.append(("B_fraction", f"f{f:.2f}", r0, f, q0))
    for rmm in (40, 50):
        for f in (0.25, 0.30, 0.40):
            pts.append(("C_joint", f"R{rmm}_f{f:.2f}", rmm / 1000.0, f, q0))
    for q in (q0, 0.050, 0.065, 0.080):
        pts.append(("D_flow", f"q{q:.3f}", r0, f0, q))
    rows = []
    for blk, lab, r, f, q in pts:
        n = int(round(f * v_tank_m3() / capsule_outer_volume_m3(r)))
        row = {"regime": cid, "pcm": pcm, "arrangement": arr, "block": blk, "level": lab, "R_in_mm": r * 1000, "fraction_req": f, "N": n, "flow": q}
        dv = dv_for(r, n, q, arr)
        per = []
        for y in roles.years_for("explore"):
            res = run_case("uttarakhand", cid, pcm, dv, **kw(cid, y))
            if not res["valid"]:
                row.update({"valid": False, "reason": res.get("reason", "")})
                per = []
                break
            m, t = res["metrics"], res["tes"]
            pw, pa, ps = plain(cid, round(q, 6), y)
            per.append((t["E_del45_window_kWh"] - pw, t["E_del45_annual_kWh"] - pa, (m["shield_water_h"] + m["shield_pcm_h"]) - ps,
                        m["max_pcm_temp_C"], m["max_water_temp_C"]))
        if per:
            a = np.array(per)
            row.update({"valid": True, "g_window": a[:, 0].mean(), "g_window_sd": a[:, 0].std(ddof=1), "g_annual": a[:, 1].mean(),
                        "d_overheat": a[:, 2].mean(), "t_pcm_max": a[:, 3].max(), "t_water_max": a[:, 4].max(),
                        "feasible_65_75": bool(a[:, 3].max() <= 65.0 and a[:, 4].max() <= 75.0)})
        rows.append(row)
        print(blk, lab, row.get("valid"), row.get("g_window"), flush=True)
        pd.DataFrame(rows).to_csv(OUT / f"g17_widen_r{cid}.csv", index=False)


if __name__ == "__main__":
    main(int(sys.argv[1]))
