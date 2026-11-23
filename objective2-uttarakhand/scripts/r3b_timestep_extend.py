"""
scripts/r3b_timestep_extend.py  -  L3 time-step gate, one more halving (18.75 -> 9.375 s)
=========================================================================================
At 175 L/day the 37.5 -> 18.75 s change of the primary metric (E_del45_window) is 0.057 % for the water-only tank in regime 0,
above the plan R5 limit of 0.05 %, so 37.5 s does not pass the gate everywhere. Plan R5 / 4.2: choose the coarsest step whose change
per halving is < 0.05 %. This script measures the change 18.75 -> 9.375 s with the same cases as scripts/r3_verification.py
(explore year 2018, centre anchor, plain + V30 + V40) and appends the 9.375 s rows to results/l3_timestep_r<c>.csv.
Usage: python scripts/r3b_timestep_extend.py <cluster_id>
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.r3_verification import DESIGNS, FLOW, OUT, YEAR, run     # noqa: E402
from src.design.space import to_design                                  # noqa: E402
from src.io_utils import get_regime                                     # noqa: E402
from src.weather import roles                                           # noqa: E402
from src.weather.inventory import CURRENT_MEDOIDS                      # noqa: E402

DT = 9.375


def main(cid):
    f = OUT / f"l3_timestep_r{cid}.csv"
    ts = pd.read_csv(f)
    ts = ts[ts.dt_s != DT]
    pcm = get_regime("uttarakhand", cid)["pcm_shortlist"][0]
    w = roles.load_point_year("uttarakhand", cid, CURRENT_MEDOIDS[cid], YEAR, "explore")
    plain = run(cid, None, to_design(*DESIGNS["V30"][:2], FLOW, DESIGNS["V30"][2]), w, DT)
    rows = [{"regime": cid, "case": "plain", "pcm": "", "dt_s": DT, **plain}]
    for name, (r_in, fr, arr) in DESIGNS.items():
        p = run(cid, pcm, to_design(r_in, fr, FLOW, arr), w, DT)
        rows.append({"regime": cid, "case": name, "pcm": pcm, "dt_s": DT, **p,
                     "g_window_kWh": p["E_del45_window_kWh"] - plain["E_del45_window_kWh"]})
    ts = pd.concat([ts, pd.DataFrame(rows)], ignore_index=True).sort_values(["case", "dt_s"], ascending=[True, False], kind="stable")
    order = {c: i for i, c in enumerate(["plain", "V30", "V40"])}
    ts = ts.sort_values(by=["dt_s", "case"], key=lambda s: -s if s.name == "dt_s" else s.map(order)).reset_index(drop=True)
    for col in ("useful_kWh", "E_del45_window_kWh"):
        ts[f"chg_{col}_pct"] = ts.groupby("case")[col].transform(lambda s: 100 * (s / s.shift(1) - 1))
    ts.to_csv(f, index=False)
    print(ts[ts.dt_s <= 18.75][["case", "dt_s", "runtime_s", "chg_E_del45_window_kWh_pct", "chg_useful_kWh_pct", "g_window_kWh"]]
          .round(4).to_string(index=False), flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]))
