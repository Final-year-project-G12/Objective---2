"""
scripts/g9_s6_grid.py
========================
G9 / S6 (plan WP5 5.4) - dense regular grid for ONE (regime, O1 PCM) pair, simulated for all five explore years, to
check the NSGA-II front against the true front. Usage: python scripts/g9_s6_grid.py <cluster_id> [pcm_rank=1]
Grid: 6 inner radii (10-40 mm) x 8 PCM fractions (2-30 %) x 5 flows (0.010-0.050) x 3 arrangements = 720 designs.
Geometry-infeasible points are recorded as rejected and not simulated. Writes results/g9_s6_grid_r<c>_p<rank>.csv
(incrementally, every 20 designs).
"""

import itertools
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.io_utils import get_regime
from src.optimize.evaluate import evaluate_design, flatten
from config import STATE

R_LEVELS = np.linspace(0.010, 0.040, 6)
F_LEVELS = np.linspace(0.02, 0.30, 8)      # v3 box: 4 % steps (v1: 6 levels to 20 %)
Q_LEVELS = np.linspace(0.010, 0.050, 5)
ARR = ("single-layer", "staggered", "radial")

# SCOPE, 2026-10-29 (ours, user-authorised). At full scope this stage is
# 9 pairs x 720 designs x 5 years = 32,400 simulated years ~= 42 CPU-hours,
# which on this machine (i7-1255U: 2 P-cores + 8 E-cores, ~1.4 GB free RAM)
# is ~17 h wall -- longer than every other stage combined.
#
# What this gate is FOR: checking the NSGA-II front against a brute-force
# front, i.e. comparing the SHAPE and position of a Pareto front. It is a
# cross-check, not a reported design. So the grid keeps its full resolution
# in the four design variables (720 points -- the thing that decides whether
# the true front is found) and economises on the two axes that do not affect
# front shape:
#   * one representative explore year instead of all five. Front shape is set
#     by the design variables; the year sets the absolute kWh level, which is
#     not what is being compared here. Per-year spread is already measured by
#     g9_band on the selected designs, at the confirmation timestep.
#   * rank-1 PCM per regime instead of all three ranks. Ranks 2-3 differ only
#     in material properties, not in the geometry of the design space, so the
#     front-finding check does not need repeating three times.
# Net: 3 jobs x 720 designs x 1 year = 2,160 simulated years, ~1/15 the cost.
#
# Pass --full to run her original 9-pair, 5-year scope.
GRID_YEARS = [2018]          # mid explore year; None => all explore years
GRID_RANKS = (1,)            # ranks actually cross-checked; (1, 2, 3) => hers


def main(cid, rank):
    pcm = get_regime(STATE, cid)["pcm_shortlist"][rank - 1]
    out = Path(f"results/g9_s6_grid_r{cid}_p{rank}.csv")

    # RESUME (ours, 2026-10-29). This grid is 720 designs x 5 years per pair and
    # 9 pairs -- about 42 CPU-hours, the most expensive stage in the sequence.
    # Her version always restarted from grid_id 0, so any interruption threw the
    # whole pair away. The grid is a deterministic itertools.product, so a row
    # already on disk is exactly the row this run would recompute; skipping it
    # changes no result. Delete the CSV to force a clean rerun.
    rows, done = [], set()
    if out.exists():
        prev = pd.read_csv(out)
        if "grid_id" in prev.columns:
            rows = prev.to_dict("records")
            done = set(prev["grid_id"].astype(int))
            print(f"resuming {out.name}: {len(done)} of 720 designs already done", flush=True)

    for i, (r, f, q, a) in enumerate(itertools.product(R_LEVELS, F_LEVELS, Q_LEVELS, ARR)):
        if i in done:
            continue
        t0 = time.time()
        try:
            res = evaluate_design(cid, pcm, float(r), float(f), float(q), a,
                                  purpose="explore", years=GRID_YEARS)
            row = flatten(res)
            row["status"] = "ok" if res["valid"] else "geometry_rejected"
            for yr in res.get("per_year", []):
                for k in ("g_window", "g_annual", "g_useful", "d_overheat", "t_pcm_max"):
                    row[f"{k}_{yr['year']}"] = yr[k]
        except Exception as e:
            row = {"cluster": cid, "pcm": pcm, "R_in_m": r, "fraction_req": f, "flow": q, "arrangement": a,
                   "valid": False, "reason": repr(e)[:120], "status": "error"}
        row.update({"grid_id": i, "runtime_s": time.time() - t0})
        rows.append(row)
        if i % 20 == 0:
            print(cid, rank, i, row["status"], flush=True)
            pd.DataFrame(rows).to_csv(out, index=False)
    pd.DataFrame(rows).to_csv(out, index=False)
    print("done", cid, rank)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--full"]
    if "--full" in sys.argv:                 # her original scope
        GRID_YEARS, GRID_RANKS = None, (1, 2, 3)
    cid = int(args[0])
    if len(args) > 1:
        main(cid, int(args[1]))
    else:
        for rank in GRID_RANKS:
            main(cid, rank)
