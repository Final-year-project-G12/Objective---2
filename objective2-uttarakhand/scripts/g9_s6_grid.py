"""
scripts/g9_s6_grid.py
========================
G9 / S6 (plan O2-11) - dense regular grid for ONE (regime, O1 PCM) pair at the CHEAP fidelity (the search's own fidelity), to check
the NSGA-II front against the true front. Usage: python scripts/g9_s6_grid.py <cluster_id> [pcm_rank=1]
Rebuild grid (2026-11-23): 8 inner radii (10-40 mm) x 10 PCM fractions (2-40 %, so the 40 % boundary is on the grid) x 3 arrangements
= 240 designs, each at the 3 robust anchors = 720 simulator runs per regime (plan "720-point" check); flow fixed at 0.030 kg/s.
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

from src.design.box import f_bounds, flow_fixed, r_bounds
from src.io_utils import get_regime
from src.optimize.evaluate import evaluate_design, flatten

R_LEVELS = np.linspace(*r_bounds(), 8)
F_LEVELS = np.linspace(*f_bounds(), 10)
Q_LEVELS = (flow_fixed(),)
ARR = ("single-layer", "staggered", "radial")


def main(cid, rank):
    pcm = get_regime("uttarakhand", cid)["pcm_shortlist"][rank - 1]
    out = Path(f"results/g9_s6_grid_r{cid}_p{rank}.csv")
    rows = []
    for i, (r, f, q, a) in enumerate(itertools.product(R_LEVELS, F_LEVELS, Q_LEVELS, ARR)):
        t0 = time.time()
        try:
            res = evaluate_design(cid, pcm, float(r), float(f), float(q), a, purpose="explore", fidelity="cheap")
            row = flatten(res)
            row["status"] = "ok" if res["valid"] else "geometry_rejected"
        except Exception as e:
            row = {"cluster": cid, "pcm": pcm, "R_in_m": r, "fraction_req": f, "flow": q, "arrangement": a,
                   "valid": False, "reason": repr(e)[:120], "status": "error"}
        row.update({"grid_id": i, "runtime_s": time.time() - t0})
        rows.append(row)
        if i % 20 == 0:
            print(cid, rank, i, row["status"], flush=True)
            pd.DataFrame(rows).to_csv(out.with_suffix(".partial.csv"), index=False)
    pd.DataFrame(rows).to_csv(out, index=False)
    out.with_suffix(".partial.csv").unlink(missing_ok=True)
    print("done", cid, rank)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 1)
