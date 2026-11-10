#!/usr/bin/env python3
"""S9 / C5 spot-check, B3: for each chosen v3 design (r0, r1, r2) one capsule is melted by a fixed 70 C wall in OpenFOAM (40 cells across the radius)
and compared with the lumped capsule (repo kernel helpers) under the frozen closure (c 5, F 2) and cfd_closure_v1 (c 10, F 5).
usage: python scripts/spotcheck_compare.py r0=<case dir> r1=<case dir> r2=<case dir>   -> results/of_spotcheck.csv
Columns: time to 50 / 90 % liquid fraction in minutes (blank = not reached in the run) and the melt-fraction RMSE against the CFD curve.
Model-to-model only; the CFD is an unvalidated upper bound on the melt rate (docs/07). The gap is closure uncertainty, not an error bar on a measurement."""
import os, sys
import numpy as np
import yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_lumped import read_cfd, meta_from_cfg, lumped_repo, ROOT

cfg = yaml.safe_load(open(os.path.join(ROOT, "configs", "rj_cases.yaml"), encoding="utf-8"))


def t_up(t, f, x):
    i = int(np.argmax(f >= x))
    return float(t[i]) / 60.0 if f[i] >= x else float("nan")


rows = []
for arg in sys.argv[1:]:
    d, case = arg.split("=", 1)
    meta = meta_from_cfg(cfg, d, "charge_70")
    t, f, _ = read_cfd(case)
    rows.append((d, meta["pcm"], meta["R_m"] * 1000, "openfoam_40cells", "", "", t_up(t, f, 0.5), t_up(t, f, 0.9), 0.0))
    for name, c, F in (("lumped_frozen_c5_F2", 5.0, 2.0), ("lumped_cfd_closure_v1_c10_F5", 10.0, 5.0)):
        tt, ff = lumped_repo(meta, float(t[-1]), c=c, F=F, dt=1.0)
        rm = float(np.sqrt(np.mean((np.interp(t, tt, ff) - f) ** 2)))
        rows.append((d, meta["pcm"], meta["R_m"] * 1000, name, c, F, t_up(tt, ff, 0.5), t_up(tt, ff, 0.9), rm))
out = os.path.join(ROOT, "results", "of_spotcheck.csv")
with open(out, "w") as fh:
    fh.write("design,pcm,R_in_mm,series,c,F,t50_min,t90_min,rmse_meltfrac_vs_cfd\n")
    for r in rows:
        fh.write(",".join(f"{x:.4g}" if isinstance(x, float) else str(x) for x in r) + "\n")
print(open(out).read())
