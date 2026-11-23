"""
scripts/r9_rebuild_figures.py  -  figures of the common-plant rebuild (results/plots_common100L/)
==================================================================================================
Reads saved rebuild results only; nothing is simulated.
  rb1_pareto_fronts      per regime: every simulated design of the three PCMs (cheap fidelity) as mean g_window vs d_overheat, coloured
                         by PCM mass; the non-dominated set outlined; the funnel's pick marked; the band around zero shaded (plan L6:
                         "report the whole Pareto front ... and the chosen point on it")
  rb2_gain_vs_fraction   DOE mean g_window and worst-anchor g_window against PCM fraction, per regime (all three PCMs)
  rb3_band               band components per regime (g_window)
  rb4_test_years         2006-2010 one-shot test: per-year mean g_window of the frozen designs (pick bold), worst anchor, band
  rb5_timestep           L3 change per halving of the primary metric and of annual useful energy, against the 0.05 % line
Usage: python scripts/r9_rebuild_figures.py
"""
import glob
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.optimize.nsga2 import non_dominated_mask       # noqa: E402
from src.design.box import full_dt                       # noqa: E402
from src.io_utils import load_state_config               # noqa: E402

DEMAND_L = float(load_state_config("uttarakhand")["demand_profile"]["daily_total_L"])

RD = ROOT / "results"
OUT = RD / "plots_common100L"
REG = (0, 1, 2, 3)
RC = {0: "#1f77b4", 1: "#ff7f0e", 2: "#2ca02c", 3: "#9467bd"}
plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": .25, "axes.spines.top": False, "axes.spines.right": False})


def band(r):
    b = pd.read_csv(RD / "wp6_band.csv")
    return float(b[(b.scope == f"r{r}") & (b.objective == "g_window")].band.iloc[0])


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT / f"{name}.png", dpi=150)
    plt.close(fig)
    print("wrote", name)


def clean(s):
    return str(s).replace("�", "").replace("®", "")


def rb1():
    fig, ax = plt.subplots(1, 4, figsize=(17, 4.2))
    for i, r in enumerate(REG):
        pts = pd.concat([pd.read_csv(f).assign(pcm_rank=int(f[-5])) for f in sorted(glob.glob(str(RD / f"g9_points_r{r}_p[1-3].csv")))])
        ok = pts[pts.feasible == True]  # noqa: E712
        sc = ax[i].scatter(ok.d_overheat, ok.g_window, c=ok.pcm_mass_kg, cmap="viridis", s=10, alpha=.7)
        F = np.column_stack([-ok.g_window, -ok.g_annual, ok.d_overheat])
        nd = ok[non_dominated_mask(F)]
        ax[i].scatter(nd.d_overheat, nd.g_window, facecolors="none", edgecolors="k", s=28, lw=.8, label="non-dominated")
        sel = json.loads((RD / f"g10_selection_r{r}.json").read_text())
        ch = sel["chosen"]
        m = ok[(ok.R_in_m.round(6) == round(ch["R_in_m"], 6)) & (ok.N == ch["N"]) & (ok.arrangement == ch["arrangement"])]
        if len(m):
            ax[i].scatter(m.d_overheat, m.g_window, marker="*", s=220, c="#c0392b", edgecolors="k", zorder=5, label="funnel pick (tested)")
        ax[i].axhspan(-band(r), band(r), color="#27ae60", alpha=.15, label="band around zero")
        ax[i].axhline(0, color="k", lw=.7)
        ax[i].set(title=f"Regime {r}: {sel['recommendation'].replace('_', '-')}", xlabel="extra guard hours (h/yr)",
                  ylabel="mean paired g_window (kWh/yr)")
        ax[i].legend(fontsize=6.5, loc="lower left")
        fig.colorbar(sc, ax=ax[i], label="PCM mass (kg)")
    fig.suptitle(f"Pareto fronts, 100 L / 2.0 m2 / {DEMAND_L:g} L/day (cheap fidelity, all simulated designs of the three O1 PCMs)")
    save(fig, "rb1_pareto_fronts")


def rb2():
    fig, ax = plt.subplots(1, 4, figsize=(17, 3.9), sharey=False)
    for i, r in enumerate(REG):
        for k, mk in ((1, "o"), (2, "s"), (3, "^")):
            d = pd.read_csv(RD / f"g8_s2_r{r}_p{k}.csv")
            d = d[d.status == "ok"]
            ax[i].scatter(d.fraction * 100, d.g_window, s=9, marker=mk, color=RC[r], alpha=.6, label=f"{clean(d.pcm.iloc[0])} mean")
            ax[i].scatter(d.fraction * 100, d.g_window_worst_anchor, s=9, marker=mk, color="#7f8c8d", alpha=.35)
        ax[i].axhspan(-band(r), band(r), color="#27ae60", alpha=.15)
        ax[i].axhline(0, color="k", lw=.7)
        ax[i].set(title=f"Regime {r} (grey = worst anchor)", xlabel="PCM fraction (%)", ylabel="paired g_window (kWh/yr)")
        ax[i].legend(fontsize=6.5, loc="lower left")
    fig.suptitle(f"Sobol DOE at {DEMAND_L:g} L/day: paired evening gain against the water-only 100 L tank")
    save(fig, "rb2_gain_vs_fraction")


def rb3():
    b = pd.read_csv(RD / "wp6_band.csv")
    b = b[b.objective == "g_window"].set_index("scope").loc[[f"r{r}" for r in REG] + ["all"]]
    terms = ["sd_year_se", "d_dt", "d_nodes", "d_prop", "d_member", "d_demand", "d_mains"]
    fig, ax = plt.subplots(figsize=(10, 4))
    x, w = np.arange(len(b)), .11
    for j, t in enumerate(terms):
        ax.bar(x + (j - 3) * w, b[t], w, label=t.replace("d_", "").replace("sd_year_se", "year scatter"))
    ax.scatter(x, b.band, marker="D", color="k", zorder=5, label="band")
    ax.set_xticks(x, [s.upper() for s in b.index])
    ax.set(ylabel="g_window (kWh/yr)", title="Repeatability band and its components (recipe frozen before use)")
    ax.legend(fontsize=7, ncol=4)
    save(fig, "rb3_band")


def rb4():
    t = pd.read_csv(RD / "o2_test_2006_2010.csv")
    fig, ax = plt.subplots(1, 4, figsize=(17, 3.9))
    for i, r in enumerate(REG):
        d = t[t.regime == r]
        for (role, pcm), g in d.groupby(["role", "pcm"]):
            y = g.groupby("year").g_window.mean()
            ax[i].plot(y.index, y.values, marker="o", lw=2.4 if role == "chosen" else 1, color=RC[r] if role == "chosen" else "#95a5a6",
                       label=clean(pcm)[:22] + (" (pick)" if role == "chosen" else ""))
            if role == "chosen":
                wa = g.groupby(["year", "anchor"]).g_window.mean().groupby("year").min()
                ax[i].plot(wa.index, wa.values, ls=":", color=RC[r], label="pick, worst anchor")
        ax[i].axhspan(-band(r), band(r), color="#27ae60", alpha=.15, label="band")
        ax[i].axhline(0, color="k", lw=.7)
        ax[i].set(title=f"Regime {r}", xlabel="test year", ylabel="paired g_window (kWh/yr)")
        ax[i].set_xticks(sorted(d.year.unique()))
        ax[i].legend(fontsize=6.5)
    fig.suptitle(f"One-shot 2006-2010 test ({full_dt():g} s, three anchors) against the repeatability band")
    save(fig, "rb4_test_years")


def rb5():
    t = pd.read_csv(RD / "l3_timestep.csv")
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
    for a, col, title in zip(ax, ("chg_E_del45_window_kWh_pct", "chg_useful_kWh_pct"), ("primary metric E_del45_window", "annual useful energy")):
        for (r, case), g in t.groupby(["regime", "case"]):
            g = g.dropna(subset=[col])
            a.plot(g.dt_s, g[col].abs(), marker="o", ms=3, color=RC[r], ls={"plain": "-", "V30": "--", "V40": ":"}[case], lw=1)
        a.axhline(.05, color="k", lw=1)
        a.set_xscale("log"); a.invert_xaxis()
        a.set(xlabel="time step reached by halving (s)", ylabel="|change| (%)", title=title)
    fig.suptitle(f"L3 time-step gate, 100 L at {DEMAND_L:g} L/day (colour = regime; solid plain, dashed 30 %, dotted 40 % PCM)")
    save(fig, "rb5_timestep")


if __name__ == "__main__":
    for f in (rb1, rb2, rb3, rb5):
        f()
    if (RD / "o2_test_2006_2010.csv").exists():
        rb4()
