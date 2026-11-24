"""
scripts/c4_l3_verification.py   (level L3, plan steps O2-4/O2-5, gate G1)
===========================================================================
Simulator verification on the common plant (100 L / 2.0 m2 / 100 L/day), one regime per call:
  A. timestep halving 150 -> 75 -> 37.5 -> 18.75 s on a PCM design and its same-flow water-only twin (year 2017, explore);
     gate: change < 0.05 % per halving in the primary energy metrics.
  B. 10 vs 20 nodes (dt 150 s): the shift goes into the repeatability band.
  C. energy closure: residual_pct_of_collector < 0.1 % in every run.
  D. IS 12976:2023 clause 4.2.3 standing loss: no draw, no sun, start near service temperature; drop over 16 h vs 8 C.
Usage: python scripts/c4_l3_verification.py <cluster_id>     -> results/c4_l3_r<id>_{timestep,nodes,standing_loss}.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import io_utils                                   # noqa: E402
from src.design.space import geometry_bounds, to_design    # noqa: E402
from src.simulation.run_case import run_case               # noqa: E402
from src.weather import roles                              # noqa: E402
from src.weather.inventory import CURRENT_MEDOIDS          # noqa: E402
from config import STATE                                   # noqa: E402

YEAR = 2017
DTS = [150.0, 75.0, 37.5, 18.75]
METRICS = ["useful_energy_kWh", "E_del45_window_kWh", "E_del45_annual_kWh", "shield_water_h", "residual_pct"]
OUT = Path("results")


def run(cid, pcm, dv, dt, nodes=10, weather=None, **kw):
    w = weather if weather is not None else roles.load_point_year(STATE, cid, CURRENT_MEDOIDS[cid], YEAR, "explore")
    r = run_case(STATE, cid, pcm, dv, design_bounds=geometry_bounds(), weather=w, tank_model="multinode", n_nodes=nodes,
                 compute_tes_metrics=True, night_day_stride=0, system_config_overrides={"solver": {"timestep_s": dt}}, **kw)
    m, t = r["metrics"], r["tes"]
    return {"useful_energy_kWh": m["useful_energy_kWh"], "E_del45_window_kWh": t["E_del45_window_kWh"],
            "E_del45_annual_kWh": t["E_del45_annual_kWh"], "shield_water_h": m["shield_water_h"],
            "residual_pct": m["residual_pct_of_collector"], "max_pcm_C": m["max_pcm_temp_C"], "max_water_C": m["max_water_temp_C"]}


def main(cid):
    pcm = io_utils.o1_top3(STATE)[cid][0]
    designs = {"pcm_f30": to_design(0.025, 0.30, 0.030, "staggered"), "pcm_f40": to_design(0.025, 0.40, 0.030, "staggered")}
    rows = []
    for name, dv in designs.items():
        for arm, p in (("pcm", pcm), ("water_only", None)):
            if arm == "water_only" and name == "pcm_f40":
                continue
            for dt in DTS:
                try:
                    r = run(cid, p, dv, dt)
                except Exception as e:                                       # noqa: BLE001
                    rows.append({"regime": cid, "design": name, "arm": arm, "dt_s": dt, "error": repr(e)[:150]}); continue
                rows.append({"regime": cid, "design": name, "arm": arm, "pcm": p, "dt_s": dt, **r})
                print(cid, name, arm, dt, round(r["useful_energy_kWh"], 3), flush=True)
    df = pd.DataFrame(rows)
    for key in ("useful_energy_kWh", "E_del45_window_kWh", "E_del45_annual_kWh"):
        df[key + "_chg_pct"] = df.groupby(["design", "arm"])[key].transform(lambda s: s.diff().abs() / s.abs().shift() * 100.0)
    df.to_csv(OUT / f"c4_l3_r{cid}_timestep.csv", index=False)

    # B. nodes
    nrows = []
    for name, dv in designs.items():
        for arm, p in (("pcm", pcm), ("water_only", None)):
            if arm == "water_only" and name == "pcm_f40":
                continue
            a, b = run(cid, p, dv, 150.0, 10), run(cid, p, dv, 150.0, 20)
            nrows.append({"regime": cid, "design": name, "arm": arm, **{f"{k}_10": a[k] for k in METRICS[:3]},
                          **{f"{k}_20": b[k] for k in METRICS[:3]},
                          **{f"{k}_shift_pct": (b[k] - a[k]) / a[k] * 100.0 for k in METRICS[:3]}})
    pd.DataFrame(nrows).to_csv(OUT / f"c4_l3_r{cid}_nodes.csv", index=False)

    # D. standing loss (no draw, no sun)
    base = roles.load_point_year(STATE, cid, CURRENT_MEDOIDS[cid], YEAR, "explore").iloc[:16].copy()
    srows = []
    for t_amb in (20.0, 28.0):
        for t0 in (45.0, 60.0):
            w = base.copy()
            w["GHI_Wm2"] = 0.0
            w["GHI_clearsky_Wm2"] = 0.0
            w["T_amb_C"] = t_amb
            r = run_case(STATE, cid, None, designs["pcm_f30"], design_bounds=geometry_bounds(), weather=w, tank_model="multinode",
                         n_nodes=10, volume_multiplier=0.0, record_hourly=True,
                         system_config_overrides={"solver": {"timestep_s": 150.0}},
                         initial_state={"T_nodes": np.full(10, t0)})
            h = r["hourly"]
            col = next((c for c in h.columns if c.lower() in ("t_water_mean_c", "t_w_c", "t_water_c", "t_mean_c")), None)
            tw = h[col].to_numpy() if col else None
            srows.append({"regime": cid, "T_amb_C": t_amb, "T_start_C": t0, "hours": len(h),
                          "T_end_C": float(tw[-1]) if tw is not None else None,
                          "drop_16h_C": float(t0 - tw[-1]) if tw is not None else None, "limit_C": 8.0,
                          "col": col, "cols": ",".join(h.columns[:12]) if tw is None else ""})
    pd.DataFrame(srows).to_csv(OUT / f"c4_l3_r{cid}_standing_loss.csv", index=False)
    print(pd.DataFrame(srows).to_string())


if __name__ == "__main__":
    main(int(sys.argv[1]))
