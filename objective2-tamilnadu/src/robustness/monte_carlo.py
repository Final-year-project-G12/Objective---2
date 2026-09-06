"""
src/robustness/monte_carlo.py
================================
Phase 8 / D2.7 — light robustness analysis (framework doc, reduced 40-hr
spec: "100-200 Monte Carlo draws per final design with concrete
distributions ... never fewer than 50 draws").

METHODOLOGY NOTE (aligned to the Rajasthan implementation of this same
framework, for cross-state comparability — see
docs_objective2/10_PHASE8_ROBUSTNESS_HANDOFF.md "Alignment with
Rajasthan" section for what changed and why): weather noise is two-level
(an annual scale/offset PLUS independent per-hour noise, not a single
constant multiplier for the whole year), and the two "meets ..."
probabilities are defined on FIXED, state-independent solar_fraction
thresholds rather than thresholds relative to each design's own nominal
value — a self-referential threshold would let a poorly-performing
nominal design look "just as robust" as a strong one purely by having a
low bar to clear, which defeats the point of a cross-state comparison.

For each of the 5 deployable designs selected in Phase 7
(`deployable_design_per_regime.csv`), draws N=120 independent scenarios
from:

  - PCM latent heat        : +/-10% uniform                  (skipped for the plain-tank baseline -- no PCM to perturb)
  - Weather                : annual GHI scale ~ U(0.93, 1.07) x per-hour
                              iid noise ~ N(1, 0.04); annual T_amb offset
                              ~ U(-1.5, +1.5) C + per-hour iid noise
                              ~ N(0, 0.4) C -- "medoid + noise" proxy for
                              an unseen weather year, since no
                              member-point weather file exists for this
                              project (40-hr cut list)
  - Demand                 : +/-20% volume (uniform), +/-30 min timing shift (uniform)
  - Inlet/mains temperature : +/-2 C (uniform)

and re-runs the FULL YEAR simulator for every draw (never the surrogate --
robustness is a simulator-only analysis). Reports, per design:

  - P(meets delivery temperature) -- solar_fraction >= 0.45 (fixed)
  - P(meets annual demand)        -- solar_fraction >= 0.50 (fixed)
  - useful-energy 5th/50th/95th percentile interval
  - solar-fraction 5th-95th percentile interval
  - max water temperature 95th percentile
  - P(any safety-temperature violation) -- n_safety_violations > 0
  - P(exceeds max safe temperature)      -- max_water_temp_C > limit or
                                             (has PCM) max_pcm_temp_C > limit

"Robust" per the framework doc's rule of thumb: P(meets demand) >= ~75%
and P(temperature-safe) >= ~95%; otherwise reported as an explicit caveat,
never hidden.
"""

import sys

import numpy as np
import pandas as pd

from config import RESULTS_DIR
from src.design.schema import DesignVector
from src.io_utils import get_pcm_properties, load_system_config, load_hourly_weather
from src.simulation.run_case import run_case

N_DRAWS = 120
MC_SEED = 20260905

# Fixed, state-independent thresholds on solar_fraction (Phase 3 doc
# definition: fraction of the ideal 300 L/day @ delivery-target demand
# actually delivered at/above that target) -- deliberately NOT relative
# to each design's own nominal value, so P(meets demand) means the same
# thing for every regime and every state.
SOLAR_FRACTION_DELIVERY_THRESHOLD = 0.45
SOLAR_FRACTION_DEMAND_THRESHOLD = 0.50


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


def run_monte_carlo_for_design(state: str, row: pd.Series, n_draws: int = N_DRAWS,
                                seed: int = MC_SEED) -> pd.DataFrame:
    pcm_id = None if row["pcm_id"] == "NONE_plain_tank" else row["pcm_id"]
    design = DesignVector(row["capsule_diameter_m"], int(row["n_capsule"]), row["flow_rate_kg_s"])
    base_mains = row["sim_mains_temp_C"] if "sim_mains_temp_C" in row and pd.notna(row.get("sim_mains_temp_C")) else None
    if base_mains is None:
        from src.io_utils import get_regime
        base_mains = get_regime(state, int(row["regime_id"]))["T_mains_est_C"]

    base_latent = get_pcm_properties(state, pcm_id)["latent_heat_kJ_kg"] if pcm_id else None
    n_hours = len(load_hourly_weather(state, int(row["regime_id"])))
    rng = np.random.default_rng(seed + int(row["regime_id"]) * 131)

    draws = []
    for i in range(n_draws):
        s = _sample_scenario(rng, pcm_id is not None, n_hours)
        pcm_overrides = ({"latent_heat_kJ_kg": base_latent * s["latent_heat_mult"]}
                          if pcm_id is not None else None)
        out = run_case(
            state, int(row["regime_id"]), pcm_id, design, record_hourly=True,
            volume_multiplier=s["demand_multiplier"], timing_shift_hours=s["timing_shift_hours"],
            mains_temp_override_C=base_mains + s["mains_delta_C"],
            pcm_record_overrides=pcm_overrides,
            weather_perturbation={"ghi_multiplier": s["ghi_multiplier_array"],
                                   "tamb_delta_C": s["tamb_delta_array"]},
        )
        rec = {
            "draw": i, "regime_id": row["regime_id"], "pcm_id": row["pcm_id"], "valid": out["valid"],
            "latent_heat_mult": s["latent_heat_mult"], "annual_ghi_scale": s["annual_ghi_scale"],
            "annual_tamb_offset_C": s["annual_tamb_offset_C"], "demand_multiplier": s["demand_multiplier"],
            "timing_shift_hours": s["timing_shift_hours"], "mains_delta_C": s["mains_delta_C"],
        }
        if out["valid"]:
            rec.update(out["metrics"])
        draws.append(rec)

    return pd.DataFrame(draws)


def summarize_design(state: str, row: pd.Series, draws: pd.DataFrame, system_config: dict) -> dict:
    max_water_limit = system_config["safety"]["max_water_temp_C"]
    max_pcm_limit = system_config["safety"]["max_pcm_temp_C"]
    has_pcm = row["pcm_id"] != "NONE_plain_tank"

    p_meets_delivery = float((draws["solar_fraction"] >= SOLAR_FRACTION_DELIVERY_THRESHOLD).mean())
    p_meets_demand = float((draws["solar_fraction"] >= SOLAR_FRACTION_DEMAND_THRESHOLD).mean())
    p_temp_violation = float((draws["n_safety_violations"] > 0).mean())
    # NOTE: for a plain-tank design (no PCM), tank_model.py sets T_pcm = T_w
    # exactly (there is no PCM to have its own temperature) -- so checking
    # max_pcm_temp_C against the PCM-specific 65 C limit for those rows would
    # wrongly flag ordinary hot water (which only needs to respect the 75 C
    # water limit) as a "PCM over-temperature". Only apply the PCM check
    # when the design actually has PCM in it.
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

    robust = (p_meets_demand >= 0.75) and ((1 - p_temp_violation) >= 0.95)

    return {
        "regime_id": row["regime_id"], "pcm_id": row["pcm_id"], "n_draws": len(draws),
        "p_meets_delivery_temp": p_meets_delivery, "p_meets_annual_demand": p_meets_demand,
        "p_temperature_violation": p_temp_violation, "p_exceeds_max_safe_temp": p_exceeds_max_safe,
        "useful_energy_p05_kWh": ue_lo, "useful_energy_p50_kWh": ue_mid, "useful_energy_p95_kWh": ue_hi,
        "solar_fraction_p05": sf_lo, "solar_fraction_p95": sf_hi,
        "pump_energy_p05_kWh": pump_lo, "pump_energy_p95_kWh": pump_hi,
        "pcm_mass_p05_kg": mass_lo, "pcm_mass_p95_kg": mass_hi,
        "max_water_temp_p95_C": max_water_p95,
        "robust_per_framework_rule": robust,
    }


def run_all(state: str, n_draws: int = N_DRAWS):
    out_dir = RESULTS_DIR / state
    deployable = pd.read_csv(out_dir / "deployable_design_per_regime.csv")
    system_config = load_system_config()

    all_draws, summaries = [], []
    for _, row in deployable.iterrows():
        print(f"Monte Carlo: regime {row['regime_id']} ({row['pcm_id']}), {n_draws} draws ...")
        draws = run_monte_carlo_for_design(state, row, n_draws=n_draws)
        all_draws.append(draws)
        summary = summarize_design(state, row, draws[draws["valid"]], system_config)
        summaries.append(summary)
        print(f"  P(meets delivery)={summary['p_meets_delivery_temp']:.2f}  "
              f"P(meets demand)={summary['p_meets_annual_demand']:.2f}  "
              f"P(temp-safe)={1-summary['p_temperature_violation']:.2f}  "
              f"robust={summary['robust_per_framework_rule']}")

    draws_df = pd.concat(all_draws, ignore_index=True)
    summary_df = pd.DataFrame(summaries)

    draws_df.to_csv(out_dir / "robustness_results.csv", index=False)
    summary_df.to_csv(out_dir / "robustness_summary.csv", index=False)
    print(f"\nSaved: {out_dir / 'robustness_results.csv'} ({len(draws_df)} rows)")
    print(f"Saved: {out_dir / 'robustness_summary.csv'} ({len(summary_df)} rows)")
    return draws_df, summary_df


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "tamilnadu"
    run_all(state)
