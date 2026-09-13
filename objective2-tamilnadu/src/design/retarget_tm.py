"""
src/design/retarget_tm.py
=============================
Deliberate, documented methodology revision (NOT a silent override) —
re-derives each regime's PCM melting-point target, `Tm_target_C`, from
this tank's own simulated water-temperature behaviour, replacing
Objective 1's climate/delivery-anchored formula
(`04b_climate_signature.py`, `SHARE_PCM=0.5`) for the purpose of PCM
selection in Objective 2.

WHY: Gate 3 (Phase 4) proved with a diagnostic PCM (synthetic Tm=40°C)
that a melting point matched to the tank's REAL operating range beats
plain tank decisively (55.19% vs 52.26% solar fraction), while the real
shortlisted PCM (n-Octacosane, Tm=61.6°C, derived from the climate/
delivery formula) does not (51.16% vs 52.26%). Phase 7's full
400-candidate search confirmed this generalizes: every regime's original
shortlist (all PCMs in the 56.5-64°C range) loses to plain tank by ~0.08%
at best, because the tank's real charging-hour water temperature sits
well below the old 57°C target in every regime (see
docs_objective2/12_TM_TARGET_RETARGETING.md for the measured
distributions).

METHOD: for each regime, run a single STANDARD reference plain-tank
design (capsule_diameter_m=0.05, n_capsule=16, flow_rate_kg_s=0.030 —
the exact midpoint of design_bounds_shared.yaml's bounds, chosen once,
identically for all 5 regimes, so no regime's target is cherry-picked
toward any particular PCM) through the full-year simulator, and take the
MEDIAN water temperature during hours the collector is actually
delivering heat (`Q_collector_Wh > 0`). This is the temperature a PCM
must melt at on a TYPICAL charging day (not just the sunniest ones) to
actually cycle every year -- the physical requirement the climate/
delivery formula never checked directly.

PCM re-selection: reuses Objective 1's own `feasibility_survivors_by_
cluster.csv` (latent heat / cycling / supercooling / corrosion / safety
pass flags — unchanged, these don't depend on Tm_target), recomputes each
candidate's melting-window pass/fail against the NEW target using the
same [target-5, target+8] °C window Objective 1's own file uses (visible
directly in its `window_lo`/`window_hi` columns), and ranks window
survivors by |Tm_C - new_target| (closest first) -- a simpler, explicitly
documented substitute for Objective 1's full 4-method MCDM consensus
(TOPSIS/GRA/PROMETHEE/VIKOR), not a re-implementation of it. Top 3 per
regime become the new `pcm_shortlist`.

Writes: configs/states/<state>.yaml (Tm_target_C, pcm_shortlist per
regime, updated in place) and results/<state>/tm_retargeting_report.csv
(the full before/after evidence table).
"""

import sys

import pandas as pd
import yaml

from config import BASE_DIR, RESULTS_DIR, CONFIGS_DIR
from src.design.schema import DesignVector
from src.simulation.run_case import run_case
from src.io_utils import load_state_config

REFERENCE_DESIGN = DesignVector(capsule_diameter_m=0.05, n_capsule=16, flow_rate_kg_s=0.030)
WINDOW_LO_OFFSET = -5.0   # matches Objective 1's own feasibility_survivors_by_cluster.csv window
WINDOW_HI_OFFSET = 8.0    # (window_lo=52, window_hi=65 for the old Tm_target=57 -> -5/+8)
TOP_N = 3


def derive_tm_targets(state: str) -> dict:
    """Returns {cluster_id: new_Tm_target_C} from the reference design's
    plain-tank charging-hour water-temperature median."""
    cfg = load_state_config(state)
    targets = {}
    for regime in cfg["regimes"]:
        cid = regime["cluster_id"]
        out = run_case(state, cid, None, REFERENCE_DESIGN, record_hourly=True)
        hourly = out["hourly"]
        charging = hourly[hourly["Q_collector_Wh"] > 0]
        targets[cid] = float(charging["T_w_C"].median())
        print(f"  regime {cid}: charging-hour T_water median = {targets[cid]:.1f} C "
              f"(all-hour median = {hourly['T_w_C'].median():.1f} C, n_charging_hours={len(charging)})")
    return targets


REQUIRED_SIMULATOR_PROPERTIES = [
    "TC_W_mK", "density_liquid_kg_m3", "density_solid_kg_m3",
    "Cp_liquid_kJ_kgK", "Cp_solid_kJ_kgK",
]


def select_shortlist_for_target(feasibility_df: pd.DataFrame, pcm_db_df: pd.DataFrame,
                                 cluster_id: int, new_target: float, top_n: int = TOP_N) -> list:
    """Re-filters Objective 1's own feasibility_survivors table (latent
    heat / cycling / supercooling / corrosion / safety flags unchanged)
    against a recomputed melting window centered on new_target, then
    ranks survivors by proximity to the new target.

    Also requires every REQUIRED_SIMULATOR_PROPERTIES field to be
    non-null in the full PCM database -- a handful of literature-only
    entries (e.g. "C22H46 (docosane-class paraffin)": Tm and latent heat
    known, but density/Cp/TC never measured or imputed,
    any_property_imputed=False) pass every feasibility flag yet cannot
    actually be simulated (capsule_enthalpy.pcm_props_from_record needs
    all five fields). These were previously never selected because their
    Tm sat outside the OLD 52-65C window; re-targeting to a lower window
    can bring them into range on melting point alone, so this check must
    be explicit here rather than assumed from the feasibility flags."""
    complete = pcm_db_df.dropna(subset=REQUIRED_SIMULATOR_PROPERTIES)["name"]

    df = feasibility_df[feasibility_df["cluster_id"] == cluster_id].copy()
    lo, hi = new_target + WINDOW_LO_OFFSET, new_target + WINDOW_HI_OFFSET
    df["new_pass_melting_window"] = df["Tm_C"].between(lo, hi)
    df["new_passes_all"] = (
        df["new_pass_melting_window"] & df["pass_latent_heat"] & df["pass_cycling"]
        & df["pass_supercooling"] & df["pass_corrosion"] & df["pass_safety"]
        & df["name"].isin(complete)
    )
    survivors = df[df["new_passes_all"]].copy()
    survivors["distance_to_target"] = (survivors["Tm_C"] - new_target).abs()
    survivors = survivors.sort_values("distance_to_target")
    return survivors.head(top_n)[["name", "Tm_C", "latent_heat_kJ_kg", "distance_to_target"]].to_dict("records")


def retarget_all(state: str) -> pd.DataFrame:
    print(f"Deriving new Tm_target_C per regime for state={state} (reference design: "
          f"{REFERENCE_DESIGN.capsule_diameter_m}m / {REFERENCE_DESIGN.n_capsule} capsules / "
          f"{REFERENCE_DESIGN.flow_rate_kg_s} kg/s, plain tank, full year) ...")
    new_targets = derive_tm_targets(state)

    feasibility_path = BASE_DIR / "data" / "objective1" / "feasibility_survivors_by_cluster.csv"
    feasibility_df = pd.read_csv(feasibility_path)
    pcm_db_df = pd.read_csv(BASE_DIR / "data" / "objective1" / f"pcm_database_{state}.csv")

    cfg = load_state_config(state)
    rows = []
    for regime in cfg["regimes"]:
        cid = regime["cluster_id"]
        old_target = regime["Tm_target_C"]
        old_shortlist = regime["pcm_shortlist"]
        new_target = new_targets[cid]
        new_shortlist_records = select_shortlist_for_target(feasibility_df, pcm_db_df, cid, new_target)
        new_shortlist = [r["name"] for r in new_shortlist_records]

        rows.append({
            "cluster_id": cid, "label": regime.get("label", ""),
            "old_Tm_target_C": old_target, "new_Tm_target_C": round(new_target, 1),
            "old_pcm_shortlist": "; ".join(old_shortlist),
            "new_pcm_shortlist": "; ".join(new_shortlist) if new_shortlist else "NONE (no survivor in window)",
            "new_shortlist_Tm_C": "; ".join(f"{r['Tm_C']}" for r in new_shortlist_records),
            "new_shortlist_latent_heat_kJ_kg": "; ".join(f"{r['latent_heat_kJ_kg']}" for r in new_shortlist_records),
        })

        regime["Tm_target_C"] = round(new_target, 1)
        if new_shortlist:
            regime["pcm_shortlist"] = new_shortlist
        print(f"  regime {cid}: Tm_target {old_target}C -> {round(new_target,1)}C | "
              f"shortlist {old_shortlist} -> {new_shortlist}")

    report_df = pd.DataFrame(rows)
    out_dir = RESULTS_DIR / state
    out_dir.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(out_dir / "tm_retargeting_report.csv", index=False)
    print(f"\nSaved: {out_dir / 'tm_retargeting_report.csv'}")

    state_path = CONFIGS_DIR / "states" / f"{state}.yaml"
    with open(state_path, "r", encoding="utf-8") as f:
        raw_text = f.read()
    with open(state_path, "w", encoding="utf-8") as f:
        f.write(_rewrite_yaml_preserving_header(raw_text, cfg))
    print(f"Saved: {state_path} (Tm_target_C / pcm_shortlist updated in place)")

    return report_df


def _rewrite_yaml_preserving_header(raw_text: str, cfg: dict) -> str:
    """Keeps the file's original header comments (provenance/history)
    intact above the YAML-dumped body, so the file still documents where
    it came from -- only the machine-readable fields are regenerated."""
    header_lines = []
    for line in raw_text.splitlines(keepends=True):
        if line.strip().startswith("#") or line.strip() == "":
            header_lines.append(line)
        else:
            break
    header = "".join(header_lines)
    header += (
        "\n# ----------------------------------------------------------------------------\n"
        "# TM_TARGET_C RETARGETED (deliberate Objective 2 methodology revision, not a\n"
        "# silent edit) -- see docs_objective2/12_TM_TARGET_RETARGETING.md and\n"
        "# results/tamilnadu/tm_retargeting_report.csv for the full before/after\n"
        "# evidence. Tm_target_C and pcm_shortlist below now reflect this tank's own\n"
        "# simulated charging-hour water-temperature median per regime, not Objective\n"
        "# 1's climate/delivery-anchored formula. Re-run Phases 3-8 after this change\n"
        "# (framework doc Phase 0 gate).\n"
        "# ----------------------------------------------------------------------------\n\n"
    )
    body = yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True, width=100)
    return header + body


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "tamilnadu"
    retarget_all(state)
