"""
src/handoff/build_obj3_contract.py
======================================
Phase 8 / D2.9 — Objective 3 environment contract, per the framework doc
§13. This is the FROZEN hand-off: Objective 3 must be able to instantiate
its training/simulation environment from this file alone, without
reopening any Objective 2 design decision (PCM identity, geometry, tank
volume, safety limits are all fixed here, not tunable by Objective 3).

Writes: results/<state>/obj3_environment_contract_<state>.json
"""

import json
import sys

import pandas as pd

from config import RESULTS_DIR
from src.io_utils import load_system_config, load_state_config, get_pcm_properties

SIMULATOR_VERSION = "sim_v1_tamilnadu"


def _design_block(state, regime, deployable_row, system_config):
    cid = regime["cluster_id"]
    pcm_id = deployable_row["pcm_id"]
    is_plain = pcm_id == "NONE_plain_tank"
    pcm_record = get_pcm_properties(state, pcm_id) if not is_plain else None

    return {
        "regime_id": int(cid),
        "regime_membership_rule": f"GMM cluster {cid} of K=5 (Objective 1, cluster_assignments_{state}.csv); "
                                   f"a new site is assigned to this regime by its max_membership_prob column",
        "selected_pcm": None if is_plain else {
            "pcm_id": pcm_id,
            "Tm_C": pcm_record["Tm_C"],
            "latent_heat_kJ_kg": pcm_record["latent_heat_kJ_kg"],
            "TC_W_mK": pcm_record["TC_W_mK"],
            "density_solid_kg_m3": pcm_record.get("density_solid_kg_m3"),
            "density_liquid_kg_m3": pcm_record.get("density_liquid_kg_m3"),
            "Cp_solid_kJ_kgK": pcm_record.get("Cp_solid_kJ_kgK"),
            "Cp_liquid_kJ_kgK": pcm_record.get("Cp_liquid_kJ_kgK"),
            "any_property_imputed": bool(pcm_record.get("any_property_imputed", False)),
        },
        "is_plain_tank_no_pcm": is_plain,
        "capsule_shape": "sphere" if not is_plain else None,
        "capsule_arrangement": "staggered" if not is_plain else None,
        "capsule_diameter_m": None if is_plain else deployable_row["capsule_diameter_m"],
        "max_pcm_conduction_distance_m": None if is_plain else deployable_row["capsule_diameter_m"] / 2.0,
        "n_capsule": 0 if is_plain else int(deployable_row["n_capsule"]),
        "pcm_mass_kg": 0.0 if is_plain else float(deployable_row["sim_pcm_mass_kg"]),
        "tank_volume_L": system_config["tank"]["volume_L"],
        "tank_insulation_m": system_config["tank"]["insulation_m"],
        "tank_U_value_W_m2K": system_config["tank"]["U_tank_W_m2K"],
        "collector_area_m2": system_config["collector"]["area_m2"],
        "collector_fr_tau_alpha": system_config["collector"]["fr_tau_alpha"],
        "collector_fr_ul_W_m2K": system_config["collector"]["fr_ul_W_m2K"],
        "heat_exchanger": "none -- direct potable-tank encapsulation (system_config_shared.yaml, pcm_integration.mode)",
        "nominal_flow_kg_s": float(deployable_row["flow_rate_kg_s"]),
        "flow_envelope_kg_s": {"min": system_config["pump"]["flow_min_kg_s"],
                                "max": system_config["pump"]["flow_max_kg_s"]},
        "pump_efficiency": system_config["pump"]["efficiency"],
        "max_pressure_bar": system_config["safety"]["max_pressure_bar"],
        "min_delivery_temp_C": system_config["delivery"]["target_temp_C"],
        "max_safe_water_temp_C": system_config["safety"]["max_water_temp_C"],
        "max_safe_pcm_temp_C": system_config["safety"]["max_pcm_temp_C"],
        "mains_temp_est_C": regime["T_mains_est_C"],
        "validated_simulator_version": SIMULATOR_VERSION,
        "performance_at_selection": {
            "useful_energy_kWh": float(deployable_row["sim_useful_energy_kWh"]),
            "solar_fraction": float(deployable_row["sim_solar_fraction"]),
            "unmet_energy_kWh": float(deployable_row["sim_unmet_energy_kWh"]),
            "constraint_margin_C": float(deployable_row["constraint_margin_C"]),
        },
    }


def _dynamic_state_schema():
    return {
        "description": "One observation per control timestep. Fields marked "
                        "measurable=false need an estimator (energy-balance + "
                        "calibrated melt-fraction observer), not a raw sensor.",
        "fields": [
            {"name": "I_t", "unit": "W/m2", "measurable": True, "source": "pyranometer or weather feed"},
            {"name": "T_amb_t", "unit": "C", "measurable": True, "source": "ambient sensor"},
            {"name": "T_water_t", "unit": "C", "measurable": True, "source": "tank thermocouple"},
            {"name": "T_pcm_t", "unit": "C", "measurable": False, "source": "estimator (no direct PCM sensor assumed)"},
            {"name": "f_melt_t", "unit": "fraction [0,1]", "measurable": False, "source": "estimator, derived from T_pcm_t via the frozen enthalpy model"},
            {"name": "H_pcm_t", "unit": "J/kg", "measurable": False, "source": "estimator (integral of Q_pcm)"},
            {"name": "T_in_t", "unit": "C", "measurable": True, "source": "mains/inlet sensor"},
            {"name": "T_out_t", "unit": "C", "measurable": True, "source": "delivery-point sensor"},
            {"name": "D_t", "unit": "kg/s or L", "measurable": True, "source": "flow meter at the draw-off point"},
            {"name": "t_day", "unit": "hour of day [0,24)", "measurable": True, "source": "clock"},
            {"name": "d_season", "unit": "categorical/cyclical encoding", "measurable": True, "source": "calendar"},
            {"name": "mdot_t", "unit": "kg/s", "measurable": True, "source": "commanded/measured pump flow"},
            {"name": "dp_t", "unit": "Pa", "measurable": True, "source": "differential pressure sensor or Ergun estimate from mdot_t"},
            {"name": "E_unmet_t", "unit": "kWh (cumulative)", "measurable": False, "source": "estimator, from T_out_t vs delivery target"},
            {"name": "mode_t", "unit": "categorical {charge, discharge, bypass}", "measurable": True, "source": "controller's own last commanded mode"},
        ],
    }


def _action_space():
    return {
        "discrete_version": {
            "actions": ["charge", "discharge", "bypass"],
            "note": "simulator applies a validated flow-rate and valve command for each mode",
        },
        "hybrid_version": {
            "mode": ["charge", "discharge", "bypass"],
            "continuous": {"flow_rate_kg_s": "within this regime's flow_envelope_kg_s above"},
            "note": "preferred if hardware can modulate pump/valve continuously -- this project's pump "
                    "range (0.010-0.050 kg/s) is continuous, so the hybrid version is RECOMMENDED",
        },
        "recommended": "hybrid_version",
        "hard_rule": "the controller must never command a flow or temperature outside this regime's "
                     "flow_envelope_kg_s / max_safe_water_temp_C / max_safe_pcm_temp_C -- the safety "
                     "shield below overrides the policy if it tries",
    }


GUARD_BAND_C = 3.0   # precautionary margin below the hard safety limits (see docstring below)


def _safety_shield(system_config):
    max_water = system_config["safety"]["max_water_temp_C"]
    max_pcm = system_config["safety"]["max_pcm_temp_C"]
    water_bypass_trigger = max_water - GUARD_BAND_C
    pcm_bypass_trigger = max_pcm - GUARD_BAND_C
    return [
        {"condition": f"T_water_t >= {water_bypass_trigger} C (precautionary, {GUARD_BAND_C} C below the "
                       f"{max_water} C hard limit -- tripping exactly AT the hard limit risks overshoot from "
                       f"sensor/control lag, per Phase 8's own P(temp-safe) results showing this margin matters)",
         "action": "force bypass, stop collector circulation"},
        {"condition": f"T_pcm_t >= {pcm_bypass_trigger} C (PCM regimes only, {GUARD_BAND_C} C below the "
                       f"{max_pcm} C hard limit)",
         "action": "force bypass/discharge, stop charging"},
        {"condition": "dp_t or estimated pressure > max_pressure_bar", "action": "force bypass, reduce flow to minimum"},
        {"condition": "commanded flow outside flow_envelope_kg_s", "action": "clip to nearest bound before executing"},
        {"condition": "dry-run (pump commanded on, flow sensor reads ~0)", "action": "stop pump, raise fault"},
        {"condition": "sensor failure / missing reading for a required field", "action": "fall back to bypass (safe default), raise fault"},
    ]


def _global_limits(system_config):
    """Shared-across-regimes summary block -- the same values already
    appear inside each regime's static_design_per_regime entry, but
    Objective 3 code that just needs "the" safety/flow envelope (rather
    than iterating every regime) can read this one block instead."""
    return {
        "delivery_target_C": system_config["delivery"]["target_temp_C"],
        "max_safe_water_temp_C": system_config["safety"]["max_water_temp_C"],
        "max_safe_pcm_temp_C": system_config["safety"]["max_pcm_temp_C"],
        "max_pressure_bar": system_config["safety"]["max_pressure_bar"],
        "irradiance_cutoff_Wm2": system_config["collector"]["min_irradiance_cutoff_Wm2"],
        "flow_envelope_kg_s": {"min": system_config["pump"]["flow_min_kg_s"],
                                "max": system_config["pump"]["flow_max_kg_s"]},
    }


def _deferred_future_work():
    return [
        "Full four-state comparison (Assam, Uttarakhand not yet run through this pipeline)",
        "Active-learning optimization loop / full NSGA-II Pareto search (Phase 7 here is a single "
        "surrogate-scored search pass, not an iterative refine-and-repeat loop)",
        "Full-draw robustness with a genuine alternate weather series (Phase 8 uses a medoid + "
        "statistical noise proxy -- no second real measured weather year exists for this project)",
        "Widened design bounds to reach the documented 15-20% PCM-volume levels (currently capped "
        "at ~12.9% by the frozen capsule diameter/count bounds -- see "
        "docs_objective2/02_PHASE2_GEOMETRY_CONSTRAINTS.md)",
        "Experimental (hardware) validation of the simulator against a physical lab rig (Objective 4 scope)",
    ]


def _reset_scenarios(system_config):
    return [
        {"name": "fully_solid", "initial_pcm_state": "solid",
         "initial_water_temp_C": system_config["solver"]["initial_water_temp_C"],
         "note": "matches src/simulation/tank_model.py's default cold-start condition"},
        {"name": "partially_charged", "initial_pcm_state": "mid",
         "initial_water_temp_C": system_config["solver"]["initial_water_temp_C"],
         "note": "PCM initialized at Tm_C (roughly 50% notional charge state)"},
        {"name": "fully_liquid", "initial_pcm_state": "liquid",
         "initial_water_temp_C": system_config["solver"]["initial_water_temp_C"],
         "note": "stresses discharge-heavy policies from a fully-charged start"},
    ]


def build_contract(state: str) -> dict:
    system_config = load_system_config()
    cfg = load_state_config(state)
    out_dir = RESULTS_DIR / state
    deployable = pd.read_csv(out_dir / "deployable_design_per_regime.csv")

    regimes_out = []
    for regime in cfg["regimes"]:
        row = deployable[deployable["regime_id"] == regime["cluster_id"]]
        if row.empty:
            continue
        regimes_out.append(_design_block(state, regime, row.iloc[0], system_config))

    return {
        "state": state,
        "contract_version": "obj3_contract_v1.0",
        "validated_simulator_version": SIMULATOR_VERSION,
        "source": "Objective 2 Phases 1-8 (see docs_objective2/ for full methodology and verification)",
        "global_limits": _global_limits(system_config),
        "static_design_per_regime": regimes_out,
        "dynamic_state_schema": _dynamic_state_schema(),
        "action_space": _action_space(),
        "safety_shield": _safety_shield(system_config),
        "reset_scenarios": _reset_scenarios(system_config),
        "weather_sequences": {
            "training_validation_test": "NOT YET SPLIT -- only one medoid weather year per regime exists "
                                          "(data/weather/weather_regime_<state>_cluster<k>_hourly.csv); "
                                          "Objective 3 must not assume separate train/val/test weather "
                                          "years are already prepared (40-hr cut list, see Objective 2 "
                                          "docs_objective2/09_NEXT_STEPS.md)",
        },
        "demand_profile_file": cfg["demand_profile"]["file"],
        "time_step_s": system_config["solver"]["timestep_s"],
        "reward_components_suggested": {
            "formula": "r_t = w1*Q_delivered_t - w2*E_unmet_t - w3*E_pump_t - w4*Penalty_safety_t - w5*Penalty_bypass_t",
            "weights": "NOT YET CHOSEN -- must be frozen by Objective 3 before training, per framework doc Sec 13.3",
        },
        "acceptance_test_before_drl_training": [
            "every action stays within flow_envelope_kg_s / temperature limits above",
            "charge/discharge/bypass transitions are physically valid",
            "the environment conserves energy (reuse Phase 4 Gate 1's <0.1% residual check)",
            "the safety shield cannot be bypassed by the policy",
            "the same seed reproduces the same trajectory",
            "simulator output matches this Objective 2 re-evaluation for identical actions",
        ],
        "deferred_future_work": _deferred_future_work(),
    }


def run(state: str):
    contract = build_contract(state)
    out_path = RESULTS_DIR / state / f"obj3_environment_contract_{state}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, default=str)
    print(f"Saved: {out_path}")
    return contract


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "tamilnadu"
    run(state)
