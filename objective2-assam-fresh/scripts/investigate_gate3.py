"""
scripts/investigate_gate3.py
Deep investigation of Gate 3:
1. Reproduce Plain Tank, Fixed OM48, Synthetic Matched-Tm PCM.
2. Trace geometry, volume fractions, and masses.
3. Trace PCM energy utilization (latent vs sensible, melt cycles, time in transition).
4. Verify baseline fairness (identical weather, demand, mains, collector, tank volume, U_tank).
5. Verify First-Law energy conservation in detail.
6. Inspect equations and physics coupling.
7. Physical vs bug classification.
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.design.schema import DesignVector
from src.simulation.run_case import run_case
from src.io_utils import (
    load_system_config, load_design_bounds, get_regime,
    get_pcm_properties, load_hourly_weather
)

def main():
    state = "assam"
    cid = 0
    sc = load_system_config()
    db = load_design_bounds()
    regime = get_regime(state, cid)

    # Designs used in Gate 3
    d_plain = DesignVector(0.08, 14, 0.030)
    d_fixed = DesignVector(0.08, 24, 0.030)

    # 1. RUN SIMULATIONS
    r_plain = run_case(state, cid, None, d_plain, record_hourly=True)
    r_om48 = run_case(state, cid, "savE® OM48", d_fixed, record_hourly=True)
    r_synth = run_case(state, cid, "savE® OM48", d_fixed, record_hourly=True,
                       pcm_record_overrides={"Tm_C": 40.0})

    cases = [
        ("A. Plain Tank Baseline", r_plain, d_plain, None),
        ("B. Fixed savE® OM48 (Tm=51C)", r_om48, d_fixed, "savE® OM48"),
        ("C. Synthetic Matched-Tm PCM (Tm=40C)", r_synth, d_fixed, "savE® OM48 (synthetic Tm=40C)")
    ]

    print("=" * 80)
    print("GATE 3 DEEP INVESTIGATION REPORT")
    print("=" * 80)

    for label, r, d_vec, pcm_str in cases:
        m = r["metrics"]
        g = r["geometry"]
        h = r["hourly"]
        print(f"\n--- {label} ---")
        print(f"  Design Vector: diameter={d_vec.capsule_diameter_m} m, n_capsule={d_vec.n_capsule}, flow={d_vec.flow_rate_kg_s} kg/s")
        print(f"  Tank Volume: {g['tank_volume_m3']*1000:.1f} L (D={g['tank_diameter_m']:.4f} m, H={g['tank_height_m']:.4f} m)")
        print(f"  Capsule Volume: {g['capsule_volume_m3']*1e6:.2f} cm3, Surface Area: {g['capsule_surface_area_m2']:.4f} m2")
        print(f"  Total PCM Volume: {g['pcm_volume_total_m3']*1000:.4f} L")
        print(f"  PCM Volume Fraction: {g['pcm_volume_fraction']*100:.2f}% (Void fraction: {g['void_fraction']*100:.2f}%)")
        print(f"  PCM Mass: {m.get('pcm_mass_kg', 0.0):.4f} kg")
        print(f"  Water Mass in Tank: {(g['tank_volume_m3'] - (g['pcm_volume_total_m3'] if pcm_str else 0.0)) * 1000.0:.2f} kg")
        print(f"  Metrics:")
        print(f"    Solar Fraction: {m['solar_fraction']*100:.2f}%")
        print(f"    Useful Energy:  {m['useful_energy_kWh']:.2f} kWh")
        print(f"    Unmet Energy:   {m['unmet_energy_kWh']:.2f} kWh")
        print(f"    Collector Heat: {m['collector_energy_kWh']:.2f} kWh")
        print(f"    Tank Losses:    {m['loss_energy_kWh']:.2f} kWh")
        print(f"    PCM Charge:     {m.get('charge_energy_kWh', 0.0):.4f} kWh")
        print(f"    PCM Discharge:  {m.get('discharge_energy_kWh', 0.0):.4f} kWh")
        print(f"    Energy Residual: {m['residual_pct_of_collector']:.6f}%")
        if pcm_str:
            print(f"    Mean f_melt:    {m.get('mean_f_melt'):.4f} (min={m.get('min_f_melt'):.4f}, max={m.get('max_f_melt'):.4f})")
            print(f"    Complete Melt Cycles: {m.get('complete_melt_cycles')}")
            # Hours in phase transition
            in_trans = ((h["f_melt"] > 0.01) & (h["f_melt"] < 0.99)).sum()
            fully_liq = (h["f_melt"] >= 0.99).sum()
            fully_sol = (h["f_melt"] <= 0.01).sum()
            print(f"    Hours in Latent Transition (0.01 < f < 0.99): {in_trans} hrs ({in_trans/8760*100:.2f}%)")
            print(f"    Hours Fully Liquid (f >= 0.99): {fully_liq} hrs ({fully_liq/8760*100:.2f}%)")
            print(f"    Hours Fully Solid  (f <= 0.01): {fully_sol} hrs ({fully_sol/8760*100:.2f}%)")
            print(f"    PCM Temp Range: min={h['T_pcm_C'].min():.2f} °C, max={h['T_pcm_C'].max():.2f} °C, mean={h['T_pcm_C'].mean():.2f} °C")
            print(f"    Water Temp Range: min={h['T_w_C'].min():.2f} °C, max={h['T_w_C'].max():.2f} °C, mean={h['T_w_C'].mean():.2f} °C")

    # Trace Day 180 (June, sunny summer day)
    hp = r_plain["hourly"]
    ho = r_om48["hourly"]
    weather = load_hourly_weather(state, cid)
    day = 180
    idx_s = day * 24
    sub_p = hp.iloc[idx_s:idx_s+24]
    sub_o = ho.iloc[idx_s:idx_s+24]
    sub_w = weather.iloc[idx_s:idx_s+24]
    print("\n" + "=" * 90)
    print("HOURLY PROFILE TRACE FOR A PEAK SUNNY DAY (DAY 180)")
    print("=" * 90)
    print(f"{'Hour':>4} | {'GHI (W/m2)':>10} | {'Tw Plain':>9} | {'Tw OM48':>9} | {'Tpcm OM48':>9} | {'f_melt':>7} | {'Q_load Plain (kWh)':>18} | {'Q_load OM48 (kWh)':>18}")
    print("-" * 90)
    for hr in range(24):
        rp = sub_p.iloc[hr]
        ro = sub_o.iloc[hr]
        rw = sub_w.iloc[hr]
        print(f"{hr:4d} | {rw['GHI_Wm2']:10.1f} | {rp['T_w_C']:9.2f} | {ro['T_w_C']:9.2f} | {ro['T_pcm_C']:9.2f} | {ro['f_melt']:7.4f} | {rp['Q_load_Wh']/1000:18.4f} | {ro['Q_load_Wh']/1000:18.4f}")

    # Inspect the 2 daily draws throughout the entire year
    # Sum Q_load and Q_unmet for morning draw (hour 7) and evening draw (hour 19)
    # Hour of day in hourly df
    h_idx = np.arange(len(hp)) % 24
    draw_morning = (h_idx == 7)
    draw_evening = (h_idx == 19)
    print("\n" + "=" * 90)
    print("ANNUAL DRAW BREAKDOWN: MORNING DRAW (07:00 IST) VS EVENING DRAW (19:00 IST)")
    print("=" * 90)
    for d_name, mask in [("Morning Draw (07:00 IST, 50 kg)", draw_morning), ("Evening Draw (19:00 IST, 50 kg)", draw_evening)]:
        print(f"\n{d_name}:")
        for label, h_df in [("Plain Tank", hp), ("Fixed OM48", ho), ("Synth 40C", r_synth["hourly"])]:
            q_l = h_df.loc[mask, "Q_load_Wh"].sum() / 1000.0
            q_u = h_df.loc[mask, "Q_unmet_Wh"].sum() / 1000.0
            tw_mean = h_df.loc[mask, "T_w_C"].mean()
            print(f"  {label:<12s}: Useful={q_l:7.2f} kWh, Unmet={q_u:7.2f} kWh, Mean Delivery Tw={tw_mean:5.2f} °C")

if __name__ == "__main__":
    main()
