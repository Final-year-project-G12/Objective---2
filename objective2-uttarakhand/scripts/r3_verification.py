"""
scripts/r3_verification.py  -  rebuild level L3: simulator verification on the common 100 L plant (plan gate G1)
===================================================================================================================
Per regime (rank-1 O1 PCM, flow 0.030 kg/s, 10-node tank, centre anchor, explore year 2018) for two verification designs
(V30: R_in 30 mm, 30 % PCM, staggered; V40: R_in 30 mm, 40 % PCM, staggered - the new cap) and the same-flow water-only tank:

  A  time step  150 -> 75 -> 37.5 -> 18.75 s. Pass (plan R5, 4.2): the change per halving is < 0.05 % for the primary energy metric
     (E_del45_window, the evening/morning delivery at the 45 C primary threshold) of every case, and the safety extrema do not change
     the feasibility decision (PCM <= 65 C, water <= 75 C). Annual useful energy is reported too. The coarsest passing step is the
     production step for that use; search stays at 150 s only if its feasibility decisions agree with the report step.
  B  node count 10 vs 20 at the report step 37.5 s: the shift goes into the repeatability band (it is not a pass/fail gate).
  C  energy closure: Gate-1 residual <= 0.1 % of collector energy in every run.
  D  IS 12976:2023 clause 4.2.3 standing loss: the water-only 100 L tank, no sun, no draw, uniform 60 C start, constant ambient,
     16 h -> mean water temperature drop against the 8 C limit. Ambient 20 C (a neutral reference) and the regime's coldest hourly
     ambient of 2016-2019 (the harshest case for that regime).
Writes results/l3_timestep_r<c>.csv, l3_nodes_r<c>.csv, l3_standing_loss_r<c>.csv (merged afterwards into results/l3_*.csv).
Usage: python scripts/r3_verification.py <regime>   (one regime per process; run the four with at most 3 at a time)
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.design.space import geometry_bounds, to_design        # noqa: E402
from src.io_utils import get_regime                             # noqa: E402
from src.simulation.run_case import run_case                    # noqa: E402
from src.weather import roles                                   # noqa: E402
from src.weather.inventory import CURRENT_MEDOIDS              # noqa: E402

OUT = ROOT / "results"
YEAR, FLOW = 2018, 0.030
DTS = (150, 75, 37.5, 18.75)
DESIGNS = {"V30": (0.030, 0.30, "staggered"), "V40": (0.030, 0.40, "staggered")}


def run(cid, pcm, dv, w, dt, nodes=10, **kw):
    t0 = time.time()
    r = run_case("uttarakhand", cid, pcm, dv, design_bounds=geometry_bounds(), weather=w, tank_model="multinode", n_nodes=nodes,
                 stack_anchor="center", compute_tes_metrics=True, night_day_stride=0, record_hourly=False,
                 system_config_overrides={"solver": {"timestep_s": dt}}, **kw)
    m, t = r["metrics"], r["tes"]
    return {"runtime_s": time.time() - t0, "useful_kWh": m["useful_energy_kWh"], "E_del45_window_kWh": t["E_del45_window_kWh"],
            "E_del45_annual_kWh": t["E_del45_annual_kWh"], "residual_pct": m["residual_pct_of_collector"],
            "t_pcm_max": m["max_pcm_temp_C"], "t_water_max": m["max_water_temp_C"],
            "shield_h": m["shield_water_h"] + m.get("shield_pcm_h", 0.0)}


def standing_loss(cid, t_amb):
    """100 L water-only tank, no sun, no draw, 60 C uniform start, constant ambient; mean water temperature after 16 h."""
    w = roles.load_point_year("uttarakhand", cid, CURRENT_MEDOIDS[cid], YEAR, "explore").iloc[:48].copy()
    w["GHI_Wm2"], w["GHI_clearsky_Wm2"], w["T_amb_C"] = 0.0, 0.0, float(t_amb)
    dv = to_design(*DESIGNS["V30"][:2], FLOW, DESIGNS["V30"][2])
    T0 = np.full(10, 60.0)
    r = run_case("uttarakhand", cid, None, dv, design_bounds=geometry_bounds(), weather=w, tank_model="multinode", n_nodes=10,
                 stack_anchor="center", record_hourly=True, volume_multiplier=0.0,
                 initial_state={"T_nodes": T0, "h_nodes": np.zeros(10), "T_w_C": 60.0})
    h = r["hourly"]
    col = "T_w_C" if "T_w_C" in h else [c for c in h.columns if c.startswith("T_w")][0]
    return float(60.0 - h[col].iloc[15])          # end of hour 16


def main(cid):
    pcm = get_regime("uttarakhand", cid)["pcm_shortlist"][0]
    w = roles.load_point_year("uttarakhand", cid, CURRENT_MEDOIDS[cid], YEAR, "explore")
    rows = []
    for dt in DTS:
        plain = run(cid, None, to_design(*DESIGNS["V30"][:2], FLOW, DESIGNS["V30"][2]), w, dt)
        rows.append({"regime": cid, "case": "plain", "pcm": "", "dt_s": dt, **plain})
        for name, (r_in, f, arr) in DESIGNS.items():
            p = run(cid, pcm, to_design(r_in, f, FLOW, arr), w, dt)
            rows.append({"regime": cid, "case": name, "pcm": pcm, "dt_s": dt, **p,
                         "g_window_kWh": p["E_del45_window_kWh"] - plain["E_del45_window_kWh"]})
        print(f"r{cid} dt {dt} done", flush=True)
    ts = pd.DataFrame(rows)
    for col in ("useful_kWh", "E_del45_window_kWh"):
        ts[f"chg_{col}_pct"] = ts.groupby("case")[col].transform(lambda s: 100 * (s / s.shift(1) - 1))
    ts.to_csv(OUT / f"l3_timestep_r{cid}.csv", index=False)

    nrows = []
    for nodes in (10, 20):
        plain = run(cid, None, to_design(*DESIGNS["V30"][:2], FLOW, DESIGNS["V30"][2]), w, 37.5, nodes)
        nrows.append({"regime": cid, "case": "plain", "n_nodes": nodes, **plain})
        for name, (r_in, f, arr) in DESIGNS.items():
            p = run(cid, pcm, to_design(r_in, f, FLOW, arr), w, 37.5, nodes)
            nrows.append({"regime": cid, "case": name, "n_nodes": nodes, **p,
                          "g_window_kWh": p["E_del45_window_kWh"] - plain["E_del45_window_kWh"]})
    pd.DataFrame(nrows).to_csv(OUT / f"l3_nodes_r{cid}.csv", index=False)

    cold = float(min(roles.load_point_year("uttarakhand", cid, CURRENT_MEDOIDS[cid], y, "explore").T_amb_C.min()
                     for y in roles.years_for("explore")))
    sl = [{"regime": cid, "ambient": "20 C reference", "T_amb_C": 20.0, "drop_16h_K": standing_loss(cid, 20.0)},
          {"regime": cid, "ambient": "coldest explore-year hour", "T_amb_C": cold, "drop_16h_K": standing_loss(cid, cold)}]
    for s in sl:
        s["limit_K"], s["pass"] = 8.0, s["drop_16h_K"] <= 8.0
    pd.DataFrame(sl).to_csv(OUT / f"l3_standing_loss_r{cid}.csv", index=False)
    print(ts[["case", "dt_s", "runtime_s", "useful_kWh", "chg_useful_kWh_pct", "E_del45_window_kWh", "chg_E_del45_window_kWh_pct",
              "t_pcm_max", "t_water_max", "residual_pct"]].round(4).to_string(index=False))
    print(pd.DataFrame(nrows)[["case", "n_nodes", "useful_kWh", "E_del45_window_kWh", "g_window_kWh"]].round(3).to_string(index=False))
    print(pd.DataFrame(sl).round(3).to_string(index=False))


if __name__ == "__main__":
    main(int(sys.argv[1]))
