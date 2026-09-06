"""
src/robustness/monte_carlo.py
================================
Phase 8 / D2.7 — light robustness pass (framework doc §11.1, Bug-Fix 6).

For each regime's Phase 7 deployable design
(results/phase7_deployable_design_per_regime.csv), run N Monte Carlo draws
with concrete perturbation distributions and report:
  - P(meet delivery temp)
  - P(meet annual demand)
  - useful-energy 5th-95th percentile interval
  - P(any safety-temperature violation)

Perturbation sources covered (framework doc lists 5; we cover the 4 that
apply to Rajasthan's selected designs):
  1. Weather — medoid hourly series + noise. No alternate member-point
     weather file exists for Rajasthan (Objective 1 shipped medoid-only,
     see docs/00), so "medoid + noise" per the framework's own fallback:
     an annual GHI scale ~ U(0.93, 1.07) and per-hour iid N(1, 0.04) on
     GHI; an annual ambient offset ~ U(-1.5, +1.5) C and per-hour iid
     N(0, 0.4) C on T_amb.
  2. Demand volume — volume_multiplier ~ U(0.80, 1.20)  (+/-20%).
  3. Demand timing — timing_shift_hours ~ U(-0.5, +0.5) (+/-30 min).
  4. Inlet/mains temperature — T_mains_est_C + U(-2, +2) C.
  5. PCM latent heat +/-10% — NOT APPLICABLE: every Phase 7 deployable
     design is the plain (no-PCM) tank, so there is no latent heat to
     perturb. Applied automatically if a future selection picks a real
     PCM; stated here rather than silently dropped.

Weather is injected by temporarily wrapping io_utils.load_hourly_weather
(the same seam gates.py uses for config overrides) so run_case stays
byte-identical and every reported metric is computed by run_case's own
code path -- the robustness numbers are therefore directly comparable to
the Phase 7 sim_* columns.

Never fewer than 50 draws (framework doc). Default 120 (100-200 band).
Robust if P(meet annual demand) >= ~0.75 AND P(temp-safe) >= ~0.95;
otherwise reported as a caveat, not hidden.
"""

import sys

import numpy as np
import pandas as pd

from config import RESULTS_DIR
import src.simulation.run_case as _run_case_mod
from src.simulation.run_case import run_case
from src.io_utils import load_system_config, get_regime, load_hourly_weather as _load_hourly_weather_orig

N_DRAWS_DEFAULT = 120
MC_SEED = 20260905

# Operational thresholds for the two "meet ..." probabilities (project
# assumptions -- stated in docs/08). No hourly demand-vs-supply match is
# attempted here; both key off run_case's solar_fraction, which is defined
# (Phase 3 doc) as "fraction of the ideal 300 L/day @ 45 C demand actually
# delivered at or above the 45 C target" -- i.e. it is already a
# delivery-temperature-weighted demand-met fraction.
DELIVERY_TEMP_SOLAR_FRACTION = 0.45   # >= 45% of the annual draw delivered at >= 45 C
ANNUAL_DEMAND_SOLAR_FRACTION = 0.50   # design supplies >= 50% of ideal annual demand from solar

DEPLOYABLE_PATH = RESULTS_DIR / "phase7_deployable_design_per_regime.csv"
ROBUSTNESS_PATH = RESULTS_DIR / "phase8_robustness.csv"
DRAWS_PATH = RESULTS_DIR / "phase8_robustness_draws.csv"   # every draw, for audit


def _perturbed_weather(state, cluster_id, rng):
    df = _load_hourly_weather_orig(state, cluster_id).copy()
    n = len(df)
    ghi_scale = rng.uniform(0.93, 1.07)
    ghi_hour = rng.normal(1.0, 0.04, n).clip(min=0.0)
    df["GHI_Wm2"] = (df["GHI_Wm2"].to_numpy() * ghi_scale * ghi_hour).clip(min=0.0)
    ta_offset = rng.uniform(-1.5, 1.5)
    ta_hour = rng.normal(0.0, 0.4, n)
    df["T_amb_C"] = df["T_amb_C"].to_numpy() + ta_offset + ta_hour
    return df


def _one_draw(state, dep_row, rng, system_config):
    cid = int(dep_row["regime_id"])
    pcm_id = None if dep_row["pcm_id"] == "NONE_plain_tank" else dep_row["pcm_id"]
    design = _run_case_mod.DesignVector(float(dep_row["capsule_diameter_m"]),
                                        int(dep_row["n_capsule"]),
                                        float(dep_row["flow_rate_kg_s"]))

    vol_mult = rng.uniform(0.80, 1.20)
    timing_shift = rng.uniform(-0.5, 0.5)
    mains_base = get_regime(state, cid)["T_mains_est_C"]
    mains = mains_base + rng.uniform(-2.0, 2.0)

    pcm_over = None
    if pcm_id is not None:
        from src.io_utils import get_pcm_properties
        base_L = get_pcm_properties(state, pcm_id)["latent_heat_kJ_kg"]
        pcm_over = {"latent_heat_kJ_kg": base_L * rng.uniform(0.90, 1.10)}

    # inject perturbed weather for this draw only
    _run_case_mod.load_hourly_weather = lambda s, c: _perturbed_weather(s, c, rng)
    try:
        out = run_case(state, cid, pcm_id, design,
                        volume_multiplier=vol_mult, timing_shift_hours=timing_shift,
                        mains_temp_override_C=mains, pcm_record_overrides=pcm_over,
                        record_hourly=True)
    finally:
        _run_case_mod.load_hourly_weather = _load_hourly_weather_orig

    if not out["valid"]:
        return None
    m = out["metrics"]
    max_water_C = system_config["safety"]["max_water_temp_C"]
    max_pcm_C = system_config["safety"]["max_pcm_temp_C"]

    delivery_ok = (m["solar_fraction"] is not None
                    and m["solar_fraction"] >= DELIVERY_TEMP_SOLAR_FRACTION)
    demand_ok = (m["solar_fraction"] is not None
                  and m["solar_fraction"] >= ANNUAL_DEMAND_SOLAR_FRACTION)
    temp_violation = (m["max_water_temp_C"] > max_water_C
                       or (pcm_id is not None and m["max_pcm_temp_C"] > max_pcm_C)
                       or m["n_safety_violations"] > 0)

    return {
        "useful_energy_kWh": m["useful_energy_kWh"],
        "solar_fraction": m["solar_fraction"],
        "delivery_temp_hours": m["delivery_temp_hours"],
        "max_water_temp_C": m["max_water_temp_C"],
        "max_pcm_temp_C": m["max_pcm_temp_C"],
        "n_safety_violations": m["n_safety_violations"],
        "meet_delivery_temp": bool(delivery_ok),
        "meet_annual_demand": bool(demand_ok),
        "temp_violation": bool(temp_violation),
    }


def run_robustness(state: str, n_draws: int = N_DRAWS_DEFAULT):
    n_draws = max(int(n_draws), 50)   # framework doc: never fewer than 50
    system_config = load_system_config()
    deployable = pd.read_csv(DEPLOYABLE_PATH)

    print(f"Phase 8 robustness: {n_draws} Monte Carlo draws x {len(deployable)} regimes "
          f"(sources: weather+noise, demand volume, demand timing, mains temp)")

    summary_rows = []
    all_draws = []
    for _, dep_row in deployable.iterrows():
        cid = int(dep_row["regime_id"])
        rng = np.random.default_rng(MC_SEED + cid)
        draws = []
        for i in range(n_draws):
            r = _one_draw(state, dep_row, rng, system_config)
            if r is not None:
                r["regime_id"] = cid
                r["draw"] = i
                draws.append(r)
        d = pd.DataFrame(draws)
        all_draws.append(d)

        p_delivery = float(d["meet_delivery_temp"].mean())
        p_demand = float(d["meet_annual_demand"].mean())
        p_temp_safe = float(1.0 - d["temp_violation"].mean())
        ue_p5, ue_p50, ue_p95 = np.percentile(d["useful_energy_kWh"], [5, 50, 95])
        robust = (p_demand >= 0.75) and (p_temp_safe >= 0.95)

        row = {
            "regime_id": cid,
            "pcm_id": dep_row["pcm_id"],
            "n_draws": len(d),
            "P_meet_delivery_temp": round(p_delivery, 4),
            "P_meet_annual_demand": round(p_demand, 4),
            "P_temp_safe": round(p_temp_safe, 4),
            "P_any_safety_violation": round(float(d["temp_violation"].mean()), 4),
            "useful_energy_p5_kWh": round(float(ue_p5), 2),
            "useful_energy_p50_kWh": round(float(ue_p50), 2),
            "useful_energy_p95_kWh": round(float(ue_p95), 2),
            "solar_fraction_p5": round(float(np.percentile(d["solar_fraction"], 5)), 4),
            "solar_fraction_p95": round(float(np.percentile(d["solar_fraction"], 95)), 4),
            "max_water_temp_C_p95": round(float(np.percentile(d["max_water_temp_C"], 95)), 2),
            "robust": bool(robust),
        }
        summary_rows.append(row)
        print(f"  regime {cid} ({dep_row['pcm_id']}): "
              f"P(demand)={p_demand:.2f}  P(temp-safe)={p_temp_safe:.2f}  "
              f"useful E [P5,P95]=[{ue_p5:.0f}, {ue_p95:.0f}] kWh  -> "
              f"{'ROBUST' if robust else 'CAVEAT (below threshold)'}")

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(ROBUSTNESS_PATH, index=False)
    pd.concat(all_draws, ignore_index=True).to_csv(DRAWS_PATH, index=False)
    print(f"\nSaved: {ROBUSTNESS_PATH}")
    print(f"Saved: {DRAWS_PATH}")
    return summary


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "rajasthan"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else N_DRAWS_DEFAULT
    run_robustness(state, n)
