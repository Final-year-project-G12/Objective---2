"""
scripts/g24_flow_fr_study.py
===============================
Plan WP3 (flow): does the "low flow is always best" result survive when the collector heat removal factor depends on flow?
Compares, for the frozen chosen design of a regime, a flow sweep with collector.flow_dependent_fr OFF (the production setting) and ON
(F_R(m) = m cp (1 - exp(-A U_L F' / (m cp))) / (A U_L), Eldokaishi 2022 Eq. 2, with F' = 0.84, U_L = 5.0 W/m2K from that paper and a reference flow of
0.030 kg/s that is an ASSUMPTION; see the flow_dependent_fr block of configs/system_config_shared.yaml). At 0.010 / 0.050 kg/s the ON option scales the collector
coefficients by about 0.952 / 1.010 relative to 0.030 kg/s.

Every case is paired with the exact water-only tank at the same flow and the same setting (no plain-baseline grid: the grid was built with the option OFF). Explore years
2016-2020 only. Reported per flow and setting: the plain tank's annual E_del,45 and useful energy, the PCM gain g_window / g_annual, d_overheat, and the PCM peak.
Reading: (1) does the plain tank still gain most at the lowest flow, (2) does the flow that maximises g_window move, (3) is the PCM gain at the same flow still nearly flat in flow.
Nothing here changes the production setting, the frozen designs or any selection.

Usage: python scripts/g24_flow_fr_study.py <cluster_id>   ->  results/g24_flow_fr_r<c>.csv
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.design.schema import DesignVector
from src.design.space import geometry_bounds, load_space, wall_m
from src.optimize.evaluate import _weather
from src.simulation.run_case import run_case
from src.weather import roles

OUT = Path("results")
SP = load_space()
FLOWS = (0.010, 0.015, 0.020, 0.030, 0.040, 0.050)


def one(cid, pcm, dv, y, on):
    over = {"collector": {"flow_dependent_fr": {"enabled": bool(on)}}}
    return run_case("rajasthan", cid, pcm, dv, design_bounds=geometry_bounds(), weather=_weather(cid, y, "explore"), tank_model=SP["model"]["tank_model"],
                    n_nodes=SP["model"]["n_nodes"], stack_anchor=SP["model"]["stack_anchor"], compute_tes_metrics=True, night_day_stride=0,
                    system_config_overrides=over)


def main(cid):
    ch = json.load(open(OUT / f"g10_selection_r{cid}.json", encoding="utf-8"))["chosen"]
    pcm, r, arr, n = ch["pcm"], float(ch["R_in_m"]), ch["arrangement"], int(ch["N"])
    rows = []
    for on in (False, True):
        for q in FLOWS:
            dv = DesignVector(capsule_diameter_m=2.0 * (r + wall_m()), n_capsule=n, flow_rate_kg_s=q, capsule_arrangement=arr)
            per = []
            for y in roles.years_for("explore"):
                a, b = one(cid, pcm, dv, y, on), one(cid, None, dv, y, on)
                m, t, mp, tp = a["metrics"], a["tes"], b["metrics"], b["tes"]
                per.append((t["E_del45_window_kWh"] - tp["E_del45_window_kWh"], t["E_del45_annual_kWh"] - tp["E_del45_annual_kWh"],
                            (m["shield_water_h"] + m["shield_pcm_h"]) - mp["shield_water_h"], m["max_pcm_temp_C"],
                            tp["E_del45_annual_kWh"], mp["useful_energy_kWh"]))
            x = np.array(per)
            rows.append({"regime": cid, "pcm": pcm, "flow_dependent_fr": on, "flow": q, "g_window": x[:, 0].mean(), "g_annual": x[:, 1].mean(),
                         "d_overheat": x[:, 2].mean(), "t_pcm_max": x[:, 3].max(), "plain_E_del45_annual_kWh": x[:, 4].mean(), "plain_useful_kWh": x[:, 5].mean()})
            print(f"FR flow-dependent={on!s:5} q={q:.3f}  plain E_del45 {x[:, 4].mean():7.1f}  g_window {x[:, 0].mean():6.1f}  PCM peak {x[:, 3].max():.1f}", flush=True)
            pd.DataFrame(rows).to_csv(OUT / f"g24_flow_fr_r{cid}.csv", index=False)
    df = pd.DataFrame(rows)
    for on in (False, True):
        d = df[df.flow_dependent_fr == on]
        print(f"flow_dependent_fr={on}: plain tank best flow {d.loc[d.plain_E_del45_annual_kWh.idxmax(), 'flow']:.3f}, g_window best flow {d.loc[d.g_window.idxmax(), 'flow']:.3f}, "
              f"g_window range over flow {d.g_window.max() - d.g_window.min():.1f} kWh")


if __name__ == "__main__":
    main(int(sys.argv[1]))
