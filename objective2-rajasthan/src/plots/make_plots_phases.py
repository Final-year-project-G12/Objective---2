"""
src/plots/make_plots_phases.py
==========================================
The 17 phase figures of the legacy set (Phases 2-8, src/plots/make_plots.py), rebuilt for the current Objective 2
chain (G1-G14). Same file names, same format: every figure is built once in Plotly and saved twice
  results/plots/static/<name>.png          flat image for reports and slides
  results/plots/interactive/<name>.html    self-contained, zoom / hover / legend toggles

Each figure answers the same question as its legacy namesake, but from the current data: the 3-variable-plus-arrangement
design vector (inner radius, PCM fraction, flow, arrangement), the multi-node tank, the paired gains over the water-only tank, and the
year roles explore 2016-2020 / select 2021-2023 / held-out 2024-2025. Where the old figure had no honest equivalent the
substitution is stated in the figure title and in docs/plots/10_PLOTS.md (Phase 8 Monte Carlo -> weather-year robustness;
Phase 6 surrogate importance -> ANOVA contribution; Gate 5 pump energy -> window delivered energy, because pump energy is not meaningful).

Data rules
  * Most figures only READ saved files under results/.
  * Figures that need a time series or a fresh sensitivity run (phase3_*, phase4_gate5, parity, robustness) simulate once on the
    EXPLORE / SELECT years and cache the result under results/plots_data/. Re-run with --refresh to rebuild the cache.
  * The held-out years are never simulated here. Their numbers come from results/g10_heldout_results.csv, which the single
    permitted run already produced; this module never calls the held-out loader.

Run: python -m src.plots.make_plots_phases [--refresh] [--only name1,name2] [--jobs N]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import RESULTS_DIR
from src.design.constraints import check_design
from src.design.geometry import compute_hydraulics
from src.design.space import geometry_bounds, load_space, to_design, wall_m
from src.io_utils import get_pcm_properties, load_system_config
from src.simulation.run_case import run_case
from src.weather import roles
from src.weather.inventory import CURRENT_MEDOIDS

TEMPLATE = "plotly_white"
RD = RESULTS_DIR
OUT = RD / "plots"
DATA = RD / "plots_data"
REGIMES = (0, 1, 2)
ARRANGEMENTS = ("single-layer", "staggered", "radial")
ARR_COL = {"single-layer": "#1f77b4", "staggered": "#2ca02c", "radial": "#d62728"}
REGIME_COL = {0: "#1f77b4", 1: "#ff7f0e", 2: "#2ca02c"}
ROLE_COL = {"explore": "#7f7f7f", "select": "#1f77b4", "held-out": "#d62728"}
SAMPLE_YEAR = 2018          # an EXPLORE year for the single-run time series
SAMPLE_REGIME = 0
REFRESH = False


# --------------------------------------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------------------------------------

def _clean(s):
    """The PCM database stores the registered-trademark sign as U+FFFD in some CSVs; show it as the real sign."""
    return str(s).replace("�", "®")


def _csv(name):
    return pd.read_csv(RD / name)


def _chosen(regime):
    return json.load(open(RD / f"g10_selection_r{regime}.json", encoding="utf-8"))["chosen"]


def _band(regime, obj="g_window"):
    b = _csv("wp6_band.csv")
    return float(b[(b.scope == f"r{regime}") & (b.objective == obj)].band.iloc[0])


def _save(fig, name, width=1000, height=620):
    (OUT / "static").mkdir(parents=True, exist_ok=True)
    (OUT / "interactive").mkdir(parents=True, exist_ok=True)
    fig.update_layout(template=TEMPLATE, width=width, height=height)
    fig.write_image(str(OUT / "static" / f"{name}.png"), scale=2)
    fig.write_html(str(OUT / "interactive" / f"{name}.html"), include_plotlyjs="inline")
    print(f"  [OK] {name}", flush=True)


def _cached(path: Path, build):
    """Return the cached DataFrame, or build it (once) and store it."""
    if path.exists() and not REFRESH:
        return pd.read_csv(path)
    DATA.mkdir(parents=True, exist_ok=True)
    df = build()
    df.to_csv(path, index=False)
    return df


def _model_kwargs():
    m = load_space()["model"]
    return dict(tank_model=m["tank_model"], n_nodes=m["n_nodes"], stack_anchor=m["stack_anchor"])


def _weather(regime, year, purpose):
    if purpose not in ("explore", "select"):
        raise ValueError("this module never loads held-out weather")
    return roles.load_point_year("rajasthan", regime, CURRENT_MEDOIDS[regime], year, purpose)


def _plain_design(flow):
    return to_design(0.02, 0.05, float(flow), "staggered")      # geometry is irrelevant for the plain tank


def _num(o):
    return float(o) if hasattr(o, "__float__") else str(o)


# --------------------------------------------------------------------------------------------------------------------
# PHASE 2 - geometry and constraints
# --------------------------------------------------------------------------------------------------------------------

def phase2_validity_map():
    sp = load_space()["variables"]
    cfg, gb = load_system_config(), geometry_bounds()
    rs = np.linspace(sp["inner_radius_m"]["min"], sp["inner_radius_m"]["max"], 31)
    fs = np.linspace(sp["pcm_volume_fraction"]["min"], sp["pcm_volume_fraction"]["max"], 37)
    rows = []
    for a in ARRANGEMENTS:
        for r in rs:
            for f in fs:
                dv = to_design(float(r), float(f), 0.030, a)
                g = check_design(dv, cfg, gb)
                rows.append({"arr": a, "R": r * 1000, "f": f * 100, "N": dv.n_capsule,
                             "reason": "valid" if g["valid"] else g["reason"]})
    df = pd.DataFrame(rows)
    colors = {"valid": "#2ca02c", "bounds_violation": "#d62728", "overlap": "#9467bd", "volume_exceeded": "#ff7f0e",
              "passage_blocked": "#8c564b", "pressure_drop_limit": "#e377c2"}
    fig = make_subplots(rows=1, cols=3, shared_yaxes=True, subplot_titles=ARRANGEMENTS, horizontal_spacing=0.03)
    seen = set()
    for c, a in enumerate(ARRANGEMENTS, start=1):
        for reason, g in df[df.arr == a].groupby("reason"):
            fig.add_trace(go.Scatter(x=g.R, y=g.f, mode="markers", name=reason, legendgroup=reason,
                                     showlegend=reason not in seen, customdata=g.N,
                                     marker=dict(size=6, symbol="square", color=colors.get(reason, "#7f7f7f")),
                                     hovertemplate="R_in=%{x:.1f} mm<br>fraction=%{y:.1f} %<br>N=%{customdata}<br>" + reason +
                                                   "<extra></extra>"), row=1, col=c)
            seen.add(reason)
        fig.update_xaxes(title_text="PCM thickness = inner radius (mm)", row=1, col=c)
    fig.update_yaxes(title_text="requested PCM volume fraction (%)", row=1, col=1)
    fig.update_layout(title="Phase 2 - design-space validity map, flow fixed at 0.030 kg/s - rajasthan")
    _save(fig, "phase2_validity_map", width=1250)


def phase2_ergun_hydraulics():
    cfg = load_system_config()
    sp = load_space()["variables"]
    flows = np.linspace(0.002, 0.10, 60)
    fig = go.Figure()
    for r in (0.010, 0.020, 0.030, 0.040):
        d = 2 * (r + wall_m())
        dp = [compute_hydraulics(f, d, void_fraction=0.90, cross_section_area_m2=0.0789, bed_length_m=0.10,
                                 system_config=cfg)["pressure_drop_pa"] for f in flows]
        fig.add_trace(go.Scatter(x=flows, y=dp, mode="lines", name=f"inner radius {r * 1000:.0f} mm (D={d * 1000:.0f} mm)"))
    fig.add_vrect(x0=sp["flow_rate_kg_s"]["min"], x1=sp["flow_rate_kg_s"]["max"], fillcolor="green", opacity=0.08,
                  line_width=0, annotation_text="permitted flow range")
    fig.update_layout(title="Phase 2 - Ergun pressure drop across the capsule bed vs flow - rajasthan<br>"
                            "<sup>millipascal-scale: the loop's real pressure drop is not modelled, so pump energy is not a design driver</sup>",
                      xaxis_title="flow_rate_kg_s", yaxis_title="pressure_drop_pa (void=0.90, bed length=0.10 m)", yaxis_type="log")
    _save(fig, "phase2_ergun_hydraulics")


# --------------------------------------------------------------------------------------------------------------------
# PHASE 3 - simulator (one chosen design, one explore year)
# --------------------------------------------------------------------------------------------------------------------

def _sample_runs():
    """Hourly series + metrics of the chosen regime-0 design and its water-only twin, on one EXPLORE year (cached)."""
    paths = {k: DATA / f"sample_{k}_hourly.csv" for k in ("pcm", "plain")}
    meta = DATA / "sample_meta.json"
    if all(p.exists() for p in paths.values()) and meta.exists() and not REFRESH:
        return {k: pd.read_csv(p) for k, p in paths.items()}, json.load(open(meta, encoding="utf-8"))
    DATA.mkdir(parents=True, exist_ok=True)
    c = _chosen(SAMPLE_REGIME)
    w = _weather(SAMPLE_REGIME, SAMPLE_YEAR, "explore")
    gb = geometry_bounds()
    out = {}
    print(f"  simulating sample year {SAMPLE_YEAR} (PCM design, then water-only twin; about 40 s)", flush=True)
    out["pcm"] = run_case("rajasthan", SAMPLE_REGIME, c["pcm"], to_design(c["R_in_m"], c["fraction"], c["flow"], c["arrangement"]),
                          design_bounds=gb, weather=w, record_hourly=True, compute_tes_metrics=True, night_day_stride=0, **_model_kwargs())
    out["plain"] = run_case("rajasthan", SAMPLE_REGIME, None, _plain_design(c["flow"]), design_bounds=gb, weather=w,
                            record_hourly=True, compute_tes_metrics=True, night_day_stride=0, **_model_kwargs())
    for k in out:
        out[k]["hourly"].to_csv(paths[k], index=False)
    m = {"pcm_name": _clean(c["pcm"]), "year": SAMPLE_YEAR, "regime": SAMPLE_REGIME,
         "pcm": {"metrics": out["pcm"]["metrics"], "tes": out["pcm"]["tes"]},
         "plain": {"metrics": out["plain"]["metrics"], "tes": out["plain"]["tes"]}}
    json.dump(m, open(meta, "w", encoding="utf-8"), default=_num, indent=1)
    return {k: out[k]["hourly"] for k in out}, json.load(open(meta, encoding="utf-8"))


def phase3_temperature_timeseries():
    h, m = _sample_runs()
    a, b = 2400, 2568                                  # same representative week as the legacy figure (day 100-107)
    wk, wp = h["pcm"].iloc[a:b], h["plain"].iloc[a:b]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=wk.hour_index, y=wk.T_w_C, name="T_water, PCM tank (C)", line=dict(color="#1f77b4")), secondary_y=False)
    fig.add_trace(go.Scatter(x=wp.hour_index, y=wp.T_w_C, name="T_water, water-only twin (C)", line=dict(color="#1f77b4", dash="dash")),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=wk.hour_index, y=wk.T_pcm_C, name="T_PCM (C)", line=dict(color="#d62728")), secondary_y=False)
    fig.add_trace(go.Scatter(x=wk.hour_index, y=wk.I_t_Wm2, name="Irradiance (W/m2)", line=dict(color="#ff7f0e", dash="dot")),
                  secondary_y=True)
    fig.update_layout(title=f"Phase 3 - one representative week, {m['year']} (explore year): chosen regime-{m['regime']} "
                            f"design, {m['pcm_name']}", xaxis_title="hour of year")
    fig.update_yaxes(title_text="Temperature (C)", secondary_y=False)
    fig.update_yaxes(title_text="Irradiance (W/m2)", secondary_y=True)
    _save(fig, "phase3_temperature_timeseries")


def phase3_melt_fraction_year():
    h, m = _sample_runs()
    d = h["pcm"].copy()
    d["day"] = d.hour_index // 24
    day = d.groupby("day").agg(fmax=("f_melt_max", "max"), fmin=("f_melt_min", "min"), fmean=("f_melt", "mean")).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=day.day, y=day.fmax, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=day.day, y=day.fmin, mode="lines", line=dict(width=0), fill="tonexty", fillcolor="rgba(44,160,44,0.30)",
                             name="daily min to max"))
    fig.add_trace(go.Scatter(x=day.day, y=day.fmean, mode="lines", line=dict(color="#1b6b1b", width=1.5), name="daily mean"))
    n_full = int(((day.fmax >= 0.99) & (day.fmin <= 0.01)).sum())
    fig.update_layout(title=f"Phase 3 - PCM liquid fraction, year {m['year']}, chosen regime-{m['regime']} design"
                            f"<br><sup>{m['pcm_name']}: {n_full} of {len(day)} days melt completely and freeze back completely "
                            f"(hourly series folded to daily min / max / mean)</sup>",
                      xaxis_title="day of year", yaxis_title="liquid fraction f_melt [0-1]")
    _save(fig, "phase3_melt_fraction_year")


def phase3_energy_breakdown():
    _, m = _sample_runs()
    labels = ["Collector input", "Delivered to load", "Delivered at >=45 C, 18:00-09:00", "Tank/pipe loss", "Unmet (shortfall)"]

    def vals(k):
        mm, tt = m[k]["metrics"], m[k]["tes"]
        return [mm["collector_energy_kWh"], mm["useful_energy_kWh"], tt["E_del45_window_kWh"], mm["loss_energy_kWh"],
                mm["unmet_energy_kWh"]]
    fig = go.Figure()
    for k, col, nm in (("plain", "#7f7f7f", "water-only twin"), ("pcm", "#1f77b4", "chosen PCM design")):
        v = vals(k)
        fig.add_trace(go.Bar(x=labels, y=v, name=nm, marker_color=col, text=[f"{x:,.0f}" for x in v], textposition="outside"))
    fig.update_layout(barmode="group", title=f"Phase 3 - annual energy breakdown, {m['year']} (explore year), regime {m['regime']}",
                      yaxis_title="kWh / year")
    _save(fig, "phase3_energy_breakdown")


# --------------------------------------------------------------------------------------------------------------------
# PHASE 4 - verification gates
# --------------------------------------------------------------------------------------------------------------------

def phase4_gate1_residuals():
    g4 = _csv("g4_multinode_report.csv")
    g2 = _csv("g2_timestep_convergence_300_150_75.csv")
    fig = make_subplots(rows=1, cols=2, column_widths=[0.55, 0.45],
                        subplot_titles=("tank model: single node vs multi-node (G4)", "time step 300 / 150 / 75 s (G2)"))
    for model, col in (("single", "#7f7f7f"), ("multinode", "#1f77b4")):
        d = g4[g4.model == model]
        lab = "R" + d.regime.astype(str) + " " + d.case.astype(str) + (" n=" + d.n_nodes.astype(str) if model == "multinode" else "")
        fig.add_trace(go.Bar(x=lab, y=d.residual_pct, name=model, marker_color=col), row=1, col=1)
    lab2 = "R" + g2.regime.astype(str) + " " + g2.case.astype(str) + " dt=" + g2.dt_s.astype(int).astype(str)
    fig.add_trace(go.Bar(x=lab2, y=g2.residual_pct, name="time-step study", marker_color="#2ca02c"), row=1, col=2)
    for c in (1, 2):
        fig.add_hline(y=0.1, line_dash="dash", line_color="orange", row=1, col=c)
        fig.add_hline(y=0.5, line_dash="dash", line_color="red", row=1, col=c)
        fig.update_yaxes(type="log", range=[-14, 0.3], dtick=2, tickformat=".0e", row=1, col=c)
        fig.update_xaxes(tickangle=-60, tickfont=dict(size=8), row=1, col=c)
    fig.update_yaxes(title_text="residual (% of collector energy); dashed = 0.1 % pass, 0.5 % stop", row=1, col=1)
    fig.update_layout(title="Phase 4 Gate 1 - energy-conservation residual, explore-year cases - rajasthan", barmode="group")
    _save(fig, "phase4_gate1_residuals", width=1250, height=680)


def phase4_gate3_baseline_comparison():
    g = _csv("g4_multinode_report.csv")
    g = g[(g.model == "single") | (g.n_nodes == load_space()["model"]["n_nodes"])]
    fig = go.Figure()
    for (model, case), col in ((("single", "plain"), "#bdbdbd"), (("single", "pcm"), "#7f7f7f"),
                               (("multinode", "plain"), "#9ecae1"), (("multinode", "pcm"), "#1f77b4")):
        d = g[(g.model == model) & (g.case == case)].drop_duplicates("regime").sort_values("regime")
        fig.add_trace(go.Bar(x=d.regime, y=d.solar_fraction * 100, name=f"{case}, {model} tank", marker_color=col,
                             text=[f"{v:.1f}%" for v in d.solar_fraction * 100], textposition="outside"))
    test_pcm = g[g.case == "pcm"].drop_duplicates("regime").sort_values("regime")
    fig.update_xaxes(tickvals=list(test_pcm.regime), ticktext=[f"Regime {r}<br>G4 test PCM: {_clean(p)[:20]}"
                                                               for r, p in zip(test_pcm.regime, test_pcm.pcm)])
    fig.update_layout(barmode="group", title="Phase 4 Gate 3 - solar fraction, water-only vs PCM, single-node vs multi-node tank"
                                             "<br><sup>G4 test designs (explore year), run before the O1 shortlist was restored in G6; "
                                             "not the final chosen designs</sup>", yaxis_title="solar fraction (%)")
    _save(fig, "phase4_gate3_baseline_comparison")


def _gate5_runs():
    def build():
        c = _chosen(SAMPLE_REGIME)
        w = _weather(SAMPLE_REGIME, SAMPLE_YEAR, "explore")
        gb = geometry_bounds()
        rec = get_pcm_properties("rajasthan", c["pcm"])
        dv = to_design(c["R_in_m"], c["fraction"], c["flow"], c["arrangement"])
        rows = []
        cases = [("base", "baseline", c["flow"], {}), ("latent", "-10%", c["flow"], {"latent_heat_kJ_kg": rec["latent_heat_kJ_kg"] * 0.9}),
                 ("latent", "+10%", c["flow"], {"latent_heat_kJ_kg": rec["latent_heat_kJ_kg"] * 1.1}),
                 ("flow", "-50%", c["flow"] * 0.5, {}), ("flow", "+50%", min(c["flow"] * 1.5, 0.05), {})]
        print("  gate-5 sensitivity: 5 runs of one explore year (about 100 s)", flush=True)
        for block, level, flow, ov in cases:
            d = to_design(c["R_in_m"], c["fraction"], flow, c["arrangement"])
            r = run_case("rajasthan", SAMPLE_REGIME, c["pcm"], d, design_bounds=gb, weather=w, record_hourly=False,
                         compute_tes_metrics=True, night_day_stride=0, pcm_record_overrides=ov or None, **_model_kwargs())
            rows.append({"block": block, "level": level, "flow": flow, "charge_energy_kWh": r["metrics"]["charge_energy_kWh"],
                         "E_del45_window_kWh": r["tes"]["E_del45_window_kWh"], "pump_energy_kWh": r["metrics"]["pump_energy_kWh"]})
        return pd.DataFrame(rows)
    return _cached(DATA / "gate5_sensitivity.csv", build)


def phase4_gate5_sensitivity():
    d = _gate5_runs()
    base = d[d.block == "base"].iloc[0]
    lat = pd.concat([d[(d.block == "latent") & (d.level == "-10%")], d[d.block == "base"], d[(d.block == "latent") & (d.level == "+10%")]])
    flo = pd.concat([d[(d.block == "flow") & (d.level == "-50%")], d[d.block == "base"], d[(d.block == "flow") & (d.level == "+50%")]])
    fig = make_subplots(rows=1, cols=2, subplot_titles=("PCM charge energy vs latent heat +/-10 %",
                                                        "Window delivered energy vs flow +/-50 %"))
    fig.add_trace(go.Bar(x=["-10%", "baseline", "+10%"], y=lat.charge_energy_kWh, marker_color="#1f77b4", showlegend=False,
                         text=[f"{v:.1f}" for v in lat.charge_energy_kWh], textposition="outside"), row=1, col=1)
    fig.add_trace(go.Bar(x=["-50%", "baseline", "+50%"], y=flo.E_del45_window_kWh, marker_color="#2ca02c", showlegend=False,
                         text=[f"{v:.1f}" for v in flo.E_del45_window_kWh], textposition="outside"), row=1, col=2)
    fig.update_yaxes(title_text="charge_energy_kWh", row=1, col=1)
    fig.update_yaxes(title_text="E_del45 window 18:00-09:00 (kWh/yr)", row=1, col=2)
    fig.update_layout(title=f"Phase 4 Gate 5 - sensitivity / monotonicity spot checks, chosen regime-{SAMPLE_REGIME} design, "
                            f"{SAMPLE_YEAR}<br><sup>pump energy (the legacy second panel) is {base.pump_energy_kWh:.1e} kWh/yr and "
                            f"not meaningful, so window delivered energy is shown instead</sup>")
    _save(fig, "phase4_gate5_sensitivity", width=1150)


# --------------------------------------------------------------------------------------------------------------------
# PHASE 5 - DOE
# --------------------------------------------------------------------------------------------------------------------

def _doe():
    frames = []
    for f in sorted(RD.glob("g8_s2_r*_p*.csv")):
        d = pd.read_csv(f)
        frames.append(d[["cluster", "pcm", "R_in_m", "fraction_req", "flow", "arrangement", "N", "feasible", "valid", "g_window",
                         "g_annual", "d_overheat", "t_pcm_max"]].assign(pair=f.stem.replace("g8_s2_", "")))
    return pd.concat(frames, ignore_index=True)


def _screening():
    frames = []
    for f in sorted(RD.glob("g8_s1_r*_p*.csv")):
        if "anova" in f.name:
            continue
        d = pd.read_csv(f)
        frames.append(d[["regime", "R_in_mm", "fraction", "flow", "arrangement"]].drop_duplicates())
    return pd.concat(frames, ignore_index=True)


def phase5_doe_coverage():
    d, s1 = _doe(), _screening()
    fig = make_subplots(rows=1, cols=2, subplot_titles=("PCM fraction vs inner radius", "flow vs inner radius"))
    shown = set()
    for a in ARRANGEMENTS:
        for feas, sym in ((True, "circle"), (False, "x")):
            g = d[(d.arrangement == a) & (d.feasible.astype(bool) == feas)]
            if g.empty:
                continue
            nm = f"{a}, " + ("feasible" if feas else "PCM peak > 65 C")
            for c, y in ((1, g.fraction_req * 100), (2, g.flow)):
                fig.add_trace(go.Scatter(x=g.R_in_m * 1000, y=y, mode="markers", name=nm, legendgroup=nm, showlegend=nm not in shown,
                                         text=g.pair + " " + g.pcm.map(_clean),
                                         marker=dict(size=7, symbol=sym, color=ARR_COL[a], opacity=0.75),
                                         hovertemplate="%{text}<br>R_in=%{x:.1f} mm<br>%{y:.3f}<extra></extra>"), row=1, col=c)
                shown.add(nm)
    for c, y in ((1, s1.fraction * 100), (2, s1.flow)):
        fig.add_trace(go.Scatter(x=s1.R_in_mm, y=y, mode="markers", name="screening designs (S1)", legendgroup="s1", showlegend=c == 1,
                                 marker=dict(size=10, symbol="diamond-open", color="black")), row=1, col=c)
    fig.update_xaxes(title_text="inner radius (mm)")
    fig.update_yaxes(title_text="requested PCM fraction (%)", row=1, col=1)
    fig.update_yaxes(title_text="flow_rate_kg_s", row=1, col=2)
    fig.update_layout(title=f"Phase 5 - DOE sample coverage: {len(d)} Sobol designs over 9 regime-PCM pairs "
                            f"+ screening - rajasthan")
    _save(fig, "phase5_doe_coverage", width=1200)


def phase5_outcome_distribution():
    d = _doe()
    d = d[d.feasible.astype(bool)]
    fig = make_subplots(rows=1, cols=3, subplot_titles=("g_window (kWh/yr)", "g_annual (kWh/yr)", "d_overheat (h/yr)"))
    for c, (col, colr) in enumerate((("g_window", "#1f77b4"), ("g_annual", "#ff7f0e"), ("d_overheat", "#d62728")), start=1):
        fig.add_trace(go.Histogram(x=d[col], marker_color=colr, showlegend=False), row=1, col=c)
        fig.add_vline(x=0, line_dash="dash", line_color="black", row=1, col=c)
    fig.update_layout(title=f"Phase 5 - outcome distribution across {len(d)} feasible DOE designs "
                            f"(paired gains over the water-only tank; dashed = no gain)")
    _save(fig, "phase5_outcome_distribution", width=1250)


# --------------------------------------------------------------------------------------------------------------------
# PHASE 6 - surrogate
# --------------------------------------------------------------------------------------------------------------------

def _oof():
    """Out-of-fold predictions of each pair's SELECTED surrogate family (same 5-fold split as scripts/g8_s3_compare.py)."""
    def build():
        from sklearn.model_selection import KFold
        from src.optimize.surrogates import FAMILIES, TARGETS, feature_matrix
        sel = _csv("g8_s3_selection.csv").set_index("pair").chosen
        rows = []
        for f in sorted(RD.glob("g8_s2_r*_p*.csv")):
            pair = f.stem.replace("g8_s2_", "")
            df = pd.read_csv(f)
            ok = df[(df.status == "ok") & df.valid.astype(bool)].reset_index(drop=True)
            X, Y = feature_matrix(ok), ok[list(TARGETS)].to_numpy(float)
            pred = np.zeros_like(Y)
            for tr, te in KFold(5, shuffle=True, random_state=7).split(X):
                pred[te] = FAMILIES[sel[pair]]().fit(X[tr], Y[tr]).predict(X[te])
            for j, t in enumerate(TARGETS):
                rows.append(pd.DataFrame({"pair": pair, "regime": int(pair[1]), "family": sel[pair], "target": t,
                                          "sim": Y[:, j], "pred": pred[:, j]}))
        return pd.concat(rows, ignore_index=True)
    return _cached(DATA / "surrogate_oof.csv", build)


def phase6_parity_plots():
    from scipy.stats import spearmanr
    o = _oof()
    targets = ("g_window", "g_annual", "d_overheat", "t_pcm_max")
    units = {"g_window": "kWh/yr", "g_annual": "kWh/yr", "d_overheat": "h/yr", "t_pcm_max": "C"}
    fig = make_subplots(rows=2, cols=2, subplot_titles=targets, vertical_spacing=0.14)
    for i, t in enumerate(targets):
        r, c = divmod(i, 2)
        d = o[o.target == t]
        for rg in REGIMES:
            g = d[d.regime == rg]
            fig.add_trace(go.Scatter(x=g.sim, y=g.pred, mode="markers", name=f"regime {rg}", legendgroup=str(rg), showlegend=i == 0,
                                     marker=dict(size=5, color=REGIME_COL[rg], opacity=0.7), text=g.pair + " " + g.family,
                                     hovertemplate="%{text}<br>simulated %{x:.3f}<br>predicted %{y:.3f}<extra></extra>"), row=r + 1, col=c + 1)
        lo, hi = float(min(d.sim.min(), d.pred.min())), float(max(d.sim.max(), d.pred.max()))
        fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines", line=dict(color="black", dash="dash"), showlegend=False),
                      row=r + 1, col=c + 1)
        within = np.nanmean([spearmanr(g.sim, g.pred)[0] for _, g in d.groupby("pair") if g.sim.nunique() > 1])
        fig.add_annotation(text=f"within-pair Spearman {within:.3f}", xref=f"x{i + 1} domain" if i else "x domain",
                           yref=f"y{i + 1} domain" if i else "y domain", x=0.03, y=0.96, showarrow=False, font=dict(size=11))
        fig.update_xaxes(title_text=f"simulated ({units[t]})", row=r + 1, col=c + 1)
        fig.update_yaxes(title_text=f"predicted ({units[t]})", row=r + 1, col=c + 1)
    fig.update_layout(title="Phase 6 - surrogate parity, 5-fold out-of-fold predictions<br><sup>selected model per pair "
                            "(XGBoost or quadratic RSM); global R2 mostly measures regime offsets, so the within-pair rank "
                            "agreement is what the selection used</sup>")
    _save(fig, "phase6_parity_plots", width=1100, height=820)


def phase6_feature_importance():
    frames = [pd.read_csv(f).assign(pair=f.stem.replace("g8_s1_anova_", "")) for f in sorted(RD.glob("g8_s1_anova_r*_p*.csv"))]
    a = pd.concat(frames, ignore_index=True)
    m = a.groupby(["factor", "response"]).contribution_pct.agg(["mean", "min", "max"]).reset_index()
    fig = go.Figure()
    for resp, col in zip(("g_window", "g_annual", "d_overheat", "t_pcm_max"), ("#1f77b4", "#ff7f0e", "#d62728", "#9467bd")):
        d = m[m.response == resp]
        fig.add_trace(go.Bar(x=d.factor, y=d["mean"], name=resp, marker_color=col,
                             error_y=dict(type="data", symmetric=False, array=d["max"] - d["mean"], arrayminus=d["mean"] - d["min"])))
    fig.update_layout(barmode="group", title="Phase 6 - ANOVA contribution of each design variable (screening runs, "
                                             "mean and range over the 9 regime-PCM pairs)",
                      xaxis_title="design variable", yaxis_title="contribution to variance (%)")
    _save(fig, "phase6_feature_importance")


# --------------------------------------------------------------------------------------------------------------------
# PHASE 7 - optimisation
# --------------------------------------------------------------------------------------------------------------------

def _points(pair):
    fs = sorted(RD.glob(f"g9_points_{pair}*.csv"))
    d = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
    return d.drop_duplicates(subset=["R_in_m", "fraction", "flow", "arrangement", "N"])


def phase7_pareto_by_regime():
    fig = make_subplots(rows=1, cols=3, subplot_titles=[f"Regime {r}: {_clean(_chosen(r)['pcm'])[:24]}" for r in REGIMES],
                        horizontal_spacing=0.06)
    shown = set()
    for r in REGIMES:
        c = _chosen(r)
        rk = int(c["pcm_rank"])
        if rk == 1:
            g = _csv(f"g9_s6_grid_r{r}_p1.csv")
            g = g[g.status.eq("ok")] if "status" in g else g
            fig.add_trace(go.Scatter(x=g.d_overheat, y=g.g_window, mode="markers", name="dense grid (540)", legendgroup="grid",
                                     showlegend="grid" not in shown, marker=dict(size=5, color="#cccccc")), row=1, col=r + 1)
            shown.add("grid")
        p = _points(f"r{r}_p{rk}")
        p = p[p.feasible.astype(bool)]
        for a in ARRANGEMENTS:
            q = p[p.arrangement == a]
            fig.add_trace(go.Scatter(x=q.d_overheat, y=q.g_window, mode="markers", name=f"optimiser points, {a}", legendgroup=a,
                                     showlegend=a not in shown, marker=dict(size=7, color=ARR_COL[a], opacity=0.75),
                                     text=("R_in " + (q.R_in_m * 1000).round(1).astype(str) + " mm, fraction " + (q.fraction * 100).round(1).astype(str)
                                           + " %, flow " + q.flow.round(4).astype(str)),
                                     hovertemplate="%{text}<br>overheat %{x:.0f} h<br>g_window %{y:.1f}<extra></extra>"), row=1, col=r + 1)
            shown.add(a)
        fig.add_trace(go.Scatter(x=[c["d_overheat"]], y=[c["g_window"]], mode="markers", name="selected (select years)", legendgroup="sel",
                                 showlegend="sel" not in shown, marker=dict(size=16, symbol="star", color="gold",
                                                                              line=dict(color="black", width=1))), row=1, col=r + 1)
        shown.add("sel")
        fig.update_xaxes(title_text="extra overheating hours vs water-only (h/yr)", row=1, col=r + 1)
    fig.update_yaxes(title_text="g_window gain (kWh/yr)", row=1, col=1)
    fig.update_layout(title="Phase 7 - trade-off between night-window gain and overheating, by regime "
                            "(explore years; star = selected on the select years)")
    _save(fig, "phase7_pareto_by_regime", width=1350)


def phase7_surrogate_vs_simulator():
    fig = make_subplots(rows=1, cols=2, subplot_titles=("mean |error| of g_annual (kWh/yr)", "mean |error| of peak PCM temperature (C)"))
    shown = set()
    for r in REGIMES:
        for rk in (1, 2, 3):
            fs = sorted(RD.glob(f"g9_al_log_r{r}_p{rk}*.csv"))
            if not fs:
                continue
            # the _ext / _ext2 logs repeat every earlier round, so the longest file already holds the whole history
            d = max((pd.read_csv(f) for f in fs), key=len)
            d = d[d.mean_abs_err_g_annual.notna()].sort_values("n_train")
            nm = f"r{r}_p{rk}"
            for c, col in ((1, "mean_abs_err_g_annual"), (2, "mean_abs_err_tpcm")):
                fig.add_trace(go.Scatter(x=d.n_train, y=d[col], mode="lines+markers", name=nm, legendgroup=nm, showlegend=nm not in shown,
                                         line=dict(color=REGIME_COL[r], dash=("solid", "dash", "dot")[rk - 1])), row=1, col=c)
                shown.add(nm)
    fig.update_xaxes(title_text="training designs after the round (active learning adds about 10 per round)")
    fig.update_layout(title="Phase 7 - surrogate error against the simulator during active learning"
                            "<br><sup>solid / dashed / dotted = O1 rank 1 / 2 / 3; error measured on the designs added in each round</sup>")
    _save(fig, "phase7_surrogate_vs_simulator", width=1200)


def phase7_safety_compliance():
    pts = []
    for r in REGIMES:
        for rk in (1, 2, 3):
            if sorted(RD.glob(f"g9_points_r{r}_p{rk}*.csv")):
                pts.append(_points(f"r{r}_p{rk}").assign(regime=r))
    p = pd.concat(pts, ignore_index=True)
    fig = go.Figure()
    for r in REGIMES:
        d = p[p.regime == r]
        share = 100 * d.feasible.astype(bool).mean()
        fig.add_trace(go.Histogram(x=d.t_pcm_max, name=f"regime {r} ({share:.0f} % feasible, n={len(d)})", opacity=0.6,
                                   marker_color=REGIME_COL[r], xbins=dict(size=0.5)))
    fig.add_vline(x=65, line_dash="dash", line_color="red", annotation_text="65 C material limit (infeasible above)")
    fig.add_vline(x=62, line_dash="dot", line_color="orange", annotation_text="62 C shield bypass", annotation_position="bottom left")
    fig.update_layout(barmode="overlay", title="Phase 7 - peak PCM temperature of every simulated optimiser design"
                                               "<br><sup>maximum over the explore years</sup>", xaxis_title="peak PCM temperature (C)",
                      yaxis_title="designs")
    _save(fig, "phase7_safety_compliance")


# --------------------------------------------------------------------------------------------------------------------
# PHASE 8 - robustness (weather years replace the Monte Carlo of the legacy chain)
# --------------------------------------------------------------------------------------------------------------------

def _eval_one(regime, purpose):
    from src.optimize.evaluate import evaluate_design
    c = _chosen(regime)
    res = evaluate_design(regime, c["pcm"], c["R_in_m"], c["fraction"], c["flow"], c["arrangement"], purpose=purpose)
    if res["N"] != c["N"]:
        raise RuntimeError(f"regime {regime}: re-derived N={res['N']} differs from the selected N={c['N']}")
    return [{"regime": regime, "year": y["year"], "role": purpose, "g_window": y["g_window"], "g_annual": y["g_annual"],
             "d_overheat": y["d_overheat"], "t_pcm_max": y["t_pcm_max"]} for y in res["per_year"]]


def _by_year():
    """The chosen design of each regime on every weather year: explore + select simulated (cached), held-out read from g10."""
    def build():
        from joblib import Parallel, delayed
        jobs = [(r, p) for r in REGIMES for p in ("explore", "select")]
        print(f"  chosen designs on 8 weather years x 3 regimes ({len(jobs)} jobs, about 8 min on one core)", flush=True)
        out = Parallel(n_jobs=min(JOBS, len(jobs)))(delayed(_eval_one)(r, p) for r, p in jobs)
        return pd.DataFrame([row for sub in out for row in sub])
    d = _cached(DATA / "chosen_by_year.csv", build)
    h = _csv("g10_heldout_results.csv")
    h = h[h.role == "chosen"][["regime", "year", "g_window", "g_annual", "d_overheat", "t_pcm_max"]].assign(role="held-out")
    return pd.concat([d, h], ignore_index=True).sort_values(["regime", "year"]).reset_index(drop=True)


def phase8_robustness_probabilities():
    y = _by_year()
    fig = go.Figure()
    tests = (("gain above the repeatability band", lambda g, b: (g.g_window > b)),
             ("window gain > 0", lambda g, b: (g.g_window > 0)),
             ("PCM peak <= 65 C", lambda g, b: (g.t_pcm_max <= 65)),
             ("no extra overheating vs water-only", lambda g, b: (g.d_overheat <= 0)))
    for name, fn in tests:
        v = [float(fn(y[y.regime == r], _band(r)).mean()) for r in REGIMES]
        fig.add_trace(go.Bar(x=[f"Regime {r}<br>{_clean(_chosen(r)['pcm'])[:22]}" for r in REGIMES], y=v, name=name,
                             text=[f"{x:.2f}" for x in v], textposition="outside"))
    n = int(y.groupby("regime").size().iloc[0])
    fig.update_layout(barmode="group", yaxis=dict(range=[0, 1.15], title="share of weather years"),
                      title=f"Phase 8 - robustness of the chosen design over {n} weather years "
                            f"(explore + select + held-out)<br><sup>replaces the legacy Monte Carlo: {n} real years, "
                            f"so probabilities are in steps of {1 / n:.1f}</sup>")
    _save(fig, "phase8_robustness_probabilities")


def phase8_useful_energy_intervals():
    y = _by_year()
    fig = go.Figure()
    shown = set()
    for r in REGIMES:
        d = y[y.regime == r]
        x0 = r * 1.0
        fig.add_trace(go.Scatter(x=[x0, x0], y=[d.g_window.min(), d.g_window.max()], mode="lines", line=dict(color="black", width=3),
                                 showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=[x0 - 0.25, x0 + 0.25], y=[d.g_window.mean()] * 2, mode="lines", line=dict(color="black", width=2),
                                 name="10-year mean" if "mean" not in shown else None, showlegend="mean" not in shown, legendgroup="mean"))
        shown.add("mean")
        for role in ("explore", "select", "held-out"):
            q = d[d.role == role]
            fig.add_trace(go.Scatter(x=x0 + (np.arange(len(q)) - (len(q) - 1) / 2) * 0.07, y=q.g_window, mode="markers", name=role,
                                     legendgroup=role, showlegend=role not in shown, marker=dict(size=10, color=ROLE_COL[role]),
                                     text=q.year.astype(str), hovertemplate="year %{text}<br>g_window %{y:.1f} kWh<extra></extra>"))
            shown.add(role)
        fig.add_shape(type="line", x0=x0 - 0.35, x1=x0 + 0.35, y0=_band(r), y1=_band(r), line=dict(color="#27ae60", dash="dash"))
    fig.add_annotation(text="green dashes = repeatability band (a gain below it is indistinguishable from zero)", xref="paper",
                       yref="paper", x=0.01, y=1.02, showarrow=False, font=dict(size=11, color="#27ae60"))
    fig.update_layout(title="Phase 8 - night-window gain of the chosen design, every weather year",
                      xaxis=dict(tickvals=list(REGIMES), ticktext=[f"Regime {r}<br>{_clean(_chosen(r)['pcm'])[:22]}" for r in REGIMES]),
                      yaxis_title="g_window gain over water-only (kWh/yr)")
    _save(fig, "phase8_useful_energy_intervals")


# --------------------------------------------------------------------------------------------------------------------

FIGURES = {
    "phase2_validity_map": phase2_validity_map, "phase2_ergun_hydraulics": phase2_ergun_hydraulics,
    "phase3_temperature_timeseries": phase3_temperature_timeseries, "phase3_melt_fraction_year": phase3_melt_fraction_year,
    "phase3_energy_breakdown": phase3_energy_breakdown,
    "phase4_gate1_residuals": phase4_gate1_residuals, "phase4_gate3_baseline_comparison": phase4_gate3_baseline_comparison,
    "phase4_gate5_sensitivity": phase4_gate5_sensitivity,
    "phase5_doe_coverage": phase5_doe_coverage, "phase5_outcome_distribution": phase5_outcome_distribution,
    "phase6_parity_plots": phase6_parity_plots, "phase6_feature_importance": phase6_feature_importance,
    "phase7_pareto_by_regime": phase7_pareto_by_regime, "phase7_surrogate_vs_simulator": phase7_surrogate_vs_simulator,
    "phase7_safety_compliance": phase7_safety_compliance,
    "phase8_robustness_probabilities": phase8_robustness_probabilities, "phase8_useful_energy_intervals": phase8_useful_energy_intervals,
}
JOBS = 3


def main(argv=None):
    global REFRESH, JOBS
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="rebuild the cached simulation data under results/plots_data/")
    ap.add_argument("--only", default="", help="comma-separated figure names")
    ap.add_argument("--jobs", type=int, default=3)
    a = ap.parse_args(argv)
    REFRESH, JOBS = a.refresh, a.jobs
    names = [n for n in a.only.split(",") if n] or list(FIGURES)
    unknown = [n for n in names if n not in FIGURES]
    if unknown:
        sys.exit(f"unknown figure(s): {unknown}")
    print(f"Generating {len(names)} rework phase figures -> {OUT}", flush=True)
    for n in names:
        FIGURES[n]()


if __name__ == "__main__":
    main()
