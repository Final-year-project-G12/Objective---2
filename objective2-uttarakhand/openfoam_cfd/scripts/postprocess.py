#!/usr/bin/env python3
"""
postprocess.py -- turn one finished capsule CFD case into KPIs and compare it
against the project's own grey-box capsule model (same scenario).

Reads  <case>/postProcessing/{meltAndTemp,wallQ,totalVolume}/0/*.dat
       <case>/case_meta.json
Writes <case>/kpi.json   (and returns the dict)

KPIs (per ONE capsule, SI / kJ):
  t_melt_50_s, t_melt_90_s, t_melt_99_s   mass-weighted liquid fraction crossing
  E_window_kJ        stored energy at the end of the charging window
  E_end_kJ, E_full_kJ  stored at end of run / theoretical full charge
  f_melt_window      liquid fraction at window end
  P_mean_window_W    mean charging power over the window
  energy_residual_pct  |int(Q dt) - dE| / dE   (QC gate, must be small)
  greybox_t_melt_90_s  melt time predicted by src/simulation lumped capsule model
  R_pcm_scale_equivalent  factor on the grey-box R_pcm = r/(5 k_eff) that makes the
                       lumped model reproduce the CFD t_melt_90 (1.0 = grey-box right;
                       frozen x2 convection factor kept as configured)
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _paths                                                    # noqa: E402
PROJ = _paths.project_root()                                     # objective2-uttarakhand/
sys.path.insert(0, PROJ)
K0 = 273.15


def read_dat(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for ln in f:
            if ln.startswith("#") or not ln.strip():
                continue
            rows.append([float(x) for x in ln.split()])
    return np.array(rows)


def first_crossing(t, y, thr):
    idx = np.where(y >= thr)[0]
    if len(idx) == 0:
        return float("nan")
    i = idx[0]
    if i == 0:
        return float(t[0])
    return float(t[i - 1] + (thr - y[i - 1]) * (t[i] - t[i - 1]) / max(y[i] - y[i - 1], 1e-12))


# ---------------------------------------------------------------------------
# project grey-box capsule (reuses src/simulation code; single source of truth)
# ---------------------------------------------------------------------------
def greybox_melt_time(meta, enhancement, thr=0.9, t_max=3 * 86400.0, dt=2.0, r_scale=1.0):
    """Lumped single-capsule charge at constant water temperature, using the
    SAME conductance expression as src/simulation/heat_transfer.ua_eff_total_w_k
    (1/UA = 1/(h A) + t_al/(k_al A) + r/(5 k_eff A)) and the SAME enthalpy
    relation as capsule_enthalpy.py (melting band Tm +/- 1 K)."""
    from src.simulation.capsule_enthalpy import (PCMThermalProps, TREF_C,
                                                 temperature_and_liquid_fraction_of_enthalpy,
                                                 enthalpy_of_temperature)
    d = meta["d_m"]
    r = d / 2.0
    area = math.pi * d * d
    vol = math.pi * d ** 3 / 6.0
    props = PCMThermalProps(Tm_C=meta["Tm_C"], latent_heat_J_kg=meta["L_kJ_kg"] * 1e3,
                            cp_solid_J_kgK=meta["cp_avg"], cp_liquid_J_kgK=meta["cp_avg"],
                            conductivity_W_mK=meta["k"], density_kg_m3=meta["rho_s"],
                            melting_half_width_K=1.0)
    m = vol * props.density_kg_m3
    h_w = meta["h_w_W_m2K"]
    t_al, k_al = 0.0008, 205.0
    T_w = meta["T_hot_C"]
    H = enthalpy_of_temperature(meta["T_init_C"], props)
    t = 0.0
    out = []
    while t < t_max:
        T, f = temperature_and_liquid_fraction_of_enthalpy(H, props)
        k_eff = props.conductivity_W_mK * (enhancement if f >= 0.5 else 1.0)
        R = 1.0 / (h_w * area) + t_al / (k_al * area) + r_scale * r / (5.0 * k_eff * area)
        q = (T_w - T) / R
        H += q * dt / m
        t += dt
        out.append((t, f))
        if f >= thr:
            return t
    return float("nan")


def r_pcm_scale_equivalent(meta, target_t90, enhancement=2.0):
    """Factor phi on the grey-box PCM-side resistance (R_pcm = phi * r/(5 k_eff))
    that makes the lumped model reproduce the CFD 90 % melt time, with the
    frozen x2 liquid-convection factor left as configured.

    phi < 1  -> the lumped r/(5k) is too pessimistic (CFD melts faster)
    phi > 1  -> the lumped model is too optimistic.

    NOTE: the frozen x2 factor only acts once f_melt >= 0.5, so it can NOT
    pull t90 below the solid-phase half-melt time; a scale on R_pcm is the
    parameter that can. (First CFD point: see docs/CFD_FINDINGS.md.)"""
    if not np.isfinite(target_t90):
        return float("nan")
    lo, hi = 0.02, 8.0
    t_lo = greybox_melt_time(meta, enhancement, r_scale=lo)
    t_hi = greybox_melt_time(meta, enhancement, r_scale=hi)
    if not np.isfinite(t_lo):
        return float("nan")
    if not np.isfinite(t_hi):
        t_hi = float("inf")
    if not (t_lo <= target_t90 <= t_hi):
        return float("nan")
    for _ in range(40):
        mid = math.sqrt(lo * hi)
        tm = greybox_melt_time(meta, enhancement, r_scale=mid)
        if tm > target_t90:
            hi = mid
        else:
            lo = mid
    return math.sqrt(lo * hi)


# ---------------------------------------------------------------------------
def extract(case_dir, window_h=6.0, do_greybox=True):
    meta = json.load(open(os.path.join(case_dir, "case_meta.json")))
    pp = os.path.join(case_dir, "postProcessing")
    ma = read_dat(os.path.join(pp, "meltAndTemp", "0", "volFieldValue.dat"))
    wq = read_dat(os.path.join(pp, "wallQ", "0", "surfaceFieldValue.dat"))
    tv = read_dat(os.path.join(pp, "totalVolume", "0", "volFieldValue.dat"))

    scale = 360.0 / meta["wedge_deg"]
    t = ma[:, 0]
    Tavg = ma[:, 1]
    alpha = np.clip(ma[:, 2], 0.0, 1.0)
    m_cap = float(tv[-1, 1]) * scale
    cp, L = meta["cp_avg"], meta["L_kJ_kg"] * 1e3
    T0 = meta["T_init_C"] + K0

    E = m_cap * (cp * (Tavg - T0) + L * alpha)                         # J
    tq, q = wq[:, 0], np.abs(wq[:, 1]) * scale                          # W
    qi = np.interp(t, tq, q)
    Ein = np.concatenate([[0.0], np.cumsum(0.5 * (qi[1:] + qi[:-1]) * np.diff(t))])
    resid = abs(Ein[-1] - E[-1]) / max(E[-1], 1e-9) * 100.0

    tw = window_h * 3600.0
    if t[-1] >= tw:
        Ew = float(np.interp(tw, t, E))
        fw = float(np.interp(tw, t, alpha))
        Pw = float(np.interp(tw, t, Ein) / tw)
        extrap = False
    else:                                                             # run stopped after melt
        Ew, fw, Pw, extrap = float(E[-1]), float(alpha[-1]), float(Ein[-1] / t[-1]), True
    E_full = m_cap * (cp * (meta["T_hot_C"] + K0 - T0) + L)

    k = dict(
        case=os.path.basename(os.path.abspath(case_dir)),
        pcm=meta["pcm"], d_m=meta["d_m"], mdot_kg_s=meta["mdot_kg_s"], dT_K=meta["dT_K"],
        tank_volume_L=meta["tank_volume_L"], h_w_W_m2K=meta["h_w_W_m2K"], Re_p=meta["Re_p"],
        Bi=meta["Bi"], Ste=meta["Ste"], conduction_only=meta["conduction_only"],
        m_capsule_kg=m_cap, n_cells=int(round(float(meta["n_cells_est"]))),
        t_melt_50_s=first_crossing(t, alpha, 0.5),
        t_melt_90_s=first_crossing(t, alpha, 0.9),
        t_melt_99_s=first_crossing(t, alpha, 0.99),
        E_window_kJ=Ew / 1e3, E_end_kJ=float(E[-1]) / 1e3, E_full_kJ=E_full / 1e3,
        f_melt_window=fw, P_mean_window_W=Pw, t_end_s=float(t[-1]),
        extrapolated_to_window=bool(extrap),
        energy_residual_pct=float(resid),
        qc_energy_ok=bool(resid < 3.0),
    )
    if do_greybox and not meta["conduction_only"] and meta.get("bc_mode", "convective") == "convective":
        try:
            gb = greybox_melt_time(meta, 2.0)
            k["greybox_t_melt_90_s_x2"] = gb
            k["greybox_over_cfd_t90"] = gb / k["t_melt_90_s"] if np.isfinite(k["t_melt_90_s"]) else float("nan")
            k["R_pcm_scale_equivalent"] = r_pcm_scale_equivalent(meta, k["t_melt_90_s"])
        except Exception as ex:                                       # keep CFD KPIs even if grey-box import fails
            k["greybox_error"] = repr(ex)
    json.dump(k, open(os.path.join(case_dir, "kpi.json"), "w"), indent=2)
    return k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case_dir")
    ap.add_argument("--window-h", type=float, default=6.0)
    a = ap.parse_args()
    print(json.dumps(extract(a.case_dir, a.window_h), indent=2))


if __name__ == "__main__":
    main()
