"""
plot_v4_pcm_comparison.py
=========================
The four shortlisted Tamil Nadu PCMs, melted on one mesh under one duty.

Reads v4_<pcm>_melt_history.csv (written incrementally by pyfluent_v4_melt.py)
and draws the melt curves plus the capsule-temperature curves. Partial runs are
plotted as far as they got -- a diverged or still-running case shows a short
curve rather than vanishing, so the figure never silently omits a PCM.

Run: python plot_v4_pcm_comparison.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "figures" / "03_pcm_melt_comparison.png"
OUT.parent.mkdir(exist_ok=True)

# Fixed order and fixed hue per PCM -- the colour follows the MATERIAL, so a
# PCM keeps its colour if a run is added or drops out. Order is the Objective-1
# shortlist ranking, not the order the runs happened to finish in.
SERIES = [
    ("rt57hc",     "RT57HC",              56.5, "#1f77b4"),
    ("c26",        "n-Hexacosane (C26)",  56.5, "#d62728"),
    ("c25",        "n-Pentacosane (C25)", 54.0, "#2ca02c"),
    ("puretemp58", "PureTemp 58",         58.0, "#9467bd"),
]

INK = "#2b2b2b"
MUTED = "#6b6b6b"
GRID = "#d8d8d8"


# A diverged Fluent run clamps temperature at its 5000 K ceiling and returns
# NaN liquid fractions. Those rows are not data and must never reach a figure.
T_CEILING_K = 1000.0


def load(key):
    """Load a melt history, preferring a re-run over a diverged original.

    Filenames carry a doubled suffix (v4_<key>_melt_melt_history.csv) because
    the driver passes a save basename already ending in "_melt". Candidates are
    tried newest-intent first: an explicit dt5 re-run supersedes the original.
    """
    # v7 first: it is the only set where all four PCMs solved, and the only one
    # where every PCM shares identical solver settings (Coupled + first-order).
    for stem in (f"v7_{key}", f"v4_{key}_dt5", f"v4_{key}_melt", f"v4_{key}"):
        p = HERE / f"{stem}_melt_history.csv"
        if not p.exists():
            continue
        d = pd.read_csv(p)
        if not len(d):
            continue
        clean = d[d.T_capsule_mean_K.notna() & (d.T_capsule_mean_K < T_CEILING_K)
                  & d.liquid_fraction.notna()]
        # A run that diverged in its first chunk leaves nothing usable; say so
        # rather than drawing a one-point curve that looks like a result.
        if len(clean) < 2:
            print(f"  {key}: {p.name} diverged (no usable rows) -- skipped")
            continue
        if len(clean) < len(d):
            print(f"  {key}: {p.name} -- dropped {len(d) - len(clean)} diverged row(s)")
        return clean.reset_index(drop=True)
    return None


def main():
    data = {k: load(k) for k, _, _, _ in SERIES}
    present = [(k, lbl, tm, c) for k, lbl, tm, c in SERIES if data[k] is not None and len(data[k]) > 1]
    if not present:
        raise SystemExit("no melt histories found -- has run_v4_pcm_comparison.sh produced any output?")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.6))
    fig.patch.set_facecolor("white")

    for key, label, tm_c, colour in present:
        d = data[key]
        h = d.time_s / 3600.0
        ax1.plot(h, d.liquid_fraction, lw=2.0, color=colour, label=label, solid_capstyle="round")
        ax2.plot(h, d.T_capsule_mean_K - 273.15, lw=2.0, color=colour, label=label, solid_capstyle="round")
        # melt point as a recessive reference, in the series colour but faint
        ax2.axhline(tm_c, color=colour, lw=1.0, ls=":", alpha=0.55)

    # direct labels at the end of each curve (<=4 series, so both legend and
    # direct labels, per the project's figure convention)
    for key, label, _, colour in present:
        d = data[key]
        x, y = d.time_s.iloc[-1] / 3600.0, d.liquid_fraction.iloc[-1]
        ax1.annotate(f"{y:.2f}", (x, y), xytext=(5, 0), textcoords="offset points",
                     color=INK, fontsize=9, va="center")

    ax1.set_xlabel("time (h)", color=INK)
    ax1.set_ylabel("capsule liquid fraction", color=INK)
    ax1.set_title("Melt progress — identical mesh, identical duty", color=INK, fontsize=12)
    ax1.set_ylim(-0.02, 1.02)

    ax2.set_xlabel("time (h)", color=INK)
    ax2.set_ylabel("capsule mean temperature (°C)", color=INK)
    ax2.set_title("Capsule temperature (dotted = each PCM's melt point)", color=INK, fontsize=12)

    for ax in (ax1, ax2):
        ax.grid(True, color=GRID, lw=0.6, alpha=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(GRID)
        ax.tick_params(colors=MUTED, labelsize=9)

    ax1.legend(frameon=False, fontsize=9, labelcolor=INK, loc="upper left")

    fig.suptitle("ANSYS Fluent — PCM melting comparison, Tamil Nadu shortlist",
                 color=INK, fontsize=14, x=0.01, ha="left", y=0.99)
    # Two short lines rather than one long one: a single line of this length
    # overflows the figure width and gets clipped at the right edge.
    fig.text(0.01, 0.035,
             "Capsule Ø 42 mm initially 30 °C solid, immersed in water at 70 °C (collector delivery). "
             "Enthalpy-porosity, 10 K mushy band, 2-D planar half-slice.",
             color=MUTED, fontsize=8.5, ha="left")
    fig.text(0.01, 0.008,
             "Coupled pressure–velocity, first-order upwind — more diffusive than second order, so these "
             "melt fractions are conservative. The ORDERING is the result, not the absolute values.",
             color=MUTED, fontsize=8.5, ha="left")
    fig.tight_layout(rect=[0, 0.065, 1, 0.96])
    fig.savefig(OUT, dpi=150, facecolor="white")
    print(f"wrote {OUT}")

    print(f"\n{'PCM':24s} {'Tm (°C)':>8s} {'t_end (h)':>10s} {'liq.frac':>9s} {'T_end (°C)':>11s}")
    for key, label, tm_c, _ in present:
        d = data[key]
        print(f"{label:24s} {tm_c:8.1f} {d.time_s.iloc[-1] / 3600:10.2f} "
              f"{d.liquid_fraction.iloc[-1]:9.3f} {d.T_capsule_mean_K.iloc[-1] - 273.15:11.2f}")
    missing = [lbl for k, lbl, _, _ in SERIES if data[k] is None]
    if missing:
        print(f"\nNOT YET AVAILABLE: {', '.join(missing)}")


if __name__ == "__main__":
    main()
