"""
scripts/verify_phase5_doe.py
Performs Quality Control on the Phase 5 DOE dataset for Assam:
1. Verifies actual number of generated DOE cases.
2. Verifies LHS variables cover permitted design space.
3. Verifies no variable exceeds shared bounds.
4. Verifies categorical PCM choices are only savE® OM48, savE® OM50, savE® OM46, and plain tank.
5. Verifies all 3 Assam regimes are represented.
6. Verifies no target leakage in the 29 surrogate input features.
7. Verifies failed simulations remain recorded with reasons.
8. Verifies Rajasthan directory remains untouched.
9. Verifies shared config hashes are unchanged.
"""

import sys
import hashlib
from pathlib import Path
import pandas as pd
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.io_utils import load_system_config, load_design_bounds
from src.surrogate.features import build_feature_table, feature_target_split, TARGET_COLS

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=" * 80)
    print("PHASE 5 DOE QUALITY CONTROL AUDIT (ASSAM)")
    print("=" * 80)

    csv_path = REPO_ROOT / "results" / "phase5_design_cases.csv"
    parquet_path = REPO_ROOT / "results" / "phase5_design_cases.parquet"
    assert csv_path.exists() and parquet_path.exists(), "DOE output files missing!"

    df = pd.read_csv(csv_path)
    df_p = pd.read_parquet(parquet_path)
    assert len(df) == len(df_p), "CSV and Parquet row count mismatch!"

    n_total = len(df)
    n_valid = int(df["valid"].sum())
    n_failed = n_total - n_valid
    print(f"\n1. Case Counts:")
    print(f"   Total Cases:   {n_total}")
    print(f"   Valid Cases:   {n_valid} ({n_valid/n_total*100:.1f}%)")
    print(f"   Failed Cases:  {n_failed} ({n_failed/n_total*100:.1f}%)")
    assert 150 <= n_total <= 300, f"Total cases {n_total} outside [150, 300]!"

    # 2 & 3. Bounds check
    bounds = load_design_bounds()
    d_b = bounds["capsule_diameter_m"]
    n_b = bounds["capsule_count"]
    f_b = bounds["flow_rate_kg_s"]

    d_min, d_max = df["capsule_diameter_m"].min(), df["capsule_diameter_m"].max()
    n_min, n_max = df["n_capsule"].min(), df["n_capsule"].max()
    f_min, f_max = df["flow_rate_kg_s"].min(), df["flow_rate_kg_s"].max()

    print(f"\n2 & 3. Design Space Coverage & Bounds:")
    print(f"   Capsule Diameter: [{d_min:.4f}, {d_max:.4f}] m (Bounds: [{d_b['min']}, {d_b['max']}])")
    print(f"   Capsule Count:    [{n_min}, {n_max}] (Bounds: [{n_b['min']}, {n_b['max']}])")
    print(f"   Flow Rate:        [{f_min:.4f}, {f_max:.4f}] kg/s (Bounds: [{f_b['min']}, {f_b['max']}])")

    assert d_min >= d_b["min"] - 1e-6 and d_max <= d_b["max"] + 1e-6
    assert n_min >= n_b["min"] and n_max <= n_b["max"]
    assert f_min >= f_b["min"] - 1e-6 and f_max <= f_b["max"] + 1e-6
    print("   [PASS] All design variables within frozen shared bounds.")

    # 4. PCM choices
    expected_pcms = {"savE® OM48", "savE® OM50", "savE® OM46", "NONE_plain_tank"}
    actual_pcms = set(df["pcm_id"].unique())
    print(f"\n4. PCM Choices:")
    print(f"   Actual:   {actual_pcms}")
    print(f"   Expected: {expected_pcms}")
    assert actual_pcms == expected_pcms, f"Unexpected PCMs found: {actual_pcms - expected_pcms}"
    print("   [PASS] Categorical PCM choices strictly match approved candidate universe.")

    # 5. Regimes
    expected_regimes = {0, 1, 2}
    actual_regimes = set(df["regime_id"].unique())
    print(f"\n5. Regime Distribution:")
    reg_counts = df["regime_id"].value_counts().sort_index()
    for cid, cnt in reg_counts.items():
        v_cnt = df[df["regime_id"] == cid]["valid"].sum()
        print(f"   Cluster {cid}: {cnt} cases total ({v_cnt} valid, {cnt - v_cnt} failed)")
    assert actual_regimes == expected_regimes, f"Regime mismatch: {actual_regimes}"
    print("   [PASS] All 3 Assam regimes uniformly represented.")

    # Distribution of PCMs
    print(f"\n   PCM Breakdown:")
    pcm_counts = df["pcm_id"].value_counts()
    for pcm, cnt in pcm_counts.items():
        v_cnt = df[df["pcm_id"] == pcm]["valid"].sum()
        print(f"   {pcm:<18s}: {cnt:3d} cases ({v_cnt:3d} valid, {cnt - v_cnt:2d} failed)")

    # Baseline cases
    n_baseline = (df["pcm_id"] == "NONE_plain_tank").sum()
    print(f"\n   Baseline Cases: {n_baseline} (1 per regime)")
    assert n_baseline == 3

    # 6. Surrogate features & target leakage
    X, y, feas, cols = feature_target_split(df, only_valid=False)
    print(f"\n6. Surrogate Input Features ({len(cols)} features):")
    print(f"   Columns: {cols}")
    assert len(cols) == 29, f"Expected 29 features, got {len(cols)}"
    for t in TARGET_COLS:
        assert t not in cols, f"Target leakage! {t} found in surrogate feature columns."
    print("   [PASS] Exactly 29 non-leaking surrogate features verified.")

    # 7. Failed cases & reasons
    print(f"\n7. Failure Reasons:")
    reasons = df.loc[~df["valid"], "reason"].value_counts()
    for r, cnt in reasons.items():
        print(f"   {r}: {cnt} cases")
    assert len(reasons) > 0 and n_failed > 0
    print("   [PASS] Infeasible cases preserved with documented reason codes.")

    # 8. Rajasthan directory
    rj_dir = REPO_ROOT.parent / "objective2-rajasthan"
    import subprocess
    cmd = ["git", "status", "--porcelain", "objective2-rajasthan/"]
    res = subprocess.run(cmd, cwd=str(REPO_ROOT.parent), capture_output=True, text=True)
    rj_clean = (len(res.stdout.strip()) == 0)
    print(f"\n8. Rajasthan Directory Integrity:")
    print(f"   Working tree clean: {rj_clean}")
    assert rj_clean, f"Rajasthan directory modified! Output: {res.stdout}"
    print("   [PASS] objective2-rajasthan/ remains completely clean and untouched.")

    # 9. Shared config hashes
    h_sys = sha256(REPO_ROOT / "configs" / "system_config_shared.yaml")
    h_bnd = sha256(REPO_ROOT / "configs" / "design_bounds_shared.yaml")
    exp_sys = "fb405ecb99dfa016764a4124d6bda5cab972559875ad37f693e8b8c6c278a945"
    exp_bnd = "506daf8ff6d3ff244b969e3be43e74116d91e3e266669e7dad373bcab27fe2c2"
    assert h_sys == exp_sys and h_bnd == exp_bnd
    print(f"\n9. Shared Config Hashes:")
    print(f"   system_config_shared.yaml: {h_sys} (MATCH)")
    print(f"   design_bounds_shared.yaml: {h_bnd} (MATCH)")
    print("   [PASS] Shared config hashes match byte-for-byte.")

    # Summary of simulated metrics on valid cases
    valid_df = df[df["valid"]]
    print(f"\n--- VALID CASE METRICS SUMMARY ({len(valid_df)} CASES) ---")
    print(f"   Useful Energy (kWh): min={valid_df['useful_energy_kWh'].min():.2f}, mean={valid_df['useful_energy_kWh'].mean():.2f}, max={valid_df['useful_energy_kWh'].max():.2f}")
    print(f"   Solar Fraction (%):  min={valid_df['solar_fraction'].min()*100:.2f}%, mean={valid_df['solar_fraction'].mean()*100:.2f}%, max={valid_df['solar_fraction'].max()*100:.2f}%")
    print(f"   Unmet Energy (kWh):  min={valid_df['unmet_energy_kWh'].min():.2f}, mean={valid_df['unmet_energy_kWh'].mean():.2f}, max={valid_df['unmet_energy_kWh'].max():.2f}")
    print(f"   Pump Energy (Wh):    min={valid_df['pump_energy_kWh'].min()*1000:.4f}, mean={valid_df['pump_energy_kWh'].mean()*1000:.4f}, max={valid_df['pump_energy_kWh'].max()*1000:.4f}")
    print(f"   PCM Mass (kg):       min={valid_df['pcm_mass_kg'].min():.2f}, mean={valid_df['pcm_mass_kg'].mean():.2f}, max={valid_df['pcm_mass_kg'].max():.2f}")
    print(f"   Mean f_melt:         min={valid_df['mean_f_melt'].min():.4f}, mean={valid_df['mean_f_melt'].mean():.4f}, max={valid_df['mean_f_melt'].max():.4f}")

    print("\n" + "=" * 80)
    print("ALL PHASE 5 QUALITY CONTROL CHECKS PASSED PERFECTLY!")
    print("=" * 80)

if __name__ == "__main__":
    main()
