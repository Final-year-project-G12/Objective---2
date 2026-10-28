"""
scripts/g22_sensitivity_extra.py
===================================
Plan WP8 item 8: the sensitivities that the repeatability band (g9_band.py: time step, node count, latent heat +/-10 %, conductivity +/-20 %) does not cover.
For the frozen chosen design of a regime (results/g10_selection_r<c>.json), explore years 2016-2020 only, each variant is run for the PCM tank AND for the
water-only tank under the SAME perturbation, and the paired g_window / g_annual / d_overheat are compared with the base case.

Variants:
  mains -2 K, +2 K        mains_temp_override_C = regime T_mains_est +/- 2
  demand x0.8, x1.2       volume_multiplier on the 300 L/day profile
  shield off              safety_shield.enabled = False (the PCM and water peaks are recorded; the 65 C / 75 C limits may then be exceeded, which is the point)
  mains 18 C, 30 C        the cold and hot ends of the state's mains range (configs/states/rajasthan.yaml, mains_temperature_C 18-30): a bracket for any
                          monthly mains series, because the tank kernels take one mains value per run (a monthly series would need a kernel change)
  conv 1, conv 4          pcm_integration.liquid_convection_enhancement 1.0 and 4.0 (frozen value 2.0)
  viscosity x0.5 / x2, expansion x0.5 / x2   mapped onto the same factor from the project's own OpenFOAM sensitivity table (openfoam_cfd/docs/CFD_FINDINGS.md section 2):
                          phi (true / lumped internal resistance) is 0.46 for the reference and 0.39 / 0.54 / 0.55 / 0.38 for the four cases, so the factor becomes
                          2.0 * 0.46 / phi = 2.36 / 1.70 / 1.67 / 2.42. This assumes the liquid-side resistance scales as 1/factor; it is a mapping of a CFD result
                          on a 60 mm RT44HC capsule, not a viscosity model
  density -10 %, +10 %    PCM solid and liquid density x0.9 / x1.1
  Cp -10 %, +10 %         PCM solid and liquid specific heat x0.9 / x1.1
The shift of g_window against the base case is printed next to the regime's repeatability band (results/wp6_band.csv).
NOT covered: a monthly mains series (see the bracket above), PCM supercooling and volume change.

Usage: python scripts/g22_sensitivity_extra.py <cluster_id>   ->  results/g22_sensitivity_r<c>.csv
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.design.schema import DesignVector
from src.design.space import geometry_bounds, load_space, wall_m
from src.io_utils import get_pcm_properties, get_regime, load_state_config
from src.optimize.evaluate import _weather
from src.simulation.run_case import run_case
from src.weather import roles

OUT = Path("results")
SP = load_space()


def dv_for(r, n, q, arr):
    return DesignVector(capsule_diameter_m=2.0 * (r + wall_m()), n_capsule=int(n), flow_rate_kg_s=float(q), capsule_arrangement=arr)


def variants(cid, pcm):
    t_m = get_regime("rajasthan", cid)["T_mains_est_C"]
    rec = get_pcm_properties("rajasthan", pcm)
    v = {"base": {}}
    v["mains-2K"] = {"mains_temp_override_C": t_m - 2.0}
    v["mains+2K"] = {"mains_temp_override_C": t_m + 2.0}
    rng = load_state_config("rajasthan")["mains_temperature_C"]
    v["mains 18C (cold end)"] = {"mains_temp_override_C": float(rng["range_low"])}
    v["mains 30C (hot end)"] = {"mains_temp_override_C": float(rng["range_high"])}
    v["demand x0.8"] = {"volume_multiplier": 0.8}
    v["demand x1.2"] = {"volume_multiplier": 1.2}
    v["shield off"] = {"system_config_overrides": {"safety_shield": {"enabled": False}}}
    v["conv 1"] = {"system_config_overrides": {"pcm_integration": {"liquid_convection_enhancement": 1.0}}}
    v["conv 4"] = {"system_config_overrides": {"pcm_integration": {"liquid_convection_enhancement": 4.0}}}
    phi_ref = 0.46
    for name, phi in (("viscosity x0.5", 0.39), ("viscosity x2", 0.54), ("expansion x0.5", 0.55), ("expansion x2", 0.38)):
        v[name + " (CFD-mapped)"] = {"system_config_overrides": {"pcm_integration": {"liquid_convection_enhancement": 2.0 * phi_ref / phi}}}
    for tag, k in (("-10%", 0.9), ("+10%", 1.1)):
        v[f"density {tag}"] = {"pcm_record_overrides": {"density_solid_kg_m3": rec["density_solid_kg_m3"] * k, "density_liquid_kg_m3": rec["density_liquid_kg_m3"] * k}}
        v[f"Cp {tag}"] = {"pcm_record_overrides": {"Cp_solid_kJ_kgK": rec["Cp_solid_kJ_kgK"] * k, "Cp_liquid_kJ_kgK": rec["Cp_liquid_kJ_kgK"] * k}}
    return v


def one(cid, pcm_name, dv, y, extra):
    return run_case("rajasthan", cid, pcm_name, dv, design_bounds=geometry_bounds(), weather=_weather(cid, y, "explore"), tank_model=SP["model"]["tank_model"],
                    n_nodes=SP["model"]["n_nodes"], stack_anchor=SP["model"]["stack_anchor"], compute_tes_metrics=True, night_day_stride=0, **extra)


def main(cid):
    ch = json.load(open(OUT / f"g10_selection_r{cid}.json", encoding="utf-8"))["chosen"]
    pcm, r, q, arr, n = ch["pcm"], float(ch["R_in_m"]), float(ch["flow"]), ch["arrangement"], int(ch["N"])
    dv = dv_for(r, n, q, arr)
    band = pd.read_csv(OUT / "wp6_band.csv")
    band = float(band[(band.scope == f"r{cid}") & (band.objective == "g_window")].band.iloc[0])
    rows, base = [], None
    for name, extra in variants(cid, pcm).items():
        per = []
        for y in roles.years_for("explore"):
            res = one(cid, pcm, dv, y, extra)
            pl_extra = {k: v for k, v in extra.items() if k != "pcm_record_overrides"}   # PCM properties do not exist in the water-only tank
            pl = one(cid, None, dv, y, pl_extra)
            m, t, mp, tp = res["metrics"], res["tes"], pl["metrics"], pl["tes"]
            per.append((t["E_del45_window_kWh"] - tp["E_del45_window_kWh"], t["E_del45_annual_kWh"] - tp["E_del45_annual_kWh"],
                        (m["shield_water_h"] + m["shield_pcm_h"]) - mp["shield_water_h"], m["max_pcm_temp_C"], m["max_water_temp_C"]))
        a = np.array(per)
        row = {"regime": cid, "pcm": pcm, "variant": name, "g_window": a[:, 0].mean(), "g_annual": a[:, 1].mean(), "d_overheat": a[:, 2].mean(),
               "t_pcm_max": a[:, 3].max(), "t_water_max": a[:, 4].max()}
        if base is None:
            base = row["g_window"]
        row["delta_g_window"] = row["g_window"] - base
        row["band_g_window"] = band
        row["beyond_band"] = bool(abs(row["delta_g_window"]) > band)
        rows.append(row)
        print(f"{name:12s} g_window={row['g_window']:.1f} delta={row['delta_g_window']:+.1f} (band {band:.1f}) PCM peak {row['t_pcm_max']:.1f} C", flush=True)
        pd.DataFrame(rows).to_csv(OUT / f"g22_sensitivity_r{cid}.csv", index=False)


if __name__ == "__main__":
    main(int(sys.argv[1]))
