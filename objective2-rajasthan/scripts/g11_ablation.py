"""
scripts/g11_ablation.py
==========================
G11 / WP8 - one-variable-at-a-time ablations around the CHOSEN design of a regime (g10_selection_r<c>.json), explore years
2016-2020 (the held-out years are not touched). Usage: python scripts/g11_ablation.py <cluster_id>

Ablated variables (approved ranges): thickness at constant PCM mass, count (via fraction), flow, arrangement and the
stack-anchor setting (tank-model assumption). Each is compared with the WP6 band (wp6_band.csv, regime scope).
Controls
  negative  N1 design variables on the WATER-ONLY tank (R, N, arrangement, anchor changed) -> results must be identical
            N2 the chosen design run twice -> identical (determinism)
            N3 capsule-wall conductivity x10 -> physically inert, expected change inside the band
  positive  P1 latent heat = 0 (PCM becomes sensible-only) -> g_window must fall by more than the band
            P2 PCM fraction x2 (capped at 20 %) -> gain must change by more than the band
            P3 Tm set to 45 C (a SYNTHETIC PCM matched to the delivery target; diagnostic, not an O1 PCM) -> night-window
               gain should respond: shows whether the metrics can see a PCM that is designed for this job
Writes results/redesign/g11_ablation_r<c>.csv (rows: block, level, objective means over 5 years + year sd).
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.design.schema import DesignVector
from src.design.space import capsule_outer_volume_m3, geometry_bounds, to_design, v_tank_m3, wall_m
from src.io_utils import get_pcm_properties
from src.optimize.baseline import plain_at
from src.simulation.run_case import run_case
from src.weather import roles
from src.weather.inventory import CURRENT_MEDOIDS

OUT = Path("results/redesign")


def design_from(r, n, q, arr):
    return DesignVector(capsule_diameter_m=2 * (r + wall_m()), n_capsule=int(n), flow_rate_kg_s=float(q), capsule_arrangement=arr)


def run(cid, pcm, dv, anchor="center", sys_over=None, pcm_over=None, years=None):
    years = years or roles.years_for("explore")
    rows = []
    for y in years:
        w = roles.load_point_year("rajasthan", cid, CURRENT_MEDOIDS[cid], y, "explore")
        r = run_case("rajasthan", cid, pcm, dv, design_bounds=geometry_bounds(), weather=w, tank_model="multinode", n_nodes=10,
                     stack_anchor=anchor, compute_tes_metrics=True, night_day_stride=0, system_config_overrides=sys_over,
                     pcm_record_overrides=pcm_over)
        if not r["valid"]:
            return None
        m, t = r["metrics"], r["tes"]
        if pcm is None:
            rows.append({"E_window": t["E_del45_window_kWh"], "E_annual": t["E_del45_annual_kWh"], "useful": m["useful_energy_kWh"],
                         "shield_h": m["shield_water_h"] + m["shield_pcm_h"], "t_pcm": m["max_pcm_temp_C"]})
        else:
            b = plain_at(cid, y, dv.flow_rate_kg_s, "explore")
            rows.append({"g_window": t["E_del45_window_kWh"] - b["E_del45_window_kWh"],
                         "g_annual": t["E_del45_annual_kWh"] - b["E_del45_annual_kWh"],
                         "d_overheat": (m["shield_water_h"] + m["shield_pcm_h"]) - b["shield_water_h"],
                         "t_pcm_max": m["max_pcm_temp_C"], "hours_over_limit": m["hours_over_limit"]})
    df = pd.DataFrame(rows)
    return df.mean(), df.std(ddof=1)


def main(cid):
    sel = json.loads((OUT / f"g10_selection_r{cid}.json").read_text())
    ch = sel["chosen"]
    pcm, r0, n0, q0, arr0 = ch["pcm"], float(ch["R_in_m"]), int(ch["N"]), float(ch["flow"]), ch["arrangement"]
    rows = []

    def add(block, level, res, extra=None):
        if res is None:
            rows.append({"regime": cid, "block": block, "level": level, "valid": False, **(extra or {})})
            return
        mean, sd = res
        row = {"regime": cid, "block": block, "level": level, "valid": True, **(extra or {})}
        for k in mean.index:
            row[k] = mean[k]
            row[k + "_sd"] = sd[k]
        rows.append(row)

    base = run(cid, pcm, design_from(r0, n0, q0, arr0))
    add("base", "chosen", base, {"R_in_mm": r0 * 1000, "N": n0, "flow": q0, "arrangement": arr0})
    # --- thickness at constant inner PCM volume
    for rmm in (10, 15, 20, 25, 30, 40):
        r = rmm / 1000.0
        n = max(1, round(n0 * (r0 / r) ** 3))
        add("thickness_const_mass", f"R{rmm}", run(cid, pcm, design_from(r, n, q0, arr0)), {"R_in_mm": rmm, "N": n})
    # --- count via fraction
    for f in (0.02, 0.04, 0.07, 0.10, 0.14, 0.20):
        n = max(1, min(round(f * v_tank_m3() / capsule_outer_volume_m3(r0)), int(0.2 * v_tank_m3() / capsule_outer_volume_m3(r0))))
        add("count", f"f{f:.2f}", run(cid, pcm, design_from(r0, n, q0, arr0)), {"fraction": n * capsule_outer_volume_m3(r0) / v_tank_m3(), "N": n})
    # --- flow
    for q in (0.010, 0.020, 0.030, 0.040, 0.050):
        add("flow", f"q{q:.3f}", run(cid, pcm, design_from(r0, n0, q, arr0)), {"flow": q})
    # --- arrangement x anchor
    for arr in ("single-layer", "staggered", "radial"):
        for anchor in ("bottom", "center", "top"):
            add("arrangement_anchor", f"{arr}|{anchor}", run(cid, pcm, design_from(r0, n0, q0, arr), anchor=anchor),
                {"arrangement": arr, "anchor": anchor})
    # --- negative controls
    plain0 = run(cid, None, design_from(r0, n0, q0, arr0))
    for lab, dv, anchor in (("plain|R10_N400_radial", design_from(0.010, 400, q0, "radial"), "top"),
                            ("plain|R40_N5_single", design_from(0.040, 5, q0, "single-layer"), "bottom"),
                            ("plain|chosen", design_from(r0, n0, q0, arr0), "center")):
        res = run(cid, None, dv, anchor=anchor)
        add("neg_control_plain_invariance", lab, res, {"max_abs_diff_vs_plain": float(np.abs(res[0] - plain0[0]).max())})
    again = run(cid, pcm, design_from(r0, n0, q0, arr0))
    add("neg_control_determinism", "rerun", again, {"max_abs_diff_vs_base": float(np.abs(again[0] - base[0]).max())})
    add("neg_control_inert_wall_k", "wall_k_x10",
        run(cid, pcm, design_from(r0, n0, q0, arr0), sys_over={"pcm_integration": {"capsule_wall_conductivity_W_mK": 2050.0}}))
    # --- positive controls
    rec = get_pcm_properties("rajasthan", pcm)
    add("pos_control_latent_zero", "L=0", run(cid, pcm, design_from(r0, n0, q0, arr0), pcm_over={"latent_heat_kJ_kg": 0.0}))
    n2 = min(2 * n0, int(0.2 * v_tank_m3() / capsule_outer_volume_m3(r0)))
    add("pos_control_fraction_x2", f"N{n2}", run(cid, pcm, design_from(r0, n2, q0, arr0)), {"N": n2})
    add("pos_control_Tm45_synthetic", "Tm=45C", run(cid, pcm, design_from(r0, n0, q0, arr0), pcm_over={"Tm_C": 45.0}),
        {"note": "synthetic PCM matched to the 45 C delivery target - diagnostic only"})
    pd.DataFrame(rows).to_csv(OUT / f"g11_ablation_r{cid}.csv", index=False)
    print("written", cid, len(rows))


if __name__ == "__main__":
    main(int(sys.argv[1]))
