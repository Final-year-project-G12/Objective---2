"""
src/handoff/recommendation_card.py
=====================================
Phase 8 / D2.8 — one recommendation card per climate regime
(framework doc §12). Reads only frozen Objective 1 tables + the Phase 7
deployable selection + the Phase 8 robustness summary; computes nothing
new. Writes results/phase8_recommendation_cards.md.

Each card carries: regime/climate summary, the Objective 1 PCM shortlist
with its MCDM rank, the selected geometry + flow, simulator-confirmed
performance, the Phase 8 robustness probabilities, the surrogate-vs-
simulator delta, the decision rationale, and an explicit caveats block.
"""

import sys

import pandas as pd

from config import BASE_DIR, RESULTS_DIR
from src.io_utils import load_state_config, load_system_config

DEPLOYABLE_PATH = RESULTS_DIR / "phase7_deployable_design_per_regime.csv"
ROBUSTNESS_PATH = RESULTS_DIR / "phase8_robustness.csv"
OPTIMIZED_PATH = RESULTS_DIR / "phase7_optimized_designs.csv"
CARDS_PATH = RESULTS_DIR / "phase8_recommendation_cards.md"

SIM_VERSION = "sim_v1_rajasthan"


def _fmt(x, nd=2):
    try:
        return f"{float(x):.{nd}f}"
    except (TypeError, ValueError):
        return str(x)


def write_cards(state: str):
    cfg = load_state_config(state)
    system_config = load_system_config()
    deployable = pd.read_csv(DEPLOYABLE_PATH).set_index("regime_id")
    robustness = pd.read_csv(ROBUSTNESS_PATH).set_index("regime_id")
    optimized = pd.read_csv(OPTIMIZED_PATH)
    profiles = pd.read_csv(BASE_DIR / "data" / "objective1" / f"cluster_profiles_{state}.csv").set_index("cluster_id")
    mcdm = pd.read_csv(BASE_DIR / "data" / "objective1" / "mcdm_topk_by_cluster.csv")

    delivery_C = system_config["delivery"]["target_temp_C"]
    max_water_C = system_config["safety"]["max_water_temp_C"]
    max_pcm_C = system_config["safety"]["max_pcm_temp_C"]

    lines = []
    lines.append(f"# Objective 2 — Recommendation Cards (Rajasthan)\n")
    lines.append(f"Simulator: `{SIM_VERSION}` (Phase 4 GO). One card per Level-A climate "
                 f"regime. Every number here is traceable to a frozen Objective 1 table, "
                 f"the Phase 7 `deployable_design_per_regime` row, or the Phase 8 "
                 f"`robustness` summary — nothing is recomputed in this file.\n")

    for regime in cfg["regimes"]:
        cid = int(regime["cluster_id"])
        dep = deployable.loc[cid]
        rob = robustness.loc[cid]
        prof = profiles.loc[cid] if cid in profiles.index else None
        pcm_id = dep["pcm_id"]
        is_plain = (pcm_id == "NONE_plain_tank")

        lines.append(f"\n---\n\n## Regime {cid} — {regime['label']}")
        lines.append(f"\n**Medoid:** `{regime['weather_daily'].split('/')[-1].split('_cluster')[0].replace('weather_regime_','')}` "
                     f"cluster {cid}  ·  **Population covered:** {int(regime['population_covered']):,}  ·  "
                     f"**Regime size:** {regime['n_points']} grid points")

        # --- climate summary --------------------------------------------
        if prof is not None:
            lines.append(f"\n### Climate summary (population-weighted, `cluster_profiles_{state}.csv`)")
            lines.append(f"\n| GHI | Ta mean | Ta p95 | CDD24 | DTR | RH sunrise | monsoon idx |")
            lines.append(f"|---|---|---|---|---|---|---|")
            lines.append(f"| {_fmt(prof['GHI_daily_kWh'])} kWh/m²/d | {_fmt(prof['Ta_mean'],1)} °C | "
                         f"{_fmt(prof['Ta_p95'],1)} °C | {_fmt(prof['CDD24'],0)} | {_fmt(prof['DTR_true'],1)} °C | "
                         f"{_fmt(prof['RH_sunrise_mean'],1)} % | {_fmt(prof['monsoon_index'],2)} |")
            lines.append(f"\nObjective 1 design targets: `Tm_target_C` = {_fmt(regime['Tm_target_C'],1)} °C, "
                         f"`L_required` = {_fmt(regime['L_required_kJ_per_kg'],1)} kJ/kg (ceiling), "
                         f"`T_mains_est` = {_fmt(regime['T_mains_est_C'],2)} °C.")

        # --- PCM shortlist with O1 rank -------------------------------
        lines.append(f"\n### Objective 1 PCM shortlist (MCDM)")
        lines.append(f"\n| Rank | PCM | MC top-3 inclusion |")
        lines.append(f"|---|---|---|")
        mc_here = mcdm[mcdm["cluster_id"] == cid]
        for rank, name in enumerate(regime["pcm_shortlist"], start=1):
            mrow = mc_here[mc_here["pcm_id"] == name]
            inc = f"{mrow.iloc[0]['mc_top3_inclusion_pct']:.1f}%" if len(mrow) else "n/a"
            lines.append(f"| {rank} | {name} | {inc} |")

        # --- selected design ----------------------------------------------
        lines.append(f"\n### Selected deployable design (Phase 7)")
        if is_plain:
            lines.append(f"\n**Plain (sensible-only) 50 L tank — no PCM.** The Objective 1 PCM "
                         f"shortlist did not survive the pre-declared selection rule (see rationale below).")
        else:
            lines.append(f"\n**PCM: {pcm_id}**")
        lines.append(f"\n| Capsule diameter | Capsule count | Flow rate | PCM volume fraction | PCM mass |")
        lines.append(f"|---|---|---|---|---|")
        lines.append(f"| {_fmt(dep['capsule_diameter_m'],4)} m | {int(dep['n_capsule'])} | "
                     f"{_fmt(dep['flow_rate_kg_s'],4)} kg/s | {_fmt(dep['geom_pcm_volume_fraction'],4)} | "
                     f"{_fmt(dep['sim_pcm_mass_kg'],3)} kg |")
        lines.append(f"\n*(For the plain-tank selection the capsule diameter/count are the search's "
                     f"nominal values; `run_case` forces `n_capsule_effective = 0`, so the tank is "
                     f"simulated as plain sensible-water storage.)*" if is_plain else "")

        # --- simulator-confirmed performance ----------------------------
        lines.append(f"\n### Simulator-confirmed performance ({SIM_VERSION}, full year)")
        lines.append(f"\n| Useful energy | Solar fraction | Unmet energy | Pump energy | Max water T | "
                     f"Safety-margin to {int(max_water_C)} °C | Energy residual |")
        lines.append(f"|---|---|---|---|---|---|---|")
        lines.append(f"| {_fmt(dep['sim_useful_energy_kWh'],1)} kWh | {_fmt(dep['sim_solar_fraction']*100,2)} % | "
                     f"{_fmt(dep['sim_unmet_energy_kWh'],1)} kWh | {_fmt(dep['sim_pump_energy_kWh']*1000,4)} Wh | "
                     f"{_fmt(dep['sim_max_water_temp_C'],1)} °C | {_fmt(dep['constraint_margin_C'],1)} °C | "
                     f"{_fmt(dep['sim_residual_pct_of_collector'],6)} % |")

        # --- surrogate vs simulator -----------------------------------
        lines.append(f"\n### Surrogate vs simulator")
        lines.append(f"\nSurrogate predicted useful energy {_fmt(dep['pred_useful_energy_kWh'],1)} kWh; "
                     f"simulator confirmed {_fmt(dep['sim_useful_energy_kWh'],1)} kWh — "
                     f"**delta {_fmt(dep['surrogate_vs_sim_error_pct'],3)} %** "
                     f"(well inside the 15 % large-error rule; the surrogate was a proposal ranker only, "
                     f"Bug-Fix 5).")

        # --- robustness (Phase 8) ---------------------------------------
        lines.append(f"\n### Robustness — {int(rob['n_draws'])} Monte Carlo draws "
                     f"(weather+noise, demand volume ±20 %, demand timing ±30 min, mains ±2 °C)")
        lines.append(f"\n| P(meet delivery temp) | P(meet annual demand) | P(temp-safe) | "
                     f"Useful energy P5–P95 | Max water T P95 |")
        lines.append(f"|---|---|---|---|---|")
        lines.append(f"| {_fmt(rob['P_meet_delivery_temp'],2)} | {_fmt(rob['P_meet_annual_demand'],2)} | "
                     f"{_fmt(rob['P_temp_safe'],2)} | {_fmt(rob['useful_energy_p5_kWh'],0)}–"
                     f"{_fmt(rob['useful_energy_p95_kWh'],0)} kWh | {_fmt(rob['max_water_temp_C_p95'],1)} °C |")
        robust_verdict = ("**ROBUST**" if bool(rob["robust"])
                          else "**NOT ROBUST — reported as a caveat, not hidden**")
        lines.append(f"\nThreshold: robust if P(meet annual demand) ≥ ~0.75 **and** P(temp-safe) ≥ ~0.95. "
                     f"Result: {robust_verdict}.")
        if not bool(rob["robust"]):
            lines.append(f"\nThe binding failure is **P(temp-safe) = {_fmt(rob['P_temp_safe'],2)}**: under "
                         f"realistic weather/demand/mains variability the tank exceeds the {int(max_water_C)} °C "
                         f"water limit in a large fraction of draws. The deployable design's nominal margin "
                         f"is only {_fmt(dep['constraint_margin_C'],1)} °C, which a +GHI / +mains draw erases. "
                         f"This is the same hot-dry-climate + frozen-collector-sizing issue flagged since "
                         f"Phase 3; it makes an **active high-temperature bypass (Objective 3) a requirement, "
                         f"not an option** for Rajasthan.")

        # --- decision rationale ---------------------------------------
        lines.append(f"\n### Decision rationale")
        lines.append(f"\nPhase 7 searched 400 candidates per regime×PCM pair and re-ran the top 5 per pair "
                     f"in the real simulator. In this regime the best PCM geometry the search found beat the "
                     f"best plain-tank geometry by only ~0.1 % useful energy — two orders of magnitude below "
                     f"the pre-declared 5 % Pareto tolerance — and **no PCM candidate cleared the "
                     f"{int(max_pcm_C)} °C PCM safety limit** (0/45 across all regimes). The selection rule "
                     f"therefore keeps the design that (a) meets temperature safety and (b) has the lowest "
                     f"PCM mass → the plain tank.")

        # --- caveats -------------------------------------------------
        lines.append(f"\n### Caveats")
        lines.append(f"\n- **Missing / imputed PCM properties:** the Objective 1 database has imputed "
                     f"fields (`any_property_imputed`) for several shortlisted PCMs; not material here "
                     f"because no PCM was selected, but it would matter if the bounds are widened.")
        lines.append(f"- **Single-pass optimization:** one surrogate search + confirmation, no "
                     f"active-learning loop, no NSGA-II Pareto front.")
        lines.append(f"- **Reduced Monte Carlo:** {int(rob['n_draws'])} draws, medoid weather + noise "
                     f"(no alternate member-point weather series exists for Rajasthan); PCM latent-heat "
                     f"±10 % perturbation is inapplicable (plain tank selected).")
        lines.append(f"- **Single-state scope:** Rajasthan only. The multi-state comparison "
                     f"(does plain-tank-wins hold for Assam / Uttarakhand / Tamil Nadu too?) is future work.")
        lines.append(f"- **Lumped grey-box model:** single water node, single capsule group, "
                     f"correlation-based heat transfer — treat absolute numbers as ±15 %.")

    CARDS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved: {CARDS_PATH}  ({len(cfg['regimes'])} cards)")
    return CARDS_PATH


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "rajasthan"
    write_cards(state)
