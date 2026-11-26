"""
src/robustness/monte_carlo.py
================================
Phase 8 / D2.7 — light robustness pass for Objective 2 (Assam).
Applies 100–200 Monte Carlo draws per final deployable regime design.

Uncertainty distributions:
  1. PCM latent heat        : +/-10% uniform (0.90 to 1.10 x nominal)
  2. Weather — GHI / Tamb   : medoid + noise (annual scale ~ U(0.93, 1.07),
                               hourly GHI ~ N(1, 0.04) clipped [0.5, 1.5];
                               Tamb annual offset ~ U(-1.5, 1.5) C + hourly noise N(0, 0.4) C)
  3. Demand                 : +/-20% volume (uniform), +/-30 min timing shift (uniform)
  4. Inlet/mains temperature: +/-2 C (uniform)

Decision rule:
  Robust if P(meets annual demand) >= 0.75 and P(temp-safe) >= 0.95.
  Otherwise CAVEAT / NOT ROBUST (reported explicitly, never hidden).

Outputs:
  results/phase8_robustness.csv
  results/phase8_robustness_draws.csv
"""

import sys
import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from config import RESULTS_DIR
from src.design.schema import DesignVector
from src.io_utils import get_pcm_properties, get_regime, load_system_config, load_hourly_weather
from src.simulation.run_case import run_case

N_DRAWS = 100
MC_SEED = 20260912
N_JOBS = 6

SOLAR_FRACTION_DELIVERY_THRESHOLD = 0.45
SOLAR_FRACTION_DEMAND_THRESHOLD = 0.50

DEPLOYABLE_PATH = RESULTS_DIR / "phase7_deployable_design_per_regime.csv"
ROBUSTNESS_SUMMARY_PATH = RESULTS_DIR / "phase8_robustness.csv"
ROBUSTNESS_DRAWS_PATH = RESULTS_DIR / "phase8_robustness_draws.csv"


def _sample_scenario(rng, has_pcm: bool, n_hours: int) -> dict:
    annual_ghi_scale = rng.uniform(0.93, 1.07)
    hourly_ghi_noise = rng.normal(1.0, 0.04, size=n_hours)
    ghi_multiplier_array = np.clip(annual_ghi_scale * hourly_ghi_noise, 0.5, 1.5)

    annual_tamb_offset_C = rng.uniform(-1.5, 1.5)
    hourly_tamb_noise_C = rng.normal(0.0, 0.4, size=n_hours)
    tamb_delta_array = annual_tamb_offset_C + hourly_tamb_noise_C

    return {
        "latent_heat_mult": rng.uniform(0.90, 1.10) if has_pcm else None,
        "annual_ghi_scale": float(annual_ghi_scale),
        "annual_tamb_offset_C": float(annual_tamb_offset_C),
        "ghi_multiplier_array": ghi_multiplier_array,
        "tamb_delta_array": tamb_delta_array,
        "demand_multiplier": rng.uniform(0.80, 1.20),
        "timing_shift_hours": rng.uniform(-0.5, 0.5),
        "mains_delta_C": rng.uniform(-2.0, 2.0),
    }


def _run_single_draw_job(args):
    (i, s, state, cid, pcm_id, pcm_name, design_dict, base_mains, base_latent, record_hourly) = args

    design = DesignVector(
        design_dict["capsule_diameter_m"],
        design_dict["n_capsule"],
        design_dict["flow_rate_kg_s"]
    )

    pcm_overrides = ({"latent_heat_kJ_kg": base_latent * s["latent_heat_mult"]}
                      if pcm_id is not None else None)
    out = run_case(
        state, cid, pcm_id, design, record_hourly=record_hourly,
        volume_multiplier=s["demand_multiplier"], timing_shift_hours=s["timing_shift_hours"],
        mains_temp_override_C=base_mains + s["mains_delta_C"],
        pcm_record_overrides=pcm_overrides,
        weather_perturbation={"ghi_multiplier": s["ghi_multiplier_array"],
                               "tamb_delta_C": s["tamb_delta_array"]},
    )
    rec = {
        "draw": i, "regime_id": cid, "pcm_id": pcm_name, "valid": out["valid"],
        "latent_heat_mult": s["latent_heat_mult"], "annual_ghi_scale": s["annual_ghi_scale"],
        "annual_tamb_offset_C": s["annual_tamb_offset_C"], "demand_multiplier": s["demand_multiplier"],
        "timing_shift_hours": s["timing_shift_hours"], "mains_delta_C": s["mains_delta_C"],
    }
    if out["valid"]:
        rec.update(out["metrics"])
    return rec


def run_monte_carlo_for_design(state: str, row: pd.Series, n_draws: int = N_DRAWS,
                                seed: int = MC_SEED, n_jobs: int = N_JOBS) -> pd.DataFrame:
    cid = int(row["regime_id"])
    pcm_id = None if row["pcm_id"] == "NONE_plain_tank" else row["pcm_id"]
    design_dict = {
        "capsule_diameter_m": float(row["capsule_diameter_m"]),
        "n_capsule": int(row["n_capsule"]),
        "flow_rate_kg_s": float(row["flow_rate_kg_s"]),
    }
    base_mains = get_regime(state, cid)["T_mains_est_C"]
    base_latent = get_pcm_properties(state, pcm_id)["latent_heat_kJ_kg"] if pcm_id else None
    n_hours = len(load_hourly_weather(state, cid))
    rng = np.random.default_rng(seed + cid * 131)

    tasks = []
    for i in range(n_draws):
        s = _sample_scenario(rng, pcm_id is not None, n_hours)
        tasks.append((i, s, state, cid, pcm_id, row["pcm_id"], design_dict, base_mains, base_latent, False))

    draws = Parallel(n_jobs=n_jobs)(delayed(_run_single_draw_job)(task) for task in tasks)
    return pd.DataFrame(draws)


def summarize_design(state: str, row: pd.Series, draws: pd.DataFrame, system_config: dict) -> dict:
    max_water_limit = system_config["safety"]["max_water_temp_C"]
    max_pcm_limit = system_config["safety"]["max_pcm_temp_C"]
    delivery_target_C = system_config["delivery"]["target_temp_C"]
    has_pcm = row["pcm_id"] != "NONE_plain_tank"

    pcm_record = get_pcm_properties(state, row["pcm_id"]) if has_pcm else None
    nominal_latent = pcm_record["latent_heat_kJ_kg"] if pcm_record is not None else 0.0

    p_meets_delivery = float((draws["solar_fraction"] >= SOLAR_FRACTION_DELIVERY_THRESHOLD).mean())
    p_meets_demand = float((draws["solar_fraction"] >= SOLAR_FRACTION_DEMAND_THRESHOLD).mean())
    p_temp_violation = float((draws["n_safety_violations"] > 0).mean())
    p_temp_safe = 1.0 - p_temp_violation

    if has_pcm:
        p_exceeds_max_safe = float(
            ((draws["max_water_temp_C"] > max_water_limit) | (draws["max_pcm_temp_C"] > max_pcm_limit)).mean()
        )
    else:
        p_exceeds_max_safe = float((draws["max_water_temp_C"] > max_water_limit).mean())

    ue_lo, ue_mid, ue_hi = draws["useful_energy_kWh"].quantile([0.05, 0.50, 0.95])
    sf_lo, sf_hi = draws["solar_fraction"].quantile([0.05, 0.95])
    pump_lo, pump_hi = draws["pump_energy_kWh"].quantile([0.05, 0.95])
    mass_lo, mass_hi = draws["pcm_mass_kg"].quantile([0.05, 0.95])
    max_water_p95 = draws["max_water_temp_C"].quantile(0.95)

    demand_pass = p_meets_demand >= 0.75
    safety_pass = p_temp_safe >= 0.95
    robust = demand_pass and safety_pass

    if robust:
        status = "ROBUST"
        caveat = "None — meets demand and temperature-safety thresholds"
    else:
        status = "CAVEAT / NOT ROBUST"
        fails = []
        if not demand_pass:
            fails.append(f"P(demand)={p_meets_demand:.2f} < 0.75")
        if not safety_pass:
            fails.append(f"P(temp-safe)={p_temp_safe:.2f} < 0.95")
        caveat = "Failed thresholds: " + "; ".join(fails)

    return {
        "state": state,
        "regime_id": int(row["regime_id"]),
        "pcm_id": row["pcm_id"],
        "n_draws": len(draws),
        "weather_source": "medoid + noise",
        "nominal_latent_heat_kJ_kg": nominal_latent,
        "demand_nominal_L_day": 100.0,
        "delivery_target_temp_C": delivery_target_C,
        "max_water_temp_limit_C": max_water_limit,
        "max_pcm_temp_limit_C": max_pcm_limit,
        "p_meets_delivery_temp": p_meets_delivery,
        "p_meets_annual_demand": p_meets_demand,
        "p_temperature_violation": p_temp_violation,
        "p_temp_safe": p_temp_safe,
        "p_exceeds_max_safe_temp": p_exceeds_max_safe,
        "useful_energy_p05_kWh": ue_lo,
        "useful_energy_p50_kWh": ue_mid,
        "useful_energy_p95_kWh": ue_hi,
        "solar_fraction_p05": sf_lo,
        "solar_fraction_p95": sf_hi,
        "pump_energy_p05_kWh": pump_lo,
        "pump_energy_p95_kWh": pump_hi,
        "pcm_mass_p05_kg": mass_lo,
        "pcm_mass_p95_kg": mass_hi,
        "max_water_temp_p95_C": max_water_p95,
        "robust_per_framework_rule": robust,
        "robustness_status": status,
        "caveat_reason": caveat,
    }


def run_all(state: str, n_draws: int = N_DRAWS, n_jobs: int = N_JOBS):
    n_draws = max(int(n_draws), 50)   # framework doc: never fewer than 50
    deployable = pd.read_csv(DEPLOYABLE_PATH)
    if "selection_role" in deployable.columns:
        optimal_mask = deployable["selection_role"].str.contains("Optimal", na=False)
        if optimal_mask.any():
            deployable = deployable[optimal_mask]
    deployable = deployable.drop_duplicates(subset=["regime_id"], keep="first")
    system_config = load_system_config()

    print(f"Phase 8 robustness: {n_draws} Monte Carlo draws x {len(deployable)} regimes "
          f"(sources: weather+noise, demand volume, demand timing, mains temp"
          f"{', PCM latent heat' if (deployable['pcm_id'] != 'NONE_plain_tank').any() else ''})")

    all_draws, summaries = [], []
    for _, row in deployable.iterrows():
        print(f"  regime {row['regime_id']} ({row['pcm_id']}), {n_draws} draws (parallel jobs={n_jobs}) ...")
        draws = run_monte_carlo_for_design(state, row, n_draws=n_draws, n_jobs=n_jobs)
        all_draws.append(draws)
        summary = summarize_design(state, row, draws[draws["valid"]], system_config)
        summaries.append(summary)
        print(f"    P(meets delivery)={summary['p_meets_delivery_temp']:.2f}  "
              f"P(meets demand)={summary['p_meets_annual_demand']:.2f}  "
              f"P(temp-safe)={summary['p_temp_safe']:.2f}  "
              f"status={summary['robustness_status']}")

    draws_df = pd.concat(all_draws, ignore_index=True)
    summary_df = pd.DataFrame(summaries)

    draws_df.to_csv(ROBUSTNESS_DRAWS_PATH, index=False)
    summary_df.to_csv(ROBUSTNESS_SUMMARY_PATH, index=False)
    print(f"\nSaved: {ROBUSTNESS_SUMMARY_PATH}  ({len(summary_df)} rows)")
    print(f"Saved: {ROBUSTNESS_DRAWS_PATH}  ({len(draws_df)} rows)")
    return draws_df, summary_df


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "assam"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else N_DRAWS
    run_all(state, n)
