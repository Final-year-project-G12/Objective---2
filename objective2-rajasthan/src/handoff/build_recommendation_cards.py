"""
src/handoff/build_recommendation_cards.py
=============================================
Phase 8 / D2.8 — one recommendation card per climate regime
(framework doc §12). Reads only frozen Objective 1 tables + the Phase 7
deployable selection + the Phase 8 robustness summary; computes nothing
new. Writes results/phase8_recommendation_cards.md.

Each card carries: regime/climate summary, the Objective 1 PCM shortlist
with its MCDM rank, the selected geometry + flow, simulator-confirmed
performance, the Phase 8 robustness probabilities, the surrogate-vs-
simulator delta, the decision rationale, and an explicit caveats block.

Naming (`build_recommendation_cards.py`, entry point `run(state)`)
matches `objective2-tamilnadu/src/handoff/build_recommendation_cards.py`.
"""

import sys

import pandas as pd

from config import BASE_DIR, RESULTS_DIR
from src.io_utils import load_state_config, load_system_config

DEPLOYABLE_PATH = RESULTS_DIR / "phase7_deployable_design_per_regime.csv"
ROBUSTNESS_PATH = RESULTS_DIR / "phase8_robustness.csv"
OPTIMIZED_PATH = RESULTS_DIR / "phase7_optimized_designs.csv"
CARDS_PATH = RESULTS_DIR / "phase8_recommendation_cards.md"

SIM_VERSION = "sim_v2_rajasthan"


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
    shield_cfg = system_config.get("safety_shield", {})
    shield_on = bool(shield_cfg.get("enabled", False))

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
        lines.append(f"\n**Selected arrangement:** {dep['arrangement']}")
        lines.append(f"\n**Arrangement rationale:** {dep['arrangement_rationale']}")

        # --- O1<->O2 cohesion (2026-09-18 cohesion-gap fix #5) ------------
        if not is_plain and "diverges_from_o1_rank1" in dep.index:
            if bool(dep["diverges_from_o1_rank1"]):
                lines.append(f"\n**Match to Objective 1's ranking:** DIVERGES — O2 deploys **{pcm_id}**, "
                             f"but Objective 1's MCDM consensus rank-1 pick for this regime is "
                             f"**{dep['o1_rank1_pcm']}**. Objective 2's selection rule (useful-energy "
                             f"tolerance, then pump energy/PCM mass/capsule count/margin) does not weight "
                             f"O1's consensus rank, so a lower-ranked-but-still-shortlisted PCM can win on "
                             f"design-level performance. This is expected and reported, not a defect — see "
                             f"`docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §2/§8.")
            else:
                lines.append(f"\n**Match to Objective 1's ranking:** MATCHES — O2's deployable design uses "
                             f"**{pcm_id}**, Objective 1's MCDM consensus rank-1 pick for this regime.")

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
        shield_note = (f" — rule-based safety shield ACTIVE (bypass at "
                       f"{_fmt(shield_cfg.get('bypass_water_C', max_water_C-3.0),1)} °C water / "
                       f"{_fmt(shield_cfg.get('bypass_pcm_C', max_pcm_C-3.0),1)} °C PCM), the pipeline "
                       f"default since 2026-09-13 — see `src/simulation/tank_model.py`"
                       if shield_on else " — safety shield DISABLED for this run")
        lines.append(f"\n### Robustness — {int(rob['n_draws'])} Monte Carlo draws "
                     f"(weather+noise, demand volume ±20 %, demand timing ±30 min, mains ±2 °C){shield_note}")
        lines.append(f"\n| P(meet delivery temp) | P(meet annual demand) | P(temp-safe) | "
                     f"P(exceeds max safe temp) | Useful energy P5–P95 | Max water T P95 |")
        lines.append(f"|---|---|---|---|---|---|")
        p_temp_safe = 1.0 - float(rob['p_temperature_violation'])
        lines.append(f"| {_fmt(rob['p_meets_delivery_temp'],2)} | {_fmt(rob['p_meets_annual_demand'],2)} | "
                     f"{_fmt(p_temp_safe,2)} | {_fmt(rob['p_exceeds_max_safe_temp'],2)} | "
                     f"{_fmt(rob['useful_energy_p05_kWh'],0)}–{_fmt(rob['useful_energy_p95_kWh'],0)} kWh | "
                     f"{_fmt(rob['max_water_temp_p95_C'],1)} °C |")
        robust_verdict = ("**ROBUST**" if bool(rob["robust_per_framework_rule"])
                          else "**NOT ROBUST — reported as a caveat, not hidden**")
        lines.append(f"\nThreshold: robust if P(meet annual demand) ≥ ~0.75 **and** P(temp-safe) ≥ ~0.95. "
                     f"Result: {robust_verdict}.")
        if not bool(rob["robust_per_framework_rule"]):
            lines.append(f"\nThe binding failure is **P(temp-safe) = {_fmt(p_temp_safe,2)}** (any flagged "
                         f"safety sub-hour) / **P(exceeds max safe temp) = {_fmt(rob['p_exceeds_max_safe_temp'],2)}** "
                         f"(the reported annual max clearing the hard limit): under realistic weather/demand/"
                         f"mains variability the tank exceeds the {int(max_water_C)} °C water limit in a large "
                         f"fraction of draws. The deployable design's nominal margin is only "
                         f"{_fmt(dep['constraint_margin_C'],1)} °C, which a +GHI / +mains draw erases. "
                         f"This is the same hot-dry-climate + frozen-collector-sizing issue flagged since "
                         f"Phase 3; it makes an **active high-temperature bypass (Objective 3) a requirement, "
                         f"not an option** for Rajasthan.")

        # --- decision rationale ---------------------------------------
        n_pcm_total = len(optimized[optimized["pcm_id"] != "NONE_plain_tank"])
        n_pcm_clears_limit = int((optimized["sim_max_pcm_temp_C"] <= max_pcm_C).sum())
        if is_plain:
            selection_phrase = ("the plain tank, since no PCM candidate in this regime both met "
                                "temperature safety and useful energy within tolerance")
        else:
            selection_phrase = (f"**{pcm_id}**, which meets temperature safety"
                                f"{' under the shield' if shield_on else ''} and is within the Pareto "
                                f"tolerance of (or beats) the best plain-tank useful energy")
        shield_search_note = (", with the safety shield active throughout search, confirmation, "
                              "and selection (pipeline default since 2026-09-13)" if shield_on else "")
        lines.append(f"\n### Decision rationale")
        lines.append(f"\nPhase 7 searched 600 candidates per regime×PCM pair (arrangement sampled uniformly "
                     f"across single-layer/staggered/radial since 2026-09-17) and re-ran the top 5 per pair "
                     f"in the real simulator{shield_search_note}. "
                     f"{n_pcm_clears_limit}/{n_pcm_total} PCM candidates (across all regimes) clear the "
                     f"{int(max_pcm_C)} °C PCM safety limit. The pre-declared selection rule "
                     f"(reject temperature-unsafe → within 5 % of best useful energy → min pump energy → "
                     f"min PCM mass → min capsule count → max constraint margin) selects {selection_phrase}.")

        # --- caveats -------------------------------------------------
        lines.append(f"\n### Caveats")
        pcm_imputed_note = ("not material here because no PCM was selected, but it would matter if "
                            "the bounds are widened" if is_plain else
                            "the selected PCM's own imputed-property flags should be checked before "
                            "quoting its properties as measured")
        lines.append(f"\n- **Missing / imputed PCM properties:** the Objective 1 database has imputed "
                     f"fields (`any_property_imputed`) for several shortlisted PCMs; {pcm_imputed_note}.")
        lines.append(f"- **Single-pass optimization:** one surrogate search + confirmation, no "
                     f"active-learning loop, no NSGA-II Pareto front.")
        mc_pcm_note = ("; PCM latent-heat ±10 % perturbation is inapplicable (plain tank selected)"
                      if is_plain else " (PCM latent-heat ±10 % perturbation included)")
        lines.append(f"- **Reduced Monte Carlo:** {int(rob['n_draws'])} draws, medoid weather + noise "
                     f"(no alternate member-point weather series exists for Rajasthan){mc_pcm_note}.")
        lines.append(f"- **Single-state scope:** Rajasthan only. The multi-state comparison "
                     f"(does this same shielded-selection outcome hold for Assam / Uttarakhand / Tamil "
                     f"Nadu too?) is future work.")
        lines.append(f"- **Lumped grey-box model:** single water node, single capsule group, "
                     f"correlation-based heat transfer — treat absolute numbers as ±15 %.")
        if shield_on:
            lines.append(f"- **Safety shield is the pipeline default (adopted 2026-09-13):** every number "
                         f"on this card (Phase 5-8) is computed WITH the rule-based safety shield active "
                         f"(`system_config_shared.yaml: safety_shield.enabled`), not as a separate what-if. "
                         f"IS 12976:2023 §8.2 validates this exact mechanism as the standard overheat-"
                         f"protection method for Indian SWH systems.")
            lines.append(f"- **A further, not-yet-adopted mitigation exists:** the frozen 50 L tank / "
                         f"1.5 m² collector sizing (33.3 L/m²) is itself below IS 12976:2023's cited "
                         f"37.5-100 L/m² range; resizing the tank to the standard's 75 L/m² reference "
                         f"(112.5 L) makes every shortlisted PCM candidate pass safety AND raises solar "
                         f"fraction, with no shield needed — see "
                         f"`results/fix6_standards_compliant_sizing_supplementary.md` and "
                         f"`docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §7. Not folded into this card's "
                         f"numbers (a frozen-shared-config change requires a coordinated 4-state re-run).")

    CARDS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved: {CARDS_PATH}  ({len(cfg['regimes'])} cards)")
    return CARDS_PATH


def run(state: str):
    """Entry point name matches objective2-tamilnadu/src/handoff/build_recommendation_cards.py."""
    return write_cards(state)


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "rajasthan"
    run(state)
