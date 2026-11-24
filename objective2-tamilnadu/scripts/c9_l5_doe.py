"""
scripts/c9_l5_doe.py   (level L5, step O2-8, CHEAP fidelity)
==============================================================
Scrambled-Sobol DOE (128 points, seed 20261026) over the common-plant box for ONE (regime, O1 PCM) pair:
  u -> inner radius 10-40 mm | PCM fraction 2-40 % | arrangement floor(3u).  Flow is frozen at 0.030 kg/s; the stack anchor is handled by the
  robust objective (rule R7): every design is simulated at bottom, centre AND top.
Cheap fidelity (pre-registered in configs/l5_fidelity_preregistration.json): dt 150 s, explore year 2017.
Geometry-infeasible points are recorded (reason code) and not simulated. Resumable (deterministic design ids).
Usage: python scripts/c9_l5_doe.py <cluster_id> <pcm_rank 1..3>   -> results/c9_l5_doe_r<c>_p<k>.csv
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import qmc

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.io_utils import get_regime                                   # noqa: E402
from src.optimize.evaluate import evaluate_design                     # noqa: E402
from config import STATE                                              # noqa: E402

SEED, N_POINTS, FLOW, YEARS, DT = 20261026, 128, 0.030, [2017], 150.0
ANCHORS = ("bottom", "center", "top")
ARRS = ("single-layer", "staggered", "radial")


def design_from_u(u):
    return 0.010 + 0.030 * u[0], 0.02 + 0.38 * u[1], ARRS[min(int(u[2] * 3), 2)]


def main(cid, rank):
    pcm = get_regime(STATE, cid)["pcm_shortlist"][rank - 1]
    out = Path(f"results/c9_l5_doe_r{cid}_p{rank}.csv")
    rows, done = [], set()
    if out.exists():
        prev = pd.read_csv(out)
        rows, done = prev.to_dict("records"), set(prev.design_id.astype(int))
    pts = qmc.Sobol(d=3, scramble=True, seed=SEED).random_base2(7)
    for i, u in enumerate(pts):
        if i in done:
            continue
        r, f, arr = design_from_u(u)
        t0 = time.time()
        row = {"design_id": i, "regime": cid, "pcm": pcm, "R_in_m": r, "fraction_req": f, "arrangement": arr, "u0": u[0], "u1": u[1], "u2": u[2]}
        try:
            res = {a: evaluate_design(cid, pcm, r, f, FLOW, arr, years=YEARS, stack_anchor=a, dt_s=DT) for a in ANCHORS}
            ok = all(v["valid"] for v in res.values())
            row.update({"valid": ok, "status": "ok" if ok else "geometry_rejected",
                        "reason": "" if ok else next(v["reason"] for v in res.values() if not v["valid"])})
            if ok:
                row.update({"N": res["center"]["N"], "fraction": res["center"]["fraction"]})
                for k in ("g_window", "g_annual", "d_overheat", "t_pcm_max"):
                    v = [res[a][k] for a in ANCHORS]
                    row.update({f"{k}_mean": float(np.mean(v)), f"{k}_worst": float(min(v) if k.startswith("g_") else max(v))})
                    for a in ANCHORS:
                        row[f"{k}_{a}"] = res[a][k]
                row["feasible"] = bool(all(v["feasible"] for v in res.values()))
        except Exception as e:                                                # noqa: BLE001
            row.update({"valid": False, "status": "error", "reason": repr(e)[:120]})
        row["runtime_s"] = time.time() - t0
        rows.append(row)
        if i % 16 == 0:
            print(cid, rank, i, row["status"], flush=True)
            pd.DataFrame(rows).to_csv(out, index=False)
    pd.DataFrame(rows).to_csv(out, index=False)
    print("done", cid, rank)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
