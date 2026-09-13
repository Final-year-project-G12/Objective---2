"""
check_overheat_track_pcm.py
=============================
O2_Rajasthan_HighImpact_Fixes.md, Fix 1 — second, higher-Tm PCM shortlist
track for hot-dry regimes ("overheat-protection" framing, Hengstberger et
al. 2016 / Li et al. 2021: Tm should track the component's expected PEAK
operating temperature, not the delivery/comfort target Objective 1's
climate-only clustering selects for). The refreshed O1 shortlist (Tm
55-61C, see configs/states/rajasthan.yaml) is closer to Rajasthan's
68-89C observed tank range than the stale 48-50C shortlist was, but still
short of the 75-85C overheat-protection band this fix asks to test.

No PCM in this project's grounded database (55-row
PCM_Properties_cleaned_mice_pmm_detailed.csv, max Tm=70C) reaches 75-85C —
per CLAUDE.md, properties for this band are NOT invented from memory.
Two real candidates were sourced by direct PDF fetch of Rubitherm's own
current datasheets (verified against the actual manufacturer PDF, not a
search-snippet paraphrase — see data/pcm/rajasthan_overheat_track_candidates.csv
for the exact source URLs and datasheet version dates):
  - RT80HC: melting area 77-80C (main peak 78C), heat storage capacity
    220 kJ/kg +/-7.5% (combined sensible+latent, 70-85C range)
  - RT82:   melting area 77-82C (main peak 82C), heat storage capacity
    170 kJ/kg +/-7.5% (combined sensible+latent, 70-85C range)
("Heat storage capacity" combining sensible+latent over a stated range is
Rubitherm's own standard datasheet convention across their whole RT-line,
consistent with how the existing frozen pcm_database_rajasthan.csv already
carries other RT-series entries, e.g. RT70HC's 260 kJ/kg.)

This is kept as a clearly-separated supplementary track, NOT merged into
the frozen Objective 1 pcm_database_rajasthan.csv (which remains the O1
climate/MCDM-selected shortlist). Only Phase 3 (simulate) + Phase 4-style
gate checks are run here per regime -- NOT a full Phase 5-7 DOE/surrogate/
optimizer sweep (mirrors Fix 3's own "single supplementary case" scoping).

Run: python check_overheat_track_pcm.py
Output: results/fix1_overheat_track_supplementary.csv/.md
"""

from unittest.mock import patch

import pandas as pd

from config import RESULTS_DIR, BASE_DIR
from src.design.schema import DesignVector
from src.io_utils import get_regime
import src.simulation.run_case as run_case_module

CANDIDATES_PATH = BASE_DIR / "data" / "pcm" / "rajasthan_overheat_track_candidates.csv"
OUT_CSV = RESULTS_DIR / "fix1_overheat_track_supplementary.csv"
OUT_MD = RESULTS_DIR / "fix1_overheat_track_supplementary.md"

MAX_WATER_C = 75.0   # system_config_shared.yaml safety.max_water_temp_C
MAX_PCM_C = 65.0     # system_config_shared.yaml safety.max_pcm_temp_C

# Nominal geometry: same as the deployable-design search's default flow;
# diameter/count near the frozen-bounds midpoint (this is a supplementary
# feasibility check, not a re-optimization for these new candidates).
NOMINAL_DIAMETER_M = 0.06
NOMINAL_N_CAPSULE = 16
NOMINAL_FLOW_KG_S = 0.03


def _overheat_track_properties():
    df = pd.read_csv(CANDIDATES_PATH)
    return {row["name"]: row.to_dict() for _, row in df.iterrows()}


def run():
    candidates = _overheat_track_properties()
    rows = []

    for cid in (0, 1, 2):
        regime = get_regime("rajasthan", cid)
        for pcm_name, record in candidates.items():
            design = DesignVector(NOMINAL_DIAMETER_M, NOMINAL_N_CAPSULE, NOMINAL_FLOW_KG_S)
            with patch.object(run_case_module, "get_pcm_properties", return_value=record):
                result = run_case_module.run_case("rajasthan", cid, pcm_name, design)
            if not result["valid"]:
                rows.append({"cluster_id": cid, "pcm_name": pcm_name, "Tm_C": record["Tm_C"],
                             "valid": False, "reason": result["reason"]})
                continue
            m = result["metrics"]
            clears_pcm_limit = m["max_pcm_temp_C"] <= MAX_PCM_C
            clears_water_limit = m["max_water_temp_C"] <= MAX_WATER_C
            rows.append({
                "cluster_id": cid, "pcm_name": pcm_name, "Tm_C": record["Tm_C"], "valid": True,
                "Tm_target_C_this_regime": regime["Tm_target_C"],
                "solar_fraction": m["solar_fraction"], "useful_energy_kWh": m["useful_energy_kWh"],
                "max_water_temp_C": m["max_water_temp_C"], "max_pcm_temp_C": m["max_pcm_temp_C"],
                "clears_65C_pcm_safety_limit": clears_pcm_limit,
                "clears_75C_water_safety_limit": clears_water_limit,
                "n_safety_violations": m["n_safety_violations"],
                "final_f_melt": m["final_f_melt"],
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    n_pass = int(df.get("clears_65C_pcm_safety_limit", pd.Series(dtype=bool)).sum())
    n_total = len(df)
    lines = [
        "# Fix 1 — Overheat-protection PCM track, supplementary check (Rajasthan)\n",
        f"{n_pass}/{n_total} (regime x candidate) combinations clear the {MAX_PCM_C:.0f} C PCM "
        f"safety limit, vs. 0/45 for the original climate-only shortlist (Phase 7, pre-refresh) "
        f"and the refreshed 55-61 C O1 shortlist (see phase7_deployable_design_per_regime.csv — "
        f"plain tank selected in all 3 regimes post-refresh too).\n",
        "Nominal geometry used (NOT re-optimized for these candidates — this is a feasibility "
        f"check, not a design search): capsule_diameter_m={NOMINAL_DIAMETER_M}, "
        f"n_capsule={NOMINAL_N_CAPSULE}, flow_rate_kg_s={NOMINAL_FLOW_KG_S}.\n",
    ]
    cols = list(df.columns)
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "|".join(["---"] * len(cols)) + "|")
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(df.to_string(index=False))
    print(f"\n{n_pass}/{n_total} combinations clear the {MAX_PCM_C:.0f} C PCM safety limit.")
    print(f"Saved: {OUT_CSV}")
    print(f"Saved: {OUT_MD}")
    return df


if __name__ == "__main__":
    run()
