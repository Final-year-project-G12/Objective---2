"""
scripts/r10_supplementary.py  -  supplementary Objective 2 studies required by the plan AFTER the main result (never used for selection)
==========================================================================================================================================
Every case pairs PCM designs with a water-only twin that receives the SAME change. Outputs go to results/supp_*.csv; the frozen
selection, test and contract are not touched.

  sens <c>      plan O2-6 / O2-12 / L4 one-at-a-time sensitivity on the common plant, around regime c's frozen best PCM design
                (results/g10_selection_r<c>.json "chosen"), explore years 2016-2019, 150 s, the three anchors:
                collector F_R(tau alpha) x0.9 / x1.1 and F_R U_L x0.8 / x1.2; F_R(flow) ON at flows 0.010-0.050 kg/s (design and twin at the
                same flow); manufacturing tolerance: capsule wall 0.6 / 1.0 mm (nominal 0.8), inner radius -+0.5 mm, PCM fill 95 % (density
                x0.95); cold mains: the state's coldest mains (range_low) and the regime estimate -4 K; lower-tail sun: GHI x0.85.
  aux <c>       plan 4.3 cold-regime item (iii): an auxiliary-heater-enabled system as a SEPARATE scenario. An ideal in-line booster tops
                every draw up to the delivery threshold; its energy is the simulator's unmet energy. Water-only tank vs the frozen best PCM
                design (three anchors), select years 2020-2021 at 37.5 s, at 45 C and at 50 C. Not a PCM benefit claim.
  cases <name>  plan decision 12 optional plant cases: d70 (70 L/day), d150 (150 L/day), legacy (2.5 m2, 300 L/day), t150 (150 L tank,
                150 L/day). Per regime a fixed design set (each O1 PCM x PCM fraction 5/10/20/30/40 % x inner radius 25/40 mm, staggered),
                three anchors, the representative explore year at 150 s. Diagnostic of direction only: the band is the main plant's.
  boundary      plan O2-11 bound-contact diagnostic: the picks sit at the 2 % fraction floor, so the box is extended below it
                (8 log-spaced capsule counts from 1 up to the pick's count, the pick's radius and arrangement, three anchors, representative year, 150 s).
Usage: python scripts/r10_supplementary.py sens <c> | aux <c> | cases <name> | boundary
"""
import json
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.design.box import REP_YEAR, anchors, full_dt                          # noqa: E402
from src.design.schema import DesignVector                                     # noqa: E402
from src.design.space import geometry_bounds, to_design, wall_m                 # noqa: E402
from src.io_utils import get_pcm_properties, get_regime, load_state_config, load_system_config   # noqa: E402
from src.simulation.run_case import run_case                                   # noqa: E402
from src.weather import roles                                                   # noqa: E402
from src.weather.inventory import CURRENT_MEDOIDS, REGIMES                      # noqa: E402

RES = ROOT / "results"


def band(cid):
    b = pd.read_csv(RES / "wp6_band.csv")
    return float(b[(b.scope == f"r{cid}") & (b.objective == "g_window")].band.iloc[0])


def pick(cid):
    return json.loads((RES / f"g10_selection_r{cid}.json").read_text())["chosen"]


def pair(cid, pcm, dv, years, purpose="explore", dt=150, sys_over=None, pcm_over=None, mains=None, vol=1.0, wpert=None,
         anchor_list=None):
    """Per (year, anchor) paired results of one design against its water-only twin under the SAME change."""
    ov = {"solver": {"timestep_s": dt}}
    for k, v in (sys_over or {}).items():
        ov[k] = {**ov.get(k, {}), **v}
    rows = []
    for y in years:
        w = roles.load_point_year("uttarakhand", cid, CURRENT_MEDOIDS[cid], y, purpose)
        kw = dict(design_bounds=geometry_bounds(), weather=w, tank_model="multinode", n_nodes=10, compute_tes_metrics=True,
                  night_day_stride=0, record_hourly=False, system_config_overrides=ov, mains_temp_override_C=mains,
                  volume_multiplier=vol, weather_perturbation=wpert)
        p = run_case("uttarakhand", cid, None, dv, stack_anchor="center", **kw)
        if p["metrics"] is None:
            return pd.DataFrame([{"valid": False, "reason": p["reason"]}])
        for a in (anchor_list or anchors()):
            r = run_case("uttarakhand", cid, pcm, dv, stack_anchor=a, pcm_record_overrides=pcm_over, **kw) if pcm else p
            if r["metrics"] is None:
                return pd.DataFrame([{"valid": False, "reason": r["reason"]}])
            m, t, pm, pt = r["metrics"], r["tes"], p["metrics"], p["tes"]
            rows.append({"valid": True, "year": y, "anchor": a,
                         "g_window": t["E_del45_window_kWh"] - pt["E_del45_window_kWh"],
                         "g_annual": t["E_del45_annual_kWh"] - pt["E_del45_annual_kWh"],
                         "d_overheat": (m["shield_water_h"] + m["shield_pcm_h"]) - pm["shield_water_h"],
                         "t_pcm_max": m["max_pcm_temp_C"], "t_water_max": m["max_water_temp_C"],
                         "unmet_kWh": m["unmet_energy_kWh"], "plain_unmet_kWh": pm["unmet_energy_kWh"],
                         "plain_useful_kWh": pm["useful_energy_kWh"], "useful_kWh": m["useful_energy_kWh"]})
    return pd.DataFrame(rows)


def summarise(d, **tags):
    if not d.valid.all():
        return {**tags, "valid": False, "reason": d.reason.iloc[0]}
    by_a = d.groupby("anchor").g_window.mean()
    return {**tags, "valid": True, "g_window": d.g_window.mean(), "g_window_worst_anchor": by_a.min(), "g_annual": d.g_annual.mean(),
            "d_overheat": d.d_overheat.mean(), "t_pcm_max": d.t_pcm_max.max(), "t_water_max": d.t_water_max.max(),
            "unmet_kWh": d.unmet_kWh.mean(), "plain_unmet_kWh": d.plain_unmet_kWh.mean(), "plain_useful_kWh": d.plain_useful_kWh.mean(),
            "feasible": bool(d.t_pcm_max.max() <= 65.0 and d.t_water_max.max() <= 75.0)}


def sens(cid):
    ch = pick(cid)
    pcm, r_in, n, arr = ch["pcm"], float(ch["R_in_m"]), int(ch["N"]), ch["arrangement"]
    cfg, st, reg = load_system_config(), load_state_config("uttarakhand"), get_regime("uttarakhand", cid)
    rec = get_pcm_properties("uttarakhand", pcm)
    years = roles.years_for("explore")
    dv = lambda r=r_in, q=0.03: DesignVector(capsule_diameter_m=2 * (r + wall_m()), n_capsule=n, flow_rate_kg_s=q, capsule_arrangement=arr)  # noqa: E731
    col = cfg["collector"]
    var = {"base": {}, "fr_tau_alpha x0.9": {"sys_over": {"collector": {"fr_tau_alpha": col["fr_tau_alpha"] * 0.9}}},
           "fr_tau_alpha x1.1": {"sys_over": {"collector": {"fr_tau_alpha": col["fr_tau_alpha"] * 1.1}}},
           "fr_ul x0.8": {"sys_over": {"collector": {"fr_ul_W_m2K": col["fr_ul_W_m2K"] * 0.8}}},
           "fr_ul x1.2": {"sys_over": {"collector": {"fr_ul_W_m2K": col["fr_ul_W_m2K"] * 1.2}}},
           "wall 0.6 mm": {"sys_over": {"pcm_integration": {"capsule_wall_thickness_m": 0.0006}}},
           "wall 1.0 mm": {"sys_over": {"pcm_integration": {"capsule_wall_thickness_m": 0.0010}}},
           "R_in -0.5 mm": {"dv": dv(r_in - 0.0005)}, "R_in +0.5 mm": {"dv": dv(r_in + 0.0005)},
           "PCM fill 95 %": {"pcm_over": {"density_solid_kg_m3": rec["density_solid_kg_m3"] * 0.95,
                                          "density_liquid_kg_m3": rec["density_liquid_kg_m3"] * 0.95}},
           f"mains {st['mains_temperature_C']['range_low']:.1f} C (state coldest)": {"mains": float(st["mains_temperature_C"]["range_low"])},
           "mains -4 K": {"mains": float(reg["T_mains_est_C"]) - 4.0},
           "GHI x0.85": {"wpert": {"ghi_multiplier": 0.85}}}
    for q in (0.010, 0.020, 0.030, 0.040, 0.050):
        var[f"F_R(flow) on, {q:.3f} kg/s"] = {"sys_over": {"collector": {"flow_dependent_fr": {**col["flow_dependent_fr"], "enabled": True}}},
                                              "dv": dv(q=q)}
    rows = []
    for name, v in var.items():
        d = pair(cid, pcm, v.get("dv", dv()), years, sys_over=v.get("sys_over"), pcm_over=v.get("pcm_over"), mains=v.get("mains"),
                 wpert=v.get("wpert"))
        rows.append(summarise(d, regime=cid, pcm=pcm, variant=name))
        print(cid, name, flush=True)
    t = pd.DataFrame(rows)
    base = t.loc[t.variant == "base", "g_window"].iloc[0]
    t["delta_g_window"] = t.g_window - base
    t["band_g_window"] = band(cid)
    t["recommendation_would_change"] = t.g_window_worst_anchor > t.band_g_window
    t.to_csv(RES / f"supp_sensitivity_r{cid}.csv", index=False)


def aux(cid):
    ch = pick(cid)
    dv = to_design(float(ch["R_in_m"]), float(ch["fraction"]), 0.03, ch["arrangement"])
    rows = []
    for tgt in (45.0, 50.0):
        d = pair(cid, ch["pcm"], dv, roles.years_for("select"), purpose="select", dt=full_dt(),
                 sys_over={"delivery": {"target_temp_C": tgt}})
        for y, g in d.groupby("year"):
            rows.append({"regime": cid, "threshold_C": tgt, "year": y, "pcm": ch["pcm"],
                         "aux_heater_kWh_water_only": float(g.plain_unmet_kWh.iloc[0]),
                         "aux_heater_kWh_pcm_mean_anchor": float(g.unmet_kWh.mean()),
                         "aux_saving_by_pcm_kWh": float(g.plain_unmet_kWh.iloc[0] - g.unmet_kWh.mean()),
                         "solar_useful_kWh_water_only": float(g.plain_useful_kWh.iloc[0])})
        print(cid, tgt, flush=True)
    pd.DataFrame(rows).to_csv(RES / f"supp_aux_heater_r{cid}.csv", index=False)


CASES = {"d70": {"vol": 0.7}, "d150": {"vol": 1.5},
         "legacy": {"vol": 3.0, "sys_over": {"collector": {"area_m2": 2.5}}},
         "t150": {"vol": 1.5, "sys_over": {"tank": {"volume_L": 150.0}}, "tank_L": 150.0}}


def cases(name):
    c = CASES[name]
    v_tank = c.get("tank_L", load_system_config()["tank"]["volume_L"]) / 1000.0
    rows = []
    for cid in REGIMES:
        for k, pcm in enumerate(get_regime("uttarakhand", cid)["pcm_shortlist"], start=1):
            for r_in in (0.025, 0.040):
                for f in (0.05, 0.10, 0.20, 0.30, 0.40):
                    n = max(1, round(f * v_tank / (4 / 3 * math.pi * (r_in + wall_m()) ** 3)))
                    dv = DesignVector(capsule_diameter_m=2 * (r_in + wall_m()), n_capsule=n, flow_rate_kg_s=0.03, capsule_arrangement="staggered")
                    d = pair(cid, pcm, dv, [REP_YEAR[cid]], sys_over=c.get("sys_over"), vol=c["vol"])
                    rows.append(summarise(d, case=name, regime=cid, pcm=pcm, pcm_rank=k, R_in_m=r_in, fraction=f, N=n))
            print(name, cid, pcm, flush=True)
    t = pd.DataFrame(rows)
    t["band_g_window_main_plant"] = t.regime.map({c: band(c) for c in REGIMES})
    t.to_csv(RES / f"supp_case_{name}.csv", index=False)


def boundary():
    rows = []
    for cid in REGIMES:
        ch = pick(cid)
        for n in sorted({int(round(x)) for x in __import__("numpy").geomspace(1, int(ch["N"]), 8)}):     # 8 log-spaced counts down to 1
            dv = DesignVector(capsule_diameter_m=2 * (float(ch["R_in_m"]) + wall_m()), n_capsule=n, flow_rate_kg_s=0.03,
                              capsule_arrangement=ch["arrangement"])
            d = pair(cid, ch["pcm"], dv, [REP_YEAR[cid]])
            frac = n * 4 / 3 * math.pi * (float(ch["R_in_m"]) + wall_m()) ** 3 / (load_system_config()["tank"]["volume_L"] / 1000.0)
            rows.append(summarise(d, regime=cid, pcm=ch["pcm"], N=n, fraction=frac))
        print("boundary", cid, flush=True)
    t = pd.DataFrame(rows)
    t["band_g_window"] = t.regime.map({c: band(c) for c in REGIMES})
    t.to_csv(RES / "supp_boundary_below_2pct.csv", index=False)


if __name__ == "__main__":
    cmd = sys.argv[1]
    {"sens": lambda: sens(int(sys.argv[2])), "aux": lambda: aux(int(sys.argv[2])), "cases": lambda: cases(sys.argv[2]),
     "boundary": boundary}[cmd]()
