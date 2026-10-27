#!/usr/bin/env python3
"""
plot_pht_vs_greybox.py -- figure comparing the packed-bed OpenFOAM runs (V1/V2/V3) with the
grey-box single node for each regime: PCM temperature and melt fraction vs hour.

  python plot_pht_vs_greybox.py            -> ../results/pht_vs_greybox.png
Needs the bed runs from pht_vs_greybox.py (cases_pht/bed_r<regime>_V<k>/hourly_bed.csv).
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import _paths  # noqa: E402

PROJ = _paths.project_root()
sys.path.insert(0, PROJ)
from src.design.schema import DesignVector            # noqa: E402
from src.simulation.run_case import run_case          # noqa: E402

ctx = json.load(open(os.path.join(ROOT, "results", "pht_vs_greybox_context.json")))
LAB = {"V1": "bed, water-node forcing, φ=1", "V2": "bed, collector-outlet forcing, φ=1",
       "V3": "bed, collector-outlet forcing, φ=CFD"}
COL = {"V1": "tab:green", "V2": "tab:orange", "V3": "tab:red"}

fig, axs = plt.subplots(2, len(ctx), figsize=(5.0 * len(ctx), 6.4), sharex=True, constrained_layout=True)
axs = np.atleast_2d(axs).reshape(2, -1)
for j, (reg, c) in enumerate(sorted(ctx.items(), key=lambda kv: int(kv[0]))):
    dsg = c["design"]
    out = run_case("rajasthan", int(reg), dsg["pcm"], DesignVector(dsg["d"], dsg["n"], dsg["mdot"], dsg["arr"]),
                   record_hourly=True)
    h = out["hourly"].reset_index(drop=True)
    w = h[(h["hour_index"] >= c["day"] * 24)].head(48).reset_index(drop=True)
    hrs = np.arange(len(w))
    ax = axs[0, j]
    ax.plot(hrs, w["T_w_C"], color="0.6", lw=1, label="grey-box water node")
    ax.plot(hrs, w["T_pcm_C"], color="k", lw=2, label="grey-box PCM")
    for v in ("V1", "V2", "V3"):
        f = os.path.join(ROOT, "cases_pht", f"bed_r{reg}_{v}", "hourly_bed.csv")
        if os.path.exists(f):
            b = pd.read_csv(f)
            ax.plot(b["t_s"] / 3600, b["T_solid_mean_K"] - 273.15, color=COL[v], lw=1.4, ls="--", label=LAB[v])
    ax.set_title(f"regime {reg}: {dsg['pcm']}, d={dsg['d']*1e3:.0f} mm, N={dsg['n']}", fontsize=10)
    ax.set_ylabel("temperature [°C]")
    ax = axs[1, j]
    ax.plot(hrs, w["f_melt"], color="k", lw=2, label="grey-box")
    for v in ("V1", "V2", "V3"):
        f = os.path.join(ROOT, "cases_pht", f"bed_r{reg}_{v}", "hourly_bed.csv")
        if os.path.exists(f):
            b = pd.read_csv(f)
            ax.plot(b["t_s"] / 3600, b["f_melt_mean"], color=COL[v], lw=1.4, ls="--")
    ax.set_ylabel("melt fraction [-]")
    ax.set_xlabel("hour from 00:00 of the representative day")
axs[0, 0].legend(fontsize=7, loc="upper right")
out_png = os.path.join(ROOT, "results", "pht_vs_greybox.png")
fig.savefig(out_png, dpi=140)
print("wrote", out_png)
