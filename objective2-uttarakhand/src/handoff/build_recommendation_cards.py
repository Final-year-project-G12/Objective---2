"""
src/handoff/build_recommendation_cards.py
=============================================
Phase 8 / D2.8 — one recommendation card per climate regime, per the
framework doc §12. Aggregates everything Phases 1-8 already produced for
that regime; invents nothing new.

Reads:
  configs/states/<state>.yaml               -- regime/PCM/climate context
  data/objective1/pcm_database_<state>.csv  -- full PCM property record
  results/<state>/deployable_design_per_regime.csv  -- Phase 7 selection
  results/<state>/surrogate_metrics.csv             -- Phase 6 hold-out error
  results/<state>/robustness_summary.csv            -- Phase 8 Monte Carlo

Writes:
  results/<state>/recommendation_cards.md   -- one card per regime
"""

import sys

import pandas as pd

from config import BASE_DIR, RESULTS_DIR
from src.io_utils import load_state_config, get_pcm_properties


def _fmt(x, fmt="{:.2f}"):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "n/a"
    return fmt.format(x)


def build_card(state: str, regime: dict, deployable_row: pd.Series, robustness_row: pd.Series,
               surrogate_metrics: pd.DataFrame) -> str:
    cid = regime["cluster_id"]
    pcm_id = deployable_row["pcm_id"]
    is_plain = pcm_id == "NONE_plain_tank"
    pcm_record = get_pcm_properties(state, pcm_id) if not is_plain else None

    useful_e_rmse = surrogate_metrics.loc[
        (surrogate_metrics["target"] == "useful_energy_kWh") & (surrogate_metrics["model"] == "ExtraTrees"),
        "RMSE"].values
    useful_e_rmse = useful_e_rmse[0] if len(useful_e_rmse) else float("nan")

    lines = []
    lines.append(f"## Regime {cid} — {regime.get('label', '')}")
    lines.append("")
    lines.append("### Regime")
    lines.append(f"- Population covered: {regime['n_points']} points, "
                  f"{regime['population_covered']:,} people")
    lines.append(f"- State: {state.title()} | Medoid weather file: `{regime['weather_hourly']}`")
    lines.append(f"- Elevation: no dedicated elevation script; three inconsistent values "
                  f"coexist (0m in 00b_build_suntimes.py, flat 1200m DEFAULT_ALT_M in "
                  f"02_combine, pressure-derived elev_proxy in 04b) (Objective 1 "
                  f"limitation, carried forward unchanged)")
    lines.append(f"- Member-point robustness: NOT run (medoid-only for sub-daily/hourly shape; the annual "
                  f"weather magnitude below is now a real 10-year historical ensemble, not a noise proxy — "
                  f"see Caveats)")
    lines.append("")
    lines.append("### Climate")
    lines.append(f"- Tm_target_C (Objective 1, climate/delivery-anchored): {regime['Tm_target_C']}")
    lines.append(f"- Mains/inlet water temperature (population-weighted regime mean): {regime['T_mains_est_C']:.2f} C")
    lines.append(f"- L_required (Objective 1 sizing target): {regime['L_required_kJ_per_kg']:.1f} kJ/kg")
    lines.append(f"- Demand scenario: 300 L/day canonical dual-peak draw (`data/demand/demand_profile_{state}.csv`)")
    lines.append("")
    lines.append("### PCM shortlist (Objective 1, this regime)")
    for rank, name in enumerate(regime["pcm_shortlist"], start=1):
        marker = " <- SELECTED" if name == pcm_id else ""
        lines.append(f"  {rank}. {name}{marker}")
    if is_plain:
        lines.append(f"  -> Plain tank (no PCM) selected instead of all {len(regime['pcm_shortlist'])} "
                      f"shortlisted candidates (see Decision below)")
    lines.append("")

    lines.append("### Selected design")
    if is_plain:
        lines.append("- **Plain sensible-water tank — no PCM capsules.**")
    else:
        lines.append(f"- PCM: **{pcm_id}** "
                      f"(Tm={pcm_record['Tm_C']} C, latent heat={pcm_record['latent_heat_kJ_kg']} kJ/kg, "
                      f"conductivity={pcm_record['TC_W_mK']} W/mK)")
        lines.append(f"- Capsule shape/arrangement: sphere, staggered (frozen for all states)")
        lines.append(f"- Capsule diameter: {deployable_row['capsule_diameter_m']:.4f} m "
                      f"(max PCM conduction distance = {deployable_row['capsule_diameter_m']/2:.4f} m)")
        lines.append(f"- Capsule count: {int(deployable_row['n_capsule'])}")
        lines.append(f"- PCM mass: {deployable_row['sim_pcm_mass_kg']:.3f} kg")
    lines.append(f"- Flow rate: {deployable_row['flow_rate_kg_s']:.4f} kg/s "
                  f"(permitted range 0.010-0.050 kg/s)")
    lines.append("")

    lines.append("### Performance (simulator-confirmed, sim_v1_uttarakhand)")
    lines.append(f"- Useful annual energy: {deployable_row['sim_useful_energy_kWh']:.1f} kWh/year")
    lines.append(f"- Solar fraction: {deployable_row['sim_solar_fraction']*100:.2f}%")
    lines.append(f"- Delivery-temperature hours (>= 45 C): {_fmt(deployable_row.get('sim_delivery_temp_hours'), '{:.0f}')}")
    lines.append(f"- Unmet energy: {deployable_row['sim_unmet_energy_kWh']:.1f} kWh/year")
    lines.append(f"- Pump energy: {deployable_row['sim_pump_energy_kWh']*1000:.4f} Wh/year")
    lines.append(f"- Constraint margin (temperature): {deployable_row['constraint_margin_C']:.2f} C below the "
                  f"tightest safety limit")
    lines.append("")

    lines.append("### Robustness (120 Monte Carlo draws — PCM latent heat, two-level weather noise "
                  "[annual scale/offset + per-hour jitter], demand volume/timing, mains temperature)")
    if robustness_row is not None:
        lines.append(f"- P(meets annual demand, solar_fraction>=50%): {robustness_row['p_meets_annual_demand']*100:.1f}%")
        lines.append(f"- P(meets delivery temperature, solar_fraction>=45%): {robustness_row['p_meets_delivery_temp']*100:.1f}%")
        lines.append(f"- P(any safety-temperature violation): {robustness_row['p_temperature_violation']*100:.1f}%")
        lines.append(f"- P(exceeds max safe temperature limit): {robustness_row['p_exceeds_max_safe_temp']*100:.1f}%")
        lines.append(f"- Useful energy 5th-50th-95th percentile: "
                      f"[{robustness_row['useful_energy_p05_kWh']:.1f}, {robustness_row['useful_energy_p50_kWh']:.1f}, "
                      f"{robustness_row['useful_energy_p95_kWh']:.1f}] kWh")
        lines.append(f"- Solar fraction 5th-95th percentile: "
                      f"[{robustness_row['solar_fraction_p05']*100:.1f}%, {robustness_row['solar_fraction_p95']*100:.1f}%]")
        lines.append(f"- Max water temperature 95th percentile: {robustness_row['max_water_temp_p95_C']:.1f} C")
        robust_verdict = "ROBUST" if robustness_row["robust_per_framework_rule"] else "NOT ROBUST BY THE FRAMEWORK RULE (report as caveat, not hidden)"
        lines.append(f"- **Framework rule (P(demand)>=75% and P(temp-safe)>=95%): {robust_verdict}**")
    else:
        lines.append("- Not yet run for this regime.")
    lines.append("")

    lines.append("### Surrogate QA")
    lines.append(f"- Hold-out RMSE (useful_energy_kWh, ExtraTrees, all regimes pooled): {useful_e_rmse:.3f} kWh")
    lines.append(f"- Surrogate-vs-simulator error for this selected design: "
                  f"{deployable_row['surrogate_vs_sim_error_pct']:.3f}%")
    lines.append("")

    lines.append("### Decision")
    if is_plain:
        lines.append(f"- Best PCM found in this regime's search reached "
                      f"{deployable_row['best_useful_energy_in_regime_kWh']:.1f} kWh vs plain tank's "
                      f"{deployable_row['sim_useful_energy_kWh']:.1f} kWh — within the pre-declared 5% "
                      f"Pareto tolerance, so the selection rule's next tie-breaker (minimize PCM mass, then "
                      f"pump energy, then capsule count) picked the zero-mass plain tank. "
                      f"See `docs_objective2/08_PHASE7_OPTIMIZATION.md` for the full comparison.")
    else:
        lines.append(f"- This PCM's best found design reached the regime's own best useful-energy value "
                      f"({deployable_row['best_useful_energy_in_regime_kWh']:.1f} kWh), winning outright "
                      f"before any tolerance tie-break was needed.")
    lines.append(f"- Selection-rule pool size (candidates within 5% of best): "
                  f"{int(deployable_row['selection_rule_pool_size'])}")
    lines.append("")

    lines.append("### Caveats")
    lines.append("- The robustness section's annual GHI/temperature variability is drawn from Objective "
                  "1's real 10-year (2016-2025) daily weather archive for this regime "
                  "(src/robustness/weather_ensemble.py) -- a genuine historical-year ensemble, not an "
                  "assumed range. The within-year HOURLY shape still comes from a single medoid year plus "
                  "synthetic per-hour jitter (no member-point/multi-year hourly data was pulled for this "
                  "project, 40-hr cut list).")
    lines.append("- Melting treated as a narrow +/-1 K band around a single reported Tm_C (no measured "
                  "solidus/liquidus interval in the PCM database).")
    lines.append("- Liquid natural convection inside the capsule is not resolved -- a fixed x2 effective-"
                  "conductivity enhancement factor is assumed once liquid fraction >=50%.")
    lines.append("- No auxiliary/backup heater modeled -- solar fraction here is the fraction of ideal 45 C "
                  "demand met by solar+PCM alone, stricter than a real installed system with backup heating.")
    lines.append("- No active high-temperature safety shield/bypass modeled -- see the robustness section's "
                  "temperature-violation probability above.")
    if not is_plain:
        lines.append(f"- {pcm_record.get('name','PCM')} property provenance: check `any_property_imputed` in "
                      f"`data/objective1/pcm_database_{state}.csv` for which fields are manufacturer-measured "
                      f"vs MICE/RF-imputed.")
    lines.append("")
    return "\n".join(lines)


def run(state: str):
    cfg = load_state_config(state)
    out_dir = RESULTS_DIR / state
    deployable = pd.read_csv(out_dir / "deployable_design_per_regime.csv")
    surrogate_metrics = pd.read_csv(out_dir / "surrogate_metrics.csv")
    robustness_path = out_dir / "robustness_summary.csv"
    robustness = pd.read_csv(robustness_path) if robustness_path.exists() else None

    header = [
        f"# Objective 2 Recommendation Cards — {state}",
        "",
        f"Simulator version: `sim_v1_{state}`. Generated from Phases 1-8 results; "
        f"nothing below is a surrogate-only estimate -- every performance number is "
        f"simulator-confirmed (Phase 7) and every robustness probability comes from "
        f"real Monte Carlo simulator re-runs (Phase 8), not the surrogate.",
        "",
    ]

    cards = []
    for regime in cfg["regimes"]:
        cid = regime["cluster_id"]
        row = deployable[deployable["regime_id"] == cid]
        if row.empty:
            continue
        row = row.iloc[0]
        rob_row = None
        if robustness is not None:
            rr = robustness[robustness["regime_id"] == cid]
            rob_row = rr.iloc[0] if not rr.empty else None
        cards.append(build_card(state, regime, row, rob_row, surrogate_metrics))

    text = "\n".join(header) + "\n\n---\n\n".join(cards)
    out_path = out_dir / "recommendation_cards.md"
    out_path.write_text(text, encoding="utf-8")
    print(f"Saved: {out_path}")
    return text


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "uttarakhand"
    run(state)
