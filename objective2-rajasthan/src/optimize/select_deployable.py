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
  results/phase7_optimized_designs.csv              -- every simulator-confirmed
                                                       candidate (the "PCM
                                                       comparison report", §9.4)
  results/phase7_deployable_design_per_regime.csv   -- ONE row per regime,
                                                       the final selection

confirm_candidates() and the large-error rule are this repo's own.
apply_selection_rule() was PORTED FROM
objective2-tamilnadu/src/optimize/select_deployable.py on 2026-09-14
(see its docstring below for the scope-correction rationale): the
plain-tank baseline is excluded from the winner pool so it can no
longer win the per-regime recommendation by default. Only the flat
results/phaseN_* output paths and the __main__ state fallback differ
from Tamil Nadu's version.
"""

import sys

import pandas as pd

from config import RESULTS_DIR
from src.design.schema import DesignVector
from src.simulation.run_case import run_case
from src.io_utils import load_system_config, load_state_config, get_regime, write_manifest_sidecar
from src.optimize.search import search_all_pairs

LARGE_ERROR_THRESHOLD_PCT = 15.0

OPTIMIZED_DESIGNS_PATH = RESULTS_DIR / "phase7_optimized_designs.csv"
DEPLOYABLE_PATH = RESULTS_DIR / "phase7_deployable_design_per_regime.csv"


def confirm_candidates(state: str, candidates: pd.DataFrame) -> pd.DataFrame:
    system_config = load_system_config()
    max_water_C = system_config["safety"]["max_water_temp_C"]
    max_pcm_C = system_config["safety"]["max_pcm_temp_C"]

    rows = []
    for _, cand in candidates.iterrows():
        pcm_id = None if cand["pcm_id"] == "NONE_plain_tank" else cand["pcm_id"]
        design = DesignVector(cand["capsule_diameter_m"], int(cand["n_capsule"]), cand["flow_rate_kg_s"],
                               capsule_arrangement=cand["arrangement"])
        out = run_case(state, int(cand["regime_id"]), pcm_id, design, record_hourly=True)
        if not out["valid"]:
            continue   # should not happen -- search.py already geometry-filtered
        m = out["metrics"]

        row = dict(cand)
        row.update({f"sim_{k}": v for k, v in m.items()
                    if k in ("useful_energy_kWh", "solar_fraction", "unmet_energy_kWh",
                              "pump_energy_kWh", "pcm_mass_kg", "mean_f_melt",
                              "max_water_temp_C", "max_pcm_temp_C", "n_safety_violations",
                              "residual_pct_of_collector",
                              # carried through so the delivery requirement can be
                              # reported (step 3.2, 2026-09-20 fix plan):
                              "delivery_temp_hours", "mains_temp_C")})

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


def _arrangement_rationale(confirmed: pd.DataFrame, regime_id, pcm_id, winner_arrangement,
                            winner_energy_kWh: float, noise_band_pct: float) -> str:
    """Compares the winning arrangement's simulator-confirmed useful_energy_kWh
    against the best simulator-confirmed candidate from each of the other two
    arrangements in the SAME regime x PCM pool (docs/07_PROMPT_PHASE7_OPTIMIZE.md
    step 4). noise_band_pct is the mean surrogate-vs-simulator error observed
    in this run (Phase 6/7) — margins inside that band aren't a real signal."""
    pool = confirmed[(confirmed["regime_id"] == regime_id) & (confirmed["pcm_id"] == pcm_id)]
    best_by_arrangement = pool.groupby("arrangement")["sim_useful_energy_kWh"].max()
    others = best_by_arrangement.drop(labels=[winner_arrangement], errors="ignore")
    if others.empty:
        return f"only arrangement {winner_arrangement} was confirmed for this regime/PCM pool."

    next_arrangement = others.idxmax()
    next_energy = others.max()
    margin_kWh = winner_energy_kWh - next_energy
    margin_pct = (margin_kWh / next_energy * 100.0) if next_energy else float("inf")

    if margin_pct > noise_band_pct:
        return (f"arrangement {winner_arrangement} won by {margin_kWh:+.3f} kWh "
                f"({margin_pct:.2f}%) over next-best arrangement {next_arrangement}.")
    else:
        tied = [winner_arrangement] + [a for a, e in others.items()
                                        if abs((e - winner_energy_kWh) / winner_energy_kWh * 100.0) <= noise_band_pct]
        return (f"arrangements tied within noise in this regime — arrangement not decisive here "
                f"(margin={margin_kWh:+.3f} kWh / {margin_pct:.2f}% <= noise band={noise_band_pct:.2f}%; "
                f"tied arrangements: {sorted(set(tied))}).")


def apply_selection_rule(state: str, confirmed: pd.DataFrame, noise_band_pct: float = 0.0) -> pd.DataFrame:
    """Selects the deployable PCM design per regime.

    SCOPE CORRECTION (2026-09-14, ported from objective2-tamilnadu's
    src/optimize/select_deployable.py, per the actual problem statement,
    presentation_review2.pdf): Objective 2 is "an AI-driven design
    optimization model to determine the optimal PCM thickness, capsule
    arrangement, number of PCM capsules, and flow rate for maximizing
    thermal energy storage" -- it presupposes a PCM design and asks for
    its optimal parameters. It does not ask whether to use PCM at all.
    The zero-mass "plain tank" option was an internal ablation/diagnostic
    baseline this implementation added on its own initiative (useful for
    Gate 3's capability check and the Phase 6 feature-importance
    analysis) -- it was never something the assignment asked to be
    eligible to win the final per-regime recommendation, and letting it
    do so was answering a different question than the one actually posed.

    So: the plain-tank rows stay in optimized_designs.csv (the full
    comparison report) for that diagnostic purpose, but are EXCLUDED from
    the pool this function selects from. Among PCM candidates only, the
    winner is the one with the highest simulator-confirmed useful energy
    (the objective's literal "maximizing thermal energy storage"),
    tie-broken by the existing pump-energy/PCM-mass/count/margin order.

    Safety is NEVER hidden: meets_temperature_safety, constraint_margin_C
    and n_safety_violations are still computed and carried through on
    every row, and a design whose margin is negative is flagged in
    `deployment_note` as needing Objective 3's active bypass before
    hardware deployment -- reported, not disqualifying the pick back to a
    non-PCM answer the assignment never asked for.
    """
    system_config = load_system_config()
    tol_pct = system_config["selection"]["pareto_tolerance_pct"]

    selected = []
    for regime_id, group in confirmed.groupby("regime_id"):
        pcm_only = group[group["pcm_id"] != "NONE_plain_tank"]
        if pcm_only.empty:
            print(f"  [WARN] regime {regime_id}: no PCM candidate was confirmed at all -- "
                  f"cannot produce a PCM design for this regime from the current search.")
            continue

        best_energy = pcm_only["sim_useful_energy_kWh"].max()
        within_tol = pcm_only[pcm_only["sim_useful_energy_kWh"] >= best_energy * (1 - tol_pct / 100.0)]

        # Tie-break order (decision D3, 2026-09-20 fix plan): safety margin
        # first, not pump energy -- least-pump-energy-first (the previous
        # rule) is not a safety or performance argument among designs
        # already tied within the Pareto tolerance on useful energy.
        within_tol = within_tol.sort_values(
            by=["constraint_margin_C", "sim_pump_energy_kWh", "sim_pcm_mass_kg", "n_capsule"],
            ascending=[False, True, True, True],
        )
        winner = within_tol.iloc[0].copy()
        winner["selection_rule_pool_size"] = len(within_tol)
        winner["best_useful_energy_in_regime_kWh"] = best_energy
        winner["arrangement_rationale"] = _arrangement_rationale(
            confirmed, regime_id, winner["pcm_id"], winner["arrangement"],
            winner["sim_useful_energy_kWh"], noise_band_pct)

        plain = group[group["pcm_id"] == "NONE_plain_tank"]
        if not plain.empty:
            winner["plain_tank_useful_energy_kWh"] = plain["sim_useful_energy_kWh"].iloc[0]
            winner["pcm_vs_plain_tank_pct"] = (
                (winner["sim_useful_energy_kWh"] - winner["plain_tank_useful_energy_kWh"])
                / winner["plain_tank_useful_energy_kWh"] * 100.0
            )
        winner["deployment_note"] = (
            "Meets this project's precautionary temperature-safety margin as-is."
            if winner["meets_temperature_safety"] else
            "Optimal PCM design per Objective 2's search, but exceeds the precautionary "
            "temperature-safety margin under nominal operation -- requires Objective 3's "
            "active bypass/discharge control before hardware deployment (see "
            "OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md). Not a disqualification of the design; "
            "a specified precondition for deploying it."
        )

        # Cohesion-gap fix #3 (2026-09-18): O2's selection rule (useful-energy
        # tolerance -> pump/mass/count/margin tie-break) never references
        # Objective 1's MCDM consensus ranking -- it is legitimately possible,
        # and does happen here, for O2 to deploy a PCM O1 ranked #2 or #3
        # rather than its #1 pick. This was previously silent (see
        # docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md, cohesion-gap analysis
        # 2026-09-18). Not made a tie-break criterion itself (that decision is
        # out of this fix's scope -- would change which design wins, not just
        # how it's reported) -- logged and flagged instead, so the divergence
        # is visible rather than discovered later by a reviewer.
        o1_shortlist = get_regime(state, regime_id).get("pcm_shortlist", [])
        o1_rank1_pcm = o1_shortlist[0] if o1_shortlist else None
        winner["o1_rank1_pcm"] = o1_rank1_pcm
        winner["diverges_from_o1_rank1"] = bool(o1_rank1_pcm is not None and winner["pcm_id"] != o1_rank1_pcm)
        if winner["diverges_from_o1_rank1"]:
            msg = (f"O2's deployable design for regime {regime_id} is {winner['pcm_id']!r}, "
                   f"not Objective 1's rank-1 consensus pick {o1_rank1_pcm!r} -- Objective 2's "
                   f"selection rule (useful-energy tolerance, then pump/mass/count/margin) does "
                   f"not weight O1's MCDM ranking. See docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md.")
            print(f"  [NOTE] {msg}")
            winner["o1_divergence_note"] = msg
        else:
            winner["o1_divergence_note"] = f"Matches Objective 1's rank-1 consensus pick for regime {regime_id}."

        selected.append(winner)

    return pd.DataFrame(selected)


def run_phase7(state: str, top_n_per_pair: int = 15):
    # Raised 5->15 (step 3.3, 2026-09-20 fix plan) together with search.py's
    # per-arrangement quota, so each of the 3 arrangements reaches the
    # simulator-confirmation step (5 each) rather than one dominating the
    # surrogate ranking.
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

    confirmed.to_csv(OPTIMIZED_DESIGNS_PATH, index=False)
    print(f"  Saved: {OPTIMIZED_DESIGNS_PATH}")
    write_manifest_sidecar(OPTIMIZED_DESIGNS_PATH, state,
                            extra={"mean_surrogate_vs_sim_error_pct": float(mean_error),
                                   "large_error_threshold_pct": LARGE_ERROR_THRESHOLD_PCT})

    print("\nStep 3/3: applying the pre-declared deployable-design selection rule ...")
    deployable = apply_selection_rule(state, confirmed, noise_band_pct=mean_error)
    deployable.to_csv(DEPLOYABLE_PATH, index=False)
    print(f"  Saved: {DEPLOYABLE_PATH}")
    write_manifest_sidecar(DEPLOYABLE_PATH, state,
                            extra={"tie_break_order": ["constraint_margin_C (desc)", "sim_pump_energy_kWh (asc)",
                                                        "sim_pcm_mass_kg (asc)", "n_capsule (asc)"],
                                   "pareto_tolerance_pct": load_system_config()["selection"]["pareto_tolerance_pct"]})

    print("\nDeployable design per regime:")
    cols = ["regime_id", "pcm_id", "arrangement", "capsule_diameter_m", "n_capsule", "flow_rate_kg_s",
            "sim_useful_energy_kWh", "sim_solar_fraction", "sim_pump_energy_kWh",
            "sim_pcm_mass_kg", "constraint_margin_C", "surrogate_vs_sim_error_pct",
            "o1_rank1_pcm", "diverges_from_o1_rank1", "arrangement_rationale"]
    print(deployable[cols].to_string(index=False))

    return confirmed, deployable


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "rajasthan"
    run_phase7(state)
