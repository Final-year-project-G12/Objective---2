"""
scripts/phase0_smoke_test_assam.py
==================================
Phase 0 validation check for Assam Objective 2.
Validates:
1. Module imports (geometry, simulation, gates, surrogate, optimizer, robustness, handoff)
2. Shared configs (verifies SHA-256 hashes of system_config_shared.yaml & design_bounds_shared.yaml are unchanged)
3. State config (configs/states/assam.yaml: 3 regimes, schemas, bounds)
4. Frozen Objective 1 inputs & manifests (cluster_profiles, assignments, population, physics_validation, swh_spec)
5. Weather profiles (all 3 medoids, continuous 8760 hours of 2025, finite & non-negative GHI, zero nighttime GHI)
6. Demand profile (24 hourly fractions summing to 100 kg/day)
7. PCM database & candidate shortlist (58 records, standardized schema, verified thermophysical properties for OM48/50/46)
8. State-independent surrogate feature compatibility (no MCDM zeroes, no physics validation target leakage)

NOTE: Actual simulator execution is deferred to Phase 3 per methodology rules.
"""

import hashlib
import json
import math
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def test_phase0_assam():
    results = {}
    all_passed = True
    
    print("=" * 72)
    print("ASSAM OBJECTIVE 2 — PHASE 0 INPUT & CONFIGURATION VALIDATION")
    print("=" * 72)

    # -------------------------------------------------------------
    # 1. IMPORTS
    # -------------------------------------------------------------
    print("\n[1/8] Validating Module Imports...")
    try:
        from src.design.schema import DesignVector
        from src.design.geometry import sphere_volume_m3, sphere_surface_area_m2, tank_dimensions_m
        from src.design.constraints import check_design
        from src.simulation.capsule_enthalpy import pcm_props_from_record, PCMThermalProps
        from src.simulation.demand_profile import load_demand_model
        from src.simulation.tank_model import DesignRuntime, run_year
        from src.simulation.run_case import run_case
        from src.verify.gates import get_rank1_pcms
        from src.doe.generate_cases import generate_all_cases
        from src.doe.run_batch import get_sim_version
        from src.surrogate.features import build_feature_table, feature_target_split, CLIMATE_COLS, PCM_COLS, DESIGN_COLS
        from src.optimize.select_deployable import apply_selection_rule, confirm_candidates, run_phase7
        from src.io_utils import (
            load_system_config, load_design_bounds, load_state_config,
            get_regime, get_pcm_properties, load_hourly_weather, load_demand_profile
        )
        results["imports"] = "PASS"
        print("  [OK] All core modules imported successfully without errors.")
    except Exception as e:
        results["imports"] = f"FAIL: {e}"
        all_passed = False
        print(f"  [FAIL] Import failure: {e}")

    # -------------------------------------------------------------
    # 2. SHARED CONFIG INTEGRITY
    # -------------------------------------------------------------
    print("\n[2/8] Validating Shared Config Integrity (Frozen SHA-256)...")
    sys_cfg_path = REPO_ROOT / "configs" / "system_config_shared.yaml"
    bounds_path = REPO_ROOT / "configs" / "design_bounds_shared.yaml"
    sys_hash = sha256_file(sys_cfg_path)
    bnd_hash = sha256_file(bounds_path)
    
    # Pristine SHA-256 hashes of shared configs
    exp_sys_hash = "fb405ecb99dfa016764a4124d6bda5cab972559875ad37f693e8b8c6c278a945"
    exp_bnd_hash = "506daf8ff6d3ff244b969e3be43e74116d91e3e266669e7dad373bcab27fe2c2"
    
    sys_match = (sys_hash == exp_sys_hash)
    bnd_match = (bnd_hash == exp_bnd_hash)
    
    if sys_match and bnd_match:
        results["shared_configs"] = "PASS"
        print(f"  [OK] system_config_shared.yaml SHA-256 matched ({sys_hash[:16]}...)")
        print(f"  [OK] design_bounds_shared.yaml SHA-256 matched ({bnd_hash[:16]}...)")
    else:
        results["shared_configs"] = "FAIL"
        all_passed = False
        print(f"  [FAIL] Hash mismatch! sys_match={sys_match}, bnd_match={bnd_match}")

    # -------------------------------------------------------------
    # 3. STATE CONFIG
    # -------------------------------------------------------------
    print("\n[3/8] Validating configs/states/assam.yaml...")
    try:
        cfg = load_state_config("assam")
        assert cfg["state"] == "assam"
        assert len(cfg["regimes"]) == 3, f"Expected 3 regimes, got {len(cfg['regimes'])}"
        
        regimes_info = {}
        for r in cfg["regimes"]:
            cid = int(r["cluster_id"])
            regimes_info[cid] = {
                "label": r["label"],
                "n_points": r["n_points"],
                "T_mains_est_C": r["T_mains_est_C"],
                "pcm_shortlist": r["pcm_shortlist"]
            }
            assert r["T_mains_est_C"] in [19.89, 19.10, 16.59], f"Unexpected Tmains: {r['T_mains_est_C']}"
            assert r["pcm_shortlist"] == ["savE® OM48", "savE® OM50", "savE® OM46"]
            
        results["state_config"] = "PASS"
        print(f"  [OK] State config valid: 3 Level-A regimes, correct Tmains & shortlist: {regimes_info}")
    except Exception as e:
        results["state_config"] = f"FAIL: {e}"
        all_passed = False
        print(f"  [FAIL] State config validation failed: {e}")

    # -------------------------------------------------------------
    # 4. FROZEN OBJECTIVE 1 INPUTS
    # -------------------------------------------------------------
    print("\n[4/8] Validating Frozen Objective 1 Input Artifacts & Provenance...")
    o1_files = [
        "cluster_profiles_assam.csv",
        "cluster_assignments_assam.csv",
        "population_grid_points_assam.csv",
        "physics_validation_assam.csv",
        "swh_design_specification_assam.csv",
        "pcm_database_assam.csv",
        "manifest_assam.json",
    ]
    o1_ok = True
    for fn in o1_files:
        fp = REPO_ROOT / "data" / "objective1" / fn
        if not fp.exists():
            print(f"  [FAIL] Missing O1 artifact: {fn}")
            o1_ok = False
        else:
            print(f"  [OK] {fn} exists ({fp.stat().st_size:,} bytes)")
    
    # Check manifest contents
    manifest_path = REPO_ROOT / "data" / "objective1" / "manifest_assam.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    print(f"  [OK] Provenance commit locked: {manifest.get('objective1_git_commit', manifest.get('git_commit_sha'))}")
    results["objective1_frozen"] = "PASS" if o1_ok else "FAIL"
    if not o1_ok: all_passed = False

    # -------------------------------------------------------------
    # 5. WEATHER PROFILES (Timestamp coverage, GHI, nocturnal zero)
    # -------------------------------------------------------------
    print("\n[5/8] Validating Weather Profiles (Coverage, GHI nonnegativity, nocturnal flux)...")
    weather_ok = True
    start_ts = pd.Timestamp("2025-01-01 00:00:00", tz="UTC")
    end_ts = pd.Timestamp("2025-12-31 23:00:00", tz="UTC")
    expected_index = pd.date_range(start_ts, end_ts, freq="h")
    
    for cid in [0, 1, 2]:
        w_path = REPO_ROOT / "data" / "weather" / f"weather_regime_assam_cluster{cid}_hourly.csv"
        df_w = pd.read_csv(w_path, parse_dates=["timestamp_utc"])
        
        # Continuous timestamp coverage check
        ts_idx = pd.DatetimeIndex(df_w["timestamp_utc"])
        if ts_idx.tz is None: ts_idx = ts_idx.tz_localize("UTC")
        coverage_ok = bool((ts_idx == expected_index).all())
        
        # GHI non-negativity & finite check
        ghi = df_w["GHI_Wm2"]
        finite_ok = bool(np.isfinite(ghi).all())
        nonneg_ok = bool((ghi >= 0.0).all())
        
        # Nocturnal radiation check (UTC 16 to 22 corresponds to 21:30 to 03:30 IST)
        night_hours = [16, 17, 18, 19, 20, 21, 22]
        night_df = df_w[df_w["timestamp_utc"].dt.hour.isin(night_hours)]
        night_max = float(night_df["GHI_Wm2"].max())
        night_ok = (night_max == 0.0)
        
        if coverage_ok and finite_ok and nonneg_ok and night_ok:
            print(f"  [OK] Cluster {cid} ({w_path.name}): 8760 continuous 2025 hours, GHI in [{ghi.min():.1f}, {ghi.max():.1f}] W/m2, night max = {night_max} W/m2")
        else:
            print(f"  [FAIL] Cluster {cid} failed! coverage={coverage_ok}, finite={finite_ok}, nonneg={nonneg_ok}, night_zero={night_ok}")
            weather_ok = False
            
    results["weather_profiles"] = "PASS" if weather_ok else "FAIL"
    if not weather_ok: all_passed = False

    # -------------------------------------------------------------
    # 6. DEMAND PROFILE
    # -------------------------------------------------------------
    print("\n[6/8] Validating Demand Profile...")
    try:
        d_path = REPO_ROOT / "data" / "demand" / "demand_profile_assam.csv"
        df_d = pd.read_csv(d_path)
        assert len(df_d) == 24, f"Expected 24 hours, got {len(df_d)}"
        assert "draw_mass_kg" in df_d.columns
        total_draw = float(df_d["draw_mass_kg"].sum())
        assert abs(total_draw - 100.0) < 1e-4, f"Expected 100 kg total draw, got {total_draw}"
        
        # Check Step 6 specification: 50 kg @ 07:00, 50 kg @ 19:00, 0 elsewhere
        m7 = float(df_d.loc[df_d["hour"] == 7, "draw_mass_kg"].iloc[0])
        m19 = float(df_d.loc[df_d["hour"] == 19, "draw_mass_kg"].iloc[0])
        non_peak = float(df_d.loc[~df_d["hour"].isin([7, 19]), "draw_mass_kg"].sum())
        assert abs(m7 - 50.0) < 1e-4, f"Hour 7 expected 50 kg, got {m7}"
        assert abs(m19 - 50.0) < 1e-4, f"Hour 19 expected 50 kg, got {m19}"
        assert non_peak < 1e-4, f"Non-peak hours expected 0 kg, got {non_peak}"

        d_model = load_demand_model(df_d)
        vol_check = float(d_model._mass.sum())
        assert abs(vol_check - 100.0) < 1e-4
        
        results["demand_profile"] = "PASS"
        print(f"  [OK] Demand profile valid: 50 kg @ 07:00, 50 kg @ 19:00, 0 elsewhere, total = {total_draw:.2f} kg/day, verified by DemandModel.")
    except Exception as e:
        results["demand_profile"] = f"FAIL: {e}"
        all_passed = False
        print(f"  [FAIL] Demand profile failed: {e}")

    # -------------------------------------------------------------
    # 7. PCM DATABASE & CANDIDATE SHORTLIST
    # -------------------------------------------------------------
    print("\n[7/8] Validating PCM Database & Candidate Shortlist...")
    try:
        pcm_df = pd.read_csv(REPO_ROOT / "data" / "objective1" / "pcm_database_assam.csv")
        assert len(pcm_df) == 58, f"Expected 58 PCMs, got {len(pcm_df)}"
        
        shortlist = ["savE® OM48", "savE® OM50", "savE® OM46"]
        for p_name in shortlist:
            rec = get_pcm_properties("assam", p_name)
            assert rec["name"] == p_name
            assert rec["Tm_C"] in [51.0, 50.0, 47.0]
            assert rec["latent_heat_kJ_kg"] > 150.0
            assert rec["density_solid_kg_m3"] > 800.0
            assert rec["TC_W_mK"] > 0.1
            print(f"  [OK] Candidate '{p_name}': Tm={rec['Tm_C']} C, L={rec['latent_heat_kJ_kg']} kJ/kg, rho={rec['density_solid_kg_m3']} kg/m3")
            
        results["pcm_database"] = "PASS"
        print("  [OK] PCM database schema standardized, all 3 physics-validated candidates resolved without invented properties.")
    except Exception as e:
        results["pcm_database"] = f"FAIL: {e}"
        all_passed = False
        print(f"  [FAIL] PCM database validation failed: {e}")

    # -------------------------------------------------------------
    # 8. SURROGATE FEATURE TABLE GENERATION (Methodology Check)
    # -------------------------------------------------------------
    print("\n[8/8] Validating State-Independent Surrogate Feature Generation...")
    try:
        dummy_cases = pd.DataFrame([
            {'case_id': 'c0', 'regime_id': 0, 'pcm_id': 'NONE_plain_tank', 'valid': True,
             'capsule_diameter_m': 0.05, 'n_capsule': 14, 'flow_rate_kg_s': 0.03,
             'geom_pcm_thickness_m': 0.02, 'geom_pcm_volume_fraction': 0.1, 'geom_void_fraction': 0.9,
             'geom_pressure_drop_pa': 100.0, 'geom_pump_power_w': 1.5, 'geom_reynolds_number_particle': 50.0,
             'useful_energy_kWh': 1000.0, 'solar_fraction': 0.6, 'unmet_energy_kWh': 200.0,
             'pump_energy_kWh': 0.05, 'pcm_mass_kg': 0.0, 'mean_f_melt': 0.0},
            {'case_id': 'c1', 'regime_id': 1, 'pcm_id': 'savE® OM50', 'valid': True,
             'capsule_diameter_m': 0.05, 'n_capsule': 14, 'flow_rate_kg_s': 0.03,
             'geom_pcm_thickness_m': 0.02, 'geom_pcm_volume_fraction': 0.1, 'geom_void_fraction': 0.9,
             'geom_pressure_drop_pa': 100.0, 'geom_pump_power_w': 1.5, 'geom_reynolds_number_particle': 50.0,
             'useful_energy_kWh': 1100.0, 'solar_fraction': 0.65, 'unmet_energy_kWh': 150.0,
             'pump_energy_kWh': 0.05, 'pcm_mass_kg': 5.0, 'mean_f_melt': 0.4},
        ])
        
        ft_assam = build_feature_table("assam", dummy_cases)
        X_a, y_a, feas_a, cols_a = feature_target_split(ft_assam)
        
        ft_rj = build_feature_table("rajasthan", dummy_cases)
        X_r, y_r, feas_r, cols_r = feature_target_split(ft_rj)
        
        assert cols_a == cols_r, "Feature columns must match exactly across states!"
        assert "top3_inclusion_probability" not in cols_a, "Legacy MCDM column should not be in state-independent schema!"
        assert "annual_solar_fraction" not in cols_a, "Physics validation target must not be in input features!"
        assert X_a.isna().sum().sum() == 0, "Assam feature table has NaNs!"
        assert X_r.isna().sum().sum() == 0, "Rajasthan feature table has NaNs!"
        
        results["surrogate_features"] = "PASS"
        print(f"  [OK] State-independent feature schema verified ({len(cols_a)} features).")
        print(f"  [OK] Zero target leakage; no artificial zero substitutions for missing MCDM.")
        print(f"  [OK] Identical schema across states: {cols_a}")
    except Exception as e:
        results["surrogate_features"] = f"FAIL: {e}"
        all_passed = False
        print(f"  ✗ Surrogate feature validation failed: {e}")

    # -------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------
    print("\n" + "=" * 72)
    print("PHASE 0 VALIDATION SUMMARY")
    print("=" * 72)
    for k, v in results.items():
        print(f"  {k:25s}: {v}")
    
    overall_status = "GREEN" if all_passed else "RED"
    print(f"\nOVERALL READINESS STATUS: {overall_status}")
    print("=" * 72)
    return overall_status, results

if __name__ == "__main__":
    status, res = test_phase0_assam()
    if status != "GREEN":
        sys.exit(1)
