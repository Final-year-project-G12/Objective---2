#!/usr/bin/env python3
"""V0 benchmark: compare OpenFOAM liquid fraction vs time of the Tan et al. 2009 n-octadecane sphere cases with the paper's
experimental points and Fluent curve (results/tan2009_fig4_digitised.csv, read by eye from Fig. 4).
usage: python scripts/v0_compare.py cases/lit_V0_tan2009_n40 [more cases...]   -> results/of_v0_benchmark.csv (+ .png)
Model-to-experiment comparison for ONE sphere; the paper itself attributes the CFD/experiment gap to the thermocouple support."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_lumped import read_cfd, ROOT

ref = {"experimental": [], "fluent": []}
for l in open(os.path.join(ROOT, "results", "tan2009_fig4_digitised.csv")):
    if l.startswith("#") or l.startswith("series"):
        continue
    s, t, f = l.strip().split(",")
    ref[s].append((float(t), float(f)))
ref = {k: np.array(v) for k, v in ref.items()}


def t_at(t, f, x):
    i = int(np.argmax(f >= x))
    return float(t[i]) / 60.0 if f[i] >= x else float("nan")


rows, curves = [], {}
for k, v in ref.items():
    rows.append((k, "", *[t_at(v[:, 0] * 60, v[:, 1], x) for x in (.25, .5, .75, .9)], float("nan"), float("nan")))
for case in sys.argv[1:]:
    t, f, _ = read_cfd(case)
    curves[os.path.basename(case.rstrip("/\\"))] = (t, f)
    ex = np.interp(t / 60, ref["experimental"][:, 0], ref["experimental"][:, 1])
    fl = np.interp(t / 60, ref["fluent"][:, 0], ref["fluent"][:, 1])
    m = t / 60 <= 140
    rows.append(("openfoam", os.path.basename(case.rstrip("/\\")), *[t_at(t, f, x) for x in (.25, .5, .75, .9)],
                 float(np.sqrt(np.mean((f[m] - ex[m]) ** 2))), float(np.sqrt(np.mean((f[m] - fl[m]) ** 2)))))
out = os.path.join(ROOT, "results", "of_v0_benchmark.csv")
with open(out, "w") as fh:
    fh.write("series,case,t25_min,t50_min,t75_min,t90_min,rmse_vs_experiment,rmse_vs_fluent\n")
    for r in rows:
        fh.write(",".join(f"{x:.4g}" if isinstance(x, float) else str(x) for x in r) + "\n")
print(open(out).read())
try:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    plt.figure(figsize=(6, 4.2))
    plt.plot(ref["experimental"][:, 0], ref["experimental"][:, 1], "ks", label="Tan 2009 experiment")
    plt.plot(ref["fluent"][:, 0], ref["fluent"][:, 1], "k-", label="Tan 2009 Fluent")
    for n, (t, f) in curves.items():
        plt.plot(t / 60, f, "--", label=n)
    plt.xlabel("time (min)"); plt.ylabel("liquid fraction"); plt.legend(fontsize=7); plt.tight_layout()
    plt.savefig(out.replace(".csv", ".png"), dpi=150)
except ImportError:
    pass
