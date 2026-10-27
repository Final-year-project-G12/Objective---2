"""
scripts/g4_multinode_report.py
=================================
G4 (O2, 2026-10-26) — evidence for the multi-node tank.

 1. Timed simulated year, single-node vs multi-node (N = 10, 20), per regime, plain and PCM
    (legacy Phase-7 deployable designs -- illustrative, not O1 designs). JIT warm-up call excluded.
 2. The project-CFD stratified-draw case (openfoam_cfd/docs/COMPONENT_CFD_NOTES.md: 50 L tank, 30 L at 55 C over
    20 L at 25 C, 0.03 kg/s of 25 C mains): litres delivered at >= 45 C versus node count, and the mixed 43 C tank.

Writes results/g4_multinode_report.csv and results/g4_cfd_draw_case.csv.
"""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.design.schema import DesignVector
from src.simulation import run_case as rc

OUT = Path("results")


def timed_years():
    designs = pd.read_csv("data/legacy/phase7_deployable_design_per_regime.csv")
    rc.run_case("rajasthan", 0, None, DesignVector(0.05, 16, 0.03, "staggered"), tank_model="multinode",
                record_hourly=False)                                    # JIT warm-up
    rows = []
    for _, r in designs.iterrows():
        dv = DesignVector(capsule_diameter_m=r.capsule_diameter_m, n_capsule=int(r.n_capsule),
                          flow_rate_kg_s=r.flow_rate_kg_s, capsule_arrangement=r.arrangement)
        for tag, pcm in (("plain", None), ("pcm", r.pcm_id)):
            for model, n in (("single", 1), ("multinode", 10), ("multinode", 20)):
                t0 = time.time()
                m = rc.run_case("rajasthan", int(r.regime_id), pcm, dv, tank_model=model, n_nodes=n,
                                record_hourly=False)["metrics"]
                rows.append({"regime": int(r.regime_id), "case": tag, "pcm": pcm or "", "model": model,
                             "n_nodes": n if model == "multinode" else 1, "runtime_s": time.time() - t0,
                             "useful_energy_kWh": m["useful_energy_kWh"], "solar_fraction": m["solar_fraction"],
                             "collector_kWh": m["collector_energy_kWh"], "loss_kWh": m["loss_energy_kWh"],
                             "unmet_kWh": m["unmet_energy_kWh"], "max_water_C": m["max_water_temp_C"],
                             "max_pcm_C": m["max_pcm_temp_C"], "residual_pct": m["residual_pct_of_collector"],
                             "shield_water_substeps": m["n_shield_water_activations"]})
                print(rows[-1], flush=True)
    return pd.DataFrame(rows)


def cfd_case():
    w = pd.DataFrame({"timestamp_utc": pd.date_range("2025-01-01", periods=2, freq="h", tz="UTC"), "GHI_Wm2": 0.0,
                      "T_amb_C": 25.0, "local_hour": [0, 1], "local_date": "2025-01-01"})
    orig = rc.load_hourly_weather, rc.load_demand_profile
    rc.load_hourly_weather = lambda s, c, **kw: w
    rc.load_demand_profile = lambda s: pd.DataFrame({"hour": range(24), "draw_mass_kg": [0.03 * 3600] + [0.0] * 23})
    dv = DesignVector(0.05, 16, 0.03, "staggered")
    rows = []
    try:
        for n in (1, 5, 10, 15, 20, 40):
            for label, T in (("stratified 30 L @55 / 20 L @25", None), ("mixed 43 C", np.full(n, 43.0))):
                if T is None:
                    T = np.full(n, 25.0)
                    T[int(round(n * 0.4)):] = 55.0
                o = rc.run_case("rajasthan", 0, None, dv, tank_model="multinode", n_nodes=n,
                                mains_temp_override_C=25.0, initial_state={"T_nodes": T, "h_nodes": np.zeros(n),
                                                                           "T_w_C": float(T.mean())},
                                system_config_overrides={"solver": {"timestep_s": 30}}, record_hourly=True)
                rows.append({"n_nodes": n, "initial_state": label,
                             "litres_at_or_above_45C": float(o["hourly"]["vol_ge_target_kg"].iloc[0])})
    finally:
        rc.load_hourly_weather, rc.load_demand_profile = orig
    return pd.DataFrame(rows)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    cfd_case().to_csv(OUT / "g4_cfd_draw_case.csv", index=False)
    timed_years().to_csv(OUT / "g4_multinode_report.csv", index=False)
