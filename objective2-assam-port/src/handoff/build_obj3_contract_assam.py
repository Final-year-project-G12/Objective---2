"""
src/handoff/build_obj3_contract_assam.py
========================================
Builds the Objective 3 environment contract for ASSAM from the CURRENT Objective 2 results.
Writes results/obj3_environment_contract_assam_v3.json (same schema as the Tamil Nadu v3 contract).

Ported from src/handoff/build_obj3_contract_tamilnadu.py on 2026-11-19. What is different, and why:
  * STATE = "assam", system 50 L tank / 1.5 m2 collector / 100 L/day (read from the configs, not typed).
  * The generic blocks (action_space, reset_scenarios, acceptance tests, state schema) come from
    data/handoff/obj3_generic_blocks.json, copied from Tamil Nadu's v3 contract -- Tamil Nadu used the archived 2026-10-27
    contract for the same blocks.  NOTE: reset_scenarios start the water at 30 C, a Tamil Nadu-style value; Assam's mains are
    16.6-19.9 C, so Objective 3 should review those initial conditions.
  * Every Tamil Nadu result sentence (designs, "9 of 9", binding 30 % cap, 60/67 C temperature table, O1 Spearman rho,
    ANSYS caveats) is REMOVED. Result statements here are computed from results/ files, or say plainly that no evidence exists
    for Assam yet.  Assam has had no CFD cross-check and no widened-bound diagnostic read into this file.
  * Assam's PCM shortlist is a physics-validated order, NOT an MCDM consensus (Objective 1 produced no K=3 MCDM ranking); the
    contract says so.

Usage:  python -m src.handoff.build_obj3_contract_assam
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

BASE = Path(__file__).resolve().parent.parent.parent
RESULTS = BASE / "results"
CONFIGS = BASE / "configs"
GENERIC = BASE / "data" / "handoff" / "obj3_generic_blocks.json"
NEW = RESULTS / "obj3_environment_contract_assam_v3.json"

STATE = "assam"
N_REGIMES = 3


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_yaml(p: Path):
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build() -> Path:
    generic = json.loads(GENERIC.read_text(encoding="utf-8"))
    sysc = _load_yaml(CONFIGS / "system_config_shared.yaml")
    statec = _load_yaml(CONFIGS / "states" / f"{STATE}.yaml")
    band = pd.read_csv(RESULTS / "wp6_band.csv")
    held = pd.read_csv(RESULTS / "g10_heldout_results.csv")
    lock = json.loads((RESULTS / "held_out_test.lock").read_text(encoding="utf-8"))
    sel = [json.loads((RESULTS / f"g10_selection_r{k}.json").read_text(encoding="utf-8")) for k in range(N_REGIMES)]

    c = {}
    c["state"] = STATE
    c["contract_version"] = "obj3_contract_v3.0_assam_2026-11-19"
    c["generated_utc"] = datetime.now(timezone.utc).isoformat()
    c["validated_simulator_version"] = (
        f"sim_v3_assam (multi-node tank, search dt={sysc['solver']['timestep_s']} s, "
        f"confirmation dt={sysc['solver']['timestep_confirm_s']} s)")
    c["source"] = ("Objective 2 Assam pipeline: the Tamil Nadu g2-g25 stages run on Assam inputs "
                   "(objective2-assam-port, scripts/run_parallel.ps1). Built by src/handoff/build_obj3_contract_assam.py.")
    c["supersession_note"] = (
        "SUPERSEDES the earlier Assam contract results/obj3_environment_contract_assam.json (the phase-0..8 pipeline, "
        "one 2025 ERA5 year per regime, no held-out test, no year roles). Objective 3 must read THIS file.")

    c["global_limits"] = {
        "delivery_target_temp_C": sysc["delivery"]["target_temp_C"],
        "max_safe_water_temp_C": sysc["safety"]["max_water_temp_C"],
        "max_safe_pcm_temp_C": sysc["safety"]["max_pcm_temp_C"],
        "max_pressure_bar": sysc["safety"]["max_pressure_bar"],
        "min_irradiance_cutoff_Wm2": sysc["collector"]["min_irradiance_cutoff_Wm2"],
        "flow_min_kg_s": sysc["pump"]["flow_min_kg_s"],
        "flow_max_kg_s": sysc["pump"]["flow_max_kg_s"],
        "pump_efficiency": sysc["pump"]["efficiency"],
        "note": ("These are HARD limits. The controller may never command outside the flow envelope, and may never drive "
                 "water above max_safe_water_temp_C or PCM above max_safe_pcm_temp_C."),
    }

    c["fixed_system"] = {
        "tank_volume_L": sysc["tank"]["volume_L"],
        "tank_height_to_diameter_ratio": sysc["tank"]["height_to_diameter_ratio"],
        "tank_insulation_m": sysc["tank"]["insulation_m"],
        "tank_U_W_m2K": sysc["tank"]["U_tank_W_m2K"],
        "collector_area_m2": sysc["collector"]["area_m2"],
        "collector_fr_tau_alpha": sysc["collector"]["fr_tau_alpha"],
        "collector_fr_ul_W_m2K": sysc["collector"]["fr_ul_W_m2K"],
        "collector_flow_dependent_fr_enabled": sysc["collector"]["flow_dependent_fr"]["enabled"],
        "capsule_wall_material": sysc["pcm_integration"]["capsule_wall_material"],
        "capsule_wall_thickness_m": sysc["pcm_integration"]["capsule_wall_thickness_m"],
        "liquid_convection_enhancement": sysc["pcm_integration"]["liquid_convection_enhancement"],
        "melting_half_width_K": sysc["pcm_integration"]["melting_half_width_K"],
        "WARNING_tank_collector": ("50 L / 1.5 m2 = 33.3 L/m2, BELOW the IS 12976:2023 4.2 band (40-100 L/m2). This is Assam's "
                                   "own Objective-1 household, kept as a stated limitation. It is NOT Tamil Nadu's 100 L / 2.5 m2, "
                                   "so absolute kWh figures are not comparable across the two states."),
    }

    bands = {f"r{k}": band[band.scope == f"r{k}"].set_index("objective").band.to_dict() for k in range(N_REGIMES)}
    regimes_cfg = {r["cluster_id"]: r for r in statec["regimes"]}

    designs = []
    for k in range(N_REGIMES):
        ch = sel[k]["chosen"]
        rc = regimes_cfg[k]
        h = held[(held.regime == k) & (held.role == "chosen")]
        designs.append({
            "regime_id": k,
            "label": rc["label"],
            "medoid_point_id": rc["medoid_point_id"],
            "n_points": rc["n_points"],
            "population_covered": rc["population_covered"],
            "T_mains_est_C": rc["T_mains_est_C"],
            "o1_pcm_shortlist": rc["pcm_shortlist"],
            "o1_shortlist_basis": "physics-validated order (O1 produced no K=3 MCDM ranking for Assam); NOT an MCDM consensus",
            "selected_pcm": ch["pcm"],
            "selected_pcm_o1_rank": ch["pcm_rank"],
            "capsule_inner_radius_m": ch["R_in_m"],
            "capsule_inner_diameter_mm": round(ch["R_in_m"] * 2000.0, 2),
            "capsule_outer_diameter_mm": round(
                (ch["R_in_m"] * 2.0 + 2.0 * sysc["pcm_integration"]["capsule_wall_thickness_m"]) * 1000.0, 2),
            "pcm_volume_fraction": ch["fraction"],
            "n_capsules": ch["N"],
            "arrangement": ch["arrangement"],
            "nominal_flow_kg_s": ch["flow"],
            "pcm_mass_kg": ch["pcm_mass_kg"],
            "select_year_metrics": {
                "g_window_kWh_yr": ch["g_window"], "g_annual_kWh_yr": ch["g_annual"], "d_overheat_h": ch["d_overheat"],
                "t_pcm_max_C": ch["t_pcm_max"], "t_water_max_C": ch["t_water_max"],
            },
            "repeatability_band": bands[f"r{k}"],
            "selection_funnel": {
                "n_candidates": sel[k]["n_candidates"],
                "n_S0_indistinguishable_on_g_window": sel[k]["n_S0_indistinguishable_on_g_window"],
                "n_S1": sel[k]["n_S1"], "n_S2": sel[k]["n_S2"],
                "note": ("Tie-breaks were declared before results were seen. Designs differing by less than the repeatability "
                         "band are treated as tied, then overheating, PCM mass, capsule count and temperature margin decide."),
            },
            "held_out_2011_2015": (h.drop(columns=[x for x in h.columns if x.startswith("plain_")],
                                          errors="ignore").round(4).to_dict("records")),
        })
    c["static_design_per_regime"] = designs

    # gates are COMPUTED from the held-out file, never typed
    per_design = held.groupby(["regime", "role", "pcm"]).agg(g=("g_window", "mean"), tp=("t_pcm_max", "max"),
                                                              tw=("t_water_max", "max")).reset_index()
    n = len(per_design)
    c["held_out_test"] = {
        "status": "COMPLETED AND LOCKED - do not re-run, do not tune against these years",
        "years": [2011, 2012, 2013, 2014, 2015],
        "run_id": lock["run_id"], "locked_utc": lock["utc"], "selection_fingerprint": lock["selection_fingerprint"],
        "n_designs_tested": int(n),
        "coverage": "The chosen design of each regime plus the best design of every other shortlisted PCM.",
        "gates": {
            "beats_water_only_twin_mean_g_window_positive": f"{int((per_design.g > 0).sum())} of {n}",
            "pcm_peak_under_limit": f"{int((per_design.tp < sysc['safety']['max_pcm_temp_C']).sum())} of {n} "
                                    f"(max {per_design.tp.max():.1f} C vs {sysc['safety']['max_pcm_temp_C']} C)",
            "water_peak_under_limit": f"{int((per_design.tw < sysc['safety']['max_water_temp_C']).sum())} of {n} "
                                      f"(max {per_design.tw.max():.1f} C vs {sysc['safety']['max_water_temp_C']} C)",
        },
    }

    c["weather_sequences"] = {
        "source": "NASA POWER hourly point data (UTC), 2011-2025, one medoid point per regime",
        "training": {"years": [2016, 2017, 2018, 2019, 2020], "role": "explore"},
        "validation": {"years": [2021, 2022, 2023], "role": "select"},
        "held_out_test": {"years": [2011, 2012, 2013, 2014, 2015], "role": "test",
                          "note": "Objective 2's one-shot test is DONE and locked. Objective 3 must NOT tune against these years."},
        "unused": {"years": [2024, 2025], "role": "used_test_v1",
                   "note": ("Carried over from Tamil Nadu's role map, where these years were spent by an earlier test. In Assam they "
                            "were never used for a test; they are simply accepted for no purpose in Objective 2.")},
        "enforcement": ("src/weather/roles.py refuses to load a year whose role differs from the stated purpose; the test years "
                        "additionally require acquire_test_lock()."),
        "medoid_points": {str(k): regimes_cfg[k]["medoid_point_id"] for k in range(N_REGIMES)},
    }

    c["time_step_s"] = sysc["solver"]["timestep_s"]
    c["time_step_confirm_s"] = sysc["solver"]["timestep_confirm_s"]
    c["demand_profile_file"] = statec["demand_profile"]["file"]
    c["demand_daily_total_L"] = statec["demand_profile"]["daily_total_L"]

    c["action_space"] = generic["action_space"]
    c["reset_scenarios"] = generic["reset_scenarios"]
    c["acceptance_test_before_drl_training"] = generic["acceptance_test_before_drl_training"]
    c["dynamic_state_schema"] = generic["dynamic_state_schema"]

    c["safety_shield"] = {
        "enabled": sysc["safety_shield"]["enabled"],
        "bypass_water_C": sysc["safety_shield"]["bypass_water_C"],
        "bypass_pcm_C": sysc["safety_shield"]["bypass_pcm_C"],
        "enforced_in": "src/simulation/tank_model.py - inside the physics, NOT in the policy",
        "note": ("Already enforced, not a specification to implement. Objective 3's job is a better controller than this reactive "
                 "trip - one that anticipates the limit instead of reacting at it."),
        "standard": "IS 12976:2023 Sec 8.2 (overheat protection).",
    }

    c["reward_function"] = {
        "status": "SUGGESTED. Weights are deliberately NOT chosen - Objective 3 sets and justifies them.",
        "formula": "r_t = w1*E_del_t - w2*overheat_step_t - w3*safety_violation_t - w4*bypass_switch_t",
        "term_definitions": {
            "E_del_t": f"energy delivered up to the {sysc['delivery']['target_temp_C']} C target in this step",
            "overheat_step_t": "shield-active time in the step",
            "safety_violation_t": "1 if TOP water or PCM is at the shield guard band, else 0",
            "bypass_switch_t": "1 if the mode changes into bypass at this step, else 0",
        },
        "removed_terms": "No pump-energy term: the model has only an Ergun pressure drop across the capsule bed.",
    }

    c["design_space_caveats"] = {
        "NOT_A_GLOBAL_OPTIMUM": True,
        "statement": ("The designs are the best found WITHIN the declared search bounds under a pre-declared selection rule; they "
                      "are not proven global optima."),
        "searched_bounds": {
            "capsule_inner_radius_mm": [10, 40], "pcm_volume_fraction": [0.02, 0.30],
            "flow_kg_s": [sysc["pump"]["flow_min_kg_s"], sysc["pump"]["flow_max_kg_s"]],
            "arrangement": ["single-layer", "staggered", "radial"],
        },
        "bounds_not_tested_for_assam": ("Whether the 30 % PCM-fraction cap or the 40 mm radius bound binds for Assam has not been "
                                        "read into this contract; see results/g17_* for the widened-bound diagnostic."),
        "flow_optimum_may_be_artefact": ("collector.flow_dependent_fr.enabled is FALSE, so F_R does not vary with flow; an optimum at the low "
                                         "flow bound is a model artefact, not a physical optimum."),
    }

    c["verification_status"] = {
        "simulator_verification": {"status": "RUN", "evidence": "tests/ and scripts g2/g3/g4 in this tree; see logs and results/"},
        "model_consistency_cross_check": {"status": "NOT DONE FOR ASSAM", "note": "No ANSYS/OpenFOAM case was built for Assam."},
        "experimental_validation": {"status": "NOT DONE", "scope": "Objective 4"},
        "o1_basis": ("Assam's PCM shortlist is a physics-validated ranking from Objective 1's lumped-enthalpy model "
                     "(savE OM48, OM50, OM46). Objective 1 has no confirmed-feasible K=3 MCDM ranking for Assam."),
        "wording_rule": "Say 'simulator verification' and 'experimental validation' - never 'CFD-validated'.",
    }

    c["objective_boundary"] = (
        "Objective 1 selected the PCM shortlist. Objective 2 selected the physical design (PCM identity, capsule geometry, "
        "arrangement, flow) and the validated operating envelope. OBJECTIVE 3 SELECTS THE REAL-TIME ACTION AND NOTHING ELSE. "
        "It must not change PCM identity, capsule geometry, tank volume, safety limits, or the released physics model, and must "
        "not re-cluster or merge the regimes.")

    c["provenance"] = {
        "selection": {f"g10_selection_r{k}.json": _sha(RESULTS / f"g10_selection_r{k}.json") for k in range(N_REGIMES)},
        "g10_heldout_results.csv": _sha(RESULTS / "g10_heldout_results.csv"),
        "held_out_test.lock": _sha(RESULTS / "held_out_test.lock"),
        "wp6_band.csv": _sha(RESULTS / "wp6_band.csv"),
        "configs/system_config_shared.yaml": _sha(CONFIGS / "system_config_shared.yaml"),
        f"configs/states/{STATE}.yaml": _sha(CONFIGS / "states" / f"{STATE}.yaml"),
        "configs/design_space.yaml": _sha(CONFIGS / "design_space.yaml"),
        "generic_blocks_reused_from": str(GENERIC.relative_to(BASE)),
        "generic_blocks_reused_sha256": _sha(GENERIC),
    }

    NEW.parent.mkdir(parents=True, exist_ok=True)
    NEW.write_text(json.dumps(c, indent=1, default=str), encoding="utf-8")
    return NEW


if __name__ == "__main__":
    p = build()
    print(f"written {p}  ({p.stat().st_size:,} bytes)")
