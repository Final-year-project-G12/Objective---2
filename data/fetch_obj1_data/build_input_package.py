"""
build_input_package.py  —  Rajasthan
========================================
Stage A / Deliverable D2.1 — "Frozen input package"

Rajasthan counterpart of the Tamil Nadu teammate's build_input_package.py. Same three
categories of file, same manifest contract, same re-run-and-diff workflow. What differs
is only the upstream filenames, because the Rajasthan Objective 1 pipeline names its
outputs differently (and in two places produces something better — see NOTES).

  1. SMALL STRUCTURAL TABLES — copied in full, byte-for-byte (shutil.copy2, no
     re-encoding). Regimes, PCM database, feasibility survivors, MCDM rankings,
     Monte Carlo stability, physics validation, recommendation cards.
  2. LARGE PER-EVENT / PER-HOUR FILES — hashed but NOT copied. Rajasthan's are big
     (climate_rajasthan_points_clean.csv is 1.5 GB, suntimes.csv 197 MB,
     daily_aggregates_rajasthan.csv 143 MB); duplicating them buys nothing. Path +
     hash go in the manifest; medoid-only SUBSETS of suntimes and daily_aggregates
     are cut here so downstream code still has what it actually needs.
  3. MEDOID RAW WEATHER — each cluster's medoid point gets its full raw hourly NASA
     POWER cache (all 10 years, 2016–2025) copied.

NOTES — where Rajasthan differs from the Tamil Nadu precedent
-------------------------------------------------------------
* MEDOID DEFINITION. Tamil Nadu picks argmax(max_membership_prob). That does not work
  here: Rajasthan's GMM is confident enough that max_membership_prob is 1.0 (to ~12
  decimals) for many points, so argmax would silently return whichever tied row came
  first. This script instead calls physics_lib.find_medoid() from the Rajasthan
  pipeline itself — nearest point to the cluster mean in the standardized (*_z)
  clustering space, the same method 05_cluster_rajasthan.py and
  09_physics_validation_rajasthan.py both already use. Importing it rather than
  re-implementing it means the frozen medoids cannot drift from O1's own.
* NO tier2_signature / pca_loadings / kmeans_comparison FILES. Rajasthan's Phase 3
  folds the tier-2 rollup and PCA straight into climate_signature_rajasthan.csv
  (PC1..PC4 plus the *_z columns), and the KMeans-vs-GMM baseline comparison lives
  inside bic_selection_rajasthan.csv. Nothing is missing; it is packaged differently.
* MCDM. Rajasthan writes ONE ranking table (mcdm_rankings_rajasthan.csv, every
  survivor x cluster with all four methods' ranks + Borda/Copeland consensus + the
  Monte Carlo columns) where Tamil Nadu writes three (topk / full_scores /
  monte_carlo_stability). This script copies the one table and additionally cuts the
  two derived views so downstream code written against the TN schema still finds
  mcdm_topk_by_cluster-shaped and monte_carlo_stability-shaped files.
* FEASIBILITY. 08_mcdm_ranking_rajasthan.py ranks the KAPPA-CALIBRATED survivors, not
  the fixed-kappa=0.7 baseline. The calibrated file is the one frozen here; the
  baseline is deliberately left behind so O2 cannot accidentally pair one with the other.

HOW TO RUN:
  python build_input_package.py

Safe to re-run — idempotent. Re-run after any Objective 1 change and diff manifest.json.
"""

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone

import pandas as pd

from config import (
    STATE, OBJ1_ROOT, OBJ1_PROCESSED_DIR, OBJ1_PREPROCESSED_DIR, OBJ1_RAW_POWER_DIR,
    OBJ1_OUTPUTS_DIR, PCM_PROPERTIES_CSV, FROZEN_DIR, FROZEN_WEATHER_DIR,
    MANIFEST_FILE, ensure_dirs,
)

# Import Objective 1's own helper library so medoid selection cannot drift.
sys.path.insert(0, str(OBJ1_ROOT))
try:
    import physics_lib as pl
except ImportError as exc:                                    # pragma: no cover
    print(f"  [FATAL] cannot import physics_lib from {OBJ1_ROOT}: {exc}")
    raise

# ═══════════════════════════════════════════════════════════════════
# FILE LISTS  — (source path relative to OBJ1_PROCESSED_DIR, destination name)
# ═══════════════════════════════════════════════════════════════════

# Destination names follow the Tamil Nadu frozen package exactly: where Tamil
# Nadu suffixes a file with its state name we do the same, and where it does
# not (feasibility_survivors_by_cluster, mcdm_topk_by_cluster,
# monte_carlo_stability, physics_validation_results, physics_validation_spearman,
# population_grid_points, pcm_properties, recommendation_cards) neither do we.
SMALL_FILES = [
    # sampling design
    ("population_grid_points.csv", "population_grid_points.csv"),
    # cross-source validation (evidence, not a modelling input)
    (f"era5_power_agreement_{STATE}.csv", f"era5_power_agreement_{STATE}.csv"),
    (f"daily_aggregates_{STATE}_summary.csv", f"daily_aggregates_summary_{STATE}.csv"),
    (f"quality_report_{STATE}.json", f"quality_report_{STATE}.json"),
    # Phase 3 — climate signature (includes PC1..PC4 + *_z; see NOTES)
    (f"climate_signature_{STATE}.csv", f"climate_signature_{STATE}.csv"),
    # Phase 4 — clustering / climate regimes
    (f"cluster_assignments_{STATE}_levelA.csv", f"cluster_assignments_levelA_{STATE}.csv"),
    (f"cluster_assignments_{STATE}_levelB.csv", f"cluster_assignments_levelB_{STATE}.csv"),
    (f"cluster_profiles_{STATE}.csv", f"cluster_profiles_{STATE}.csv"),
    (f"bic_selection_{STATE}.csv", f"bic_selection_{STATE}.csv"),
    (f"bic_selection_{STATE}_levelB.csv", f"bic_selection_levelB_{STATE}.csv"),
    (f"koppen_validation_{STATE}.csv", f"koppen_validation_{STATE}.csv"),
    (f"level_b_feature_importance_{STATE}.csv", f"level_b_feature_importance_{STATE}.csv"),
    # Phase 5-6 — feasibility + MCDM (calibrated branch only, see NOTES)
    ("feasibility_survivors_by_cluster_kappa_calibrated.csv",
     "feasibility_survivors_by_cluster.csv"),
    ("mcdm_full_rankings.csv", f"mcdm_rankings_{STATE}.csv"),
    ("mcdm_topk_by_cluster.csv", "mcdm_topk_by_cluster.csv"),
    ("monte_carlo_stability.csv", "monte_carlo_stability.csv"),
    ("mcdm_method_agreement.csv", f"mcdm_method_agreement_{STATE}.csv"),
    # Phase 7-8 — physics validation + sensitivity
    (f"physics_validation_{STATE}.csv", "physics_validation_results.csv"),
    (f"spearman_rho_by_cluster_{STATE}.csv", "physics_validation_spearman.csv"),
    (f"calibration_check_{STATE}.csv", f"calibration_check_{STATE}.csv"),
    (f"pcm_mass_sensitivity_{STATE}.csv", f"pcm_mass_sensitivity_{STATE}.csv"),
    (f"phase8_supercooling_sweep_{STATE}.csv", f"phase8_supercooling_sweep_{STATE}.csv"),
]

# Files that live outside data/processed/ — (absolute source, destination name)
EXTERNAL_FILES = [
    # Tamil Nadu calls this exact 55-row manufacturer table pcm_properties.csv
    # (byte-identical file, md5 cf351cc413). Its pcm_database_<state>.csv is a
    # different, 62-row NORMALISED table that Rajasthan does not write to disk.
    (PCM_PROPERTIES_CSV, "pcm_properties.csv"),
    (OBJ1_OUTPUTS_DIR / f"recommendation_cards_{STATE}.md", "recommendation_cards.md"),
    (OBJ1_OUTPUTS_DIR / f"cluster_profile_cards_{STATE}.md", f"cluster_profile_cards_{STATE}.md"),
    (OBJ1_ROOT / f"physics_validation_summary_{STATE}.txt", f"physics_validation_summary_{STATE}.txt"),
]

# Hashed, not copied. Medoid subsets of the first two are cut below.
LARGE_REFERENCE_FILES = [
    OBJ1_PROCESSED_DIR / "suntimes.csv",
    OBJ1_PROCESSED_DIR / f"daily_aggregates_{STATE}.csv",
    OBJ1_PROCESSED_DIR / f"climate_{STATE}_points.csv",
    OBJ1_PROCESSED_DIR / f"climate_{STATE}_points_clean.csv",
    OBJ1_PREPROCESSED_DIR / f"{STATE}_cleaned_physical.csv",
    OBJ1_PREPROCESSED_DIR / f"{STATE}_cleaned_scaled.csv",
]

SUBSET_CHUNKSIZE = 500_000


# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def sha256_of(path, chunk_size=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def _entry(src, dest, status):
    e = {"source": str(src), "dest": str(dest) if dest else None, "status": status}
    if dest is not None and status in ("copied", "derived", "subset"):
        e["sha256"] = sha256_of(dest)
        e["size_bytes"] = dest.stat().st_size
    return e


def copy_one(src, dest_name, entries, label=""):
    dest = FROZEN_DIR / dest_name
    if not src.exists():
        print(f"  [SKIP-MISSING] {src.name}  (Objective 1 has not produced this yet)")
        entries.append(_entry(src, None, "missing"))
        return False
    shutil.copy2(src, dest)
    print(f"  [OK] {src.name:52s} -> {dest_name}  ({dest.stat().st_size / 1024:.1f} KB)")
    entries.append(_entry(src, dest, "copied"))
    return True


def copy_small_files():
    entries = []
    for rel_src, dest_name in SMALL_FILES:
        copy_one(OBJ1_PROCESSED_DIR / rel_src, dest_name, entries)
    for src, dest_name in EXTERNAL_FILES:
        copy_one(src, dest_name, entries)
    return entries


def reference_large_files():
    entries = []
    for src in LARGE_REFERENCE_FILES:
        if not src.exists():
            print(f"  [SKIP-MISSING] {src.name}")
            entries.append(_entry(src, None, "missing"))
            continue
        digest = sha256_of(src)
        print(f"  [HASHED, NOT COPIED] {src.name:42s} "
              f"({src.stat().st_size / 1e6:7.1f} MB)  sha256={digest[:12]}...")
        entries.append({"source": str(src), "dest": None, "sha256": digest,
                        "size_bytes": src.stat().st_size, "status": "referenced_only"})
    return entries


def find_medoids():
    """One (cluster_id, point_id) per Level-A cluster, via Objective 1's own
    physics_lib.find_medoid — nearest point to the cluster mean in the standardized
    (*_z) clustering space. See NOTES in the module docstring for why this is not
    argmax(max_membership_prob) as in the Tamil Nadu script."""
    assign_path = OBJ1_PROCESSED_DIR / f"cluster_assignments_{STATE}_levelA.csv"
    sig_path = OBJ1_PROCESSED_DIR / f"climate_signature_{STATE}.csv"
    if not assign_path.exists() or not sig_path.exists():
        print("  [WARN] cluster assignments or climate signature missing — run "
              f"05_cluster_{STATE}.py first. Skipping medoid selection.")
        return []

    assign = pd.read_csv(assign_path)
    sig = pd.read_csv(sig_path)
    sig.rename(columns={sig.columns[0]: "point_id"}, inplace=True)
    z_cols = [c for c in sig.columns if c.endswith("_z")]

    out = []
    for cid in sorted(assign["cluster_id"].unique()):
        pid = pl.find_medoid(cid, assign, sig, z_cols)
        n = int((assign["cluster_id"] == cid).sum())
        row = assign.loc[assign["point_id"] == pid].iloc[0]
        out.append({"cluster_id": int(cid), "point_id": str(pid),
                    "lat": float(row["lat"]), "lon": float(row["lon"]),
                    "population": float(row["population"]),
                    "max_membership_prob": float(row["max_membership_prob"]),
                    "cluster_n_points": n})
    return out


def write_medoid_table(medoids):
    df = pd.DataFrame(medoids)
    dest = FROZEN_DIR / f"medoid_points_{STATE}.csv"
    df.to_csv(dest, index=False)
    print(f"  [OK] medoid_points_{STATE}.csv  ({len(df)} regimes)")
    return _entry("derived from cluster_assignments + climate_signature via "
                  "physics_lib.find_medoid", dest, "derived")


def subset_large_by_point(src, dest_name, point_ids, entries, label):
    """Stream a multi-hundred-MB per-point file, keeping only the medoid rows."""
    if not src.exists():
        print(f"  [SKIP-MISSING] {src.name}")
        entries.append(_entry(src, None, "missing"))
        return
    dest = FROZEN_DIR / dest_name
    dest.unlink(missing_ok=True)
    kept, seen, header = 0, 0, False
    print(f"  streaming {src.name} ({src.stat().st_size / 1e6:.0f} MB) for {label} ...")
    for chunk in pd.read_csv(src, chunksize=SUBSET_CHUNKSIZE, low_memory=False):
        seen += len(chunk)
        hit = chunk[chunk["point_id"].isin(point_ids)]
        if hit.empty:
            continue
        hit.to_csv(dest, mode="a", index=False, header=not header)
        header = True
        kept += len(hit)
    print(f"  [OK] {dest_name}  ({kept:,} of {seen:,} rows kept, "
          f"{dest.stat().st_size / 1e6:.1f} MB)")
    e = _entry(src, dest, "subset")
    e["rows_kept"] = kept
    e["rows_scanned"] = seen
    entries.append(e)


def copy_medoid_raw_weather(medoids):
    entries = []
    for m in medoids:
        cid, point_id = m["cluster_id"], m["point_id"]
        matches = sorted(OBJ1_RAW_POWER_DIR.glob(f"power_{point_id}_*.json"))
        if not matches:
            print(f"  [WARN] no raw NASA POWER cache for medoid {point_id} "
                  f"(cluster {cid}) under {OBJ1_RAW_POWER_DIR}")
            continue
        for src in matches:
            dest = FROZEN_WEATHER_DIR / src.name
            shutil.copy2(src, dest)
            entries.append({"source": str(src), "dest": str(dest), "cluster_id": cid,
                            "point_id": point_id, "sha256": sha256_of(dest),
                            "size_bytes": dest.stat().st_size, "status": "copied"})
        years = sorted(int(p.stem.split("_")[-1]) for p in matches)
        print(f"  [OK] cluster {cid}: medoid {point_id} — {len(matches)} yearly JSON "
              f"files copied ({years[0]}–{years[-1]})")
    return entries


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 72)
    print(f"  Objective 2 — Build Frozen Input Package (D2.1) — {STATE.title()}")
    print(f"  Reading from : {OBJ1_ROOT}")
    print(f"  Writing to   : {FROZEN_DIR}")
    print("=" * 72)

    if not OBJ1_ROOT.exists():
        print(f"\n  ERROR: {OBJ1_ROOT} not found. Edit OBJ1_FOLDER_NAME in config.py.")
        sys.exit(1)

    ensure_dirs()

    print("\n[1/5] Copying small structural tables ...")
    small_entries = copy_small_files()

    print("\n[2/5] Hashing (not copying) large per-event/per-hour Objective 1 files ...")
    large_entries = reference_large_files()

    print("\n[3/5] Identifying per-cluster medoid points (physics_lib.find_medoid) ...")
    medoids = find_medoids()
    for m in medoids:
        print(f"  cluster {m['cluster_id']} -> {m['point_id']}  "
              f"({m['lat']:.3f}, {m['lon']:.3f})  n={m['cluster_n_points']}")
    if medoids:
        small_entries.append(write_medoid_table(medoids))

    print("\n[4/5] Cutting medoid-only subsets of the large per-point files ...")
    if medoids:
        pids = {m["point_id"] for m in medoids}
        subset_large_by_point(OBJ1_PROCESSED_DIR / "suntimes.csv",
                              f"suntimes_medoids_{STATE}.csv", pids,
                              small_entries, "sun-event timestamps")
        subset_large_by_point(OBJ1_PROCESSED_DIR / f"daily_aggregates_{STATE}.csv",
                              f"daily_aggregates_medoids_{STATE}.csv", pids,
                              small_entries, "daily weather aggregates")
    else:
        print("  (skipped — no medoids)")

    print("\n[5/5] Copying medoid points' full raw hourly NASA POWER cache ...")
    weather_entries = copy_medoid_raw_weather(medoids) if medoids else []

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "state": STATE,
        "objective1_root": str(OBJ1_ROOT),
        "medoid_selection_method": "physics_lib.find_medoid — nearest point to cluster "
                                   "mean in standardized (*_z) clustering space",
        "small_structural_files": small_entries,
        "large_referenced_files": large_entries,
        "medoid_points": medoids,
        "medoid_raw_weather_files": weather_entries,
    }
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    n_missing = sum(1 for e in small_entries + large_entries if e.get("status") == "missing")
    n_copied = sum(1 for e in small_entries + weather_entries
                   if e.get("status") in ("copied", "derived", "subset"))

    print("\n" + "=" * 72)
    print("  DONE")
    print(f"  Files written : {n_copied}")
    print(f"  Files missing : {n_missing}")
    print(f"  Manifest      : {MANIFEST_FILE}")
    print("=" * 72)
    if n_missing:
        print("\nMissing (check whether the matching Objective 1 phase was run):")
        for e in small_entries + large_entries:
            if e.get("status") == "missing":
                print(f"    {e['source']}")
    print("\nNext: python build_regime_weather.py   then   python build_demand_profile.py")


if __name__ == "__main__":
    main()
