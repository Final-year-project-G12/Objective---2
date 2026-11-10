#!/usr/bin/env python3
"""Freezing (discharge) check, B3: OpenFOAM liquid fraction of one r0 capsule cooled from liquid (64 C) by a fixed wall at the mains temperature
against the lumped capsule (repo kernel helpers) with the frozen closure (c 5, F 2) and cfd_closure_v1 (c 10, F 5).
usage: python scripts/freeze_compare.py cases/r0_discharge_mains_n20 [cases/r0_discharge_mains_n40 ...]  -> results/of_freeze_check.csv
Times are minutes until the liquid fraction falls to 0.9 / 0.5 / 0.1. Model-to-model only: the CFD is not validated against measurements (docs/07)."""
import os, sys
import numpy as np
import yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_lumped import read_cfd, meta_from_cfg, lumped_repo, ROOT

cfg = yaml.safe_load(open(os.path.join(ROOT, "configs", "rj_cases.yaml"), encoding="utf-8"))


def t_down(t, f, x):
    i = int(np.argmax(f <= x))
    return float(t[i]) / 60.0 if f[i] <= x else float("nan")


rows = []
meta = meta_from_cfg(cfg, "r0", "discharge_mains")
t_end = meta["bc"]["end_time_s"]
for name, c, F in (("lumped_frozen_c5_F2", 5.0, 2.0), ("lumped_cfd_closure_v1_c10_F5", 10.0, 5.0)):
    tt, ff = lumped_repo(meta, t_end, c=c, F=F, dt=1.0)
    rows.append((name, "", c, F, *[t_down(tt, ff, x) for x in (0.9, 0.5, 0.1)]))
for case in sys.argv[1:]:
    t, f, _ = read_cfd(case)
    rows.append(("openfoam", os.path.basename(case.rstrip("/\\")), "", "", *[t_down(t, f, x) for x in (0.9, 0.5, 0.1)]))
out = os.path.join(ROOT, "results", "of_freeze_check.csv")
with open(out, "w") as fh:
    fh.write("series,case,c,F,t_f90_min,t_f50_min,t_f10_min\n")
    for r in rows:
        fh.write(",".join(f"{x:.4g}" if isinstance(x, float) else str(x) for x in r) + "\n")
print(open(out).read())
