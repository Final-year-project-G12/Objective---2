"""
fetch_missing_from_obj1.py — Rajasthan
======================================
Fills the six Tamil-Nadu-shaped files that the frozen Rajasthan package was
missing. Everything here comes from era5-rajasthan; nothing is invented.

  1. daily_aggregates_rajasthan.csv    full 320-point table (was medoids only)
  2. suntimes.csv                      full 320-point table (was medoids only)
  3. kmeans_comparison_rajasthan.csv   projection of bic_selection_rajasthan.csv
  4. tier2_signature_rajasthan.csv     copy of daily_aggregates_rajasthan_summary
  5. pcm_database_rajasthan.csv        62-row normalised PCM table, rebuilt
  6. pca_loadings.csv                  PCA loadings, re-fit and verified

Destination names follow Tamil Nadu exactly: state-suffixed where Tamil Nadu
suffixes, unsuffixed where it does not (suntimes.csv, pca_loadings.csv).

Safe to re-run — idempotent.
"""
import shutil
import sys

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from config import (
    STATE, OBJ1_PROCESSED_DIR, PCM_PROPERTIES_CSV, FROZEN_DIR, ensure_dirs,
)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ── Constants copied from the Objective 1 scripts so the two cannot drift ────
# 04_climate_signature_rajasthan.py:255
PCA_BLOCK = ["Ta_mean", "Ta_p95", "Ta_p05", "T_sunrise_mean", "T_noon_mean",
             "HDD18", "CDD24", "elevation_m"]
# 07_feasibility_filter_rajasthan.py:156
ABSOLUTE_TM_MIN, ABSOLUTE_TM_MAX = 42.0, 70.0

# Whether to append the 7 Singh2025 Table-2 literature PCMs to the 55 rows of
# PCM_Properties_cleaned_mice_pmm_detailed.csv.
#
# FALSE (current): the database is exactly the cleaned manufacturer file — 55
# rows, every property MICE-RF-PMM completed and traceable to a datasheet. The
# literature rows carry only Tm and latent heat; density, Cp, TC and cycles are
# NaN for all seven, so they enter the MCDM matrix with most criteria missing.
#
# Because the PCM table is state-independent (verified: all 23 columns of
# Rajasthan's rebuild matched Tamil Nadu's exactly), this writes BOTH states.
INCLUDE_LITERATURE_ROWS = False
PCM_DB_STATES = {"rajasthan": "pcm_database_rajasthan.csv",
                 "tamil_nadu": "pcm_database_tamilnadu.csv"}

# era5-tamilnadu/06_build_pcm_database.py:63-65 — the properties whose *_imputed
# flags count toward n_properties_imputed.
IMPUTABLE_PROPS = ["Tm_melting", "Tm_freezing", "latent_heat_melting", "density_liquid",
                   "density_solid", "Cp_liquid", "Cp_solid", "TC_liquid", "TC_solid",
                   "TC_both", "cycles_tested", "flammability"]

# Singh2025 Table 2 — the same seven literature rows Tamil Nadu's
# 06_build_pcm_database.py:105-121 uses and 07_feasibility_filter_rajasthan.py
# reuses verbatim. Densities on the generic paraffin come from Tamil Nadu's row.
LITERATURE_PCMS = [
    {"name": "Myristic acid", "family": "Fatty acid", "pcm_type": "Organic",
     "Tm_C": 53.0, "latent_heat_kJ_kg": 190.0},
    {"name": "Palmitic acid", "family": "Fatty acid", "pcm_type": "Organic",
     "Tm_C": 63.0, "latent_heat_kJ_kg": 185.4},
    {"name": "Myristic-Palmitic eutectic (58/42)", "family": "Eutectic",
     "pcm_type": "Organic", "Tm_C": 42.6, "latent_heat_kJ_kg": 169.7},
    {"name": "Palmitic-Stearic eutectic (64.2/35.8)", "family": "Eutectic",
     "pcm_type": "Organic", "Tm_C": 52.3, "latent_heat_kJ_kg": 181.7},
    {"name": "Paraffin wax (generic)", "family": "Paraffin", "pcm_type": "Organic",
     "Tm_C": 64.0, "latent_heat_kJ_kg": 173.6,
     "density_solid_kg_m3": 916.0, "density_liquid_kg_m3": 790.0},
    {"name": "C22H46 (docosane-class paraffin)", "family": "Paraffin",
     "pcm_type": "Organic", "Tm_C": 44.5, "latent_heat_kJ_kg": 249.0},
    {"name": "C30H62 (triacontane-class paraffin)", "family": "Paraffin",
     "pcm_type": "Organic", "Tm_C": 65.5, "latent_heat_kJ_kg": 252.0},
]

# Tamil Nadu's pcm_database_<state>.csv column order.
TN_PCM_COLS = [
    "name", "family", "pcm_type", "Tm_C", "Tm_freezing_C", "latent_heat_kJ_kg",
    "density_liquid_kg_m3", "density_solid_kg_m3", "Cp_liquid_kJ_kgK",
    "Cp_solid_kJ_kgK", "TC_W_mK", "cycles_tested", "cycles_tested_status",
    "flammable", "supercooling_K", "n_properties_imputed", "any_property_imputed",
    "source", "rho_H_MJ_m3", "Cp_avg_kJ_kgK", "cycles_confidence",
    "in_absolute_band", "corrosion_class",
]


def step(n, msg):
    print(f"\n[{n}/6] {msg}")


def copy_large(src, dest_name):
    dest = FROZEN_DIR / dest_name
    if not src.exists():
        print(f"  [MISSING] {src}")
        return
    shutil.copy2(src, dest)
    print(f"  [OK] {dest_name}  ({dest.stat().st_size / 1e6:.1f} MB)")


# ── 1 + 2. Full per-point tables ────────────────────────────────────────────
def fetch_full_tables():
    step(1, "Full daily aggregates (all 320 points, was medoids only) ...")
    copy_large(OBJ1_PROCESSED_DIR / f"daily_aggregates_{STATE}.csv",
               f"daily_aggregates_{STATE}.csv")
    step(2, "Full sun-event times (all 320 points, was medoids only) ...")
    copy_large(OBJ1_PROCESSED_DIR / "suntimes.csv", "suntimes.csv")


# ── 3. KMeans comparison ────────────────────────────────────────────────────
def fetch_kmeans_comparison():
    step(3, "KMeans-vs-GMM comparison ...")
    src = OBJ1_PROCESSED_DIR / f"bic_selection_{STATE}.csv"
    if not src.exists():
        print(f"  [MISSING] {src}")
        return
    bic = pd.read_csv(src)
    out = bic[["k", "kmeans_silhouette"]].copy()
    dest = FROZEN_DIR / f"kmeans_comparison_{STATE}.csv"
    out.to_csv(dest, index=False)
    print(f"  [OK] kmeans_comparison_{STATE}.csv  ({len(out)} rows, k="
          f"{out['k'].min()}..{out['k'].max()})")


# ── 4. Tier-2 signature ─────────────────────────────────────────────────────
def fetch_tier2():
    step(4, "Tier-2 signature ...")
    src = OBJ1_PROCESSED_DIR / f"daily_aggregates_{STATE}_summary.csv"
    if not src.exists():
        print(f"  [MISSING] {src}")
        return
    shutil.copy2(src, FROZEN_DIR / f"tier2_signature_{STATE}.csv")
    df = pd.read_csv(src)
    print(f"  [OK] tier2_signature_{STATE}.csv  ({len(df)} points, "
          f"{len(df.columns)} cols)")
    print("       This IS Rajasthan's tier 2 — 04_climate_signature_rajasthan.py:344")
    print("       loads this exact file as `tier2`.")
    missing = ["Ta_mean_true", "Ta_p95_true", "Ta_p05_true",
               "RH_mean_true", "wind_mean_true"]
    print(f"       No Rajasthan equivalent for Tamil Nadu's {', '.join(missing)} —")
    print("       Rajasthan derives temperature/RH/wind at sun events in Tier 1")
    print("       instead, and those columns are in climate_signature_rajasthan.csv.")


# ── 5. Normalised 62-row PCM database ───────────────────────────────────────
def fetch_pcm_database():
    step(5, "Normalised PCM candidate database ...")
    if not PCM_PROPERTIES_CSV.exists():
        print(f"  [MISSING] {PCM_PROPERTIES_CSV}")
        return
    raw = pd.read_csv(PCM_PROPERTIES_CSV)

    # Manufacturer rows — same mapping as 07_feasibility_filter_rajasthan.py:181-205
    m = pd.DataFrame()
    m["name"] = raw["product"]
    m["family"] = raw["manufacturer"]
    m["pcm_type"] = raw["pcm_type"]
    m["Tm_C"] = raw["Tm_melting"]
    m["Tm_freezing_C"] = raw["Tm_freezing"]
    m["latent_heat_kJ_kg"] = raw["latent_heat_melting"]
    m["density_liquid_kg_m3"] = raw["density_liquid"]
    m["density_solid_kg_m3"] = raw["density_solid"]
    m["Cp_liquid_kJ_kgK"] = raw["Cp_liquid"]
    m["Cp_solid_kJ_kgK"] = raw["Cp_solid"]
    # Tamil Nadu prefers the real per-phase average over the imputed-constant
    # TC_both (06_build_pcm_database.py:82-83).
    m["TC_W_mK"] = (raw["TC_liquid"] + raw["TC_solid"]) / 2.0
    m["cycles_tested"] = raw["cycles_tested"]
    m["cycles_tested_status"] = raw.get("cycles_tested_status", "manufacturer_reported")
    m["flammable"] = raw["flammability"]
    m["supercooling_K"] = m["Tm_C"] - m["Tm_freezing_C"]
    imputed_cols = [c + "_imputed" for c in IMPUTABLE_PROPS if c + "_imputed" in raw.columns]
    m["n_properties_imputed"] = raw[imputed_cols].sum(axis=1) if imputed_cols else 0
    m["any_property_imputed"] = m["n_properties_imputed"] > 0
    m["source"] = "manufacturer_datasheet_MICE_RF_PMM_completed"

    if INCLUDE_LITERATURE_ROWS:
        lit = pd.DataFrame(LITERATURE_PCMS)
        for c in ["density_liquid_kg_m3", "density_solid_kg_m3", "Cp_liquid_kJ_kgK",
                  "Cp_solid_kJ_kgK", "TC_W_mK", "cycles_tested", "supercooling_K"]:
            if c not in lit.columns:
                lit[c] = np.nan
        lit["cycles_tested_status"] = "not_reported"
        lit["flammable"] = "Likely (organic)"
        # not imputed - genuinely unmeasured, left NaN (Tamil Nadu 06:129-130)
        lit["any_property_imputed"] = False
        lit["n_properties_imputed"] = 0
        lit["source"] = "Singh2025_Table2_literature"
        db = pd.concat([m, lit], ignore_index=True, sort=False)
    else:
        db = m.copy()

    # Derived columns - all four reproduce Tamil Nadu's add_derived() exactly.
    density_for_rho = db["density_solid_kg_m3"].fillna(db["density_liquid_kg_m3"])
    db["rho_H_MJ_m3"] = (density_for_rho * db["latent_heat_kJ_kg"]) / 1000.0
    db["Cp_avg_kJ_kgK"] = (db["Cp_liquid_kJ_kgK"].fillna(db["Cp_solid_kJ_kgK"]) +
                           db["Cp_solid_kJ_kgK"].fillna(db["Cp_liquid_kJ_kgK"])) / 2.0
    max_cycles = db["cycles_tested"].max()
    db["cycles_confidence"] = np.where(
        db["cycles_tested"].notna(),
        np.log1p(db["cycles_tested"]) / np.log1p(max_cycles)
        if max_cycles and max_cycles > 0 else np.nan,
        np.nan)
    db["in_absolute_band"] = db["Tm_C"].between(ABSOLUTE_TM_MIN, ABSOLUTE_TM_MAX)
    db["corrosion_class"] = np.where(
        db["pcm_type"].astype(str).str.contains("Inorganic", na=False),
        "check_manually", "low_organic")

    db = db.sort_values("Tm_C").reset_index(drop=True)[TN_PCM_COLS]

    n_manu = int((db["source"] != "Singh2025_Table2_literature").sum())
    n_lit = int((db["source"] == "Singh2025_Table2_literature").sum())
    # State-independent table — written into every state folder, each under the
    # name that state uses. Any existing file is kept as *.bak_62row first.
    for state_dir, fname in PCM_DB_STATES.items():
        target_dir = FROZEN_DIR.parent / state_dir
        if not target_dir.is_dir():
            print(f"  [SKIP] {state_dir}/ not present")
            continue
        dest = target_dir / fname
        if dest.exists():
            backup = dest.with_suffix(".csv.bak_62row")
            if not backup.exists():
                shutil.copy2(dest, backup)
                print(f"  backed up existing {fname} -> {backup.name}")
        db.to_csv(dest, index=False)
        print(f"  [OK] {state_dir}/{fname}  ({len(db)} rows, {len(db.columns)} cols)")

    print(f"       composition: {n_manu} manufacturer + {n_lit} literature "
          f"(INCLUDE_LITERATURE_ROWS={INCLUDE_LITERATURE_ROWS})")
    print(f"       in_absolute_band [{ABSOLUTE_TM_MIN}, {ABSOLUTE_TM_MAX}] degC: "
          f"{int(db['in_absolute_band'].sum())} of {len(db)} pass")
    return db


# ── 6. PCA loadings ─────────────────────────────────────────────────────────
def fetch_pca_loadings():
    step(6, "PCA loadings on the correlated temperature/elevation block ...")
    sig_path = OBJ1_PROCESSED_DIR / f"climate_signature_{STATE}.csv"
    if not sig_path.exists():
        print(f"  [MISSING] {sig_path}")
        return
    sig = pd.read_csv(sig_path)
    missing = [c for c in PCA_BLOCK if c not in sig.columns]
    if missing:
        print(f"  [ABORT] signature is missing {missing}")
        return

    # Re-fit exactly as 04_climate_signature_rajasthan.py:503-514 does.
    pca_input = sig[PCA_BLOCK].fillna(sig[PCA_BLOCK].median())
    scaled = StandardScaler().fit_transform(pca_input)
    pca = PCA(n_components=0.95, random_state=42)
    scores = pca.fit_transform(scaled)
    n_comp = scores.shape[1]
    pcs = [f"PC{i + 1}" for i in range(n_comp)]

    # Verify the re-fit reproduces the PC columns already stored in the
    # signature (sign is arbitrary in PCA, so compare |correlation|).
    checks = []
    for i, pc in enumerate(pcs):
        if pc in sig.columns:
            r = float(np.corrcoef(scores[:, i], sig[pc].values)[0, 1])
            checks.append(f"{pc} |r|={abs(r):.6f}")
    print(f"  {n_comp} components (95% variance). Re-fit vs stored: "
          f"{'  '.join(checks) if checks else 'stored PCs not present'}")

    loadings = pd.DataFrame(pca.components_.T, index=PCA_BLOCK, columns=pcs)
    dest = FROZEN_DIR / "pca_loadings.csv"
    loadings.to_csv(dest)
    print(f"  [OK] pca_loadings.csv  ({len(loadings)} features x {n_comp} PCs)")
    print(f"       explained variance: {np.round(pca.explained_variance_ratio_, 3)}")
    print(loadings.round(3).to_string())


def main():
    print("=" * 74)
    print(f"  Fetch Tamil-Nadu-shaped gaps from Objective 1 — {STATE.title()}")
    print(f"  Source : {OBJ1_PROCESSED_DIR}")
    print(f"  Dest   : {FROZEN_DIR}")
    print("=" * 74)
    ensure_dirs()
    fetch_full_tables()
    fetch_kmeans_comparison()
    fetch_tier2()
    fetch_pcm_database()
    fetch_pca_loadings()
    print("\n" + "=" * 74)
    print("  DONE — re-run build_input_package.py to refresh manifest.json")
    print("=" * 74)


if __name__ == "__main__":
    main()
