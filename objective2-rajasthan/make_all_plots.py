"""
make_all_plots.py  -  generate every Objective-2 (Rajasthan) figure in one run.

    python make_all_plots.py            all figures  ->  results/plots/*.png
    python make_all_plots.py --list     list the figures without drawing
    python make_all_plots.py fig13 fig22   only the figures whose file name starts with one of these

What it does
  * fig1 ... fig9   the nine figures of src/plots/make_plots_results.py (imported, so there is one definition of each).
  * fig10 ... fig50  new figures that show the saved results more completely: chosen designs, held-out years, method checks
                     (time step, tank model, search learning, seeds, DOE, screening, surrogates, band), sensitivity and controls,
                     boundary re-test, sizing, OpenFOAM checks and the weather inputs.
Every figure only READS saved files (results/, rj_openfoam/results/, data/weather/point_years/). Nothing is simulated, no number is
typed by hand, the held-out loader is never called, and nothing outside results/plots/ is written. One failing figure does not stop
the others; a summary is printed at the end and the exit code is 1 if any figure failed.
Matplotlib only (no extra packages).
"""

import json
import sys
import time
import traceback
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from config import RESULTS_DIR                      # noqa: E402
from src.plots import make_plots_results as base    # noqa: E402

RD = Path(RESULTS_DIR)
OF = ROOT / "rj_openfoam" / "results"
OUT = RD / "plots"
REG = (0, 1, 2)
RC = {0: "#1f77b4", 1: "#ff7f0e", 2: "#2ca02c"}        # regime colours
ROLE = {"explore": "#7f8c8d", "select": "#2980b9", "test": "#c0392b", "used_test_v1": "#bdc3c7"}
BAND_C = "#27ae60"
plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": .25, "axes.spines.top": False, "axes.spines.right": False})


# ------------------------------------------------------------------ helpers
def csv(name, root=None):
    return pd.read_csv((root or RD) / name)


def clean(s):
    return str(s).replace("�", "").replace("®", "")


def band(r, obj="g_window"):
    return base._band(r, obj)


def chosen(r):
    return base._chosen(r)


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT / f"{name}.png", dpi=150)
    plt.close(fig)
    print("  wrote", OUT / f"{name}.png")


def boxplot(ax, data, labels, **kw):
    """Matplotlib 3.9 renamed `labels` to `tick_labels`; work with both."""
    try:
        return ax.boxplot(data, tick_labels=labels, **kw)
    except TypeError:
        return ax.boxplot(data, labels=labels, **kw)


def pairs():
    return [(r, k) for r in REG for k in (1, 2, 3)]


# ------------------------------------------------------------------ new figures
def fig10_chosen_designs():
    """Table of the three frozen designs with their select-year and held-out gains."""
    h = csv("g10_heldout_results.csv")
    rows = []
    for r in REG:
        c = chosen(r)
        ho = h[(h.regime == r) & (h.role == "chosen")].g_window
        rows.append([f"R{r}", f"{clean(c['pcm'])} (O1 rank {int(c['pcm_rank'])})", f"{c['R_in_m'] * 1000:.1f}", f"{c['fraction'] * 100:.1f}",
                     f"{c['flow']:.4f}", c["arrangement"], int(c["N"]), f"{c['pcm_mass_kg']:.1f}", f"{c['g_window']:.1f}",
                     f"{ho.mean():.1f} ({ho.min():.0f}-{ho.max():.0f})", f"{band(r):.1f}"])
    cols = ["regime", "PCM", "R_in mm", "PCM %", "flow kg/s", "arrangement", "capsules", "PCM kg", "select g_window", "held-out g_window (min-max)", "band"]
    fig, ax = plt.subplots(figsize=(15, 2.8))
    ax.axis("off")
    t = ax.table(cellText=rows, colLabels=cols, loc="center", cellLoc="center", colWidths=[.05, .17, .06, .06, .07, .09, .07, .06, .09, .15, .06])
    t.auto_set_font_size(False); t.set_fontsize(8.5); t.scale(1, 2.0)
    for j in range(len(cols)):
        t[0, j].set_facecolor("#dfe6e9")
    ax.set_title("Frozen designs (50 L tank, 1.5 m2 collector); gains in kWh/yr over the same-flow water-only tank", fontsize=10)
    save(fig, "fig10_chosen_designs")


def fig11_heldout_by_year():
    """Held-out years 2011-2015: g_window of the chosen design (bold) and the best design of the other O1 PCMs, against the band."""
    h = csv("g10_heldout_results.csv")
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.8), sharey=False)
    for r in REG:
        d = h[h.regime == r]
        for (role, pcm), g in d.groupby(["role", "pcm"]):
            g = g.sort_values("year")
            ax[r].plot(g.year, g.g_window, marker="o", ms=4, lw=2.4 if role == "chosen" else 1,
                       color=RC[r] if role == "chosen" else "#95a5a6", label=clean(pcm)[:24] + (" (selected)" if role == "chosen" else ""))
        ax[r].axhline(band(r), color=BAND_C, ls="--", lw=1.2, label="repeatability band")
        ax[r].set(title=f"Regime {r}", xlabel="held-out year", ylabel="g_window (kWh/yr)")
        ax[r].set_xticks(sorted(d.year.unique()))
        ax[r].legend(fontsize=6.5, loc="lower right")
    lo = min((h.g_window - h.regime.map(band)).min(), 1e9)
    fig.suptitle(f"Held-out test (run once): smallest margin over the band in any design-year = {lo:.0f} kWh/yr")
    save(fig, "fig11_heldout_by_year")


def fig12_gain_vs_pcm_mass():
    """Held-out gain against PCM mass for all nine tested designs: is the gain just more material?"""
    h = csv("g10_heldout_results.csv").groupby(["regime", "role", "pcm"]).agg(g=("g_window", "mean"), m=("pcm_mass_kg", "mean")).reset_index()
    fig, ax = plt.subplots(figsize=(6.5, 4.4))
    for r in REG:
        d = h[h.regime == r]
        ax.scatter(d.m, d.g, s=np.where(d.role == "chosen", 120, 40), color=RC[r], edgecolor="k", label=f"Regime {r}")
    x = np.linspace(h.m.min() * .9, h.m.max() * 1.05, 20)
    k = (h.g / h.m).median()
    ax.plot(x, k * x, color="#7f8c8d", ls=":", label=f"median {k:.1f} kWh/yr per kg")
    ax.set(xlabel="PCM mass (kg)", ylabel="held-out g_window (kWh/yr)", title="Gain against PCM mass (large marker = selected design)")
    ax.legend(fontsize=7)
    save(fig, "fig12_gain_vs_pcm_mass")


def fig13_timestep_convergence():
    """G2: change in annual useful energy each time dt is halved, against the 0.05 % acceptance line."""
    d = pd.concat([csv("g2_timestep_convergence_300_150_75.csv"), csv("g2_timestep_convergence_150_75_37p5.csv")])
    d = d.drop_duplicates(["regime", "case", "dt_s"]).dropna(subset=["change_vs_prev_dt_pct"])
    fig, ax = plt.subplots(figsize=(7, 4))
    for (r, c), g in d.groupby(["regime", "case"]):
        g = g.sort_values("dt_s", ascending=False)
        ax.plot(g.dt_s, g.change_vs_prev_dt_pct.abs(), marker="o", ms=4, ls="-" if c == "pcm" else "--", color=RC[r], label=f"R{r} {c}")
    ax.axhline(.05, color="k", lw=1)
    ax.text(ax.get_xlim()[0], .052, "0.05 % limit", fontsize=8)
    ax.set_xscale("log"); ax.invert_xaxis()
    ax.set(xlabel="time step reached by halving (s)", ylabel="|change in useful energy| (%)", title="G2 time-step convergence")
    ax.legend(fontsize=7, ncol=2)
    save(fig, "fig13_timestep_convergence")


def fig14_tank_model_check():
    """G4: single-node and 10-node tank on the same case: useful energy, solar fraction and peak water temperature."""
    d = csv("g4_multinode_report.csv")
    d["label"] = "R" + d.regime.astype(str) + " " + d.case
    labs = list(dict.fromkeys(d.label))
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
    for a, (col, t) in zip(ax, (("useful_energy_kWh", "useful energy (kWh/yr)"), ("solar_fraction", "solar fraction"), ("max_water_C", "peak water temperature (C)"))):
        for i, (m, c) in enumerate((("single", "#95a5a6"), ("multinode", "#2980b9"))):
            g = d[d.model == m].groupby("label")[col].mean().reindex(labs)
            a.bar(np.arange(len(labs)) + (i - .5) * .38, g.values, .38, color=c, label=m)
        a.set_xticks(range(len(labs)), labs, rotation=45, ha="right", fontsize=7)
        a.set_title(t, fontsize=9)
    ax[0].legend(fontsize=8)
    fig.suptitle("G4: the 10-node stratified tank against the single-node tank")
    save(fig, "fig14_tank_model_check")


def fig15_search_learning():
    """G9: how each optimiser front improved as simulated designs were added (base rounds solid, extra rounds dashed)."""
    fig, ax = plt.subplots(1, 3, figsize=(14, 4))
    for r, k in pairs():
        ls = ["-", "--", ":"][k - 1]
        for suffix, alpha in (("", 1.0), ("_ext2", .6)):
            f = RD / f"g9_al_log_r{r}_p{k}{suffix}.csv"
            if not f.exists():
                continue
            d = pd.read_csv(f)
            ref = pd.read_csv(RD / f"g9_al_log_r{r}_p{k}.csv").hv_simulated_front.iloc[0]
            ax[0].plot(d.n_train, d.hv_simulated_front / ref, ls=ls, color=RC[r], alpha=alpha, lw=1.2)
            ax[1].plot(d.n_train, d.mean_abs_err_g_annual, ls=ls, color=RC[r], alpha=alpha, lw=1.2)
    s = csv("g9_al_summary.csv")
    ax[2].bar(s.pair, s.hv_gain_pct, color=[RC[int(p[1])] for p in s.pair])
    ax[0].set(xlabel="simulated training designs", ylabel="front hypervolume / first round", title="Front quality")
    ax[1].set(xlabel="simulated training designs", ylabel="surrogate mean abs error, g_annual (kWh/yr)", title="Surrogate error", yscale="log")
    ax[2].set(ylabel="hypervolume gain over the base rounds (%)", title="Gain by pair"); ax[2].tick_params(axis="x", labelsize=7, rotation=45)
    fig.suptitle("G9 active learning (colour = regime; solid/dashed/dotted = O1 PCM rank 1/2/3)")
    save(fig, "fig15_search_learning")


def fig16_seed_stability():
    """G9: hypervolume of three NSGA-II seeds relative to their union, with the repeatability band."""
    s = csv("g9_seed_stability.csv")
    fig, ax = plt.subplots(figsize=(9, 4))
    x = np.arange(len(s))
    for i, c in enumerate(("hv_seed1", "hv_seed2", "hv_seed3")):
        ax.scatter(x, s[c] / s.hv_union, s=36, label=f"seed {i + 1}")
    ax.plot(x, 1 - s.hv_band / s.hv_union, color=BAND_C, ls="--", label="union minus band")
    ax.set_xticks(x, s.pair)
    ax.set(ylabel="hypervolume / union of seeds", title=f"G9 seed stability: spread inside the band in {int(s.spread_within_band.astype(bool).sum())} of {len(s)} pairs")
    ax.legend(fontsize=7, ncol=4, loc="lower right")
    save(fig, "fig16_seed_stability")


def fig17_doe_distribution():
    """G8 S2: g_window of every valid design in the Sobol DOE, per (regime, PCM rank)."""
    data, labs, share = [], [], []
    for r, k in pairs():
        d = csv(f"g8_s2_r{r}_p{k}.csv")
        d = d[d.valid.astype(bool) & d.g_window.notna()]
        data.append(d.g_window.values); labs.append(f"r{r}_p{k}"); share.append((d.g_window > 0).mean() * 100)
    fig, ax = plt.subplots(figsize=(11, 4.4))
    bp = boxplot(ax, data, labs, patch_artist=True, showfliers=True, flierprops=dict(ms=2))
    for patch, (r, k) in zip(bp["boxes"], pairs()):
        patch.set_facecolor(RC[r]); patch.set_alpha(.55)
    ax.axhline(0, color="k", lw=1)
    for i, s in enumerate(share):
        ax.text(i + 1, ax.get_ylim()[1], f"{s:.0f}%", ha="center", va="top", fontsize=7)
    ax.set(ylabel="g_window of DOE designs (kWh/yr)", title="G8 DOE: spread of the gain over the whole design box (percent = share of designs above zero)")
    save(fig, "fig17_doe_distribution")


def fig18_screening_anova():
    """G8 S1: share of g_window variance explained by each factor in the Taguchi L9 screening."""
    rows = []
    for r, k in pairs():
        a = csv(f"g8_s1_anova_r{r}_p{k}.csv")
        a = a[a.response == "g_window"].set_index("factor").contribution_pct
        rows.append(a.rename(f"r{r}_p{k}"))
    d = pd.DataFrame(rows).fillna(0)
    fig, ax = plt.subplots(figsize=(10, 4.2))
    d.plot.bar(stacked=True, ax=ax, colormap="Set2", rot=0, width=.75)
    ax.set(ylabel="contribution to g_window variance (%)", title="G8 screening (Taguchi L9 + ANOVA): the PCM fraction dominates")
    ax.legend(fontsize=7, ncol=5)
    save(fig, "fig18_screening_anova")


def fig19_surrogate_heatmap():
    """G8 S3: rank correlation of each surrogate family per pair; the winner is boxed."""
    s = csv("g8_s3_selection.csv").set_index("pair")
    fam = [c for c in s.columns if c != "chosen"]
    m = s[fam].values.astype(float)
    fig, ax = plt.subplots(figsize=(6.5, 4.6))
    im = ax.imshow(m, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(fam)), fam, rotation=30, ha="right"); ax.set_yticks(range(len(s)), s.index)
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            ax.text(j, i, f"{m[i, j]:.3f}", ha="center", va="center", color="w", fontsize=7)
        j = fam.index(s.chosen.iloc[i])
        ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, fill=False, ec="#f1c40f", lw=2))
    ax.grid(False)
    fig.colorbar(im, label="Spearman rho")
    ax.set_title("G8 surrogate selection (yellow box = family used by the search)")
    save(fig, "fig19_surrogate_heatmap")


def fig20_band_decomposition():
    """WP6: the four terms of the repeatability band (year scatter, time step, node count, material properties) per regime."""
    b = csv("wp6_band.csv")
    b = b[b.objective == "g_window"].set_index("scope").loc[["r0", "r1", "r2", "all"]]
    terms = [("sd_year_se", "year scatter"), ("d_dt", "time step"), ("d_nodes", "node count"), ("d_prop", "material properties")]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    x = np.arange(len(b)); w = .19
    for i, (c, l) in enumerate(terms):
        ax.bar(x + (i - 1.5) * w, b[c], w, label=l)
    ax.scatter(x, b.band, marker="D", color="k", zorder=5, label="band used")
    ax.set_xticks(x, ["R0", "R1", "R2", "all"])
    ax.set(ylabel="g_window (kWh/yr)", title="WP6 repeatability band and its components")
    ax.legend(fontsize=7, ncol=3)
    save(fig, "fig20_band_decomposition")


def fig21_boundary_retest():
    """Share of each optimiser front sitting on the upper fraction and radius bounds: v3 box against the B1 widened box."""
    def share(df, key):
        d = df[df.bound.str.contains(key, regex=False)]
        return d.groupby("pair").share_of_front.max()
    v3, b1 = csv("g9_boundary_check.csv"), csv("b1_boundary_check.csv")
    prs = [f"r{r}_p{k}" for r, k in pairs()]
    fig, ax = plt.subplots(1, 2, figsize=(13, 4))
    for a, (title, k3, kb, lab3, labb) in zip(ax, (("PCM fraction at the cap", "fraction at 30 % cap", "fraction at 40 % cap", "v3 box (cap 30 %)", "B1 box (cap 40 %)"),
                                                  ("inner radius at the upper end", "R_in at 40 mm end", "R_in at 50 mm end", "v3 box (40 mm)", "B1 box (50 mm)"))):
        x = np.arange(len(prs))
        a.bar(x - .2, share(v3, k3).reindex(prs).fillna(0), .4, color="#8e44ad", label=lab3)
        a.bar(x + .2, share(b1, kb).reindex(prs).fillna(0), .4, color="#e67e22", label=labb)
        a.set_xticks(x, prs, rotation=45, ha="right", fontsize=7)
        a.set(title=title, ylabel="share of final front", ylim=(0, 1.05))
        a.legend(fontsize=7)
    fig.suptitle("Boundary test: widening the box does not remove the boundary (B1, explore/select years only)")
    save(fig, "fig21_boundary_retest")


def fig22_sensitivity_blocks():
    """G7 one-factor sweeps (10-node tank, mean of the explore years): window gain against thickness, PCM fraction, flow and arrangement."""
    g = csv("g7_sensitivity_paired.csv")
    g = g[g.model.eq("multinode") & g.valid.astype(bool)]
    col = "d_E_del45_window_kWh"
    fig, ax = plt.subplots(1, 4, figsize=(16, 3.8))
    for r in REG:
        for a, (blk, x, lab) in zip(ax[:3], (("A_thickness", "R_in_mm", "inner radius (mm)"), ("B_count", "frac_outer", "PCM fraction of tank"), ("C_flow", "flow", "flow (kg/s)"))):
            d = g[(g.block == blk) & (g.regime == r)].groupby(x)[col].mean()
            a.plot(d.index, d.values, marker="o", ms=3, color=RC[r], label=f"R{r}")
            a.set(xlabel=lab, ylabel="window gain (kWh/yr)")
        d = g[(g.block == "D_arrangement") & (g.regime == r)].groupby("arrangement")[col].mean()
        ax[3].bar(np.arange(len(d)) + (r - 1) * .27, d.values, .27, color=RC[r], label=f"R{r}")
        ax[3].set_xticks(range(len(d)), d.index, fontsize=8)
    for a, t in zip(ax, ("A thickness", "B PCM fraction", "C flow", "D arrangement")):
        a.set_title(t, fontsize=10)
    ax[0].legend(fontsize=7)
    fig.suptitle("G7 sensitivity (paired against the same-condition water-only tank)")
    save(fig, "fig22_sensitivity_blocks")


def fig23_controls():
    """G14: change in g_window of each control relative to the interior anchor design, against the band."""
    fig, ax = plt.subplots(1, 3, figsize=(14, 4.6))
    for r in REG:
        c = csv(f"g14_controls_r{r}.csv")
        base_v = c[c.block == "base"].g_window.iloc[0]
        d = c[(c.block != "base") & c.g_window.notna()].copy()
        d["lab"] = d.block.str.replace("_", " ") + " " + d.level.astype(str)
        d["delta"] = d.g_window - base_v
        ax[r].barh(d.lab, d.delta, color=["#c0392b" if abs(v) > band(r) else "#95a5a6" for v in d.delta])
        ax[r].axvspan(-band(r), band(r), color=BAND_C, alpha=.2); ax[r].axvline(0, color="k", lw=.8)
        ax[r].invert_yaxis(); ax[r].tick_params(axis="y", labelsize=7)
        ax[r].set(title=f"Regime {r} (anchor g_window {base_v:.0f})", xlabel="change in g_window (kWh/yr)")
    fig.suptitle("G14 controls from an interior anchor: red = larger than the band")
    save(fig, "fig23_controls")


def fig24_stack_anchor():
    """G15: g_window of the chosen design with the capsule stack at the bottom, centre or top of the tank (select years)."""
    fig, ax = plt.subplots(figsize=(8, 4))
    for r in REG:
        d = csv(f"g15_anchor_r{r}.csv")
        d = d[(d.role == "chosen") & (d.purpose == "select")]
        m = d.groupby("anchor").g_window.agg(["mean", "min", "max"]).reindex(["bottom", "center", "top"])
        ax.errorbar(range(3), m["mean"], yerr=[m["mean"] - m["min"], m["max"] - m["mean"]], marker="o", capsize=3, color=RC[r], label=f"R{r}")
    ax.set_xticks(range(3), ["bottom", "centre", "top"])
    allmin = min(csv(f"g15_anchor_r{r}.csv").query("role == 'chosen' and purpose == 'select'").g_window.min() for r in REG)
    ax.set(xlabel="stack position in the tank", ylabel="g_window (kWh/yr)", title=f"G15 stack position (select years, bars = year range); smallest value {allmin:.0f} kWh/yr")
    ax.legend(fontsize=8)
    save(fig, "fig24_stack_anchor")


def fig25_shield_split():
    """G13: hours the water-side safety shield acts, PCM tank against water-only tank, and hours the PCM shield acts (select years)."""
    rows = []
    for r in REG:
        d = csv(f"g13_shield_split_r{r}.csv")
        d = d[(d.role == "chosen") & (d.purpose == "select")]
        rows.append((f"R{r}", d.shield_water_h_pcm.mean(), d.shield_water_h_plain.mean(), d.shield_pcm_h.mean()))
    t = pd.DataFrame(rows, columns=["regime", "water-side, PCM tank", "water-side, water-only tank", "PCM-side shield"]).set_index("regime")
    fig, ax = plt.subplots(figsize=(7, 4))
    t.plot.bar(ax=ax, rot=0, color=["#2980b9", "#95a5a6", "#c0392b"])
    ax.set(ylabel="hours per year", title="G13 shield activity of the chosen designs (select years)")
    ax.legend(fontsize=7)
    save(fig, "fig25_shield_split")


def fig26_night_serve():
    """G16: night-serve duration and the share of the draw served at 45 C or above, PCM tank against water-only tanks (select years)."""
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    for r in REG:
        pc = csv(f"g16_serve_r{r}.csv")
        p40 = csv(f"g16_serve_plain_40L_r{r}.csv")
        for a, col, t in zip(ax, ("tau_serve_mean_h", "serve_frac_45_mean"), ("night-serve duration (h)", "served at 45 C or above (share of draw)")):
            vals = [pc[pc.case == "pcm"][col].mean(), pc[pc.case == "plain"][col].mean(), p40[col].mean()]
            a.bar(np.arange(3) + (r - 1) * .27, vals, .27, color=RC[r], label=f"R{r}")
            a.set_xticks(range(3), ["PCM tank (50 L)", "water-only 50 L", "water-only 40 L"], fontsize=8)
            a.set_title(t, fontsize=10)
    ax[0].legend(fontsize=7)
    fig.suptitle("G16: PCM raises delivered energy at 45 C but not the night-serve duration (select years)")
    save(fig, "fig26_night_serve")


def fig27_widened_box():
    """G17: gain against inner radius, PCM fraction and flow, with the v3 bounds marked."""
    fig, ax = plt.subplots(1, 3, figsize=(14, 3.9))
    for r in REG:
        g = csv(f"g17_widen_r{r}.csv")
        g = g[g.valid.astype(bool)]
        for a, (blk, x, lab, cap) in zip(ax, (("A_radius", "R_in_mm", "inner radius (mm)", 40), ("B_fraction", "fraction_req", "PCM fraction", .30), ("D_flow", "flow", "flow (kg/s)", .05))):
            d = g[g.block == blk].sort_values(x)
            a.plot(d[x], d.g_window, marker="o", ms=4, color=RC[r], label=f"R{r}")
            a.axvline(cap, color="k", ls=":", lw=1)
            a.set(xlabel=lab, ylabel="g_window (kWh/yr)")
    for a, t in zip(ax, ("radius", "PCM fraction", "flow")):
        a.set_title(f"{t} (dotted line = v3 bound)", fontsize=9)
    ax[0].legend(fontsize=7)
    fig.suptitle("G17 widened-bound diagnostic (explore years)")
    save(fig, "fig27_widened_box")


def fig28_sizing():
    """G21: gain of the frozen designs when only the tank volume changes (collector fixed at 1.5 m2, explore years)."""
    fig, ax = plt.subplots(figsize=(7.5, 4.3))
    for r in REG:
        d = csv(f"g21_sizing_r{r}.csv")
        d = d[d.valid.astype(bool)]
        for v, ls in (("same_fraction", "-"), ("same_count", "--")):
            g = d[d.variant == v].sort_values("tank_L")
            ax.plot(g.tank_L, g.g_window, ls=ls, marker="o", ms=4, color=RC[r], label=f"R{r} {v.replace('_', ' ')}")
    ax.axhline(0, color="k", lw=.8)
    ax.set(xlabel="tank volume (L) at fixed 1.5 m2 collector", ylabel="g_window (kWh/yr)", title="G21 sizing study (diagnostic of direction, not a design)")
    ax.legend(fontsize=6.5, ncol=2)
    save(fig, "fig28_sizing")


def fig29_sensitivity_tornado():
    """G22: change in g_window for each model-input perturbation, against the band."""
    fig, ax = plt.subplots(1, 3, figsize=(14, 5))
    for r in REG:
        d = csv(f"g22_sensitivity_r{r}.csv")
        d = d[d.variant != "base"].copy()
        d = d.reindex(d.delta_g_window.abs().sort_values(ascending=False).index)
        ax[r].barh(d.variant, d.delta_g_window, color=["#c0392b" if b else "#95a5a6" for b in d.beyond_band.astype(bool)])
        ax[r].axvspan(-band(r), band(r), color=BAND_C, alpha=.2); ax[r].axvline(0, color="k", lw=.8)
        ax[r].invert_yaxis(); ax[r].tick_params(axis="y", labelsize=7)
        ax[r].set(title=f"Regime {r}", xlabel="change in g_window (kWh/yr)")
    fig.suptitle("G22 input sensitivity of the chosen design: red = beyond the band")
    save(fig, "fig29_sensitivity_tornado")


def fig30_flow_fr():
    """G24: gain against flow with and without a flow-dependent collector factor F_R."""
    fig, ax = plt.subplots(figsize=(7, 4))
    for r in REG:
        d = csv(f"g24_flow_fr_r{r}.csv")
        for flag, ls in ((False, "-"), (True, "--")):
            g = d[d.flow_dependent_fr.astype(bool) == flag].sort_values("flow")
            ax.plot(g.flow, g.g_window, ls=ls, marker="o", ms=3, color=RC[r], label=f"R{r} " + ("flow-dependent F_R" if flag else "constant F_R"))
    mx = max((csv(f"g24_flow_fr_r{r}.csv").pivot(index="flow", columns="flow_dependent_fr", values="g_window").diff(axis=1).abs().max().max()) for r in REG)
    ax.set(xlabel="flow (kg/s)", ylabel="g_window (kWh/yr)", title=f"G24: a flow-dependent F_R changes g_window by at most {mx:.1f} kWh/yr")
    ax.legend(fontsize=6.5, ncol=2)
    save(fig, "fig30_flow_fr")


def fig31_gpbo_vs_nsga():
    """G20: best feasible g_window found so far by an independent GP Bayesian search, against the NSGA-II chosen design (explore years)."""
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.8), sharey=False)
    for r in REG:
        g = csv(f"g20_gpbo_r{r}_p1.csv")
        best = g.g_window.where(g.feasible.astype(bool)).cummax()
        ax[r].plot(np.arange(1, len(g) + 1), best, color=RC[r], label="GP-BO best so far")
        c = chosen(r)
        ref = c.get("explore_g_window", c["g_window"])
        ax[r].axhline(ref, color="k", ls="--", label="NSGA-II chosen (explore)")
        ax[r].axhspan(ref - band(r), ref + band(r), color=BAND_C, alpha=.2, label="band")
        ax[r].set(title=f"Regime {r}", xlabel="simulated designs", ylabel="g_window (kWh/yr)")
        ax[r].legend(fontsize=7, loc="lower right")
    fig.suptitle("G20: independent GP Bayesian search (60 simulations, rank-1 PCM) against the NSGA-II chosen design, explore years")
    save(fig, "fig31_gpbo_vs_nsga")


def fig32_box_vertex():
    """G18: front hypervolume of the three search variants (base, extra rounds, box vertices + extra rounds), relative to the best."""
    d = csv("g18_issue1_with_without.csv")
    t = d.pivot(index="pair", columns="state", values="hv_rel_to_best_state")[["base", "novert", "vert"]]
    fig, ax = plt.subplots(figsize=(9, 4))
    t.plot.bar(ax=ax, rot=0, color=["#95a5a6", "#2980b9", "#e67e22"])
    ax.set(ylim=(t.min().min() - .02, 1.005), ylabel="hypervolume / best of the three", title=f"G18 search variants: lowest relative hypervolume {t.min().min():.3f}")
    ax.legend(fontsize=8, ncol=3)
    save(fig, "fig32_box_vertex")


def fig33_b1_retest():
    """B1: select-year gain and the design chosen in the v3 box against the widened box (radius to 50 mm, fraction to 40 %)."""
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for r in REG:
        a = chosen(r)
        b = json.load(open(RD / f"b1_selection_r{r}.json", encoding="utf-8"))["chosen"]
        ax.bar(r * 3, a["g_window"], 1, color="#95a5a6", label="v3 box" if r == 0 else None)
        ax.bar(r * 3 + 1, b["g_window"], 1, color="#e67e22", label="B1 widened box" if r == 0 else None)
        ax.text(r * 3, a["g_window"] + 3, f"R {a['R_in_m'] * 1000:.0f} mm\n{a['fraction'] * 100:.0f} %", ha="center", fontsize=7)
        ax.text(r * 3 + 1, b["g_window"] + 3, f"R {b['R_in_m'] * 1000:.0f} mm\n{b['fraction'] * 100:.0f} %", ha="center", fontsize=7)
    ax.set_xticks([.5, 3.5, 6.5], ["Regime 0", "Regime 1", "Regime 2"])
    ax.set(ylabel="g_window, select years (kWh/yr)", ylim=(0, 225), title="B1 re-test: a wider box raises the gain but the fronts still end on the new bounds")
    ax.legend(fontsize=8)
    save(fig, "fig33_b1_retest")


def fig34_night_hold():
    """G3: hours the tank stays at or above 30 C (hold) and hours it serves at 45 C after each evening, PCM tank against water-only tank."""
    fig, ax = plt.subplots(2, 3, figsize=(13, 6))
    for r in REG:
        for i, (col, t) in enumerate((("tau_hold_h", "hold time above 30 C (h)"), ("tau_serve_h", "night-serve duration (h)"))):
            p = csv(f"g3_night_daily_r{r}_pcm.csv")[col].dropna()
            w = csv(f"g3_night_daily_r{r}_plain.csv")[col].dropna()
            boxplot(ax[i, r], [w, p], ["water-only", "PCM"], patch_artist=True, boxprops=dict(facecolor=RC[r], alpha=.5), flierprops=dict(ms=2))
            ax[i, r].set_title(f"Regime {r}: {t}", fontsize=9)
    fig.suptitle("G3 night metrics over every evening of a year (reference PCM, before the optimisation)")
    save(fig, "fig34_night_hold")


def fig35_chen_benchmark():
    """G23: simulated hold-time gain against PCM fraction, with the published Chen 2025 simulated and measured gain."""
    fig, ax = plt.subplots(figsize=(7, 4))
    for r in REG:
        f = RD / f"g23_chen_benchmark_r{r}.csv"
        if not f.exists():                           # only the regime-0 benchmark was run for Rajasthan
            continue
        d = pd.read_csv(f).sort_values("pcm_fraction")
        ax.plot(d.pcm_fraction * 100, d.gain_pct, marker="o", color=RC[r], label=f"R{r}")
    d = csv("g23_chen_benchmark_r0.csv")
    ax.axhline(d.chen_gain_sim_pct.iloc[0], color="k", ls="--", lw=1, label="Chen 2025 simulated")
    ax.axhline(d.chen_gain_exp_pct.iloc[0], color="k", ls=":", lw=1, label="Chen 2025 measured")
    ax.set(xlabel="PCM fraction (%)", ylabel="gain in hold time above 30 C (%)", title="G23 trend check against the published benchmark")
    ax.legend(fontsize=7)
    save(fig, "fig35_chen_benchmark")


def _melt(case):
    f = OF / "runs" / case / "meltAndTemp.dat"
    d = pd.read_csv(f, comment="#", sep=r"\s+", header=None, names=["t", "T", "f"])
    return d


def fig40_of_melt_curves():
    """OpenFOAM single-capsule runs (40 cells): liquid fraction against time for the three chosen designs and the discharge case."""
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    for case, lab, col in (("r0_charge_70_n40", "r0 savE OM55", RC[0]), ("r1_charge_70_n40", "r1 PureTemp 60", RC[1]), ("r2_charge_70_n40", "r2 PureTemp 58", RC[2])):
        d = _melt(case)
        ax[0].plot(d.t / 60, d.f, color=col, label=lab)
    ax[0].set(xlabel="time (min)", ylabel="liquid fraction", title="Charging: 70 C wall, solid start at 30 C", xlim=(0, 120))
    ax[0].legend(fontsize=8)
    d = _melt("r0_discharge_mains_n40")
    ax[1].plot(d.t / 60, d.f, color=RC[0], label="r0 discharge (mains-temperature wall)")
    ax[1].set(xlabel="time (min)", ylabel="liquid fraction", title="Discharging: liquid start at 64 C")
    ax[1].legend(fontsize=8)
    fig.suptitle("OpenFOAM (v2406) capsule runs: model-to-model only, not validated against measurements")
    save(fig, "fig40_of_melt_curves")


def fig41_of_lumped_vs_cfd():
    """Minutes to 50 % melt: CFD against the frozen lumped closure (c 5, F 2) and the unvalidated v1 closure (c 10, F 5)."""
    d = csv("of_spotcheck.csv", OF)
    lab = {"openfoam_40cells": "OpenFOAM (40 cells)", "lumped_frozen_c5_F2": "lumped, frozen c 5 / F 2", "lumped_cfd_closure_v1_c10_F5": "lumped, v1 c 10 / F 5 (unvalidated)"}
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for i, (s, c) in enumerate((("openfoam_40cells", "#2c3e50"), ("lumped_frozen_c5_F2", "#2980b9"), ("lumped_cfd_closure_v1_c10_F5", "#e67e22"))):
        g = d[d.series == s].set_index("design").loc[["r0", "r1", "r2"]]
        ax.bar(np.arange(3) + (i - 1) * .27, g.t50_min, .27, color=c, label=lab[s])
        for j, v in enumerate(g.t50_min):
            ax.text(j + (i - 1) * .27, v + 1.5, f"{v:.0f}", ha="center", fontsize=7)
    ax.set_xticks(range(3), ["r0 savE OM55", "r1 PureTemp 60", "r2 PureTemp 58"])
    cf = d[d.series == "openfoam_40cells"].set_index("design").t50_min
    fr = d[d.series == "lumped_frozen_c5_F2"].set_index("design").t50_min
    ratio = (fr / cf).loc[["r0", "r1", "r2"]]
    ax.set(ylabel="minutes to 50 % liquid", title=f"Frozen lumped model is {ratio.min():.1f}-{ratio.max():.1f} times slower than the CFD at 50 % melt (CFD itself unvalidated)")
    ax.legend(fontsize=7)
    save(fig, "fig41_of_lumped_vs_cfd")


def fig42_of_mesh_and_freeze():
    """OpenFOAM mesh study (t50, t90 against cells across the radius) and the freezing check (minutes to 90/50/10 % liquid)."""
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    m = csv("of_mesh_study.csv", OF).sort_values("cells_radial")
    ax[0].plot(m.cells_radial, m.t50_s / 60, marker="o", label="t50")
    ax[0].plot(m.cells_radial, m.t90_s / 60, marker="s", label="t90")
    ax[0].set_xscale("log", base=2); ax[0].set_xticks(m.cells_radial, m.cells_radial)
    ax[0].set(xlabel="cells across the radius", ylabel="minutes", title="Mesh study: times grow with refinement (not in the asymptotic range)")
    ax[0].legend(fontsize=8)
    f = csv("of_freeze_check.csv", OF)
    f["lab"] = f.series.str.replace("_", " ") + np.where(f.case.notna(), " (" + f.case.fillna("").str.extract(r"_n(\d+)$")[0].fillna("") + " cells)", "")
    cols = ["t_f90_min", "t_f50_min", "t_f10_min"]
    for i, (c, l) in enumerate(zip(cols, ("to 90 % liquid", "to 50 %", "to 10 %"))):
        ax[1].bar(np.arange(len(f)) + (i - 1) * .27, f[c], .27, label=l)
    ax[1].set_xticks(range(len(f)), f.lab, rotation=25, ha="right", fontsize=7)
    ax[1].set(ylabel="minutes", title="Freezing (discharge) check, r0", yscale="log")
    ax[1].legend(fontsize=8)
    save(fig, "fig42_of_mesh_and_freeze")


def fig50_weather_inputs():
    """Annual irradiation and mean temperature of the regime medoid point for every weather year, coloured by role."""
    import re
    from src.weather import roles
    files = sorted((ROOT / "data" / "weather" / "point_years" / "rajasthan").glob("cluster*_*.csv"))
    rows = []
    for f in files:
        m = re.match(r"cluster(\d)_(RJP_\d+)_(\d{4})\.csv", f.name)
        if not m:
            continue
        d = pd.read_csv(f)
        rows.append(dict(regime=int(m.group(1)), year=int(m.group(3)), ghi=d.GHI_Wm2.clip(lower=0).sum() / 1000, tamb=d.T_amb_C.mean()))
    w = pd.DataFrame(rows)
    w["role"] = w.year.map(roles.YEAR_ROLES)
    fig, ax = plt.subplots(2, 3, figsize=(14, 6), sharex=True)
    for r in REG:
        d = w[w.regime == r].sort_values("year")
        for i, (c, t) in enumerate((("ghi", "annual GHI (kWh/m2)"), ("tamb", "mean ambient temperature (C)"))):
            ax[i, r].vlines(d.year, d[c].min() - 0, d[c], color="#ddd", lw=.8)
            ax[i, r].scatter(d.year, d[c], s=60, color=[ROLE.get(x, "#999") for x in d.role], zorder=3)
            ax[i, r].set_title(f"Regime {r}: {t}", fontsize=9)
    h = [plt.Rectangle((0, 0), 1, 1, color=ROLE[k]) for k in ("explore", "select", "test", "used_test_v1")]
    fig.legend(h, ["explore 2016-20", "select 2021-23", "held-out 2011-15 (used once)", "v1 test 2024-25 (spent)"], loc="lower center", ncol=4, fontsize=8)
    fig.suptitle("Weather inputs of the three regime medoid points, by year role")
    fig.tight_layout(rect=(0, .05, 1, 1))
    fig.savefig(OUT / "fig50_weather_inputs.png", dpi=150); plt.close(fig)
    print("  wrote", OUT / "fig50_weather_inputs.png")


# ------------------------------------------------------------------ registry
EXISTING = [("fig1_front_vs_grid", base.fig_front_vs_grid), ("fig2_g9_grid_check", base.fig_g9_checks), ("fig3_gain_by_year_role", base.fig_gain_by_stage),
            ("fig4_heldout_pcm_comparison", base.fig_pcm_comparison), ("fig5_heldout_nulls_and_costs", base.fig_null_results),
            ("fig6_ablations", base.fig_ablation), ("fig7_surrogate_comparison", base.fig_surrogates),
            ("fig8_fraction_response", base.fig_fraction_response), ("fig9_boundary_share", base.fig_boundary)]
NEW = [(f.__name__, f) for f in (fig10_chosen_designs, fig11_heldout_by_year, fig12_gain_vs_pcm_mass, fig13_timestep_convergence, fig14_tank_model_check,
                                  fig15_search_learning, fig16_seed_stability, fig17_doe_distribution, fig18_screening_anova, fig19_surrogate_heatmap,
                                  fig20_band_decomposition, fig21_boundary_retest, fig22_sensitivity_blocks, fig23_controls, fig24_stack_anchor,
                                  fig25_shield_split, fig26_night_serve, fig27_widened_box, fig28_sizing, fig29_sensitivity_tornado, fig30_flow_fr,
                                  fig31_gpbo_vs_nsga, fig32_box_vertex, fig33_b1_retest, fig34_night_hold, fig35_chen_benchmark,
                                  fig40_of_melt_curves, fig41_of_lumped_vs_cfd, fig42_of_mesh_and_freeze, fig50_weather_inputs)]


def main(argv):
    figs = EXISTING + NEW
    if "--list" in argv:
        for n, f in figs:
            print(f"{n:34s} {(f.__doc__ or '').strip().splitlines()[0] if f.__doc__ else ''}")
        return 0
    sel = [a for a in argv if not a.startswith("-")]
    if sel:
        figs = [(n, f) for n, f in figs if any(n.startswith(s) for s in sel)]
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Generating {len(figs)} figures -> {OUT}")
    ok, bad, t0 = [], [], time.time()
    for n, f in figs:
        try:
            f()
            ok.append(n)
        except Exception as e:                       # one broken figure must not stop the rest
            plt.close("all")
            bad.append((n, repr(e)[:160]))
            print(f"  FAILED {n}: {e!r}")
            traceback.print_exc(limit=2)
    print(f"\n{len(ok)} written, {len(bad)} failed in {time.time() - t0:.0f} s -> {OUT}")
    for n, e in bad:
        print("  FAILED", n, e)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
