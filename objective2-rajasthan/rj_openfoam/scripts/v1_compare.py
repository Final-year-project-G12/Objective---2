#!/usr/bin/env python3
"""V1 benchmark: OpenFOAM liquid fraction vs time of the Dong et al. 2022 sphere (constrained melting, n-octadecane, 34.3 mm radius,
2 mm resin shell, bath 10 K above Tm) against the experimental points of Fig. 7 (results/dong2022_fig7_sphere_digitised.csv, read by eye).
usage: python scripts/v1_compare.py cases/lit_V1_dong2022_n40_glass [more cases...]   -> results/of_v1_benchmark.csv (+ .png)
Model-to-experiment comparison for ONE sphere (the paper's own curve is the experiment; it gives no CFD sphere curve)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_lumped import read_cfd, ROOT

ref = np.array([[float(x) for x in l.split(",")[1:]] for l in open(os.path.join(ROOT, "results", "dong2022_fig7_sphere_digitised.csv"))
                if l.startswith("experimental")])


def t_at(t, f, x):
    i = int(np.argmax(f >= x))
    return float(t[i]) / 60.0 if f[i] >= x else float("nan")


rows, curves = [("experimental", "", *[t_at(ref[:, 0] * 60, ref[:, 1], x) for x in (.25, .5, .75, .9)], float("nan"))], {}
for case in sys.argv[1:]:
    t, f, _ = read_cfd(case)
    name = os.path.basename(case.rstrip("/\\"))
    curves[name] = (t, f)
    m = (t / 60 <= 143) & (t > 0)
    ex = np.interp(t / 60, ref[:, 0], ref[:, 1])
    rows.append(("openfoam", name, *[t_at(t, f, x) for x in (.25, .5, .75, .9)], float(np.sqrt(np.mean((f[m] - ex[m]) ** 2)))))
out = os.path.join(ROOT, "results", "of_v1_benchmark.csv")
with open(out, "w") as fh:
    fh.write("series,case,t25_min,t50_min,t75_min,t90_min,rmse_vs_experiment\n")
    for r in rows:
        fh.write(",".join(f"{x:.4g}" if isinstance(x, float) else str(x) for x in r) + "\n")
print(open(out).read())
try:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    plt.figure(figsize=(6, 4.2))
    plt.plot(ref[:, 0], ref[:, 1], "ks", label="Dong 2022 experiment (sphere)")
    for n, (t, f) in curves.items():
        plt.plot(t / 60, f, "--", label=n)
    plt.xlabel("time (min)"); plt.ylabel("liquid fraction"); plt.legend(fontsize=7); plt.tight_layout()
    plt.savefig(out.replace(".csv", ".png"), dpi=150)
except ImportError:
    pass
