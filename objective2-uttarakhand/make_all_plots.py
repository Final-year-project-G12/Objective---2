"""
make_all_plots.py  -  generate every Objective-2 (Uttarakhand) figure in one run.

    python make_all_plots.py            all figures  ->  results/plots/*.png
    python make_all_plots.py --list     list the figures without drawing
    python make_all_plots.py fig13 fig22   only the figures whose file name starts with one of these

Port of objective2-rajasthan/make_all_plots.py (Rajasthan commit 7f2f701) to the Uttarakhand folder and data:
  * four regimes (src.weather.inventory.REGIMES), delivery target 50 C (columns named "45" are computed at 50 C),
    held-out years 2024-2025, weather points UKP_*.
  * fig1 ... fig9   the nine figures of src/plots/make_plots_results.py (imported, so there is one definition of each).
  * fig10 ... fig50 the further figures, drawn from the Uttarakhand result files.
  * Figures whose study was never run for Uttarakhand are SKIPPED, not drawn (no result file exists, nothing is invented):
    fig28 sizing (g21), fig29 input sensitivity (g22), fig30 flow F_R (g24), fig31 GP-BO (g20), fig32 search variants (g18),
    fig33 B1 widened box, fig35 Chen benchmark (g23), fig41/fig42 OpenFOAM closure and mesh studies.
    fig40 is the Uttarakhand OpenFOAM figure: the one capsule case that was run (openfoam_cfd/results/).
Every figure only READS saved files (results/, openfoam_cfd/results/, data/weather/point_years/). Nothing is simulated, no number is
typed by hand, the held-out loader is never called, and nothing outside results/plots/ is written. One failing figure does not stop
the others; a summary is printed at the end and the exit code is 1 if any figure failed (skipped figures are not failures).
Matplotlib only (no extra packages).
"""

import json  # noqa: F401  (kept for parity with the Rajasthan script)
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
from src.weather.inventory import REGIMES           # noqa: E402

RD = Path(RESULTS_DIR)
OF = ROOT / "openfoam_cfd" / "results"
OUT = RD / "plots"
REG = tuple(int(r) for r in REGIMES)
NR = len(REG)
RC = {0: "#1f77b4", 1: "#ff7f0e", 2: "#2ca02c", 3: "#9467bd"}        # regime colours
ROLE = {"explore": "#7f8c8d", "select": "#2980b9", "test": "#c0392b"}
BAND_C = "#27ae60"
T_DEL = 50                                            # delivery target, configs/system_config_shared.yaml (delivery.target_temp_C)
plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": .25, "axes.spines.top": False, "axes.spines.right": False})


class Skip(Exception):
    """The study behind this figure was not run for Uttarakhand."""


# ------------------------------------------------------------------ helpers
def csv(name, root=None):
    return pd.read_csv((root or RD) / name)


def need(*names, root=None):
    miss = [n for n in names if not ((root or RD) / n).exists()]
    if miss:
        raise Skip("not run for Uttarakhand (missing " + ", ".join(miss) + ")")


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


def offs(i, n=NR, total=.8):
    """Bar offset of group member i out of n."""
    w = total / n
    return (i - (n - 1) / 2) * w, w


def row_axes(h=4.0, wper=4.0, **kw):
    fig, ax = plt.subplots(1, NR, figsize=(wper * NR, h), **kw)
    return fig, np.atleast_1d(ax)


# ------------------------------------------------------------------ figures
def fig10_chosen_designs():
    """Table of the four frozen designs with their select-year and held-out gains."""
    h = csv("g10_heldout_results.csv")
    rows = []
    for r in REG:
        c = chosen(r)
        ho = h[(h.regime == r) & (h.role == "chosen")].g_window
        rows.append([f"R{r}", f"{clean(c['pcm'])} (O1 rank {int(c['pcm_rank'])})", f"{c['R_in_m'] * 1000:.1f}", f"{c['fraction'] * 100:.1f}",
                     f"{c['flow']:.4f}", c["arrangement"], int(c["N"]), f"{c['pcm_mass_kg']:.1f}", f"{c['g_window']:.1f}",
                     f"{ho.mean():.1f} ({ho.min():.0f} to {ho.max():.0f})", f"{band(r):.1f}"])
    cols = ["regime", "PCM", "R_in mm", "PCM %", "flow kg/s", "arrangement", "capsules", "PCM kg", "select g_window", "held-out g_window (min to max)", "band"]
    fig, ax = plt.subplots(figsize=(15, 3.1))
    ax.axis("off")
    t = ax.table(cellText=rows, colLabels=cols, loc="center", cellLoc="center", colWidths=[.05, .17, .06, .06, .07, .09, .07, .06, .09, .15, .06])
    t.auto_set_font_size(False); t.set_fontsize(8.5); t.scale(1, 2.0)
    for j in range(len(cols)):
        t[0, j].set_facecolor("#dfe6e9")
    ax.set_title(f"Frozen designs (50 L tank, 1.5 m2 collector, {T_DEL} C target); gains in kWh/yr over the same-flow water-only tank. "
                 "Regime 3: no PCM gain (degenerate)", fontsize=10)
    save(fig, "fig10_chosen_designs")


def fig11_heldout_by_year():
    """Held-out years 2024-2025: g_window of the chosen design (bold) and the best design of the other O1 PCMs, against the band."""
    h = csv("g10_heldout_results.csv")
    fig, ax = row_axes(3.8, 3.4)
    for i, r in enumerate(REG):
        d = h[h.regime == r]
        for (role, pcm), g in d.groupby(["role", "pcm"]):
            g = g.sort_values("year")
            ax[i].plot(g.year, g.g_window, marker="o", ms=4, lw=2.4 if role == "chosen" else 1,
                       color=RC[r] if role == "chosen" else "#95a5a6", label=clean(pcm)[:24] + (" (selected)" if role == "chosen" else ""))
        ax[i].axhline(band(r), color=BAND_C, ls="--", lw=1.2, label="repeatability band")
        ax[i].axhline(0, color="k", lw=.7)
        ax[i].set(title=f"Regime {r}", xlabel="held-out year", ylabel="g_window (kWh/yr)")
        ax[i].set_xticks(sorted(d.year.unique()))
        ax[i].legend(fontsize=6.5, loc="best")
    m = h[(h.regime != 3) & (h.role == "chosen")]
    lo = (m.g_window - m.regime.map(band)).min()
    fig.suptitle(f"Held-out test (run once): smallest margin of a selected design over the band, regimes 0-2 = {lo:.0f} kWh/yr "
                 "(regime 3: no PCM gain)")
    save(fig, "fig11_heldout_by_year")


def fig12_gain_vs_pcm_mass():
    """Held-out gain against PCM mass for all tested designs: is the gain just more material?"""
    h = csv("g10_heldout_results.csv").groupby(["regime", "role", "pcm"]).agg(g=("g_window", "mean"), m=("pcm_mass_kg", "mean")).reset_index()
    fig, ax = plt.subplots(figsize=(6.5, 4.4))
    for r in REG:
        d = h[h.regime == r]
        ax.scatter(d.m, d.g, s=np.where(d.role == "chosen", 120, 40), color=RC[r], edgecolor="k", label=f"Regime {r}")
    pos = h[h.g > 0]
    x = np.linspace(0, h.m.max() * 1.05, 20)
    k = (pos.g / pos.m).median()
    ax.plot(x, k * x, color="#7f8c8d", ls=":", label=f"median {k:.1f} kWh/yr per kg (positive gains)")
    ax.axhline(0, color="k", lw=.7)
    ax.set(xlabel="PCM mass (kg)", ylabel="held-out g_window (kWh/yr)", title="Gain against PCM mass (large marker = selected design)")
    ax.legend(fontsize=7)
    save(fig, "fig12_gain_vs_pcm_mass")


def fig13_timestep_convergence():
    """G2: change in annual useful energy each time dt is halved, against the 0.05 % acceptance line."""
    files = [f for f in ("g2_timestep_convergence_300_150_75.csv", "g2_timestep_convergence_150_75_37p5.csv") if (RD / f).exists()]
    need(*files[:1] or ["g2_timestep_convergence_150_75_37p5.csv"])
    d = pd.concat([csv(f) for f in files])
    d = d.drop_duplicates(["regime", "case", "dt_s"]).dropna(subset=["change_vs_prev_dt_pct"])
    fig, ax = plt.subplots(figsize=(7, 4))
    for (r, c), g in d.groupby(["regime", "case"]):
        g = g.sort_values("dt_s", ascending=False)
        ax.plot(g.dt_s, g.change_vs_prev_dt_pct.abs(), marker="o", ms=4, ls="-" if c == "pcm" else "--", color=RC[int(r)], label=f"R{r} {c}")
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
    fig, ax = plt.subplots(1, 3, figsize=(14, 3.9))
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
    """G9: how each optimiser front improved as simulated designs were added (base rounds solid, extra rounds faded)."""
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
    ax[2].set(ylabel="hypervolume gain over the first round (%)", title="Gain by pair"); ax[2].tick_params(axis="x", labelsize=7, rotation=45)
    fig.suptitle("G9 active learning (colour = regime; solid/dashed/dotted = O1 PCM rank 1/2/3)")
    save(fig, "fig15_search_learning")


def fig16_seed_stability():
    """G9: hypervolume of three NSGA-II seeds relative to their union, with the repeatability band."""
    s = csv("g9_seed_stability.csv")
    fig, ax = plt.subplots(figsize=(10, 4))
    x = np.arange(len(s))
    for i, c in enumerate(("hv_seed1", "hv_seed2", "hv_seed3")):
        ax.scatter(x, s[c] / s.hv_union, s=36, label=f"seed {i + 1}")
    ax.plot(x, 1 - s.hv_band / s.hv_union, color=BAND_C, ls="--", label="union minus band")
    ax.set_xticks(x, s.pair, rotation=45, ha="right", fontsize=8)
    ax.set(ylabel="hypervolume / union of seeds", title=f"G9 seed stability: spread inside the band in {int(s.spread_within_band.astype(bool).sum())} of {len(s)} pairs")
    ax.legend(fontsize=7, ncol=4, loc="lower right")
    save(fig, "fig16_seed_stability")


def fig17_doe_distribution():
    """G8 S2: g_window of every valid design in the Sobol DOE, per (regime, PCM rank)."""
    data, labs, share, cols = [], [], [], []
    for r, k in pairs():
        f = RD / f"g8_s2_r{r}_p{k}.csv"
        if not f.exists():
            continue
        d = pd.read_csv(f)
        d = d[d.valid.astype(bool) & d.g_window.notna()]
        data.append(d.g_window.values); labs.append(f"r{r}_p{k}"); share.append((d.g_window > 0).mean() * 100); cols.append(RC[r])
    fig, ax = plt.subplots(figsize=(13, 4.4))
    bp = boxplot(ax, data, labs, patch_artist=True, showfliers=True, flierprops=dict(ms=2))
    for patch, c in zip(bp["boxes"], cols):
        patch.set_facecolor(c); patch.set_alpha(.55)
    ax.axhline(0, color="k", lw=1)
    for i, s in enumerate(share):
        ax.text(i + 1, ax.get_ylim()[1], f"{s:.0f}%", ha="center", va="top", fontsize=7)
    ax.tick_params(axis="x", labelsize=8)
    ax.set(ylabel="g_window of DOE designs (kWh/yr)", title="G8 DOE: spread of the gain over the whole design box (percent = share of designs above zero)")
    save(fig, "fig17_doe_distribution")


def fig18_screening_anova():
    """G8 S1: share of g_window variance explained by each factor in the Taguchi L9 screening."""
    rows = []
    for r, k in pairs():
        f = RD / f"g8_s1_anova_r{r}_p{k}.csv"
        if not f.exists():
            continue
        a = pd.read_csv(f)
        a = a[a.response == "g_window"].set_index("factor").contribution_pct
        rows.append(a.rename(f"r{r}_p{k}"))
    d = pd.DataFrame(rows).fillna(0)
    top = d.mean().idxmax()
    fig, ax = plt.subplots(figsize=(12, 4.2))
    d.plot.bar(stacked=True, ax=ax, colormap="Set2", rot=45, width=.75)
    ax.set(ylabel="contribution to g_window variance (%)", title=f"G8 screening (Taguchi L9 + ANOVA): largest mean contribution from {top}")
    ax.legend(fontsize=7, ncol=5)
    save(fig, "fig18_screening_anova")


def fig19_surrogate_heatmap():
    """G8 S3: rank correlation of each surrogate family per pair; the winner is boxed."""
    s = csv("g8_s3_selection.csv").set_index("pair")
    fam = [c for c in s.columns if c != "chosen"]
    m = s[fam].values.astype(float)
    fig, ax = plt.subplots(figsize=(6.5, 5.4))
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
    scopes = [f"r{r}" for r in REG] + ["all"]
    b = b[b.objective == "g_window"].set_index("scope").reindex(scopes).dropna(subset=["band"])
    terms = [("sd_year_se", "year scatter"), ("d_dt", "time step"), ("d_nodes", "node count"), ("d_prop", "material properties")]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    x = np.arange(len(b)); w = .19
    for i, (c, l) in enumerate(terms):
        ax.bar(x + (i - 1.5) * w, b[c], w, label=l)
    ax.scatter(x, b.band, marker="D", color="k", zorder=5, label="band used")
    ax.set_xticks(x, [s.upper() if s != "all" else "all" for s in b.index])
    ax.set(ylabel="g_window (kWh/yr)", title="WP6 repeatability band and its components")
    ax.legend(fontsize=7, ncol=3)
    save(fig, "fig20_band_decomposition")


def fig21_boundary_retest():
    """Share of each optimiser front sitting on the upper PCM-fraction and radius bounds (v3 box; no widened-box test for Uttarakhand)."""
    v3 = csv("g9_boundary_check.csv")
    prs = [f"r{r}_p{k}" for r, k in pairs()]
    fig, ax = plt.subplots(1, 2, figsize=(14, 4))
    for a, (title, key) in zip(ax, (("PCM fraction at the 30 % cap", "fraction at 30 % cap"), ("inner radius at the 40 mm end", "R_in at 40 mm end"))):
        s = v3[v3.bound.str.contains(key, regex=False)].groupby("pair").share_of_front.max().reindex(prs).fillna(0)
        a.bar(np.arange(len(prs)), s, .6, color=[RC[int(p[1])] for p in prs])
        a.set_xticks(range(len(prs)), prs, rotation=45, ha="right", fontsize=7)
        a.set(title=title, ylabel="share of final front", ylim=(0, 1.05))
    fig.suptitle("Boundary check of the final fronts (v3 box; a widened-box B1 re-test was not run for Uttarakhand)")
    save(fig, "fig21_boundary_retest")


def fig22_sensitivity_blocks():
    """G7 one-factor sweeps (10-node tank, mean of the explore years): window gain against thickness, PCM fraction, flow and arrangement."""
    g = csv("g7_sensitivity_paired.csv")
    g = g[g.model.eq("multinode") & g.valid.astype(bool)]
    col = "d_E_del45_window_kWh"
    fig, ax = plt.subplots(1, 4, figsize=(16, 3.9))
    for i, r in enumerate(REG):
        for a, (blk, x, lab) in zip(ax[:3], (("A_thickness", "R_in_mm", "inner radius (mm)"), ("B_count", "frac_outer", "PCM fraction of tank"), ("C_flow", "flow", "flow (kg/s)"))):
            d = g[(g.block == blk) & (g.regime == r)].groupby(x)[col].mean()
            a.plot(d.index, d.values, marker="o", ms=3, color=RC[r], label=f"R{r}")
            a.set(xlabel=lab, ylabel="window gain (kWh/yr)")
        d = g[(g.block == "D_arrangement") & (g.regime == r)].groupby("arrangement")[col].mean()
        o, w = offs(i)
        ax[3].bar(np.arange(len(d)) + o, d.values, w, color=RC[r], label=f"R{r}")
        ax[3].set_xticks(range(len(d)), d.index, fontsize=8)
    for a, t in zip(ax, ("A thickness", "B PCM fraction", "C flow", "D arrangement")):
        a.set_title(t, fontsize=10); a.axhline(0, color="k", lw=.6)
    ax[0].legend(fontsize=7)
    fig.suptitle(f"G7 sensitivity (paired against the same-condition water-only tank; energy delivered at {T_DEL} C)")
    save(fig, "fig22_sensitivity_blocks")


def fig23_controls():
    """G14: change in g_window of each control relative to the interior anchor design, against the band."""
    fig, ax = row_axes(4.8, 3.9)
    for i, r in enumerate(REG):
        c = csv(f"g14_controls_r{r}.csv")
        base_v = c[c.block == "base"].g_window.iloc[0]
        d = c[(c.block != "base") & c.g_window.notna()].copy()
        d["lab"] = d.block.str.replace("_", " ") + " " + d.level.astype(str)
        d["delta"] = d.g_window - base_v
        ax[i].barh(d.lab, d.delta, color=["#c0392b" if abs(v) > band(r) else "#95a5a6" for v in d.delta])
        ax[i].axvspan(-band(r), band(r), color=BAND_C, alpha=.2); ax[i].axvline(0, color="k", lw=.8)
        ax[i].invert_yaxis(); ax[i].tick_params(axis="y", labelsize=7)
        ax[i].set(title=f"Regime {r} (anchor g_window {base_v:.0f})", xlabel="change in g_window (kWh/yr)")
    fig.suptitle("G14 controls from an interior anchor: red = larger than the band")
    save(fig, "fig23_controls")


def fig24_stack_anchor():
    """G15: g_window of the chosen design with the capsule stack at the bottom, centre or top of the tank (select years)."""
    fig, ax = plt.subplots(figsize=(8, 4))
    allmin = np.inf
    for r in REG:
        d = csv(f"g15_anchor_r{r}.csv")
        d = d[(d.role == "chosen") & (d.purpose == "select")]
        allmin = min(allmin, d.g_window.min())
        m = d.groupby("anchor").g_window.agg(["mean", "min", "max"]).reindex(["bottom", "center", "top"])
        ax.errorbar(range(3), m["mean"], yerr=[m["mean"] - m["min"], m["max"] - m["mean"]], marker="o", capsize=3, color=RC[r], label=f"R{r}")
    ax.axhline(0, color="k", lw=.7)
    ax.set_xticks(range(3), ["bottom", "centre", "top"])
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
    fig, ax = plt.subplots(figsize=(8, 4))
    t.plot.bar(ax=ax, rot=0, color=["#2980b9", "#95a5a6", "#c0392b"])
    ax.set(ylabel="hours per year", title="G13 shield activity of the chosen designs (select years)")
    ax.legend(fontsize=7)
    save(fig, "fig25_shield_split")


def fig26_night_serve():
    """G16: night-serve duration and the share of the draw served at the 50 C target, PCM tank against the 50 L water-only tank (select years)."""
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    cases = [("pcm", "PCM tank (50 L)"), ("plain", "water-only 50 L")]
    for i, r in enumerate(REG):
        pc = csv(f"g16_serve_r{r}.csv")
        o, w = offs(i)
        for a, col, t in zip(ax, ("tau_serve_mean_h", "serve_frac_45_mean"), ("night-serve duration (h)", f"served at {T_DEL} C or above (share of draw)")):
            vals = [pc[pc.case == c][col].mean() for c, _ in cases]
            a.bar(np.arange(len(cases)) + o, vals, w, color=RC[r], label=f"R{r}")
            a.set_xticks(range(len(cases)), [l for _, l in cases], fontsize=8)
            a.set_title(t, fontsize=10)
    ax[0].legend(fontsize=7)
    fig.suptitle(f"G16 night serve at the {T_DEL} C target (select years; no 40 L water-only case was run for Uttarakhand)")
    save(fig, "fig26_night_serve")


def fig27_widened_box():
    """G17: gain against inner radius, PCM fraction and flow, with the v3 bounds marked."""
    fig, ax = plt.subplots(1, 3, figsize=(14, 3.9))
    for r in REG:
        g = csv(f"g17_widen_r{r}.csv")
        g = g[g.valid.astype(bool)]
        for a, (blk, x, lab, cap) in zip(ax, (("A_radius", "R_in_mm", "inner radius (mm)", 40), ("B_fraction", "fraction_req", "PCM fraction", .30), ("D_flow", "flow", "flow (kg/s)", .05))):
            d = g[g.block == blk].sort_values(x)
            if d.empty:
                continue
            a.plot(d[x], d.g_window, marker="o", ms=4, color=RC[r], label=f"R{r}")
            a.axvline(cap, color="k", ls=":", lw=1)
            a.set(xlabel=lab, ylabel="g_window (kWh/yr)")
    for a, t in zip(ax, ("radius", "PCM fraction", "flow")):
        a.set_title(f"{t} (dotted line = v3 bound)", fontsize=9); a.axhline(0, color="k", lw=.6)
    ax[0].legend(fontsize=7)
    fig.suptitle("G17 widened-bound diagnostic (explore years)")
    save(fig, "fig27_widened_box")


def fig28_sizing():
    """G21 tank-sizing study."""
    need("g21_sizing_r0.csv")


def fig29_sensitivity_tornado():
    """G22 model-input sensitivity."""
    need("g22_sensitivity_r0.csv")


def fig30_flow_fr():
    """G24 flow-dependent collector F_R study."""
    need("g24_flow_fr_r0.csv")


def fig31_gpbo_vs_nsga():
    """G20 GP Bayesian search against NSGA-II."""
    need("g20_gpbo_r0_p1.csv")


def fig32_box_vertex():
    """G18 search variants."""
    need("g18_issue1_with_without.csv")


def fig33_b1_retest():
    """B1 widened-box re-test."""
    need("b1_selection_r0.json")


def fig34_night_hold():
    """G3: hours the tank holds the 50 C target and serves it after each evening, PCM tank against water-only tank."""
    fig, ax = plt.subplots(2, NR, figsize=(3.5 * NR, 6))
    for i, r in enumerate(REG):
        for j, (col, t) in enumerate((("tau_hold_h", f"hold time at {T_DEL} C (h)"), ("tau_serve_h", "night-serve duration (h)"))):
            p = csv(f"g3_night_daily_r{r}_pcm.csv")[col].dropna()
            w = csv(f"g3_night_daily_r{r}_plain.csv")[col].dropna()
            boxplot(ax[j, i], [w, p], ["water-only", "PCM"], patch_artist=True, boxprops=dict(facecolor=RC[r], alpha=.5), flierprops=dict(ms=2))
            ax[j, i].set_title(f"Regime {r}: {t}", fontsize=9)
    fig.suptitle("G3 night metrics over every evening of a year (reference PCM, before the optimisation)")
    save(fig, "fig34_night_hold")


def fig35_chen_benchmark():
    """G23 Chen 2025 benchmark."""
    need("g23_chen_benchmark_r0.csv")


def fig40_of_capsule():
    """OpenFOAM single-capsule case(s) that were run for Uttarakhand: melt times, and the grey-box model's t90 against the CFD."""
    need("cfd_capsule_results_uttarakhand.csv", root=OF)
    d = csv("cfd_capsule_results_uttarakhand.csv", OF)
    ok = d[d.status == "ok"]
    if ok.empty:
        raise Skip("no OpenFOAM case has status ok")
    labs = [f"{c.split('/')[-1]}" for c in ok.case]
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    x = np.arange(len(ok))
    for i, (c, l) in enumerate((("t_melt_50_s", "50 % liquid"), ("t_melt_90_s", "90 %"), ("t_melt_99_s", "99 %"))):
        ax[0].bar(x + (i - 1) * .27, ok[c] / 60, .27, label=l)
    ax[0].set_xticks(x, labs, fontsize=8)
    ax[0].set(ylabel="minutes", title="CFD melt times")
    ax[0].legend(fontsize=8)
    ax[1].bar(x - .2, ok.t_melt_90_s / 60, .4, color="#2c3e50", label="OpenFOAM")
    ax[1].bar(x + .2, ok.greybox_t_melt_90_s_x2 / 60, .4, color="#2980b9", label="grey-box (lumped, x2 convection)")
    for j, v in enumerate(ok.greybox_over_cfd_t90):
        ax[1].text(j + .2, ok.greybox_t_melt_90_s_x2.iloc[j] / 60, f"x{v:.2f}", ha="center", va="bottom", fontsize=8)
    ax[1].set_xticks(x, labs, fontsize=8)
    ax[1].set(ylabel="minutes to 90 % liquid", title="Grey-box against CFD at 90 % melt")
    ax[1].legend(fontsize=8)
    n_all = int((d.kind.str.startswith("capsule")).sum())
    fig.suptitle(f"OpenFOAM capsule runs: {len(ok)} of {n_all} capsule cases run; model-to-model only, not validated against measurements")
    save(fig, "fig40_of_capsule")


def fig41_of_lumped_vs_cfd():
    """OpenFOAM spot-check of the lumped closures."""
    need("of_spotcheck.csv", root=OF)


def fig42_of_mesh_and_freeze():
    """OpenFOAM mesh study and freezing check."""
    need("of_mesh_study.csv", root=OF)


def fig50_weather_inputs():
    """Annual irradiation and mean temperature of the regime medoid point for every weather year, coloured by role."""
    import re
    from src.weather import roles
    files = sorted((ROOT / "data" / "weather" / "point_years" / "uttarakhand").glob("cluster*_*.csv"))
    rows = []
    for f in files:
        m = re.match(r"cluster(\d)_(UKP_\d+)_(\d{4})\.csv", f.name)
        if not m:
            continue
        d = pd.read_csv(f)
        rows.append(dict(regime=int(m.group(1)), year=int(m.group(3)), ghi=d.GHI_Wm2.clip(lower=0).sum() / 1000, tamb=d.T_amb_C.mean()))
    w = pd.DataFrame(rows)
    w["role"] = w.year.map(roles.YEAR_ROLES)
    fig, ax = plt.subplots(2, NR, figsize=(3.6 * NR, 6), sharex=True)
    for i, r in enumerate(REG):
        d = w[w.regime == r].sort_values("year")
        for j, (c, t) in enumerate((("ghi", "annual GHI (kWh/m2)"), ("tamb", "mean ambient temperature (C)"))):
            ax[j, i].vlines(d.year, d[c].min(), d[c], color="#ddd", lw=.8)
            ax[j, i].scatter(d.year, d[c], s=50, color=[ROLE.get(x, "#999") for x in d.role], zorder=3)
            ax[j, i].set_title(f"Regime {r}: {t}", fontsize=9)
    h = [plt.Rectangle((0, 0), 1, 1, color=ROLE[k]) for k in ("explore", "select", "test")]
    fig.legend(h, ["explore 2016-20", "select 2021-23", "held-out 2024-25 (used once)"], loc="lower center", ncol=3, fontsize=8)
    fig.suptitle("Weather inputs of the four regime medoid points, by year role")
    fig.tight_layout(rect=(0, .05, 1, 1))
    OUT.mkdir(parents=True, exist_ok=True)
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
                                  fig40_of_capsule, fig41_of_lumped_vs_cfd, fig42_of_mesh_and_freeze, fig50_weather_inputs)]


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
    ok, bad, skipped, t0 = [], [], [], time.time()
    for n, f in figs:
        try:
            f()
            ok.append(n)
        except Skip as e:
            skipped.append((n, str(e)))
            print(f"  skipped {n}: {e}")
        except Exception as e:                       # one broken figure must not stop the rest
            plt.close("all")
            bad.append((n, repr(e)[:160]))
            print(f"  FAILED {n}: {e!r}")
            traceback.print_exc(limit=2)
    print(f"\n{len(ok)} written, {len(skipped)} skipped (study not run for Uttarakhand), {len(bad)} failed in {time.time() - t0:.0f} s -> {OUT}")
    for n, e in bad:
        print("  FAILED", n, e)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
