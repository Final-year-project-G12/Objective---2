"""
scripts/g8_s2_doe.py
=======================
G8 / S2 (plan WP5 5.4) - scrambled-Sobol initial DOE over the approved space for ONE (regime, O1 PCM) pair,
simulated for all five explore years (2016-2020) with the real simulator. Same 128 Sobol points for every pair
(seed 20261026) so pairs are comparable. Usage: python scripts/g8_s2_doe.py <cluster_id> <pcm_rank 1..3>

Mapping u in [0,1)^4 -> inner radius 10-40 mm, PCM fraction 2-30 %, flow 0.010-0.050 kg/s, arrangement
floor(3u). Geometry-infeasible points (exact engine) are recorded as rejected and NOT simulated.
Writes results/g8_s2_r<c>_p<rank>.csv (one row per design: means over years + per-year sd).
"""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import qmc

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.io_utils import get_regime
from src.optimize.evaluate import evaluate_design, flatten

SEED = 20261026
N_POINTS = 128          # 2^7


def sobol_points():
    return qmc.Sobol(d=4, scramble=True, seed=SEED).random_base2(7)


def design_from_u(u):
    arr = ("single-layer", "staggered", "radial")[min(int(u[3] * 3), 2)]
    return 0.010 + 0.030 * u[0], 0.02 + 0.28 * u[1], 0.010 + 0.040 * u[2], arr


def main(cid, rank):
    pcm = get_regime("rajasthan", cid)["pcm_shortlist"][rank - 1]
    rows = []
    for i, u in enumerate(sobol_points()):
        r, f, q, arr = design_from_u(u)
        t0 = time.time()
        try:
            res = evaluate_design(cid, pcm, r, f, q, arr, purpose="explore")
            row = flatten(res)
            row["status"] = "ok" if res["valid"] else "geometry_rejected"
            for yr in res.get("per_year", []):          # per-year targets, needed for leave-one-year-out (S3)
                for k in ("g_window", "g_annual", "g_useful", "d_overheat", "t_pcm_max"):
                    row[f"{k}_{yr['year']}"] = yr[k]
        except Exception as e:                                # a real failure, counted against the 95 % gate
            row = {"cluster": cid, "pcm": pcm, "R_in_m": r, "fraction_req": f, "flow": q, "arrangement": arr,
                   "valid": False, "reason": repr(e)[:120], "status": "error"}
        row.update({"design_id": i, "u0": u[0], "u1": u[1], "u2": u[2], "u3": u[3], "runtime_s": time.time() - t0})
        rows.append(row)
        if i % 16 == 0:
            print(cid, rank, i, row["status"], flush=True)
            pd.DataFrame(rows).to_csv(f"results/g8_s2_r{cid}_p{rank}.csv", index=False)
    pd.DataFrame(rows).to_csv(f"results/g8_s2_r{cid}_p{rank}.csv", index=False)
    print("done", cid, rank)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
