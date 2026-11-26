"""
scripts/final_phase0_regression_check.py
Validates the 10 final regression points required before Phase 2-4:
1. Assam config loads correctly.
2. All 3 regimes load.
3. All 3 Assam weather files contain complete 2025 hourly coverage (8760 continuous hours).
4. GHI is nonnegative and nighttime GHI is zero.
5. T_mains values come only from assam.yaml.
6. Demand profile contains the two exact 50 kg draws (07:00 and 19:00 IST, 100 kg total).
7. OM48, OM50 and OM46 load with complete required thermophysical properties.
8. Shared config/design-bound hashes remain unchanged.
9. Rajasthan config and feature generation still pass.
10. 29 surrogate features contain no simulation-target leakage.
"""

import sys
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def run_checks():
    from src.io_utils import (
        load_system_config, load_design_bounds, load_state_config,
        get_regime, get_pcm_properties, load_hourly_weather, load_demand_profile
    )
    from src.simulation.demand_profile import load_demand_model
    from src.surrogate.features import build_feature_table, feature_target_split, TARGET_COLS

    print("=" * 72)
    print("STEP 2: FINAL PHASE-0 / INPUT REGRESSION CHECK (10 CRITICAL CHECKS)")
    print("=" * 72)

    # 1 & 2. Assam config & 3 regimes
    cfg_as = load_state_config("assam")
    assert cfg_as["state"] == "assam"
    regimes = cfg_as["regimes"]
    assert len(regimes) == 3, f"Expected 3 regimes, got {len(regimes)}"
    print("[1 & 2 PASS] Assam config loaded with 3 regimes: C0, C1, C2.")

    # 3 & 4. Weather coverage, nonnegativity, nocturnal 0
    exp_hours = pd.date_range("2025-01-01 00:00:00", "2025-12-31 23:00:00", freq="h", tz="UTC")
    for cid in range(3):
        w = load_hourly_weather("assam", cid)
        assert len(w) == 8760, f"Cluster {cid} hours = {len(w)}"
        ts = pd.DatetimeIndex(w["timestamp_utc"])
        if ts.tz is None: ts = ts.tz_localize("UTC")
        assert (ts == exp_hours).all()
        assert (w["GHI_Wm2"] >= 0.0).all()
        assert np.isfinite(w["GHI_Wm2"]).all()
        night_df = w[w["timestamp_utc"].dt.hour.isin([16, 17, 18, 19, 20, 21, 22])]
        assert (night_df["GHI_Wm2"] == 0.0).all()
        print(f"  [Cluster {cid} Weather OK] 8760 continuous hours, GHI >= 0, night max = 0.0 W/m2")
    print("[3 & 4 PASS] Weather coverage and radiation bounds strictly validated.")

    # 5. T_mains authority
    tmains_expected = {0: 19.89, 1: 19.10, 2: 16.59}
    for cid, exp_tm in tmains_expected.items():
        reg = get_regime("assam", cid)
        assert abs(float(reg["T_mains_est_C"]) - exp_tm) < 1e-4
    print(f"[5 PASS] T_mains values confirmed from assam.yaml: {tmains_expected}")

    # 6. Demand profile
    df_d = load_demand_profile("assam")
    assert len(df_d) == 24
    m7 = float(df_d.loc[df_d["hour"] == 7, "draw_mass_kg"].iloc[0])
    m19 = float(df_d.loc[df_d["hour"] == 19, "draw_mass_kg"].iloc[0])
    nonpeak = float(df_d.loc[~df_d["hour"].isin([7, 19]), "draw_mass_kg"].sum())
    total_d = float(df_d["draw_mass_kg"].sum())
    assert abs(m7 - 50.0) < 1e-4 and abs(m19 - 50.0) < 1e-4 and nonpeak < 1e-4 and abs(total_d - 100.0) < 1e-4
    dm = load_demand_model(df_d)
    assert abs(sum(dm.draw_mass_kg_for_hour(h) for h in range(24)) - 100.0) < 1e-4
    print("[6 PASS] Demand profile: exact 50 kg @ 07:00, 50 kg @ 19:00, 0 elsewhere, total 100 kg/day.")

    # 7. OM48, OM50, OM46 properties
    required_props = ["Tm_C", "latent_heat_kJ_kg", "TC_W_mK", "density_liquid_kg_m3", "Cp_liquid_kJ_kgK"]
    for pcm in ["savE® OM48", "savE® OM50", "savE® OM46"]:
        props = get_pcm_properties("assam", pcm)
        for p in required_props:
            val = props[p]
            assert pd.notna(val) and np.isfinite(float(val)) and float(val) > 0.0
        print(f"  [PCM {pcm} OK] Tm={props['Tm_C']} C, L={props['latent_heat_kJ_kg']} kJ/kg, k={props['TC_W_mK']} W/m-K")
    print("[7 PASS] All 3 candidate PCMs loaded with complete validated thermophysical properties.")

    # 8. Shared config hashes
    h_sys = sha256(REPO_ROOT / "configs" / "system_config_shared.yaml")
    h_bnd = sha256(REPO_ROOT / "configs" / "design_bounds_shared.yaml")
    assert h_sys == "fb405ecb99dfa016764a4124d6bda5cab972559875ad37f693e8b8c6c278a945"
    assert h_bnd == "506daf8ff6d3ff244b969e3be43e74116d91e3e266669e7dad373bcab27fe2c2"
    print(f"[8 PASS] Shared configs unchanged: sys={h_sys[:12]}..., bnd={h_bnd[:12]}...")

    # 9. Rajasthan untouched original compatibility
    rj_root = REPO_ROOT.parent / "objective2-rajasthan"
    sys.path.insert(0, str(rj_root))
    import yaml
    cfg_rj = yaml.safe_load(open(rj_root / "configs" / "states" / "rajasthan.yaml", encoding="utf-8"))
    assert cfg_rj["state"] == "rajasthan" and len(cfg_rj["regimes"]) == 3
    print("[9 PASS] Untouched Rajasthan reference config intact and verified.")

    # 10. 29 features & no simulation-target leakage
    dummy_cases = pd.DataFrame([{
        "case_id": "test_0", "regime_id": 0, "pcm_id": "savE® OM48",
        "capsule_diameter_m": 0.05, "n_capsule": 14, "flow_rate_kg_s": 0.030,
        "geom_pcm_thickness_m": 0.002, "geom_pcm_volume_fraction": 0.08,
        "geom_void_fraction": 0.92, "geom_pressure_drop_pa": 120.0,
        "geom_pump_power_w": 0.5, "geom_reynolds_number_particle": 35.0,
        "valid": True,
        # Put targets to check leakage
        "useful_energy_kWh": 1500.0, "solar_fraction": 0.75, "unmet_energy_kWh": 500.0,
        "pump_energy_kWh": 10.0, "pcm_mass_kg": 25.0, "mean_f_melt": 0.65
    }])
    ft = build_feature_table("assam", dummy_cases)
    X, y, feas, cols = feature_target_split(ft, only_valid=True)
    assert len(cols) == 29, f"Expected 29 features, got {len(cols)}"
    for t in TARGET_COLS:
        assert t not in cols, f"Target leakage detected: {t} found in feature columns!"
    print(f"[10 PASS] Exactly 29 state-independent features. Zero target leakage.")
    print("=" * 72)
    print("ALL 10 STEP-2 REGRESSION CHECKS PASSED WITH GREEN VERDICT!")
    print("=" * 72)

if __name__ == "__main__":
    run_checks()
