#!/usr/bin/env python3
"""Compare the OpenFOAM melt-fraction curve of one capsule with the O2 lumped capsule model and
fit the two lumped constants the report flags as assumed (Section 3.6):
  - conduction coefficient c in R_pcm = r / (c k)            (frozen: c = 5)
  - liquid-convection factor F applied once melt >= 0.5       (frozen: F = 2.0)

Two implementations of the same lumped capsule (one enthalpy node, Tm +/- half-width band, fixed wall T,
explicit enthalpy update  h += UA (T_wall - T_pcm) dt / m):
  * standalone (numba, fast)  - written to match the repo's rules: ONE conductivity k (database TC_W_mK),
    k_eff = k * F once f >= 0.5, R = r_in / (c k_eff A_in), mass = density_solid * V_inner (src/simulation/capsule_mass.py)
  * repo model (--use-repo-model) - calls the real kernel helpers of src/simulation/tank_model_multinode.py
    (_h_of_T, _T_f_of_h, _ua_node) with the water-side and wall resistances switched off, so only the PCM
    path r/(c k_eff) remains; c != 5 enters as k * c / 5 because the repo hard-codes 5.

Usage:
  python scripts/calibrate_lumped.py --parity r0 charge_70      # R1: standalone vs repo model, no CFD needed
  python scripts/calibrate_lumped.py cases/r0_charge_70_n40 [--use-repo-model]   # fit c, F against an OpenFOAM case
The CFD-to-lumped agreement is model-to-model, not a measurement.
Output: results/calib_<case>.csv / .png, results/of_model_parity.csv
"""
import argparse, glob, os, sys
import numpy as np
import yaml
from numba import njit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # rj_openfoam/
REPO = os.path.dirname(ROOT)                                           # objective2-rajasthan/
WALL_T = 0.0008                                                         # system_config_shared.yaml, pcm_integration.capsule_wall_thickness_m
K0 = 273.15


# --------------------------------------------------------------------------- inputs
def read_cfd(case):
    """postProcessing/meltAndTemp/*/volFieldValue.dat: columns time, volAverage(T), volAverage(alpha1) (mass-weighted)."""
    f = sorted(glob.glob(os.path.join(case, "postProcessing", "meltAndTemp", "*", "volFieldValue.dat")))
    if not f:
        sys.exit("no postProcessing/meltAndTemp output; run the case first")
    rows = {}
    for fn in f:
        for line in open(fn):
            if line.startswith("#") or not line.strip():
                continue
            p = line.split()
            rows[float(p[0])] = (float(p[2]), float(p[1]))                # time -> (alpha1, T); later restart wins
    ts = np.array(sorted(rows))
    return ts, np.array([rows[t][0] for t in ts]), np.array([rows[t][1] for t in ts])


def meta_from_cfg(cfg, design, scenario):
    """Same content as the case_meta.yaml that make_capsule_case.py writes, without needing a case."""
    sc = dict(cfg["scenarios"][scenario])
    des = cfg["designs"][design]
    if sc.get("wall_from") == "mains_regime_C":
        sc["T_wall_C"] = cfg["mains_regime_C"][design]
    hw = cfg["melting_half_width_K"]
    Tm = cfg["pcm_properties"][des["pcm"]]["Tm_C"] + K0
    return {"design": design, "scenario": scenario, "pcm": des["pcm"], "R_m": des["inner_radius_m"],
            "Tsol_K": Tm - hw, "Tliq_K": Tm + hw, "props": cfg["pcm_properties"][des["pcm"]], "bc": sc}


# --------------------------------------------------------------------------- standalone lumped capsule
@njit(cache=True)
def _lumped_core(R, Tsol, Tliq, L, cs, cl, k, m, Tw, T0, c, F, dt, n):
    A = 4.0 * np.pi * R * R
    span = Tliq - Tsol
    # enthalpy referenced to 0 at Tsol; same piecewise law as capsule_enthalpy.py with wall_cp = 0
    if T0 < Tsol:
        H = cs * (T0 - Tsol)
    elif T0 <= Tliq:
        H = L * (T0 - Tsol) / span
    else:
        H = L + cl * (T0 - Tliq)
    f_out = np.zeros(n + 1)
    T_out = np.zeros(n + 1)
    for i in range(n + 1):
        if H < 0.0:
            T, f = Tsol + H / cs, 0.0
        elif H <= L:
            f = H / L
            T = Tsol + f * span
        else:
            T, f = Tliq + (H - L) / cl, 1.0
        f_out[i] = f
        T_out[i] = T
        keff = k * (F if f >= 0.5 else 1.0)
        UA = A * c * keff / R
        H += UA * (Tw - T) * dt / m
    return f_out, T_out


def lumped(meta, t_end, c=5.0, F=2.0, dt=1.0):
    p, R = meta["props"], meta["R_m"]
    m = p["rho_solid"] * 4.0 / 3.0 * np.pi * R ** 3                     # repo mass: density_solid * inner volume
    n = int(round(t_end / dt))
    f, T = _lumped_core(R, meta["Tsol_K"], meta["Tliq_K"], p["latent_J_kg"], p["cp_solid"], p["cp_liquid"],
                        p["k_solid"], m, meta["bc"]["T_wall_C"] + K0, meta["bc"]["T_init_C"] + K0, c, F, dt, n)
    return np.arange(n + 1) * dt, f


# --------------------------------------------------------------------------- repo model (real kernel helpers)
def lumped_repo(meta, t_end, c=5.0, F=2.0, dt=1.0):
    sys.path.insert(0, REPO)
    from src.simulation.tank_model_multinode import _h_of_T, _T_f_of_h, _ua_node
    p, R = meta["props"], meta["R_m"]
    Ts, Tl = meta["Tsol_K"] - K0, meta["Tliq_K"] - K0
    L, cs, cl = p["latent_J_kg"], p["cp_solid"], p["cp_liquid"]
    d_out = 2.0 * (R + WALL_T)
    area_out = np.pi * d_out ** 2
    m = p["rho_solid"] * 4.0 / 3.0 * np.pi * R ** 3
    Tw, T0 = meta["bc"]["T_wall_C"], meta["bc"]["T_init_C"]
    k_pcm = p["k_solid"] * c / 5.0                                       # repo hard-codes 5 in R = r/(5 k_eff)
    h = _h_of_T(T0, Ts, Tl, L, cs, cl, 0.0)                              # x = 0: wall heat capacity switched off (CFD has no wall)
    n = int(round(t_end / dt))
    f_out = np.zeros(n + 1)
    for i in range(n + 1):
        Tp, f = _T_f_of_h(h, Ts, Tl, L, cs, cl, 0.0)
        f_out[i] = f
        # v huge -> water-side R ~ 0; wall_k huge -> wall R ~ 0: only r_in/(5 k_eff A_in) is left
        ua = _ua_node(1.0, d_out, area_out, 1e9, f, 1000.0, 0.63, 4.3, 6.5e-4, WALL_T, 1e12, k_pcm, F)
        h += ua * (Tw - Tp) * dt / m
    return np.arange(n + 1) * dt, f_out


def t_at(tt, ff, x):
    i = int(np.argmax(ff >= x))
    return float(tt[i]) if ff[i] >= x else float("nan")


# --------------------------------------------------------------------------- R1 parity
def parity(design, scenario):
    cfg = yaml.safe_load(open(os.path.join(ROOT, "configs", "rj_cases.yaml"), encoding="utf-8"))
    meta = meta_from_cfg(cfg, design, scenario)
    t_end = meta["bc"]["end_time_s"]
    out = os.path.join(ROOT, "results", "of_model_parity.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    new = not os.path.exists(out)
    with open(out, "a") as fh:
        if new:
            fh.write("design,scenario,c,F,dt_s,max_abs_diff_meltfrac,t50_standalone_s,t50_repo_s,t90_standalone_s,t90_repo_s\n")
        for c, F in ((5.0, 2.0), (5.0, 1.0), (8.0, 3.0)):
            ts, fs = lumped(meta, t_end, c, F)
            tr, fr = lumped_repo(meta, t_end, c, F)
            d = float(np.max(np.abs(fs - fr)))
            fh.write(f"{design},{scenario},{c},{F},1,{d:.6f},{t_at(ts, fs, .5)},{t_at(tr, fr, .5)},{t_at(ts, fs, .9)},{t_at(tr, fr, .9)}\n")
            print(f"{design} {scenario} c={c} F={F}: max|standalone-repo| = {d:.6f}")


# --------------------------------------------------------------------------- fit
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case", nargs="?")
    ap.add_argument("--use-repo-model", action="store_true")
    ap.add_argument("--parity", nargs=2, metavar=("DESIGN", "SCENARIO"))
    a = ap.parse_args()
    if a.parity:
        return parity(*a.parity)
    meta = yaml.safe_load(open(os.path.join(a.case, "case_meta.yaml")))
    if meta["bc"]["bc"] != "fixedWall":
        sys.exit("calibration uses the fixed-wall scenarios only")
    t, f_cfd, _ = read_cfd(a.case)
    model = lumped_repo if a.use_repo_model else lumped
    DT = 5.0

    def err(c, F):
        tl, fl = model(meta, t[-1], c, F, DT)
        return float(np.sqrt(np.mean((np.interp(t, tl, fl) - f_cfd) ** 2)))

    base = err(5.0, 2.0)
    grid = [(c, F, err(c, F)) for c in np.linspace(2, 10, 17) for F in np.linspace(1, 5, 17)]
    cb, Fb, eb = min(grid, key=lambda r: r[2])
    tl0, fl0 = model(meta, t[-1], 5.0, 2.0, DT)
    tl1, fl1 = model(meta, t[-1], cb, Fb, DT)

    name = os.path.basename(a.case.rstrip("/\\"))
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    out = os.path.join(ROOT, "results", f"calib_{name}.csv")
    with open(out, "w") as fh:
        fh.write("case,model,c,F,rmse_meltfrac,t50_s,t90_s\n")
        fh.write(f"{name},openfoam,,,0,{t_at(t, f_cfd, 0.5)},{t_at(t, f_cfd, 0.9)}\n")
        fh.write(f"{name},lumped_frozen,5,2,{base:.4f},{t_at(tl0, fl0, 0.5)},{t_at(tl0, fl0, 0.9)}\n")
        fh.write(f"{name},lumped_fitted,{cb:.2f},{Fb:.2f},{eb:.4f},{t_at(tl1, fl1, 0.5)},{t_at(tl1, fl1, 0.9)}\n")
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        plt.figure(figsize=(6, 4))
        plt.plot(t / 3600, f_cfd, "k", label="OpenFOAM")
        plt.plot(tl0 / 3600, fl0, "--", label="lumped c=5, F=2 (frozen)")
        plt.plot(tl1 / 3600, fl1, ":", label=f"lumped c={cb:.1f}, F={Fb:.1f} (fitted)")
        plt.xlabel("time (h)"); plt.ylabel("melt fraction"); plt.legend(); plt.title(name); plt.tight_layout()
        plt.savefig(out.replace(".csv", ".png"), dpi=150)
    except ImportError:
        pass
    print(open(out).read())


if __name__ == "__main__":
    main()
