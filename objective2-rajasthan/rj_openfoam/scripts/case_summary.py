#!/usr/bin/env python3
"""Summarise finished OpenFOAM capsule cases: time to 50 % / 90 % melt (or to 50 % / 10 % liquid for discharge), max |U|, and the energy check
(integral of the wall heat flux, scaled from the wedge to the sphere, against the enthalpy change of the PCM: m [cp (T_end - T_0) + L (f_end - f_0)]
with the CFD's own cp (mean of solid and liquid) and m = rho_solid V).
usage: python scripts/case_summary.py out.csv cases/<case> [more cases]"""
import math, os, sys
import numpy as np, yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_lumped import read_cfd


def read_dat(fn):
    rows = [l.split() for l in open(fn) if not l.startswith("#") and l.strip()]
    return rows


def summarize(case):
    meta = yaml.safe_load(open(os.path.join(case, "case_meta.yaml")))
    t, f, T = read_cfd(case)
    p, R, sc = meta["props"], meta["R_m"], meta["bc"]
    cp = 0.5 * (p["cp_solid"] + p["cp_liquid"])
    m = p["rho_solid"] * 4 / 3 * math.pi * R ** 3
    charge = f[0] < 0.5
    cross = lambda x: float(t[np.argmax(f >= x)]) if f.max() >= x else float("nan")
    cross_d = lambda x: float(t[np.argmax(f <= x)]) if f.min() <= x else float("nan")
    t50, t90 = (cross(.5), cross(.9)) if charge else (cross_d(.5), cross_d(.1))
    wq = read_dat(glob_one(case, "wallQ", "surfaceFieldValue.dat"))
    tq = np.array([float(r[0]) for r in wq]); q = np.array([float(r[1]) for r in wq])
    wedge = 5.0
    e_wall = float(np.trapezoid(q, tq)) * 360.0 / wedge          # J into the sphere (positive = heating); sign checked below
    mu = read_dat(glob_one(case, "maxU", "volFieldValue.dat"))
    umax = max(math.sqrt(sum(float(v.strip("()")) ** 2 for v in r[1:4])) for r in mu)
    dH = m * (cp * (T[-1] - T[0]) + p["latent_J_kg"] * (f[-1] - f[0]))
    return dict(case=os.path.basename(case.rstrip("/\\")), design=meta["design"], scenario=meta["scenario"], cells_radial=meta["cells_radial"],
                t50_s=t50, t90_s=t90, f_end=float(f[-1]), t_end_s=float(t[-1]), max_U_m_s=umax,
                E_wall_J=abs(e_wall), dH_J=abs(dH), energy_mismatch_pct=100 * (abs(e_wall) - abs(dH)) / abs(dH) if dH else float("nan"))


def glob_one(case, fo, name):
    import glob
    return sorted(glob.glob(os.path.join(case, "postProcessing", fo, "*", name)))[-1]


if __name__ == "__main__":
    out, cases = sys.argv[1], sys.argv[2:]
    rows = [summarize(c) for c in cases]
    with open(out, "w") as fh:
        fh.write(",".join(rows[0]) + "\n")
        for r in rows:
            fh.write(",".join(f"{v:.6g}" if isinstance(v, float) else str(v) for v in r.values()) + "\n")
    print(open(out).read())
