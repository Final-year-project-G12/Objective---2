#!/usr/bin/env python3
"""1-D spherical enthalpy (Stefan) solution of constrained, conduction-only melting: independent check of the CFD latent-heat source.
Same physics as `make_capsule_case.py --conduction-only`: isothermal melting at Tm, constant k, rho, cp, wall at T_wall from t=0.
usage: python scripts/stefan_sphere_1d.py V0_tan2009 -> prints times to 25/50/75/90 % melt (min)"""
import os, sys
import numpy as np, yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_lumped import ROOT

def run(R, k, rho, cp, L, Tm, T0, Tw, n=400, tend=40000.0, dm=1.0):
    r = (np.arange(n) + 0.5) * R / n; dr = R / n
    face = np.arange(n + 1) * dr
    H = np.full(n, cp * (T0 - Tm) if T0 < Tm else 0.0)
    def T_of(H): return np.where(H < 0, Tm + H / cp, np.where(H > L, Tm + (H - L) / cp, Tm))
    t, dt = 0.0, 0.05; out = []
    vol = 4 / 3 * np.pi * (face[1:] ** 3 - face[:-1] ** 3)
    while t < tend:
        T = T_of(H)
        Tx = np.concatenate([T, [Tw]])
        flux = np.zeros(n + 1)
        flux[1:n] = -k * (T[1:] - T[:-1]) / dr
        flux[n] = -k * (Tw - T[-1]) / (dr / 2)
        q = 4 * np.pi * face ** 2 * flux
        H += -(q[1:] - q[:-1]) * dt / (rho * vol)
        t += dt
        if int(t / dm) != int((t - dt) / dm): out.append((t, float(np.sum(np.clip(H, 0, L) / L * vol) / np.sum(vol))))
    return np.array(out)

if __name__ == "__main__":
    cfg = yaml.safe_load(open(os.path.join(ROOT, "configs", "rj_cases.yaml"), encoding="utf-8"))
    sc = cfg["scenarios"][sys.argv[1]]; p = cfg["pcm_properties"][sc["pcm"]]
    cp = 0.5 * (p["cp_solid"] + p["cp_liquid"])
    o = run(sc["radius_m"], p["k_solid"], p["rho_solid"], cp, p["latent_J_kg"], p["Tm_C"], sc["T_init_C"], sc["T_wall_C"])
    for x in (.25, .5, .75, .9):
        i = int(np.argmax(o[:, 1] >= x)); print(f"conduction-only 1-D: f>={x}: {o[i,0]/60:.1f} min")
