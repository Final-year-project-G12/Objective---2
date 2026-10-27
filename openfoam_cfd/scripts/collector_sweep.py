#!/usr/bin/env python3
"""
collector_sweep.py -- run the collector strip CFD over inlet temperature and loop flow rate, then fit the
efficiency line  eta = F_R(tau alpha) - F_R U_L (T_in - T_a)/G  and compare with the frozen config.

  python collector_sweep.py [--workers 3]
Writes results/collector_cfd_sweep.csv and results/collector_cfd_fit.json.
"""
import argparse
import csv
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import collector_make_case as cm  # noqa: E402

FROZEN = dict(fr_tau_alpha=0.75, fr_ul=4.5)


def wsl(p):
    p = os.path.abspath(p).replace("\\", "/")
    return f"/mnt/{p[0].lower()}{p[2:]}"


def run(name, **kw):
    out = os.path.join(ROOT, "cases_collector", name)
    if os.path.exists(os.path.join(out, "collector_metrics.json")):
        return json.load(open(os.path.join(out, "collector_metrics.json"))), cm_meta(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cm.build(out, **kw)
    r = subprocess.run(["wsl", "-d", "Ubuntu-24.04", "-e", "bash", wsl(os.path.join(HERE, "collector_run.sh")), wsl(out)],
                       capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        raise RuntimeError(name + ": " + r.stdout[-300:])
    import collector_postprocess as cp
    cp.main(out)
    return json.load(open(os.path.join(out, "collector_metrics.json"))), cm_meta(out)


def cm_meta(out):
    return json.load(open(os.path.join(out, "case_meta.json")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    jobs = [(f"sw_T{t:02d}_m030", dict(mdot_loop=0.03, T_in_C=float(t))) for t in (30, 40, 50, 60, 70)]
    jobs += [(f"sw_T40_m{int(m * 1000):03d}", dict(mdot_loop=m, T_in_C=40.0)) for m in (0.010, 0.050)]
    rows = []
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(run, n, **kw): (n, kw) for n, kw in jobs}
        for fu, (n, kw) in futs.items():
            res, meta = fu.result()
            an = meta["analytic"]
            x = (kw["T_in_C"] - meta["T_amb_C"]) / meta["G"]
            rows.append(dict(case=n, mdot_loop=kw["mdot_loop"], T_in_C=kw["T_in_C"], x_Km2_W=x,
                             Re=meta["Re_channel"], eta_cfd=res["eta"], eta_analytic=an["eta"],
                             Q_cfd_W=res["Q_u_W"], Q_analytic_W=an["Q_riser_W"],
                             T_out_cfd_C=res["T_out_C"], T_out_analytic_C=an["T_out_C"],
                             F_R_cfd=res["F_R_cfd"], F_R_analytic=an["F_R"], F_prime_analytic=an["F_prime"]))
            print(f"{n:16s} eta CFD {res['eta']:.4f}  analytic {an['eta']:.4f}", flush=True)
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    out_csv = os.path.join(ROOT, "results", "collector_cfd_sweep.csv")
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["mdot_loop"], r["T_in_C"])))
    # line fit on the 0.03 kg/s temperature series
    base = sorted([r for r in rows if abs(r["mdot_loop"] - 0.03) < 1e-9], key=lambda r: r["x_Km2_W"])
    x = np.array([r["x_Km2_W"] for r in base])
    y = np.array([r["eta_cfd"] for r in base])
    slope, icpt = np.polyfit(x, y, 1)
    fit = dict(F_R_tau_alpha_cfd=float(icpt), F_R_U_L_cfd=float(-slope), frozen=FROZEN,
               assumed=dict(tau_alpha=0.80, U_L=5.0), note="tau*alpha and U_L are INPUTS (assumed) here; "
               "CFD returns F_R: F_R_cfd = F_R_tau_alpha / tau_alpha = %.3f" % (icpt / 0.80),
               n_points=len(base), residual_rms=float(np.sqrt(np.mean((np.polyval([slope, icpt], x) - y) ** 2))))
    json.dump(fit, open(os.path.join(ROOT, "results", "collector_cfd_fit.json"), "w"), indent=1)
    print(json.dumps(fit, indent=1))


if __name__ == "__main__":
    main()
