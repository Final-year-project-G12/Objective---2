"""
check_standards_compliant_sizing.py
=====================================
Fix — the frozen collector:tank sizing (system_config_shared.yaml:
tank.volume_L=50, collector.area_m2=1.5 -> storage/collector ratio =
33.3 L/m^2) is verified NON-COMPLIANT with IS 12976:2023 (Bureau of
Indian Standards, "Solar Water Heating Systems -- Code of Practice"),
the actual governing Indian standard for this class of system:

  Sec 4.2: "It should be such sized as to store 1.5 to 2 times the
  average daily hot water usage. The tank capacities are generally
  chosen between 40 l/m2 to 100 l/m2 of collector area."
  Sec 7.1 (f-chart design parameters table): "Storage capacity: 50 l/m2
  to 100 l/m2."
  Sec 7.1 correction term C3: defined only "if the storage/collector
  ratio is other than 75 l/m2 collector area (between the limits of
  37.5 l/m2 and 300 l/m2)" -- i.e. 75 l/m2 is the standard's own
  reference/no-correction ratio, and its own f-chart method is not even
  defined below 37.5 l/m2.

33.3 L/m2 is below EVERY one of those thresholds (the 37.5 l/m2 floor
where the standard's own correction formula stops applying, the 40
l/m2 general lower bound, and half the 75 l/m2 reference). Verified
directly against PCM-Selection-ML-model/Sources/pdfs/IS12976_2023.pdf
this session (all four quotes above checked against the extracted PDF
text, not taken from a paraphrase).

This is a single supplementary check (two resized configs x plain-tank
+ 3-PCM shortlist x 3 regimes = 24 cases), NOT a full Phase 5-7
DOE/surrogate/optimizer re-run -- same scoping precedent as Fix 3's
widened-bounds check. It does NOT edit system_config_shared.yaml
(frozen, identical across all 4 states) -- both resized configs exist
only as in-memory `system_config_overrides` passed to run_case(),
the same seam Fix 2's shield check and Fix 3's widened-bounds check
both already use.

TWO resize directions tested, both anchored to IS 12976's 75 l/m2
reference ratio (the value at which its own correction term C3 = 1,
i.e. the standard's implicit "typical" case):
  Case A -- resize TANK, keep collector: 1.5 m2 x 75 l/m2 = 112.5 L.
  Case B -- resize COLLECTOR, keep tank: 50 L / 75 l/m2 = 0.667 m2.
Geometries reused are each (regime, pcm) combination's own Phase 7
simulator-confirmed design vector (phase7_deployable_design_per_regime.csv
for the plain tank, phase7_optimized_designs.csv's highest-useful-energy
confirmed row per (regime, pcm) for the shortlisted PCMs) -- not
re-searched, so this checks "does resizing the tank/collector change the
safety outcome for designs Phase 7 already found," not a fresh
optimization at the new sizing (that would be a full DOE/surrogate
re-run, out of scope for a supplementary check per this project's own
precedent).

Run: python check_standards_compliant_sizing.py
Output: results/fix6_standards_compliant_sizing_supplementary.csv/.md
"""

import pandas as pd

from config import RESULTS_DIR
from src.design.schema import DesignVector
from src.simulation.run_case import run_case

DEPLOYABLE_PATH = RESULTS_DIR / "phase7_deployable_design_per_regime.csv"
OPTIMIZED_PATH = RESULTS_DIR / "phase7_optimized_designs.csv"

OUT_CSV = RESULTS_DIR / "fix6_standards_compliant_sizing_supplementary.csv"
OUT_MD = RESULTS_DIR / "fix6_standards_compliant_sizing_supplementary.md"

FROZEN_COLLECTOR_M2 = 1.5
FROZEN_TANK_L = 50.0
IS12976_REFERENCE_RATIO_L_PER_M2 = 75.0

CONFIGS = {
    "frozen_33.3_Lm2": {"collector": {"area_m2": FROZEN_COLLECTOR_M2},
                         "tank": {"volume_L": FROZEN_TANK_L}},
    "caseA_tank_resize_75.0_Lm2": {"collector": {"area_m2": FROZEN_COLLECTOR_M2},
                                    "tank": {"volume_L": FROZEN_COLLECTOR_M2 * IS12976_REFERENCE_RATIO_L_PER_M2}},
    "caseB_collector_resize_75.0_Lm2": {"collector": {"area_m2": FROZEN_TANK_L / IS12976_REFERENCE_RATIO_L_PER_M2},
                                         "tank": {"volume_L": FROZEN_TANK_L}},
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
    cases = build_case_list()
    rows = []
    for config_label, overrides in CONFIGS.items():
        ratio = overrides["tank"]["volume_L"] / overrides["collector"]["area_m2"]
        for c in cases:
            pcm_name = None if c["pcm_id"] == "NONE_plain_tank" else c["pcm_id"]
            design = DesignVector(c["capsule_diameter_m"], c["n_capsule"], c["flow_rate_kg_s"], capsule_arrangement="staggered")
            result = run_case("rajasthan", c["regime_id"], pcm_name, design,
                              system_config_overrides=overrides)
            row = {
                "config_label": config_label,
                "collector_area_m2": overrides["collector"]["area_m2"],
                "tank_volume_L": overrides["tank"]["volume_L"],
                "storage_collector_ratio_Lm2": ratio,
                "regime_id": c["regime_id"], "pcm_id": c["pcm_id"],
                "capsule_diameter_m": c["capsule_diameter_m"], "n_capsule": c["n_capsule"],
                "flow_rate_kg_s": c["flow_rate_kg_s"],
                "valid": result["valid"],
            }
            if result["valid"]:
                m = result["metrics"]
                max_water_C = 75.0
                max_pcm_C = 65.0
                meets_safety = (m["max_water_temp_C"] <= max_water_C
                                and (pcm_name is None or m["max_pcm_temp_C"] <= max_pcm_C)
                                and m["n_safety_violations"] == 0)
                row.update({
                    "solar_fraction_pct": m["solar_fraction"] * 100.0,
                    "useful_energy_kWh": m["useful_energy_kWh"],
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
        "# Fix — Standards-compliant collector:tank sizing, supplementary check (Rajasthan)\n",
        "The frozen `system_config_shared.yaml` (`tank.volume_L=50`, `collector.area_m2=1.5` "
        "-> storage/collector ratio = **33.3 L/m2**) is verified NON-COMPLIANT with "
        "IS 12976:2023 Sec 4.2/7.1 (40-100 L/m2 general range; 75 L/m2 reference ratio; "
        "37.5 L/m2 floor below which the standard's own f-chart correction is undefined) -- "
        "quotes checked directly against `PCM-Selection-ML-model/Sources/pdfs/IS12976_2023.pdf` "
        "this session, not taken from a paraphrase. Two resize directions tested, both anchored "
        "to the standard's 75 L/m2 reference ratio, using each (regime, pcm) case's own Phase 7 "
        "simulator-confirmed geometry (not re-searched -- this checks whether resizing changes "
        "the safety outcome for designs Phase 7 already found, not a fresh optimization at the "
        "new sizing). `system_config_shared.yaml` itself is untouched (frozen, identical across "
        "all 4 states) -- both resized configs exist only as in-memory `system_config_overrides` "
        "to `run_case()`.\n",
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
