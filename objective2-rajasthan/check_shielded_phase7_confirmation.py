"""
check_shielded_phase7_confirmation.py
========================================
Follow-up to Fix 2, raised in review: the safety shield
(src/simulation/tank_model.py) was only ever turned on at Phase 8's Monte
Carlo call site — Phase 5 (DOE), Phase 6 (surrogate training), and Phase
7 (optimizer proposal + confirmation) were all run against UNSHIELDED
physics, including the deployable-design selection itself and Gate 4's
headline 55.07% solar-fraction number. Since the shield stops the pump
above 72 C, it discards collector energy that pre-shield physics counted
-- so "does the Phase 7 selection still hold, and is 55.07% still the
honest number to quote" are open questions, not something to assume away.

Full rigor would mean re-running Phase 5's DOE + Phase 6's surrogate
retrain with the shield on by default (~4800 candidates x geometry search
+ a full retrain) -- expensive, and not actually needed: the surrogate's
only job is to RANK candidates by predicted useful energy, and the shield
only clips a small high-temperature tail, so re-ranking 4800 unscored
candidates was judged not to be where the risk lives. The risk lives in
whether the FINAL selection (Phase 7 Step 2's 60 simulator-confirmed
candidates -> the pre-declared selection rule) changes once shielded.
That is fully checkable by re-running the exact same 60 proposed
candidates (results/phase7_surrogate_top_candidates.csv -- the surrogate
proposals, i.e. the search step's output, not yet simulator-confirmed)
through the REAL confirm_candidates()/apply_selection_rule() pipeline
functions with the shield enabled, and comparing against the existing
(pre-shield) results/phase7_optimized_designs.csv /
phase7_deployable_design_per_regime.csv. This is the same "single
supplementary check, not a full re-run" scoping already used for Fix 1's
overheat track and Fix 3's widened bounds.

Run: python check_shielded_phase7_confirmation.py
Output: results/fix2_shielded_phase7_confirmation.csv/.md
"""

import pandas as pd

from config import RESULTS_DIR
from src.optimize.select_deployable import confirm_candidates, apply_selection_rule

SURROGATE_CANDIDATES_PATH = RESULTS_DIR / "phase7_surrogate_top_candidates.csv"
UNSHIELDED_OPTIMIZED_PATH = RESULTS_DIR / "phase7_optimized_designs.csv"
UNSHIELDED_DEPLOYABLE_PATH = RESULTS_DIR / "phase7_deployable_design_per_regime.csv"

OUT_CSV = RESULTS_DIR / "fix2_shielded_phase7_confirmation.csv"
OUT_MD = RESULTS_DIR / "fix2_shielded_phase7_confirmation.md"

SHIELD_OVERRIDE = {"safety_shield": {"enabled": True}}


def run(state: str = "rajasthan"):
    candidates = pd.read_csv(SURROGATE_CANDIDATES_PATH)
    unshielded_optimized = pd.read_csv(UNSHIELDED_OPTIMIZED_PATH)
    unshielded_deployable = pd.read_csv(UNSHIELDED_DEPLOYABLE_PATH).set_index("regime_id")

    print(f"Re-confirming {len(candidates)} Phase 7 proposed candidates WITH the safety "
          f"shield enabled ...")
    shielded_confirmed = confirm_candidates(state, candidates, system_config_overrides=SHIELD_OVERRIDE)
    shielded_deployable = apply_selection_rule(state, shielded_confirmed).set_index("regime_id")

    rows = []
    for regime_id in sorted(unshielded_deployable.index):
        u = unshielded_deployable.loc[regime_id]
        s = shielded_deployable.loc[regime_id]
        same_pcm = (u["pcm_id"] == s["pcm_id"])
        same_geometry = (abs(u["capsule_diameter_m"] - s["capsule_diameter_m"]) < 1e-9
                          and int(u["n_capsule"]) == int(s["n_capsule"])
                          and abs(u["flow_rate_kg_s"] - s["flow_rate_kg_s"]) < 1e-9)
        solar_fraction_delta_pp = (s["sim_solar_fraction"] - u["sim_solar_fraction"]) * 100.0
        rows.append({
            "regime_id": regime_id,
            "pcm_id_unshielded": u["pcm_id"], "pcm_id_shielded": s["pcm_id"],
            "selection_unchanged": same_pcm and same_geometry,
            "solar_fraction_unshielded_pct": u["sim_solar_fraction"] * 100.0,
            "solar_fraction_shielded_pct": s["sim_solar_fraction"] * 100.0,
            "solar_fraction_delta_pp": solar_fraction_delta_pp,
            "useful_energy_unshielded_kWh": u["sim_useful_energy_kWh"],
            "useful_energy_shielded_kWh": s["sim_useful_energy_kWh"],
            "max_water_temp_unshielded_C": u["sim_max_water_temp_C"],
            "max_water_temp_shielded_C": s["sim_max_water_temp_C"],
            # Added on review: confirm_candidates() already computes these for
            # both runs (src/optimize/select_deployable.py:66-84) -- a prior
            # summary of this file quoted a shielded max_pcm_temp/violation-count
            # pair that was never actually saved anywhere. Saving them for real
            # here rather than repeating an unsourced number.
            "max_pcm_temp_unshielded_C": u.get("sim_max_pcm_temp_C"),
            "max_pcm_temp_shielded_C": s.get("sim_max_pcm_temp_C"),
            "n_safety_violations_unshielded": u.get("sim_n_safety_violations"),
            "n_safety_violations_shielded": s.get("sim_n_safety_violations"),
            "meets_temperature_safety_unshielded": u.get("meets_temperature_safety"),
            "meets_temperature_safety_shielded": s.get("meets_temperature_safety"),
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    all_unchanged = bool(df["selection_unchanged"].all())
    max_abs_delta_pp = df["solar_fraction_delta_pp"].abs().max()

    lines = [
        "# Fix 2 follow-up — shielded Phase 7 re-confirmation (Rajasthan)\n",
        "Raised in review: the shield (Fix 2) was only turned on at Phase 8's Monte Carlo "
        "call site, so Phase 5-7's design search, surrogate training, and deployable-design "
        "selection -- including Gate 4's reported 55.07% solar fraction -- were all computed "
        "against UNSHIELDED physics. This re-runs the exact 60 surrogate-proposed candidates "
        "through the real confirm_candidates()/apply_selection_rule() pipeline functions with "
        "the shield enabled (not a full DOE/surrogate re-run -- see module docstring for why "
        "that full re-run was judged unnecessary).\n",
        f"\n**Deployable-design selection unchanged in all 3 regimes: {all_unchanged}.** "
        f"Largest solar-fraction shift from enabling the shield: {max_abs_delta_pp:.4f} "
        f"percentage points (shield only clips a rare high-temperature tail, so this is "
        f"expected to be small, and is now a measured confirmation rather than an assumption).\n",
    ]
    cols = list(df.columns)
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "|".join(["---"] * len(cols)) + "|")
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(f"{r[c]:.6g}" if isinstance(r[c], float) else str(r[c])
                                        for c in cols) + " |")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(df.to_string(index=False))
    print(f"\nSelection unchanged in all regimes: {all_unchanged}")
    print(f"Max |solar fraction delta|: {max_abs_delta_pp:.4f} pp")
    print(f"Saved: {OUT_CSV}")
    print(f"Saved: {OUT_MD}")
    return df


if __name__ == "__main__":
    run()
