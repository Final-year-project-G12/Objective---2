"""
src/optimize/robust_eval.py
==============================
One design -> one flat row of ROBUST (three-anchor, rule R7) paired metrics at a chosen fidelity. Shared by the L6 search, the L7 funnel
and the L9 test so every stage reports the same columns:
  g_*_mean = mean over bottom/centre/top anchors, g_*_worst = minimum, d_overheat_* / t_pcm_max_* : mean and maximum.
"""
import numpy as np

from src.design.space import load_space
from src.optimize.evaluate import evaluate_design

FLOW = 0.030


def robust_row(cid, pcm, r_in_m, fraction_req, arrangement, years, dt_s=None, purpose="explore"):
    anchors = load_space()["model"]["stack_anchors"]
    res = {a: evaluate_design(cid, pcm, r_in_m, fraction_req, FLOW, arrangement, purpose=purpose, years=years, stack_anchor=a, dt_s=dt_s)
           for a in anchors}
    row = {"regime": cid, "pcm": pcm, "R_in_m": r_in_m, "fraction_req": fraction_req, "arrangement": arrangement}
    ok = all(v["valid"] for v in res.values())
    row["valid"] = ok
    if not ok:
        row["status"], row["reason"] = "geometry_rejected", next(v["reason"] for v in res.values() if not v["valid"])
        return row
    c = res["center"]
    row.update({"status": "ok", "reason": "", "N": c["N"], "fraction": c["fraction"], "pcm_mass_kg": c["pcm_mass_kg"]})
    for k in ("g_window", "g_annual", "g_useful", "d_overheat", "t_pcm_max", "t_water_max"):
        v = [res[a][k] if k in res[a] else np.nan for a in anchors]
        if k == "t_water_max" and all(np.isnan(v)):
            continue
        row[f"{k}_mean"] = float(np.mean(v))
        row[f"{k}_worst"] = float(min(v) if k.startswith("g_") else max(v))
        for a in anchors:
            row[f"{k}_{a}"] = res[a].get(k)
    row["hours_over_limit"] = float(max(sum(y["hours_over_limit"] for y in res[a]["per_year"]) for a in anchors))
    row["feasible"] = bool(all(v["feasible"] for v in res.values()))
    for i, y in enumerate(years):
        row[f"g_window_{y}"] = float(np.mean([res[a]["per_year"][i]["g_window"] for a in anchors]))
        row[f"g_annual_{y}"] = float(np.mean([res[a]["per_year"][i]["g_annual"] for a in anchors]))
    return row
