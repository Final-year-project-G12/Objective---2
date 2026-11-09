#!/usr/bin/env python3
"""
make_uttarakhand_cases.py -- write every Uttarakhand OpenFOAM case from the saved Objective 2 results.

Reads (objective2-uttarakhand):
  results/g10_selection_r{0,1,2,3}.json   chosen design per regime (PCM, inner radius, flow)
  results/g10_heldout_results.csv          best design of every other O1 PCM (runner-up = best held-out g_window)
  configs/states/uttarakhand.yaml          mains temperature per regime

Writes (objective2-uttarakhand/openfoam_cfd):
  cases/r<c>_chosen_<pcm>/          capsule case of the chosen design (KPIs + comparison with the grey-box)
  cases/r<c>_chosen_<pcm>_cond/     same capsule, conduction only (g = 0): calibrates the x2 convection factor
  cases/r<c>_alt_<pcm>/             runner-up PCM of the regime (regimes 0-2, where the PCM choice is not resolved)
  cases_viz/r<c>_chosen_<pcm>/      the chosen capsule with every 30 s kept, for the ParaView melt animation
  cases_tank/r<c>_{charge,draw,idle}/  50 L water tank at the regime's mains temperature
  results/cases_index.csv           one row per case with every input

The capsule is the PCM sphere: --d = 2 x inner radius (thickness = inner radius, decision D3); the aluminium wall
is in the boundary condition. Nothing is run here; see ../README.md and run_all_cases.ps1.

  python make_uttarakhand_cases.py            # write all cases (existing case folders are rewritten)
"""
import csv
import json
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                          # objective2-uttarakhand/openfoam_cfd
sys.path.insert(0, HERE)
import _paths  # noqa: E402
import make_case as mc  # noqa: E402
import tank_make_case as tc  # noqa: E402

PROJ = _paths.project_root()
REGIMES = (0, 1, 2, 3)
CFG = mc.load_cfg()
DT_DRIVE_K = 12.0            # hot water above Tm; the shared quick-start uses 15 K, which puts PureTemp 58 water at 73 C, above
                             # the 72 C water-side shield, so 12 K keeps T_hot at 67-70 C (inside what the tank actually reaches)
VIZ_T_END_H = 6.0            # the charge window
TANK_T_IN_C = 60.0           # charge: collector return temperature, as in the shared charge case
TANK_T_HOT_C = 55.0          # draw / idle: hot-layer temperature, as in the shared CFD draw case
TANK_HOT_FRACTION = 0.6      # draw: 30 L hot over 20 L cold (the shared CFD draw case)
TANK_MDOT = 0.03


def slug(name):
    s = name.encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").lower()


def runner_up(regime, chosen_pcm):
    rows = [r for r in csv.DictReader(open(os.path.join(PROJ, "results", "g10_heldout_results.csv"), encoding="utf-8"))
            if int(r["regime"]) == regime and r["role"] != "chosen"]
    best = {}
    for r in rows:
        best.setdefault(r["pcm"], []).append(float(r["g_window"]))
    pcm = max(best, key=lambda p: sum(best[p]) / len(best[p]))
    r = next(x for x in rows if x["pcm"] == pcm)
    return dict(pcm=pcm, R_in_m=float(r["R_in_m"]), flow=float(r["flow"]), fraction=float(r["fraction"]),
                arrangement=r["arrangement"], heldout_g_window=sum(best[pcm]) / len(best[pcm]))


def main():
    state = yaml.safe_load(open(os.path.join(PROJ, "configs", "states", "uttarakhand.yaml"), encoding="utf-8"))
    mains = {int(r["cluster_id"]): float(r["T_mains_est_C"]) for r in state["regimes"]}
    index = []

    def capsule(kind, out, regime, d, meaningful, **kw):
        m = mc.build_case(out, d["pcm"], 2.0 * d["R_in_m"], d["flow"], DT_DRIVE_K, cfg=CFG, **kw)
        index.append(dict(case=os.path.relpath(out, ROOT).replace("\\", "/"), kind=kind, regime=regime, pcm=d["pcm"],
                          R_in_mm=round(d["R_in_m"] * 1000, 2), pcm_diameter_m=round(2 * d["R_in_m"], 5),
                          fraction=round(d["fraction"], 4), flow_kg_s=round(d["flow"], 5), arrangement=d["arrangement"],
                          dT_drive_K=DT_DRIVE_K, h_w_W_m2K=round(m["h_w_W_m2K"], 2), Bi=round(m["Bi"], 3),
                          Ste=round(m["Ste"], 3), n_cells_est=m["n_cells_est"], T_mains_C=mains[regime],
                          pcm_beats_water_only=meaningful))

    for c in REGIMES:
        sel = json.load(open(os.path.join(PROJ, "results", f"g10_selection_r{c}.json"), encoding="utf-8"))
        ch, ok = sel["chosen"], bool(sel["meaningful_on_primary_metric"])
        tag = f"r{c}_chosen_{slug(ch['pcm'])}"
        capsule("capsule_chosen", os.path.join(ROOT, "cases", tag), c, ch, ok)
        capsule("capsule_viz", os.path.join(ROOT, "cases_viz", tag), c, ch, ok, viz=True,
                t_end_h=VIZ_T_END_H, sample_every_s=30.0)
        if ok:   # regime 3: PCM does not help, so no calibration / PCM comparison is needed there
            capsule("capsule_conduction", os.path.join(ROOT, "cases", tag + "_cond"), c, ch, ok, conduction_only=True)
            alt = runner_up(c, ch["pcm"])
            capsule("capsule_runner_up", os.path.join(ROOT, "cases", f"r{c}_alt_{slug(alt['pcm'])}"), c, alt, ok)

        for mode in ("charge", "draw", "idle"):
            out = os.path.join(ROOT, "cases_tank", f"r{c}_{mode}")
            kw = dict(mode=mode, mdot=TANK_MDOT, T_amb_C=round(mains[c] + 2.0, 2), viz=True, write_every=120.0,
                      t_end_s=7200.0 if mode == "idle" else 3600.0)
            if mode == "charge":
                kw.update(T_in_C=TANK_T_IN_C, T_init_C=mains[c])
            elif mode == "draw":
                kw.update(T_hot_C=TANK_T_HOT_C, T_mains_C=mains[c], hot_fraction=TANK_HOT_FRACTION)
            else:
                kw.update(T_hot_C=TANK_T_HOT_C)
            m = tc.build(out, **kw)
            index.append(dict(case=os.path.relpath(out, ROOT).replace("\\", "/"), kind=f"tank_{mode}", regime=c,
                              pcm="", flow_kg_s=TANK_MDOT, T_mains_C=mains[c], T_amb_C=kw["T_amb_C"],
                              n_cells_est=m["n_cells"], pcm_beats_water_only=ok))

    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    keys = list(dict.fromkeys(k for r in index for k in r))
    with open(os.path.join(ROOT, "results", "cases_index.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(index)
    print(f"wrote {len(index)} cases; index results/cases_index.csv")


if __name__ == "__main__":
    main()
