"""
scripts/g9_band.py
=====================
Repeatability band (plan O2-12, recipe frozen in docs/REBUILD_COMMON100L.md section 5 on 2026-11-23): how large must a paired gain be
before it counts as real? Measured on 4 designs of the rank-1 O1 PCM of ONE regime (the 20 / 50 / 80 % quantiles of g_annual among
the feasible cheap-DOE designs and the best feasible g_window), centre anchor, flow 0.030, explore years 2016-2019.
Usage: python scripts/g9_band.py <cluster_id>

Variants (each paired with a water-only twin that gets the SAME change):
  base            150 s, 10 nodes                                   (also gives the per-year sd -> year-scatter term)
  dt_report, dt_half  report step R = full_dt() (18.75 s at 175 L/day) and R/2 -> term: R vs R/2 (discretisation at the report step)
  nodes20_report  20 nodes at R (against dt_report, 10 nodes)       -> term: node count at the report step
  latent+-10, cond+-20                                              -> term: PCM properties (larger of the two)
  member:<pid>    the two most-populated non-medoid member points   -> term: medoid versus member points
  demand0.8/1.2   volume multiplier                                 -> term: demand
  mains-2/+2      regime mains estimate -+2 K                       -> term: mains
Writes results/g9_band_r<c>.csv (design x variant x objective: value, delta against its reference variant, per-year sd).
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.design.box import flow_fixed, full_dt            # noqa: E402
from src.design.space import geometry_bounds, to_design   # noqa: E402
from src.io_utils import get_pcm_properties, get_regime   # noqa: E402
from src.simulation.run_case import run_case               # noqa: E402
from src.weather import roles                               # noqa: E402
from src.weather.inventory import CURRENT_MEDOIDS          # noqa: E402

OBJ = ("g_window", "g_annual", "d_overheat")
MEMBERS_CSV = roles.WEATHER_POINT_YEARS_DIR / "member_inventory.csv"


def run_gains(cid, pcm, dv, years, point=None, dt=150, n_nodes=10, pcm_over=None, mains=None, vol=1.0):
    per_year = []
    for y in years:
        w = roles.load_point_year("uttarakhand", cid, point or CURRENT_MEDOIDS[cid], y, "explore")
        kw = dict(design_bounds=geometry_bounds(), weather=w, tank_model="multinode", n_nodes=n_nodes, stack_anchor="center",
                  compute_tes_metrics=True, night_day_stride=0, record_hourly=False, volume_multiplier=vol,
                  mains_temp_override_C=mains, system_config_overrides={"solver": {"timestep_s": dt}})
        r = run_case("uttarakhand", cid, pcm, dv, pcm_record_overrides=pcm_over, **kw)
        p = run_case("uttarakhand", cid, None, dv, **kw)
        per_year.append({"g_window": r["tes"]["E_del45_window_kWh"] - p["tes"]["E_del45_window_kWh"],
                         "g_annual": r["tes"]["E_del45_annual_kWh"] - p["tes"]["E_del45_annual_kWh"],
                         "d_overheat": (r["metrics"]["shield_water_h"] + r["metrics"]["shield_pcm_h"]) - p["metrics"]["shield_water_h"]})
    df = pd.DataFrame(per_year)
    return df.mean(), df.std(ddof=1)


def main(cid):
    reg = get_regime("uttarakhand", cid)
    pcm = reg["pcm_shortlist"][0]
    t_m = float(reg["T_mains_est_C"])
    rec = get_pcm_properties("uttarakhand", pcm)
    members = pd.read_csv(MEMBERS_CSV)
    members = members[(members.cluster_id == cid) & members.accepted].point_id.unique().tolist()
    doe = pd.read_csv(f"results/g8_s2_r{cid}_p1.csv")
    doe = doe[(doe.status == "ok") & (doe.feasible == True)].sort_values("g_annual")  # noqa: E712
    picks = [doe.iloc[int(q * (len(doe) - 1))] for q in (0.2, 0.5, 0.8)] + [doe.sort_values("g_window").iloc[-1]]
    years = roles.years_for("explore")
    variants = {  # name: (kwargs, reference variant for the delta)
        "base": ({}, "base"),
        "dt_report": ({"dt": full_dt()}, "base"), "dt_half": ({"dt": full_dt() / 2}, "dt_report"),
        "nodes20_report": ({"dt": full_dt(), "n_nodes": 20}, "dt_report"),
        "latent-10": ({"pcm_over": {"latent_heat_kJ_kg": rec["latent_heat_kJ_kg"] * 0.9}}, "base"),
        "latent+10": ({"pcm_over": {"latent_heat_kJ_kg": rec["latent_heat_kJ_kg"] * 1.1}}, "base"),
        "cond-20": ({"pcm_over": {"TC_W_mK": rec["TC_W_mK"] * 0.8}}, "base"),
        "cond+20": ({"pcm_over": {"TC_W_mK": rec["TC_W_mK"] * 1.2}}, "base"),
        "demand0.8": ({"vol": 0.8}, "base"), "demand1.2": ({"vol": 1.2}, "base"),
        "mains-2": ({"mains": t_m - 2.0}, "base"), "mains+2": ({"mains": t_m + 2.0}, "base"),
        **{f"member:{pid}": ({"point": pid}, "base") for pid in members},
    }
    rows = []
    for k, d in enumerate(picks):
        dv = to_design(float(d.R_in_m), float(d.fraction), flow_fixed(), d.arrangement)
        vals, sds = {}, {}
        for name, (kw, ref) in variants.items():
            vals[name], sds[name] = run_gains(cid, pcm, dv, years, **kw)
            for o in OBJ:
                rows.append({"regime": cid, "design": k, "R_in_m": float(d.R_in_m), "fraction": float(d.fraction),
                             "arrangement": d.arrangement, "variant": name, "reference": ref, "objective": o,
                             "value": vals[name][o], "delta": vals[name][o] - vals[ref][o], "year_sd": sds["base"][o]})
        print(cid, "design", k, "done", flush=True)
        pd.DataFrame(rows).to_csv(f"results/g9_band_r{cid}.partial.csv", index=False)
    pd.DataFrame(rows).to_csv(f"results/g9_band_r{cid}.csv", index=False)
    Path(f"results/g9_band_r{cid}.partial.csv").unlink(missing_ok=True)
    print("written", flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]))
