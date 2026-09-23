"""
src/design/retarget_tm.py
=============================
Step 4 of the 2026-09-20 fix plan ("Objective2 rajasthan fix plan.md") —
PORTED FROM objective2-tamilnadu/src/design/retarget_tm.py, decision D2
("re-target, keep the O1 capped value as a reported comparison").

WHY: Rajasthan targets Tm_target_C = 67.0 C in every regime (Objective
1's climate/delivery-anchored formula), but a reference plain-tank
simulation shows median charging-hour tank water sitting well below that
in every regime, so most of the shortlisted PCMs rarely melt (see
CLAUDE.md §3.2-3.4 for the delivery-temperature history this compounds).
This module re-derives a Tm target from the tank's own simulated
behaviour instead, the same way Tamil Nadu's Phase 7 full-search finding
motivated its version of this file.

METHOD: identical to Tamil Nadu's — for each regime, run one STANDARD
reference plain-tank design (capsule_diameter_m=0.05, n_capsule=16,
flow_rate_kg_s=0.030, the design_bounds_shared.yaml midpoint) through the
full-year simulator, take the MEDIAN water temperature during hours the
collector is actually delivering heat (Q_collector_Wh > 0), and use the
accepted window [target-5, target+8] deg C (matches Objective 1's own
window_lo/window_hi convention).

ADAPTATIONS FOR RAJASTHAN (fix plan step 4.2 — Tamil Nadu's script
assumes column names that do not exist here):
  - Rajasthan's feasibility_survivors_by_cluster.csv uses `pcm_id` (not
    `name`) as the PCM-name column, and has no separate
    "_kappa_calibrated" file -- calibrated_kappa/rescuable_by_kappa/
    calibration_status already live in the one file
    (data/objective1/feasibility_survivors_by_cluster.csv).
  - Its per-criterion pass/fail columns are `c2_absolute_band`,
    `c3_latent_heat`, `c4_cycling`, `c5_supercooling` (string "pass"/
    "fail", same convention as Tamil Nadu) plus `c7_corrosion_veto` and
    `c8_safety`, which here are strings ("pass"/"not_applicable"/
    "flag_..."), NOT the separate `survives_c7_corrosion` /
    `survives_c8_safety` booleans Tamil Nadu's file has. A survivor
    passes c7/c8 iff the string does not start with "fail".
  - Objective 1's own `calibrated_kappa` per cluster (already the
    authoritative rescue mechanism per CLAUDE.md §3.1) is applied to
    `c3_latent_heat` the same way Objective 1 itself applies it (a
    candidate whose raw c3 is "fail" but is `rescuable_by_kappa=True`
    still counts as passing) -- this mirrors using the kappa-calibrated
    file in Tamil Nadu, adapted to Rajasthan's single-file layout.
  - Any missing column referenced here fails loudly (raises), per the
    fix plan's "map the columns explicitly and fail loudly on any
    missing one" instruction -- no silent `.get()` defaults.

Writes: configs/states/rajasthan.yaml (Tm_target_C / pcm_shortlist per
regime, updated in place; the OLD O1-derived value is preserved alongside
as `o1_Tm_target_C` per decision D2 -- "keep the O1 capped value as a
reported comparison") and results/tm_retargeting_report.csv (the full
before/after evidence table, including any PCM dropped for missing
simulator-complete properties).
"""

import sys

import pandas as pd
import yaml

from config import BASE_DIR, RESULTS_DIR, CONFIGS_DIR
from src.design.schema import DesignVector
from src.simulation.run_case import run_case
from src.io_utils import load_state_config

REFERENCE_DESIGN = DesignVector(capsule_diameter_m=0.05, n_capsule=16, flow_rate_kg_s=0.030,
                                 capsule_arrangement="staggered")   # fixed reference arrangement,
                                 # identical rationale to Tamil Nadu's version: Tm retargeting
                                 # derives a target from tank behaviour, not from arrangement search.
WINDOW_LO_OFFSET = -5.0   # matches Objective 1's own feasibility_survivors_by_cluster.csv window
WINDOW_HI_OFFSET = 8.0
TOP_N = 3

REQUIRED_COLUMNS = [
    "cluster_id", "pcm_id", "Tm_C", "latent_heat_kJ_kg",
    "c2_absolute_band", "c3_latent_heat", "c4_cycling", "c5_supercooling",
    "c7_corrosion_veto", "c8_safety", "rescuable_by_kappa", "calibrated_kappa",
]
REQUIRED_SIMULATOR_PROPERTIES = [
    "TC_W_mK", "density_liquid_kg_m3", "density_solid_kg_m3",
    "Cp_liquid_kJ_kgK", "Cp_solid_kJ_kgK",
]


def _require_columns(df: pd.DataFrame, required: list, source: str):
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"{source} is missing required column(s) {missing} -- "
                        f"found columns: {list(df.columns)}. Fix the column mapping "
                        f"in retarget_tm.py rather than silently defaulting.")


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


def select_shortlist_for_target(feasibility_df: pd.DataFrame, pcm_db_df: pd.DataFrame,
                                 cluster_id: int, new_target: float, top_n: int = TOP_N) -> tuple:
    """Re-filters Objective 1's own feasibility_survivors_by_cluster.csv
    (latent heat / cycling / supercooling / corrosion / safety flags
    unchanged) against a recomputed melting window centered on
    new_target, then ranks survivors by proximity to the new target.

    Returns (records, dropped_incomplete) -- dropped_incomplete lists any
    PCM that passed every flag but is missing a REQUIRED_SIMULATOR_PROPERTIES
    field in the full database (fix plan step 4.3: "require simulator-
    complete PCM properties ... and list any dropped PCMs with the reason")."""
    complete = set(pcm_db_df.dropna(subset=REQUIRED_SIMULATOR_PROPERTIES)["name"])
    incomplete = set(pcm_db_df["name"]) - complete

    df = feasibility_df[feasibility_df["cluster_id"] == cluster_id].copy()
    lo, hi = new_target + WINDOW_LO_OFFSET, new_target + WINDOW_HI_OFFSET
    df["new_pass_melting_window"] = df["Tm_C"].between(lo, hi)

    # c3_latent_heat, rescued by Objective 1's own kappa calibration
    # (CLAUDE.md §3.1) exactly as O1's mcdm_topk_by_cluster.csv already does.
    df["c3_pass_or_rescued"] = (df["c3_latent_heat"] == "pass") | df["rescuable_by_kappa"].fillna(False)

    # c7/c8 here are strings ("pass" / "not_applicable" / "flag_...") not
    # booleans -- a real veto is the literal string "fail"; anything else
    # (pass, not_applicable, an unverified-property flag) does not veto.
    df["c7_ok"] = ~df["c7_corrosion_veto"].astype(str).str.startswith("fail")
    df["c8_ok"] = ~df["c8_safety"].astype(str).str.startswith("fail")

    df["new_passes_all"] = (
        df["new_pass_melting_window"]
        & (df["c2_absolute_band"] == "pass")
        & df["c3_pass_or_rescued"]
        & (df["c4_cycling"] == "pass")
        & (df["c5_supercooling"] == "pass")
        & df["c7_ok"] & df["c8_ok"]
    )

    dropped_incomplete = sorted(set(df.loc[df["new_passes_all"], "pcm_id"]) & incomplete)
    df["new_passes_all"] = df["new_passes_all"] & df["pcm_id"].isin(complete)

    survivors = df[df["new_passes_all"]].copy()
    survivors["distance_to_target"] = (survivors["Tm_C"] - new_target).abs()
    survivors = survivors.sort_values("distance_to_target")
    records = survivors.head(top_n)[["pcm_id", "Tm_C", "latent_heat_kJ_kg", "distance_to_target"]].rename(
        columns={"pcm_id": "name"}).to_dict("records")
    return records, dropped_incomplete


def retarget_all(state: str) -> pd.DataFrame:
    print(f"Deriving new Tm_target_C per regime for state={state} (reference design: "
          f"{REFERENCE_DESIGN.capsule_diameter_m}m / {REFERENCE_DESIGN.n_capsule} capsules / "
          f"{REFERENCE_DESIGN.flow_rate_kg_s} kg/s, plain tank, full year) ...")
    new_targets = derive_tm_targets(state)

    feasibility_path = BASE_DIR / "data" / "objective1" / "feasibility_survivors_by_cluster.csv"
    feasibility_df = pd.read_csv(feasibility_path)
    _require_columns(feasibility_df, REQUIRED_COLUMNS, str(feasibility_path))
    pcm_db_df = pd.read_csv(BASE_DIR / "data" / "objective1" / f"pcm_database_{state}.csv")
    _require_columns(pcm_db_df, ["name"] + REQUIRED_SIMULATOR_PROPERTIES, str(pcm_db_df))

    cfg = load_state_config(state)
    rows = []
    for regime in cfg["regimes"]:
        cid = regime["cluster_id"]
        old_target = regime["Tm_target_C"]
        old_shortlist = regime["pcm_shortlist"]
        new_target = new_targets[cid]
        new_shortlist_records, dropped_incomplete = select_shortlist_for_target(
            feasibility_df, pcm_db_df, cid, new_target)
        new_shortlist = [r["name"] for r in new_shortlist_records]

        rows.append({
            "cluster_id": cid, "label": regime.get("label", ""),
            "old_o1_Tm_target_C": old_target, "new_Tm_target_C": round(new_target, 1),
            "old_pcm_shortlist": "; ".join(old_shortlist),
            "new_pcm_shortlist": "; ".join(new_shortlist) if new_shortlist else "NONE (no survivor in window)",
            "new_shortlist_Tm_C": "; ".join(f"{r['Tm_C']}" for r in new_shortlist_records),
            "new_shortlist_latent_heat_kJ_kg": "; ".join(f"{r['latent_heat_kJ_kg']}" for r in new_shortlist_records),
            "dropped_missing_simulator_properties": "; ".join(dropped_incomplete) if dropped_incomplete else "",
        })

        # Decision D2: re-target, but KEEP the O1 value as a reported
        # comparison rather than overwriting it.
        regime["o1_Tm_target_C"] = old_target
        regime["Tm_target_C"] = round(new_target, 1)
        if new_shortlist:
            regime["pcm_shortlist"] = new_shortlist
        print(f"  regime {cid}: Tm_target {old_target}C -> {round(new_target,1)}C | "
              f"shortlist {old_shortlist} -> {new_shortlist}"
              + (f"  [dropped, missing sim properties: {dropped_incomplete}]" if dropped_incomplete else ""))

    report_df = pd.DataFrame(rows)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = RESULTS_DIR / "tm_retargeting_report.csv"
    report_df.to_csv(report_path, index=False)
    print(f"\nSaved: {report_path}")

    state_path = CONFIGS_DIR / "states" / f"{state}.yaml"
    with open(state_path, "r", encoding="utf-8") as f:
        raw_text = f.read()
    with open(state_path, "w", encoding="utf-8") as f:
        f.write(_rewrite_yaml_preserving_header(raw_text, cfg))
    print(f"Saved: {state_path} (Tm_target_C / o1_Tm_target_C / pcm_shortlist updated in place)")

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
        "# TM_TARGET_C RETARGETED (step 4, 2026-09-20 fix plan, decision D2: re-target,\n"
        "# keep the O1 value as a reported comparison) -- ported from\n"
        "# objective2-tamilnadu/src/design/retarget_tm.py. Each regime's Tm_target_C\n"
        "# below now reflects this tank's own simulated charging-hour water-temperature\n"
        "# median (see results/tm_retargeting_report.csv for the full before/after\n"
        "# evidence); o1_Tm_target_C keeps Objective 1's original climate/delivery-\n"
        "# anchored value for comparison. Re-run Phases 3-8 after this change\n"
        "# (framework doc Phase 0 gate).\n"
        "# ----------------------------------------------------------------------------\n\n"
    )
    body = yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True, width=100)
    return header + body


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "rajasthan"
    retarget_all(state)
