"""
src/plots/make_plots.py
==========================
Generates the justification plots for Phases 2-7, one function per figure.
Every figure is built once in Plotly and saved TWICE:
  results/<state>/plots/interactive/<name>.html   -- self-contained (all JS
                                                       inlined), fully
                                                       interactive (zoom,
                                                       pan, hover tooltips
                                                       with exact values),
                                                       opens in any browser
                                                       with no server and
                                                       no internet needed.
  results/<state>/plots/static/<name>.png          -- same figure, flat
                                                       image, for reports/
                                                       slides/viva printouts.

Nothing here re-derives results — every figure either reads a file already
written by Phases 2-7 (design_cases.parquet, optimized_designs.csv, the
trained surrogate) or re-runs a specific, already-verified case through
run_case() to get a time series that isn't persisted by default (Phase 3).

Run: python -m src.plots.make_plots uttarakhand
"""

import json
import pickle
import sys

import numpy as np
import pandas as pd
# pyrefly: ignore [missing-import]
import plotly.graph_objects as go
# pyrefly: ignore [missing-import]
from plotly.subplots import make_subplots

from config import BASE_DIR, RESULTS_DIR
from src.design.schema import DesignVector
from src.design.constraints import check_design
from src.design.geometry import compute_hydraulics
from src.io_utils import load_system_config, load_design_bounds, get_pcm_properties, get_regime
from src.simulation.run_case import run_case
from src.surrogate.features import build_feature_table, feature_target_split

TEMPLATE = "plotly_white"


def _save(fig: go.Figure, name: str, out_dir, width=1000, height=620):
    static_dir = out_dir / "static"
    interactive_dir = out_dir / "interactive"
    static_dir.mkdir(parents=True, exist_ok=True)
    interactive_dir.mkdir(parents=True, exist_ok=True)
    fig.update_layout(template=TEMPLATE, width=width, height=height)
    fig.write_image(str(static_dir / f"{name}.png"), scale=2)
    fig.write_html(str(interactive_dir / f"{name}.html"), include_plotlyjs="inline")
    print(f"  [OK] {name}")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 2 — geometry & constraints
# ═══════════════════════════════════════════════════════════════════════

def phase2_validity_map(state, out_dir):
    bounds = load_design_bounds()
    system_config = load_system_config()
    d_bounds, n_bounds, f_bounds = bounds["capsule_diameter_m"], bounds["capsule_count"], bounds["flow_rate_kg_s"]
    diam_grid = np.linspace(d_bounds["min"], d_bounds["max"], 61)
    count_grid = np.arange(n_bounds["min"], n_bounds["max"] + 1)
    mid_flow = (f_bounds["min"] + f_bounds["max"]) / 2

    rows = []
    for d in diam_grid:
        for n in count_grid:
            g = check_design(DesignVector(float(d), int(n), mid_flow), system_config, bounds)
            rows.append({"diameter": d, "count": n, "reason": g["reason"] if not g["valid"] else "valid"})
    df = pd.DataFrame(rows)

    colors = {"valid": "#2ca02c", "bounds_violation": "#d62728", "overlap": "#9467bd",
              "volume_exceeded": "#ff7f0e", "passage_blocked": "#8c564b", "pressure_drop_limit": "#e377c2"}
    fig = go.Figure()
    for reason, group in df.groupby("reason"):
        fig.add_trace(go.Scatter(
            x=group["diameter"], y=group["count"], mode="markers",
            marker=dict(size=7, symbol="square", color=colors.get(reason, "#7f7f7f")),
            name=reason, hovertemplate="diameter=%{x:.4f} m<br>count=%{y}<br>" + reason + "<extra></extra>",
        ))
    fig.update_layout(
        title=f"Phase 2 — Design-space validity map (flow fixed at {mid_flow:.3f} kg/s) — {state}",
        xaxis_title="capsule_diameter_m", yaxis_title="n_capsule",
    )
    fig.add_vline(x=0.04, line_dash="dash", line_color="black",
                  annotation_text="diameter=0.04 m (thickness bound edge)", annotation_position="top")
    _save(fig, "phase2_validity_map", out_dir)


def phase2_ergun_hydraulics(state, out_dir):
    system_config = load_system_config()
    flows = np.linspace(0.002, 0.10, 60)
    fig = go.Figure()
    for diam in (0.02, 0.04, 0.06, 0.08):
        dp = [compute_hydraulics(f, diam, void_fraction=0.90, cross_section_area_m2=0.0789,
                                  bed_length_m=0.10, system_config=system_config)["pressure_drop_pa"]
              for f in flows]
        fig.add_trace(go.Scatter(x=flows, y=dp, mode="lines", name=f"diameter={diam} m"))
    bounds = load_design_bounds()
    fig.add_vrect(x0=bounds["flow_rate_kg_s"]["min"], x1=bounds["flow_rate_kg_s"]["max"],
                  fillcolor="green", opacity=0.08, line_width=0, annotation_text="permitted flow range")
    fig.update_layout(
        title=f"Phase 2 — Ergun-equation pressure drop vs flow rate — {state}",
        xaxis_title="flow_rate_kg_s", yaxis_title="pressure_drop_pa (void=0.90, bed length=0.10 m)",
    )
    _save(fig, "phase2_ergun_hydraulics", out_dir)


# ═══════════════════════════════════════════════════════════════════════
# PHASE 3 — grey-box simulator
# ═══════════════════════════════════════════════════════════════════════

def _phase3_sample_run(state):
    pcm = get_regime(state, 0)["pcm_shortlist"][0]
    design = DesignVector(0.08, 19, 0.030)
    out = run_case(state, cluster_id=0, pcm_name=pcm, design=design, record_hourly=True)
    return out["hourly"], out["metrics"], pcm


def phase3_temperature_timeseries(state, out_dir, hourly, pcm):
    week = hourly.iloc[2400:2568]   # one representative week (~day 100-107)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=week["hour_index"], y=week["T_w_C"], name="T_water (C)",
                              line=dict(color="#1f77b4")), secondary_y=False)
    fig.add_trace(go.Scatter(x=week["hour_index"], y=week["T_pcm_C"], name="T_PCM (C)",
                              line=dict(color="#d62728")), secondary_y=False)
    fig.add_trace(go.Scatter(x=week["hour_index"], y=week["I_t_Wm2"], name="Irradiance (W/m2)",
                              line=dict(color="#ff7f0e", dash="dot")), secondary_y=True)
    fig.update_layout(title=f"Phase 3 — one representative week: T_water, T_PCM, irradiance — {state}, "
                             f"cluster 0, {pcm}",
                       xaxis_title="hour of year")
    fig.update_yaxes(title_text="Temperature (C)", secondary_y=False)
    fig.update_yaxes(title_text="Irradiance (W/m2)", secondary_y=True)
    _save(fig, "phase3_temperature_timeseries", out_dir)


def phase3_melt_fraction_year(state, out_dir, hourly, pcm):
    fig = go.Figure(go.Scatter(x=hourly["hour_index"], y=hourly["f_melt"], mode="lines",
                                line=dict(color="#2ca02c", width=1)))
    fig.update_layout(title=f"Phase 3 — PCM liquid fraction over the simulated year — {state}, "
                             f"cluster 0, {pcm}",
                       xaxis_title="hour of year", yaxis_title="liquid fraction f_melt [0-1]")
    _save(fig, "phase3_melt_fraction_year", out_dir)


def phase3_energy_breakdown(state, out_dir, metrics):
    labels = ["Collector input", "Delivered to load", "Tank/pipe loss", "Unmet (shortfall)"]
    values = [metrics["collector_energy_kWh"], metrics["useful_energy_kWh"],
              metrics["loss_energy_kWh"], metrics["unmet_energy_kWh"]]
    fig = go.Figure(go.Bar(x=labels, y=values, marker_color=["#1f77b4", "#2ca02c", "#d62728", "#7f7f7f"],
                            text=[f"{v:,.0f}" for v in values], textposition="outside"))
    fig.update_layout(title=f"Phase 3 — annual energy breakdown (sample case) — {state}",
                       yaxis_title="kWh / year")
    _save(fig, "phase3_energy_breakdown", out_dir)


# ═══════════════════════════════════════════════════════════════════════
# PHASE 4 — verification gates
# ═══════════════════════════════════════════════════════════════════════

def phase4_gate1_residuals(state, out_dir):
    cases = [
        ("A: cluster0/n-Octacosane", 0, "n-Octacosane (C28)", DesignVector(0.05, 14, 0.030)),
        ("B: cluster1/RT64HC", 1, "RT64HC", DesignVector(0.04, 20, 0.020)),
        ("C: cluster4/n-Hexacosane", 4, "n-Hexacosane (C26)", DesignVector(0.08, 10, 0.045)),
        ("D: cluster2/no-PCM", 2, None, DesignVector(0.05, 14, 0.030)),
        ("E: cluster3/bounds-extreme", 3, "n-Octacosane (C28)", DesignVector(0.08, 24, 0.050)),
    ]
    names, residuals = [], []
    for name, cid, pcm, design in cases:
        out = run_case(state, cid, pcm, design, record_hourly=False)
        names.append(name)
        residuals.append(out["metrics"]["residual_pct_of_collector"])

    fig = go.Figure(go.Bar(x=names, y=residuals, marker_color="#1f77b4",
                            text=[f"{r:.2e}%" for r in residuals], textposition="outside"))
    fig.add_hline(y=0.1, line_dash="dash", line_color="orange", annotation_text="0.1% pass threshold")
    fig.add_hline(y=0.5, line_dash="dash", line_color="red", annotation_text="0.5% warn/stop threshold")
    fig.update_layout(title=f"Phase 4 Gate 1 — energy-conservation residual, 5 diverse cases — {state}",
                       yaxis_title="residual (% of collector energy)", yaxis_type="log")
    _save(fig, "phase4_gate1_residuals", out_dir)


def phase4_gate3_baseline_comparison(state, out_dir):
    cid = 0
    pcm = get_regime(state, cid)["pcm_shortlist"][0]
    plain = run_case(state, cid, None, DesignVector(0.08, 14, 0.030), record_hourly=False)["metrics"]
    fixed = run_case(state, cid, pcm, DesignVector(0.08, 24, 0.030), record_hourly=False)["metrics"]
    optimized = run_case(state, cid, pcm, DesignVector(0.08, 19, 0.040), record_hourly=False)["metrics"]
    matched = run_case(state, cid, pcm, DesignVector(0.08, 24, 0.030), record_hourly=False,
                        pcm_record_overrides={"Tm_C": 40.0})["metrics"]

    labels = ["Plain tank", f"Fixed PCM\n({pcm}, 12.9%)", "Optimized-looking\n(10.2%)",
              "Capability check\n(synthetic Tm=40C PCM)"]
    sf = [m["solar_fraction"] * 100 for m in (plain, fixed, optimized, matched)]
    fig = go.Figure(go.Bar(x=labels, y=sf, marker_color=["#7f7f7f", "#d62728", "#ff7f0e", "#2ca02c"],
                            text=[f"{v:.2f}%" for v in sf], textposition="outside"))
    fig.update_layout(title=f"Phase 4 Gate 3 — solar fraction: plain tank vs PCM designs — {state}",
                       yaxis_title="solar fraction (%)")
    _save(fig, "phase4_gate3_baseline_comparison", out_dir)


def phase4_gate5_sensitivity(state, out_dir):
    cid = 0
    pcm = get_regime(state, cid)["pcm_shortlist"][0]
    design = DesignVector(0.05, 18, 0.040)
    record = get_pcm_properties(state, pcm)

    base = run_case(state, cid, pcm, design, record_hourly=False)["metrics"]
    plus_l = run_case(state, cid, pcm, design, record_hourly=False,
                       pcm_record_overrides={"latent_heat_kJ_kg": record["latent_heat_kJ_kg"] * 1.10})["metrics"]
    minus_l = run_case(state, cid, pcm, design, record_hourly=False,
                        pcm_record_overrides={"latent_heat_kJ_kg": record["latent_heat_kJ_kg"] * 0.90})["metrics"]
    hi_flow = run_case(state, cid, pcm, DesignVector(0.05, 18, min(design.flow_rate_kg_s * 1.5, 0.05)),
                        record_hourly=False)["metrics"]
    lo_flow = run_case(state, cid, pcm, DesignVector(0.05, 18, design.flow_rate_kg_s * 0.5),
                        record_hourly=False)["metrics"]

    fig = make_subplots(rows=1, cols=2, subplot_titles=("PCM charge energy vs latent heat +/-10%",
                                                          "Pump energy vs flow +/-50%"))
    fig.add_trace(go.Bar(x=["-10%", "baseline", "+10%"],
                          y=[minus_l["charge_energy_kWh"], base["charge_energy_kWh"], plus_l["charge_energy_kWh"]],
                          marker_color="#1f77b4", showlegend=False), row=1, col=1)
    fig.add_trace(go.Bar(x=["-50%", "baseline", "+50%"],
                          y=[lo_flow["pump_energy_kWh"], base["pump_energy_kWh"], hi_flow["pump_energy_kWh"]],
                          marker_color="#2ca02c", showlegend=False), row=1, col=2)
    fig.update_layout(title=f"Phase 4 Gate 5 — sensitivity/monotonicity spot checks — {state}")
    fig.update_yaxes(title_text="charge_energy_kWh", row=1, col=1)
    fig.update_yaxes(title_text="pump_energy_kWh", row=1, col=2)
    _save(fig, "phase4_gate5_sensitivity", out_dir, width=1150)


# ═══════════════════════════════════════════════════════════════════════
# PHASE 5 — DOE
# ═══════════════════════════════════════════════════════════════════════

def phase5_doe_coverage(state, out_dir, design_cases):
    fig = go.Figure()
    for valid, group in design_cases.groupby("valid"):
        fig.add_trace(go.Scatter(
            x=group["capsule_diameter_m"], y=group["flow_rate_kg_s"], mode="markers",
            marker=dict(size=7, color="#2ca02c" if valid else "#d62728",
                        symbol=group["sampling_method"].map({"lhs": "circle", "boundary": "diamond",
                                                              "baseline": "star"})),
            name="valid" if valid else "rejected (bounds_violation)",
            text=group["case_id"], hovertemplate="%{text}<br>diameter=%{x:.4f}<br>flow=%{y:.4f}<extra></extra>",
        ))
    fig.update_layout(title=f"Phase 5 — DOE sample coverage (215 cases: LHS + boundary + baseline) — {state}",
                       xaxis_title="capsule_diameter_m", yaxis_title="flow_rate_kg_s")
    _save(fig, "phase5_doe_coverage", out_dir)


def phase5_outcome_distribution(state, out_dir, design_cases):
    valid = design_cases[design_cases["valid"]]
    fig = make_subplots(rows=1, cols=2, subplot_titles=("useful_energy_kWh", "solar_fraction"))
    fig.add_trace(go.Histogram(x=valid["useful_energy_kWh"], marker_color="#1f77b4", showlegend=False),
                  row=1, col=1)
    fig.add_trace(go.Histogram(x=valid["solar_fraction"], marker_color="#ff7f0e", showlegend=False),
                  row=1, col=2)
    fig.update_layout(title=f"Phase 5 — outcome distribution across 145 valid DOE cases — {state}")
    _save(fig, "phase5_outcome_distribution", out_dir, width=1150)


# ═══════════════════════════════════════════════════════════════════════
# PHASE 6 — surrogate
# ═══════════════════════════════════════════════════════════════════════

def phase6_parity_plots(state, out_dir, design_cases):
    feat_df = build_feature_table(state, design_cases)
    hold = feat_df[feat_df["split"] == "holdout"]
    with open(RESULTS_DIR / state / "surrogate" / "models.pkl", "rb") as f:
        saved = pickle.load(f)
    models, feature_cols = saved["models"], saved["feature_cols"]

    X_hold, y_hold_dict, _, _ = feature_target_split(hold, only_valid=True)

    fig = make_subplots(rows=1, cols=2, subplot_titles=("useful_energy_kWh", "solar_fraction"))
    for col, target in enumerate(["useful_energy_kWh", "solar_fraction"], start=1):
        y_true = y_hold_dict[target]
        y_pred = models[target].predict(X_hold)
        lo, hi = min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())
        fig.add_trace(go.Scatter(x=y_true, y=y_pred, mode="markers", marker=dict(color="#1f77b4"),
                                  showlegend=False), row=1, col=col)
        fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines",
                                  line=dict(color="gray", dash="dash"), showlegend=False), row=1, col=col)
        fig.update_xaxes(title_text=f"simulator {target}", row=1, col=col)
        fig.update_yaxes(title_text=f"surrogate predicted {target}", row=1, col=col)
    fig.update_layout(title=f"Phase 6 — surrogate parity plots (hold-out set, n={len(X_hold)}) — {state}")
    _save(fig, "phase6_parity_plots", out_dir, width=1150)


def phase6_feature_importance(state, out_dir):
    with open(RESULTS_DIR / state / "surrogate" / "models.pkl", "rb") as f:
        saved = pickle.load(f)
    models, feature_cols = saved["models"], saved["feature_cols"]
    importances = models["useful_energy_kWh"].feature_importances_
    order = np.argsort(importances)[-15:]
    fig = go.Figure(go.Bar(x=importances[order], y=[feature_cols[i] for i in order], orientation="h",
                            marker_color="#1f77b4"))
    fig.update_layout(title=f"Phase 6 — top-15 feature importances (useful_energy_kWh model) — {state}",
                       xaxis_title="ExtraTrees feature importance")
    _save(fig, "phase6_feature_importance", out_dir, height=560)


# ═══════════════════════════════════════════════════════════════════════
# PHASE 7 — optimization
# ═══════════════════════════════════════════════════════════════════════

def phase7_pareto_by_regime(state, out_dir, optimized, deployable):
    fig = make_subplots(rows=2, cols=3, subplot_titles=[f"Regime {r}" for r in sorted(optimized["regime_id"].unique())])
    positions = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2)]
    for (row, col), (regime_id, group) in zip(positions, optimized.groupby("regime_id")):
        for pcm_id, sub in group.groupby("pcm_id"):
            fig.add_trace(go.Scatter(x=sub["sim_pcm_mass_kg"], y=sub["sim_useful_energy_kWh"], mode="markers",
                                      name=pcm_id, legendgroup=pcm_id,
                                      showlegend=(row, col) == (1, 1)), row=row, col=col)
        winner = deployable[deployable["regime_id"] == regime_id]
        if not winner.empty:
            fig.add_trace(go.Scatter(x=winner["sim_pcm_mass_kg"], y=winner["sim_useful_energy_kWh"],
                                      mode="markers", marker=dict(size=16, symbol="star", color="black"),
                                      name="selected", legendgroup="selected", showlegend=(row, col) == (1, 1)),
                          row=row, col=col)
    fig.update_layout(title=f"Phase 7 — useful energy vs PCM mass, all 100 confirmed candidates — {state}",
                       height=760, width=1200)
    fig.update_xaxes(title_text="PCM mass (kg)")
    fig.update_yaxes(title_text="useful energy (kWh)")
    _save(fig, "phase7_pareto_by_regime", out_dir, width=1200, height=760)


def phase7_surrogate_vs_simulator(state, out_dir, optimized):
    lo = min(optimized["pred_useful_energy_kWh"].min(), optimized["sim_useful_energy_kWh"].min())
    hi = max(optimized["pred_useful_energy_kWh"].max(), optimized["sim_useful_energy_kWh"].max())
    mean_err = optimized["surrogate_vs_sim_error_pct"].mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=optimized["sim_useful_energy_kWh"], y=optimized["pred_useful_energy_kWh"],
                              mode="markers", marker=dict(color="#1f77b4"),
                              text=optimized["pcm_id"], hovertemplate="%{text}<extra></extra>", name="candidates"))
    fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines", line=dict(color="gray", dash="dash"),
                              name="perfect agreement"))
    fig.update_layout(title=f"Phase 7 — surrogate-predicted vs simulator-confirmed useful energy "
                             f"(100 candidates, mean error {mean_err:.2f}%) — {state}",
                       xaxis_title="simulator useful_energy_kWh", yaxis_title="surrogate-predicted useful_energy_kWh")
    _save(fig, "phase7_surrogate_vs_simulator", out_dir)


def phase8_robustness_probabilities(state, out_dir, robustness_summary):
    labels = [f"Regime {r} ({p})" for r, p in zip(robustness_summary["regime_id"], robustness_summary["pcm_id"])]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=robustness_summary["p_meets_delivery_temp"] * 100,
                          name="P(meets delivery temp, SF>=45%)", marker_color="#9467bd"))
    fig.add_trace(go.Bar(x=labels, y=robustness_summary["p_meets_annual_demand"] * 100,
                          name="P(meets annual demand, SF>=50%)", marker_color="#1f77b4"))
    fig.add_trace(go.Bar(x=labels, y=(1 - robustness_summary["p_temperature_violation"]) * 100,
                          name="P(temperature-safe)", marker_color="#2ca02c"))
    fig.add_hline(y=75, line_dash="dash", line_color="#1f77b4", annotation_text="75% demand threshold")
    fig.add_hline(y=95, line_dash="dash", line_color="#2ca02c", annotation_text="95% safety threshold")
    fig.update_layout(barmode="group", title=f"Phase 8 — robustness probabilities (120 Monte Carlo draws/design) — {state}",
                       yaxis_title="probability (%)")
    _save(fig, "phase8_robustness_probabilities", out_dir, width=1150)


def phase8_useful_energy_intervals(state, out_dir, robustness_summary, deployable):
    fig = go.Figure()
    for _, row in robustness_summary.iterrows():
        nominal = deployable.loc[deployable["regime_id"] == row["regime_id"], "sim_useful_energy_kWh"]
        nominal = float(nominal.iloc[0]) if len(nominal) else None
        is_first = bool(row["regime_id"] == robustness_summary["regime_id"].iloc[0])
        fig.add_trace(go.Scatter(
            x=[row["useful_energy_p05_kWh"], row["useful_energy_p95_kWh"]],
            y=[f"Regime {row['regime_id']}"] * 2, mode="lines+markers",
            line=dict(color="#1f77b4", width=4), marker=dict(size=9), showlegend=False,
        ))
        fig.add_trace(go.Scatter(x=[row["useful_energy_p50_kWh"]], y=[f"Regime {row['regime_id']}"],
                                  mode="markers", marker=dict(size=11, symbol="circle", color="#1f77b4",
                                                               line=dict(color="white", width=1)),
                                  name="median (P50)", showlegend=is_first))
        if nominal is not None:
            fig.add_trace(go.Scatter(x=[nominal], y=[f"Regime {row['regime_id']}"], mode="markers",
                                      marker=dict(size=12, symbol="diamond", color="black"),
                                      name="nominal (unperturbed)", showlegend=is_first))
    fig.update_layout(title=f"Phase 8 — useful-energy 5th-50th-95th percentile interval per regime — {state}",
                       xaxis_title="useful_energy_kWh")
    _save(fig, "phase8_useful_energy_intervals", out_dir)


def phase6b_multifidelity(state, out_dir, speedup_report, efficiency_df):
    fig = make_subplots(rows=1, cols=2, subplot_titles=(
        "Total simulator runtime: high- vs low-fidelity (215 cases)",
        "Hold-out R2 vs high-fidelity training fraction (useful_energy_kWh)"))

    fig.add_trace(go.Bar(
        x=["High fidelity\n(Phase 5, adaptive sub-stepping)", "Low fidelity\n(fixed dt, no sub-stepping)"],
        y=[speedup_report["high_fidelity_total_runtime_s"], speedup_report["low_fidelity_total_runtime_s"]],
        marker_color=["#1f77b4", "#ff7f0e"],
        text=[f"{speedup_report['high_fidelity_total_runtime_s']:.0f}s", f"{speedup_report['low_fidelity_total_runtime_s']:.0f}s"],
        textposition="outside", showlegend=False,
    ), row=1, col=1)
    fig.add_annotation(text=f"speedup: {speedup_report['speedup_x']:.1f}x", x=0.5, y=1.08,
                        xref="x domain", yref="y domain", showarrow=False, row=1, col=1)

    sub = efficiency_df[efficiency_df["target"] == "useful_energy_kWh"].sort_values("hf_training_fraction")
    for model_name, color in [("high_fidelity_only", "#7f7f7f"), ("multi_fidelity_augmented", "#2ca02c")]:
        s = sub[sub["model"] == model_name]
        fig.add_trace(go.Scatter(x=s["hf_training_fraction"] * 100, y=s["R2"], mode="lines+markers",
                                  name=model_name, line=dict(color=color)), row=1, col=2)
    fig.update_xaxes(title_text="% of Phase-5 high-fidelity training rows used", row=1, col=2)
    fig.update_yaxes(title_text="hold-out R2 (same fixed hold-out set as Phase 6)", row=1, col=2)
    fig.update_yaxes(title_text="total runtime (s)", row=1, col=1)
    fig.update_layout(title=f"Phase 6b — multi-fidelity surrogate: speedup + sample-efficiency — {state}")
    _save(fig, "phase6b_multifidelity", out_dir, width=1250)


def phase7_safety_compliance(state, out_dir, optimized):
    counts = optimized.groupby(["regime_id", "meets_temperature_safety"]).size().unstack(fill_value=0)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=counts.index, y=counts.get(True, 0), name="meets safety", marker_color="#2ca02c"))
    fig.add_trace(go.Bar(x=counts.index, y=counts.get(False, 0), name="violates safety", marker_color="#d62728"))
    fig.update_layout(barmode="stack", title=f"Phase 7 — temperature-safety compliance of confirmed candidates — {state}",
                       xaxis_title="regime_id", yaxis_title="# confirmed candidates")
    _save(fig, "phase7_safety_compliance", out_dir)


# ═══════════════════════════════════════════════════════════════════════

def main(state: str):
    out_dir = RESULTS_DIR / state / "plots"
    print(f"Generating justification plots for state={state} -> {out_dir}")

    print("Phase 2 ...")
    phase2_validity_map(state, out_dir)
    phase2_ergun_hydraulics(state, out_dir)

    print("Phase 3 ... (running one sample case)")
    hourly, metrics, pcm_sample = _phase3_sample_run(state)
    phase3_temperature_timeseries(state, out_dir, hourly, pcm_sample)
    phase3_melt_fraction_year(state, out_dir, hourly, pcm_sample)
    phase3_energy_breakdown(state, out_dir, metrics)

    print("Phase 4 ... (re-running gate cases)")
    phase4_gate1_residuals(state, out_dir)
    phase4_gate3_baseline_comparison(state, out_dir)
    phase4_gate5_sensitivity(state, out_dir)

    print("Phase 5 ...")
    design_cases = pd.read_parquet(RESULTS_DIR / state / "design_cases.parquet")
    phase5_doe_coverage(state, out_dir, design_cases)
    phase5_outcome_distribution(state, out_dir, design_cases)

    print("Phase 6 ...")
    phase6_parity_plots(state, out_dir, design_cases)
    phase6_feature_importance(state, out_dir)

    mf_report_path = RESULTS_DIR / state / "multifidelity_speedup_report.json"
    mf_efficiency_path = RESULTS_DIR / state / "multifidelity_sample_efficiency.csv"
    if mf_report_path.exists() and mf_efficiency_path.exists():
        print("Phase 6b ...")
        with open(mf_report_path, "r", encoding="utf-8") as f:
            speedup_report = json.load(f)
        efficiency_df = pd.read_csv(mf_efficiency_path)
        phase6b_multifidelity(state, out_dir, speedup_report, efficiency_df)
    else:
        print("Phase 6b ... skipped (multifidelity_speedup_report.json not found -- run --stage multifidelity first)")

    print("Phase 7 ...")
    optimized = pd.read_csv(RESULTS_DIR / state / "optimized_designs.csv")
    deployable = pd.read_csv(RESULTS_DIR / state / "deployable_design_per_regime.csv")
    phase7_pareto_by_regime(state, out_dir, optimized, deployable)
    phase7_surrogate_vs_simulator(state, out_dir, optimized)
    phase7_safety_compliance(state, out_dir, optimized)

    robustness_path = RESULTS_DIR / state / "robustness_summary.csv"
    if robustness_path.exists():
        print("Phase 8 ...")
        robustness_summary = pd.read_csv(robustness_path)
        phase8_robustness_probabilities(state, out_dir, robustness_summary)
        phase8_useful_energy_intervals(state, out_dir, robustness_summary, deployable)
    else:
        print("Phase 8 ... skipped (robustness_summary.csv not found -- run --stage robustness first)")

    print(f"\nAll plots saved under: {out_dir}")
    print(f"  Static PNGs:       {out_dir / 'static'}")
    print(f"  Interactive HTML:  {out_dir / 'interactive'}")


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "uttarakhand"
    main(state)
