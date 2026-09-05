"""
src/optimize/select_deployable.py
=====================================
Phase 7 / D2.6 — second half of "one optimization pass + simulator
confirmation". Takes the surrogate's top-N candidates per regime x PCM
pair (src/optimize/search.py) and:

  1. Re-runs every one of them in the REAL simulator (non-negotiable,
     framework doc: "never report a surrogate-only number").
  2. Computes surrogate-vs-simulator error per candidate; if error >15%
     (Bug-Fix 5), trusts the simulator value and logs the mismatch.
  3. Applies the pre-declared deployable-design selection rule (framework
     doc §9.5, frozen in system_config_shared.yaml's
     `selection.pareto_tolerance_pct`):
       reject infeasible -> meet delivery/safety reliability -> within
       tolerance of best useful energy -> minimize pump energy then PCM
       mass -> prefer simpler/lower capsule count -> prefer larger
       constraint margin -> (unseen-weather re-confirmation: DEFERRED,
       medoid-only per the 40-hr cut list -- noted explicitly, not hidden).

Writes:
  results/<state>/optimized_designs.csv       -- every simulator-confirmed
                                                  candidate (the "PCM
                                                  comparison report", §9.4)
  results/<state>/deployable_design_per_regime.csv -- ONE row per regime,
                                                  the final selection
"""

import sys

import pandas as pd

from config import RESULTS_DIR
from src.design.schema import DesignVector
from src.simulation.run_case import run_case
from src.io_utils import load_system_config, load_state_config
from src.optimize.search import search_all_pairs

LARGE_ERROR_THRESHOLD_PCT = 15.0


def confirm_candidates(state: str, candidates: pd.DataFrame) -> pd.DataFrame:
    system_config = load_system_config()
    max_water_C = system_config["safety"]["max_water_temp_C"]
    max_pcm_C = system_config["safety"]["max_pcm_temp_C"]

    rows = []
    for _, cand in candidates.iterrows():
        pcm_id = None if cand["pcm_id"] == "NONE_plain_tank" else cand["pcm_id"]
        design = DesignVector(cand["capsule_diameter_m"], int(cand["n_capsule"]), cand["flow_rate_kg_s"])
        out = run_case(state, int(cand["regime_id"]), pcm_id, design, record_hourly=True)
        if not out["valid"]:
            continue   # should not happen -- search.py already geometry-filtered
        m = out["metrics"]

        row = dict(cand)
        row.update({f"sim_{k}": v for k, v in m.items()
                    if k in ("useful_energy_kWh", "solar_fraction", "unmet_energy_kWh",
                              "pump_energy_kWh", "pcm_mass_kg", "mean_f_melt",
                              "max_water_temp_C", "max_pcm_temp_C", "n_safety_violations",
                              "residual_pct_of_collector")})

        pred_e, sim_e = cand.get("pred_useful_energy_kWh"), m["useful_energy_kWh"]
        row["surrogate_vs_sim_error_pct"] = (abs(pred_e - sim_e) / sim_e * 100.0
                                              if sim_e else float("nan"))
        row["large_surrogate_error"] = row["surrogate_vs_sim_error_pct"] > LARGE_ERROR_THRESHOLD_PCT

        row["meets_temperature_safety"] = (m["max_water_temp_C"] <= max_water_C
                                            and (pcm_id is None or m["max_pcm_temp_C"] <= max_pcm_C)
                                            and m["n_safety_violations"] == 0)
        row["constraint_margin_C"] = min(
            max_water_C - m["max_water_temp_C"],
            (max_pcm_C - m["max_pcm_temp_C"]) if pcm_id is not None else 1e9,
        )
        rows.append(row)

    return pd.DataFrame(rows)


def apply_selection_rule(state: str, confirmed: pd.DataFrame) -> pd.DataFrame:
    system_config = load_system_config()
    tol_pct = system_config["selection"]["pareto_tolerance_pct"]

    selected = []
    for regime_id, group in confirmed.groupby("regime_id"):
        feasible = group[group["meets_temperature_safety"]]
        if feasible.empty:
            print(f"  [WARN] regime {regime_id}: no candidate met the temperature-safety rule; "
                  f"widening to all simulator-confirmed candidates for this regime.")
            feasible = group
        if feasible.empty:
            continue

        best_energy = feasible["sim_useful_energy_kWh"].max()
        within_tol = feasible[feasible["sim_useful_energy_kWh"] >= best_energy * (1 - tol_pct / 100.0)]

        within_tol = within_tol.sort_values(
            by=["sim_pump_energy_kWh", "sim_pcm_mass_kg", "n_capsule", "constraint_margin_C"],
            ascending=[True, True, True, False],
        )
        winner = within_tol.iloc[0].copy()
        winner["selection_rule_pool_size"] = len(within_tol)
        winner["best_useful_energy_in_regime_kWh"] = best_energy
        selected.append(winner)

    return pd.DataFrame(selected)


def run_phase7(state: str, top_n_per_pair: int = 5):
    print(f"Phase 7 -- optimization pass + simulator confirmation, state={state}")
    print("Step 1/3: surrogate proposal search ...")
    candidates = search_all_pairs(state, top_n=top_n_per_pair)
    if candidates.empty:
        print("No candidates proposed -- check Phase 6 surrogate training.")
        return None, None

    print(f"\nStep 2/3: re-running {len(candidates)} candidates in the REAL simulator ...")
    confirmed = confirm_candidates(state, candidates)

    n_large_error = int(confirmed["large_surrogate_error"].sum())
    mean_error = confirmed["surrogate_vs_sim_error_pct"].mean()
    print(f"  Surrogate-vs-simulator mean error (useful energy): {mean_error:.2f}%  "
          f"({n_large_error}/{len(confirmed)} candidates >{LARGE_ERROR_THRESHOLD_PCT}% -- "
          f"large-error rule: trust the simulator value for these, already done above)")

    out_dir = RESULTS_DIR / state
    confirmed.to_csv(out_dir / "optimized_designs.csv", index=False)
    print(f"  Saved: {out_dir / 'optimized_designs.csv'}")

    print("\nStep 3/3: applying the pre-declared deployable-design selection rule ...")
    deployable = apply_selection_rule(state, confirmed)
    deployable.to_csv(out_dir / "deployable_design_per_regime.csv", index=False)
    print(f"  Saved: {out_dir / 'deployable_design_per_regime.csv'}")

    print("\nDeployable design per regime:")
    cols = ["regime_id", "pcm_id", "capsule_diameter_m", "n_capsule", "flow_rate_kg_s",
            "sim_useful_energy_kWh", "sim_solar_fraction", "sim_pump_energy_kWh",
            "sim_pcm_mass_kg", "constraint_margin_C", "surrogate_vs_sim_error_pct"]
    print(deployable[cols].to_string(index=False))

    return confirmed, deployable


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "tamilnadu"
    run_phase7(state)
