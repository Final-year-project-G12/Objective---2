#!/usr/bin/env python3
"""
summarise_results.py -- collect the per-case outputs of the Uttarakhand CFD runs into two tables.

  results/cfd_capsule_results_uttarakhand.csv   one row per capsule case (cases/*/kpi.json, written by postprocess.py)
  results/cfd_tank_results_uttarakhand.csv      one row per tank case (cases_tank/*/tank_metrics.json, tank_postprocess.py)

Cases that have not been run yet are listed with status "not run". Run after run_all_cases.ps1.
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def main():
    index = list(csv.DictReader(open(os.path.join(ROOT, "results", "cases_index.csv"), encoding="utf-8")))
    caps, tanks = [], []
    for r in index:
        case = os.path.join(ROOT, r["case"])
        if r["kind"].startswith("capsule"):
            if r["kind"] == "capsule_viz":
                continue
            p = os.path.join(case, "kpi.json")
            row = dict(case=r["case"], kind=r["kind"], regime=r["regime"], pcm=r["pcm"])
            if os.path.exists(p):
                k = json.load(open(p, encoding="utf-8"))
                row.update(status="ok", **{x: k.get(x) for x in (
                    "t_melt_50_s", "t_melt_90_s", "t_melt_99_s", "E_window_kJ", "E_full_kJ", "f_melt_window",
                    "P_mean_window_W", "energy_residual_pct", "qc_energy_ok", "greybox_t_melt_90_s_x2",
                    "greybox_over_cfd_t90", "R_pcm_scale_equivalent")})
            else:
                row["status"] = "not run"
            caps.append(row)
        else:
            p = os.path.join(case, "tank_metrics.json")
            row = dict(case=r["case"], kind=r["kind"], regime=r["regime"], T_mains_C=r["T_mains_C"])
            if os.path.exists(p):
                m = json.load(open(p, encoding="utf-8"))
                row.update(status="ok", MIX_end=m["MIX"][-1], thermocline_10_90_m_end=m["thermocline_10_90_m"][-1],
                           T_out_C_end=m["T_out_C"][-1], litres_at_Tout_below_50C=m.get("litres_at_Tout_below_target"),
                           delivered_fraction_of_hot_volume=m.get("delivered_fraction_of_hot_volume"))
            else:
                row["status"] = "not run"
            tanks.append(row)
    for name, rows in (("cfd_capsule_results_uttarakhand.csv", caps), ("cfd_tank_results_uttarakhand.csv", tanks)):
        keys = list(dict.fromkeys(k for r in rows for k in r))
        with open(os.path.join(ROOT, "results", name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)
        done = sum(r["status"] == "ok" for r in rows)
        print(f"results/{name}: {done} of {len(rows)} cases run")


if __name__ == "__main__":
    main()
