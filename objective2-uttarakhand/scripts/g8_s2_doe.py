"""
scripts/g8_s2_doe.py
=======================
G8 / S2 (plan O2-8) - scrambled-Sobol DOE over the rebuild box for ONE (regime, O1 PCM) pair at the CHEAP fidelity (150 s, the
regime's representative explore year, every robust anchor; src/design/box.py). Same 128 points for every pair (seed 20261026), so
pairs are comparable. Rebuild mapping (2026-11-23): u in [0,1)^3 -> inner radius 10-40 mm, PCM fraction 2-40 %, arrangement
floor(3u); flow fixed at 0.030 kg/s. Geometry-infeasible points (exact engine) are recorded as rejected and NOT simulated.
Usage: python scripts/g8_s2_doe.py <cluster_id> <pcm_rank 1..3>  ->  results/g8_s2_r<c>_p<rank>.csv (one row per design: means over
anchors, the per-anchor g_window and the worst anchor).
"""
import sys
import time
from pathlib import Path

import pandas as pd
from scipy.stats import qmc

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.design.box import design_from_unit, flow_fixed      # noqa: E402
from src.io_utils import get_regime                          # noqa: E402
from src.optimize.evaluate import evaluate_design, flatten   # noqa: E402

SEED = 20261026
N_POINTS = 128          # 2^7


def sobol_points():
    return qmc.Sobol(d=3, scramble=True, seed=SEED).random_base2(7)


def evaluate_u(cid, pcm, u):
    r, f, arr = design_from_unit(*u)
    res = evaluate_design(cid, pcm, r, f, flow_fixed(), arr, purpose="explore", fidelity="cheap")
    row = flatten(res)
    row["status"] = "ok" if res["valid"] else "geometry_rejected"
    return row


def main(cid, rank):
    pcm = get_regime("uttarakhand", cid)["pcm_shortlist"][rank - 1]
    out = Path(f"results/g8_s2_r{cid}_p{rank}.csv")
    rows = []
    for i, u in enumerate(sobol_points()):
        t0 = time.time()
        try:
            row = evaluate_u(cid, pcm, u)
        except Exception as e:                                # a real failure, repaired by g8_s2_repair.py
            r, f, arr = design_from_unit(*u)
            row = {"cluster": cid, "pcm": pcm, "R_in_m": r, "fraction_req": f, "flow": flow_fixed(), "arrangement": arr,
                   "valid": False, "reason": repr(e)[:120], "status": "error"}
        row.update({"design_id": i, "u0": u[0], "u1": u[1], "u2": u[2], "runtime_s": time.time() - t0})
        rows.append(row)
        if i % 16 == 0:
            print(cid, rank, i, row["status"], flush=True)
            pd.DataFrame(rows).to_csv(out.with_suffix(".partial.csv"), index=False)     # the final name appears only when complete
    pd.DataFrame(rows).to_csv(out, index=False)
    out.with_suffix(".partial.csv").unlink(missing_ok=True)
    print("done", cid, rank, flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
