#!/usr/bin/env python3
"""
tank_postprocess.py -- stratification metrics and figures for a tank_make_case.py case.

  python tank_postprocess.py ../cases_tank/charge

Reads postProcessing/{meanT,outletT,profile}/0/*.dat and case_meta.json; writes
  <case>/tank_metrics.json , <case>/tank_profiles.png

Metrics (definitions stated so they can be cited):
  T_mean(t)           volume-average temperature
  T_out(t)            flow-weighted outlet temperature
  thermocline_10_90   vertical distance between the 10 % and 90 % points of the normalised axial
                      profile T*(x) = (T - T_cold)/(T_hot - T_cold), from the 10 probe heights
                      (linear interpolation; coarse -> a bound, not a measurement)
  MIX number          energy-weighted height moment method (Davidson 1994): 0 = perfectly stratified,
                      1 = fully mixed; moment of energy M = sum(E_i * x_i), M_str / M_mix from the same
                      total energy; MIX = (M_str - M_exp) / (M_str - M_mix). Computed from the probe
                      profile (equal height slabs).
  delivery (draw)     volume of water drawn until T_out falls below T_target (default 50 C, the Uttarakhand target in configs/system_config_shared.yaml; Rajasthan uses 45 C, the frozen
                      delivery target) and the fraction of the initial hot volume this represents
"""
import argparse
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

K0 = 273.15


def read_dat(p):
    rows = []
    for ln in open(p):
        if ln.startswith("#") or not ln.strip():
            continue
        rows.append([float(x) for x in ln.replace("(", " ").replace(")", " ").split()])
    return np.array(rows)


def mix_number(Tx, xs, Th, Tc):
    """Davidson (1994) MIX from an equal-slab profile. Tx at heights xs (bottom -> top)."""
    n = len(Tx)
    E = np.maximum(Tx - Tc, 0.0)                  # energy relative to the cold reference (equal slab mass)
    Etot = E.sum()
    if Etot <= 0:
        return float("nan")
    M_exp = (E * xs).sum()
    M_mix = Etot * xs.mean()
    # fully stratified: the same total energy packed into the top slabs at T_hot
    n_hot = Etot / max(Th - Tc, 1e-9)
    M_str = 0.0
    left = n_hot
    for i in range(n - 1, -1, -1):
        take = min(1.0, left)
        M_str += (Th - Tc) * take * xs[i]
        left -= take
        if left <= 0:
            break
    den = M_str - M_mix
    return float((M_str - M_exp) / den) if abs(den) > 1e-12 else float("nan")


def thermocline(Tx, xs, Th, Tc):
    s = (Tx - Tc) / max(Th - Tc, 1e-9)
    order = np.argsort(xs)
    xs, s = xs[order], s[order]
    def cross(level):
        for i in range(len(s) - 1):
            if (s[i] - level) * (s[i + 1] - level) <= 0 and s[i] != s[i + 1]:
                return xs[i] + (level - s[i]) * (xs[i + 1] - xs[i]) / (s[i + 1] - s[i])
        return float("nan")
    a, b = cross(0.1), cross(0.9)
    return abs(b - a) if np.isfinite(a) and np.isfinite(b) else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("--T-target", type=float, default=50.0)
    a = ap.parse_args()
    meta = json.load(open(os.path.join(a.case, "case_meta.json")))
    pp = os.path.join(a.case, "postProcessing")
    mean = read_dat(os.path.join(pp, "meanT", "0", "volFieldValue.dat"))
    out = read_dat(os.path.join(pp, "outletT", "0", "surfaceFieldValue.dat"))
    prof = read_dat(os.path.join(pp, "profile", "0", "T"))
    xs = np.array(meta["probe_heights_m"])
    t = prof[:, 0]
    TP = prof[:, 1:1 + len(xs)] - K0
    Th = max(meta["T_in_C"] or 0, meta["T_hot_C"], meta["T_init_C"])
    Tc = min(meta["T_init_C"], meta["T_in_C"] if meta["T_in_C"] is not None else 99, 25.0 if meta["mode"] == "draw" else 99)
    if meta["mode"] == "charge":
        Th, Tc = meta["T_in_C"], meta["T_init_C"]
    elif meta["mode"] == "draw":
        Th, Tc = meta["T_hot_C"], meta.get("T_mains_C", 25.0)
    res = dict(mode=meta["mode"], mdot_kg_s=meta["mdot_kg_s"], Re_port=meta["Re_port"], T_hot_ref_C=Th, T_cold_ref_C=Tc)
    res["t_s"] = t.tolist()
    res["MIX"] = [mix_number(TP[i], xs, Th, Tc) for i in range(len(t))]
    res["thermocline_10_90_m"] = [thermocline(TP[i], xs, Th, Tc) for i in range(len(t))]
    res["T_mean_C"] = [(float(np.interp(tt, mean[:, 0], mean[:, 1])) - K0) for tt in t]
    res["T_out_C"] = [(float(np.interp(tt, out[:, 0], out[:, 1])) - K0) for tt in t]
    if meta["mode"] == "draw":
        Vdrawn = meta["mdot_kg_s"] * t / 1000.0 * 1000.0            # litres (rho = 1000)
        Tout = np.array(res["T_out_C"])
        below = np.where(Tout < a.T_target)[0]
        i = below[0] if len(below) else None
        V_hot = meta["volume_L"] * meta["hot_fraction"]
        res["litres_at_Tout_below_target"] = float(Vdrawn[i]) if i is not None else None
        res["hot_volume_L_initial"] = V_hot
        res["delivered_fraction_of_hot_volume"] = float(Vdrawn[i] / V_hot) if i is not None else None
    json.dump(res, open(os.path.join(a.case, "tank_metrics.json"), "w"), indent=1)

    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2), constrained_layout=True)
    pick = np.linspace(0, len(t) - 1, 6).astype(int)
    for k in pick:
        ax[0].plot(TP[k], xs, marker="o", ms=3, label=f"t = {t[k] / 60:.0f} min")
    ax[0].set_xlabel("T on the mid-radius line [°C]")
    ax[0].set_ylabel("height above tank bottom [m]")
    ax[0].legend(fontsize=7)
    ax[0].set_title(f"{meta['mode']}: axial profiles")
    ax[1].plot(t / 60, res["T_out_C"], label="outlet")
    ax[1].plot(t / 60, res["T_mean_C"], label="tank mean")
    if meta["mode"] == "draw":
        ax[1].axhline(a.T_target, color="k", ls=":", lw=1)
    ax[1].set_xlabel("time [min]")
    ax[1].set_ylabel("temperature [°C]")
    ax[1].legend()
    ax[2].plot(t / 60, res["MIX"], label="MIX number (0 stratified, 1 mixed)")
    ax2 = ax[2].twinx()
    ax2.plot(t / 60, np.array(res["thermocline_10_90_m"]) * 100, color="tab:red", ls="--", label="thermocline thickness")
    ax2.set_ylabel("thermocline 10–90 % [cm]", color="tab:red")
    ax[2].set_xlabel("time [min]")
    ax[2].set_ylabel("MIX [-]")
    fig.savefig(os.path.join(a.case, "tank_profiles.png"), dpi=130)
    print(json.dumps({k: (v if not isinstance(v, list) else [round(x, 3) if x == x else None for x in v[-1:]])
                      for k, v in res.items() if k != "t_s"}, indent=1))


if __name__ == "__main__":
    main()
