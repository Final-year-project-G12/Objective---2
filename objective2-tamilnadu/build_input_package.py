"""
build_input_package.py
==========================
Stage A / Deliverable D2.1 — "Frozen input package"

Copies the Objective 1 outputs Objective 2 actually needs from the sibling
era5_tamilnadu/ pipeline into this project's data/objective1/ folder, and
writes a manifest.json recording a SHA-256 hash of every source file.

WHY A MANIFEST: the Objective 2 workflow doc's own QC checklist requires
"Objective 1 input hash: Regime, weather and PCM files match frozen
manifest. If it fails: Stop and rebuild the case manifest." If Objective 1
is ever re-run later (bigger PCM database, different K, elevation repair,
etc.) this file is what lets you detect that instead of silently mixing
two different Objective 1 runs into one Objective 2 experiment.

THREE CATEGORIES OF FILE:

1. SMALL STRUCTURAL TABLES — copied in full. Regimes, PCM database,
   feasibility survivors, MCDM rankings, Monte Carlo stability, physics
   validation, recommendation cards, daily-resolution weather aggregates.
   These are what geometry.py / schema.py / the surrogate will actually
   read.

2. LARGE PER-EVENT / PER-HOUR FILES — hashed but NOT copied (would just
   duplicate hundreds of MB for no benefit at this stage). Their path and
   hash are recorded in the manifest; read them directly from Objective 1
   (read-only) if you ever need row-level access.

3. MEDOID RAW WEATHER — for each cluster, the single point with the
   highest GMM membership probability (cluster_assignments_tamilnadu.csv)
   has its FULL raw hourly NASA POWER cache (all years) copied. This is
   the real, unreconstructed hourly series the Obj2 doc's §2.1 asks for
   ("the NASA POWER cache contains the full hourly record needed for...
   transient simulation") for the one representative point per regime you
   need for the first-pass simulator. Non-medoid points stay read-only in
   Objective 1 — copy them the same way later if a robustness run needs
   more member points.

HOW TO RUN:
  cd objective2_design_optimization
  python build_input_package.py

Safe to re-run — everything here is small/cheap, so just re-run after any
Objective 1 change and diff manifest.json.
"""

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone

import pandas as pd

from config import (
    OBJ1_ROOT, OBJ1_PROCESSED_DIR, OBJ1_PREPROCESSED_DIR, OBJ1_RAW_POWER_DIR,
    OBJ1_FROZEN_DIR, OBJ1_FROZEN_WEATHER_DIR, MANIFEST_FILE, ensure_dirs,
)

# ═══════════════════════════════════════════════════════════
# FILE LISTS  — edit these if your Objective 1 filenames differ
# ═══════════════════════════════════════════════════════════

# (path relative to OBJ1_PROCESSED_DIR, destination filename in data/objective1/)
SMALL_FILES = [
    # sampling design / sun-event timing
    ("population_grid_points.csv", "population_grid_points.csv"),
    ("suntimes.csv", "suntimes.csv"),
    # daily-resolution weather — this is what DOE/simulator should drive
    # off, not the giant per-sun-event CSV (see LARGE_REFERENCE_FILES)
    ("daily_aggregates_tamilnadu.csv", "daily_aggregates_tamilnadu.csv"),
    ("tier2_signature_tamilnadu.csv", "tier2_signature_tamilnadu.csv"),
    ("era5_power_agreement_tamilnadu.csv", "era5_power_agreement_tamilnadu.csv"),
    # Phase 3 — climate signature
    ("signatures/climate_signature_tamilnadu.csv", "climate_signature_tamilnadu.csv"),
    ("signatures/pca_loadings.csv", "pca_loadings.csv"),
    # Phase 4 — clustering / climate regimes
    ("clustering/cluster_assignments_tamilnadu.csv", "cluster_assignments_tamilnadu.csv"),
    ("clustering/cluster_profiles_tamilnadu.csv", "cluster_profiles_tamilnadu.csv"),
    ("clustering/bic_selection_tamilnadu.csv", "bic_selection_tamilnadu.csv"),
    ("clustering/kmeans_comparison_tamilnadu.csv", "kmeans_comparison_tamilnadu.csv"),
    # Phase 5-6 — PCM database, feasibility, MCDM ranking
    ("pcm/pcm_database_tamilnadu.csv", "pcm_database_tamilnadu.csv"),
    ("pcm/feasibility_survivors_by_cluster.csv", "feasibility_survivors_by_cluster.csv"),
    ("pcm/mcdm_topk_by_cluster.csv", "mcdm_topk_by_cluster.csv"),
    ("pcm/mcdm_full_scores_by_cluster.csv", "mcdm_full_scores_by_cluster.csv"),
    ("pcm/monte_carlo_stability.csv", "monte_carlo_stability.csv"),
    # Phase 7 — physics validation (optional: only exists if you ran 10_physics_validation.py)
    ("pcm/physics_validation_results.csv", "physics_validation_results.csv"),
    ("pcm/physics_validation_spearman.csv", "physics_validation_spearman.csv"),
    # Phase 4 Level B — seasonal sensitivity (optional)
    ("pcm/level_b_seasonal_topk.csv", "level_b_seasonal_topk.csv"),
    ("pcm/level_b_seasonal_summary.md", "level_b_seasonal_summary.md"),
    # Phase 8 — recommendation cards (your Obj1 results section)
    ("pcm/recommendation_cards.md", "recommendation_cards.md"),
]

# Large per-sun-event / per-hour files: hash + record path, do NOT copy.
LARGE_REFERENCE_FILES = [
    OBJ1_PROCESSED_DIR / "climate_tamilnadu_points.csv",
    OBJ1_PREPROCESSED_DIR / "tamilnadu_cleaned_physical.csv",
    OBJ1_PREPROCESSED_DIR / "tamilnadu_cleaned_scaled.csv",
]


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def sha256_of(path, chunk_size=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_small_files():
    entries = []
    for rel_src, dest_name in SMALL_FILES:
        src = OBJ1_PROCESSED_DIR / rel_src
        dest = OBJ1_FROZEN_DIR / dest_name
        if not src.exists():
            print(f"  [SKIP-MISSING] {rel_src}  (not produced yet by Objective 1 — "
                  f"fine if you haven't run that phase's script)")
            entries.append({"source": str(src), "dest": None, "status": "missing"})
            continue
        shutil.copy2(src, dest)
        digest = sha256_of(dest)
        size_kb = dest.stat().st_size / 1024
        print(f"  [OK] {rel_src:55s} -> {dest_name}  ({size_kb:.1f} KB)")
        entries.append({"source": str(src), "dest": str(dest), "sha256": digest,
                         "size_bytes": dest.stat().st_size, "status": "copied"})
    return entries


def reference_large_files():
    entries = []
    for src in LARGE_REFERENCE_FILES:
        if not src.exists():
            print(f"  [SKIP-MISSING] {src.name}")
            entries.append({"source": str(src), "status": "missing"})
            continue
        digest = sha256_of(src)
        size_mb = src.stat().st_size / 1e6
        print(f"  [HASHED, NOT COPIED] {src.name}  ({size_mb:.1f} MB)  sha256={digest[:12]}...")
        entries.append({"source": str(src), "dest": None, "sha256": digest,
                         "size_bytes": src.stat().st_size, "status": "referenced_only"})
    return entries


def find_medoid_points():
    """One (cluster_id, point_id) per cluster — the point with the highest
    GMM membership probability. Only these points' full raw hourly NASA
    POWER cache gets copied (see module docstring, category 3)."""
    path = OBJ1_PROCESSED_DIR / "clustering" / "cluster_assignments_tamilnadu.csv"
    if not path.exists():
        print("  [WARN] cluster_assignments_tamilnadu.csv not found — run "
              "05_cluster_tamilnadu.py in the Objective 1 pipeline first. "
              "Skipping medoid raw-weather copy.")
        return []
    assign = pd.read_csv(path)
    if "max_membership_prob" not in assign.columns:
        print("  [WARN] cluster_assignments_tamilnadu.csv has no "
              "max_membership_prob column — skipping medoid raw-weather copy.")
        return []
    idx = assign.groupby("cluster_id")["max_membership_prob"].idxmax()
    medoids = assign.loc[idx, ["cluster_id", "point_id"]].reset_index(drop=True)
    return list(medoids.itertuples(index=False))


def copy_medoid_raw_weather(medoids):
    entries = []
    for row in medoids:
        cid, point_id = row.cluster_id, row.point_id
        matches = sorted(OBJ1_RAW_POWER_DIR.glob(f"power_{point_id}_*.json"))
        if not matches:
            print(f"  [WARN] no raw NASA POWER cache found for medoid {point_id} "
                  f"(cluster {cid}) — expected files under {OBJ1_RAW_POWER_DIR}")
            continue
        for src in matches:
            dest = OBJ1_FROZEN_WEATHER_DIR / src.name
            shutil.copy2(src, dest)
            digest = sha256_of(dest)
            entries.append({"source": str(src), "dest": str(dest), "cluster_id": int(cid),
                             "point_id": point_id, "sha256": digest,
                             "size_bytes": dest.stat().st_size, "status": "copied"})
        print(f"  [OK] cluster {cid}: medoid {point_id} — {len(matches)} yearly JSON files copied")
    return entries


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    print("=" * 68)
    print("  Objective 2 — Build Frozen Input Package (D2.1)")
    print(f"  Reading from : {OBJ1_ROOT}")
    print("=" * 68)

    if not OBJ1_ROOT.exists():
        print(f"\n  ERROR: {OBJ1_ROOT} not found.")
        print("  Edit OBJ1_ROOT in config.py if your Objective 1 folder has a "
              "different name, or if objective2_design_optimization is not a "
              "sibling of it.")
        sys.exit(1)

    ensure_dirs()

    print("\n[1/4] Copying small structural tables (regimes, PCM database, "
          "rankings, daily weather) ...")
    small_entries = copy_small_files()

    print("\n[2/4] Hashing (not copying) large per-event/per-hour Objective 1 files ...")
    large_entries = reference_large_files()

    print("\n[3/4] Identifying per-cluster medoid points ...")
    medoids = find_medoid_points()
    for m in medoids:
        print(f"  cluster {m.cluster_id} -> medoid {m.point_id}")

    print("\n[4/4] Copying medoid points' full raw hourly NASA POWER cache ...")
    weather_entries = copy_medoid_raw_weather(medoids)

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective1_root": str(OBJ1_ROOT),
        "small_structural_files": small_entries,
        "large_referenced_files": large_entries,
        "medoid_points": [{"cluster_id": int(m.cluster_id), "point_id": m.point_id} for m in medoids],
        "medoid_raw_weather_files": weather_entries,
    }
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    n_missing = sum(1 for e in small_entries + large_entries if e.get("status") == "missing")
    n_copied = sum(1 for e in small_entries + weather_entries if e.get("status") == "copied")

    print("\n" + "=" * 68)
    print("  DONE")
    print(f"  Files copied  : {n_copied}")
    print(f"  Files missing : {n_missing}")
    print(f"  Manifest      : {MANIFEST_FILE}")
    print("=" * 68)
    if n_missing:
        print("\nMissing files (not necessarily a problem — some are optional, e.g. "
              "physics_validation_* and level_b_seasonal_* only exist if you've run "
              "10_physics_validation.py / 11_level_b_seasonal_analysis.py):")
        for e in small_entries + large_entries:
            if e.get("status") == "missing":
                print(f"    {e['source']}")
    print("\nNext: open data/objective1/manifest.json, confirm the medoid list and "
          "cluster count look right, then start on schema.py / geometry.py "
          "(Objective 2 workflow doc, Section 3).")


if __name__ == "__main__":
    main()
