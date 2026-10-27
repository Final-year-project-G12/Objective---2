"""
scripts/g9_s6_grid.py
========================
G9 / S6 (plan WP5 5.4) - dense regular grid for ONE (regime, O1 PCM) pair, simulated for all five explore years, to
check the NSGA-II front against the true front. Usage: python scripts/g9_s6_grid.py <cluster_id> [pcm_rank=1]
Grid: 6 inner radii (10-40 mm) x 6 PCM fractions (2-20 %) x 5 flows (0.010-0.050) x 3 arrangements = 540 designs.
Geometry-infeasible points are recorded as rejected and not simulated. Writes results/redesign/g9_s6_grid_r<c>_p<rank>.csv
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

R_LEVELS = np.linspace(0.010, 0.040, 6)
F_LEVELS = np.linspace(0.02, 0.20, 6)
Q_LEVELS = np.linspace(0.010, 0.050, 5)
ARR = ("single-layer", "staggered", "radial")


def main(cid, rank):
    pcm = get_regime("rajasthan", cid)["pcm_shortlist"][rank - 1]
    out = Path(f"results/redesign/g9_s6_grid_r{cid}_p{rank}.csv")
    rows = []
    for i, (r, f, q, a) in enumerate(itertools.product(R_LEVELS, F_LEVELS, Q_LEVELS, ARR)):
        t0 = time.time()
        try:
            res = evaluate_design(cid, pcm, float(r), float(f), float(q), a, purpose="explore")
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
    main(int(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 1)
