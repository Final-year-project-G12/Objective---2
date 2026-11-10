#!/usr/bin/env python3
"""Richardson extrapolation / grid-convergence index (Celik et al. 2008 procedure) from the three-mesh study of the r0 charge_70 capsule.
usage: python scripts/gci.py [of_mesh_study.csv]   -> results/of_gci.csv
Meshes 20 / 40 / 80 cells across the radius, refinement ratio r = 2. Observed order p = ln((f3-f2)/(f2-f1)) / ln r with f1 the finest.
A valid GCI needs monotone convergence (0 < (f2-f1)/(f3-f2) < 1 gives p > 0); otherwise the file records p as negative and GCI as nan:
the solution is then NOT in the asymptotic range and no discretisation-error band can be quoted.
Model-to-model numerical check only; it says nothing about agreement with measurements."""
import math, os, sys
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "results", "of_mesh_study.csv")
ms = pd.read_csv(src).set_index("cells_radial")
r = 2.0
rows = []
for q in ("t50_s", "t90_s"):
    f3, f2, f1 = float(ms[q][20]), float(ms[q][40]), float(ms[q][80])
    ratio = (f3 - f2) / (f2 - f1)
    p = math.log(ratio) / math.log(r) if ratio > 0 else float("nan")
    monotone = ratio > 0
    converging = monotone and abs(f2 - f1) < abs(f3 - f2)
    if converging:
        f_ext = f1 + (f1 - f2) / (r ** p - 1.0)
        e21 = abs((f1 - f2) / f1)
        gci = 1.25 * e21 / (r ** p - 1.0) * 100.0
    else:
        f_ext, gci = float("nan"), float("nan")
    rows.append(dict(quantity=q, f_20=f3, f_40=f2, f_80=f1, change_40_80_pct=100.0 * (f1 - f2) / f2, ratio_eps32_over_eps21=ratio,
                     observed_order_p=p, monotone=monotone, converging=converging, richardson_extrapolated=f_ext, gci_fine_pct=gci))
out = pd.DataFrame(rows)
out.to_csv(os.path.join(ROOT, "results", "of_gci.csv"), index=False)
print(out.to_string())
