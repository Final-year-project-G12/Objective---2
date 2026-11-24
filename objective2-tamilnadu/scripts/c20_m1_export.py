"""
scripts/c20_m1_export.py   (MATLAB checkpoint M1, step 1: simulator export)
=============================================================================
Runs the Objective 2 multi-node kernel for the SEVEN design criteria of the Fluent study (regime 0 + its funnel-winning O1 PCM) and for the four O1 PCMs
in the optimal geometry, and writes everything MATLAB needs to show how the water warms, how the capsules melt and how the criteria differ:

  results/m1/manifest.json                     designs, geometry (capsules per node), PCM properties, run settings, annual metrics, file list
  results/m1/discharge_<case>.csv              Fluent-style sealed discharge: water 30 C, capsules 70 C, no sun, no draw, 12 h (hourly output of the kernel)
  results/m1/day_<case>_<daykind>.csv          48 h real-weather window (select year 2020): per-node water temperature, per-node capsule liquid fraction, energy terms
  results/m1/pcm_<name>_<daykind>.csv          the four O1 PCMs in the optimal geometry, same windows
  results/m1/annual_<case>.csv                 annual paired metrics of each criterion vs the water-only tank (select year 2020, centre anchor, dt 37.5 s)
All numbers come from src/simulation (the optimiser's own evaluator). This is data for visualisation, not a second simulator.
Usage: python scripts/c20_m1_export.py [--dev]     (--dev uses a stand-in optimum if the funnel has not finished)
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.design.space import capsule_outer_volume_m3, geometry_bounds, to_design, v_tank_m3          # noqa: E402
from src.io_utils import get_pcm_properties, get_regime                                              # noqa: E402
from src.simulation.capsule_enthalpy import pcm_props_from_record, temperature_and_liquid_fraction_of_enthalpy   # noqa: E402
from src.simulation.run_case import run_case                                                         # noqa: E402
from src.simulation.tank_model_multinode import layout_from_geometry                                 # noqa: E402
from src.weather import roles                                                                        # noqa: E402
from src.weather.inventory import CURRENT_MEDOIDS                                                    # noqa: E402
from config import STATE                                                                             # noqa: E402

# --regime k  : regime to export (default 0). Regime 0 keeps the original folder results/m1 (docs and the Word report point at it);
#               regimes 1 and 2 go to results/m1_regime1 / results/m1_regime2. matlab_m1/m1_main.m reads the folder named in env var M1_DIR.
REGIME = int(sys.argv[sys.argv.index("--regime") + 1]) if "--regime" in sys.argv else 0
OUT = Path("results/m1") if REGIME == 0 else Path(f"results/m1_regime{REGIME}")
YEAR, DT = 2020, 37.5
FOUR_PCMS = ["RT57HC", "n-Hexacosane (C26)", "PureTemp 58", "n-Pentacosane (C25)"]
ANCHOR = "center"


def optimum(dev):
    w = Path("results/c16_funnel_winners.csv")
    if w.exists() and not dev:
        d = pd.read_csv(w)
        r = d[d.regime == REGIME].iloc[0]
        if r.recommendation == "PCM":
            return dict(pcm=r.pcm, R_in=float(r.R_in_m), fraction=float(r.fraction), arrangement=r.arrangement, N=int(r.N), note="funnel winner"), r
    pts = Path(f"results/c14_l6_points_r{REGIME}_p1.csv")
    if pts.exists() and not dev:
        p = pd.read_csv(pts)
        p = p[p.feasible == True].sort_values("g_window_mean", ascending=False).iloc[0]                  # noqa: E712
        return dict(pcm=p.pcm, R_in=float(p.R_in_m), fraction=float(p.fraction), arrangement=p.arrangement, N=int(p.N), note="search best (no funnel winner)"), None
    return dict(pcm="RT57HC", R_in=0.040, fraction=0.30, arrangement="staggered", N=0, note="DEV stand-in"), None


def n_for(r, fraction):
    return int(round(fraction * v_tank_m3() / capsule_outer_volume_m3(r)))


def frac_for_n(r, n):
    return n * capsule_outer_volume_m3(r) / v_tank_m3()


M1_TITLES = {"criteria_0_optimal_reference": "0 Optimal (reference)", "criteria_1_max_all": "1 Max of every parameter",
             "criteria_2_min_all": "2 Min of every parameter", "criteria_3_ok_not_optimal": "3 Working, not optimal",
             "criteria_4_only_30_capsules": "4 Only 30 capsules", "criteria_5_10pct_of_optimal": "5 10 % of optimal PCM",
             "criteria_6_50pct_of_optimal": "6 50 % of optimal PCM"}


def scenario_designs():
    """The seven designs from the SAME file the Fluent / node-model study uses (ansys/criteria_common/scenarios.py): one source of truth,
    so the MATLAB checkpoint and the ansys/criteria_* folders can never describe different designs (they did before 2026-11-24: criterion 3
    was a real funnel candidate of 132 capsules there and a rule-built 77 % design of 108 capsules here)."""
    import importlib.util
    p = Path(__file__).resolve().parent.parent / "ansys" / "criteria_common" / "scenarios.py"
    spec = importlib.util.spec_from_file_location("o2_criteria_scenarios", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.SCENARIOS, m.OPT


def rule_criteria(opt, row, regime):
    """The seven designs by the SAME rules as ansys/criteria_common/regen_scenarios.py, for ANY regime (that generator is written for regime 0 only).
    optimum = the regime's funnel winner | 1 max of every knob | 2 min of every knob | 3 a real evaluated candidate of the winning pair's funnel pool,
    the one closest to 70 % of the optimal gain | 4 only 30 capsules | 5 10 % and 6 50 % of the optimal capsule count (radius, flow, arrangement kept optimal)."""
    R, F, arr, N = opt["R_in"], opt["fraction"], opt["arrangement"], int(opt["N"])
    ev = pd.read_csv("results/c16_select_eval_all.csv")
    pool = ev[(ev.regime == regime) & (ev.pair == row.pair) & (ev.S0 == True)]                  # noqa: E712
    pool = pool[pool.N != N]
    if len(pool):
        c = pool.iloc[(pool.g_window_mean - 0.70 * float(row.select_g_window_mean)).abs().argsort()].iloc[0]
        r3, f3, a3 = float(c.R_in_m), float(c.fraction), c.arrangement
    else:                                                                                        # same fallback as regen_scenarios.py
        r3, f3, a3 = R, frac_for_n(R, max(1, int(round(0.77 * N)))), arr
    return [
        dict(key="criteria_0_optimal_reference", R_in=R, fraction=F, flow=0.030, arrangement=arr),
        dict(key="criteria_1_max_all", R_in=0.040, fraction=0.40, flow=0.050, arrangement="staggered"),
        dict(key="criteria_2_min_all", R_in=0.010, fraction=0.02, flow=0.010, arrangement="single-layer"),
        dict(key="criteria_3_ok_not_optimal", R_in=r3, fraction=f3, flow=0.030, arrangement=a3),
        dict(key="criteria_4_only_30_capsules", R_in=R, fraction=frac_for_n(R, 30), flow=0.030, arrangement=arr),
        dict(key="criteria_5_10pct_of_optimal", R_in=R, fraction=frac_for_n(R, max(1, int(round(0.10 * N)))), flow=0.030, arrangement=arr),
        dict(key="criteria_6_50pct_of_optimal", R_in=R, fraction=frac_for_n(R, max(1, int(round(0.50 * N)))), flow=0.030, arrangement=arr),
    ]


def check_rules_reproduce_scenarios():
    """Proof that rule_criteria() is a faithful generalisation: for regime 0 it must reproduce ansys/criteria_common/scenarios.py exactly."""
    win = pd.read_csv("results/c16_funnel_winners.csv")
    r0 = win[win.regime == 0].iloc[0]
    opt0 = dict(R_in=float(r0.R_in_m), fraction=float(r0.fraction), arrangement=r0.arrangement, N=int(r0.N))
    scen, _ = scenario_designs()
    mine = rule_criteria(opt0, r0, 0)
    for a, b in zip(mine, scen):
        d = b["design"]
        assert a["key"] == b["key"], (a["key"], b["key"])
        for k in ("R_in", "fraction", "flow"):
            assert abs(a[k] - d[k]) < 1e-9, f"{a['key']} {k}: rule {a[k]} != scenarios.py {d[k]}"
        assert a["arrangement"] == d["arrangement"], f"{a['key']} arrangement"


def criteria(opt, row=None, regime=0):
    if opt.get("note") == "funnel winner":
        check_rules_reproduce_scenarios()
        if regime == 0:                                                                          # regime 0: the shared single source of truth
            scen, sopt = scenario_designs()
            if abs(sopt["R_in"] - opt["R_in"]) > 1e-9 or abs(sopt["fraction"] - opt["fraction"]) > 1e-9 or sopt["arrangement"] != opt["arrangement"]:
                raise SystemExit("ansys/criteria_common/scenarios.py has a different optimum from results/c16_funnel_winners.csv: "
                                 "run ansys/criteria_common/regen_scenarios.py first")
            return [dict(key=s["key"], title=M1_TITLES[s["key"]], R_in=s["design"]["R_in"], fraction=s["design"]["fraction"], flow=s["design"]["flow"],
                         arrangement=s["design"]["arrangement"]) for s in scen]
        return [dict(s, title=M1_TITLES[s["key"]]) for s in rule_criteria(opt, row, regime)]
    R, F, arr = opt["R_in"], opt["fraction"], opt["arrangement"]       # DEV stand-in only (no funnel winner yet): rule-built designs
    N = n_for(R, F)
    return [
        dict(key="criteria_0_optimal_reference", title="0 Optimal (reference)", R_in=R, fraction=F, flow=0.030, arrangement=arr),
        dict(key="criteria_1_max_all", title="1 Max of every parameter", R_in=0.040, fraction=0.40, flow=0.050, arrangement="staggered"),
        dict(key="criteria_2_min_all", title="2 Min of every parameter", R_in=0.010, fraction=0.02, flow=0.010, arrangement="single-layer"),
        dict(key="criteria_3_ok_not_optimal", title="3 Working, not optimal", R_in=R, fraction=frac_for_n(R, max(1, int(round(0.77 * N)))), flow=0.030, arrangement=arr),
        dict(key="criteria_4_only_30_capsules", title="4 Only 30 capsules", R_in=R, fraction=frac_for_n(R, 30), flow=0.030, arrangement=arr),
        dict(key="criteria_5_10pct_of_optimal", title="5 10 % of optimal PCM", R_in=R, fraction=frac_for_n(R, max(1, int(round(0.10 * N)))), flow=0.030, arrangement=arr),
        dict(key="criteria_6_50pct_of_optimal", title="6 50 % of optimal PCM", R_in=R, fraction=frac_for_n(R, max(1, int(round(0.50 * N)))), flow=0.030, arrangement=arr),
    ]


def pick_days(w):
    d = w.copy()
    d["date"] = pd.to_datetime(d.timestamp_utc).dt.tz_convert("Asia/Kolkata").dt.date
    g = d.groupby("date").GHI_Wm2.sum() / 1000.0
    g = g[(pd.Series(g.index).apply(lambda x: x.month).values >= 1)]
    clear = g.idxmax()
    mid = (g - g.median()).abs().idxmin()
    cloudy = g[g > 0.5].idxmin()
    return {"clear": clear, "average": mid, "cloudy": cloudy}, d


def window(d, date, hours=48):
    idx = d.index[d.date == date]
    i0 = int(idx[0])
    return i0, min(i0 + hours, len(d))


def run(cid, pcm, spec, w, dt, **kw):
    dv = to_design(spec["R_in"], spec["fraction"], spec["flow"], spec["arrangement"])
    r = run_case(STATE, cid, pcm, dv, design_bounds=geometry_bounds(), weather=w, tank_model="multinode", n_nodes=10, stack_anchor=ANCHOR,
                 record_hourly=True, compute_tes_metrics=kw.pop("tes", False), night_day_stride=0,
                 system_config_overrides={"solver": {"timestep_s": dt}}, **kw)
    return r, dv


def node_frame(r, pcm_rec, n_nodes=10):
    h = r["hourly"].copy()
    nt, nh = h.attrs["node_T"], h.attrs["node_h"]
    cols = {f"T_node{j + 1}_C": nt[:, j] for j in range(n_nodes)}
    if pcm_rec is not None:
        props = pcm_props_from_record(pcm_rec, 1.0)
        from src.simulation.capsule_mass import capsule_masses, wall_cp_per_kg_pcm
        from dataclasses import replace
        g = r["geometry"]
        m = capsule_masses(int(g["n_capsule"]), g["capsule_diameter_m"], 0.0008, props.density_kg_m3)
        props = replace(props, wall_cp_J_kgK=wall_cp_per_kg_pcm(m))
        for j in range(n_nodes):
            cols[f"f_node{j + 1}"] = [temperature_and_liquid_fraction_of_enthalpy(x, props)[1] for x in nh[:, j]]
    return pd.concat([h.reset_index(drop=True), pd.DataFrame(cols)], axis=1)


def main(dev):
    OUT.mkdir(parents=True, exist_ok=True)
    opt, row = optimum(dev)
    pcm = opt["pcm"]
    rec = get_pcm_properties(STATE, pcm)
    specs = criteria(opt, row, REGIME)
    print(f"regime {REGIME}: optimum {pcm} R {opt['R_in']*1000:.1f} mm, {opt['N']} capsules -> {OUT}", flush=True)
    w_year = roles.load_point_year(STATE, REGIME, CURRENT_MEDOIDS[REGIME], YEAR, "select")
    days, dfw = pick_days(w_year)
    files, annual = [], []
    # plain tank (water only), same weather, same demand
    plain_spec = dict(specs[0])
    plain, _ = run(REGIME, None, plain_spec, w_year, DT, tes=True)
    base_window = plain["tes"]["E_del45_window_kWh"]
    pf = node_frame(plain, None)
    for kind, date in days.items():
        i0, i1 = window(dfw, date)
        pf.iloc[i0:i1].to_csv(OUT / f"day_plain_{kind}.csv", index=False)
        files.append(f"day_plain_{kind}.csv")
    geoms = {}
    for s in specs:
        r, dv = run(REGIME, pcm, s, w_year, DT, tes=True)
        g = r["geometry"]
        lay = layout_from_geometry(g, 10, ANCHOR)
        geoms[s["key"]] = {"n_capsule": int(g["n_capsule"]), "capsule_diameter_m": g["capsule_diameter_m"], "pcm_thickness_m": g["pcm_thickness_m"],
                           "fraction": g["pcm_volume_fraction"], "capsules_per_node": lay.capsules_per_node.tolist(), "tank_diameter_m": g["tank_diameter_m"],
                           "tank_height_m": g["tank_height_m"], "pcm_mass_kg": r["metrics"]["pcm_mass_kg"]}
        nf = node_frame(r, rec)
        for kind, date in days.items():
            i0, i1 = window(dfw, date)
            nf.iloc[i0:i1].to_csv(OUT / f"day_{s['key']}_{kind}.csv", index=False)
            files.append(f"day_{s['key']}_{kind}.csv")
        m, t = r["metrics"], r["tes"]
        annual.append({"key": s["key"], "title": s["title"], **{k: s[k] for k in ("R_in", "fraction", "flow", "arrangement")}, "N": int(g["n_capsule"]),
                       "pcm_mass_kg": m["pcm_mass_kg"], "E_del45_window_kWh": t["E_del45_window_kWh"], "E_del45_window_plain_kWh": base_window,
                       "paired_gain_window_kWh": t["E_del45_window_kWh"] - base_window, "shield_h": m["shield_water_h"] + m["shield_pcm_h"],
                       "shield_plain_h": plain["metrics"]["shield_water_h"], "max_pcm_C": m["max_pcm_temp_C"], "max_water_C": m["max_water_temp_C"],
                       "residual_pct": m["residual_pct_of_collector"], "solar_fraction": m["solar_fraction"], "solar_fraction_plain": plain["metrics"]["solar_fraction"]})
        # Fluent-style sealed discharge: water 30 C, capsules 70 C, no sun, no draw
        wd = w_year.iloc[:12].copy()
        wd["GHI_Wm2"], wd["GHI_clearsky_Wm2"], wd["T_amb_C"] = 0.0, 0.0, 25.0
        rd, _ = run(REGIME, pcm, s, wd, 60.0, volume_multiplier=0.0, initial_state={"T_nodes": np.full(10, 30.0), "T_pcm_C": 70.0})
        node_frame(rd, rec).to_csv(OUT / f"discharge_{s['key']}.csv", index=False)
        files.append(f"discharge_{s['key']}.csv")
        print("criterion", s["key"], round(annual[-1]["paired_gain_window_kWh"], 2), flush=True)
    pd.DataFrame(annual).to_csv(OUT / "annual_criteria.csv", index=False)
    # four PCMs in the optimal geometry
    s0 = specs[0]
    for name in FOUR_PCMS:
        rr = get_pcm_properties(STATE, name)
        r, _ = run(REGIME, name, s0, w_year, DT, tes=True)
        nf = node_frame(r, rr)
        for kind, date in days.items():
            i0, i1 = window(dfw, date)
            nf.iloc[i0:i1].to_csv(OUT / f"pcm_{name.split()[0].replace('-', '')}_{kind}.csv", index=False)
            files.append(f"pcm_{name.split()[0].replace('-', '')}_{kind}.csv")
        print("pcm", name, round(r["tes"]["E_del45_window_kWh"] - base_window, 2), flush=True)
    manifest = {"state": STATE, "regime": REGIME, "year": YEAR, "pcm": pcm, "optimum": opt, "dev": bool(dev), "dt_s": DT, "anchor": ANCHOR,
                "plant": {"tank_volume_L": 100, "collector_area_m2": 2.0, "demand_L_day": 175, "delivery_C": 45},
                "days": {k: str(v) for k, v in days.items()}, "criteria": specs, "geometry": geoms, "pcm_record": {k: (None if (isinstance(v, float) and math.isnan(v)) else v) for k, v in rec.items() if isinstance(v, (int, float, str))},
                "four_pcms": FOUR_PCMS, "files": sorted(set(files)),
                "limits": "Visualisation of Objective 2 multi-node kernel output (hourly records; the discharge is 12 h at hourly resolution), not CFD and not experiment. Capsule arrangement shown by node (10 nodes), not true 3-D packing."}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    print("manifest written", len(files), "files")


if __name__ == "__main__":
    main("--dev" in sys.argv)
