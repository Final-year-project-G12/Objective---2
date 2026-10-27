#!/usr/bin/env python3
"""
pht_vs_greybox.py -- drive the packed-bed OpenFOAM solver (porousHeatTransferFoam)
with the grey-box's hourly water temperatures for a representative day of each
regime and compare the PCM response with the grey-box single node.

For each regime (Phase-7 deployable design, frozen closure):
  1. run the grey-box for the year (record_hourly=True)
  2. pick the representative day: median daily collector energy among days with a
     complete melt-and-freeze cycle; simulate that day plus the following night
     (48 h) from the grey-box state at 00:00
  3. forcing at the bed inlet, continuous flow at the design flow rate
        V1  T_w(t)                     water-node temperature, phi = 1
        V2  collector outlet T_w + Q_coll/(m cp), phi = 1       (as requested)
        V3  collector outlet, phi = CFD-calibrated (phi surrogate from the 48-case DOE)
  4. compare bed-mean PCM temperature and melt fraction with the grey-box's
     T_pcm_C and f_melt for the same hours

ONE-WAY COUPLING: the bed does not feed back on the water node; this isolates the
PCM-side response (closure + axial structure). Known differences from the grey-box:
the bed's alpha is constant (the grey-box doubles the PCM conductivity after 50 %
melt), the water is not drawn at night, hourly values are treated as samples at the
start of the hour.

Run from openfoam_cfd/scripts:  python pht_vs_greybox.py [--dt 5] [--regimes 0 1 2]
"""
import argparse
import csv
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import _paths                                   # noqa: E402
PROJ = _paths.project_root()
sys.path.insert(0, PROJ)

DISTRO = "Ubuntu-24.04"
CP_W = 4186.0
STATE = "rajasthan"


def wsl_path(p):
    p = os.path.abspath(p).replace("\\", "/")
    return f"/mnt/{p[0].lower()}{p[2:]}" if len(p) > 1 and p[1] == ":" else p


def run_bed(name, gen_args):
    runner = wsl_path(os.path.join(HERE, "pht_run_case.sh"))
    argv = ["wsl", "-d", DISTRO, "-e", "bash", runner, name, "rajasthan"] + gen_args
    r = subprocess.run(argv, capture_output=True, text=True, errors="replace")
    out = "\n".join(l for l in r.stdout.splitlines() if "Failed to translate" not in l)
    return r.returncode, out


def pick_day(h, ṁ_unused=None):
    """Median daily collector energy among days that melt fully and refreeze."""
    h = h.copy()
    h["day"] = h["hour_index"] // 24
    g = h.groupby("day")
    cand = []
    for day, d in g:
        if len(d) < 24 or day >= h["day"].max():
            continue
        nxt = h[h["day"] == day + 1]["f_melt"]
        if d["f_melt"].max() >= 0.99 and (min(d["f_melt"].min(), nxt.min()) <= 0.01):
            cand.append((day, d["Q_collector_Wh"].sum()))
    if not cand:
        raise SystemExit("no day with a complete melt/freeze cycle")
    cand.sort(key=lambda x: x[1])
    return cand[len(cand) // 2][0], len(cand)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--regimes", type=int, nargs="*", default=[0, 1, 2])
    ap.add_argument("--dt", type=float, default=5.0)
    ap.add_argument("--hours", type=int, default=48)
    ap.add_argument("--cfd-csv", default=os.path.join(ROOT, "results", "cfd_doe_results.csv"))
    a = ap.parse_args()

    from src.design.schema import DesignVector
    from src.simulation.run_case import run_case
    import cfd_calibrated_greybox as cg

    phi_model, props, _ = cg.fit_phi_model(a.cfd_csv)
    p7 = pd.read_csv(os.path.join(PROJ, "results", "phase7_deployable_design_per_regime.csv"))
    fdir = os.path.join(ROOT, "cases_pht", "_forcing")
    os.makedirs(fdir, exist_ok=True)

    jobs, ctx = [], {}
    for r in p7.itertuples():
        reg = int(r.regime_id)
        if reg not in a.regimes:
            continue
        d, n, md, arr, pcm = float(r.capsule_diameter_m), int(r.n_capsule), float(r.flow_rate_kg_s), \
            r.arrangement, r.pcm_id
        dv = DesignVector(d, n, md, arr)
        out = run_case(STATE, reg, pcm, dv, record_hourly=True)
        h = out["hourly"].reset_index(drop=True)
        day, ncand = pick_day(h)
        w = h[(h["hour_index"] >= day * 24) & (h["hour_index"] < day * 24 + a.hours)].reset_index(drop=True)
        if len(w) < a.hours:
            w = h[(h["hour_index"] >= day * 24)].head(a.hours).reset_index(drop=True)
        t = np.arange(len(w)) * 3600.0
        Tw = w["T_w_C"].values + 273.15
        Tc = Tw + np.where(w["Q_collector_Wh"].values > 0, w["Q_collector_Wh"].values / (md * CP_W), 0.0)
        for tag, T in (("Tw", Tw), ("Tcoll", Tc)):
            with open(os.path.join(fdir, f"r{reg}_{tag}.csv"), "w") as f:
                f.write("t_s,T_K\n")
                for ti, Ti in zip(t, T):
                    f.write(f"{ti:.0f},{Ti:.4f}\n")
        phi_cfd = cg.phi_for(phi_model, props, pcm, d, md)
        ctx[reg] = dict(design=dict(pcm=pcm, d=d, n=n, mdot=md, arr=arr), day=int(day), n_candidate_days=ncand,
                        grey=w, phi_cfd=phi_cfd, T0_solid=float(w["T_pcm_C"].iloc[0] + 273.15),
                        T0_fluid=float(w["T_w_C"].iloc[0] + 273.15))
        base = ["--pcm", pcm, "--d", f"{d}", "--n", f"{n}", "--mdot", f"{md}", "--t-end-s", f"{(len(w) - 1) * 3600}",
                "--dt", f"{a.dt}", "--write-every", "3600", "--T-init-solid-K", f"{ctx[reg]['T0_solid']}",
                "--T-init-fluid-K", f"{ctx[reg]['T0_fluid']}"]
        for var, tag, phi in (("V1", "Tw", 1.0), ("V2", "Tcoll", 1.0), ("V3", "Tcoll", phi_cfd)):
            csvp = wsl_path(os.path.join(fdir, f"r{reg}_{tag}.csv"))
            jobs.append((f"bed_r{reg}_{var}", reg, var, base + ["--phi", f"{phi}", "--tin-csv", csvp]))

    print(f"{len(jobs)} bed runs", flush=True)
    res = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(run_bed, nm, args): (nm, reg, var) for nm, reg, var, args in jobs}
        for fu, (nm, reg, var) in futs.items():
            rc, out = fu.result()
            print(f"  {nm:14s} rc={rc}", flush=True)
            if rc != 0:
                print(out[-400:])
            res[(reg, var)] = rc

    rows = []
    for reg, c in ctx.items():
        g = c["grey"]
        hrs = np.arange(len(g))
        for var in ("V1", "V2", "V3"):
            f = os.path.join(ROOT, "cases_pht", f"bed_r{reg}_{var}", "hourly_bed.csv")
            if not os.path.exists(f):
                continue
            b = pd.read_csv(f)
            bt = np.interp(hrs * 3600.0, b["t_s"], b["T_solid_mean_K"]) - 273.15
            bf = np.interp(hrs * 3600.0, b["t_s"], b["f_melt_mean"])
            gt, gf = g["T_pcm_C"].values, g["f_melt"].values

            def cross(y, thr, up=True):
                idx = np.where((y[1:] >= thr) & (y[:-1] < thr))[0] if up else np.where((y[1:] < thr) & (y[:-1] >= thr))[0]
                return float(idx[0] + 1) if len(idx) else float("nan")

            rows.append(dict(
                regime=reg, variant=var, pcm=c["design"]["pcm"], d_m=c["design"]["d"], N=c["design"]["n"],
                mdot=c["design"]["mdot"], phi=1.0 if var != "V3" else c["phi_cfd"], day=c["day"],
                rmse_T_K=float(np.sqrt(np.mean((bt - gt) ** 2))), mean_dT_K=float(np.mean(bt - gt)),
                rmse_f=float(np.sqrt(np.mean((bf - gf) ** 2))),
                hours_f_gt_0p5_grey=int((gf > 0.5).sum()), hours_f_gt_0p5_bed=int((bf > 0.5).sum()),
                t_melt50_grey_h=cross(gf, 0.5), t_melt50_bed_h=cross(bf, 0.5),
                t_freeze50_grey_h=cross(gf, 0.5, up=False), t_freeze50_bed_h=cross(bf, 0.5, up=False),
                f_peak_grey=float(gf.max()), f_peak_bed=float(bf.max())))
    df = pd.DataFrame(rows)
    out_csv = os.path.join(ROOT, "results", "pht_vs_greybox.csv")
    df.to_csv(out_csv, index=False)
    print(df.round(3).to_string(index=False))
    with open(os.path.join(ROOT, "results", "pht_vs_greybox_context.json"), "w") as f:
        json.dump({str(k): {kk: vv for kk, vv in v.items() if kk != "grey"} for k, v in ctx.items()}, f, indent=1)
    print("wrote", out_csv)


if __name__ == "__main__":
    main()
