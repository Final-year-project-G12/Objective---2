"""
src/robustness/monte_carlo.py
================================
Phase 8 / D2.7 — light robustness pass (framework doc §11.1, Bug-Fix 6,
reduced 40-hr spec: "100-200 Monte Carlo draws per final design with
concrete distributions ... never fewer than 50 draws").

This is Objective 2's own reference implementation of this methodology —
Tamil Nadu's Phase 8 pass (`objective2-tamilnadu/src/robustness/monte_carlo.py`)
was later aligned to match it exactly, for cross-state comparability
(`O2_Unified_PerState_Execution_Framework.md` §0.1) — see
`docs/08_PHASE8_ROBUSTNESS_HANDOFF.md`, "Alignment with Tamil Nadu".
Function/column naming below matches Tamil Nadu's aligned version
one-for-one so the two states' `phase8_robustness*.csv` files are
directly comparable column-by-column.

For each of Phase 7's deployable designs (`phase7_deployable_design_per_regime.csv`),
draws N=120 independent scenarios from:

  - PCM latent heat        : +/-10% uniform (skipped for the plain-tank baseline — no PCM to perturb)
  - Weather — GHI / T_amb  : annual scale/offset drawn from one of the 10 REAL observed years
                              (2016-2025) for this regime (src/robustness/weather_ensemble.py,
                              step 6.2 of the 2026-09-20 fix plan — replaces the earlier
                              synthetic U(0.93,1.07)/U(-1.5,+1.5) "medoid + noise" proxy),
                              jittered slightly (~1% GHI, ~0.1C T_amb) plus per-hour iid noise
                              (GHI: N(1,0.04) clipped [0.5,1.5]; T_amb: N(0,0.4) C) so the
                              within-year hourly SHAPE still comes from the single medoid
                              year's hourly file — only the annual magnitude is now real
                              inter-annual variability, not an assumed range.
  - Demand                 : +/-20% volume (uniform), +/-30 min timing shift (uniform)
  - Inlet/mains temperature: +/-2 C (uniform)

and re-runs the FULL YEAR simulator for every draw (never the surrogate —
robustness is a simulator-only analysis, via `run_case`'s
`weather_perturbation` keyword, the same override seam Phase 4's
`gates.py` uses for its own limiting-case tests, so `run_case` itself
needs no Phase-8-specific code path). Reports, per design:

  - P(meets delivery temperature) — solar_fraction >= 0.45 (fixed, state-independent)
  - P(meets annual demand)        — solar_fraction >= 0.50 (fixed, state-independent)
  - useful-energy / solar-fraction / pump-energy / PCM-mass 5th-95th percentile intervals
  - max water temperature 95th percentile
  - P(any safety-temperature violation)  — n_safety_violations > 0
  - P(exceeds max safe temperature)      — max_water_temp_C > limit, or (has PCM
                                            only) max_pcm_temp_C > limit — kept
                                            separate from the line above because they
                                            are genuinely different questions (any
                                            flagged sub-hour, vs. the reported annual
                                            max actually clearing the hard limit)

Both "meets ..." thresholds are FIXED and state-independent, not relative
to each design's own nominal value — a self-referential threshold would
let a weak nominal design look "just as robust" as a strong one purely by
having an easy bar to clear, which defeats the point of a cross-state
comparison (this is exactly the failure mode Tamil Nadu's first Phase 8
pass had, and fixed by aligning to this implementation — see docs/08).

"Robust" per the framework doc's rule of thumb: P(meets demand) >= ~75%
and P(temperature-safe) >= ~95%; otherwise reported as an explicit
caveat, never hidden.

2026-09-17: arrangement was restored as a searched variable (Phase 1-2)
and Phase 7's winners now carry a real `arrangement` column (not always
"staggered") — run_monte_carlo_for_design() reads it from the deployable
row so this Monte Carlo is re-run against the actual winning geometry,
never assumed staggered. Every regime's robustness numbers in this run are
freshly computed against Phase 7's new winners, not carried over from any
prior staggered-only run, since the geometry (and therefore thermal
margin) can differ even where the winning PCM identity is unchanged.
"""

import sys

import numpy as np
import pandas as pd

from config import RESULTS_DIR
from src.design.schema import DesignVector
from src.io_utils import (get_pcm_properties, get_regime, load_system_config, load_hourly_weather,
                           write_manifest_sidecar)
from src.simulation.run_case import run_case
from src.robustness.weather_ensemble import load_historical_ensemble

N_DRAWS = 120
MC_SEED = 20260905

# Fixed, state-independent thresholds on solar_fraction (Phase 3 doc
# definition: fraction of the ideal 300 L/day @ delivery-target demand
# actually delivered at/above that target) — deliberately NOT relative to
# each design's own nominal value, so P(meets demand) means the same
# thing for every regime and every state.
SOLAR_FRACTION_DELIVERY_THRESHOLD = 0.45
SOLAR_FRACTION_DEMAND_THRESHOLD = 0.50

DEPLOYABLE_PATH = RESULTS_DIR / "phase7_deployable_design_per_regime.csv"
ROBUSTNESS_SUMMARY_PATH = RESULTS_DIR / "phase8_robustness.csv"
ROBUSTNESS_DRAWS_PATH = RESULTS_DIR / "phase8_robustness_draws.csv"


def _sample_scenario(rng, has_pcm: bool, n_hours: int, historical_pairs) -> dict:
    # Step 6.2 of the 2026-09-20 fix plan: draw the annual GHI-scale/T_amb-
    # offset from one of the 10 REAL observed years for this cluster
    # (src/robustness/weather_ensemble.py) instead of an assumed uniform
    # range -- then jitter slightly to smooth the discrete year-support
    # into a continuous distribution (does not change the real magnitude,
    # just avoids only ever drawing exactly 10 distinct annual values
    # across N_DRAWS=120 draws).
    year_ghi_scale, year_tamb_offset_C = historical_pairs[rng.integers(0, len(historical_pairs))]
    annual_ghi_scale = year_ghi_scale * rng.normal(1.0, 0.01)
    annual_tamb_offset_C = year_tamb_offset_C + rng.normal(0.0, 0.1)

    hourly_ghi_noise = rng.normal(1.0, 0.04, size=n_hours)
    ghi_multiplier_array = np.clip(annual_ghi_scale * hourly_ghi_noise, 0.5, 1.5)

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
    cid = int(row["regime_id"])
    pcm_id = None if row["pcm_id"] == "NONE_plain_tank" else row["pcm_id"]
    design = DesignVector(float(row["capsule_diameter_m"]), int(row["n_capsule"]),
                          float(row["flow_rate_kg_s"]), capsule_arrangement=row["arrangement"])
    base_mains = get_regime(state, cid)["T_mains_est_C"]
    base_latent = get_pcm_properties(state, pcm_id)["latent_heat_kJ_kg"] if pcm_id else None
    n_hours = len(load_hourly_weather(state, cid))
    historical_pairs = load_historical_ensemble(state, cid)
    rng = np.random.default_rng(seed + cid * 131)

    draws = []
    for i in range(n_draws):
        s = _sample_scenario(rng, pcm_id is not None, n_hours, historical_pairs)
        pcm_overrides = ({"latent_heat_kJ_kg": base_latent * s["latent_heat_mult"]}
                          if pcm_id is not None else None)
        out = run_case(
            state, cid, pcm_id, design, record_hourly=True,
            volume_multiplier=s["demand_multiplier"], timing_shift_hours=s["timing_shift_hours"],
            mains_temp_override_C=base_mains + s["mains_delta_C"],
            pcm_record_overrides=pcm_overrides,
            weather_perturbation={"ghi_multiplier": s["ghi_multiplier_array"],
                                   "tamb_delta_C": s["tamb_delta_array"]},
        )
        rec = {
            "draw": i, "regime_id": cid, "pcm_id": row["pcm_id"], "valid": out["valid"],
            "latent_heat_mult": s["latent_heat_mult"], "annual_ghi_scale": s["annual_ghi_scale"],
            "annual_tamb_offset_C": s["annual_tamb_offset_C"], "demand_multiplier": s["demand_multiplier"],
            "timing_shift_hours": s["timing_shift_hours"], "mains_delta_C": s["mains_delta_C"],
        }
        if out["valid"]:
            rec.update(out["metrics"])
        draws.append(rec)

    return pd.DataFrame(draws)


def summarize_design(row: pd.Series, draws: pd.DataFrame, system_config: dict) -> dict:
    max_water_limit = system_config["safety"]["max_water_temp_C"]
    max_pcm_limit = system_config["safety"]["max_pcm_temp_C"]
    has_pcm = row["pcm_id"] != "NONE_plain_tank"

    p_meets_delivery = float((draws["solar_fraction"] >= SOLAR_FRACTION_DELIVERY_THRESHOLD).mean())
    p_meets_demand = float((draws["solar_fraction"] >= SOLAR_FRACTION_DEMAND_THRESHOLD).mean())
    p_temp_violation = float((draws["n_safety_violations"] > 0).mean())
    # For a plain-tank design (no PCM), tank_model.py sets T_pcm = T_w exactly
    # (there is no PCM to have its own temperature) — so checking max_pcm_temp_C
    # against the PCM-specific 65 C limit for those rows would wrongly flag
    # ordinary hot water (which only needs to respect the 75 C water limit) as
    # a "PCM over-temperature". Only apply the PCM check when the design
    # actually has PCM in it.
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
    n_draws = max(int(n_draws), 50)   # framework doc: never fewer than 50
    deployable = pd.read_csv(DEPLOYABLE_PATH)
    system_config = load_system_config()

    print(f"Phase 8 robustness: {n_draws} Monte Carlo draws x {len(deployable)} regimes "
          f"(sources: weather+noise, demand volume, demand timing, mains temp"
          f"{', PCM latent heat' if (deployable['pcm_id'] != 'NONE_plain_tank').any() else ''})")

    all_draws, summaries = [], []
    for _, row in deployable.iterrows():
        print(f"  regime {row['regime_id']} ({row['pcm_id']}), {n_draws} draws ...")
        draws = run_monte_carlo_for_design(state, row, n_draws=n_draws)
        all_draws.append(draws)
        summary = summarize_design(row, draws[draws["valid"]], system_config)
        summaries.append(summary)
        print(f"    P(meets delivery)={summary['p_meets_delivery_temp']:.2f}  "
              f"P(meets demand)={summary['p_meets_annual_demand']:.2f}  "
              f"P(temp-safe)={1 - summary['p_temperature_violation']:.2f}  "
              f"robust={summary['robust_per_framework_rule']}")

    draws_df = pd.concat(all_draws, ignore_index=True)
    summary_df = pd.DataFrame(summaries)

    draws_df.to_csv(ROBUSTNESS_DRAWS_PATH, index=False)
    summary_df.to_csv(ROBUSTNESS_SUMMARY_PATH, index=False)
    print(f"\nSaved: {ROBUSTNESS_SUMMARY_PATH}  ({len(summary_df)} rows)")
    print(f"Saved: {ROBUSTNESS_DRAWS_PATH}  ({len(draws_df)} rows)")
    write_manifest_sidecar(ROBUSTNESS_SUMMARY_PATH, state,
                            extra={"n_draws": n_draws, "weather_source": "historical_ensemble"})
    return draws_df, summary_df


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "rajasthan"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else N_DRAWS
    run_all(state, n)
