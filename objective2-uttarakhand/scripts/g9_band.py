"""
scripts/g9_band.py
=====================
WP6 repeatability band (plan WP6; decisions D9/D10): how large must a paired gain be before it counts as real?
Measured, not assumed, on 4 designs of the rank-1 O1 PCM of ONE regime (quantiles of the S2 DOE: 20 %, 50 %, 80 % of
g_annual and the best feasible one). Usage: python scripts/g9_band.py <cluster_id>

For each design (mean over the 5 explore years, paired against the water-only tank at the same flow and the SAME
variant) the change in each objective is recorded for:
  dt        time step 150 s -> 75 s
  nodes     multi-node N = 10 -> 20
  latent    PCM latent heat +-10 %
  conduct   PCM conductivity +-20 %
plus the weather-year spread (sd of the per-year paired gain / sqrt(5) = standard error of the 5-year mean).
Writes results/g9_band_r<c>.csv (per design x variant x objective).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.design.space import geometry_bounds, to_design
from src.io_utils import get_regime
from src.optimize.baseline import plain_at
from src.simulation.run_case import run_case
from src.weather import roles
from src.weather.inventory import CURRENT_MEDOIDS

OBJ = ("g_window", "g_annual", "d_overheat")


def run_gains(cid, pcm, dv, years, n_nodes=10, sys_over=None, pcm_over=None, exact_plain=False):
    """Mean and per-year paired gains for one design under one variant."""
    per_year = []
    for y in years:
        w = roles.load_point_year("uttarakhand", cid, CURRENT_MEDOIDS[cid], y, "explore")
        kw = dict(design_bounds=geometry_bounds(), weather=w, tank_model="multinode", n_nodes=n_nodes,
                  compute_tes_metrics=True, night_day_stride=0, system_config_overrides=sys_over)
        r = run_case("uttarakhand", cid, pcm, dv, pcm_record_overrides=pcm_over, **kw)
        m, t = r["metrics"], r["tes"]
        if exact_plain:
            p = run_case("uttarakhand", cid, None, dv, **kw)
            pw, pa, ps = p["tes"]["E_del45_window_kWh"], p["tes"]["E_del45_annual_kWh"], p["metrics"]["shield_water_h"]
        else:
            b = plain_at(cid, y, dv.flow_rate_kg_s, "explore")
            pw, pa, ps = b["E_del45_window_kWh"], b["E_del45_annual_kWh"], b["shield_water_h"]
        per_year.append({"g_window": t["E_del45_window_kWh"] - pw, "g_annual": t["E_del45_annual_kWh"] - pa,
                         "d_overheat": (m["shield_water_h"] + m["shield_pcm_h"]) - ps})
    df = pd.DataFrame(per_year)
    return df.mean(), df.std(ddof=1)


def main(cid):
    pcm = get_regime("uttarakhand", cid)["pcm_shortlist"][0]
    doe = pd.read_csv(f"results/g8_s2_r{cid}_p1.csv")
    doe = doe[(doe.status == "ok") & (doe.feasible == True)].sort_values("g_annual")  # noqa: E712
    picks = [doe.iloc[int(q * (len(doe) - 1))] for q in (0.2, 0.5, 0.8)] + [doe.iloc[-1]]
    years = roles.years_for("explore")
    rows = []
    for k, d in enumerate(picks):
        dv = to_design(float(d.R_in_m), float(d.fraction), float(d.flow), d.arrangement)
        base, sd = run_gains(cid, pcm, dv, years)
        for o in OBJ:
            rows.append({"regime": cid, "design": k, "variant": "base", "objective": o, "value": base[o],
                         "delta": 0.0, "year_sd": sd[o]})
        variants = {
            "dt75": dict(sys_over={"solver": {"timestep_s": 75}}, exact_plain=True),
            "nodes20": dict(n_nodes=20, exact_plain=True),
            "latent-10": dict(pcm_over={"latent_heat_kJ_kg": None}),
            "latent+10": dict(pcm_over={"latent_heat_kJ_kg": None}),
            "cond-20": dict(pcm_over={"TC_W_mK": None}),
            "cond+20": dict(pcm_over={"TC_W_mK": None}),
        }
        from src.io_utils import get_pcm_properties
        rec = get_pcm_properties("uttarakhand", pcm)
        variants["latent-10"]["pcm_over"] = {"latent_heat_kJ_kg": rec["latent_heat_kJ_kg"] * 0.9}
        variants["latent+10"]["pcm_over"] = {"latent_heat_kJ_kg": rec["latent_heat_kJ_kg"] * 1.1}
        variants["cond-20"]["pcm_over"] = {"TC_W_mK": rec["TC_W_mK"] * 0.8}
        variants["cond+20"]["pcm_over"] = {"TC_W_mK": rec["TC_W_mK"] * 1.2}
        for name, kw in variants.items():
            v, _ = run_gains(cid, pcm, dv, years, **kw)
            for o in OBJ:
                rows.append({"regime": cid, "design": k, "variant": name, "objective": o, "value": v[o],
                             "delta": v[o] - base[o], "year_sd": sd[o]})
        print(cid, "design", k, "done", flush=True)
        pd.DataFrame(rows).to_csv(f"results/g9_band_r{cid}.csv", index=False)
    print("written")


if __name__ == "__main__":
    main(int(sys.argv[1]))
