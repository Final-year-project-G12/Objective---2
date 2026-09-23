"""
check_delivery_temp_reconciliation.py
=====================================
Fix — the O1<->O2 delivery-temperature divergence documented (not
resolved) in docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md §1: Objective
1's `T_DELIVERY_C` is 60 C (corrected 2026-09-13, Avargani et al.
2021-anchored, project CLAUDE.md §3.2), while Objective 2's frozen
`system_config_shared.yaml` `delivery.target_temp_C` is 45 C, chosen
before O1's correction.

This is a single supplementary check (2 delivery-temp configs x plain-
tank + 3-PCM shortlist x 3 regimes = 24 cases), NOT a full Phase 5-7
DOE/surrogate/optimizer re-run -- same scoping precedent as
check_standards_compliant_sizing.py (Fix 6) and check_widened_bounds_
pcm_loading.py (Fix 3). It does NOT edit system_config_shared.yaml
(frozen, identical across all 4 states -- changing it means every state
must re-run from DOE onward per that file's own header) -- the
60 C-reconciled config exists only as an in-memory `system_config_
overrides` dict passed to run_case(), the same seam every prior
supplementary check in this project already uses.

Geometries reused are each (regime, pcm) combination's own Phase 7
simulator-confirmed design vector (phase7_deployable_design_per_regime.csv
for the plain tank, phase7_optimized_designs.csv's highest-useful-energy
confirmed row per (regime, pcm) for the shortlisted PCMs) -- not
re-searched, so this checks "does raising the delivery target to O1's
basis change the solar-fraction / safety outcome for designs Phase 7
already found," not a fresh optimization at the new target (that would
be a full DOE/surrogate re-run, out of scope for a supplementary check
per this project's own precedent).

Note: `target_temp_C` only feeds the solar-fraction *denominator*
(e_demand_ideal_kWh = draw_kg * cp * (target_temp_C - mains_temp_C)) and
the `delivery_hours` count in run_case() -- it does NOT change the
simulated water/PCM temperatures themselves, so this check cannot
change any Gate-1/2/3 safety verdict; it only changes how the SAME
simulated year is scored against a stricter (60 C) vs looser (45 C)
delivery bar.

Run: python check_delivery_temp_reconciliation.py
Output: results/fix7_delivery_temp_reconciliation_supplementary.csv/.md
"""

import pandas as pd

from config import RESULTS_DIR
from src.design.schema import DesignVector
from src.io_utils import load_system_config
from src.simulation.run_case import run_case

DEPLOYABLE_PATH = RESULTS_DIR / "phase7_deployable_design_per_regime.csv"
OPTIMIZED_PATH = RESULTS_DIR / "phase7_optimized_designs.csv"

OUT_CSV = RESULTS_DIR / "fix7_delivery_temp_reconciliation_supplementary.csv"
OUT_MD = RESULTS_DIR / "fix7_delivery_temp_reconciliation_supplementary.md"

FROZEN_TARGET_C = 45.0
O1_RECONCILED_TARGET_C = 60.0   # T_DELIVERY_C, CLAUDE.md §3.2 / §3.3

CONFIGS = {
    "frozen_45C": {"delivery": {"target_temp_C": FROZEN_TARGET_C}},
    "o1_reconciled_60C": {"delivery": {"target_temp_C": O1_RECONCILED_TARGET_C}},
}


def build_case_list():
    """One row per (regime, pcm_id, design vector) -- plain tank's own Phase 7
    deployable geometry, plus each shortlisted PCM's own highest-useful-energy
    Phase 7 confirmed geometry. Reused verbatim, not re-searched."""
    deployable = pd.read_csv(DEPLOYABLE_PATH)
    optimized = pd.read_csv(OPTIMIZED_PATH)
    pcm_rows = optimized[optimized["pcm_id"] != "NONE_plain_tank"]
    best_pcm = pcm_rows.loc[pcm_rows.groupby(["regime_id", "pcm_id"])["sim_useful_energy_kWh"].idxmax()]

    cases = []
    for _, r in deployable.iterrows():
        cases.append({"regime_id": int(r["regime_id"]), "pcm_id": "NONE_plain_tank",
                      "capsule_diameter_m": r["capsule_diameter_m"],
                      "n_capsule": int(r["n_capsule"]), "flow_rate_kg_s": r["flow_rate_kg_s"]})
    for _, r in best_pcm.iterrows():
        cases.append({"regime_id": int(r["regime_id"]), "pcm_id": r["pcm_id"],
                      "capsule_diameter_m": r["capsule_diameter_m"],
                      "n_capsule": int(r["n_capsule"]), "flow_rate_kg_s": r["flow_rate_kg_s"]})
    return cases


def run():
    base_config = load_system_config()
    gate4_lo = base_config["verification"]["gate4_benchmark_solar_fraction_low_pct"]
    gate4_hi = base_config["verification"]["gate4_benchmark_solar_fraction_high_pct"]

    cases = build_case_list()
    rows = []
    for config_label, overrides in CONFIGS.items():
        target_c = overrides["delivery"]["target_temp_C"]
        for c in cases:
            pcm_name = None if c["pcm_id"] == "NONE_plain_tank" else c["pcm_id"]
            design = DesignVector(c["capsule_diameter_m"], c["n_capsule"], c["flow_rate_kg_s"], capsule_arrangement="staggered")
            result = run_case("rajasthan", c["regime_id"], pcm_name, design,
                              system_config_overrides=overrides)
            row = {
                "config_label": config_label,
                "delivery_target_temp_C": target_c,
                "regime_id": c["regime_id"], "pcm_id": c["pcm_id"],
                "capsule_diameter_m": c["capsule_diameter_m"], "n_capsule": c["n_capsule"],
                "flow_rate_kg_s": c["flow_rate_kg_s"],
                "valid": result["valid"],
            }
            if result["valid"]:
                m = result["metrics"]
                max_water_C = base_config["safety"]["max_water_temp_C"]
                max_pcm_C = base_config["safety"]["max_pcm_temp_C"]
                meets_safety = (m["max_water_temp_C"] <= max_water_C
                                and (pcm_name is None or m["max_pcm_temp_C"] <= max_pcm_C)
                                and m["n_safety_violations"] == 0)
                sf_pct = m["solar_fraction"] * 100.0
                row.update({
                    "solar_fraction_pct": sf_pct,
                    "in_gate4_band": gate4_lo <= sf_pct <= gate4_hi,
                    "useful_energy_kWh": m["useful_energy_kWh"],
                    "unmet_energy_kWh": m["unmet_energy_kWh"],
                    "delivery_temp_hours": m.get("delivery_temp_hours"),
                    "max_water_temp_C": m["max_water_temp_C"],
                    "max_pcm_temp_C": m.get("max_pcm_temp_C"),
                    "n_safety_violations": m["n_safety_violations"],
                    "meets_temperature_safety": meets_safety,
                })
            else:
                row["reason"] = result["reason"]
            rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    lines = [
        "# Fix — O1<->O2 delivery-temperature reconciliation, supplementary check (Rajasthan)\n",
        f"Objective 1's `T_DELIVERY_C` is **60 C** (corrected 2026-09-13, Avargani et al. "
        f"2021-anchored, CLAUDE.md §3.2). Objective 2's frozen `system_config_shared.yaml` "
        f"`delivery.target_temp_C` is **45 C**, chosen before O1's correction — documented as an "
        f"unresolved divergence in `docs/09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §1. This "
        f"supplementary check quantifies the effect of scoring the SAME Phase-7-confirmed designs "
        f"against O1's 60 C target instead of the frozen 45 C target, using each (regime, pcm) "
        f"case's own Phase 7 simulator-confirmed geometry (not re-searched — a fresh optimization "
        f"at 60 C would require a full DOE/surrogate/optimizer re-run, out of scope for a "
        f"supplementary check per this project's own precedent). `system_config_shared.yaml` "
        f"itself is untouched (frozen, identical across all 4 states) — the 60 C config exists "
        f"only as an in-memory `system_config_overrides` dict to `run_case()`. Gate 4 benchmark "
        f"band: {gate4_lo:.0f}-{gate4_hi:.0f}% (Singh et al. 2025, cited).\n",
    ]
    for regime_id in sorted(df["regime_id"].unique()):
        lines.append(f"\n## Regime {regime_id}\n")
        sub = df[df["regime_id"] == regime_id]
        cols = [c for c in sub.columns if c not in ("regime_id",)]
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("|" + "|".join(["---"] * len(cols)) + "|")
        for _, r in sub.iterrows():
            lines.append("| " + " | ".join(
                f"{r[c]:.4g}" if isinstance(r[c], float) else str(r[c]) for c in cols) + " |")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(df.to_string(index=False))
    print(f"\nSaved: {OUT_CSV}")
    print(f"Saved: {OUT_MD}")
    return df


if __name__ == "__main__":
    run()
