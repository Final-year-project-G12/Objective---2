"""
scripts/test_single_case_assam.py
Minimal single-case Assam simulator test:
- Cluster: 0
- Weather: ASP_0012 (weather_regime_assam_cluster0_hourly.csv)
- PCM: savE® OM48
- d: 0.05 m
- N: 14
- flow: 0.030 kg/s
Traces and reports every input entering the simulator.
"""

import sys
import json
import time
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.design.schema import DesignVector
from src.simulation.run_case import run_case
from src.io_utils import (
    load_system_config, load_design_bounds, get_regime,
    get_pcm_properties, load_hourly_weather, load_demand_profile
)

def run_single_case():
    print("=" * 72)
    print("PHASE 3: SINGLE-CASE ASSAM SIMULATOR TRACE & TEST")
    print("=" * 72)

    state = "assam"
    cluster_id = 0
    pcm_name = "savE® OM48"
    design = DesignVector(capsule_diameter_m=0.05, n_capsule=14, flow_rate_kg_s=0.030)

    # 1. TRACE INPUTS
    print("\n--- 1. INPUT TRACE ---")
    regime = get_regime(state, cluster_id)
    print(f"State: {state}")
    print(f"Cluster ID: {cluster_id} ({regime['label']})")
    print(f"Medoid Weather File: {regime['weather_hourly']}")
    print(f"Mains Temperature (T_mains_est_C from assam.yaml): {regime['T_mains_est_C']} °C")
    print(f"PCM Name: {pcm_name}")
    
    pcm_record = get_pcm_properties(state, pcm_name)
    print(f"PCM Properties:")
    print(f"  - Melting Point (Tm_C): {pcm_record['Tm_C']} °C")
    print(f"  - Latent Heat (latent_heat_kJ_kg): {pcm_record['latent_heat_kJ_kg']} kJ/kg")
    print(f"  - Thermal Conductivity (TC_W_mK): {pcm_record['TC_W_mK']} W/m-K")
    print(f"  - Liquid Density: {pcm_record['density_liquid_kg_m3']} kg/m3")
    print(f"  - Solid Density: {pcm_record['density_solid_kg_m3']} kg/m3")
    print(f"  - Liquid Specific Heat: {pcm_record['Cp_liquid_kJ_kgK']} kJ/kg-K")
    print(f"  - Solid Specific Heat: {pcm_record['Cp_solid_kJ_kgK']} kJ/kg-K")
    
    sc = load_system_config()
    print(f"System & Solver Config:")
    print(f"  - Collector Area: {sc['collector']['area_m2']} m2")
    print(f"  - Tank Volume: {sc['tank']['volume_L']} L")
    print(f"  - Delivery Target Temp: {sc['delivery']['target_temp_C']} °C")
    print(f"  - Solver Timestep: {sc['solver']['timestep_s']} s")
    print(f"  - Substeps per Hour: {3600 // sc['solver']['timestep_s']}")
    
    demand_df = load_demand_profile(state)
    print(f"Demand Profile: {len(demand_df)} hours, daily total = {demand_df['draw_mass_kg'].sum():.2f} kg/day")
    print(f"  - Draw at 07:00 IST: {demand_df.loc[demand_df['hour']==7, 'draw_mass_kg'].iloc[0]} kg")
    print(f"  - Draw at 19:00 IST: {demand_df.loc[demand_df['hour']==19, 'draw_mass_kg'].iloc[0]} kg")

    # 2. RUN SIMULATION
    print("\n--- 2. RUNNING SIMULATION ---")
    t0 = time.time()
    out = run_case(state, cluster_id, pcm_name, design, record_hourly=True)
    elapsed = time.time() - t0
    print(f"Simulation completed in {elapsed:.2f} s")

    # 3. VERIFY METRICS & ENERGY BALANCE
    print("\n--- 3. SIMULATION RESULTS & ENERGY BALANCE ---")
    print(f"Validity: {out['valid']} (Reason: {out['reason']})")
    assert out["valid"], "Case unexpectedly failed!"

    metrics = out["metrics"]
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.4f}")
        else:
            print(f"  {k}: {v}")

    hourly = out["hourly"]
    print(f"\nHourly Timeseries Data: {len(hourly)} rows (8760 hours)")
    print(f"  Water Temp (T_w_C): min={hourly['T_w_C'].min():.2f} °C, mean={hourly['T_w_C'].mean():.2f} °C, max={hourly['T_w_C'].max():.2f} °C")
    print(f"  PCM Temp (T_pcm_C): min={hourly['T_pcm_C'].min():.2f} °C, mean={hourly['T_pcm_C'].mean():.2f} °C, max={hourly['T_pcm_C'].max():.2f} °C")
    print(f"  PCM Melt Fraction (f_melt): min={hourly['f_melt'].min():.4f}, mean={hourly['f_melt'].mean():.4f}, max={hourly['f_melt'].max():.4f}")
    
    residual_pct = metrics["residual_pct_of_collector"]
    print(f"\nEnergy Balance Residual: {residual_pct:.6f}% of collector input (Gate 1 limit: < 0.1%)")
    assert abs(residual_pct) < 0.1, f"Energy residual {residual_pct}% exceeds 0.1% limit!"

    print("\n[OK] Single-case simulator test passed completely!")
    return out

if __name__ == "__main__":
    run_single_case()
