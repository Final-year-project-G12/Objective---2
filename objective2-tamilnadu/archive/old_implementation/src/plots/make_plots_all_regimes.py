"""
src/plots/make_plots_all_regimes.py
=====================================
Extends Phase 3's single-regime sample plots (make_plots.py's
_phase3_sample_run, hardcoded to regime 0) to all 3 regimes / both final
PCMs, using the real final deployable design for each
(results/<state>/deployable_design_per_regime.csv) -- never a hardcoded
placeholder.

Re-runs run_case() for each regime (the full-year hourly trace isn't
persisted by Phase 7/8, only the annual summary is), so this doesn't
change or re-derive any existing result -- it just re-produces the same
Phase-3-style time series for regimes 1 and 2 the way regime 0 already has.

Writes:
  results/<state>/plots/interactive/phase3_temperature_timeseries_regime{1,2}.html
  results/<state>/plots/interactive/phase3_melt_fraction_year_all_regimes.html
  results/<state>/plots/interactive/phase3_energy_breakdown_all_regimes.html
  results/<state>/phase3_heating_summary.csv   -- hours heating vs shield-bypassed, per regime

Run: python -m src.plots.make_plots_all_regimes tamilnadu
"""

import sys

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import RESULTS_DIR
from src.design.schema import DesignVector
from src.simulation.run_case import run_case
from src.plots.make_plots import _save

REGIME_COLORS = {0: "#1f77b4", 1: "#2ca02c", 2: "#d62728"}


def _run_regime(state, row):
    design = DesignVector(row["capsule_diameter_m"], int(row["n_capsule"]), row["flow_rate_kg_s"],
                           capsule_arrangement=row["arrangement"])
    out = run_case(state, cluster_id=int(row["regime_id"]), pcm_name=row["pcm_id"],
                    design=design, record_hourly=True)
    return out["hourly"], out["metrics"], row["pcm_id"], design


def main(state):
    out_dir = RESULTS_DIR / state / "plots"
    deployable = pd.read_csv(RESULTS_DIR / state / "deployable_design_per_regime.csv")

    runs = {}
    summary_rows = []
    for _, row in deployable.iterrows():
        regime_id = int(row["regime_id"])
        print(f"  running regime {regime_id} ({row['pcm_id']}, {row['arrangement']}) for the full year...")
        hourly, metrics, pcm_name, design = _run_regime(state, row)
        runs[regime_id] = (hourly, metrics, pcm_name, design)

        total_hours = len(hourly)
        heating_hours = int((hourly["Q_collector_Wh"] > 0).sum())
        shield_hours = int((hourly["shield_activations"] > 0).sum())
        summary_rows.append({
            "regime_id": regime_id, "pcm_id": pcm_name, "arrangement": design.capsule_arrangement,
            "total_hours": total_hours, "heating_hours": heating_hours,
            "idle_or_bypassed_hours": total_hours - heating_hours,
            "pct_time_heating": round(100 * heating_hours / total_hours, 2),
            "shield_trip_hours": shield_hours,
            "total_shield_activations": int(hourly["shield_activations"].sum()),
            "mean_liquid_fraction": round(float(hourly["f_melt"].mean()), 4),
            "max_liquid_fraction": round(float(hourly["f_melt"].max()), 4),
            "collector_energy_kWh": round(metrics["collector_energy_kWh"], 1),
            "useful_energy_kWh": round(metrics["useful_energy_kWh"], 1),
            "unmet_energy_kWh": round(metrics["unmet_energy_kWh"], 1),
        })

    summary_df = pd.DataFrame(summary_rows)
    summary_path = RESULTS_DIR / state / "phase3_heating_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    print(f"\n[OK] wrote {summary_path}\n")
    print(summary_df.to_string(index=False))

    # ---- temperature timeseries, regimes 1 & 2 (regime 0 already exists) ----
    for regime_id in (1, 2):
        hourly, metrics, pcm_name, design = runs[regime_id]
        week = hourly.iloc[2400:2568]
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=week["hour_index"], y=week["T_w_C"], name="T_water (C)",
                                  line=dict(color="#1f77b4")), secondary_y=False)
        fig.add_trace(go.Scatter(x=week["hour_index"], y=week["T_pcm_C"], name="T_PCM (C)",
                                  line=dict(color="#d62728")), secondary_y=False)
        fig.add_trace(go.Scatter(x=week["hour_index"], y=week["I_t_Wm2"], name="Irradiance (W/m2)",
                                  line=dict(color="#ff7f0e", dash="dot")), secondary_y=True)
        fig.update_layout(title=f"Phase 3 — one representative week: T_water, T_PCM, irradiance — {state}, "
                                 f"regime {regime_id}, {pcm_name}, {design.capsule_arrangement}",
                           xaxis_title="hour of year")
        fig.update_yaxes(title_text="Temperature (C)", secondary_y=False)
        fig.update_yaxes(title_text="Irradiance (W/m2)", secondary_y=True)
        _save(fig, f"phase3_temperature_timeseries_regime{regime_id}", out_dir)

    # ---- liquid fraction, all 3 regimes overlaid ----
    fig = go.Figure()
    for regime_id, (hourly, metrics, pcm_name, design) in sorted(runs.items()):
        fig.add_trace(go.Scatter(x=hourly["hour_index"], y=hourly["f_melt"], mode="lines",
                                  name=f"Regime {regime_id} ({pcm_name})",
                                  line=dict(color=REGIME_COLORS[regime_id], width=1)))
    fig.update_layout(title=f"Phase 3 — PCM liquid fraction over the simulated year, all 3 regimes — {state}",
                       xaxis_title="hour of year", yaxis_title="liquid fraction f_melt [0-1]")
    _save(fig, "phase3_melt_fraction_year_all_regimes", out_dir)

    # ---- energy breakdown, all 3 regimes grouped bar ----
    labels = ["Collector input", "Delivered to load", "Tank/pipe loss", "Unmet (shortfall)"]
    fig = go.Figure()
    for regime_id, (hourly, metrics, pcm_name, design) in sorted(runs.items()):
        values = [metrics["collector_energy_kWh"], metrics["useful_energy_kWh"],
                  metrics["loss_energy_kWh"], metrics["unmet_energy_kWh"]]
        fig.add_trace(go.Bar(x=labels, y=values, name=f"Regime {regime_id} ({pcm_name})",
                              marker_color=REGIME_COLORS[regime_id],
                              text=[f"{v:,.0f}" for v in values], textposition="outside"))
    fig.update_layout(title=f"Phase 3 — annual energy breakdown, all 3 regimes — {state}",
                       yaxis_title="kWh / year", barmode="group")
    _save(fig, "phase3_energy_breakdown_all_regimes", out_dir)

    print("\nDone.")


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "tamilnadu"
    main(state)
