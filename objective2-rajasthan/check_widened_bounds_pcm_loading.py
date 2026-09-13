"""
check_widened_bounds_pcm_loading.py
=====================================
O2_Rajasthan_HighImpact_Fixes.md, Fix 3 — the frozen design_bounds_shared.yaml
(sphere-only, capsule_count<=24, capsule_diameter_m<=0.08) caps the reachable
PCM volume fraction at ~12.9% of tank volume, below the 15-20% loading Chen
et al. (2025) — this project's own cited DOE baseline — reports results at.
That makes the Phase 5/7 "PCM gives < 0.2% improvement" conclusion a
conclusion about a narrower design space than the comparison baseline uses.

This is a single supplementary check per regime, NOT a full Phase 5-7
DOE/surrogate/optimizer re-run (mirrors the fix doc's own scoping: "even as
a single supplementary case per regime rather than a full DOE re-run").
It does NOT edit design_bounds_shared.yaml (frozen, identical across all 4
states) — the widened bounds exist only as an in-memory override passed to
run_case()'s existing `design_bounds` parameter, exactly the seam Phase 4's
gates.py already uses for its own limiting-case tests.

Run: python check_widened_bounds_pcm_loading.py
Output: results/fix3_widened_bounds_supplementary.csv/.md
"""

import copy
import json

import pandas as pd

from config import RESULTS_DIR
from src.design.schema import DesignVector
from src.io_utils import load_design_bounds, get_regime, load_pcm_database
from src.simulation.run_case import run_case

OUT_CSV = RESULTS_DIR / "fix3_widened_bounds_supplementary.csv"
OUT_MD = RESULTS_DIR / "fix3_widened_bounds_supplementary.md"

# Widened envelope: only capsule_diameter_m / capsule_count / the derived
# pcm_thickness_m ceiling change; shape/arrangement/flow bounds untouched
# (still sphere-only, staggered-only — Fix 3 is about loading %, not the
# shape/arrangement scope cut, which is separately-justified future work).
WIDENED_DIAMETER_MAX_M = 0.12
WIDENED_COUNT_MAX = 40


def widened_bounds():
    bounds = copy.deepcopy(load_design_bounds())
    bounds["capsule_diameter_m"]["max"] = WIDENED_DIAMETER_MAX_M
    bounds["pcm_thickness_m"]["max"] = WIDENED_DIAMETER_MAX_M / 2.0
    bounds["capsule_count"]["max"] = WIDENED_COUNT_MAX
    return bounds


def frozen_bounds():
    return load_design_bounds()


def _search_max_loading(state, cid, pcm_name, bounds, diam, count_grid, flow_kg_s=0.03):
    """Among (diameter=diam, count in count_grid) sweep, return the row with
    the largest geometrically-valid PCM volume fraction."""
    best = None
    for n_capsule in count_grid:
        design = DesignVector(capsule_diameter_m=diam, n_capsule=n_capsule, flow_rate_kg_s=flow_kg_s)
        result = run_case(state, cid, pcm_name, design, design_bounds=bounds)
        if not result["valid"]:
            continue
        frac = result["geometry"]["pcm_volume_fraction"]
        if best is None or frac > best["geom_pcm_volume_fraction"]:
            best = {
                "n_capsule": n_capsule, "capsule_diameter_m": diam,
                "geom_pcm_volume_fraction": frac, "result": result,
            }
    return best


def run():
    frozen = frozen_bounds()
    widened = widened_bounds()

    rows = []
    for cid in (0, 1, 2):
        regime = get_regime("rajasthan", cid)
        top_pcm = regime["pcm_shortlist"][0]

        # Frozen-bounds max achievable (sanity anchor — should reproduce the
        # documented ~12.9% ceiling).
        frozen_best = _search_max_loading(
            "rajasthan", cid, top_pcm, frozen,
            diam=frozen["capsule_diameter_m"]["max"],
            count_grid=range(frozen["capsule_count"]["min"], frozen["capsule_count"]["max"] + 1),
        )
        # Widened-bounds max achievable, targeting >=15%.
        widened_best = _search_max_loading(
            "rajasthan", cid, top_pcm, widened,
            diam=widened["capsule_diameter_m"]["max"],
            count_grid=range(frozen["capsule_count"]["min"], widened["capsule_count"]["max"] + 1, 2),
        )

        for label, best in (("frozen_bounds", frozen_best), ("widened_bounds", widened_best)):
            if best is None:
                rows.append({"cluster_id": cid, "pcm_name": top_pcm, "bounds": label,
                             "valid": False})
                continue
            m = best["result"]["metrics"]
            rows.append({
                "cluster_id": cid, "pcm_name": top_pcm, "bounds": label, "valid": True,
                "capsule_diameter_m": best["capsule_diameter_m"], "n_capsule": best["n_capsule"],
                "pcm_volume_fraction": best["geom_pcm_volume_fraction"],
                "reaches_15pct_chen_comparable": best["geom_pcm_volume_fraction"] >= 0.15,
                "solar_fraction": m["solar_fraction"], "useful_energy_kWh": m["useful_energy_kWh"],
                "max_water_temp_C": m["max_water_temp_C"], "max_pcm_temp_C": m["max_pcm_temp_C"],
                "n_safety_violations": m["n_safety_violations"],
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    lines = ["# Fix 3 — Widened-bounds supplementary check (Rajasthan)\n",
             "One supplementary case per regime (not a full Phase 5-7 DOE/surrogate/optimizer "
             "re-run), comparing the frozen design_bounds_shared.yaml ceiling against a "
             f"widened envelope (capsule_diameter_m max {WIDENED_DIAMETER_MAX_M} m, capsule_count "
             f"max {WIDENED_COUNT_MAX}) built purely as an in-memory `design_bounds` override to "
             "`run_case()` — design_bounds_shared.yaml itself is untouched (frozen, identical "
             "across all 4 states).\n"]
    for cid in (0, 1, 2):
        sub = df[df["cluster_id"] == cid]
        lines.append(f"\n## Cluster {cid}\n")
        cols = list(sub.columns)
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("|" + "|".join(["---"] * len(cols)) + "|")
        for _, r in sub.iterrows():
            lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
        lines.append("")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(df.to_string(index=False))
    print(f"\nSaved: {OUT_CSV}")
    print(f"Saved: {OUT_MD}")
    return df


if __name__ == "__main__":
    run()
