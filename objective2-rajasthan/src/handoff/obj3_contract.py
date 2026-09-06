"""
src/handoff/obj3_contract.py
===============================
Phase 8 / D2.9 — the Objective 3 environment contract
(framework doc §13). Writes results/obj3_environment_contract_rajasthan.json:
one entry per climate regime with the frozen operating envelope Objective
3's DRL controller trains against, plus a state-vector / action-space
skeleton and the safety-shield conditions.

Reads only the frozen shared config, the state config, the Phase 7
deployable selection and the Phase 8 robustness summary — computes
nothing new.
"""

import json
import sys

import pandas as pd

from config import BASE_DIR, RESULTS_DIR
from src.io_utils import load_state_config, load_system_config, load_design_bounds

DEPLOYABLE_PATH = RESULTS_DIR / "phase7_deployable_design_per_regime.csv"
ROBUSTNESS_PATH = RESULTS_DIR / "phase8_robustness.csv"
CONTRACT_PATH = RESULTS_DIR / "obj3_environment_contract_rajasthan.json"

SIM_VERSION = "sim_v1_rajasthan"


def _pcm_properties(state, pcm_id):
    if pcm_id == "NONE_plain_tank":
        return None
    df = pd.read_csv(BASE_DIR / load_state_config(state)["pcm_database_file"])
    row = df[df["name"] == pcm_id]
    if row.empty:
        return None
    keep = ["name", "Tm_C", "Tm_freezing_C", "latent_heat_kJ_kg", "density_liquid_kg_m3",
            "density_solid_kg_m3", "Cp_liquid_kJ_kgK", "Cp_solid_kJ_kgK", "TC_W_mK",
            "supercooling_K", "cycles_tested", "any_property_imputed", "source"]
    return {k: (float(row.iloc[0][k]) if isinstance(row.iloc[0][k], (int, float)) else row.iloc[0][k])
            for k in keep if k in row.columns}


def write_contract(state: str):
    cfg = load_state_config(state)
    sc = load_system_config()
    db = load_design_bounds()
    deployable = pd.read_csv(DEPLOYABLE_PATH).set_index("regime_id")
    robustness = pd.read_csv(ROBUSTNESS_PATH).set_index("regime_id")

    flow_min = db["flow_rate_kg_s"]["min"]
    flow_max = db["flow_rate_kg_s"]["max"]

    regimes_out = []
    for regime in cfg["regimes"]:
        cid = int(regime["cluster_id"])
        dep = deployable.loc[cid]
        rob = robustness.loc[cid]
        pcm_id = dep["pcm_id"]
        is_plain = (pcm_id == "NONE_plain_tank")

        regimes_out.append({
            "regime_id": cid,
            "label": regime["label"],
            "medoid_weather_hourly": regime["weather_hourly"],
            "T_mains_est_C": round(float(regime["T_mains_est_C"]), 3),
            "Tm_target_C": float(regime["Tm_target_C"]),
            "selected_design": {
                "pcm_id": None if is_plain else pcm_id,
                "is_plain_tank": bool(is_plain),
                "pcm_properties": _pcm_properties(state, pcm_id),
                "geometry": {
                    "capsule_shape": "sphere",
                    "capsule_arrangement": "staggered",
                    "capsule_diameter_m": round(float(dep["capsule_diameter_m"]), 5),
                    "n_capsule": int(dep["n_capsule"]),
                    "pcm_thickness_m": round(float(dep["geom_pcm_thickness_m"]), 5),
                    "pcm_volume_fraction": round(float(dep["geom_pcm_volume_fraction"]), 5),
                    "void_fraction": round(float(dep["geom_void_fraction"]), 5),
                    "tank_volume_L": sc["tank"]["volume_L"],
                    "collector_area_m2": sc["collector"]["area_m2"],
                },
                "flow_envelope_kg_s": {
                    "nominal": round(float(dep["flow_rate_kg_s"]), 5),
                    "min": flow_min,
                    "max": flow_max,
                },
            },
            "sim_confirmed_performance": {
                "useful_energy_kWh": round(float(dep["sim_useful_energy_kWh"]), 2),
                "solar_fraction": round(float(dep["sim_solar_fraction"]), 4),
                "unmet_energy_kWh": round(float(dep["sim_unmet_energy_kWh"]), 2),
                "max_water_temp_C": round(float(dep["sim_max_water_temp_C"]), 2),
                "constraint_margin_C": round(float(dep["constraint_margin_C"]), 2),
                "surrogate_vs_sim_error_pct": round(float(dep["surrogate_vs_sim_error_pct"]), 4),
            },
            "robustness": {
                "n_draws": int(rob["n_draws"]),
                "P_meet_delivery_temp": float(rob["P_meet_delivery_temp"]),
                "P_meet_annual_demand": float(rob["P_meet_annual_demand"]),
                "P_temp_safe": float(rob["P_temp_safe"]),
                "useful_energy_p5_kWh": float(rob["useful_energy_p5_kWh"]),
                "useful_energy_p95_kWh": float(rob["useful_energy_p95_kWh"]),
                "robust": bool(rob["robust"]),
            },
        })

    contract = {
        "schema": "obj3_environment_contract/v1",
        "state": state,
        "simulator_version": SIM_VERSION,
        "generated_from": {
            "deployable": DEPLOYABLE_PATH.name,
            "robustness": ROBUSTNESS_PATH.name,
            "system_config": "configs/system_config_shared.yaml",
            "design_bounds": "configs/design_bounds_shared.yaml",
            "state_config": f"configs/states/{state}.yaml",
        },
        "global_limits": {
            "delivery_temp_target_C": sc["delivery"]["target_temp_C"],
            "max_water_temp_C": sc["safety"]["max_water_temp_C"],
            "max_pcm_temp_C": sc["safety"]["max_pcm_temp_C"],
            "max_pressure_bar": sc["safety"]["max_pressure_bar"],
            "min_irradiance_cutoff_Wm2": sc["collector"]["min_irradiance_cutoff_Wm2"],
            "pump_flow_min_kg_s": sc["pump"]["flow_min_kg_s"],
            "pump_flow_max_kg_s": sc["pump"]["flow_max_kg_s"],
        },
        "control_skeleton": {
            "actions": ["charge", "discharge", "bypass"],
            "action_notes": {
                "charge": "circulate collector loop through the store (pump on, "
                          "flow in [pump_flow_min, pump_flow_max])",
                "discharge": "draw store -> load at delivery temp; collector loop off or idle",
                "bypass": "collector loop bypasses the store (pump off / diverter) — "
                          "the overheat-protection action",
            },
            "state_vector": [
                "T_water_C", "T_pcm_C", "f_melt", "GHI_Wm2", "T_amb_C",
                "hour_of_day", "draw_mass_kg_now", "T_mains_C",
                "store_energy_above_mains_kWh", "minutes_since_last_draw",
            ],
            "observation_notes": "T_pcm_C and f_melt are degenerate for the plain-tank "
                                 "regimes (no PCM); keep them in the vector for a "
                                 "state-invariant contract across future PCM-bearing states.",
            "safety_shield": {
                "force_bypass_if": f"T_water_C >= {sc['safety']['max_water_temp_C'] - 3.0} "
                                   f"(3 C guard band below the {sc['safety']['max_water_temp_C']} C limit)",
                "force_bypass_if_pcm": f"T_pcm_C >= {sc['safety']['max_pcm_temp_C'] - 3.0} "
                                       f"(PCM-bearing designs only)",
                "clamp_flow_to": f"[{sc['pump']['flow_min_kg_s']}, {sc['pump']['flow_max_kg_s']}] kg/s",
                "pump_off_below_irradiance_Wm2": sc["collector"]["min_irradiance_cutoff_Wm2"],
                "rationale": "Phase 8 robustness found P(temp-safe) well below 0.95 for every "
                             "Rajasthan regime even with the plain tank — an active bypass shield "
                             "is a hard requirement here, not an optimisation nicety.",
            },
        },
        "regimes": regimes_out,
        "deferred_future_work": [
            "multi-state comparison (Assam / Uttarakhand / Tamil Nadu under identical methodology)",
            "active-learning optimization loop (retrain-and-repeat) and full NSGA-II Pareto front",
            "full-draw robustness with real alternate member-point weather series",
            "widened design bounds to reach 15-20% PCM volume fraction (Phase-0-gate decision)",
        ],
    }

    CONTRACT_PATH.write_text(json.dumps(contract, indent=2), encoding="utf-8")
    print(f"Saved: {CONTRACT_PATH}  ({len(regimes_out)} regimes)")
    return CONTRACT_PATH


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "rajasthan"
    write_contract(state)
