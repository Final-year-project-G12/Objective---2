"""
scripts/g16_issue3_serve.py
==============================
Issue 3 (progress log sections 18/22): why the night-serve duration (tau_serve) shows no gain, and whether another measurement of the same evening
scenario can separate designs. For the frozen chosen design of a regime, select years 2021-2023, night scenarios every 15th day (stride 15), the
quantities of src/metrics/tes_metrics.py (tau_hold, tau_serve, serve_frac_45, serve_E_del45 = energy delivered at >= 45 C during the 18:00-09:00
draw scenario, minimum outlet temperature) are reported for four cases:
  pcm        the chosen PCM design
  plain      the official baseline: water-only tank, same flow, same 50 L tank
  pcm_L0     the chosen design with the latent heat set to zero (PCM becomes sensible-only): separates the latent contribution
  plain_40L  DIAGNOSTIC ONLY, not a baseline: water-only tank with the water volume reduced by the capsule volume (tank volume x (1 - outer fraction)),
             to test whether volume displacement alone reproduces the PCM tank's serve numbers. The fixed 50 L tank is not changed anywhere else.
Usage: python scripts/g16_issue3_serve.py <cluster_id>  ->  results/g16_serve_r<c>.csv
"""

import json
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.design.space import geometry_bounds, load_space, to_design
from src.optimize.evaluate import _weather
from src.simulation.run_case import run_case
from src.weather import roles

OUT = Path("results")
KEYS = ("tau_hold_mean_h", "tau_serve_mean_h", "serve_frac_45_mean", "serve_E_del45_mean_kWh", "serve_T_out_min_mean_C")


def main(cid):
    ch = json.load(open(OUT / f"g10_selection_r{cid}.json", encoding="utf-8"))["chosen"]
    sp = load_space()
    dv = to_design(ch["R_in_m"], ch["fraction"], ch["flow"], ch["arrangement"])
    frac = float(ch["fraction"])
    cases = {
        "pcm": dict(pcm=ch["pcm"]),
        "plain": dict(pcm=None),
        "pcm_L0": dict(pcm=ch["pcm"], pcm_record_overrides={"latent_heat_kJ_kg": 0.0}),
        "plain_40L": dict(pcm=None, system_config_overrides={"tank": {"volume_L": 50.0 * (1.0 - frac)}}),
    }
    rows = []
    only = os.environ.get("G16_ONLY")                       # re-run one case only; output file then gets the case name appended
    dv_plain = to_design(0.02, 0.05, ch["flow"], "staggered")   # the plain tank ignores the capsule layout (G11 control N1); a 40 L tank cannot hold the real stack
    for name, kw in cases.items():
        if only and name != only:
            continue
        pcm = kw.pop("pcm")
        for y in roles.years_for("select"):
            try:
                r = run_case("rajasthan", cid, pcm, dv_plain if name == "plain_40L" else dv, design_bounds=geometry_bounds(), weather=_weather(cid, y, "select"),
                             tank_model=sp["model"]["tank_model"], n_nodes=sp["model"]["n_nodes"], stack_anchor=sp["model"]["stack_anchor"],
                             compute_tes_metrics=True, night_day_stride=15, **kw)
            except Exception as e:                                   # a diagnostic that cannot run is reported, not hidden
                rows.append({"regime": cid, "case": name, "year": y, "error": repr(e)[:200]})
                continue
            row = {"regime": cid, "case": name, "year": y, "valid": bool(r["valid"])}
            if r["valid"]:
                row.update({k: r["tes"].get(k, float("nan")) for k in KEYS})
                row["E_del45_window_kWh"] = r["tes"]["E_del45_window_kWh"]
                row["useful_energy_kWh"] = r["metrics"]["useful_energy_kWh"]
            rows.append(row)
        print("done", name, flush=True)
        pd.DataFrame(rows).to_csv(OUT / (f"g16_serve_r{cid}.csv" if not only else f"g16_serve_{only}_r{cid}.csv"), index=False)


if __name__ == "__main__":
    main(int(sys.argv[1]))
